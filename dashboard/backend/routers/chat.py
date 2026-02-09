#!/usr/bin/env python3
"""
Chat API Router for KRX Sector Rotation Dashboard

Provides AI-powered investment Q&A using:
- Gemini-2.0-Flash via OpenRouter
- PostgreSQL for conversation history
- Security-hardened system prompt
"""

import os
import uuid
import httpx
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_session
from models.chat import Conversation, Message

router = APIRouter()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemini-2.0-flash-001"

# QA Document path for RAG context
QA_DOC_PATH = Path(__file__).parent.parent.parent.parent / "analysis" / "QA_investment_questions_20260129.md"

# Cache for QA content
_qa_content_cache = None


def load_qa_content() -> str:
    """Load QA document for RAG context (cached)"""
    global _qa_content_cache
    if _qa_content_cache is None:
        if QA_DOC_PATH.exists():
            _qa_content_cache = QA_DOC_PATH.read_text(encoding="utf-8")
        else:
            _qa_content_cache = ""
    return _qa_content_cache


# Security-hardened system prompt
SYSTEM_PROMPT = """You are a KRX Sector Rotation investment assistant for Wealth PBs (Private Bankers).

## STRICT SECURITY RULES (MUST FOLLOW):
1. ONLY answer questions about stock recommendations, themes, market conditions, and dashboard navigation
2. NEVER explain internal algorithms or methodologies:
   - Do NOT explain Fiedler eigenvalue calculation
   - Do NOT explain HMM (Hidden Markov Model) regime detection
   - Do NOT explain correlation matrix computation
   - Do NOT explain PageRank centrality calculation
   - Do NOT explain meta-labeling model internals
   - Do NOT explain Bollinger Band technical details
3. If asked about implementation/algorithms, respond: "이 정보는 내부 분석 시스템에서 제공됩니다. 결과만 안내해 드릴 수 있습니다."
4. Stay within the scope of pre-computed analysis data
5. Redirect users to appropriate dashboard pages when relevant
6. NEVER make up stock prices, dates, or specific numbers not in the context
7. If you don't have specific data, say so honestly

## VOCABULARY (use consistently):
- 군집성 (Cohesion): 테마 내 종목들의 동조화 강도 (높을수록 함께 움직임)
- 모멘텀 (Momentum): 상승 추세 + 매수 조건을 충족한 종목 (Transition regime + Above BB)
- 시그널 (Signal): 매수/매도 신호 (메타 레이블링 품질 필터 통과 여부)
- 핵심 종목 (Key Player): 테마 내 중심성이 높은 종목
- TIER 1: 최고 품질 테마 (메타 레이블링 필터 통과)

## DASHBOARD PAGES (guide users here, use relative paths only):
- 개요 (Overview): /index.html - 전체 현황, 모멘텀 종목, 테마 건강도
- 모멘텀 (Momentum): /breakout.html - 관심 종목 리스트, 단계별 분포
- 시그널 (Signals): /signals.html - 테마별 신호 품질, 통과율
- 군집성 (Cohesion): /cohesion.html - 테마 군집성 분석
- 네트워크 (Network): /theme-graph.html - 테마 관계도 시각화
- AI 채팅 (Chat): /chat.html - AI 투자 Q&A

## RESPONSE STYLE:
- Answer in the user's language (Korean or English)
- Keep responses concise and actionable
- Use bullet points and tables when appropriate
- Always cite which dashboard page has more details
- Be professional and helpful

## CONTEXT DATA:
Below is the current analysis data you can reference:

{qa_content}
"""


# Request/Response models
class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language: str = "ko"  # "ko" or "en"


class ChatMessageResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str


class ConversationListItem(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationHistory(BaseModel):
    id: str
    title: Optional[str]
    messages: List[MessageItem]


async def call_openrouter(messages: list, language: str = "ko") -> str:
    """Call OpenRouter API with Gemini model"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY not configured"
        )

    # Load QA content and format system prompt
    qa_content = load_qa_content()
    system_content = SYSTEM_PROMPT.format(qa_content=qa_content[:15000])  # Limit context size

    # Build messages with system prompt
    api_messages = [
        {"role": "system", "content": system_content}
    ] + messages

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000"),
        "X-Title": os.getenv("OPENROUTER_SITE_NAME", "KRX-Sector-Rotation-Dashboard"),
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": api_messages,
        "max_tokens": 1000,
        "temperature": 0.3,  # Lower temperature for more consistent answers
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OpenRouter API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call OpenRouter: {str(e)}"
            )


def generate_title(message: str) -> str:
    """Generate a short title from the first message"""
    # Take first 50 chars, clean up
    title = message.strip()[:50]
    if len(message) > 50:
        title += "..."
    return title


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message and get AI response.
    Creates a new conversation if conversation_id is not provided.
    """
    try:
        conversation = None

        # Get or create conversation
        if request.conversation_id:
            try:
                conv_uuid = uuid.UUID(request.conversation_id)
                result = await session.execute(
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(Conversation.id == conv_uuid)
                )
                conversation = result.scalar_one_or_none()
            except ValueError:
                pass  # Invalid UUID, create new conversation

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                title=generate_title(request.message)
            )
            session.add(conversation)
            await session.flush()  # Get the ID

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        session.add(user_message)

        # Build conversation history for API
        # Get recent messages (limit to last 10 for context)
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        history_messages = list(reversed(result.scalars().all()))

        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        # Add current message
        api_messages.append({"role": "user", "content": request.message})

        # Get AI response
        ai_response = await call_openrouter(api_messages, request.language)

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response
        )
        session.add(assistant_message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        await session.commit()

        return ChatMessageResponse(
            response=ai_response,
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id)
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def new_conversation(
    session: AsyncSession = Depends(get_session)
):
    """Start a new conversation"""
    try:
        conversation = Conversation()
        session.add(conversation)
        await session.commit()

        return {
            "conversation_id": str(conversation.id),
            "created_at": conversation.created_at.isoformat()
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get full conversation history"""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_uuid)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Sort messages by created_at
    sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)

    return ConversationHistory(
        id=str(conversation.id),
        title=conversation.title,
        messages=[
            MessageItem(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            )
            for msg in sorted_messages
        ]
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """List recent conversations"""
    result = await session.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        ConversationListItem(
            id=str(conv.id),
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages)
        )
        for conv in conversations
    ]


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Delete a conversation and all its messages"""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    result = await session.execute(
        select(Conversation).where(Conversation.id == conv_uuid)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.delete(conversation)
    await session.commit()

    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/health")
async def chat_health():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "qa_document_loaded": QA_DOC_PATH.exists(),
        "model": MODEL
    }

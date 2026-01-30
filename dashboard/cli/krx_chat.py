#!/usr/bin/env python3
"""
KRX Sector Rotation Chat CLI
============================
Terminal-based chat with the KRX investment assistant.

Usage:
    python krx_chat.py "질문"           # Single question
    python krx_chat.py                   # Interactive mode
    python krx_chat.py --new "질문"      # Start new conversation
    python krx_chat.py --history         # Show conversation history
"""

import argparse
import os
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

# Configuration
CONFIG = {
    "api_base": os.getenv("KRX_API_BASE", "http://localhost:8000")
}
CONVERSATION_FILE = Path.home() / ".krx_chat_conversation_id"

# Rich console with custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "user": "bold blue",
    "assistant": "bold green",
})
console = Console(theme=custom_theme)


def get_api_base() -> str:
    """Get API base URL."""
    return CONFIG["api_base"]


def get_conversation_id() -> str | None:
    """Load saved conversation ID."""
    if CONVERSATION_FILE.exists():
        return CONVERSATION_FILE.read_text().strip()
    return None


def save_conversation_id(conv_id: str) -> None:
    """Save conversation ID for persistence."""
    CONVERSATION_FILE.write_text(conv_id)


def clear_conversation() -> None:
    """Clear saved conversation."""
    if CONVERSATION_FILE.exists():
        CONVERSATION_FILE.unlink()


def create_new_conversation() -> str | None:
    """Create a new conversation via API."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{get_api_base()}/api/chat/new")
            if response.status_code == 200:
                data = response.json()
                conv_id = data.get("conversation_id")
                if conv_id:
                    save_conversation_id(conv_id)
                    return conv_id
    except Exception as e:
        console.print(f"[error]Failed to create conversation: {e}[/error]")
    return None


def send_message(message: str, conversation_id: str | None = None) -> tuple[str, str]:
    """
    Send message to chat API.

    Returns:
        tuple: (response_text, conversation_id)
    """
    try:
        with httpx.Client(timeout=60.0) as client:
            payload = {
                "message": message,
                "conversation_id": conversation_id,
                "language": "ko"
            }

            response = client.post(
                f"{get_api_base()}/api/chat/message",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", ""), data.get("conversation_id", "")
            else:
                return f"[API Error {response.status_code}] {response.text}", ""

    except httpx.TimeoutException:
        return "[Error] Request timed out. The server might be busy.", ""
    except httpx.ConnectError:
        return f"[Error] Cannot connect to {get_api_base()}. Is the server running?", ""
    except Exception as e:
        return f"[Error] {str(e)}", ""


def get_history(conversation_id: str) -> list[dict]:
    """Get conversation history."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{get_api_base()}/api/chat/history/{conversation_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
    except Exception as e:
        console.print(f"[error]Failed to get history: {e}[/error]")
    return []


def display_response(response: str) -> None:
    """Display AI response with markdown formatting."""
    console.print()
    console.print(Panel(
        Markdown(response),
        title="[assistant]KRX Assistant[/assistant]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print()


def display_history(messages: list[dict]) -> None:
    """Display conversation history."""
    if not messages:
        console.print("[warning]No conversation history found.[/warning]")
        return

    console.print("\n[bold]Conversation History[/bold]\n")
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            console.print(Panel(
                content,
                title="[user]You[/user]",
                border_style="blue"
            ))
        else:
            console.print(Panel(
                Markdown(content),
                title="[assistant]Assistant[/assistant]",
                border_style="green"
            ))
        console.print()


def interactive_mode() -> None:
    """Run interactive chat mode."""
    console.print(Panel(
        "[bold]KRX Sector Rotation Chat[/bold]\n\n"
        "Commands:\n"
        "  /new     - Start new conversation\n"
        "  /history - Show conversation history\n"
        "  /clear   - Clear conversation\n"
        "  /quit    - Exit chat\n",
        title="Interactive Mode",
        border_style="cyan"
    ))

    conversation_id = get_conversation_id()
    if conversation_id:
        console.print(f"[info]Resuming conversation: {conversation_id[:8]}...[/info]\n")

    while True:
        try:
            user_input = Prompt.ask("\n[user]You[/user]")

            if not user_input.strip():
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().strip()

                if cmd in ["/quit", "/exit", "/q"]:
                    console.print("[info]Goodbye![/info]")
                    break

                elif cmd == "/new":
                    clear_conversation()
                    conversation_id = create_new_conversation()
                    if conversation_id:
                        console.print(f"[success]New conversation started: {conversation_id[:8]}...[/success]")
                    continue

                elif cmd == "/history":
                    if conversation_id:
                        messages = get_history(conversation_id)
                        display_history(messages)
                    else:
                        console.print("[warning]No active conversation.[/warning]")
                    continue

                elif cmd == "/clear":
                    clear_conversation()
                    conversation_id = None
                    console.print("[success]Conversation cleared.[/success]")
                    continue

                else:
                    console.print(f"[warning]Unknown command: {cmd}[/warning]")
                    continue

            # Send message
            with console.status("[bold green]Thinking...[/bold green]"):
                response, new_conv_id = send_message(user_input, conversation_id)

            if new_conv_id and new_conv_id != conversation_id:
                conversation_id = new_conv_id
                save_conversation_id(conversation_id)

            display_response(response)

        except KeyboardInterrupt:
            console.print("\n[info]Use /quit to exit.[/info]")
        except EOFError:
            console.print("\n[info]Goodbye![/info]")
            break


def single_question(question: str, new_conversation: bool = False) -> None:
    """Ask a single question and exit."""
    conversation_id = None if new_conversation else get_conversation_id()

    if new_conversation:
        clear_conversation()

    with console.status("[bold green]Thinking...[/bold green]"):
        response, new_conv_id = send_message(question, conversation_id)

    if new_conv_id:
        save_conversation_id(new_conv_id)

    display_response(response)


def main():
    parser = argparse.ArgumentParser(
        description="KRX Sector Rotation Chat CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "오늘 모멘텀 종목은?"        Single question
  %(prog)s                              Interactive mode
  %(prog)s --new "새 대화 시작"         New conversation
  %(prog)s --history                    Show history

Environment:
  KRX_API_BASE    API server URL (default: http://localhost:8000)
        """
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (omit for interactive mode)"
    )
    parser.add_argument(
        "--new", "-n",
        action="store_true",
        help="Start a new conversation"
    )
    parser.add_argument(
        "--history", "-H",
        action="store_true",
        help="Show conversation history"
    )
    parser.add_argument(
        "--clear", "-c",
        action="store_true",
        help="Clear saved conversation"
    )
    parser.add_argument(
        "--api",
        default=CONFIG["api_base"],
        help=f"API base URL (default: {CONFIG['api_base']})"
    )

    args = parser.parse_args()

    # Override API base if provided via argument
    CONFIG["api_base"] = args.api

    # Handle commands
    if args.clear:
        clear_conversation()
        console.print("[success]Conversation cleared.[/success]")
        return

    if args.history:
        conversation_id = get_conversation_id()
        if conversation_id:
            messages = get_history(conversation_id)
            display_history(messages)
        else:
            console.print("[warning]No active conversation. Start one first.[/warning]")
        return

    # Interactive or single question mode
    if args.question:
        single_question(args.question, new_conversation=args.new)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

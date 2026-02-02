# Sector-Rotation-KRX Project Instructions

## Project Overview

KRX (Korea Exchange) Sector Rotation Analysis System using Three-Layer Framework:
- **Cohesion**: Fiedler eigenvalue for theme network connectivity
- **Regime**: HMM-based Bull/Bear state detection
- **Trend**: Momentum-based stage classification

---

## Stage Classification System

Stages are determined from momentum and regime signals:

| Stage | Criteria | Priority | Action |
|-------|----------|----------|--------|
| **Super Trend** | momentum > 0.1 + bull_ratio ≥ 0.5 + in_green | HIGH | BUY |
| **Early Breakout** | momentum > 0.1 + bull_ratio ≥ 0.5 | HIGH | BUY |
| **Burgeoning** | momentum > 0.05 | MEDIUM | HOLD |
| **Building** | momentum > 0 | LOW | HOLD |
| **Consolidation** | momentum ≈ 0 | LOW | WATCH |
| **Bear Volatile** | momentum < -0.05 | AVOID | AVOID |

**Stage data is pre-computed and stored in:**
- `data/actionable_tickers_*.csv` - Daily stage assignments

### TIER Classification (Theme Level)

| Tier | Action | Fiedler Value |
|------|--------|---------------|
| **Tier 1** | BUY NOW | > 50 |
| **Tier 2** | ACCUMULATE | > 20 |
| **Tier 3** | RESEARCH | > 5 |
| **Tier 4** | MONITOR | ≤ 5 |

---

## Directory Structure

```
Sector-Rotation-KRX/
├── analysis/                    # Analysis reports and Q&A
│   └── QA_investment_questions_*.md  # AI chat context data
├── backtest/                    # Meta-labeling models and backtest
│   └── models/                  # Trained XGBoost models
├── dashboard/                   # Visual Q&A Dashboard
│   ├── backend/                 # FastAPI backend (port 8000)
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── db.py               # Database connection (PostgreSQL)
│   │   ├── models/             # SQLAlchemy models
│   │   │   └── chat.py         # Conversation & Message models
│   │   ├── routers/            # API route modules
│   │   │   ├── meta_labeling.py # Meta-labeling endpoints
│   │   │   ├── sector_rotation.py # Sector rotation endpoints
│   │   │   ├── portfolio.py    # Portfolio endpoints
│   │   │   ├── breakout.py     # Breakout candidates endpoints
│   │   │   ├── network.py      # Theme network endpoints
│   │   │   └── chat.py         # AI Chat endpoints (OpenRouter)
│   │   ├── setup_db.sql        # PostgreSQL schema
│   │   ├── .env.example        # Environment template
│   │   └── requirements.txt
│   └── frontend/               # Static HTML frontend (KOR/ENG i18n)
│       ├── index.html          # 개요 - Overview dashboard
│       ├── breakout.html       # 모멘텀 - Momentum candidates
│       ├── signals.html        # 시그널 - Signal quality matrix
│       ├── cohesion.html       # 군집성 - Theme cohesion analysis
│       ├── theme-graph.html    # 네트워크 - Theme network visualization
│       ├── chat-widget.js      # Floating AI chat widget
│       └── chat-test.html      # Chat API test page
│   └── cli/                    # Command-line tools
│       ├── krx_chat.py         # Terminal chat client
│       ├── install.sh          # CLI installation script
│       └── requirements.txt    # CLI dependencies
├── data/                        # Output data files
├── reports/                     # Generated reports
├── *.py                         # Analysis scripts
└── CLAUDE.md                    # This file
```

---

## Dashboard Architecture

### Overview

The dashboard provides a visual Q&A interface for sector rotation analysis with five main pages:

| Page | URL | Korean Title | Purpose |
|------|-----|--------------|---------|
| Overview | `/` | 개요 | Market snapshot, signal quality, top picks |
| Momentum | `/breakout.html` | 모멘텀 | Momentum candidates with scoring |
| Signals | `/signals.html` | 시그널 | Meta-labeling quality assessment |
| Cohesion | `/cohesion.html` | 군집성 | Theme co-movement analysis |
| Network | `/theme-graph.html` | 네트워크 | Theme-stock network visualization |

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy (async) |
| AI Chat | OpenRouter API (Gemini-2.0-Flash) |
| Frontend | Vanilla HTML/JS + Tailwind CSS + DaisyUI |
| Visualization | vis.js (network graphs), Chart.js |
| Stock Charts | Next.js app with lightweight-charts |
| i18n | localStorage-based KOR/ENG toggle |

### API Base URL Configuration

All frontend pages use dynamic API base URL for cross-machine access:
```javascript
const API_BASE = window.location.origin;  // Works from any host
```

### Running the Dashboard

```bash
# 1. Database Setup (first time only)
sudo -u postgres createdb krx_chat
sudo -u postgres psql -d krx_chat -f dashboard/backend/setup_db.sql
sudo -u postgres psql -d krx_chat -c "CREATE ROLE krxchat WITH LOGIN PASSWORD 'krxchat123';"
sudo -u postgres psql -d krx_chat -c "GRANT ALL PRIVILEGES ON DATABASE krx_chat TO krxchat;"
sudo -u postgres psql -d krx_chat -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO krxchat;"

# 2. Environment Setup
cd dashboard/backend
cp .env.example .env
# Edit .env with:
#   DATABASE_URL=postgresql+asyncpg://krxchat:krxchat123@127.0.0.1:5432/krx_chat
#   OPENROUTER_API_KEY=sk-or-v1-your-key

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Start Backend (port 8000)
export $(grep -v '^#' .env | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Stock Chart App (port 3001)
cd /mnt/nas/WWAI/stock-chart
npm run dev -- -p 3001
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://krxchat:krxchat123@127.0.0.1:5432/krx_chat` |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI chat | `sk-or-v1-xxx` |

---

## Internationalization (i18n)

### Language Toggle

All dashboard pages include a KOR/ENG toggle in the upper-right corner. Language preference is synchronized across pages via `localStorage('krx-dashboard-lang')`.

### Korean Terminology

| English | Korean | Context |
|---------|--------|---------|
| Sector Rotation | 섹터 로테이션 | Dashboard title |
| Co-movement | 군집성 | Theme synchronization |
| Breakout | 모멘텀 | Price momentum stage |
| Signal | 시그널 | Trading signal |
| Network | 네트워크 | Graph visualization |
| Theme | 테마 | Stock grouping |
| Cohesion | 군집성 | Fiedler-based measure |
| Early Breakout | 모멘텀 | Stage classification |
| Super Trend | 슈퍼트렌드 | Stage classification |
| High Priority | 눈여겨볼 주식 | Priority label |
| Pass Rate | 통과율 | Meta-labeling metric |

### Translation Implementation

```javascript
// Shared pattern across all pages
const translations = {
    ko: {
        title: 'KRX 섹터 로테이션 대시보드',
        subtitle: '3단계 프레임워크: 군집성 + 국면 + 추세',
        'nav.overview': '개요',
        'nav.breakout': '모멘텀',
        'nav.signals': '시그널',
        'nav.comovement': '군집성',
        'nav.network': '네트워크',
        // ... page-specific translations
    },
    en: { /* English translations */ }
};

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('krx-dashboard-lang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.innerHTML = translations[currentLang][key];
    });
}
```

---

## Dashboard Pages

### 1. Overview Page (`index.html`) - 개요

**Features:**
- KOR/ENG language toggle (upper right)
- Today's Market Snapshot banner (오늘의 시장 현황)
- Signal Quality card (시그널 품질)
- Top Momentum Candidates (모멘텀 종목)
- Theme Cohesion Health grid (테마 군집성)
- Focus Themes tags (관심 테마)
- Quick Actions navigation (빠른 실행)

**Korean Labels:**
| English | Korean |
|---------|--------|
| Themes Analyzed | 분석 테마 |
| Passed Filter | 필터 통과 |
| Breakout Candidates | 모멘텀 종목 |
| TIER 1 Themes | TIER 1 테마 |

### 2. Momentum Page (`breakout.html`) - 모멘텀

**Features:**
- Filterable momentum candidates table
- Score breakdown with stage distribution chart
- Expected returns by stage chart
- Chart icon links to stock chart app

**Korean Labels:**
| English | Korean |
|---------|--------|
| Data as of | 현재 |
| Early Breakout | 모멘텀 |
| Super Trend | 슈퍼트렌드 |
| High Priority | 눈여겨볼 주식 |
| Total Candidates | 종목수 |
| Stage Distribution | 단계별 분포 |
| Expected Returns | 단계별 기대수익 |
| Breakout Candidates | 관심주 |

### 3. Signals Page (`signals.html`) - 시그널

**Features:**
- Pass Rate gauge (통과율)
- Filter Funnel visualization (필터 퍼널)
- Signal Quality by Theme matrix (테마별 시그널)
- Model Performance metrics (모델 성과)

**Korean Labels:**
| English | Korean |
|---------|--------|
| Pass Rate | 통과율 |
| Signal Quality by Theme | 테마별 시그널 |
| Total Signals | 전체 시그널 |
| Passed | 통과 |
| Failed | 필터됨 |
| Accuracy | 정확도 |

### 4. Cohesion Page (`cohesion.html`) - 군집성

**Features:**
- Theme co-movement summary cards
- Top 5 Increasing/Decreasing trends
- Co-movement Gravity chart by theme
- Interpretation Guide (해석 가이드)

**Korean Labels:**
| English | Korean |
|---------|--------|
| Top 5 Increasing | 군집성 상승 TOP 5 |
| Top 5 Decreasing | 군집성 하락 TOP 5 |
| Co-movement Gravity | 테마별 군집성 강도 |
| Very Strong / Strong / Moderate / Weak | 매우 강함 / 강함 / 보통 / 약함 |
| Interpretation Guide | 해석 가이드 |

### 5. Network Page (`theme-graph.html`) - 네트워크

**Features:**
- KOR/ENG language toggle
- Partial word matching search with autocomplete (부분 일치 검색)
- Stock/Theme search with suggestions (250+ themes)
- Signal probability pre-loaded on stock nodes (Buy%)
- Theme nodes with Fiedler-based coloring
- Click stock → Opens stock chart in new tab

**Search Features:**
```javascript
// Partial word matching - type 2+ chars for suggestions
async function fetchSuggestions(query) {
    const response = await fetch(`${API_BASE}/api/network/search?q=${encodeURIComponent(query)}&limit=15`);
    // Returns both stocks AND themes with type badges (종목/테마)
}

// Examples:
// "반도" → 반도체 재료/부품, 반도체 장비, SFA반도체...
// "2차" → 2차전지, 2차전지(소재/부품)...
// "삼성" → 삼성전자, 삼성SDI, 삼성전기...
```

**Signal Probability Colors:**
```javascript
function getStockColor(signal, buyPct) {
    if (buyPct >= 70) return { bg: '#059669' }; // Strong Buy (적극 매수)
    if (buyPct >= 50) return { bg: '#10b981' }; // Buy (매수)
    if (buyPct >= 30) return { bg: '#f59e0b' }; // Neutral (중립)
    return { bg: '#ef4444' };                    // Avoid (회피)
}
```

**Korean Labels:**
| English | Korean |
|---------|--------|
| Search Stock or Theme | 종목 또는 테마 검색 |
| (partial match) | (부분 일치) |
| Selected Node | 선택된 노드 |
| Connected Themes | 연결된 테마 |
| Co-movement Gravity | 군집성 강도 |
| Stock Signal (Buy%) | 매수 시그널 (Buy%) |

### 6. AI Chat Widget (All Pages)

**Features:**
- Floating chat button (bottom-right corner, blue)
- Expandable chat panel (380x520px)
- Conversation history persistence (PostgreSQL)
- KOR/ENG language support (syncs with page language)
- Clickable links in responses (dashboard pages)
- Security-hardened (no algorithm disclosure)

**Activation:**
- Click blue chat button on any dashboard page
- Or access test page: `/chat-test.html`

**Example Questions:**
```
• 오늘 모멘텀 상위 종목은?
• TIER 1 테마는 무엇인가요?
• 군집성이 가장 강한 테마는?
• Which stocks have highest momentum?
```

**Security Rules (System Prompt):**
- ONLY answers questions about stocks, themes, market conditions
- NEVER explains internal algorithms (Fiedler, HMM, PageRank, etc.)
- Deflects algorithm questions: "이 정보는 내부 분석 시스템에서 제공됩니다"
- References dashboard pages with clickable links

**Korean Labels:**
| English | Korean |
|---------|--------|
| AI Investment Assistant | AI 투자 어시스턴트 |
| Sector Rotation Q&A | 섹터 로테이션 Q&A |
| New Chat | 새 대화 |
| Send | 전송 |
| Type your question | 질문을 입력하세요 |

### 7. CLI Chat Tool

**Location:** `dashboard/cli/krx_chat.py`

**Installation:**
```bash
cd dashboard/cli
./install.sh

# Add to ~/.bashrc or ~/.zshrc:
alias krx-chat='KRX_API_BASE=http://163.239.155.97:8000 python /path/to/krx_chat.py'
```

**Usage:**
```bash
krx-chat                           # Interactive mode
krx-chat "모멘텀 종목 추천해줘"      # Single question
krx-chat --new "새 대화"            # New conversation
krx-chat --history                  # Show history
krx-chat --clear                    # Clear conversation
krx-chat --api http://server:8000   # Custom API URL
```

**Features:**
- Rich terminal UI with colored panels
- Markdown rendering for responses
- Conversation persistence across sessions
- Interactive mode with `/new`, `/history`, `/quit` commands
- Configurable API endpoint via `--api` or `KRX_API_BASE` env var

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `KRX_API_BASE` | `http://localhost:8000` | Backend API URL |

---

## Stock Chart Integration

### Location
```
/mnt/nas/WWAI/stock-chart/
├── src/
│   ├── app/
│   │   ├── api/stock/route.ts    # Stock data API
│   │   └── stock/page.tsx        # Chart page component
│   └── lib/
│       └── tickers.ts            # Ticker mapping
├── package.json
└── next.config.js
```

### Stock Chart Features

| Feature | Description |
|---------|-------------|
| OHLCV Chart | Candlestick with volume |
| Moving Averages | MA10, MA20, MA60 |
| Bollinger Bands | Toggle BB overlay |
| RSI Indicator | Toggle RSI panel |
| Period Selection | 1M, 3M, 6M, 1Y, 5Y |
| Fundamentals | PER, PBR, EPS, BPS |
| Company Info | Description (KR/EN) |
| Related ETFs | ETFs containing the stock |
| Signal Probability | Buy/Neutral/Sell percentages |
| Language Toggle | Korean ↔ English |

### Dynamic Ticker Lookup

The stock chart supports dynamic ticker resolution from KRX database:

```typescript
// /src/app/api/stock/route.ts
async function lookupTickerFromDb(stockName: string): Promise<TickerLookupResult | null> {
    const stockDb = await loadKrxStockDb();

    // 1. Exact name match
    let stock = stockDb.find(s => s.name === stockName);

    // 2. Partial match
    if (!stock) {
        stock = stockDb.find(s => s.name.includes(stockName) || stockName.includes(s.name));
    }

    // 3. Ticker code match
    if (!stock && /^\d{6}$/.test(stockName)) {
        stock = stockDb.find(s => s.tickers === stockName);
    }

    if (stock) {
        const suffix = stock.market === 'KOSDAQ' ? '.KQ' : '.KS';
        return {
            ticker: stock.tickers.padStart(6, '0') + suffix,
            companyName: stock.name,
            market: stock.market
        };
    }
    return null;
}
```

### Display Format

Stock names display as: `회사명(티커코드.마켓)`

Examples:
- `삼성전자(005930.KS)`
- `에코프로에이치엔(383310.KQ)`

### Language Toggle Implementation

```typescript
// Translations object
const translations = {
    ko: {
        home: '← 홈',
        marketCap: '시가총액',
        overview: '개요',
        fundamentals: '펀더멘탈',
        // ... more translations
    },
    en: {
        home: '← Home',
        marketCap: 'Market Cap',
        overview: 'Overview',
        fundamentals: 'Fundamentals',
        // ... more translations
    }
};

// Language state with localStorage persistence
const [lang, setLang] = useState<'ko' | 'en'>('ko');

useEffect(() => {
    const saved = localStorage.getItem('stock-chart-lang');
    if (saved) setLang(saved);
}, []);

const toggleLang = () => {
    const newLang = lang === 'ko' ? 'en' : 'ko';
    setLang(newLang);
    localStorage.setItem('stock-chart-lang', newLang);
};
```

---

## Backend API Reference

### Overview Router (`/api/overview/`)

| Endpoint | Method | Response |
|----------|--------|----------|
| `/summary` | GET | `{regime, sentiment, signal_quality, date}` |
| `/top-picks` | GET | `[{ticker, score, themes}]` |
| `/theme-health` | GET | `[{theme, tier, fiedler, level}]` |

### Breakout Router (`/api/breakout/`)

| Endpoint | Method | Parameters | Response |
|----------|--------|------------|----------|
| `/candidates` | GET | `min_score`, `theme` | `[{ticker, score, regime_score, tech_score, theme_score, themes}]` |
| `/stages` | GET | - | `{stages: [{name, count}], priorities: [{name, count}], total}` |
| `/top-picks` | GET | `limit` | `{picks: [{ticker, score, strategy}], count}` |

### Network Router (`/api/network/`)

| Endpoint | Method | Parameters | Response |
|----------|--------|------------|----------|
| `/search` | GET | `q`, `limit` | `{stocks: [{name, ticker, buy_pct}], themes: [{theme, fiedler}]}` |
| `/graph-data` | GET | `stock`, `theme`, `depth` | `{nodes: [], edges: [], stats: {}}` |
| `/stock-themes` | GET | `name` | `{themes: [{theme, fiedler, tier}]}` |

### Chat Router (`/api/chat/`)

| Endpoint | Method | Parameters | Response |
|----------|--------|------------|----------|
| `/message` | POST | `{message, conversation_id?, language}` | `{response, conversation_id, message_id}` |
| `/history/{id}` | GET | - | `{id, title, messages: [{role, content, created_at}]}` |
| `/conversations` | GET | `limit` | `[{id, title, created_at, message_count}]` |
| `/new` | POST | - | `{conversation_id, created_at}` |
| `/health` | GET | - | `{status, openrouter_configured, qa_document_loaded, model}` |

**Chat Database Schema:**
```sql
-- PostgreSQL tables
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    title VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20),  -- 'user' or 'assistant'
    content TEXT,
    created_at TIMESTAMP
);
```

### Search API with Partial Matching

```python
# /api/network/search - Fuzzy/partial word matching
@router.get("/search")
async def search_all(q: str, limit: int = 20):
    """
    Search stocks and themes with partial matching.
    Examples:
    - "반도" → matches "반도체 재료/부품", "SFA반도체"
    - "2차" → matches "2차전지", "2차전지(소재/부품)"
    """

def fuzzy_match(query: str, text: str) -> bool:
    query = query.lower().strip()
    text = text.lower()
    if query in text:
        return True
    # Multi-word matching
    words = query.split()
    if len(words) > 1:
        return all(word in text for word in words)
    return False
```

### Signal Probability Integration

```python
# Pre-load signal probability from AutoML predictions
SIGNAL_PROB_DIR = Path("/mnt/nas/AutoGluon/AutoML_Krx/predictedProbability")

def get_signal_probability(stock_name: str) -> dict:
    file_path = SIGNAL_PROB_DIR / f"{stock_name}_pp.csv"
    if file_path.exists():
        df = pd.read_csv(file_path)
        last_row = df.iloc[-1]
        return {
            "sell": float(last_row.get('-1', 0)) * 100,
            "neutral": float(last_row.get('0', 0)) * 100,
            "buy": float(last_row.get('1', 0)) * 100
        }
    return {"sell": 0, "neutral": 0, "buy": 0}
```

### Helper Functions

```python
# Safe float conversion for JSON serialization
def safe_float(value):
    """Convert to float, return 0 if NaN/None"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return float(value)
```

---

## Key Data Sources

| Data Type | Location | Update Frequency |
|-----------|----------|------------------|
| Regime Detection | `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/` | Daily |
| Super Trend Picks | `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/` | Daily |
| Theme Cohesion | Computed by `analyze_naver_theme_cohesion.py` | On-demand |
| Meta-labeling Model | `./backtest/models/meta_labeler_xgboost_*.pkl` | Monthly |
| KRX Stock Database | `/mnt/nas/AutoGluon/AutoML_Krx/DB/db_final.csv` | Daily |
| Fundamental Data | `/mnt/nas/AutoGluon/AutoML_Krx/DB/fundamental_data.json` | Daily |
| Company Overview | `/mnt/nas/AutoGluon/AutoML_Krx/DB/company_overview.csv` | Weekly |
| ETF Mapping | `/mnt/nas/AutoGluon/AutoML_KrxETF/DB/domestic_ticker_to_etfs_map.json` | Weekly |
| **Chat QA Context** | `./analysis/QA_investment_questions_*.md` | On-demand |
| **Chat History** | PostgreSQL `krx_chat` database | Real-time |

---

## Replication Guide (For Other Markets)

### To create a USA Sector Rotation Dashboard:

#### 1. Data Layer Changes

| KRX Component | USA Equivalent |
|---------------|----------------|
| `db_final.csv` | S&P 500 / Russell constituents |
| Naver themes | GICS sectors / ETF holdings |
| `.KS` / `.KQ` suffix | No suffix needed for US tickers |
| Korean company names | English names only |
| Won (₩) formatting | Dollar ($) formatting |
| Signal probability dir | Adapt prediction output path |

#### 2. Backend Modifications

```python
# Change market suffix logic
def get_yahoo_ticker(symbol: str) -> str:
    # KRX: return f"{code}.KS" or f"{code}.KQ"
    # USA: return symbol directly (no suffix)
    return symbol

# Change currency formatting
def format_price(price: float, lang: str) -> str:
    # KRX: return f"{price:,.0f}원"
    # USA: return f"${price:,.2f}"
```

#### 3. Frontend i18n Adaptation

```javascript
// For USA dashboard - English only (no toggle needed)
// OR keep toggle for multilingual support

const translations = {
    en: {
        title: 'USA Sector Rotation Dashboard',
        subtitle: 'Three-Layer Framework: Co-movement + Regime + Trend',
        'nav.overview': 'Overview',
        'nav.breakout': 'Momentum',
        'nav.signals': 'Signals',
        'nav.comovement': 'Cohesion',
        'nav.network': 'Network',
        // ... US-specific translations
    },
    // Optional: Add Spanish, Chinese, etc.
};

// Currency display
const formatPrice = (price) => '$' + price.toLocaleString('en-US');

// Market cap units
const formatMarketCap = (cap) => {
    if (cap >= 1e12) return (cap / 1e12).toFixed(1) + 'T';
    if (cap >= 1e9) return (cap / 1e9).toFixed(1) + 'B';
    return (cap / 1e6).toFixed(1) + 'M';
};
```

#### 4. i18n Key Mapping

When adapting translations, map these KRX-specific terms:

| KRX Key | KRX Korean | USA Equivalent |
|---------|------------|----------------|
| `nav.breakout` | 모멘텀 | Momentum |
| `nav.comovement` | 군집성 | Cohesion |
| `summary.earlyBreakout` | 모멘텀 | Momentum |
| `summary.superTrend` | 슈퍼트렌드 | Super Trend |
| `summary.highPriority` | 눈여겨볼 주식 | High Priority |
| `legend.veryStrong` | 매우 강함 | Very Strong |

#### 5. Stock Chart App Changes

```typescript
// tickers.ts - Remove .KS/.KQ suffix logic
export function getYahooTicker(symbol: string): string {
    return symbol;  // US tickers don't need suffix
}

// Remove Korean language option OR add other languages
const translations = {
    en: {
        marketCap: 'Market Cap',
        trillion: 'T',
        billion: 'B',
    }
};

// localStorage key should be unique per market
localStorage.setItem('usa-dashboard-lang', lang);
```

#### 6. Theme/Sector Mapping

| KRX (Naver Themes) | USA Equivalent |
|--------------------|----------------|
| 테마 (Theme) | Sector / Industry |
| 2차전지 | Electric Vehicles |
| 반도체 | Semiconductors |
| 방위산업 | Defense |
| AI/인공지능 | AI / Artificial Intelligence |

---

## Available Skills

### `/sector-rotation-qa`
Answer investment questions from current analysis data.

### `/calculate-fiedler`
Compute Fiedler eigenvalue for specified themes.

### `/run-meta-labeling`
Apply meta-labeling model to filter current signals.

### `/find-key-players`
Calculate PageRank centrality for theme key players.

### `/early-breakout-scan`
Find Early Breakout candidates (Transition + Above BB).

---

## Agent Definitions

### 1. Investment Q&A Agent (`investment-qa-agent`)

**Purpose**: Answer investment questions from pre-computed analysis data

**Capabilities**:
- Stock selection queries (top picks, sector leaders)
- Theme analysis (cohesion, TIER classification)
- Risk assessment (filtered signals, momentum levels)
- Historical performance reference
- Portfolio construction guidance

**Data Files Required**:
```
./data/actionable_tickers_YYYYMMDD.csv
./data/consolidated_ticker_analysis_YYYYMMDD.json
./data/tier1_key_players_YYYYMMDD.json
./data/meta_labeling_results_YYYYMMDD.csv
```

### 2. Fiedler Calculation Agent (`fiedler-calc-agent`)

**Purpose**: Compute theme cohesion using Fiedler eigenvalue

**Method**:
1. Load theme member stocks from Naver theme data
2. Fetch price data for lookback window (default: 30 days)
3. Calculate correlation matrix
4. Build network graph (threshold: 0.25)
5. Compute Laplacian matrix
6. Extract 2nd smallest eigenvalue (Fiedler value)

**Parameters**:
- `THRESHOLD`: 0.25 (correlation threshold for edge creation)
- `WINDOW`: 20 (rolling correlation window)
- `MIN_STOCKS`: 3 (minimum stocks for valid theme)
- `LOOKBACK_DAYS`: 30 (price data lookback)

### 3. Meta-Labeling Agent (`meta-label-agent`)

**Purpose**: Filter trading signals using trained XGBoost model

**Model**: `./backtest/models/meta_labeler_xgboost_20251113.pkl`

**19 Features**:
```python
FEATURE_NAMES = [
    'signal_type_tier', 'signal_type_cohesion', 'signal_type_leadership',
    'signal_strength', 'tier', 'is_tier1', 'is_tier2',
    'leadership_gap', 'current_fiedler', 'week_before_fiedler',
    'fiedler_change', 'fiedler_pct_change',
    'day_of_week', 'day_of_month', 'month', 'quarter',
    'is_month_end', 'is_quarter_end', 'n_stocks'
]
```

**Performance**: Accuracy 80.44%, AUC 0.865

### 4. Key Player Agent (`key-player-agent`)

**Purpose**: Identify central stocks within themes using PageRank

### 5. Early Breakout Scanner (`breakout-scanner-agent`)

**Purpose**: Find stocks in Early Breakout stage

**Criteria**:
- Regime: Transition (from Bear to Bull)
- Price: Above Bollinger Band (220, 2)
- Scoring: Regime (40) + Tech (30) + Theme (up to 30)

---

## Common Workflows

### Daily Morning Analysis
```
1. Check regime report: /mnt/nas/AutoGluon/AutoML_Krx/regime/results/
2. Run: /early-breakout-scan
3. Run: /run-meta-labeling --current
4. Run: /find-key-players --tier1-all
5. Open dashboard: http://localhost:8000/
```

### Weekly Review
```
1. Run: /calculate-fiedler --all-tier1
2. Compare with previous week's cohesion
3. Generate: /integrated-report
4. Save to: ./analysis/YYYY-MM-DD.md
```

---

## Error Handling

### NaN Values in JSON
```python
# Always use safe_float() when serializing to JSON
import math
def safe_float(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return float(value)
```

### Stock Not Found
Dynamic lookup from database handles most cases. Fallback to partial name match.

### Theme Not Found
Check Naver theme naming (Korean) vs internal naming conventions.

---

## References

- Dashboard Backend: `./dashboard/backend/`
- Dashboard Frontend: `./dashboard/frontend/`
- Stock Chart App: `/mnt/nas/WWAI/stock-chart/`
- Analysis Reports: `./analysis/`
- Meta-labeling Reports: `./reports/`

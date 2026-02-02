# KRX Breakout Scanner 필터링 방법 가이드

> 마지막 업데이트: 2026-02-02 (장기추세돌파 BB 필터 추가)

## 개요

KRX Breakout Scanner (`breakout.html`)는 네 가지 필터링 방법을 사용하여 투자 후보를 선별합니다:

1. **Daily Top Performers (AutoML)** - AutoML 기반 일일 상위 종목
2. **SuperTrend Candidates** - 슈퍼트렌드 종목
3. **Long Term Trend Breakout (장기추세돌파)** - BB(220, 2.0) 상단 돌파 종목
4. **Breakout Candidates** - 브레이크아웃 후보 전체

---

## 1. Daily Top Performers (AutoML)

### 설명
AutoML 파이프라인에서 생성된 일일 최고 성과 종목입니다. 복합 점수(Composite Score)를 기반으로 상위 10개 종목을 선정합니다.

### 필터링 기준
| 지표 | 설명 | 가중치 |
|------|------|--------|
| Regime Score | 시장 국면 점수 | 40% |
| Technical Score | 기술적 지표 점수 | 30% |
| Momentum Score | 모멘텀 점수 | 20% |
| PageRank | 테마 내 중요도 | 10% |

### 데이터 소스

```
/mnt/nas/AutoGluon/AutoML_Krx/Backtest/Rankings/daily_summary_{DATE}.json
```

### 소스 파일

| 파일 | 위치 | 역할 |
|------|------|------|
| `daily_summary_{DATE}.json` | `/mnt/nas/AutoGluon/AutoML_Krx/Backtest/Rankings/` | 일일 요약 데이터 |
| `breakout.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend/routers/` | API 엔드포인트 |

### API 엔드포인트

```
GET /api/breakout/daily-summary
GET /api/breakout/daily-summary?date=2026-01-30
```

### 응답 예시

```json
{
  "date": "2026-01-30",
  "total_tickers": 713,
  "top_performers": [
    {
      "rank": 1,
      "ticker": "에코프로에이치엔",
      "name": "에코프로에이치엔",
      "sector": "2차전지",
      "composite_score": 92.5,
      "regime": "Transition",
      "signals": ["UCS_Green", "LRS_Green"]
    }
  ],
  "hidden_gems": [...]
}
```

### 업데이트 방법

```bash
# AutoML 일일 스케줄러 실행 (자동)
python3 /mnt/nas/AutoGluon/AutoML_Krx/daily_krx_scheduler.py

# 수동 업데이트
python3 /mnt/nas/AutoGluon/AutoML_Krx/Backtest/generate_daily_summary.py 2026-01-30
```

---

## 2. SuperTrend Candidates

### 설명
**Bull Quiet 국면**에서 **Bollinger Band 상단을 돌파**한 강한 모멘텀 종목입니다. 지속적인 상승 추세를 보이는 종목을 식별합니다.

### 필터링 기준

| 조건 | 설명 | 임계값 |
|------|------|--------|
| **Regime** | 시장 국면 | Bull Quiet |
| **BB Position** | 볼린저밴드 위치 | Price > Upper BB (220, 2) |
| **Momentum** | 모멘텀 점수 | > 0.1 (10%) |
| **Trend Strength** | 추세 강도 | > 0 |

### 분류 로직

```python
# trend_classifier.py 핵심 로직
if regime == "Bull Quiet" and price > upper_bb:
    trend_stage = "Super Trend"
```

### 데이터 파이프라인

```
1. regime_prob.csv (Regime 분류)
   /mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/
        ↓
2. trend_classifier.py (BB + Regime → Stage)
   /mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/scripts/
        ↓
3. classified_trends_{DATE}.csv
   /mnt/nas/AutoGluon/AutoML_Krx/superTrend/
        ↓
4. actionable_tickers_{DATE}.csv (stage = "Super Trend" 필터)
   /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/
```

### 소스 파일

| 파일 | 위치 | 역할 |
|------|------|------|
| `trend_classifier.py` | `/mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/scripts/` | Trend Stage 분류 (핵심) |
| `run_analysis.py` | `/mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/` | 오케스트레이터 |
| `classified_trends_{DATE}.csv` | `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/` | 분류 결과 |
| `daily_price_update.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts/` | actionable_tickers 생성 |
| `breakout.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend/routers/` | API 엔드포인트 |

### API 엔드포인트

```
GET /api/breakout/supertrend-candidates
GET /api/breakout/supertrend-candidates?limit=30
```

### 응답 예시

```json
{
  "candidates": [
    {
      "ticker": "미래에셋벤처투자",
      "score": 78,
      "stage": "Super Trend",
      "priority": "HIGH",
      "strategy": "Super Trend (Bull Quiet)",
      "themes": "['스페이스X(SpaceX)', '창투사']"
    }
  ],
  "count": 30,
  "total_supertrend": 174,
  "expected_return": "+2.10% (20D avg)",
  "note": "Super Trend = Strong momentum in bull regime"
}
```

### 업데이트 방법

```bash
# Step 1: classified_trends 생성
/mnt/nas/AutoGluon/AutoML_Krx/run_daily_theme_analysis.sh 2026-01-30

# Step 2: actionable_tickers 생성
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts
python3 daily_price_update.py --date 2026-01-30

# 또는 전체 파이프라인 실행
python3 /mnt/nas/AutoGluon/AutoML_Krx/daily_krx_scheduler.py
```

---

## 3. Long Term Trend Breakout (장기추세돌파)

### 설명
**220일 볼린저밴드(BB) 상단을 돌파**한 종목입니다. 장기 추세 전환 신호로, 전일에는 BB 상단 아래에 있다가 당일 BB 상단을 상향 돌파한 종목을 식별합니다.

### 필터링 기준

| 조건 | 설명 | 임계값 |
|------|------|--------|
| **BB Period** | 볼린저밴드 기간 | 220일 |
| **BB Multiplier** | 표준편차 배수 | 2.0 |
| **Crossover** | 돌파 조건 | 전일: Price ≤ Upper BB → 당일: Price > Upper BB |

### 분류 로직

```python
# filter_bb.py 핵심 로직
def filter_bb(data, isDate, period=220):
    df = get_bb(data, period)  # BB(220, 2.0) 계산

    yesterday = df.iloc[-2]
    today = df.iloc[-1]

    # Crossover 조건: 전일 BB 상단 이하 → 당일 BB 상단 돌파
    crossover = (yesterday['close'] <= yesterday['bb_upper']) and \
                (today['close'] > today['bb_upper'])

    return crossover
```

### 데이터 파이프라인

```
1. Daily Price Data
   /mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED/*.csv
        ↓
2. filter_bb.py (BB(220, 2.0) Crossover 체크)
   /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/
        ↓
3. bb_filtered_tickers.json
   /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/Filter/
        ↓
4. Dashboard API
   GET /api/breakout/bb-crossover
```

### 소스 파일

| 파일 | 위치 | 역할 |
|------|------|------|
| `filter_bb.py` | `/mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/` | BB Crossover 필터 (핵심) |
| `libPath.json` | `/mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/` | 날짜/마켓 설정 |
| `bb_filtered_tickers.json` | `/mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/Filter/` | 필터 결과 |
| `breakout.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend/routers/` | API 엔드포인트 |

### API 엔드포인트

```
GET /api/breakout/bb-crossover
GET /api/breakout/bb-crossover?date=2026-02-02
```

### 응답 예시

```json
{
  "date": "2026-02-02",
  "tickers": [
    {
      "ticker": "천일고속",
      "themes": "[]",
      "signal": "BB Upper Crossover",
      "bb_setting": "BB(220, 2.0)"
    },
    {
      "ticker": "동아지질",
      "themes": "['철도', 'GTX', '재난/안전']",
      "signal": "BB Upper Crossover",
      "bb_setting": "BB(220, 2.0)"
    }
  ],
  "count": 17,
  "description": "Tickers that crossed above BB(220, 2.0) upper band",
  "note": "Yesterday: below or at upper BB → Today: above upper BB"
}
```

### 업데이트 방법

```bash
# libPath.json 업데이트 (날짜 설정)
echo '{"isMkt": "Krx", "isDate": "2026-02-02"}' > /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/libPath.json

# BB 필터 실행
cd /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB
python filter_bb.py

# 또는 daily_update_all.sh 실행 (Step 12에서 자동 실행)
bash /mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh
```

### 투자 의미

- **장기 추세 전환 신호**: 220일 BB 상단 돌파는 장기 상승 추세 시작을 의미
- **모멘텀 확인**: SuperTrend와 함께 확인하면 신뢰도 증가
- **진입 시점**: 돌파 당일 또는 다음날 진입 검토

---

## 4. Breakout Candidates

### 설명
**전체 브레이크아웃 후보** 목록입니다. 4가지 Stage로 분류되며, 점수와 우선순위에 따라 정렬됩니다.

### Stage 분류 기준

| Stage | Regime 조건 | BB 조건 | 기대수익률 (20D) | 추천 |
|-------|------------|---------|-----------------|------|
| **Early Breakout** | Transition / Ranging | Price > Upper BB | +7.93% | BUY |
| **Super Trend** | Bull Quiet | Price > Upper BB | +2.10% | BUY |
| **Burgeoning** | Transition / Ranging | Price < Upper BB | +1.50% | HOLD |
| **Healthy Correction** | Bull Quiet | Price < Upper BB | +1.20% | HOLD |

### Bollinger Band 설정

```python
BB_PERIOD = 220   # 220일 이동평균
BB_STD = 2        # 표준편차 2배

# Deviation_BB = (Price - Upper_BB) / Upper_BB
# 양수 = BB 상단 위, 음수 = BB 상단 아래
```

### 점수 계산 (Score)

```python
# Regime 점수 (40점 만점)
REGIME_SCORE = {
    "Transition": 40,      # 전환기 (최고)
    "Bull Quiet": 30,      # 조용한 상승
    "Ranging": 20,         # 횡보
    "Bull Volatile": 15,   # 변동성 상승
    "Bear Quiet": 10,      # 조용한 하락
    "Bear Volatile": 0     # 변동성 하락
}

# Stage 점수 (30점 만점)
STAGE_SCORE = {
    "Early Breakout": 30,  # 초기 돌파 (최고)
    "Super Trend": 25,     # 슈퍼트렌드
    "Burgeoning": 20,      # 성장 초기
    "Healthy Correction": 10  # 건강한 조정
}

# BB 보너스 (최대 10점)
bb_bonus = min(int(deviation_bb * 100), 10)

# PageRank 보너스 (최대 10점)
pagerank_bonus = min(int(pagerank * 10), 10)

# 최종 점수
total_score = regime_score + stage_score + bb_bonus + pagerank_bonus
```

### 우선순위 (Priority)

| Priority | 조건 | 의미 |
|----------|------|------|
| **HIGH** | Early Breakout + Transition | 최우선 매수 |
| **HIGH** | Super Trend + Bull Quiet | 모멘텀 추종 |
| **MEDIUM** | Early Breakout, Super Trend, Burgeoning | 관심 종목 |
| **LOW** | Healthy Correction, 기타 | 관망 |

### 제외 필터

```python
# 제외 패턴 (SPAC, 우선주)
EXCLUDED_PATTERNS = ["스팩", "SPAC", "우B", "우선주"]
```

### 데이터 파이프라인

```
1. Daily Price Data
   /mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED/*.csv
        ↓
2. UCS_LRS Signal Filter (Green만)
   /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_{DATE}.json
        ↓
3. trend_classifier.py (Regime + BB → Stage)
        ↓
4. classified_trends_{DATE}.csv
   /mnt/nas/AutoGluon/AutoML_Krx/superTrend/
        ↓
5. daily_price_update.py (점수 계산, 우선순위 부여)
        ↓
6. actionable_tickers_{DATE}.csv
   /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/
        ↓
7. Dashboard API
```

### 소스 파일

| 파일 | 위치 | 역할 |
|------|------|------|
| `trend_classifier.py` | `/mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/scripts/` | Trend Stage 분류 |
| `run_analysis.py` | `/mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/` | 파이프라인 오케스트레이터 |
| `daily_price_update.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts/` | 점수 계산 + actionable_tickers 생성 |
| `breakout.py` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend/routers/` | API 엔드포인트 |
| `breakout.html` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/frontend/` | 프론트엔드 UI |

### API 엔드포인트

```
GET /api/breakout/candidates
GET /api/breakout/candidates?stage=Early%20Breakout
GET /api/breakout/candidates?priority=HIGH
GET /api/breakout/candidates?min_score=70
GET /api/breakout/candidates?theme=2차전지
GET /api/breakout/candidates?limit=50
```

### 응답 예시

```json
{
  "candidates": [
    {
      "ticker": "에코프로에이치엔",
      "strategy": "Early Breakout (Transition)",
      "score": 85,
      "stage": "Early Breakout",
      "themes": "['황사/미세먼지', '코리아 밸류업 지수']",
      "priority": "HIGH"
    }
  ],
  "count": 50,
  "total_available": 713,
  "stage_distribution": {
    "Healthy Correction": 300,
    "Burgeoning": 212,
    "Super Trend": 174,
    "Early Breakout": 27
  },
  "date": "20260130"
}
```

### 업데이트 방법

```bash
# 전체 파이프라인 실행 (권장)
python3 /mnt/nas/AutoGluon/AutoML_Krx/daily_krx_scheduler.py

# 또는 개별 단계 실행:

# Step 1: Regime 분석 + classified_trends 생성
/mnt/nas/AutoGluon/AutoML_Krx/run_daily_theme_analysis.sh 2026-01-30

# Step 2: actionable_tickers 생성
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts
python3 daily_price_update.py --date 2026-01-30
```

---

## 전체 데이터 흐름 요약

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AutoML_Krx Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Daily Price Data ──────────────────────────────────────────────────│
│  /KRXNOTTRAINED/*.csv                                               │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────┐    ┌─────────────────┐                         │
│  │ Regime Detector │    │ UCS_LRS Filter  │                         │
│  │ (6 Regimes)     │    │ (Green Signal)  │                         │
│  └────────┬────────┘    └────────┬────────┘                         │
│           │                      │                                   │
│           ▼                      ▼                                   │
│  ┌─────────────────────────────────────────┐                        │
│  │         trend_classifier.py             │                        │
│  │  Regime + BB (220,2) → Trend_Stage      │                        │
│  │  • Super Trend                          │                        │
│  │  • Early Breakout                       │                        │
│  │  • Burgeoning                           │                        │
│  │  • Healthy Correction                   │                        │
│  └────────────────┬────────────────────────┘                        │
│                   │                                                  │
│                   ▼                                                  │
│  classified_trends_{DATE}.csv                                        │
│  /superTrend/                                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Sector-Rotation-KRX Pipeline                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────┐                        │
│  │       daily_price_update.py             │                        │
│  │  • SPAC/우선주 제외                      │                        │
│  │  • Stage 필터 (4개만)                    │                        │
│  │  • Score 계산                           │                        │
│  │  • Priority 부여                         │                        │
│  └────────────────┬────────────────────────┘                        │
│                   │                                                  │
│                   ▼                                                  │
│  actionable_tickers_{DATE}.csv                                       │
│  /data/                                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Dashboard API                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  /api/breakout/daily-summary      → Daily Top Performers             │
│  /api/breakout/supertrend-candidates → SuperTrend Candidates         │
│  /api/breakout/candidates         → Breakout Candidates (All)        │
│  /api/breakout/stages             → Stage Distribution               │
│  /api/breakout/top-picks          → Top Early Breakout               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend (breakout.html)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │ Daily Top         │  │ SuperTrend        │  │ Breakout         │ │
│  │ Performers        │  │ Candidates        │  │ Candidates       │ │
│  │ (AutoML)          │  │ 🚀                │  │ (Full Table)     │ │
│  └───────────────────┘  └───────────────────┘  └──────────────────┘ │
│                                                                      │
│  URL: http://163.239.155.97:8000/breakout.html                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 빠른 참조

### 주요 파일 위치

| 구분 | 파일 | 경로 |
|------|------|------|
| **입력** | 일일 가격 | `/mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED/` |
| **입력** | Regime 결과 | `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/regime_prob.csv` |
| **중간** | classified_trends | `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/classified_trends_{DATE}.csv` |
| **출력** | actionable_tickers | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/actionable_tickers_{DATE}.csv` |
| **출력** | daily_summary | `/mnt/nas/AutoGluon/AutoML_Krx/Backtest/Rankings/daily_summary_{DATE}.json` |

### 일일 업데이트 명령어

```bash
# 전체 자동 실행 (권장) - 11단계 파이프라인
bash /mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh

# 또는 스케줄러 실행
python3 /mnt/nas/AutoGluon/AutoML_Krx/daily_krx_scheduler.py

# 대시보드 재시작
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend
pkill -f "uvicorn.*8000" && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```

---

## Daily Routine 통합 (daily_update_all.sh)

> 파일 위치: `/mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh`

### 전체 11단계 파이프라인

| Step | 작업 | 설명 |
|------|------|------|
| 1 | Price Update | KRXNOTTRAINED 가격 데이터 업데이트 |
| 2 | Remote Sync | 원격 서버에 가격 데이터 동기화 |
| 3 | Filter | 기본 필터 처리 |
| 4 | UCS-LRS | UCS-LRS 분석 (1시간 이상) |
| 5 | Research | 연구 스크립트 (18:00 이후) |
| 6 | Netbuy | 순매수 데이터 업데이트 |
| 7 | Buy or Not | 매수/비매수 DB 업데이트 |
| 8 | Daily Reports | 일일 보고서 생성 |
| **9** | **Regime Analysis** | **classified_trends 생성 (신규)** |
| **10** | **Copy Trends** | **superTrend 디렉토리에 복사 (신규)** |
| **11** | **Frontend Data** | **actionable_tickers 생성 (신규)** |

### 프론트엔드 필터링 관련 신규 단계 (9-11)

#### Step 9: Regime/Theme Analysis
```bash
# 실행 파일
python /mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/run_analysis.py --date $(date +%Y-%m-%d)

# 출력
/mnt/nas/AutoGluon/AutoML_Krx/regime/results/classified_trends_{DATE}.csv
```

#### Step 10: Copy to superTrend
```bash
# classified_trends를 superTrend 디렉토리로 복사
cp /mnt/nas/AutoGluon/AutoML_Krx/regime/results/classified_trends_{DATE}.csv \
   /mnt/nas/AutoGluon/AutoML_Krx/superTrend/
```

#### Step 11: Generate actionable_tickers
```bash
# 실행 파일
python /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts/daily_price_update.py

# 출력
/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/actionable_tickers_{DATE}.csv
/mnt/nas/AutoGluon/AutoML_Krx/superTrend/actionable_tickers_{DATE}.csv
```

### 자동 실행 (Cron)

```bash
# crontab -e
# 매일 18:30 KST 실행 (시장 마감 후)
30 18 * * 1-5 /mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh >> /mnt/nas/AutoGluon/AutoML_Krx/logs/cron_daily.log 2>&1
```

### 로그 확인

```bash
# 오늘 로그 확인
tail -100 /mnt/nas/AutoGluon/AutoML_Krx/logs/daily_update_$(date +%Y%m%d).log

# 프론트엔드 데이터 생성 확인
ls -la /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/actionable_tickers_*.csv | tail -5
```

### 현재 통계 (2026-01-30 기준)

| Stage | 종목 수 | 비율 |
|-------|--------|------|
| Early Breakout | 27 | 3.8% |
| Super Trend | 174 | 24.4% |
| Burgeoning | 212 | 29.7% |
| Healthy Correction | 300 | 42.1% |
| **총계** | **713** | 100% |

---

## 참고 문서

- [AI Instruction (SuperTrend)](/mnt/nas/AutoGluon/AutoML_Krx/superTrend/ai_instruction.md)
- [CLAUDE.md (KRX)](/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/CLAUDE.md)
- [Regime Analysis Skill](/mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis/SKILL.md)

# Investment Questions & Answers (투자 Q&A)
**Based on Analysis Date**: 2026-01-29

**Dashboard**: http://localhost:8000 (KOR/ENG 언어 전환 지원)

---

## Terminology / 용어 가이드
| English | Korean | Description |
|---------|--------|-------------|
| Cohesion | 군집성 | 테마 내 종목 동조화 강도 |
| Breakout | 모멘텀 | 상승 추세 + 매수 조건 충족 종목 |
| Signal | 시그널 | 분석 시스템 품질 필터 통과 신호 |
| Key Player | 핵심 종목 | 테마 내 중심성이 높은 종목 |
| TIER | 티어 | 테마 품질 등급 |

---

## Stock Selection Questions

### Q1: Which stocks have the highest momentum potential today? (오늘 모멘텀 상위 종목은?)
**Answer**: 분석 시스템 기준 모멘텀 상위 종목

| Rank | Ticker | Score | Momentum Strength | Key Themes |
|------|--------|-------|------------|------------|
| 1 | 포스코퓨처엠 | 90 | 3.09% | 리튬, 2차전지, 밸류업 |
| 2 | 강원에너지 | 90 | 1.21% | 2차전지, 리튬, 전기차, 원자력 |
| 3 | 신흥에스이씨 | 80 | 4.31% | 전기차 화재방지, 2차전지 |
| 4 | 에이티넘인베스트 | 75 | 4.74% | 창투사, 두나무, 가상화폐 |
| 5 | 현우산업 | 75 | 4.33% | PCB(FPCB 등) |

**Source**: `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/daily_top_picks_2026-01-28.csv`

---

### Q2: What are the top picks in 2차전지/EV battery sector?
**Answer**: 3 stocks with strong EV/battery exposure

| Ticker | Score | Specific Themes |
|--------|-------|-----------------|
| 포스코퓨처엠 | 90 | 리튬, 2차전지, 2차전지(소재/부품) |
| 강원에너지 | 90 | 2차전지(장비), 리튬, 전기차 |
| 신흥에스이씨 | 80 | 전기차 화재 방지, 2차전지(소재/부품) |

---

### Q3: Which stocks are central players in currently trending themes?
**Answer**: Top 10 by Centrality centrality in TIER 1 themes

| Ticker | Centrality | Theme | Role |
|--------|----------|-------|------|
| LG유플러스 | 26.4 | 통신 | Theme leader |
| SK텔레콤 | 21.3 | 통신 | Major player |
| KT | 20.3 | 통신 | Major player |
| LG | 19.9 | 통신, 스페이스X | Multi-theme hub |
| SK | 19.8 | 통신, 증권 | Multi-theme hub |
| 미래에셋증권 | 12.1 | 증권, 스페이스X | Cross-sector |
| 우리금융지주 | 11.2 | 은행 | Sector leader |
| 하나금융지주 | 10.4 | 은행 | Major player |
| 기업은행 | 10.3 | 은행 | Major player |
| 신한지주 | 10.1 | 은행 | Major player |

**Source**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/tier1_key_players_20260129.json`

---

### Q4: Which telecom stocks have highest network influence?
**Answer**: 통신 theme Centrality ranking

| Rank | Ticker | Centrality | Notes |
|------|--------|----------|-------|
| 1 | LG유플러스 | 26.4 | Highest centrality |
| 2 | SK텔레콤 | 21.3 | Strong position |
| 3 | KT | 20.3 | Stable player |
| 4 | LG | 19.9 | Holding company exposure |
| 5 | SK | 19.8 | Holding company exposure |

---

### Q5: Which bank stocks are most influential in the sector?
**Answer**: 은행 theme Centrality ranking

| Rank | Ticker | Centrality | Notes |
|------|--------|----------|-------|
| 1 | 우리금융지주 | 11.2 | Top bank holding |
| 2 | 하나금융지주 | 10.4 | Major player |
| 3 | 기업은행 | 10.3 | Government-backed |
| 4 | 신한지주 | 10.1 | Established player |
| 5 | iM금융지주 | 10.0 | Regional strength |
| 6 | BNK금융지주 | 9.1 | Regional bank |
| 7 | 제주은행 | 9.1 | Regional bank |

---

## Theme/Sector Analysis Questions

### Q6: Which themes have strongest cohesion? (군집성이 가장 강한 테마는?)
**Answer**: 군집성 지표 기준 순위 (높을수록 군집성 강함)

| Rank | Theme | Cohesion | Interpretation |
|------|-------|---------|----------------|
| 1 | 은행 | 3.728 | Very strong - stocks move together |
| 2 | 방위산업/전쟁 및 테러 | 3.629 | Very strong cohesion |
| 3 | 증권 | 3.518 | Very strong cohesion |
| 4 | 전력설비 | 2.703 | Strong cohesion |
| 5 | 통신 | 0.700 | Moderate cohesion |
| 6 | 스페이스X(SpaceX) | 0.566 | Weaker cohesion |

**군집성 해석 가이드**:
- Cohesion > 3.0: 매우 강함 (테마 내 높은 상관관계)
- Cohesion 1.0-3.0: 강함
- Cohesion 0.5-1.0: 보통
- Cohesion < 0.5: 약함 (분산된 테마)

**Source**: Computed this session using `analyze_naver_theme_cohesion.py` methodology

---

### Q7: Which TIER 1 themes should I focus on? (어떤 TIER 1 테마에 집중해야 하나?)
**Answer**: 메타 레이블링 필터 통과 6개 테마

| Theme | Cohesion | Confidence | Recommendation |
|-------|---------|------------|----------------|
| 통신 | 0.700 | 62.5% | Focus - stable sector rotation play |
| 방위산업/전쟁 및 테러 | 3.629 | 62.5% | Focus - strong cohesion |
| 전력설비 | 2.703 | 62.5% | Focus - infrastructure theme |
| 증권 | 3.518 | 62.5% | Focus - financial sector |
| 은행 | 3.728 | 62.5% | Focus - highest cohesion |
| 스페이스X(SpaceX) | 0.566 | 62.5% | Selective - weaker cohesion |

---

### Q8: Which themes failed quality filtering? (회피해야 할 테마는?)
**Answer**: 메타 레이블링 필터링된 4개 테마

| Theme | Reason | Action |
|-------|--------|--------|
| 로봇 | Low signal quality | Avoid or reduce exposure |
| 3D 낸드 | Low signal quality | Avoid or reduce exposure |
| 우주항공산업 | Low signal quality | Avoid or reduce exposure |
| 풍력에너지 | Low signal quality | Avoid or reduce exposure |

**Note**: These themes may have momentum but historical signal quality is poor.

**Source**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/meta_labeling_results_20260129.csv`

---

### Q9: What's the current market regime?
**Answer**: From pre-computed regime analysis (2026-01-28)

Refer to: `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_theme_report_2026-01-28.md`

**Note**: 레짐 분석이 이 세션에서 실행되지 않았습니다. 링크된 보고서를 참조하세요.

---

## Risk Assessment Questions

### Q10: Which signals are low quality? (저품질 시그널은?)
**Answer**: 메타 레이블링 필터로 26개 중 4개 제외 (15.4%)

| Filtered Theme | Pass Rate |
|----------------|-----------|
| 로봇 | Failed |
| 3D 낸드 | Failed |
| 우주항공산업 | Failed |
| 풍력에너지 | Failed |

**Overall**: 22/26 passed (84.6% pass rate)

---

### Q11: How strong is momentum for top stocks? (모멘텀 종목의 강도는?)
**Answer**: Momentum Strength가 모멘텀 강도를 나타냄

| 리스크 수준 | Momentum Strength | 종목 |
|-------------|------------|------|
| 높은 모멘텀 (고위험) | 4-5% | 에이티넘인베스트 (4.74%), 현우산업 (4.33%), 신흥에스이씨 (4.31%) |
| 보통 모멘텀 | 3-4% | 공구우먼 (4.04%), 리가켐바이오 (3.58%), 코메론 (3.22%), 포스코퓨처엠 (3.09%) |
| 낮은 모멘텀 (저위험) | 1-2% | 우정바이오 (1.63%), 영풍 (1.31%), 강원에너지 (1.21%) |

**해석**: Momentum Strength가 높을수록 모멘텀은 강하지만 과열 가능성도 있음

---

### Q12: Which themes have weak cohesion? (군집성이 약한 테마는?)
**Answer**: Cohesion < 1.0인 테마

| 테마 | Cohesion | 리스크 |
|------|---------|--------|
| 스페이스X(SpaceX) | 0.566 | 종목이 함께 움직이지 않을 수 있음 |
| 통신 | 0.700 | 다소 분산됨 |

**시사점**: 테마 기반 포지션은 개별 종목 리스크가 높을 수 있음

---

## Historical Performance Questions

### Q13: What's the expected return for momentum stage? (모멘텀 단계 기대수익률은?)
**Answer**: 백테스트 기준 (2024-01-05 ~ 2025-12-16)

| 지표 | 값 |
|------|-----|
| 평균 수익률 (20일) | +7.93% |
| 승률 | 43.0% |
| 표본 수 | 172 거래 |

**대시보드**: 모멘텀 탭 → 단계별 기대수익 차트 참조
**Source**: `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/backtest_results_sample.csv`

---

### Q14: How does the momentum stage perform historically?
**Answer**: 모멘텀 단계 성과 분석

| Metric | Value |
|--------|-------|
| Average Return (20D) | +4.24% |
| Win Rate | 40.9% |
| Sample Size | 556 trades |

---

### Q15: What stages should I avoid?
**Answer**: Negative expected return stages

| Stage | Return (20D) | Win Rate | Recommendation |
|-------|--------------|----------|----------------|
| Bear Volatile | -7.23% | 28.6% | **Avoid** |
| Super Trend (in Bear) | -0.39% | 37.1% | Caution |
| Bear Quiet | -2.15% | 33.2% | Avoid |

---

## Portfolio Construction Questions

### Q16: How to prioritize between momentum and sector rotation?
**Answer**: Use priority tiers

| Priority | Strategy | Tickers | Rationale |
|----------|----------|---------|-----------|
| HIGH | Early Breakout (Momentum) | 10 tickers | Higher expected return (+7.93%) |
| MEDIUM | Sector Rotation (Key Players) | 15 tickers | Stable, theme-driven |

**Suggested Allocation**:
- 60-70% to HIGH priority (momentum)
- 30-40% to MEDIUM priority (sector rotation)

---

### Q17: Which themes overlap (diversification risk)?
**Answer**: Multi-theme stocks to watch

| Ticker | Themes | Risk |
|--------|--------|------|
| LG | 통신, 스페이스X | Correlated exposure |
| SK | 통신, 증권 | Correlated exposure |
| 미래에셋증권 | 증권, 스페이스X | Correlated exposure |
| 켄코아에어로스페이스 | 방위산업, 스페이스X | Correlated exposure |

**Implication**: Holding multiple overlapping stocks reduces diversification benefit

---

### Q18: How many stocks passed all quality filters? (품질 필터 통과 종목 수는?)
**Answer**: 필터링 단계별 현황

| 단계 | 수량 | 통과율 |
|------|------|--------|
| 초기 시그널 | 26 | 100% |
| 메타 레이블링 후 | 22 | 84.6% |
| TIER 1 (최고 품질) | 6개 테마 | 23.1% |

**대시보드**: 시그널 탭 → 통과율 게이지 참조

---

## Questions NOT Answerable (Need Additional Analysis)

| Question | Missing Data | How to Get |
|----------|--------------|------------|
| What's the exact current HMM regime state? | Need to run HMM | Run regime detection pipeline |
| Price targets / stop-loss levels? | Price data, volatility | Technical analysis |
| Optimal position sizing? | Portfolio constraints | Portfolio optimization |
| Cross-market correlation (US/KRX)? | US market data | Run cross-validate skill |
| Earnings/fundamental analysis? | Financial statements | Fundamental data source |
| Liquidity/volume analysis? | Trading volume | Market data API |
| Intraday entry timing? | Intraday data | Real-time data feed |

---

## Quick Reference: Data File Locations

| Data | File Path |
|------|-----------|
| Actionable tickers | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/actionable_tickers_20260129.csv` |
| Consolidated analysis | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/consolidated_ticker_analysis_20260129.json` |
| Key players | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/tier1_key_players_20260129.json` |
| Meta-labeling results | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/meta_labeling_results_20260129.csv` |
| Regime report | `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_theme_report_2026-01-28.md` |
| Backtest results | `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/backtest_results_sample.csv` |

---

---

## Dashboard Navigation / 대시보드 안내

| Tab | URL | Key Feature |
|-----|-----|-------------|
| 개요 (Overview) | http://localhost:8000/ | 전체 현황 요약, 모멘텀 종목, 테마 군집성 |
| 모멘텀 (Momentum) | http://localhost:8000/breakout.html | 단계별 분포, 기대수익, 관심주 |
| 시그널 (Signals) | http://localhost:8000/signals.html | 메타 레이블링 통과율, 테마별 시그널 |
| 군집성 (Cohesion) | http://localhost:8000/cohesion.html | 테마 군집성 분석, 상승/하락 TOP 5 |
| 네트워크 (Network) | http://localhost:8000/theme-graph.html | 테마 네트워크 시각화, 부분 검색 지원 |

**언어 전환**: 우측 상단 KOR/ENG 토글로 한/영 전환 가능

---

*Generated: 2026-01-29 (Updated: 2026-01-30)*
*Analysis Framework: Sector-Rotation-KRX*
*Dashboard: KOR/ENG i18n 지원*

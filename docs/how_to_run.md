# KRX Sector Rotation - 실행 가이드

> 마지막 업데이트: 2026-02-03

## 개요

KRX Sector Rotation 시스템의 일일/주간 실행 방법을 설명합니다.

---

## 일일 업데이트 (Daily Update)

### 전체 파이프라인 실행 (권장)

```bash
# 12단계 전체 파이프라인 실행
bash /mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh
```

### 파이프라인 단계

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
| 9 | Regime Analysis | classified_trends 생성 |
| 10 | Copy Trends | superTrend 디렉토리에 복사 |
| 11 | Frontend Data | actionable_tickers 생성 |
| **12** | **BB Filter** | **장기추세돌파 (BB Crossover) 필터** |

### 개별 단계 실행

```bash
# Step 9: Regime/Theme 분석
cd /mnt/nas/AutoGluon/AutoML_Krx/.agent/skills/regime_analysis
python run_analysis.py --date 2026-02-02

# Step 10: classified_trends 복사
cp /mnt/nas/AutoGluon/AutoML_Krx/regime/results/classified_trends_2026-02-02.csv \
   /mnt/nas/AutoGluon/AutoML_Krx/superTrend/

# Step 11: actionable_tickers 생성
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts
python daily_price_update.py

# Step 12: BB 필터 (장기추세돌파)
cd /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB
echo '{"isMkt": "Krx", "isDate": "2026-02-02"}' > libPath.json
python filter_bb.py
```

---

## 주간 분석 (Weekly Analysis)

```bash
# 주간 분석 전체 실행
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
./run_weekly_analysis.sh
```

### 주간 분석 단계

1. **Tier 분류** - TIER 1-4 분류
2. **Fundamental Validation** - 펀더멘탈 검증
3. **Report Generation** - 투자 보고서 생성

---

## 대시보드 실행

### 로컬 실행

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 서버 재시작

```bash
pkill -f "uvicorn.*8000"
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/dashboard/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/krx_dashboard.log 2>&1 &
```

### 대시보드 URL

- **로컬**: http://localhost:8000/
- **서버**: http://163.239.155.97:8000/

---

## 필터 방법별 실행

### 1. Daily Top Performers (AutoML)

```bash
python3 /mnt/nas/AutoGluon/AutoML_Krx/Backtest/generate_daily_summary.py 2026-02-02
```

### 2. SuperTrend Candidates

```bash
# classified_trends → actionable_tickers 파이프라인
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts
python daily_price_update.py
```

### 3. Long Term Trend Breakout (장기추세돌파)

```bash
# BB(220, 2.0) Crossover 필터
cd /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB
echo '{"isMkt": "Krx", "isDate": "2026-02-02"}' > libPath.json
python filter_bb.py
```

### 4. Breakout Candidates

```bash
# actionable_tickers 생성 (SuperTrend와 동일)
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/scripts
python daily_price_update.py
```

---

## Cron 설정 (자동 실행)

```bash
# crontab -e
# 매일 18:30 KST 실행 (시장 마감 후)
30 18 * * 1-5 /mnt/nas/AutoGluon/AutoML_Krx/daily_update_all.sh >> /mnt/nas/AutoGluon/AutoML_Krx/logs/cron_daily.log 2>&1
```

---

## 로그 확인

```bash
# 오늘 로그 확인
tail -100 /mnt/nas/AutoGluon/AutoML_Krx/logs/daily_update_$(date +%Y%m%d).log

# 프론트엔드 데이터 확인
ls -la /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/actionable_tickers_*.csv | tail -5

# BB 필터 결과 확인
cat /mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/Filter/bb_filtered_tickers.json
```

---

## 출력 파일 위치

| 파일 | 위치 | 설명 |
|------|------|------|
| `actionable_tickers_{DATE}.csv` | `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/` | 브레이크아웃 후보 |
| `classified_trends_{DATE}.csv` | `/mnt/nas/AutoGluon/AutoML_Krx/superTrend/` | 트렌드 분류 |
| `bb_filtered_tickers.json` | `/mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/Filter/` | 장기추세돌파 종목 |
| `daily_summary_{DATE}.json` | `/mnt/nas/AutoGluon/AutoML_Krx/Backtest/Rankings/` | 일일 상위 종목 |

---

## Meta-Labeling in Theme

Meta-labeling은 테마 시그널의 품질을 ML 모델로 필터링하는 기법입니다.

### 개념

```
Historical Signals (과거)  →  Backtest  →  Training Data  →  Train Model  →  Use Today
        ↓                        ↓              ↓                ↓              ↓
2025-02-09 ~ 2025-05-04    12주 대기      15,643개 시그널    XGBoost.pkl    2026-02-03
   (시그널 생성)          (실제 수익률)    (signal_perf)      (79.4% 정확도)    (예측)
```

**핵심**: 과거 시그널의 실제 수익률을 학습하여, 현재 시그널 중 성공 확률이 높은 것만 필터링

### 파일 구조

| 파일 | 위치 | 설명 |
|------|------|------|
| `signal_performance_*.csv` | `backtest/results/` | 학습 데이터 (과거 시그널 + 실제 수익률) |
| `meta_labeler_xgboost_*.pkl` | `backtest/models/` | 학습된 XGBoost 모델 |
| `meta_labeling_results_*.csv` | `data/` | 필터링 결과 (PASS/FILTERED) |

### 학습 데이터 생성 (Backtest)

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/backtest

# 백테스트 실행 → signal_performance.csv 생성
python run_backtest.py \
  --start-date 2025-05-01 \
  --end-date 2025-11-01 \
  --holding-period 12
```

**주의**: 12주 holding period가 필요하므로, 학습 가능한 최신 날짜는 `오늘 - 12주`

### 모델 학습 (Training)

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/backtest

# 학습 실행 (~30초)
python train_meta_labeler.py \
  --results-file results/signal_performance_20251113.csv \
  --model-type xgboost \
  --skip-ucs
```

**학습 결과 예시**:
- Accuracy: 79.4%
- AUC: 0.846
- 학습 샘플: 15,643개 시그널

### 주간 업데이트 (Weekly Update)

```bash
# 주간 meta-labeling 결과 생성 + Railway 배포
/mnt/nas/WWAI/Sector-Rotation/Jobs/krx_weekly_update_meta_labeling.sh

# 특정 날짜 지정
/mnt/nas/WWAI/Sector-Rotation/Jobs/krx_weekly_update_meta_labeling.sh 2026-02-03
```

**수행 작업**:
1. `enhanced_cohesion_themes_*.csv` 로드 (79개 테마)
2. 19개 피처 추출 (tier, cohesion, fiedler 등)
3. Meta-labeler 모델로 예측
4. PASS/FILTERED 분류 → `meta_labeling_results_*.csv` 저장
5. Railway 자동 배포

### 학습 데이터 조회

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/backtest/results

# 특정 날짜의 테마 시그널 조회
python3 -c "
import pandas as pd
df = pd.read_csv('signal_performance_20251113.csv')

# 날짜 목록
print(df['signal_date'].unique())

# 특정 날짜 조회
date = '2025-03-09'
week_df = df[df['signal_date'] == date]
theme_perf = week_df.groupby('theme')['total_return'].mean().sort_values(ascending=False)
print(theme_perf.head(10))
"
```

### 학습 데이터 통계

| 항목 | 값 |
|------|-----|
| 총 시그널 | 15,643개 |
| 기간 | 2025-02-09 ~ 2025-05-04 (13주) |
| 테마 수 | 82개 |
| 양성(수익) | 10,586개 (67.7%) |
| 음성(손실) | 5,057개 (32.3%) |

### 피처 (19개)

```
signal_type_tier, signal_type_cohesion, signal_type_leadership, signal_type_combined,
signal_strength, tier, is_tier1, is_tier2, leadership_gap,
current_fiedler, week_before_fiedler, fiedler_change, fiedler_pct_change,
day_of_week, day_of_month, month, quarter, is_month_end, is_quarter_end
```

### 결과 확인

```bash
# PASS된 테마 확인
grep "PASS" /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/meta_labeling_results_*.csv

# 대시보드에서 확인
# https://web-production-e5d7.up.railway.app/signals.html
```

---

## Update Cohesion (테마 군집성 업데이트)

Cohesion 데이터는 주간 분석에서 생성되며, Dashboard의 cohesion.html 페이지에 표시됩니다.

### 현재 상태 확인

```bash
# Railway API에서 현재 cohesion 날짜 확인
curl -s "https://web-production-e5d7.up.railway.app/api/sector-rotation/themes" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Date:', d.get('date'))"

# 로컬 cohesion 파일 확인
ls -la /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/data/enhanced_cohesion_themes_*.csv | tail -3
```

### Cohesion 업데이트 실행

```bash
# 1. 주간 분석 실행 (cohesion 데이터 생성, ~2-5분)
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
./run_weekly_analysis.sh

# 2. Railway 배포
bash /mnt/nas/WWAI/Sector-Rotation/Jobs/daily_deploy_krx.sh
```

### 생성 파일

| 파일 | 위치 | 설명 |
|------|------|------|
| `enhanced_cohesion_themes_{DATE}.csv` | `data/` | 테마별 Fiedler 값, 변화율 |
| `NAVER_THEME_COHESION_REPORT_{DATE}.md` | `reports/` | Cohesion 분석 보고서 |

### 개별 Cohesion 분석만 실행

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX

# 특정 날짜로 cohesion 분석
python3 analyze_naver_theme_cohesion.py --date 2026-02-03

# 결과 확인
head data/enhanced_cohesion_themes_20260203.csv
```

### Cohesion 데이터 구조

| 필드 | 설명 |
|------|------|
| `theme` | 테마명 |
| `current_fiedler` | 현재 Fiedler eigenvalue (군집성) |
| `historical_fiedler` | 30일 전 Fiedler 값 |
| `fiedler_change` | 변화량 (current - historical) |
| `pct_change` | 변화율 (%) |
| `n_stocks` | 테마 내 종목 수 |
| `status` | VERY STRONG / STRONG / MODERATE / WEAK |

### Dashboard 확인

- **Railway**: https://web-production-e5d7.up.railway.app/cohesion.html
- **로컬**: http://localhost:8000/cohesion.html

---

## 참고 문서

- [필터링 방법 가이드](./how_to_filter.md) - 4가지 필터 상세 설명
- [RECONCILIATION_FRAMEWORK.md](./RECONCILIATION_FRAMEWORK.md) - 펀더멘탈 검증 프레임워크
- [CLAUDE.md](../CLAUDE.md) - 프로젝트 전체 개요

# KRX Sector Rotation - 실행 가이드

> 마지막 업데이트: 2026-02-02

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

## 참고 문서

- [필터링 방법 가이드](./how_to_filter.md) - 4가지 필터 상세 설명
- [RECONCILIATION_FRAMEWORK.md](./RECONCILIATION_FRAMEWORK.md) - 펀더멘탈 검증 프레임워크
- [CLAUDE.md](../CLAUDE.md) - 프로젝트 전체 개요

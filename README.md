# Bluetooth Channel Sounding 데이터 분석 (정보통신 DCCS 206 · Team A3)

> 이 문서는 **Claude Code에 넘기기 위한 인수인계용 README**다.
> 프로젝트 맥락, 이미 확인된 사실, 해야 할 분석, 산출물 형식을 모두 담았다.
> Claude Code는 이 문서만 보고 작업을 이어갈 수 있어야 한다.

---

## 1. 프로젝트 맥락

- **수업:** 정보통신 (Information Communication, DCCS 206), 고려대학교
- **팀:** A3 — 전재형, 최연우, 김영웅
- **주제:** *From Flagship-Only to Everywhere: Bluetooth Channel Sounding and the Evolution of Precise Short-Range Ranging*
- **카테고리:** Close range — the things you touch
- **진행 방식:** 교수님 승인 하에 **자체 실험 없이 자료조사 중심**으로 진행한다. 정량 근거는 공개 측정 연구와 공개 데이터셋으로 대신한다.
  - 이 레포의 목적: **공개 데이터셋을 우리가 직접 분석해서 발표 슬라이드용 그래프를 만드는 것.** 직접 측정은 하지 않는다.

### 발표 스토리
`RSSI (싸지만 부정확·릴레이 공격 취약)` → `UWB (cm 단위·안전하지만 별도 칩, 플래그십 전용)` → `Channel Sounding (별도 칩 없이 블루투스만으로, 충분히 정확)`

### 우리만의 질문 (midpoint 승인됨)
> "Apple pioneered UWB in phones, yet it added Bluetooth Channel Sounding in iOS 27 — and Samsung's SmartTag3 now ships with both. Is Channel Sounding a replacement for UWB, or the start of a division of labor between them?"

잠정 결론: **단기적으로는 분업, 저가 기기 시장에서는 부분 대체.** 분석 결과는 이 질문과 공통 질문 6번("무엇을 포기했나")의 근거로 쓰인다.

### 마감
| 날짜 | 제출물 |
|---|---|
| **2026-11-09 (월) 23:59** | 발표 영상(영어, 15–20분, YouTube 일부공개 / Drive 보기전용) + 슬라이드 PDF |
| 2026-11-13 (금) | 수업 중 Live Q&A (조당 최대 15분) |
| 2026-11-18 (수) 23:59 | Q&A 결과 보고서 (받은 질문·답변·질문 평가 루브릭·점수) |

→ **분석은 짧게 끝내야 한다.** 목표는 슬라이드에 넣을 그래프 2~3장이다.

---

## 2. 데이터셋

- **레포:** https://github.com/RuijieXu0408/Bl-CS-Evaluation-Dataset
- **저자:** Ruijie Xu, Penghui Xu, Cheng Chang, Tung-Hao Hsu, Li-Ta Hsu
- **관련 논문 (데이터셋 README 기준 제목):** "Beyond Proximity: Evaluating High-Precision Bluetooth Channel Sounding for Mobile Applications," accepted to *IPIN 2026* (2026.10.5–8, Rome).

### 측정 구성 (데이터셋 README에서 확인)
| 항목 | 내용 |
|---|---|
| Initiator | Google Pixel 10 Pro (Android 16, BT 6.0) |
| Reflector | Nordic nRF54L15 DK |
| Ground truth | **Qorvo DW1000** UWB 모듈 (블루투스 안테나와 물리적으로 붙여서 설치) |
| 대역 | 2.4 GHz ISM, 최대 72채널 |
| 업데이트 주기 | 0.2 Hz, 5 Hz, 10 Hz |
| 환경 | 실외 잔디밭 (60 m × 30 m, LOS) / 실내 복도 (폭 2.5 m, 다중경로 많음) |

### 폴더 구조
```
GT/              # UWB 기준값.  컬럼: Timestamp, Distance(m)
                 #   Timestamp 형식: 2026-01-18 15:23:39.786
RangingFilter/   # Android CS API 결과.  컬럼: Timestamp, Device Name, Address,
                 #   Distance (m), Confidence Level (0 low / 1 medium / 2 high)
                 #   Timestamp 형식: 1/18/2026 15:23:39.786  (월/일/년)
firmware/, app/  # 분석에는 불필요
```
- 같은 시나리오는 **GT와 RangingFilter에서 파일명이 같다.**
- 파일명 규칙: `<Static|Dynamic>_<02Hz|5Hz|10Hz>_<1m|10m|25m|50m 또는 패턴>_<Outdoor|Indoor_Corridor>.csv`
- **주의:** `Static_5Hz_10m_Indoor_Corridor.csv`는 CS 로그가 약 2분, GT 로그가 약 9분이다. 의도된 차이고, 시간 정렬하면 자동으로 해결된다.

### 정렬 방법 (논문 저자와 동일)
CS 각 측정값에 대해 **가장 가까운 시각의 GT 값**을 짝짓는다. 허용 오차는 **500 ms**다.
```python
cs["t"] = pd.to_datetime(cs["Timestamp"], format="%m/%d/%Y %H:%M:%S.%f")
gt["t"] = pd.to_datetime(gt["Timestamp"])
m = pd.merge_asof(cs.sort_values("t"), gt.sort_values("t")[["t", "Distance(m)"]],
                  on="t", direction="nearest", tolerance=pd.Timedelta("500ms"))
err = m["Distance (m)"] - m["Distance(m)"]   # CS - UWB
```

---

## 3. 1차 분석 결과 (이미 확인됨)

정지 측정 13개 파일, 약 1만 6천 개 측정값. 오차 = CS − UWB (단위 m).

| 파일 | 환경 | 거리 | n | 평균오차 | MAE | 표준편차 | 95% | RMSE |
|---|---|---|---|---|---|---|---|---|
| Static_5Hz_1m_Indoor_Corridor | Indoor | 1 | 1734 | -0.37 | 0.37 | 0.10 | 0.50 | 0.38 |
| Static_5Hz_10m_Indoor_Corridor | Indoor | 10 | 704 | 4.26 | **4.26** | 5.32 | **11.35** | 6.81 |
| Static_5Hz_25m_Indoor_Corridor | Indoor | 25 | 1889 | 0.68 | 0.68 | 0.08 | 0.79 | 0.68 |
| Static_5Hz_50m_Indoor_Corridor | Indoor | 50 | 2040 | -0.42 | 0.42 | 0.12 | 0.59 | 0.43 |
| Static_10Hz_1m_Outdoor | Outdoor | 1 | 1669 | -0.20 | 0.28 | 0.28 | 0.68 | 0.34 |
| Static_5Hz_1m_Outdoor | Outdoor | 1 | 897 | 0.36 | 0.37 | 0.15 | 0.57 | 0.39 |
| Static_02Hz_10m_Outdoor | Outdoor | 10 | 354 | 0.07 | 0.20 | 0.27 | 0.66 | 0.28 |
| Static_10Hz_10m_Outdoor | Outdoor | 10 | 2167 | 0.43 | 0.51 | 0.35 | 0.87 | 0.56 |
| Static_5Hz_10m_Outdoor | Outdoor | 10 | 1306 | 0.79 | 0.87 | 1.16 | 1.91 | 1.40 |
| Static_10Hz_25m_Outdoor | Outdoor | 25 | 1724 | 0.47 | 0.50 | 0.60 | 0.82 | 0.76 |
| Static_5Hz_25m_Outdoor | Outdoor | 25 | 1393 | 0.94 | 0.94 | 1.74 | 1.30 | 1.98 |
| Static_10Hz_50m_Outdoor | Outdoor | 50 | 524 | 0.26 | 0.31 | 0.41 | 0.54 | 0.48 |
| Static_5Hz_50m_Outdoor | Outdoor | 50 | 188 | 0.10 | 0.17 | 0.18 | 0.44 | 0.21 |

**해석 (잠정)**
- 실외는 1–50 m 전 구간에서 평균 절대오차가 약 0.2–0.9 m다. cm 단위가 아니라 **수십 cm 수준**이다.
- **실내 복도 10 m만 크게 튄다** (MAE 4.26 m, 95% 11.35 m). 다중경로 영향으로 추정되지만 **아직 확인 안 됨** → 아래 작업 2에서 확인한다.
- 같은 거리에서 5 Hz가 10 Hz보다 오차가 큰 경우가 있다 (10 m, 25 m 실외). 원인 미확인. 발표에서 단정하지 말 것.

---

## 4. 할 일 (Claude Code)

### 작업 1 — 레포 기본 구성
```
cs-analysis/
├── README.md               # 이 문서 (분석 끝나면 결과 섹션 갱신)
├── requirements.txt        # pandas, numpy, matplotlib
├── data/                   # 데이터셋 클론 위치 (.gitignore 처리, 커밋하지 않음)
├── scripts/
│   ├── align.py            # 공통: 파일 로드 + merge_asof 정렬 함수
│   ├── static_error.py     # 작업 3
│   └── timeseries.py       # 작업 2
└── figures/                # 슬라이드용 PNG (dpi 200 이상)
```
- 데이터는 `git clone --depth 1 https://github.com/RuijieXu0408/Bl-CS-Evaluation-Dataset data/` 로 받는다. 우리 레포에는 커밋하지 않는다(재배포 대신 링크).
- 스크립트는 `python scripts/xxx.py --data data --out figures` 형태로 실행되게 만든다.

### 작업 2 — 실내 10 m 이상치 확인 (우선순위 높음)
- `Static_5Hz_10m_Indoor_Corridor`의 CS 값과 UWB 값을 **시간축 그래프**에 겹쳐 그린다.
- 오차가 특정 구간에 몰려 있는지, 특정 값으로 "점프"하는지 본다. Confidence Level별로 색을 나눠서, 신뢰도 낮은 값에 오차가 몰리는지도 확인한다.
- 결론은 **데이터에서 보이는 것만** 적는다. 원인(다중경로 등)은 "추정"으로 표기한다.

### 작업 3 — 발표용 메인 그래프 정리
- **Figure A — 거리별 오차 (실외 vs 실내):** x = 실제 거리, y = MAE와 95% 오차. 업데이트 주기별 결과는 n 가중평균으로 합친다. 1차 버전은 이미 그렸고, 발표용으로 다듬기만 하면 된다.
- **Figure B — 시간축 예시 1장:** 실외 10 m 하나(안정적인 사례)와 실내 10 m(튀는 사례)를 위아래로 배치한다. "같은 10 m인데 환경에 따라 이렇게 다르다"를 보여주는 그림이다.
- **(선택) Figure C — 동적 보행:** `Dynamic_*` 파일 하나에서 사람이 걸어갈 때 CS가 UWB를 얼마나 따라가는지 보여준다.

### 그래프 스타일 규칙
- 영어 라벨을 쓴다 (발표가 영어다).
- 축 단위를 반드시 표시한다: `Distance (m)`, `Error (m)`.
- 캡션이나 제목에 출처를 넣는다: `Data: Xu et al., IPIN 2026 dataset (Pixel 10 Pro + nRF54L15, UWB DW1000 ground truth)`
- 색: 실외 = 파랑 `#2a6fb0`, 실내 = 주황 `#d4762a`. 슬라이드 16:9에 맞게 `figsize=(10, 5.6)` 정도로 한다.

---

## 5. 발표에서 이 결과를 말할 때 주의할 점

1. **기준값도 UWB다.** 이 데이터의 "정답"은 UWB(DW1000) 측정값이고, UWB도 자체 오차가 있다. 그래서 이 분석은 정확히 말하면 **"CS가 UWB와 얼마나 다른가"**를 본 것이다.
2. **우리가 측정한 데이터가 아니다.** 슬라이드에 "Analysis by Team A3 on public dataset [Xu et al.]"처럼 출처를 명시한다.
3. **샘플이 작다.** 시나리오별 측정은 한 번씩이라, 일반화는 조심한다 ("이 실험 조건에서는").
4. **Comarch 결과와 연결한다.** Comarch 실험에서도 UWB가 더 안정적이었다 (CS 정밀 모듈 평균 1.8 mA vs UWB 0.75 mA 소비전력). 두 자료가 같은 방향을 가리킨다는 식으로 쓴다.

---

## 6. 확인된 참고 자료 (제안서 기준)

1. M. Woolley, "Bluetooth Channel Sounding: A Technical Overview," v1.0, Bluetooth SIG, Jul. 2024. https://www.bluetooth.com/channel-sounding-tech-overview/ — PBR(위상 기반) + RTT(왕복시간), **1 MHz 채널 72개**, 약 150 m까지 모호성 없음
2. Apple, "Find your accessory with Bluetooth Channel Sounding," WWDC26 Session 369. https://developer.apple.com/videos/play/wwdc2026/369/ — iOS 27, N1 칩 아이폰, 액세서리 BT 6.3 필요, 포그라운드에서만 동작
3. Nordic DevZone, Channel Sounding on Pixel 10. https://devzone.nordicsemi.com/nordic/nordic-blog/b/blog/posts/evaluating-bluetooth-channel-sounding-with-our-open_2d00_source-android-app-on-google-pixel-10 — Pixel 10(2025.8)이 첫 지원 폰, Pixel 9는 Android 16 QPR2로 지원
4. Android Developers, "Range between devices." https://developer.android.com/develop/connectivity/ranging — Android 16 Ranging module: UWB, BT CS, Wi-Fi NAN RTT, BT RSSI
5. Comarch, "UWB vs Bluetooth Channel Sounding," 2025. https://www.comarch.com/sw-and-hw-services/blog/uwb-vs-bluetooth-channel-sounding-which-is-better-for-distance-measurements/
6. ZDNet Korea, 갤럭시 스마트태그3 (2026.10.1). https://zdnet.co.kr/view/?no=20261001095757 — CS로 최대 약 60 m 방향·거리 안내, 약 20 m 이내는 UWB
7. 중앙이코노미뉴스, 갤럭시 스마트태그3 (2026.10.1). https://www.joongangenews.com/news/articleView.html?idxno=551782
8. Xu et al., Bluetooth 6.0 CS Evaluation Dataset. https://github.com/RuijieXu0408/Bl-CS-Evaluation-Dataset

### 정정 사항 (제출된 제안서와 다른 점)
- 제안서 [8]에는 논문 제목을 "From Proximity to Precision…"으로 적었다(GitHub 저장소 소개 문구 기준). 그런데 **데이터셋 README에는 "Beyond Proximity: Evaluating High-Precision Bluetooth Channel Sounding for Mobile Applications"**로 되어 있다. **발표 슬라이드에는 README 제목을 쓴다.**
- 기준값 UWB 모듈은 **DW1000**이다 (DW3000 아님).

---

## 7. AI 활용 고지

이 레포의 분석 계획과 코드는 Claude(Anthropic)의 도움을 받아 작성했다. 강의 규정상 AI 활용은 명시해야 하고, 교수님이 내용을 직접 설명하라고 할 수 있다. 팀원 모두 **정렬 방법(섹션 2)과 해석 주의점(섹션 5)**은 직접 설명할 수 있어야 한다.

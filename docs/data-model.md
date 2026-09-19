# 데이터 모델

## 흐름

```text
MCP 원본 응답
  → data/raw/ 원본 JSON
  → data/imports/ 정규화 JSON
  → listings / listing_observations / seller_safety_checks
  → pricing_runs / price_guide_rows
  → dist/data.json + dist/index.html
```

Git에는 SQLite 파일을 넣지 않는다. `db/migrations/`, `config/`, `data/raw/`, `data/imports/`만으로 `var/salmanhanga.sqlite`를 다시 만들 수 있게 관리한다.

## 테이블 책임

| 테이블 | 역할 |
|---|---|
| `ingestion_runs` | 수집 시각·원본 파일·내용 해시를 기록하는 가져오기 단위 |
| `marketplaces` | 번개장터·중고나라 구분과 기준 URL |
| `products` | 브랜드·모델·용량/구성 조합 |
| `sellers` | 마켓별 판매자 식별자. 식별자가 없는 응답은 연결하지 않음 |
| `listings` | 매물의 고정 정보와 원문 링크. 중고나라 링크도 여기 저장 |
| `listing_observations` | 조회할 때마다 달라지는 가격·판매 상태의 이력 |
| `seller_safety_checks` | 안전거래 횟수와 확인 가능 여부의 시점별 증거 |
| `pricing_runs` | 기준 시각과 적용 규칙을 고정한 집계 실행 |
| `price_guide_rows` | 공개 가격표 한 줄의 값과 근거 매물 링크 |

## 현재가 규칙

1. `active`이고 정상 비교 가능한 매물만 본다.
2. `updated_at`, 없으면 `listed_at`을 사용한다.
3. 기준 시각보다 미래인 매물과 **25일을 초과한 매물은 제외**한다.
4. 남은 매물 중 최저가가 `판매중 최저가`다.
5. 최신 안전거래 확인이 `verified`이고 횟수가 1회 이상인 판매자만 비주의로 본다.
6. 안전거래 0회는 `주의 · 안전거래 0회`, 확인 불가는 `주의 · 안전거래 이력 확인불가`다.
7. 비주의 판매자 중 최저가를 `판매중-안전`에 기록한다.
8. 가격 셀은 반드시 근거 매물의 `listing_url`을 함께 가진다.

기존 2026-09-20 스냅샷에는 매물 갱신 시각과 판매자 안전거래 횟수가 완전하게 들어 있지 않다. 그래서 기존 값은 `legacy_snapshot`으로 보존하고, 새 규칙을 임의로 소급 적용하지 않는다.

2026-09-20 MCP 전면 갱신에서는 중고나라 `판매가` 이력의 상세 매물이 판매중 목록과 모두 겹쳤다. 판매 완료 근거로 쓸 수 없어서 6개월 최저와 3개월 평균은 비워 두며, 판매중 매물을 판매 완료로 바꾸지 않는다.

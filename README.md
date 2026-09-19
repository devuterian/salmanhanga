# 살만한가

중고 기기의 `판매중 최저가 → 판매중-안전 → 6개월 최저 → 3개월 평균`을 근거 매물 링크와 함께 관리하는 가격 가이드입니다.

현재 공개 사이트: https://salmanhanga.nyaanimdesu.chatgpt.site

**JSON과 JSON Schema가 원본**입니다. SQLite는 JSON 원본을 빠르게 검색하고 가격표를 계산하기 위해 재생성하는 로컬 캐시입니다.

## 핵심 규칙

- 판매중 가격은 게시·갱신일이 기준 시각에서 **25일 이내**인 정상 매물만 사용합니다.
- 안전거래 0회인 판매자는 `주의 · 안전거래 0회`로 표시합니다.
- 안전거래 이력을 확인할 수 없는 판매자는 `주의 · 안전거래 이력 확인불가`로 표시합니다.
- 안전거래 이력이 확인되고 1회 이상인 판매자 중 최저가를 `판매중-안전`에 표시합니다.
- 모든 가격 근거에는 중고나라 또는 번개장터 원문 링크를 저장합니다.
- 기존 2026-09-20 데이터는 원형 그대로 보존합니다. 부족한 날짜나 판매자 이력을 추측해 채우지 않습니다.

## 저장소 구조

```text
config/             JSON으로 관리하는 가격 계산 규칙
data/catalog/       JSON 상품 카탈로그
data/imports/       MCP 원본·레거시 수집 스냅샷
db/migrations/      재현 가능한 SQLite 스키마
docs/               데이터 모델과 판정 기준
schemas/            수집·안전거래·출력 JSON 계약
scripts/            DB 초기화, 수집 반영, 계산, 사이트 빌드
src/                사이트 원본
dist/               ChatGPT Sites에 배포할 정적 결과
tests/              25일·주의·판매중-안전 회귀 테스트
var/                로컬 SQLite DB. Git에는 올리지 않음
```

## 시작하기

Python 3.11 이상이 필요합니다. JSON Schema 검증 도구는 개발 의존성으로 분리했습니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
make PYTHON=.venv/bin/python bootstrap
make PYTHON=.venv/bin/python test
make PYTHON=.venv/bin/python verify
```

`make bootstrap`은 마이그레이션과 보존된 스냅샷으로 `var/salmanhanga.sqlite`를 만듭니다. DB 파일은 결과물이므로 커밋하지 않습니다.

## 새 MCP 수집 반영

1. MCP 응답을 `schemas/listing-import.schema.json` 구조로 정리합니다.
2. 원본 파일을 `data/imports/YYYY-MM-DD-이름.json`에 커밋합니다.
3. DB에 넣고 기준 시각으로 가격표를 계산합니다.
4. `dist/`를 다시 만든 뒤 테스트합니다.

```bash
.venv/bin/python scripts/validate_json.py
python3 scripts/manage_db.py ingest data/imports/2026-09-21-example.json
python3 scripts/manage_db.py compute --as-of 2026-09-21T12:00:00+09:00
python3 scripts/manage_db.py build
make test
python3 scripts/manage_db.py verify
```

테이블별 역할과 안전 판정 방식은 [데이터 모델](docs/data-model.md)에 정리돼 있습니다.

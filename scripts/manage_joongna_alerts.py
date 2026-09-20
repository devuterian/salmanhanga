#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "https://main-api.joongna.com"
KEYCHAIN_ACCOUNT = "local"
KEYCHAIN_SERVICE = "com.55fries.joongna.session"
DEFAULT_MIN_PRICE = 100_000
ROOT = Path(__file__).resolve().parents[1]
SOLD_AVERAGES_DIR = ROOT / "data" / "aggregates"
DEFAULT_HEADERS = {
    "App-Version": "8.8.1",
    "Content-Type": "application/json",
    "Os-Type": "0",
    "Os-Version": "Android16",
    "scheme": "jnapp",
    "User-Agent": "55FRIES/1.0 (Joongna Android 8.8.1)",
}


def read_session() -> dict:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            KEYCHAIN_SERVICE,
            "-w",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def save_session(session: dict) -> None:
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-a",
            KEYCHAIN_ACCOUNT,
            "-s",
            KEYCHAIN_SERVICE,
            "-l",
            "55FRIES Joongna Session",
            "-w",
            json.dumps(session, ensure_ascii=False, separators=(",", ":")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def send(method: str, path: str, token: str | None = None, payload: dict | None = None) -> dict:
    headers = dict(DEFAULT_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def refresh_session(session: dict) -> dict:
    refreshed = send(
        "POST",
        "/common/token/refresh",
        payload={
            "accessToken": session["accessToken"],
            "refreshToken": session["refreshToken"],
        },
    ).get("data")
    if not refreshed or not refreshed.get("accessToken"):
        raise RuntimeError("중고나라 토큰 갱신 응답이 비어 있습니다")
    session.update(refreshed)
    save_session(session)
    return session


def valid_session() -> dict:
    session = read_session()
    if session.get("accessTokenExpiration", 0) <= int(time.time()) + 60:
        session = refresh_session(session)
    return session


def api(method: str, path: str, payload: dict | None = None) -> dict:
    session = valid_session()
    try:
        response = send(method, path, session["accessToken"], payload)
    except urllib.error.HTTPError as error:
        if error.code not in (401, 403):
            raise
        session = refresh_session(session)
        response = send(method, path, session["accessToken"], payload)
    meta = response.get("meta", {})
    if meta.get("code") != 0:
        raise RuntimeError(meta.get("message") or f"API 오류: {meta.get('code')}")
    return response


def keyword_payload(
    keyword: str,
    *,
    min_price: int | None,
    max_price: int | None,
    user_keyword_seq: int = 0,
) -> dict:
    min_price = DEFAULT_MIN_PRICE if min_price is None else min_price
    if min_price < DEFAULT_MIN_PRICE:
        raise ValueError(f"최저 가격은 {DEFAULT_MIN_PRICE:,}원 이상이어야 합니다")
    if max_price is not None and max_price < min_price:
        raise ValueError("최고 가격은 최저 가격보다 낮을 수 없습니다")
    return {
        "categoryName": None,
        "categorySeq": "0",
        "flawed": 0,
        "fullPackage": 0,
        "keywordLocation": [],
        "limitedEdition": 0,
        "productColor": "ZZZZZZ",
        "productCondition": 3,
        "productEndPrice": max_price,
        "productStartPrice": min_price,
        "productTradeType": 0,
        "tagKeywordName": keyword.strip(),
        "tagKeywordSeq": 0,
        "userKeywordSeq": user_keyword_seq,
        "userSeq": 0,
        "isKeywordDuplicateCheck": True,
    }


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_list(_: argparse.Namespace) -> None:
    response = api("GET", "/mypage/pushSetting/keyword")
    print_json(response["data"])


def command_validate(args: argparse.Namespace) -> None:
    response = api(
        "POST",
        "/mypage/pushSetting/validate/keyword",
        {"keyword": args.keyword.strip()},
    )
    print_json(response["data"])


def command_add(args: argparse.Namespace) -> None:
    response = api(
        "POST",
        "/mypage/pushSetting/keywordRedeem",
        keyword_payload(args.keyword, min_price=args.min_price, max_price=args.max_price),
    )
    print_json(response.get("data"))


def command_update(args: argparse.Namespace) -> None:
    response = api(
        "PUT",
        f"/mypage/pushSetting/keyword/{args.user_keyword_seq}",
        keyword_payload(
            args.keyword,
            min_price=args.min_price,
            max_price=args.max_price,
            user_keyword_seq=args.user_keyword_seq,
        ),
    )
    print_json(response.get("data"))


def command_remove(args: argparse.Namespace) -> None:
    response = api("DELETE", f"/mypage/pushSetting/keyword/{args.user_keyword_seq}")
    print_json(response.get("data"))


def command_sync_discounts(_: argparse.Namespace) -> None:
    paths = sorted(SOLD_AVERAGES_DIR.glob("sold-averages-*.json"))
    if not paths:
        raise ValueError("3개월 판매완료 평균 데이터가 없습니다")
    rows = json.loads(paths[-1].read_text())["rows"]
    current = api("GET", "/mypage/pushSetting/keyword")["data"]["keywordVOS"]
    by_keyword = {item["tagKeywordName"]: item for item in current}
    updated = []
    skipped = []
    for row in rows:
        maximum = row["alert_max_price_krw"]
        if maximum is None:
            skipped.extend(row["alert_keywords"])
            continue
        for keyword in row["alert_keywords"]:
            item = by_keyword.get(keyword)
            if item is None:
                skipped.append(keyword)
                continue
            api(
                "PUT",
                f"/mypage/pushSetting/keyword/{item['userKeywordSeq']}",
                keyword_payload(
                    keyword,
                    min_price=DEFAULT_MIN_PRICE,
                    max_price=maximum,
                    user_keyword_seq=item["userKeywordSeq"],
                ),
            )
            updated.append({"keyword": keyword, "max_price": maximum})
            time.sleep(2)
    print_json({"updated": updated, "skipped": skipped})


def add_price_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--min-price", type=int)
    parser.add_argument("--max-price", type=int)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="중고나라 키워드 알림 관리")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="현재 알림 목록 조회")
    list_parser.set_defaults(handler=command_list)

    validate_parser = subparsers.add_parser("validate", help="키워드 등록 가능 여부 확인")
    validate_parser.add_argument("keyword")
    validate_parser.set_defaults(handler=command_validate)

    add_parser = subparsers.add_parser("add", help="새 알림 등록")
    add_parser.add_argument("keyword")
    add_price_arguments(add_parser)
    add_parser.set_defaults(handler=command_add)

    update_parser = subparsers.add_parser("update", help="기존 알림 수정")
    update_parser.add_argument("user_keyword_seq", type=int)
    update_parser.add_argument("keyword")
    add_price_arguments(update_parser)
    update_parser.set_defaults(handler=command_update)

    remove_parser = subparsers.add_parser("remove", help="기존 알림 삭제")
    remove_parser.add_argument("user_keyword_seq", type=int)
    remove_parser.set_defaults(handler=command_remove)

    sync_parser = subparsers.add_parser(
        "sync-discounts", help="3개월 판매완료 평균보다 15% 낮은 상한으로 동기화"
    )
    sync_parser.set_defaults(handler=command_sync_discounts)
    return parser


def main() -> None:
    try:
        args = build_parser().parse_args()
        args.handler(args)
    except (KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"키체인에서 중고나라 세션을 읽지 못했습니다: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except (RuntimeError, ValueError, urllib.error.URLError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

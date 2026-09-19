#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog" / "products.json"
KST = timezone(timedelta(hours=9))

ALIASES = {
    "Osmo Action 4": ("osmoaction4", "오즈모액션4"),
    "Osmo Action 5 Pro": ("osmoaction5pro", "오즈모액션5프로"),
    "Osmo Action 6": ("osmoaction6", "오즈모액션6"),
    "Osmo Pocket 3": ("osmopocket3", "오즈모포켓3"),
    "Osmo Pocket 4": ("osmopocket4", "오즈모포켓4"),
    "Osmo Pocket 4P": ("osmopocket4p", "오즈모포켓4p"),
    "Galaxy Z Flip7": ("galaxyzflip7", "갤럭시z플립7", "갤럭시플립7", "zflip7"),
    "Galaxy Z Fold6": ("galaxyzfold6", "갤럭시z폴드6", "갤럭시폴드6", "zfold6"),
    "Galaxy Z Fold7": ("galaxyzfold7", "갤럭시z폴드7", "갤럭시폴드7", "zfold7"),
    "iPhone 15 Pro": ("iphone15pro", "아이폰15프로"),
    "iPhone 16": ("iphone16", "아이폰16"),
    "iPhone 16 Plus": ("iphone16plus", "아이폰16플러스"),
    "iPhone 16 Pro": ("iphone16pro", "아이폰16프로"),
    "iPhone 17": ("iphone17", "아이폰17"),
    "iPhone 17 Plus": ("iphone17plus", "아이폰17플러스"),
    "iPhone 17 Pro": ("iphone17pro", "아이폰17프로"),
    "iPhone Air": ("iphoneair", "아이폰에어"),
    "Sony FX3": ("sonyfx3", "소니fx3"),
    "Sony a6400": ("sonya6400", "소니a6400", "a6400"),
    "Sony a6700": ("sonya6700", "소니a6700", "a6700"),
    "Sony a7 III": ("sonya7iii", "소니a7iii", "a7iii", "a7m3", "a7mark3"),
    "Sony a7 IV": ("sonya7iv", "소니a7iv", "a7iv", "a7m4", "a7mark4"),
    "Sony a7 V": ("sonya7v", "소니a7v", "a7v", "a7m5", "a7mark5"),
    "Sony a7C II": ("sonya7cii", "소니a7cii", "a7cii", "a7c2"),
    "Sony a7CR": ("sonya7cr", "소니a7cr", "a7cr"),
    "Sony a7R V": ("sonya7rv", "소니a7rv", "a7rv", "a7r5"),
    "Sony a7R VI": ("sonya7rvi", "소니a7rvi", "a7rvi", "a7r6"),
    "Panasonic GH7": ("panasonicgh7", "파나소닉gh7", "lumixgh7", "루믹스gh7", "gh7"),
    "Panasonic S1R II": ("panasonics1rii", "파나소닉s1rii", "lumixs1rii", "s1r2"),
    "Panasonic S5 II": ("panasonics5ii", "파나소닉s5ii", "lumixs5ii", "s5ii", "s5m2"),
    "Panasonic S5 IIX": ("panasonics5iix", "파나소닉s5iix", "lumixs5iix", "s5iix", "s5m2x"),
    "Panasonic S9": ("panasonics9", "파나소닉s9", "lumixs9", "루믹스s9"),
    "Insta360 Ace Pro 2": ("insta360acepro2", "인스타360acepro2", "에이스프로2"),
    "Insta360 GO 3S": ("insta360go3s", "인스타360go3s", "go3s"),
    "Insta360 GO Ultra": ("insta360goultra", "인스타360고울트라", "goultra"),
    "Canon PowerShot V1": ("canonpowershotv1", "캐논powershotv1", "캐논파워샷v1", "powershotv1"),
    "Canon R1": ("canonr1", "캐논r1"),
    "Canon R10": ("canonr10", "캐논r10"),
    "Canon R3": ("canonr3", "캐논r3"),
    "Canon R5 Mark II": ("canonr5markii", "캐논r5markii", "캐논r5m2", "eosr5markii", "r5m2"),
    "Canon R6 Mark II": ("canonr6markii", "캐논r6markii", "캐논r6m2", "eosr6markii", "r6m2"),
    "Canon R6 Mark III": ("canonr6markiii", "캐논r6markiii", "캐논r6m3", "eosr6markiii", "r6m3"),
    "Canon R7": ("canonr7", "캐논r7"),
    "Canon R8": ("canonr8", "캐논r8"),
    "Nikon Zf": ("nikonzf", "니콘zf"),
    "Fujifilm X-E5": ("fujifilmxe5", "후지필름xe5", "후지xe5", "xe5"),
    "Fujifilm X-H2S": ("fujifilmxh2s", "후지필름xh2s", "후지xh2s", "xh2s"),
    "Fujifilm X-M5": ("fujifilmxm5", "후지필름xm5", "후지xm5", "xm5"),
    "Fujifilm X-S20": ("fujifilmxs20", "후지필름xs20", "후지xs20", "xs20"),
    "Fujifilm X-T5": ("fujifilmxt5", "후지필름xt5", "후지xt5", "xt5"),
    "Fujifilm X-T50": ("fujifilmxt50", "후지필름xt50", "후지xt50", "xt50"),
    "Fujifilm X100V": ("fujifilmx100v", "후지필름x100v", "후지x100v", "x100v"),
    "Fujifilm X100VI": ("fujifilmx100vi", "후지필름x100vi", "후지x100vi", "x100vi"),
    "Ricoh GR III": ("ricohgriii", "리코griii", "gr3"),
    "Ricoh GR IIIx": ("ricohgriiix", "리코griiix", "gr3x"),
}

BLOCKED = re.compile(
    r"삽니다|구매합니다|구해요|매입|최고가|대여|렌탈|교환원함|부품용|수리용|고장|파손|"
    r"액정\s*(불량|깨짐)|번인|잔상|터치\s*불가|박스만|박스\s*단품|케이스|필름|보호유리|"
    r"배터리\s*(단품|만)|충전기\s*(단품|만)|스트랩|마운트|커버|모형|목업|"
    r"노트북|완본체|데스크탑|게이밍\s*(컴퓨터|pc)|조립\s*pc|교환|"
    r"케이지|뷰파인더|메인보드|lcd\s*멍|액정\s*멍|레노버|리전\d|레이저\s*블레이드",
    re.IGNORECASE,
)


def compact(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣+]", "", value.casefold())


def model_matches(model: str, title: str) -> bool:
    text = compact(title)
    if model.startswith("RTX "):
        number = re.search(r"\d{4}", model).group()
        if f"rtx{number}" not in text:
            return False
        return ("ti" in model.casefold()) == ("ti" in text)
    if model.startswith("Galaxy S"):
        number = re.search(r"s\d+", model.casefold()).group()
        if number not in text or not ("galaxy" in text or "갤럭시" in text):
            return False
        suffixes = {"Ultra": ("ultra", "울트라", f"{number}u"), "Edge": ("edge", "엣지"), "FE": ("fe",), "+": ("+", "plus", "플러스")}
        wanted = next((key for key in suffixes if key in model), None)
        present = next((key for key, words in suffixes.items() if any(word in text for word in words)), None)
        return wanted == present
    aliases = ALIASES.get(model, (compact(model),))
    if not any(alias in text for alias in aliases):
        return False
    conflicts = {
        "Osmo Pocket 4": ("pocket4p", "포켓4p"),
        "iPhone 16": ("iphone16pro", "아이폰16프로", "아이폰16pro", "iphone16plus", "아이폰16플러스", "아이폰16plus"),
        "iPhone 15 Pro": ("iphone15promax", "아이폰15프로맥스", "아이폰15promax"),
        "iPhone 16 Pro": ("iphone16promax", "아이폰16프로맥스", "아이폰16promax"),
        "iPhone 17": ("iphone17pro", "아이폰17프로", "아이폰17pro", "iphone17plus", "아이폰17플러스", "아이폰17plus", "iphone17e", "아이폰17e"),
        "iPhone 17 Pro": ("iphone17promax", "아이폰17프로맥스", "아이폰17promax"),
        "Canon PowerShot V1": ("powershotv10", "파워샷v10"),
        "Canon R1": ("canonr10", "캐논r10"),
        "Nikon Zf": ("nikonzfc", "니콘zfc"),
        "Sony FX3": ("fx30",),
        "Fujifilm X-E5": ("xe4",),
        "Fujifilm X-M5": ("xt30",),
        "Sony a7 III": ("a7rii", "a7riii"),
        "Sony a7 IV": ("a7riv",),
        "Panasonic S5 II": ("s5iix", "s5m2x"),
        "Fujifilm X100V": ("x100vi",),
        "Ricoh GR III": ("griiix", "gr3x"),
    }
    if model == "Fujifilm X100VI" and re.search(r"x100v(?!i)", text):
        return False
    return not any(word in text for word in conflicts.get(model, ()))


def capacity(title: str) -> str | None:
    text = title.casefold().replace(" ", "")
    match = re.search(r"(?<!\d)(1)(?:tb|테라|t)(?!\w)", text)
    if match:
        return "1TB"
    match = re.search(r"(?<!\d)(128|256|512)(?:gb|기가|g)?(?!\d)", text)
    return f"{match.group(1)}GB" if match else None


def choose_variant(model: str, variants: list[str], title: str) -> str | None:
    if all(value in {"128GB", "256GB", "512GB", "1TB"} for value in variants):
        found = capacity(title)
        return found if found in variants else None
    if model == "RTX 3080":
        text = compact(title)
        if "12gb" in text or "12g" in text:
            return "12GB"
        if "10gb" in text or "10g" in text or not re.search(r"(?:8|16|20|24)g(?:b)?", text):
            return "10GB"
        return None
    if len(variants) == 1:
        return variants[0]
    text = compact(title)
    if model.startswith("Osmo Action"):
        if "어드벤처" in text or "어드밴처" in text or "adventure" in text:
            return "어드벤처"
        if "강화" in text:
            return "강화"
        return "스탠다드/본체"
    if model.startswith("Osmo Pocket"):
        if "크리에이터" in text or "creator" in text:
            return "크리에이터"
        if "브이로그" in text or "vlog" in text or "풀세트" in text or "세트" in text:
            return "브이로그/세트"
        return "스탠다드"
    return variants[0]


def minimum_price(product: dict) -> int:
    model = product["model"]
    if model.startswith("RTX "):
        return {
            "RTX 3080": 300_000, "RTX 3080 Ti": 400_000, "RTX 3090": 500_000,
            "RTX 4080": 800_000, "RTX 4090": 1_500_000, "RTX 5060": 300_000,
            "RTX 5070": 600_000, "RTX 5080": 1_200_000, "RTX 5090": 2_000_000,
        }[model]
    return {
        "NVIDIA": 150_000,
        "DJI": 100_000,
        "Samsung": 150_000,
        "Apple": 150_000,
        "Insta360": 80_000,
    }.get(product["brand"], 150_000)


def comparable(product: dict, title: str, description: str | None, price: int) -> bool:
    if price < minimum_price(product) or BLOCKED.search(title):
        return False
    if product["model"] == "Ricoh GR III" and "hdf" in title.casefold():
        return False
    if product["brand"] == "Insta360" and re.search(r"렌즈|그립", title) and not re.search(r"본체|카메라", title):
        return False
    if product["variant"] in {"Body", "바디", "본체", "일반형"} and re.search(
        r"렌즈|\d{2,3}[-~]\d{2,3}|\d+\s*(mm|미리)|올인원\s*세트", title, re.IGNORECASE
    ):
        return False
    return True


def record(product: dict, marketplace: str, item: dict, state: str, fetched_at: str) -> dict:
    timestamp = item.get("updated_at") if marketplace == "bunjang" else item.get("sorted_at")
    external_id = item.get("product_id") if marketplace == "bunjang" else item.get("sequence")
    result = {
        "marketplace": marketplace,
        "external_listing_id": str(external_id),
        "brand": product["brand"],
        "model": product["model"],
        "variant": product["variant"],
        "seller_external_id": str(item["seller_id"]) if item.get("seller_id") is not None else None,
        "seller_name": item.get("seller_name"),
        "title": item["title"],
        "listing_url": item["listing_url"],
        "price_krw": int(item["price_krw"]),
        "state": state,
        "listed_at": None,
        "updated_at": timestamp if state == "active" else None,
        "sold_at": timestamp if state == "sold" else None,
        "is_comparable": True,
        "exclusion_reason": None,
        "raw": {"source_fetched_at": fetched_at, "source_item": item},
    }
    return result


def normalize(raw: dict, catalog: dict) -> dict:
    normalized_fetched_at = datetime.fromisoformat(raw["fetched_at"].replace("Z", "+00:00")).astimezone(KST).isoformat(timespec="seconds")
    products_by_model: dict[str, list[dict]] = {}
    for product in catalog["products"]:
        products_by_model.setdefault(product["model"], []).append(product)
    output: dict[tuple[str, str], dict] = {}
    safety: dict[tuple[str, str], dict] = {}
    for query in raw["queries"]:
        products = products_by_model[query["model"]]
        variants = [product["variant"] for product in products]
        datasets = [
            ("joongna", "active", query["joongna"].get("available_listings") or [], query["joongna"].get("fetched_at")),
            ("joongna", "sold", (query["joongna"].get("sold_price_history") or {}).get("listings") or [], query["joongna"].get("fetched_at")),
            ("bunjang", "active", query["bunjang"].get("listings") or [], query["bunjang"].get("fetched_at")),
        ]
        for marketplace, state, items, source_fetched_at in datasets:
            for item in items:
                title = item.get("title") or ""
                if not model_matches(query["model"], title):
                    continue
                variant = choose_variant(query["model"], variants, title)
                product = next((value for value in products if value["variant"] == variant), None)
                if not product or not comparable(product, title, item.get("description"), int(item.get("price_krw") or 0)):
                    continue
                normalized = record(product, marketplace, item, state, source_fetched_at or raw["fetched_at"])
                key = (marketplace, normalized["external_listing_id"])
                previous = output.get(key)
                if previous is None or (previous["state"] != "active" and state == "active"):
                    output[key] = normalized
                seller_id = normalized["seller_external_id"]
                if seller_id:
                    safety[(marketplace, seller_id)] = {
                        "marketplace": marketplace,
                        "seller_external_id": seller_id,
                        "checked_at": source_fetched_at or raw["fetched_at"],
                        "verification_status": "unavailable",
                        "safe_trade_count": None,
                        "source_url": normalized["listing_url"],
                        "raw": {"reason": "MCP 응답에 판매자의 안전거래 횟수가 없음"},
                    }
    return {
        "run_id": raw["run_id"],
        "fetched_at": normalized_fetched_at,
        "listings": sorted(output.values(), key=lambda item: (item["brand"], item["model"], item["variant"], item["marketplace"], item["external_listing_id"])),
        "seller_safety_checks": sorted(safety.values(), key=lambda item: (item["marketplace"], item["seller_external_id"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP 원본을 살만한가 매물 스키마로 정규화")
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = normalize(json.loads(args.raw.read_text()), json.loads(CATALOG.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"normalized listings: {len(payload['listings'])}")
    print(f"seller safety checks: {len(payload['seller_safety_checks'])}")


if __name__ == "__main__":
    main()

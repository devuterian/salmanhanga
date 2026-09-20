#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "aggregates" / "sold-averages-2026-09-20.json"
API_URL = "https://search-api.joongna.com/v4/analysis/product-price/scatter-plot"
WINDOW_DAYS = 90
DISCOUNT_PERCENT = 15
ROUNDING_KRW = 10_000

SPECS = [
    ("Galaxy S22 Ultra", "갤럭시 S22 울트라", 150_000, ["Galaxy S22 Ultra", "갤럭시 s22 울트라"]),
    ("Galaxy S23 Ultra", "갤럭시 S23 울트라", 150_000, ["galaxy s23 ultra", "갤럭시 s23 울트라"]),
    ("Galaxy S22", "갤럭시 S22", 150_000, ["Galaxy S22", "갤럭시 s22"]),
    ("Galaxy S23", "갤럭시 S23", 150_000, ["Galaxy S23", "갤럭시 s23"]),
    ("iPhone 14 Pro", "아이폰 14 프로", 150_000, ["iPhone 14 pro", "아이폰 14 프로"]),
    ("iPhone 14 Pro Max", "아이폰 14 프로 맥스", 150_000, ["iphone 14 pro max", "아이폰 14 프로 맥스"]),
    ("Ricoh GR IV", "리코 GR4", 500_000, ["Ricoh GR IV", "리코 gr4"]),
    ("Sony RX100 VII", "소니 RX100M7", 500_000, ["Sony RX100 VII", "소니 RX100 VII"]),
    ("Panasonic TZ99 / ZS99", "파나소닉 TZ99", 300_000, ["Panasonic TZ99", "파나소닉 TZ99"]),
    ("Insta360 X6", "인스타360 X6", 300_000, ["insta360 x6", "인스타360 x6"]),
    ("DJI Mini 5 Pro", "DJI 미니 5 프로", 500_000, ["dji mini 5 pro", "DJI 미니 5 프로"]),
    ("DJI Air 3S", "DJI 에어 3S", 700_000, ["dji air 3s", "dji 에어 3s"]),
    ("DJI Mavic 4 Pro", "DJI 매빅 4 프로", 1_500_000, ["dji mavic 4 pro", "dji 매빅 4 프로"]),
    ("MacBook Air M4", "맥북 에어 M4", 700_000, ["macbook air m4", "맥북 에어 m4"]),
    ("MacBook Pro M4 Pro", "맥북 프로 M4 프로", 700_000, ["MacBook Pro M4 Pro", "맥북 프로 M4 프로"]),
    ("MacBook Pro M4 Max", "맥북프로 M4 MAX", 700_000, ["MacBook Pro M4 Max", "맥북 프로 M4 맥스"]),
    ("Apple Watch Series 10", "애플워치10", 150_000, ["Apple Watch S10", "애플워치 시리즈10"]),
    ("Apple Watch Ultra 2", "애플워치 울트라2", 150_000, ["apple watch ultra 2", "애플워치 울트라2"]),
]


def fetch_prices(search_word: str) -> list[int]:
    body = json.dumps(
        {
            "searchWord": search_word,
            "productPriceSize": 1,
            "dateRange": WINDOW_DAYS,
            "priceType": 1,
        }
    ).encode()
    request = urllib.request.Request(
        API_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    prices: list[int] = []
    for point in (payload.get("data", {}).get("productPrice") or {}).get("scatterPrices", []):
        for price_count in point.get("priceCounts", []):
            prices.extend([int(price_count["price"])] * int(price_count["count"]))
    return prices


def comparable_prices(prices: list[int], minimum: int) -> list[int]:
    candidates = [price for price in prices if price >= minimum]
    if not candidates:
        return []
    median = statistics.median(candidates)
    return [price for price in candidates if median * 0.5 <= price <= median * 1.75]


def alert_max_price(average: int) -> int:
    discounted = average * (100 - DISCOUNT_PERCENT) // 100
    return discounted // ROUNDING_KRW * ROUNDING_KRW


def main() -> None:
    rows = []
    for model, search_word, minimum, alert_keywords in SPECS:
        raw = fetch_prices(search_word)
        samples = comparable_prices(raw, minimum)
        average = round(sum(samples) / len(samples)) if samples else None
        rows.append(
            {
                "model": model,
                "search_word": search_word,
                "source_url": "https://web.joongna.com/search-price/"
                + urllib.parse.quote(search_word),
                "minimum_comparable_price_krw": minimum,
                "raw_sample_size": len(raw),
                "sample_size": len(samples),
                "average_price_krw": average,
                "alert_max_price_krw": alert_max_price(average) if average else None,
                "alert_keywords": alert_keywords,
            }
        )
    payload = {
        "schema_version": 1,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_days": WINDOW_DAYS,
        "discount_percent": DISCOUNT_PERCENT,
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(rows)} models)")


if __name__ == "__main__":
    main()

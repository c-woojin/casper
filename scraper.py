import json
import os
import random

import time

import requests

API_URL = "https://casper.hyundai.com/gw/wp/product/v2/product/exhibition/cars/E20260369"

BASE_PAYLOAD = {
    "carCode": "AX05",
    "subsidyRegion": "4131",
    "exhbNo": "E20260369",
    "sortCode": "50",
    "deliveryAreaCode": "",
    "deliveryLocalAreaCode": "",
    "carBodyCode": "",
    "carEngineCode": "",
    "carTrimCode": "",
    "exteriorColorCode": "",
    "interiorColorCode": [],
    "deliveryCenterCode": "",
    "wpaScnCd": "",
    "optionFilter": "",
    "minSalePrice": "",
    "maxSalePrice": "",
    "choiceOptYn": "Y",
    "pageNo": 1,
    "pageSize": 18,
}

REGIONS = [
    ("서울", "B", "B0"),
    ("인천", "D", "D1"),
    ("과천", "E", "E2"),
    ("광명", "E", "E3"),
    ("구리", "E", "E5"),
    ("김포", "E", "E7"),
    ("남양주", "E", "E8"),
    ("부천", "E", "EA"),
    ("성남", "E", "EB"),
    ("수원", "E", "EC"),
    ("용인", "E", "EM"),
    ("의정부", "E", "EP"),
    ("하남", "E", "EU"),
    ("강원", "F", "F0"),
    ("속초", "F", "F4"),
    ("양양", "F", "F6"),
    ("원주", "F", "F8"),
    ("춘천", "F", "FC"),
    ("세종", "W", "I9"),
    ("천안", "I", "IB"),
    ("대전", "H", "H0"),
    ("청주", "G", "G9"),
    ("대구", "M", "M0"),
    ("경주", "N", "N1"),
    ("포항", "N", "NL"),
    ("부산", "P", "P0"),
    ("울산", "U", "U0"),
    ("전주", "J", "JB"),
    ("목포", "L", "L7"),
    ("여수", "L", "LB"),
    ("광주", "K", "K0"),
    ("서귀포", "T", "T2"),
    ("제주", "T", "T1"),
]


def notify_slack(message: str):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("  (SLACK_WEBHOOK_URL 미설정, Slack 알림 생략)")
        return
    try:
        requests.post(webhook_url, json={"text": message}, timeout=10)
    except Exception as e:
        print(f"  Slack 알림 실패: {e}")


def fetch_cars(area_code: str, local_area_code: str) -> list:
    """지역별 모든 차량을 페이지네이션으로 수집"""
    all_cars = []
    page = 1

    while True:
        payload = {**BASE_PAYLOAD, "deliveryAreaCode": area_code, "deliveryLocalAreaCode": local_area_code, "pageNo": page}

        for attempt in range(3):
            try:
                resp = requests.post(API_URL, json=payload, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"  재시도 ({attempt + 1}/3): {e}")
                time.sleep(2)

        cars = data.get("data", {}).get("discountsearchcars", [])
        if not cars:
            break

        all_cars.extend(cars)

        total_count = data.get("data", {}).get("totalCount", 0)
        if len(all_cars) >= total_count:
            break

        page += 1
        time.sleep(random.uniform(0.5, 1))

    return all_cars


def main():
    result = {}
    failed = []

    print(f"캐스퍼 전시차량 조회 시작 (총 {len(REGIONS)}개 지역)")
    print("-" * 50)

    for i, (name, area, local) in enumerate(REGIONS, 1):
        try:
            cars = fetch_cars(area, local)
            result[name] = cars
            count = len(cars)
            print(f"[{i:2d}/{len(REGIONS)}] {name}: {count}대")

            if count > 0:
                notify_slack(f":car: *캐스퍼 차량 발견!* {name}: {count}대 배송 가능")

        except Exception as e:
            print(f"[{i:2d}/{len(REGIONS)}] {name}: 실패 - {e}")
            failed.append(name)
            result[name] = []

        if i < len(REGIONS):
            time.sleep(random.uniform(0.5, 1))

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    total = sum(len(v) for v in result.values())
    print(f"완료! 총 {total}대 수집 → result.json 저장")
    if failed:
        print(f"실패 지역: {', '.join(failed)}")


if __name__ == "__main__":
    main()

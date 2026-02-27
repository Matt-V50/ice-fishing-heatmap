import requests
import pandas as pd
import re
import os
from datetime import datetime, timedelta
import time


def get_sid() -> tuple[str, str]:
    """从页面获取新的 SID 和 session cookie"""
    url = (
        "https://cwroyalty.checkfront.com/reserve/item/"
        "?inline=1&header=hide&options=tabs"
        "&src=https%3A%2F%2Fwww.cwroyalty.com"
        "&pipe=https%3A%2F%2Fwww.cwroyalty.com%2Fwp-content%2Fplugins%2Fcheckfront-wp-booking%2Fpipe.html"
        "&ssl=1&provider=wordpress&category_id=37"
        "&start_date=2026-03-01&end_date=2026-03-01"
        "&cf-month=20260301&item_id=48"
    )
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    # 提取 SID
    match = re.search(r'id="SID"\s+name="SID"\s+value="([^"]+)"', resp.text)
    if not match:
        raise RuntimeError("Failed to extract SID from page")
    sid = match.group(1)

    # 提取 session cookie
    cookie = resp.cookies.get("RES", sid)

    print(f"[SID] {sid}")
    return sid, cookie


def query(start_date: str, end_date: str) -> pd.DataFrame:
    """
    查询 start_date 到 end_date 之间每一天的 timeslot 数据。
    start_date, end_date 格式: 'YYYY-MM-DD'
    """
    sid, cookie = get_sid()
    config = [{"name":"The Shack", "pg_parent_id": "48", "children-cal": "50", "children": "50", "item_id": "50", "seats": 4},  # The Shack
              {"name":"The Lakeview Cabin 1", "pg_parent_id": "51", "children-cal": "52", "children": "52", "item_id": "52", "seats": 6},  # The Lakeview Cabin 1
              {"name":"The Lakeview Cabin 2", "pg_parent_id": "196", "children-cal": "197", "children": "197", "item_id": "197", "seats": 6},  # The Lakeview Cabin 2
              {"name":"Angler's Paradise", "pg_parent_id": "54", "children-cal": "55", "children": "55", "item_id": "55", "seats": 7},  # Angler's Paradise
              {"name":"Winter Wonderland", "pg_parent_id": "127", "children-cal": "128", "children": "128", "item_id": "128", "seats": 8},  # Winter Wonderland
              {"name":"The Ice Palace", "pg_parent_id": "57", "children-cal": "58", "children": "58", "item_id": "58", "seats": 8},  # The Ice Palace
              ]

    url = "https://cwroyalty.checkfront.com/reserve/api/?call=rate"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://cwroyalty.checkfront.com",
        "referer": "https://cwroyalty.checkfront.com/reserve/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": f"RES={cookie}",
    }

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    all_rows = []

    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        date_key = current.strftime("%Y%m%d")
        
        for cfg in config:
            payload = (
                f"pg_parent_id={cfg['pg_parent_id']}&children-cal={cfg['children-cal']}&children={cfg['children']}"
                f"&start_date={date_str}&end_date={date_str}"
                f"&qty=1&slip=&customer_id=&date_id="
                f"&SID={sid}&layout=&line_id=&opt="
                f"&item_id={cfg['item_id']}&discount_code=&ui_date=1&ui_param=1"
            )
            seats = cfg['seats']

            try:
                resp = requests.post(url, headers=headers, data=payload, timeout=15)
                data = resp.json()

                timeslots = (
                    data.get("item", {})
                        .get("rate", {})
                        .get("dates", {})
                        .get(date_key, {})
                        .get("timeslots", {})
                )

                if isinstance(timeslots, dict):
                    timeslots = []
                else:                    
                    for slot in timeslots:
                        slot["seats"] = seats

                all_rows.extend(timeslots)

                print(f"[OK] {date_str} - {len(timeslots)} slots")

            except Exception as e:
                print(f"[ERR] {date_str} - {e}")

            current += timedelta(days=1)
            time.sleep(0.5)

    return pd.DataFrame(all_rows)


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")

    print(f"Querying {today} → {end}")
    df = query(today, end)

    # 保存到 data/ 目录（合并已有数据）
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "timeslots.csv")

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        old_df = pd.read_csv(out_path, dtype=str)
        # 如果没有 date 列，从 start_date (unix timestamp) 推算
        old_df["date"] = pd.to_numeric(old_df["start_date"], errors="coerce").apply(
            lambda ts: datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if pd.notna(ts) else None
        )
        # 只保留不在本次查询范围内的旧数据
        old_df = old_df[~old_df["date"].between(today, end)]
        old_df = old_df.drop(columns=["date"])
        df = pd.concat([old_df, df.astype(str)], ignore_index=True)

    # 按日期和时间排序
    df = df.sort_values(by=["start_time"], ignore_index=True)
    df = df[df["status"] == "A"]
    df.to_csv(out_path, index=False)
    print(f"\nDone: {len(df)} rows → {out_path}")
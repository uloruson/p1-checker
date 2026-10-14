import csv

DEFAULT_LIMIT = 3000
LIMITS = {"研修": 5000}


def get_limit(reason):
    """理由に応じた上限額を返す"""
    return LIMITS.get(reason, DEFAULT_LIMIT)


def check_request(r):
    """申請1件を判定し、(結果, コメント) を返す"""
    if r["reason"] == "":
        return "NG", "理由が未入力"

    try:
        fare = int(r["fare"])
    except ValueError:
        return "NG", f"金額が数値ではない（{r['fare']}）"

    limit = get_limit(r["reason"])
    if fare > limit:
        return "要確認", f"上限{limit}円を超過"
    return "OK", ""


def main():
    with open("requests.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["result"], r["comment"] = check_request(r)

    with open("result.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    ng = sum(1 for r in rows if r["result"] != "OK")
    print(f"{len(rows)}件を判定しました（要対応 {ng}件）→ result.csv")


if __name__ == "__main__":
    main()
import csv
import json

import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """あなたは経理部の交通費チェック担当です。
申請1件を受け取り、次のルールで判定してください。

# 判定ルール（上から順に判定し、最初に当てはまったものを採用する）
1. 金額が数値にできない、または理由が空 → NG
2. 理由が私用・業務と無関係 → NG
3. 理由が抽象的で、目的が読み取れない → 要確認
4. 金額が上限を超える → 要確認
5. それ以外 → OK
迷った場合は、OKにせず「要確認」とすること。

# 金額の扱い
"1,240円" "￥1240" "１２４０" などの表記ゆれは整数に直す。数値にできなければ null。

# 上限
- 研修・セミナー・勉強会など、学習目的のもの: 5000円
- それ以外: 3000円

# 判定例
- 理由「A社定例会議」→ OK（訪問先と目的が明確）
- 理由「顧客訪問」→ OK（業務目的が明確。訪問先の記載は任意）
- 理由「出張」→ OK（業務区分として十分。詳細は出張報告書で確認する）
- 理由「研修」→ OK（業務区分として十分）
- 理由「打ち合わせ」→ 要確認（相手と目的が不明）
- 理由「なんとなく」→ NG（業務目的ではない）

# 出力
次のJSONだけを出力すること。説明文やコードブロックは付けない。
{"fare": 整数またはnull, "verdict": "OK|要確認|NG", "comment": "判定理由を30字以内で"}"""

def ai_check(r):
    """Claudeに申請1件を判定させ、(結果の辞書, 入力トークン, 出力トークン) を返す"""
    user_text = (f"申請者: {r['name']}\n区間: {r['from']}→{r['to']}\n"
                 f"金額: {r['fare']}\n理由: {r['reason']}")
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )
    except anthropic.APIError as e:
        return {"fare": None, "verdict": "エラー", "comment": f"API失敗: {e}"}, 0, 0

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"fare": None, "verdict": "エラー", "comment": f"JSONでない応答: {text[:40]}"}
    return result, resp.usage.input_tokens, resp.usage.output_tokens


def main():
    with open("requests.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    total_in = total_out = 0
    for r in rows:
        result, tin, tout = ai_check(r)
        r["fare_ai"] = result.get("fare")
        r["result"] = result.get("verdict")
        r["comment"] = result.get("comment")
        total_in += tin
        total_out += tout
        print(f"{r['name']}: {r['result']}（{r['comment']}）")

    with open("result_ai.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cost_usd = total_in / 1_000_000 * 2 + total_out / 1_000_000 * 10
    print(f"トークン: 入力{total_in} / 出力{total_out}　概算 ${cost_usd:.4f}")

    match = miss = 0
    for r in rows:
        if r["result"] == r["expected"]:
            match += 1
        elif r["expected"] != "OK" and r["result"] == "OK":
            miss += 1
            print(f"見逃し: {r['name']}")
    print(f"一致率 {match / len(rows):.0%}（{match}/{len(rows)}）　見逃し {miss}件")


if __name__ == "__main__":
    main()
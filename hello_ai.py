import anthropic
from dotenv import load_dotenv

load_dotenv()                        # .env からキーを読み込む
client = anthropic.Anthropic()

resp = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=200,
    system="あなたは経理部のベテラン社員です。簡潔に答えてください。",
    messages=[
        {"role": "user", "content": "交通費精算でよくあるミスを3つ教えて"}
    ],
)
text = "".join(b.text for b in resp.content if b.type == "text").strip()
print(text)
print(resp.usage)                    # 使ったトークン数
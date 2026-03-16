import os
import asyncio
import requests
from datetime import datetime
from openai import OpenAI
from telegram import Bot
from notion_client import Client

# --- 설정 및 환경 변수 ---
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

pplx_client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)
notion = Client(auth=NOTION_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)



# 1. 브리프 생성 (Perplexity sonar - 웹 검색 내장)
def generate_brief():
    date_str = datetime.now().strftime("%Y년 %m월 %d일 %A")

    prompt = f"""오늘 날짜: {date_str}

아래 섹션 순서대로 모닝 브리프를 작성해줘. 웹 검색이 필요한 섹션은 반드시 최신 정보를 검색해서 작성해.

### 📅 날짜 및 요일
- 오늘 날짜와 요일을 한국어로 표시
- 특별한 날(명절, 기념일 등)이 있으면 함께 표시

### 🌤️ 오늘의 날씨 (인천)
- 인천 날씨: 최저/최고 기온, 날씨 상태
- 간단한 옷차림 조언 또는 우산 필요 여부

### 🌍 국제사회 핫뉴스 (1~2개)
- 오늘 기준 가장 주목받는 뉴스 1~2개
- 헤드라인, 핵심 요약(2~3문장), 향후 영향, 출처 링크

### 🇰🇷 오늘의 한국 뉴스 (1~2개)
- 경제/사회적으로 가장 주목해야 하는 뉴스 1~2개
- 헤드라인, 핵심 요약(2~3문장), 실생활 영향, 출처 링크

### 🤖 AI 뉴스 (2~3개)
- 최신 AI 관련 뉴스 2~3개
- 비전문가도 이해할 수 있게 쉽게 설명
- 제목, 중요한 이유, 실무 영향

### 🔄 메인 AI 툴 업데이트
- ChatGPT, Gemini, Claude, Perplexity, Grok, Kimi 각각의 최신 버전/변경사항 정리
- 변경 없으면 "최근 변경 없음"으로 표기

### 🛠️ AI 툴 데일리 업데이트
- 어제 소셜에서 화제였던 실제 프롬프트 1~2개 (원문 + 한국어 번역)
- 비주류 신서비스 2~3개 (이게 뭔지 / 써볼 기능 / 퀵스타트)

### 💻 바이브코딩 지식 (1개)
- AI 활용 개발 핵심 용어 중 1개 선정해서 설명
- 한 줄 요약, 실생활 비유, 왜 주목받는지, 활용 시나리오

### 🎬 AI 유튜브 추천 (1개)
- 최근 화제의 AI 관련 한국어 유튜브 영상 1개
- 제목, 채널명, 소개, 추천 이유, URL

### 📚 오늘의 10분 학습 – 개발/코딩 용어 (1개)
- 개발/코딩 필수 용어 중 1개 선정해서 설명
- 한 줄 요약, 실생활 비유, 사용 사례 2~3개, 비개발자가 알면 좋은 이유

### 📊 마케팅 트렌드 (2개)
- 글로벌 트렌드 1개, 일본 트렌드 1개
- 각각 설명과 실무 활용 팁

### 🎵 오늘의 노동요 – 클래식 추천 (1개)
- 베토벤, 브람스 등 집중력 높여주는 클래식 1곡
- 곡명, 연주 추천, 분위기, 어울리는 업무 상황, YouTube 검색 키워드
"""

    response = pplx_client.chat.completions.create(
        model="sonar",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# 2. 텔레그램 전송 (4096자 제한으로 분할)
async def send_telegram(text):
    MAX_LEN = 4000
    chunks = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for chunk in chunks:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)


# 3. 노션 업로드
def upload_notion(brief):
    date_str = datetime.now().strftime("%b %d")
    try:
        notion.pages.create(
            parent={"database_id": NOTION_PAGE_ID},
            properties={
                "Name": {"title": [{"text": {"content": f"☀️ Morning Brief - {date_str}"}}]}
            },
            children=[
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": brief[:2000]}}]}}
            ]
        )
        print("✅ 노션 업로드 완료!")
    except Exception as e:
        print(f"❌ 노션 에러: {e}")


async def main():
    print("🚀 브리핑 생성 시작...")
    brief = generate_brief()
    print("✅ 브리프 생성 완료")

    await send_telegram(brief)
    print("✅ 텔레그램 전송 완료")

    upload_notion(brief)
    print("✅ 모든 전송 완료!")


if __name__ == "__main__":
    asyncio.run(main())

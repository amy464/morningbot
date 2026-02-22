import os
import asyncio
import edge_tts
import google.generativeai as genai
from telegram import Bot
from notion_client import Client

# 1. 환경변수 설정
genai.configure(api_key=os.environ.get("GEMINI_API"))
notion = Client(auth=os.environ.get("NOTION_TOKEN"))
telegram_bot = Bot(token=os.environ.get("TELEGRAM_TOKEN"))

# 2. 대화형 스크립트 생성 (NotebookLM 스타일)
def generate_script():
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = """
    오늘의 날씨, AI 뉴스, 바이브코딩 용어(RAG), 개발 용어(API)를 바탕으로
    남성 호스트 '인준'과 여성 호스트 '선희'가 대화하는 팟캐스트 대본을 작성해줘.
    - 아주 친근하고 싶게, "오 정말요?" 같은 추임새 포함.
    - 형식: [인준] 대사 / [선희] 대사
    """
    response = model.generate_content(prompt)
    return response.text

# 3. 오디오 생성 (Edge-TTS 활용 - 무료)
async def create_audio(script):
    # 스크립트를 파싱해서 [인준]은 남성 목소리, [선희]는 여성 목소리로 생성 후 합치기
    # (pydub 라이브러리로 mp3 파일들을 연결)
    pass

# 4. 배포 (텔레그램 & 노션)
def deploy(audio_path, text_content):
    # 텔레그램으로 오디오 전송
    # 노션 페이지 생성 및 텍스트 업로드
    pass

async def main():
    script = generate_script()
    await create_audio(script)
    deploy(None, script)

if __name__ == "__main__":
    asyncio.run(main())

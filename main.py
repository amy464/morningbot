import os
import asyncio
import random
import requests
from datetime import datetime
from google import genai
import edge_tts
from pydub import AudioSegment
from telegram import Bot
from notion_client import Client

# --- 설정 및 환경 변수 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
notion = Client(auth=NOTION_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)

# --- 데이터 목록 ---
AI_TERMS = [
    "LLM", "Prompt", "Token", "RAG", "Vector DB", "Agent", "MCP", "Fine-tuning",
    "Embedding", "Hallucination", "Transformer", "Attention", "GPT", "BERT", "Diffusion",
    "Reinforcement Learning", "Zero-shot", "Few-shot", "Chain of Thought", "Multimodal",
    "Tokenizer", "Context Window", "Temperature", "Top-p", "Inference",
    "Training", "Overfitting", "Underfitting", "Benchmark", "RLHF",
    "Instruction Tuning", "Quantization", "LoRA", "Distillation", "Perplexity",
    "Semantic Search", "Cosine Similarity", "Neural Network", "Deep Learning", "Gradient Descent",
    "Backpropagation", "Activation Function", "Batch Size", "Epoch", "Learning Rate",
    "Dropout", "Normalization", "Softmax", "Cross-Entropy", "Autoregressive"
]

DEV_TERMS = [
    "API", "REST", "JSON", "HTTP", "Backend", "Frontend", "Docker", "CI/CD", "Git", "Database",
    "Webhook", "OAuth", "JWT", "HTTPS", "GraphQL", "gRPC", "WebSocket", "CDN", "DNS", "SSL",
    "Kubernetes", "Microservice", "Monolith", "Cache", "Queue",
    "Async", "Sync", "Thread", "Process", "Memory",
    "SQL", "NoSQL", "Index", "Query", "Migration",
    "Deployment", "Staging", "Production", "Rollback", "Blue-Green",
    "Unit Test", "Integration Test", "TDD", "Code Review", "Refactoring",
    "Repository", "Branch", "Merge", "Pull Request", "Commit"
]


# 1. 날씨 정보 가져오기 (인천)
def get_weather():
    try:
        res = requests.get("https://wttr.in/Incheon?format=j1").json()
        curr = res['current_condition'][0]
        temp = res['weather'][0]
        return f"현재 {curr['lang_ko'][0]['value']}, 기온 {curr['temp_C']}도 (최저 {temp['mintemp_C']} / 최고 {temp['maxtemp_C']})"
    except:
        return "날씨 정보를 가져올 수 없습니다."


# 2. 대본 및 내용 생성 (Gemini)
def generate_content():
    ai_term = random.choice(AI_TERMS)
    dev_term = random.choice(DEV_TERMS)
    weather = get_weather()
    date_str = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""
    오늘 날짜: {date_str}
    인천 날씨: {weather}
    오늘의 AI 용어: {ai_term}
    오늘의 개발 용어: {dev_term}

    위 정보를 바탕으로 '인준(남성)'과 '선희(여성)'가 진행하는 5분 팟캐스트 대본을 써줘.
    - [인준]과 [선희] 이름을 문장 앞에 붙일 것.
    - 아주 친근하고 유머러스하게, 초등학생도 이해할 비유를 들어서 설명해줘.
    - 날씨에 맞는 옷차림 조언과 마지막에 브람스나 베토벤 같은 노동요 클래식 추천도 포함해줘.
    """
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text, ai_term, dev_term


# 3. 오디오 생성 (Edge-TTS)
async def create_audio(script_text):
    lines = script_text.split('\n')
    parts = []

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        if "[인준]" in line:
            voice = "ko-KR-InJoonNeural"
            text = line.replace("[인준]", "").strip()
        elif "[선희]" in line:
            voice = "ko-KR-SunHiNeural"
            text = line.replace("[선희]", "").strip()
        else:
            continue

        file_path = f"part_{i}.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file_path)
        parts.append(AudioSegment.from_mp3(file_path))

    # 오디오 합치기
    combined = sum(parts)
    combined.export("morning_brief.mp3", format="mp3")

    # 임시 파일 삭제
    for i in range(len(lines)):
        if os.path.exists(f"part_{i}.mp3"):
            os.remove(f"part_{i}.mp3")


# 4. 노션 및 텔레그램 전송
async def main():
    print("🚀 브리핑 생성 시작...")
    script, ai_t, dev_t = generate_content()
    await create_audio(script)

    # 1. 텔레그램 전송
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"📅 오늘의 브리핑: {ai_t} & {dev_t}")
    with open("morning_brief.mp3", "rb") as audio:
        await bot.send_audio(chat_id=TELEGRAM_CHAT_ID, audio=audio)

    # 2. 노션 데이터베이스에 업로드
    try:
        notion.pages.create(
            parent={"database_id": NOTION_PAGE_ID},
            properties={
                "Name": {"title": [{"text": {"content": f"☀️ Morning Brief - {datetime.now().strftime('%b %d')}"}}]},
                "TL;DR": {"rich_text": [{"text": {"content": f"오늘의 AI: {ai_t} / 개발: {dev_t}"}}]}
            },
            children=[
                {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🎙️ 오늘의 팟캐스트 대본"}}]}},
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": script}}]}}
            ]
        )
        print("✅ 노션 업로드 완료!")
    except Exception as e:
        print(f"❌ 노션 에러 발생: {e} (연결 추가를 확인하세요!)")

    print("✅ 모든 전송 완료!")


if __name__ == "__main__":
    asyncio.run(main())

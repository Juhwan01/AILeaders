from asyncio.log import logger
from fastapi import APIRouter, Depends, Response
from deep_translator import GoogleTranslator# from domains.users.services import UserService
# from domains.users.repositories import UserRepository
from domains.users.dto import (
    ChainDTO,
    ChatHistory,
    TTSRequest,
)
from domains.users.models import (
    ChainStore,
)
from dependencies.Rag import create_chain
from dependencies.data import appendData
from fastapi.responses import JSONResponse
from langdetect import detect
import io
from datetime import datetime
import json
import os
import re
from gtts import gTTS

from openai import OpenAI
from fastapi import HTTPException
from dotenv import load_dotenv


load_dotenv()
OPENAI_API_KEY = os.getenv("openai_api_key")
client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()
name = "users"
chain_store= ChainStore()


async def mask_personal_info(text):
    print("start")
    if not text.strip():  # 빈 문자열이면 그대로 반환
        return text
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """당신은 개인정보 보호 전문가입니다. 주어진 텍스트에서 개인정보를 식별하고 정확히 마스킹하는 것이 당신의 임무입니다. 다음 지침을 따라 주어진 텍스트를 처리하세요:

1. 이름: 성을 제외한 이름을 '*'로 대체합니다. 예: 홍길동 -> 홍**
2. 주민등록번호: 앞 6자리를 제외한 나머지를 '*'로 대체합니다. 예: 901225-1234567 -> 901225-*******
3. 전화번호: 중간 4자리를 '*'로 대체합니다. 예: 010-1234-5678 -> 010-****-5678
4. 이메일 주소: '@' 앞부분의 절반을 '*'로 대체합니다. 예: example@email.com -> exa***@email.com
5. 주소: 시/군/구 이후의 상세 주소를 '*'로 대체합니다. 예: 서울시 강남구 테헤란로 152 -> 서울시 강남구 *****
6. 신용카드 번호: 마지막 4자리를 제외한 나머지를 '*'로 대체합니다. 예: 1234-5678-9012-3456 -> ****-****-****-3456
7. 계좌번호: 앞 4자리와 뒤 2자리를 제외한 나머지를 '*'로 대체합니다. 예: 123-456-789012 -> 123-***-**9012
8. IP 주소: 마지막 옥텟을 '*'로 대체합니다. 예: 192.168.0.1 -> 192.168.0.*

추가적인 텍스트를 생성하지 마세요. 원본 텍스트를 그대로 유지하면서 개인정보만 마스킹하세요. 개인정보가 없는 경우 원본 텍스트를 그대로 반환하세요."""},
                {"role": "user", "content": text}
            ]
        )
        masked_text = response.choices[0].message.content.strip()
        # 추가 설명이 포함된 경우 제거
        if "개인정보" in masked_text:
            return text  # 원본 텍스트 반환
        return masked_text
    except Exception as e:
        logger.error(f"Error masking personal information: {str(e)}")
        return text  # 에러 발생 시 원본 텍스트 반환

@router.post("/save_chat")
async def save_chat(chat_history: ChatHistory):
    save_dir = "chat_histories"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.json"
    filepath = os.path.join(save_dir, filename)
    
    masked_messages = []
    for message in chat_history.messages:
        masked_message = {
            "대화셋일련번호": message.대화셋일련번호,
            "고객질문": await mask_personal_info(message.고객질문),
            "상담사답변": message.상담사답변
        }
        masked_messages.append(masked_message)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(masked_messages, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved masked chat history to {filepath}")
    appendData(filename)
    return {"message": "Masked chat history saved successfully", "file": filename}

def translate_to_korean(text):
    try:
        lang = detect(text)
        if lang != 'ko':
            translator = GoogleTranslator(source='auto', target='ko')
            return translator.translate(text)
        return text
    except:
        return text  # 번역 실패 시 원본 텍스트 반환

def get_chain_store():
    return chain_store

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en'  # 기본값으로 영어 설정
    


async def ChainStart():
    dataset_path = 'log.json'
    chain = create_chain(dataset_path)
    chain_store.set_chain(chain)
    print("Chain created")

@router.post("/use_chain")
async def use_chain(payload: ChainDTO,store: ChainStore = Depends(get_chain_store)):
    chain = store.get_chain()
    print(payload.query)
    query=payload.query
    lang = detect_language(query)
    if chain:
        if lang != 'ko':  # 한국어가 아닌 경우
            translated_question = translate_to_korean(query)
            answer = chain.invoke(translated_question)
            response = chain.invoke(f"Rewrite the following in English: {answer}")
            return response
        else:
            response = chain.invoke(query)
            return response
    else:
        return JSONResponse(content={"message": "Chain not found"}, status_code=404)



@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    tts = gTTS(text=request.text, lang=request.lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_data = fp.getvalue()
    
    return Response(content=audio_data, media_type="audio/mpeg") 
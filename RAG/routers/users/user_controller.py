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

router = APIRouter()
name = "users"
chain_store= ChainStore()



def mask_personal_info(text):
    # 이름 마스킹
    text = re.sub(r'\b[가-힣]{2,4}\b', '[PERSON]', text)
    
    # 이메일 주소 마스킹
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
    
    # 전화번호 마스킹 (다양한 형식)
    text = re.sub(r'\b(\d{2,4}[-\s]?)+\d{4}\b', '[PHONE]', text)
    
    return text

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
            # "고객질문(요청)": mask_personal_info(message.고객질문_요청),
            # "상담사질문(요청)": mask_personal_info(message.상담사질문_요청)
            "고객질문": message.고객질문,
            "상담사답변": message.상담사답변
        }
        masked_messages.append(masked_message)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(masked_messages, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved masked chat history to {filepath}")
    appendData(filename)
    return {"message": "Masked chat history saved successfully", "file": filename}


@router.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    tts = gTTS(text=request.text, lang=request.lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_data = fp.getvalue()
    
    return Response(content=audio_data, media_type="audio/mpeg") 
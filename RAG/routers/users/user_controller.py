from fastapi import APIRouter, Depends
from deep_translator import GoogleTranslator# from domains.users.services import UserService
# from domains.users.repositories import UserRepository
from domains.users.dto import (
    ChainDTO,
)
from domains.users.models import (
    ChainStore,
)
from dependencies.Rag import create_chain
from fastapi.responses import JSONResponse
from langdetect import detect

router = APIRouter()
name = "users"
chain_store= ChainStore()



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
    dataset_path = '민원.json'
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

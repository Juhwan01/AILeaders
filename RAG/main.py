import logging
import traceback
from typing import List
from urllib.request import Request
from pydantic import BaseModel
from gtts import gTTS
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn
from dependencies.database import init_db
from dependencies.config import get_config
from routers import router as main_router
from routers.users.user_controller import ChainStart
import asyncio
import io
from datetime import datetime
import json
import os
import re

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

init_db(config=get_config())

app = FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.include_router(router=main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


async def add_cors_to_response(
    request: Request, response: JSONResponse
) -> JSONResponse:
    origin = request.headers.get("origin")

    # Set CORS CORS header.
    if origin:
        cors = CORSMiddleware(
            app=app,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        response.headers.update(cors.simple_headers)
        has_cookie = "cookie" in request.headers

        # Allow Origin header if CORS is allowed.
        if cors.allow_all_origins and has_cookie:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not cors.allow_all_origins and cors.is_allowed_origin(
            origin=origin,
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add_vary_header("Origin")
    return response



class Message(BaseModel):
    sender: str
    text: str

class ChatHistory(BaseModel):
    messages: List[Message]

# def mask_personal_info(text):
#     # 이름 마스킹
#     text = re.sub(r'\b[가-힣]{2,4}\b', '[PERSON]', text)
    
#     # 이메일 주소 마스킹
#     text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
    
#     # 전화번호 마스킹 (다양한 형식)
#     text = re.sub(r'\b(\d{2,4}[-\s]?)+\d{4}\b', '[PHONE]', text)
    
#     return text

@app.post("/api/save_chat")
async def save_chat(chat_history: ChatHistory):
    save_dir = "chat_histories"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.json"
    filepath = os.path.join(save_dir, filename)
    
    formatted_messages = []
    dialogue_set_number = f"B{timestamp}"
    
    for message in chat_history.messages:
        qa = "Q" if message.sender == "user" else "A"
        formatted_message = {
            "대화셋일련번호": dialogue_set_number,
            "QA": qa,
            "고객질문(요청)": message.text if message.sender == "user" else "",
            "답변": message.text if message.sender != "user" else ""
        }
        formatted_messages.append(formatted_message)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(formatted_messages, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved formatted chat history to {filepath}")
    
    return {"message": "Formatted chat history saved successfully", "file": filename}




class TTSRequest(BaseModel): # gtts
    text: str
    lang: str

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    tts = gTTS(text=request.text, lang=request.lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_data = fp.getvalue()
    
    return Response(content=audio_data, media_type="audio/mpeg") 

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )


# 애플리케이션 실행 (개발 서버)
if __name__ == "__main__":
    asyncio.run(ChainStart())  # ChainStart 함수를 비동기로 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
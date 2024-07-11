from pydantic import BaseModel
from typing import List

class ChainDTO(BaseModel):
    query: str

class ChatHistory(BaseModel): # json 저장
    messages: list

class TTSRequest(BaseModel): # gtts
    text: str
    lang: str

class ChatMessage(BaseModel):
    대화셋일련번호: str
    고객질문: str
    상담사답변: str
class ChatHistory(BaseModel):
    messages: List[ChatMessage]
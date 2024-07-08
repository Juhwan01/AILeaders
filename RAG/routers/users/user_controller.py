from fastapi import APIRouter, Depends

# from domains.users.services import UserService
# from domains.users.repositories import UserRepository
from domains.users.dto import (
    ChainDTO,
)
from domains.users.models import (
    ChainStore,
)
from dependencies.Rag import create_chain
from fastapi.responses import JSONResponse
router = APIRouter()
name = "users"
chain_store= ChainStore()

def get_chain_store():
    return chain_store


async def ChainStart():
    dataset_path = 'Conversation_Data.json'
    chain = create_chain(dataset_path)
    chain_store.set_chain(chain)
    print("Chain created")

@router.post("/use_chain")
async def use_chain(payload: ChainDTO,store: ChainStore = Depends(get_chain_store)):
    chain = store.get_chain()
    print(payload.query)
    query=payload.query
    if chain:
        answer = chain.invoke(query)
        if answer:
            return answer
        else:
            return "실행 오류"
    else:
        return JSONResponse(content={"message": "Chain not found"}, status_code=404)
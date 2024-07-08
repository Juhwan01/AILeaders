from fastapi import APIRouter, Depends
from dependencies.database import provide_session

from domains.users.services import UserService
from domains.users.repositories import UserRepository
from domains.users.dto import (
    UserItemGetResponse,
    UserPostRequest,
    UserPostResponse,
)

router = APIRouter()

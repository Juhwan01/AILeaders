from domains import Service
from fastapi import HTTPException, status

from .repositories import UserRepository


class UserService(Service):
    def __init__(
        self,
        *,
        user_repository: UserRepository,
    ):
        self._user_repository = user_repository

    
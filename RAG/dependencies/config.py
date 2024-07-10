import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class DefaultConfig(BaseSettings):
    postgresql_endpoint: str = os.getenv("POSTGRESQL_ENDPOINT", "postgresql")
    postgresql_port: int = os.getenv("POSTGRESQL_PORT", "32752")
    postgresql_table: str = os.getenv("POSTGRESQL_TABLE", "reaction_db")
    postgresql_user: str = os.getenv("POSTGRESQL_USER", "")
    postgresql_password: str = os.getenv("POSTGRESQL_PASSWORD", "")


@lru_cache
def get_config():
    return DefaultConfig()

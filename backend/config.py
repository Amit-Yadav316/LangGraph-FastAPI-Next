from pydantic import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    redis_url: str =  Field(..., env="REDIS_URL")
    pinecone_api_key: str =  Field(..., env="PINECONE_API_KEY")
    pinecone_env: str =  Field(..., env="PINECONE_ENV")
    pinecone_index_name: str =  Field(..., env="PINECONE_INDEX_NAME")

    class Config:
        env_file = ".env"

settings = Settings()
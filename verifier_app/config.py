from typing import Optional

from pydantic_settings import BaseSettings


class ProtocolProperties(BaseSettings):
    prover_host: str
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env_verifier"


protocol_properties = ProtocolProperties()

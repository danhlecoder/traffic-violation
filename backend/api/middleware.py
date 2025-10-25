"""
FastAPI Middleware Configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.config import settings


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware
    """
    origins_env = settings.ALLOWED_ORIGINS
    allow_all = origins_env.strip() == "*"
    origins = ["*"] if allow_all else [o.strip() for o in origins_env.split(",") if o.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False if allow_all else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

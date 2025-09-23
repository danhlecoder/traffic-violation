import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .routers import streams_router


app = FastAPI(title="Traffic Violation Backend", version="0.1.0")

# Allow frontend to access API in dev/local setups
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
_allow_all = _origins_env.strip() == "*"
_origins = ["*"] if _allow_all else [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False if _allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(streams_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

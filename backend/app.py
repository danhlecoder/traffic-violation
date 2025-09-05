from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pathlib import Path

from .src.rtsp_stream.streamer import generate_mjpeg


app = FastAPI(title="Traffic Violation Backend", version="0.1.0")

# Allow frontend to access API in dev/local setups
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stream")
def stream(
    rtsp: Optional[str] = Query(None, alias="src"),
    fps: int = Query(30, ge=1, le=60),
    quality: int = Query(80, ge=10, le=95),
):
    """
    MJPEG stream from RTSP/HTTP video source.

    Usage (frontend <img>):
      <img src="http://localhost:8000/api/stream?src=ENCODED_RTSP_URL" />
    """
    if not rtsp:
        raise HTTPException(status_code=400, detail="Missing 'src' query (RTSP/URL)")

    generator = generate_mjpeg(rtsp, fps=fps, jpeg_quality=quality)
    return StreamingResponse(generator, media_type="multipart/x-mixed-replace; boundary=frame")


# Optional root for quick sanity check
@app.get("/")
def root():
    return JSONResponse({"service": "traffic-backend", "endpoints": ["/api/health", "/api/stream?src=..."]})


# Serve a favicon to avoid 404s when accessing backend directly
@app.get("/favicon.ico")
def favicon():
    repo_root = Path(__file__).resolve().parent.parent
    candidates = [
        repo_root / "frontend" / "dist" / "logo.png",
        repo_root / "frontend" / "public" / "logo.png",
    ]
    for p in candidates:
        if p.exists():
            return FileResponse(p, media_type="image/png")
    raise HTTPException(status_code=404, detail="favicon not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

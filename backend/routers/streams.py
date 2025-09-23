from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from ..src.rtsp_stream.streamer import generate_mjpeg


router = APIRouter()


@router.get("/api/stream")
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



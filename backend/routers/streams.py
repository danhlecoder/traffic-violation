from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, Response

from ..src.rtsp_stream.streamer import generate_mjpeg, open_capture
import cv2


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


@router.get("/api/snapshot")
def snapshot(
    rtsp: Optional[str] = Query(None, alias="src"),
    quality: int = Query(85, ge=10, le=95),
):
    """
    Return a single JPEG frame from the source for annotation snapshot.
    """
    if not rtsp:
        raise HTTPException(status_code=400, detail="Missing 'src' query (RTSP/URL)")

    cap = open_capture(rtsp, reconnect=False, timeout_sec=5)
    if cap is None:
        raise HTTPException(status_code=503, detail="Cannot open source")
    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            raise HTTPException(status_code=502, detail="Failed to read frame")
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise HTTPException(status_code=500, detail="Encode JPEG failed")
        jpg: bytes = buf.tobytes()
        return Response(content=jpg, media_type="image/jpeg")
    finally:
        try:
            cap.release()
        except Exception:
            pass


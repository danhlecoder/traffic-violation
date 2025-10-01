from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..src.services.db import get_db


router = APIRouter()


class Point(BaseModel):
  x: float = Field(ge=0.0, le=1.0)
  y: float = Field(ge=0.0, le=1.0)

class CameraRegion(BaseModel):
  stopLine: Optional[tuple[Point, Point]] = None
  roi: Optional[list[Point]] = None

class Camera(BaseModel):
  id: str
  name: str
  rtsp: str
  location: str
  regions: Optional[CameraRegion] = None


@router.get('/api/cameras')
def list_cameras():
  """Trả về danh sách camera + vùng vẽ đã lưu."""
  db = get_db()
  items = list(db.cameras.find({}))
  for x in items:
    x['id'] = x.get('id') or x.get('_id')
    x.pop('_id', None)
  return items


@router.post('/api/cameras')
def upsert_camera(cam: Camera):
  """Thêm hoặc cập nhật camera theo id."""
  db = get_db()
  # Không ghi đè các field None (vd: regions=None) để tránh mất dữ liệu hiện có
  doc = cam.model_dump(exclude_none=True) if hasattr(cam, 'model_dump') else cam.dict(exclude_none=True)  # pydantic v1/v2
  db.cameras.update_one({'id': cam.id}, {'$set': doc}, upsert=True)
  return { 'ok': True }


@router.get('/api/cameras/{cam_id}')
def get_camera(cam_id: str):
  db = get_db()
  doc = db.cameras.find_one({'id': cam_id})
  if not doc:
    raise HTTPException(status_code=404, detail='Camera not found')
  doc['id'] = doc.get('id') or doc.get('_id')
  doc.pop('_id', None)
  return doc


@router.put('/api/cameras/{cam_id}/regions')
def update_regions(cam_id: str, regions: CameraRegion):
  """Cập nhật tọa độ vạch dừng và ROI theo chuẩn hóa 0..1."""
  db = get_db()
  # Chỉ cập nhật phần được gửi lên, không xoá phần còn lại (merge từng field)
  payload = regions.model_dump(exclude_unset=True, exclude_none=True) if hasattr(regions, 'model_dump') else regions.dict(exclude_unset=True, exclude_none=True)
  if not payload:
    return { 'ok': True }
  updates = { f'regions.{k}': v for k, v in payload.items() }
  db.cameras.update_one({'id': cam_id}, {'$set': updates}, upsert=True)
  return { 'ok': True }


@router.delete('/api/cameras/{cam_id}')
def delete_camera(cam_id: str):
  """Xóa camera theo id (bao gồm regions)."""
  db = get_db()
  res = db.cameras.delete_one({'id': cam_id})
  if res.deleted_count == 0:
    raise HTTPException(status_code=404, detail='Camera not found')
  return { 'ok': True }



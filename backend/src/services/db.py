import os
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError
import yaml

_client: Optional[MongoClient] = None

def _build_uri_from_yaml() -> Optional[str]:
  """Đọc file YAML cấu hình server và tạo URI MongoDB.
  """
  try:
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'configs', 'server.yaml')
    cfg_path = os.path.abspath(cfg_path)
    if not os.path.exists(cfg_path):
      return None
    with open(cfg_path, 'r', encoding='utf-8') as f:
      y = yaml.safe_load(f) or {}
    node = (y.get('database') or {}).get('mongo_camera') or {}
    host = node.get('host', 'localhost')
    port = int(node.get('port', 27017))
    db = node.get('database', 'traffic')
    user = node.get('username') or ''
    pwd = node.get('password') or ''
    auth = node.get('authSource') or 'admin'
    options = node.get('options') or ''
    cred = ''
    if user and pwd:
      cred = f"{user}:{pwd}@"
      opt_q = f"authSource={auth}"
      if options:
        options = (options.lstrip('?') + '&' + opt_q) if '?' in options else ('?' + options + '&' + opt_q)
      else:
        options = '?' + opt_q
    uri = f"mongodb://{cred}{host}:{port}/{db}{options}"
    return uri
  except Exception:
    return None

def get_client() -> MongoClient:
  """Khởi tạo MongoClient 1 lần (singleton đơn giản)."""
  global _client
  if _client is None:
    uri = _build_uri_from_yaml()
    _client = MongoClient(uri)
  return _client

def get_db():
  """Trả về database theo uri (mặc định db name là 'traffic')."""
  client = get_client()
  # Nếu MONGODB_URI không chứa db name, mặc định dùng 'traffic'
  uri = _build_uri_from_yaml()
  db_name = uri.rsplit('/', 1)[-1] or 'traffic'
  return client[db_name]

def init_indexes():
  """Khởi tạo các index cần thiết cho CSDL (chạy 1 lần lúc khởi động).
  - Tạo unique index cho trường `id` của collection `cameras` để đảm bảo không trùng ID.
  """
  try:
    db = get_db()
    db.cameras.create_index('id', unique=True, name='uniq_camera_id')
  except PyMongoError:
    # Không làm crash app nếu tạo index lỗi (ví dụ quyền hạn), chỉ bỏ qua
    pass



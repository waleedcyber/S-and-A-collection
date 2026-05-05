from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
resp = client.get("/api/products/random")
print('STATUS', resp.status_code)
try:
    data = resp.json()
except Exception as e:
    print('JSON ERR', e)
    print(resp.text)
    raise
print('COUNT', len(data) if isinstance(data, list) else 'not-list')
import json
print(json.dumps(data, indent=2, default=str))

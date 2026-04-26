from src.ServerParcer.Parcer import ParcerItem
from src.ServerParcer import OriginalParcer
import uuid
from fastapi import FastAPI
from pathlib import Path
import uvicorn
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os
import uuid

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title='MC API',
    version="1.0.0",
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")



@app.get('/api/v1/version_list')
def server_version_get(server_type: str):
    original = OriginalParcer()
    if server_type == original.name:
        return OriginalParcer().get_versions()
    return {'status': False, 'msg': 'server type syntx'}

@app.get('/api/v1/server_create')
def server_create(server_type: str, version: str, server_name: str):
    original = OriginalParcer()
    if server_type == original.name:
        uid = str(uuid.uuid4())
        server_dir = BASE_DIR / f'server/{uid.replace('-', '_')}'
        os.makedirs(server_dir)
        val = ParcerItem(server_dir,uid,server_name,server_type, version)
        original.download(version, server_dir)
        
        original.initServer(val)
        return {'status': True, 'uid': uid}
        

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5858)
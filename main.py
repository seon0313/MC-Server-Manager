from src.ServerParcer.Parcer import ParcerItem
from src.ServerParcer import OriginalParcer
from src.ProcessManager.router import make_router
import uuid
from fastapi import FastAPI
from pathlib import Path
import uvicorn
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os
import json

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title='MC API',
    version="1.0.0",
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.include_router(make_router(BASE_DIR), prefix='/api/v1')



@app.get('/api/v1/version_list')
def server_version_get(server_type: str):
    original = OriginalParcer()
    if server_type == original.name:
        return OriginalParcer().get_versions()
    return {'status': False, 'msg': 'server type syntx'}

@app.get('/api/v1/server_create')
def server_create(server_type: str, version: str, server_name: str, auth: str):
    original = OriginalParcer()
    if server_type == original.name:
        uid = str(uuid.uuid4())
        server_dir = BASE_DIR / f'server/{uid.replace('-', '_')}'
        os.makedirs(server_dir)
        val = ParcerItem(server_dir,uid,server_name,server_type, version, auth)
        original.download(version, server_dir)
        
        original.initServer(val)
        return {'status': True, 'uid': uid}

@app.get('/api/v1/get_servers')
def get_server_list(auth: str):
    servers = os.listdir(BASE_DIR / 'server')
    r = []
    for i in servers:
        try:
            if not os.path.isfile(i):
                files = os.listdir(BASE_DIR / 'server' / i)
                for l in files:
                    if l == 'status.json':
                        a = json.loads((BASE_DIR / 'server' / i / l).read_text())
                        q,w,e,t,y = a['uuid'], a['version'], a['name'], a['server_type'], a['auth']

                        if y == auth:
                            r.append({'uuid': q, 'version': w, 'name': e, 'server_type': t, 'auth': y})

        except Exception as e: print(e)
    return {'status': True, 'data': r}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5858)
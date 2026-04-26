import uuid
from fastapi import FastAPI
from pathlib import Path
from src.ServerParcer.original import OriginalParcer
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
        original.download(version, server_dir)
        with open(server_dir / 'run.sh', 'w') as f:
            f.write(f'java -Xms2048m -Xmx2048m -jar {server_dir}/server.jar')
        with open(server_dir / 'status.json' ,'w') as f:
            f.writelines([
                '{\n',
                f'   "uuid": "{uid}",\n',
                f'  "version": "{version}",\n',
                f'  "name": "{server_name}"\n'
                '}'
            ])
        
        return {'status': True, 'uid': uid}
        

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5858)
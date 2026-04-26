import asyncio
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from . import manager


def _get_server_dir(uuid: str, base_dir: Path) -> Path | None:
    dir_name = uuid.replace('-', '_')
    server_dir = base_dir / 'server' / dir_name
    return server_dir if server_dir.exists() else None


def _verify_auth(uuid: str, auth: str, base_dir: Path) -> tuple[bool, str]:
    server_dir = _get_server_dir(uuid, base_dir)
    if not server_dir:
        return False, '서버를 찾을 수 없습니다'

    status_file = server_dir / 'status.json'
    if not status_file.exists():
        return False, 'status.json을 찾을 수 없습니다'

    status = json.loads(status_file.read_text())
    if status.get('auth') != auth:
        return False, '인증키가 올바르지 않습니다'

    return True, ''


def make_router(base_dir: Path) -> APIRouter:
    router = APIRouter()

    @router.get('/start')
    async def start_server(uuid: str, auth: str):
        ok, msg = _verify_auth(uuid, auth, base_dir)
        if not ok:
            return {'status': False, 'msg': msg}

        server_dir = _get_server_dir(uuid, base_dir)
        return await manager.start(uuid, auth, server_dir)

    @router.get('/stop')
    async def stop_server(uuid: str, auth: str):
        ok, msg = _verify_auth(uuid, auth, base_dir)
        if not ok:
            return {'status': False, 'msg': msg}

        return await manager.stop(uuid, auth)

    @router.get('/console')
    async def stream_console(uuid: str, auth: str):
        ok, msg = _verify_auth(uuid, auth, base_dir)
        if not ok:
            return {'status': False, 'msg': msg}

        proc, err = manager.get_process(uuid, auth)
        if not proc:
            return {'status': False, 'msg': err}

        q = proc.subscribe()

        async def event_stream():
            try:
                for line in list(proc.output_buffer):
                    yield f"data: {json.dumps({'line': line})}\n\n"

                while True:
                    try:
                        line = await asyncio.wait_for(q.get(), timeout=30)
                        if line is None:
                            yield f"data: {json.dumps({'line': '[서버가 종료되었습니다]', 'done': True})}\n\n"
                            break
                        yield f"data: {json.dumps({'line': line})}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
            finally:
                proc.unsubscribe(q)

        return StreamingResponse(event_stream(), media_type='text/event-stream')

    @router.post('/console/command')
    async def console_command(uuid: str, auth: str, command: str):
        ok, msg = _verify_auth(uuid, auth, base_dir)
        if not ok:
            return {'status': False, 'msg': msg}

        return await manager.send_command(uuid, auth, command)

    return router

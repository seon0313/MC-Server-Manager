import asyncio
from collections import deque
from pathlib import Path


class ServerProcess:
    def __init__(self, uuid: str, auth: str, process: asyncio.subprocess.Process):
        self.uuid = uuid
        self.auth = auth
        self.process = process
        self.output_buffer: deque[str] = deque(maxlen=1000)
        self._subscribers: list[asyncio.Queue] = []

    async def _read_output(self):
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            decoded = line.decode('utf-8', errors='replace').rstrip('\n')
            self.output_buffer.append(decoded)
            for q in list(self._subscribers):
                await q.put(decoded)
        for q in list(self._subscribers):
            await q.put(None)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)


class ProcessManager:
    def __init__(self):
        self._processes: dict[str, ServerProcess] = {}
        self._auth_to_uuid: dict[str, str] = {}

    async def start(self, uuid: str, auth: str, server_dir: Path) -> dict:
        if auth in self._auth_to_uuid:
            running = self._auth_to_uuid[auth]
            return {'status': False, 'msg': f'이미 실행 중인 서버가 있습니다 (uuid: {running})'}
        if uuid in self._processes:
            return {'status': False, 'msg': '해당 서버가 이미 실행 중입니다'}

        run_script = server_dir / 'run.sh'
        if not run_script.exists():
            return {'status': False, 'msg': 'run.sh 파일을 찾을 수 없습니다'}

        process = await asyncio.create_subprocess_exec(
            'bash', str(run_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=server_dir,
        )

        server_proc = ServerProcess(uuid, auth, process)
        self._processes[uuid] = server_proc
        self._auth_to_uuid[auth] = uuid

        asyncio.create_task(server_proc._read_output())
        asyncio.create_task(self._monitor(uuid, auth, process))

        return {'status': True, 'msg': '서버를 시작했습니다'}

    async def _monitor(self, uuid: str, auth: str, process: asyncio.subprocess.Process):
        await process.wait()
        self._processes.pop(uuid, None)
        self._auth_to_uuid.pop(auth, None)

    async def stop(self, uuid: str, auth: str) -> dict:
        proc = self._processes.get(uuid)
        if not proc:
            return {'status': False, 'msg': '서버가 실행 중이지 않습니다'}
        if proc.auth != auth:
            return {'status': False, 'msg': '인증키가 올바르지 않습니다'}

        try:
            proc.process.stdin.write(b'stop\n')
            await proc.process.stdin.drain()
        except Exception:
            proc.process.terminate()

        return {'status': True, 'msg': '서버 종료 요청을 전송했습니다'}

    async def send_command(self, uuid: str, auth: str, command: str) -> dict:
        proc = self._processes.get(uuid)
        if not proc:
            return {'status': False, 'msg': '서버가 실행 중이지 않습니다'}
        if proc.auth != auth:
            return {'status': False, 'msg': '인증키가 올바르지 않습니다'}

        try:
            proc.process.stdin.write((command + '\n').encode())
            await proc.process.stdin.drain()
        except Exception as e:
            return {'status': False, 'msg': str(e)}

        return {'status': True, 'msg': '명령을 전송했습니다'}

    def get_process(self, uuid: str, auth: str) -> tuple['ServerProcess | None', str]:
        proc = self._processes.get(uuid)
        if not proc:
            return None, '서버가 실행 중이지 않습니다'
        if proc.auth != auth:
            return None, '인증키가 올바르지 않습니다'
        return proc, ''

    def is_running(self, uuid: str) -> bool:
        return uuid in self._processes

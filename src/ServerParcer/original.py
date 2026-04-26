import json
import requests
from .Parcer import Parcer, ParcerItem

DOMAIN_MAP = {
    'S': 'mcseoul.seon06.dev',
    'B': 'mcbusan.seon06.dev',
}

class OriginalParcer(Parcer):
    def __init__(self):
        super().__init__()
        self.url = 'https://launchermeta.mojang.com/mc/game/version_manifest_v2.json'
        self.download_url = ''
        self.name = 'Vanilla'
    
    def get_versions(self) -> dict:
        r = self.get_json()
        latest = r['latest']['release']
        releases = []
        for i in r['versions']:
            if i['type'] == 'release':
                releases.append(i['id'])
        return {'status': True,'latest': latest, 'releases': releases}
    
    def createStatus(self, val: ParcerItem):
        domain = DOMAIN_MAP.get(val.auth[0].upper(), '')
        status = {
            'uuid': val.uid,
            'version': val.version,
            'name': val.name,
            'server_type': val.type_,
            'auth': val.auth,
            'domain': domain,
        }
        (val.server_dir / 'status.json').write_text(json.dumps(status, indent=2))
    def createScript(self, val: ParcerItem):
        port = 25565 if val.auth.startswith('S') else 25566
        rcon_port = port + 10
        with open(val.server_dir / 'eula.txt', 'w') as f:
            f.write('eula=true\n')
        with open(val.server_dir / 'server.properties', 'w') as f:
            f.write(
                f'server-port={port}\n'
                f'query.port={port}\n'
                f'rcon.port={rcon_port}\n'
            )
        with open(val.server_dir / 'run.sh', 'w') as f:
            f.write('#!/bin/bash\njava -Xms2048m -Xmx2048m -jar server.jar nogui\n')

    def download(self, version, path):
        print(f'[downloader] {version} start')
        r = self.get_json()
        target: str = ''
        for i in r['versions']:
            if i['id'] == version:
                target = i['url']

        if target == '' or target == None:
            return {'status': False}
        
        print(f'[downloader] {version} find')
        
        downloads_data = self.get_json(target)['downloads']['server']
        sha1 = downloads_data['sha1']
        download_link = downloads_data['url']
        size = downloads_data['size']

        print(f'[downloader] {version} download start')

        with requests.get(download_link, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(path / 'server.jar', 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
        print(f'[downloader] {version} end')


if __name__ == '__main__':
    a = OriginalParcer()
    a.get_versions()

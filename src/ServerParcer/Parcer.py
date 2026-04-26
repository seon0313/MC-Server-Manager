from dataclasses import dataclass
from enum import Enum
import requests

class ParcerItem:
    def __init__(self, server_dir, uid, name, type_, version):
        self.server_dir = server_dir
        self.uid = uid
        self.name = name
        self.type_ = type_
        self.version = version

class Parcer:
    def __init__(self):
        self.url = ''
        self.name = ''
        self.download_url = ''
    
    def get_json(self, url='') -> dict:
        if url == '': url = self.url
        r = requests.get(url)
        return r.json()

    def get_versions(self) -> dict:
        pass
    
    def createStatus(self, val: ParcerItem):
        pass
    
    def createScript(self, val: ParcerItem):
        pass

    def initServer(self, val: ParcerItem) -> bool:
        self.createStatus(val)
        self.createScript(val)

    def download(self, version: str, path):
        pass
import requests

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

    def download(self, version: str, path):
        pass
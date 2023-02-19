import os
import sys
import json
import datetime
import subprocess

TRANSIFEX_API_TOKEN = os.environ.get('TRANSIFEX_API_TOKEN')


def download(download_url):
    p = subprocess.Popen([
        'curl', '-sL', download_url,
        '-w', '%{stderr}%{json}',
        "-H", f"Authorization: Bearer {TRANSIFEX_API_TOKEN}",
        "-H", "Content-Type: application/vnd.api+json"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    res = json.loads(stderr)
    data = stdout
    if res.get('num_redirects') == 1:
        return data
    else:
        assert res.get('http_code') == 200, f'invalid http status code\n{res}\n{data}'
        status = json.loads(data)['data']['attributes']['status']
        assert status != 'failed', f'download failed\n{res}\n{data}'
        return None


def get_download_url(lang):
    return json.loads(subprocess.check_output([
        "curl", "-sXPOST", "https://rest.api.transifex.com/resource_translations_async_downloads",
        "-H", f"Authorization: Bearer {TRANSIFEX_API_TOKEN}",
        "-d", json.dumps({"data": {
            "relationships": {
                "language": {"data": {"id": f"l:{lang}", "type": "languages"}},
                "resource": {"data": {"id": "o:the-public-knowledge-workshop:p:datacity-ckan:r:ckanpot", "type": "resources"}}
            },
            "type": "resource_translations_async_downloads"
        }}),
        "-H", "Content-Type: application/vnd.api+json"
    ]))['data']['links']['self']


def main(cmd, *args):
    if cmd == 'get_download_url':
        print(get_download_url(args[0]))
    elif cmd == 'download':
        print(download(args[0]))
    else:
        download_url = get_download_url(cmd)
        print(f'waiting for download... ({download_url})')
        start_time = datetime.datetime.now()
        data = None
        while data is None:
            data = download(download_url)
            if data is None and (datetime.datetime.now() - start_time).total_seconds() > 60*15:
                raise Exception('waited too long for download')
        print(f'saving data to {args[0]}')
        with open(args[0], 'wb') as f:
            f.write(data)
        print('OK')


if __name__ == '__main__':
    main(*sys.argv[1:])

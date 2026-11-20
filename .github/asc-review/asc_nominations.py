"""App Store featuring nominations. MODE=read: print the API schema for nominations and list existing ones.
MODE=draft: create/update DRAFT nominations from nominations.json (never submits).
MODE=submit: submit the drafts listed in SUBMIT_NAMES (only on Joseph's own "send them")."""
import json, os, time, urllib.request, urllib.error, zipfile, io
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
MODE = os.environ.get('MODE', 'read')
def call(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1500]); return {'data': []}
if MODE == 'read':
    try:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen('https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip').read()))
        spec = json.loads(z.read([n for n in z.namelist() if n.endswith('.json')][0]))
        for k, v in spec['components']['schemas'].items():
            if k.startswith('Nomination'):
                print('SCHEMA', k, json.dumps(v)[:4000])
        for p, ops in spec['paths'].items():
            if 'nomination' in p: print('PATH', p, list(ops.keys()))
    except Exception as e:
        print('spec download failed', e)
    for bundle in ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard', 'com.halfgridgames.nestrows']:
        d = call('GET', f'/v1/apps?filter[bundleId]={bundle}')['data']
        print('APP', bundle, d and d[0]['id'], d and d[0]['attributes'].get('name'))
    print('EXISTING NOMINATIONS')
    for n in call('GET', '/v1/nominations?filter[type]=APP_LAUNCH,APP_ENHANCEMENTS,NEW_CONTENT&filter[state]=DRAFT,SUBMITTED,ARCHIVED&limit=50').get('data', []):
        print(' ', n['id'], json.dumps(n['attributes']))

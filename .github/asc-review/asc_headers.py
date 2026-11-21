"""Upload the chosen header pictures into each app's App Store Asset Library (category CREATIVE_ASSETS).
Upload only: never submits for review, never places them. Skips a file already in the library (same referenceName)."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
HERE = os.path.dirname(__file__)
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1500]); return None
APPS = [('com.studsup.game', 'studs-up-header.png'), ('com.halfgridgames.marblemayhem', 'marble-mayhem-header.png'), ('com.halfgridgames.knotwizard', 'knot-wizard-header.png')]
rd = api('GET', '/v1/appAssetLibraryRefData')
pass
for bundle, fn in APPS:
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    print(f'\n=== {bundle} {fn}')
    lib = api('GET', f'/v1/apps/{app}/assetLibrary')
    if not lib or not lib.get('data'): print('  no asset library'); continue
    lid = lib['data']['id']; print('  library', lid, lib['data'].get('type'))
    have = api('GET', f'/v1/appAssetLibraries/{lid}/images?limit=200') or {}
    for im in have.get('data', []): print('  EXISTING', im['id'], json.dumps(im['attributes'])[:300])
    if any((im['attributes'].get('referenceName') == fn[:-4] + '-v2' and im['attributes'].get('state') != 'FAILED' and im['attributes'].get('fileName') == fn) for im in have.get('data', [])):
        print('  already uploaded, skipping'); continue
    path = os.path.join(HERE, 'headers', fn); size = os.path.getsize(path); data = open(path, 'rb').read()
    r = api('POST', '/v1/appAssetLibraryImages', {'data': {'type': 'appAssetLibraryImages',
        'attributes': {'category': 'CREATIVE_ASSETS', 'fileName': fn, 'fileSize': size, 'referenceName': fn[:-4] + '-v2'},
        'relationships': {'assetLibrary': {'data': {'type': 'appAssetLibraries', 'id': lid}}}}})
    if not r: continue
    iid = r['data']['id']; ops = r['data']['attributes'].get('uploadOperations') or []
    print('  created', iid, 'ops', len(ops))
    for op in ops:
        chunk = data[op['offset']:op['offset'] + op['length']]
        req = urllib.request.Request(op['url'], method=op['method'], data=chunk, headers={h['name']: h['value'] for h in op.get('requestHeaders', [])})
        with urllib.request.urlopen(req) as resp: print('   put', op['offset'], resp.status)
    r = api('PATCH', f'/v1/appAssetLibraryImages/{iid}', {'data': {'type': 'appAssetLibraryImages', 'id': iid, 'attributes': {'uploaded': True}}})
    for i in range(18):
        st = api('GET', f'/v1/appAssetLibraryImages/{iid}')
        s = st and json.dumps(st['data']['attributes'])[:400]; print('  state', s)
        if st and st['data']['attributes'].get('state') not in ('AWAITING_UPLOAD', 'UPLOAD_COMPLETE', None): break
        time.sleep(10)

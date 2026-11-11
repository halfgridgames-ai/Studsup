"""Upload each app's review video (videos/<bundle>.mp4|.mov) as an App Review attachment on its rejected
version. Never submits anything for review."""
import hashlib, json, os, sys, time, urllib.request, urllib.error
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
VID = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
BUNDLES = ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard']

def token():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'},
                      P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})

def api(method, path, body=None):
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f'  ! {method} {path} -> {e.code}: {e.read().decode()[:600]}'); return None

problems = 0
for bundle in BUNDLES:
    files = [f for f in os.listdir(VID) if f.startswith(bundle + '.')] if os.path.isdir(VID) else []
    if not files:
        print(f'{bundle}: no video, skipped'); continue
    path = os.path.join(VID, files[0]); data = open(path, 'rb').read()
    print(f'\n=== {bundle}: {files[0]} ({len(data)//1024} KB)')
    app_id = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    vers = api('GET', f'/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
    ver = next(v for v in vers if v['attributes'].get('appStoreState') not in ('READY_FOR_SALE', 'REPLACED_WITH_NEW_VERSION', 'REMOVED_FROM_SALE'))
    rd = api('GET', f"/v1/appStoreVersions/{ver['id']}/appStoreReviewDetail")['data']
    old = (api('GET', f"/v1/appStoreReviewDetails/{rd['id']}/appStoreReviewAttachments") or {}).get('data', [])
    for a in old:
        if a['attributes'].get('fileName') == files[0]:
            api('DELETE', f"/v1/appStoreReviewAttachments/{a['id']}"); print('  replaced earlier copy')
    att = api('POST', '/v1/appStoreReviewAttachments', {'data': {'type': 'appStoreReviewAttachments',
              'attributes': {'fileName': files[0], 'fileSize': len(data)},
              'relationships': {'appStoreReviewDetail': {'data': {'type': 'appStoreReviewDetails', 'id': rd['id']}}}}})
    if not att: problems += 1; continue
    att = att['data']
    for op in att['attributes']['uploadOperations']:
        chunk = data[op['offset']:op['offset'] + op['length']]
        req = urllib.request.Request(op['url'], method=op['method'], data=chunk,
                                     headers={h['name']: h['value'] for h in op.get('requestHeaders', [])})
        urllib.request.urlopen(req).read()
    res = api('PATCH', f"/v1/appStoreReviewAttachments/{att['id']}", {'data': {'type': 'appStoreReviewAttachments', 'id': att['id'],
              'attributes': {'uploaded': True, 'sourceFileChecksum': hashlib.md5(data).hexdigest()}}})
    if res is None: problems += 1
    else: print(f"  uploaded, state {res['data']['attributes'].get('assetDeliveryState')}")
print(f'\nDone with {problems} problem(s).'); sys.exit(1 if problems else 0)

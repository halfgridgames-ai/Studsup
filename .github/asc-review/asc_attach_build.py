"""Attach the newest processed build of each version (ATTACH env: bundle=version;...). Waits up to ~10 min for processing."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            d = r.read(); return json.loads(d) if d else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:800]); return None
bad = 0
for pair in filter(None, os.environ['ATTACH'].split(';')):
    bundle, ver = pair.split('=')
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    v = api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&filter[versionString]={ver}')['data'][0]
    print(f'\n=== {bundle} {ver} state', v['attributes']['appStoreState'])
    for i in range(60):
        bs = api('GET', f'/v1/builds?filter[app]={app}&filter[preReleaseVersion.version]={ver}&sort=-uploadedDate&limit=1')['data']
        b = bs[0]; st = b['attributes']['processingState']
        print('  newest build', b['attributes']['version'], b['attributes']['uploadedDate'], st)
        if st != 'PROCESSING': break
        time.sleep(10)
    if st != 'VALID': bad += 1; continue
    if b['attributes'].get('usesNonExemptEncryption') is None:
        api('PATCH', f"/v1/builds/{b['id']}", {'data': {'type': 'builds', 'id': b['id'], 'attributes': {'usesNonExemptEncryption': False}}})
    r = api('PATCH', f"/v1/appStoreVersions/{v['id']}/relationships/build", {'data': {'type': 'builds', 'id': b['id']}})
    cur = api('GET', f"/v1/appStoreVersions/{v['id']}/build")['data']['attributes']['version']
    print('  attached build now', cur)
    if cur != b['attributes']['version']: bad += 1
if bad: raise SystemExit(f'{bad} problem(s): not submitting')

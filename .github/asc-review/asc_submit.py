"""Submit prepared App Store versions for review (only run on Joseph's explicit ask).
SUBMIT env: bundle=version;bundle=version"""
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
problems = 0
for pair in filter(None, os.environ.get('SUBMIT', '').split(';')):
    bundle, ver = pair.split('=')
    print(f'\n=== {bundle} {ver}')
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    v = api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&filter[versionString]={ver}')['data'][0]
    print('  version state', v['attributes']['appStoreState'])
    b = api('GET', f"/v1/appStoreVersions/{v['id']}/build")['data']
    print('  build', b['attributes']['version'], 'encryption', b['attributes'].get('usesNonExemptEncryption'))
    if b['attributes'].get('usesNonExemptEncryption') is None:
        r = api('PATCH', f"/v1/builds/{b['id']}", {'data': {'type': 'builds', 'id': b['id'], 'attributes': {'usesNonExemptEncryption': False}}})
        print('  set encryption none', 'ok' if r else 'FAILED')
    # reuse an open (not yet submitted) submission or make one
    subs = [s for s in api('GET', f'/v1/reviewSubmissions?filter[app]={app}&filter[platform]=IOS&limit=10')['data'] if s['attributes']['state'] == 'READY_FOR_REVIEW']
    sub = subs[0] if subs else (api('POST', '/v1/reviewSubmissions', {'data': {'type': 'reviewSubmissions', 'attributes': {'platform': 'IOS'},
                 'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}}) or {}).get('data')
    if not sub: problems += 1; continue
    items = api('GET', f"/v1/reviewSubmissions/{sub['id']}/items")['data']
    if not any((it['relationships'].get('appStoreVersion') or {}).get('data', {}) for it in items):
        r = api('POST', '/v1/reviewSubmissionItems', {'data': {'type': 'reviewSubmissionItems', 'relationships': {
                 'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': sub['id']}},
                 'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': v['id']}}}}})
        print('  added version to submission', 'ok' if r else 'FAILED')
        if not r: problems += 1; continue
    r = api('PATCH', f"/v1/reviewSubmissions/{sub['id']}", {'data': {'type': 'reviewSubmissions', 'id': sub['id'], 'attributes': {'submitted': True}}})
    print('  submitted:', r['data']['attributes']['state'] if r else 'FAILED')
    if not r: problems += 1
    time.sleep(3)
    print('  version state now', api('GET', f"/v1/appStoreVersions/{v['id']}")['data']['attributes']['appStoreState'])
print(f'\nDone with {problems} problem(s).')

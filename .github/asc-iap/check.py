"""Studs Up App Store state; with SWAP=1 points the editable App Store version at the newest 0.5.8 build.
Never submits for review."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
SWAP = os.environ.get('SWAP') == '1'
def token():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
def api(method, path, body=None):
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path, e.code, e.read().decode()[:600]); return None
app = api('GET', '/v1/apps?filter[bundleId]=com.studsup.game')['data'][0]['id']
vers = api('GET', f'/v1/apps/{app}/appStoreVersions?limit=5')['data']
for v in vers:
    b = (api('GET', f"/v1/appStoreVersions/{v['id']}/build") or {}).get('data')
    print('version', v['attributes']['versionString'], v['attributes']['appStoreState'], 'build', b and b['attributes']['version'])
subs = api('GET', f'/v1/reviewSubmissions?filter[app]={app}&limit=5') or {}
for s in subs.get('data', []): print('submission', s['id'], s['attributes'].get('state'), s['attributes'].get('submittedDate'))
builds = api('GET', f'/v1/builds?filter[app]={app}&sort=-uploadedDate&limit=6&include=preReleaseVersion')
pre = {i['id']: i['attributes']['version'] for i in builds.get('included', [])}
for b in builds['data']:
    a = b['attributes']
    print('build', pre.get(b['relationships']['preReleaseVersion']['data']['id']), a['version'], a['processingState'], a['uploadedDate'])
if SWAP:
    ver = vers[0]; st = ver['attributes']['appStoreState']
    target = next((b for b in builds['data'] if pre.get(b['relationships']['preReleaseVersion']['data']['id']) == '0.5.8' and b['attributes']['processingState'] == 'VALID'), None)
    print('SWAP: version state', st, 'target build', target and target['attributes']['version'])
    if target and st in ('PREPARE_FOR_SUBMISSION', 'REJECTED', 'DEVELOPER_REJECTED', 'METADATA_REJECTED', 'INVALID_BINARY'):
        api('PATCH', f"/v1/appStoreVersions/{ver['id']}", {'data': {'type': 'appStoreVersions', 'id': ver['id'], 'attributes': {'versionString': '0.5.8'}}})
        api('PATCH', f"/v1/appStoreVersions/{ver['id']}/relationships/build", {'data': {'type': 'builds', 'id': target['id']}})
        b = api('GET', f"/v1/appStoreVersions/{ver['id']}/build")['data']; v2 = api('GET', f"/v1/appStoreVersions/{ver['id']}")['data']
        print('NOW version', v2['attributes']['versionString'], v2['attributes']['appStoreState'], 'build', b['attributes']['version'])
        # Same build on the public TestFlight link, so the review video can be recorded from it
        grp = next((g for g in api('GET', f'/v1/apps/{app}/betaGroups?limit=50')['data'] if not g['attributes'].get('isInternalGroup')), None)
        if grp:
            api('POST', f"/v1/betaGroups/{grp['id']}/relationships/builds", {'data': [{'type': 'builds', 'id': target['id']}]})
            api('POST', '/v1/betaAppReviewSubmissions', {'data': {'type': 'betaAppReviewSubmissions', 'relationships': {'build': {'data': {'type': 'builds', 'id': target['id']}}}}})
            st2 = (api('GET', f"/v1/builds/{target['id']}/buildBetaDetail") or {}).get('data', {}).get('attributes', {})
            print('TestFlight external state', st2.get('externalBuildState'), 'group', grp['attributes'].get('name'), grp['attributes'].get('publicLink'))
    else:
        print('SWAP skipped')

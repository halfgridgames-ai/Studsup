"""Knot Wizard: the build is beta-approved but its public link still refuses testers.
Print the full beta detail, turn on auto-notify, and make a fresh external group with a new public link."""
import json, os, sys, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
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
        print(f'  ! {method} {path.split("?")[0]} -> {e.code}: {e.read().decode()[:500]}'); return None
app_id = api('GET', '/v1/apps?filter[bundleId]=com.halfgridgames.knotwizard')['data'][0]['id']
vers = api('GET', f'/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
ver = next(v for v in vers if v['attributes'].get('appStoreState') not in ('READY_FOR_SALE', 'REPLACED_WITH_NEW_VERSION', 'REMOVED_FROM_SALE'))
build = api('GET', f"/v1/appStoreVersions/{ver['id']}/build")['data']
print('build attrs:', json.dumps({k: build['attributes'].get(k) for k in ('version', 'processingState', 'expired', 'usesNonExemptEncryption', 'expirationDate')}))
bbd = api('GET', f"/v1/builds/{build['id']}/buildBetaDetail")['data']
print('beta detail:', json.dumps(bbd['attributes']))
if not bbd['attributes'].get('autoNotifyEnabled'):
    api('PATCH', f"/v1/buildBetaDetails/{bbd['id']}", {'data': {'type': 'buildBetaDetails', 'id': bbd['id'], 'attributes': {'autoNotifyEnabled': True}}})
    print('auto-notify turned on')
for g in api('GET', f'/v1/apps/{app_id}/betaGroups?limit=50')['data']:
    print('group:', g['attributes'].get('name'), json.dumps({k: g['attributes'].get(k) for k in ('isInternalGroup', 'publicLinkEnabled', 'publicLinkLimit', 'publicLink')}))
grp = (api('POST', '/v1/betaGroups', {'data': {'type': 'betaGroups', 'attributes': {'name': 'iPad link', 'publicLinkEnabled': True,
       'publicLinkLimitEnabled': True, 'publicLinkLimit': 10}, 'relationships': {'app': {'data': {'type': 'apps', 'id': app_id}},
       'builds': {'data': [{'type': 'builds', 'id': build['id']}]}}}}) or {}).get('data')
if grp:
    api('POST', f"/v1/betaGroups/{grp['id']}/relationships/builds", {'data': [{'type': 'builds', 'id': build['id']}]})
    time.sleep(5)
    print('NEW PUBLIC LINK:', grp['attributes'].get('publicLink'))
print('beta detail after:', json.dumps(api('GET', f"/v1/builds/{build['id']}/buildBetaDetail")['data']['attributes']))

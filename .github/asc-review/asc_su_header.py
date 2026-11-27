"""Studs Up header picture (Joseph OK'd 21 Nov): SU 0.5.8 is now live, so send image 29800019... to Apple's asset review.
Touches only the asset submission, never app versions, builds or promo text."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
IMG = '29800019-70ac-866f-8017-35d25148e5af'
OLD_SUB = '3c5531c1-9a99-45f3-9b9a-50d3dd027abb'
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1200]); return None
app = api('GET', '/v1/apps?filter[bundleId]=com.studsup.game')['data'][0]['id']
for v in api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=5')['data']:
    print('version', v['attributes']['versionString'], v['attributes']['appStoreState'])
im = api('GET', f'/v1/appAssetLibraryImages/{IMG}')
st = im and im['data']['attributes'].get('state'); print('image', IMG, st)
s = api('GET', f'/v1/reviewSubmissions/{OLD_SUB}')
print('old asset submission', s and s['data']['attributes'].get('state'))
if st in ('PREPARE_FOR_SUBMISSION', 'READY_FOR_REVIEW') and s and s['data']['attributes'].get('state') == 'READY_FOR_REVIEW':
    r = api('PATCH', f'/v1/reviewSubmissions/{OLD_SUB}', {'data': {'type': 'reviewSubmissions', 'id': OLD_SUB, 'attributes': {'submitted': True}}})
    print('submitted:', r and r['data']['attributes'].get('state'))
    time.sleep(3)
    print('image now', api('GET', f'/v1/appAssetLibraryImages/{IMG}')['data']['attributes'].get('state'))

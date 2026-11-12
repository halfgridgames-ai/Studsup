"""Read-only: TestFlight beta state of the newest Studs Up 0.5.7 build and the App Store version state."""
import json, os, time, urllib.request
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(path):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    with urllib.request.urlopen(urllib.request.Request('https://api.appstoreconnect.apple.com' + path, headers={'Authorization': 'Bearer ' + t})) as r:
        return json.loads(r.read())
su = api('/v1/apps?filter[bundleId]=com.studsup.game')['data'][0]['id']
b = api(f'/v1/builds?filter[app]={su}&filter[preReleaseVersion.version]=0.5.7&sort=-uploadedDate&limit=1')['data'][0]
d = api(f"/v1/builds/{b['id']}/buildBetaDetail")['data']['attributes']
print('SU_BUILD', b['attributes']['version'], 'EXTERNAL', d.get('externalBuildState'))
for v in api(f'/v1/apps/{su}/appStoreVersions?filter[platform]=IOS&limit=3')['data']:
    print('SU_VERSION', v['attributes']['versionString'], v['attributes']['appStoreState'])

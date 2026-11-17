"""Read-only: App Store search metadata (name, subtitle, keywords, promo text, description, categories) for all apps."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(path):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    try:
        with urllib.request.urlopen(urllib.request.Request('https://api.appstoreconnect.apple.com' + path, headers={'Authorization': 'Bearer ' + t})) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print('  ! GET', path.split('?')[0], e.code, e.read().decode()[:300]); return {'data': []}
for bundle in ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard', 'com.halfgridgames.nestrows']:
    apps = api(f'/v1/apps?filter[bundleId]={bundle}')['data']
    if not apps: print('\n=== NO APP', bundle); continue
    app = apps[0]; print(f"\n=== {bundle} id {app['id']} name {app['attributes'].get('name')} primaryLocale {app['attributes'].get('primaryLocale')}")
    for ai in api(f"/v1/apps/{app['id']}/appInfos?include=primaryCategory,secondaryCategory,primarySubcategoryOne")['data']:
        r = ai['relationships']
        print('APPINFO', ai['id'], ai['attributes'].get('appStoreState') or ai['attributes'].get('state'), 'cat', (r.get('primaryCategory') or {}).get('data'), (r.get('primarySubcategoryOne') or {}).get('data'), (r.get('secondaryCategory') or {}).get('data'))
        for l in api(f"/v1/appInfos/{ai['id']}/appInfoLocalizations")['data']:
            print('  INFO-LOC', json.dumps(l['attributes']))
    for v in api(f"/v1/apps/{app['id']}/appStoreVersions?filter[platform]=IOS&limit=4")['data']:
        print('VERSION', v['attributes']['versionString'], v['attributes']['appStoreState'])
        for l in api(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
            print('  VER-LOC', json.dumps(l['attributes']))

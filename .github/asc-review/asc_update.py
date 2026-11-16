"""Prepare an App Store update (never submits): for each UPDATES entry, create the iOS version if it
doesn't exist, set marketing URL + What's New, and attach the newest VALID build with that version.
UPDATES env: bundle=version;bundle=version"""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
MARKETING = 'https://halfgridgames-ai.github.io'
NOTES = {
 'com.halfgridgames.marblemayhem': 'New shop with more marbles and better offers, smoother races, family-friendly ads, and a Rate us button.',
 'com.halfgridgames.knotwizard': 'Family-friendly ads, small fixes, and a Rate us button.',
 'com.studsup.game': 'New collector team cards, more natural tackles and falls, family-friendly ads, and a Rate us button.',
}
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            d = r.read(); return json.loads(d) if d else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:500]); return None
problems = 0
for pair in filter(None, os.environ.get('UPDATES', '').split(';')):
    bundle, ver = pair.split('=')
    print(f'\n=== {bundle} {ver}')
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    vs = api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&filter[versionString]={ver}')['data']
    if vs: v = vs[0]; print('  version exists', v['attributes']['appStoreState'])
    else:
        r = api('POST', '/v1/appStoreVersions', {'data': {'type': 'appStoreVersions', 'attributes': {'platform': 'IOS', 'versionString': ver, 'releaseType': 'AFTER_APPROVAL'},
                 'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}})
        if not r: problems += 1; continue
        v = r['data']; print('  created version', v['id'])
    for l in api('GET', f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
        r = api('PATCH', f"/v1/appStoreVersionLocalizations/{l['id']}", {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id'],
                 'attributes': {'marketingUrl': MARKETING, 'whatsNew': NOTES[bundle]}}})
        print('  loc', l['attributes']['locale'], 'ok' if r else 'FAILED'); problems += 0 if r else 1
    builds = api('GET', f'/v1/builds?filter[app]={app}&filter[preReleaseVersion.version]={ver}&filter[processingState]=VALID&sort=-uploadedDate&limit=1')['data']
    if not builds: print('  no VALID build for', ver, 'yet'); problems += 1; continue
    b = builds[0]
    r = api('PATCH', f"/v1/appStoreVersions/{v['id']}/relationships/build", {'data': {'type': 'builds', 'id': b['id']}})
    print('  attached build', b['attributes']['version'], 'uploaded', b['attributes']['uploadedDate'][:16], 'ok' if r is not None else 'FAILED')
    if r is None: problems += 1
    # export compliance: no non-exempt encryption
    if b['attributes'].get('usesNonExemptEncryption') is None:
        api('PATCH', f"/v1/builds/{b['id']}", {'data': {'type': 'builds', 'id': b['id'], 'attributes': {'usesNonExemptEncryption': False}}})
print(f'\nDone with {problems} problem(s). Nothing was submitted for review.')

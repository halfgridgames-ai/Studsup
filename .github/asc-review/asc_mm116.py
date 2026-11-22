"""Marble Mayhem 1.0.16 on the App Store. Boss asked on 22 Nov 2026 to put it up for review.
STEP=prepare: reuse the open (not yet submitted) iOS version or create 1.0.16, set What's New + marketing URL,
              attach the newest VALID 1.0.16 build. Never submits.
STEP=submit:  the above, then submit that version for review."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
BUNDLE, VER, STEP = 'com.halfgridgames.marblemayhem', '1.0.16', os.environ.get('STEP', 'prepare')
NOTES = ('New Grand Prix career: unlock cups one podium at a time, win 13 hand-drawn trophies and earn 13 new marbles, '
         'including Champ the lion. Every world has a new look with painted skies and scenery, the menus fit on one screen, '
         'and races run smoother.')
EDITABLE = {'PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED', 'INVALID_BINARY'}
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
app = api('GET', f'/v1/apps?filter[bundleId]={BUNDLE}')['data'][0]['id']
allv = api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=8')['data']
for x in allv: print('  version', x['attributes']['versionString'], x['attributes']['appStoreState'])
v = next((x for x in allv if x['attributes']['versionString'] == VER), None)
if not v:
    v = next((x for x in allv if x['attributes']['appStoreState'] in EDITABLE), None)
    if v:
        r = api('PATCH', f"/v1/appStoreVersions/{v['id']}", {'data': {'type': 'appStoreVersions', 'id': v['id'], 'attributes': {'versionString': VER}}})
        print('  renamed open version', v['attributes']['versionString'], '->', VER, 'ok' if r else 'FAILED')
        if not r: raise SystemExit(1)
    else:
        r = api('POST', '/v1/appStoreVersions', {'data': {'type': 'appStoreVersions', 'attributes': {'platform': 'IOS', 'versionString': VER, 'releaseType': 'AFTER_APPROVAL'},
                 'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}})
        if not r: raise SystemExit(1)
        v = r['data']; print('  created version', VER)
for l in api('GET', f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
    r = api('PATCH', f"/v1/appStoreVersionLocalizations/{l['id']}", {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id'],
             'attributes': {'marketingUrl': 'https://halfgridgames-ai.github.io', 'whatsNew': NOTES}}})
    print('  notes', l['attributes']['locale'], 'ok' if r else 'FAILED')
builds = api('GET', f'/v1/builds?filter[app]={app}&filter[preReleaseVersion.version]={VER}&sort=-uploadedDate&limit=3')['data']
for b in builds: print('  build', b['attributes']['version'], b['attributes']['processingState'], b['attributes']['uploadedDate'][:16])
valid = [b for b in builds if b['attributes']['processingState'] == 'VALID']
if not valid: print('  no VALID 1.0.16 build yet'); raise SystemExit(1)
b = valid[0]
if b['attributes'].get('usesNonExemptEncryption') is None:
    api('PATCH', f"/v1/builds/{b['id']}", {'data': {'type': 'builds', 'id': b['id'], 'attributes': {'usesNonExemptEncryption': False}}})
r = api('PATCH', f"/v1/appStoreVersions/{v['id']}/relationships/build", {'data': {'type': 'builds', 'id': b['id']}})
print('  attached build', b['attributes']['version'], 'ok' if r is not None else 'FAILED')
if r is None: raise SystemExit(1)
if STEP != 'submit': print('Prepared. Not submitted.'); raise SystemExit(0)
subs = [s for s in api('GET', f'/v1/reviewSubmissions?filter[app]={app}&filter[platform]=IOS&limit=10')['data'] if s['attributes']['state'] == 'READY_FOR_REVIEW']
sub = subs[0] if subs else (api('POST', '/v1/reviewSubmissions', {'data': {'type': 'reviewSubmissions', 'attributes': {'platform': 'IOS'},
             'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}}) or {}).get('data')
if not sub: raise SystemExit(1)
items = api('GET', f"/v1/reviewSubmissions/{sub['id']}/items")['data']
if not any((it['relationships'].get('appStoreVersion') or {}).get('data') for it in items):
    r = api('POST', '/v1/reviewSubmissionItems', {'data': {'type': 'reviewSubmissionItems', 'relationships': {
             'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': sub['id']}},
             'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': v['id']}}}}})
    print('  added version to submission', 'ok' if r else 'FAILED')
    if not r: raise SystemExit(1)
r = api('PATCH', f"/v1/reviewSubmissions/{sub['id']}", {'data': {'type': 'reviewSubmissions', 'id': sub['id'], 'attributes': {'submitted': True}}})
print('  submitted:', r['data']['attributes']['state'] if r else 'FAILED')
time.sleep(4)
print('  version state now', api('GET', f"/v1/appStoreVersions/{v['id']}")['data']['attributes']['appStoreState'])

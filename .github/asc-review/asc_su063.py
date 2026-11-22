"""Studs Up 0.6.3 on the App Store. Joseph asked on 22 Nov 2026 ("Send the apple ones") to send it for review.
STEP=status:  read-only report (versions, screenshot sets, open review submissions).
STEP=submit:  reuse the open (not yet submitted) iOS version or create 0.6.3, set What's New + marketing URL,
              attach build 105 (or newest VALID 0.6.3 build), then submit that version for review."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
BUNDLE, VER, BUILD, STEP = 'com.studsup.game', '0.6.3', '105', os.environ.get('STEP', 'status')
NOTES = ('Every career win now unlocks something: beat your first opponent and the Polar Bears are yours. Lift a trophy when you '
         'conquer a region, nine new teams, new goal and team sounds, and fresh menu music. Turn on reminders and we will tell you '
         'when your daily bonus is ready, so your streak keeps growing.')
EDITABLE = {'PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED', 'INVALID_BINARY'}
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            d = r.read(); return json.loads(d) if d else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1500]); return None
app = api('GET', f'/v1/apps?filter[bundleId]={BUNDLE}')['data'][0]['id']
allv = api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=8')['data']
for x in allv:
    print('  version', x['attributes']['versionString'], x['attributes']['appStoreState'])
    if x['attributes']['appStoreState'] in EDITABLE:
        b = (api('GET', f"/v1/appStoreVersions/{x['id']}/build") or {}).get('data')
        print('    build', b and b['attributes']['version'])
        for l in api('GET', f"/v1/appStoreVersions/{x['id']}/appStoreVersionLocalizations")['data']:
            for s in api('GET', f"/v1/appStoreVersionLocalizations/{l['id']}/appScreenshotSets")['data']:
                n = len(api('GET', f"/v1/appScreenshotSets/{s['id']}/appScreenshots")['data'])
                print('    shots', l['attributes']['locale'], s['attributes']['screenshotDisplayType'], n)
for s in api('GET', f'/v1/reviewSubmissions?filter[app]={app}&filter[platform]=IOS&limit=10')['data']:
    items = api('GET', f"/v1/reviewSubmissions/{s['id']}/items")['data']
    kinds = [k for it in items for k, v in it['relationships'].items() if isinstance(v, dict) and v.get('data')]
    print('  submission', s['id'][:8], s['attributes']['state'], s['attributes'].get('submittedDate'), kinds)
for b in api('GET', f'/v1/builds?filter[app]={app}&filter[preReleaseVersion.version]={VER}&sort=-uploadedDate&limit=4')['data']:
    print('  build', b['attributes']['version'], b['attributes']['processingState'], b['attributes']['uploadedDate'][:16])
if STEP == 'status': raise SystemExit(0)
busy = [x for x in allv if x['attributes']['appStoreState'] in ('WAITING_FOR_REVIEW', 'IN_REVIEW', 'PENDING_DEVELOPER_RELEASE')]
if busy: print('  another version is in review:', busy[0]['attributes']['versionString'], '- not submitting'); raise SystemExit(1)
v = next((x for x in allv if x['attributes']['versionString'] == VER), None) or next((x for x in allv if x['attributes']['appStoreState'] in EDITABLE), None)
if v and v['attributes']['versionString'] != VER:
    r = api('PATCH', f"/v1/appStoreVersions/{v['id']}", {'data': {'type': 'appStoreVersions', 'id': v['id'], 'attributes': {'versionString': VER}}})
    print('  renamed open version', v['attributes']['versionString'], '->', VER, 'ok' if r else 'FAILED')
    if not r: raise SystemExit(1)
if not v:
    r = api('POST', '/v1/appStoreVersions', {'data': {'type': 'appStoreVersions', 'attributes': {'platform': 'IOS', 'versionString': VER, 'releaseType': 'AFTER_APPROVAL'},
             'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}})
    if not r: raise SystemExit(1)
    v = r['data']; print('  created version', VER)
for l in api('GET', f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
    r = api('PATCH', f"/v1/appStoreVersionLocalizations/{l['id']}", {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id'],
             'attributes': {'marketingUrl': 'https://halfgridgames-ai.github.io', 'whatsNew': NOTES}}})
    print('  notes', l['attributes']['locale'], 'ok' if r else 'FAILED')
builds = [b for b in api('GET', f'/v1/builds?filter[app]={app}&filter[preReleaseVersion.version]={VER}&sort=-uploadedDate&limit=4')['data'] if b['attributes']['processingState'] == 'VALID']
b = next((x for x in builds if x['attributes']['version'] == BUILD), builds[0] if builds else None)
if not b: print('  no VALID 0.6.3 build yet'); raise SystemExit(1)
if b['attributes'].get('usesNonExemptEncryption') is None:
    api('PATCH', f"/v1/builds/{b['id']}", {'data': {'type': 'builds', 'id': b['id'], 'attributes': {'usesNonExemptEncryption': False}}})
r = api('PATCH', f"/v1/appStoreVersions/{v['id']}/relationships/build", {'data': {'type': 'builds', 'id': b['id']}})
print('  attached build', b['attributes']['version'], 'ok' if r is not None else 'FAILED')
if r is None: raise SystemExit(1)
# a fresh submission holding only this version (an older open one may hold the header picture, which can't go yet)
open_subs = [s for s in api('GET', f'/v1/reviewSubmissions?filter[app]={app}&filter[platform]=IOS&limit=10')['data'] if s['attributes']['state'] == 'READY_FOR_REVIEW']
sub = None
for s in open_subs:
    items = api('GET', f"/v1/reviewSubmissions/{s['id']}/items")['data']
    if items and all((it['relationships'].get('appStoreVersion') or {}).get('data') for it in items): sub = s
if not sub:
    sub = (api('POST', '/v1/reviewSubmissions', {'data': {'type': 'reviewSubmissions', 'attributes': {'platform': 'IOS'},
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

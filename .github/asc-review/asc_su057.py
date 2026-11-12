"""Studs Up: put the 0.5.7 build on the public TestFlight link (sent for beta review, approved by Joseph
2026-11-12) and attach it to the rejected App Store version, renaming that version to 0.5.7.
Knot Wizard: read-only report of its TestFlight groups and links (re-enables a disabled public link).
Never submits anything to App Store review; Joseph taps Update Review himself."""
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
        print(f'  ! {method} {path.split("?")[0]} -> {e.code}: {e.read().decode()[:600]}'); return None
problems = 0
def bstate(bid):
    return ((api('GET', f'/v1/builds/{bid}/buildBetaDetail') or {}).get('data') or {}).get('attributes', {})

# ---------- Knot Wizard report ----------
print('=== Knot Wizard')
kw = api('GET', '/v1/apps?filter[bundleId]=com.halfgridgames.knotwizard')['data'][0]['id']
for g in api('GET', f'/v1/apps/{kw}/betaGroups?limit=50')['data']:
    a = g['attributes']
    if a.get('isInternalGroup'): print('  internal group:', a.get('name')); continue
    if not a.get('publicLinkEnabled'):
        r = api('PATCH', f"/v1/betaGroups/{g['id']}", {'data': {'type': 'betaGroups', 'id': g['id'], 'attributes': {'publicLinkEnabled': True}}})
        if r: a = r['data']['attributes']; print('  re-enabled public link')
    blds = (api('GET', f"/v1/betaGroups/{g['id']}/builds?limit=10") or {}).get('data', [])
    testers = (api('GET', f"/v1/betaGroups/{g['id']}/betaTesters?limit=50") or {}).get('data', [])
    print(f"  group '{a.get('name')}': link={a.get('publicLink')} enabled={a.get('publicLinkEnabled')} limitOn={a.get('publicLinkLimitEnabled')} limit={a.get('publicLinkLimit')} testers={len(testers)}")
    for b in blds:
        print(f"    build {b['attributes'].get('version')} expired={b['attributes'].get('expired')} beta={json.dumps(bstate(b['id']))}")

# ---------- Studs Up 0.5.7 ----------
print('\n=== Studs Up')
su = api('GET', '/v1/apps?filter[bundleId]=com.studsup.game')['data'][0]['id']
builds = api('GET', f'/v1/builds?filter[app]={su}&filter[preReleaseVersion.version]=0.5.7&sort=-uploadedDate&limit=5')['data']
build = next((b for b in builds if b['attributes'].get('processingState') == 'VALID' and not b['attributes'].get('expired')), None)
if not build: print('  ! no processed 0.5.7 build yet'); sys.exit(1)
bid = build['id']; print(f"  0.5.7 build number {build['attributes'].get('version')}")
if build['attributes'].get('usesNonExemptEncryption') is None:
    api('PATCH', f'/v1/builds/{bid}', {'data': {'type': 'builds', 'id': bid, 'attributes': {'usesNonExemptEncryption': False}}})
bls = (api('GET', f'/v1/builds/{bid}/betaBuildLocalizations') or {}).get('data', [])
wt = {'whatsNew': 'Play a match, then open the shop: Offers tab has Remove Ads, Starter Pack and coin packs, plus Restore purchases.'}
if bls: api('PATCH', f"/v1/betaBuildLocalizations/{bls[0]['id']}", {'data': {'type': 'betaBuildLocalizations', 'id': bls[0]['id'], 'attributes': wt}})
else: api('POST', '/v1/betaBuildLocalizations', {'data': {'type': 'betaBuildLocalizations', 'attributes': dict(wt, locale='en-GB'), 'relationships': {'build': {'data': {'type': 'builds', 'id': bid}}}}})
bbd = (api('GET', f'/v1/builds/{bid}/buildBetaDetail') or {}).get('data')
if bbd and not bbd['attributes'].get('autoNotifyEnabled'):
    api('PATCH', f"/v1/buildBetaDetails/{bbd['id']}", {'data': {'type': 'buildBetaDetails', 'id': bbd['id'], 'attributes': {'autoNotifyEnabled': True}}})
for g in api('GET', f'/v1/apps/{su}/betaGroups?limit=50')['data']:
    if g['attributes'].get('isInternalGroup'): continue
    api('POST', f"/v1/betaGroups/{g['id']}/relationships/builds", {'data': [{'type': 'builds', 'id': bid}]})
    print(f"  added to group '{g['attributes'].get('name')}' link={g['attributes'].get('publicLink')} enabled={g['attributes'].get('publicLinkEnabled')}")
st = bstate(bid).get('externalBuildState'); print('  external state:', st)
if st in ('READY_FOR_BETA_SUBMISSION', 'MISSING_EXPORT_COMPLIANCE', None):
    r = api('POST', '/v1/betaAppReviewSubmissions', {'data': {'type': 'betaAppReviewSubmissions', 'relationships': {'build': {'data': {'type': 'builds', 'id': bid}}}}})
    print('  sent for TestFlight beta review' if r is not None else '  ! beta review submission failed'); problems += r is None
print('  external state now:', bstate(bid).get('externalBuildState'))
# App Store version -> 0.5.7 with this build (no submission)
vers = api('GET', f'/v1/apps/{su}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
ver = next(v for v in vers if v['attributes'].get('appStoreState') not in ('READY_FOR_SALE', 'REPLACED_WITH_NEW_VERSION', 'REMOVED_FROM_SALE'))
print(f"  App Store version {ver['attributes'].get('versionString')} state={ver['attributes'].get('appStoreState')}")
if ver['attributes'].get('versionString') != '0.5.7':
    r = api('PATCH', f"/v1/appStoreVersions/{ver['id']}", {'data': {'type': 'appStoreVersions', 'id': ver['id'], 'attributes': {'versionString': '0.5.7'}}})
    print('  renamed version to 0.5.7' if r else '  ! rename failed'); problems += not r
r = api('PATCH', f"/v1/appStoreVersions/{ver['id']}/relationships/build", {'data': {'type': 'builds', 'id': bid}})
print('  attached 0.5.7 build to the App Store version' if r is not None else '  ! attach failed'); problems += r is None
cur = (api('GET', f"/v1/appStoreVersions/{ver['id']}/build") or {}).get('data') or {}
v2 = api('GET', f"/v1/appStoreVersions/{ver['id']}")['data']['attributes']
print(f"  check: version {v2.get('versionString')} state={v2.get('appStoreState')} build={cur.get('attributes', {}).get('version')}")
print(f'\nDone with {problems} problem(s).'); sys.exit(1 if problems else 0)

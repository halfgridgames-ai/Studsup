"""Outside (external) TestFlight for the three apps: a group with a public link, the submitted build
added, beta review details copied from the App Review contact, and the build sent to TestFlight beta
review (approved by Joseph). Prints each public link. Never submits to App Store review."""
import json, os, sys, time, urllib.request, urllib.error
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
APPS = [('com.studsup.game', 'Studs Up'), ('com.halfgridgames.marblemayhem', 'Marble Mayhem'), ('com.halfgridgames.knotwizard', 'Knot Wizard')]
SEND = os.environ.get('SEND_FOR_BETA_REVIEW') == '1'

def token():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'},
                      P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})

def api(method, path, body=None):
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f'  ! {method} {path.split("?")[0]} -> {e.code}: {e.read().decode()[:500]}'); return None

problems = 0
for bundle, name in APPS:
    print(f'\n=== {name}')
    app_id = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    vers = api('GET', f'/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
    ver = next(v for v in vers if v['attributes'].get('appStoreState') not in ('READY_FOR_SALE', 'REPLACED_WITH_NEW_VERSION', 'REMOVED_FROM_SALE'))
    build = api('GET', f"/v1/appStoreVersions/{ver['id']}/build")['data']
    rd = (api('GET', f"/v1/appStoreVersions/{ver['id']}/appStoreReviewDetail") or {}).get('data') or {}
    ra = rd.get('attributes', {})
    # Beta review contact = App Review contact
    bard = (api('GET', f'/v1/apps/{app_id}/betaAppReviewDetail') or {}).get('data')
    if bard:
        api('PATCH', f"/v1/betaAppReviewDetails/{bard['id']}", {'data': {'type': 'betaAppReviewDetails', 'id': bard['id'], 'attributes': {
            'contactFirstName': ra.get('contactFirstName'), 'contactLastName': ra.get('contactLastName'),
            'contactPhone': ra.get('contactPhone'), 'contactEmail': ra.get('contactEmail') or 'halfgridgames@gmail.com',
            'demoAccountRequired': False, 'notes': 'No login needed. Open the app and tap Play.'}}})
    # Beta app description + feedback email (English)
    locs = (api('GET', f'/v1/apps/{app_id}/betaAppLocalizations') or {}).get('data', [])
    attrs = {'feedbackEmail': 'halfgridgames@gmail.com', 'description': f'{name} by Half Grid Games. Test build for recording an App Review demo.'}
    if locs:
        api('PATCH', f"/v1/betaAppLocalizations/{locs[0]['id']}", {'data': {'type': 'betaAppLocalizations', 'id': locs[0]['id'], 'attributes': attrs}})
    else:
        api('POST', '/v1/betaAppLocalizations', {'data': {'type': 'betaAppLocalizations', 'attributes': dict(attrs, locale='en-GB'),
            'relationships': {'app': {'data': {'type': 'apps', 'id': app_id}}}}})
    # What to test on the build
    bls = (api('GET', f"/v1/builds/{build['id']}/betaBuildLocalizations") or {}).get('data', [])
    wt = {'whatsNew': 'Play the game, open the shop and try a purchase.'}
    if bls:
        api('PATCH', f"/v1/betaBuildLocalizations/{bls[0]['id']}", {'data': {'type': 'betaBuildLocalizations', 'id': bls[0]['id'], 'attributes': wt}})
    else:
        api('POST', '/v1/betaBuildLocalizations', {'data': {'type': 'betaBuildLocalizations', 'attributes': dict(wt, locale='en-GB'),
            'relationships': {'build': {'data': {'type': 'builds', 'id': build['id']}}}}})
    # External group with a public link
    groups = api('GET', f'/v1/apps/{app_id}/betaGroups?limit=50')['data']
    grp = next((g for g in groups if not g['attributes'].get('isInternalGroup')), None)
    if not grp:
        grp = (api('POST', '/v1/betaGroups', {'data': {'type': 'betaGroups', 'attributes': {'name': 'Public link',
               'publicLinkEnabled': True, 'publicLinkLimitEnabled': True, 'publicLinkLimit': 10},
               'relationships': {'app': {'data': {'type': 'apps', 'id': app_id}}}}}) or {}).get('data')
    if not grp: problems += 1; continue
    if not grp['attributes'].get('publicLinkEnabled'):
        grp = api('PATCH', f"/v1/betaGroups/{grp['id']}", {'data': {'type': 'betaGroups', 'id': grp['id'],
              'attributes': {'publicLinkEnabled': True, 'publicLinkLimitEnabled': True, 'publicLinkLimit': 10}}})['data']
    api('POST', f"/v1/betaGroups/{grp['id']}/relationships/builds", {'data': [{'type': 'builds', 'id': build['id']}]})
    state = (api('GET', f"/v1/builds/{build['id']}/buildBetaDetail") or {}).get('data', {}).get('attributes', {}).get('externalBuildState')
    print(f"  build {build['attributes'].get('version')} external state: {state}, expired={build['attributes'].get('expired')}")
    if state == 'BETA_APPROVED':
        # Approved but not handed to the public-link group: take the build out of the group and put it back
        rel = {'data': [{'type': 'builds', 'id': build['id']}]}
        api('DELETE', f"/v1/betaGroups/{grp['id']}/relationships/builds", rel)
        api('POST', f"/v1/betaGroups/{grp['id']}/relationships/builds", rel)
        state = (api('GET', f"/v1/builds/{build['id']}/buildBetaDetail") or {}).get('data', {}).get('attributes', {}).get('externalBuildState')
        print(f'  re-added build to the public group; state now {state}')
    sub = (api('GET', f"/v1/builds/{build['id']}/betaAppReviewSubmission") or {}).get('data') or {}
    print(f"  beta review submission: {sub.get('attributes', {}).get('betaReviewState')}")
    ga = grp['attributes']
    gb = [b['id'] for b in (api('GET', f"/v1/betaGroups/{grp['id']}/builds?limit=20") or {}).get('data', [])]
    print(f"  group '{ga.get('name')}': publicLinkEnabled={ga.get('publicLinkEnabled')} limit={ga.get('publicLinkLimit')} build attached={build['id'] in gb}")
    if SEND and state in ('READY_FOR_BETA_SUBMISSION', 'MISSING_EXPORT_COMPLIANCE', None):
        res = api('POST', '/v1/betaAppReviewSubmissions', {'data': {'type': 'betaAppReviewSubmissions',
              'relationships': {'build': {'data': {'type': 'builds', 'id': build['id']}}}}})
        print('  sent for TestFlight beta review' if res is not None else '  ! beta review submission failed')
        if res is None: problems += 1
    print(f"  PUBLIC LINK: {grp['attributes'].get('publicLink')}")
print(f'\nDone with {problems} problem(s).'); sys.exit(1 if problems else 0)

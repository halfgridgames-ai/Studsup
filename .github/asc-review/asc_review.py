"""Prepare the three iOS apps for resubmission through the App Store Connect API.

For each app: write the App Review notes on the rejected version, and make an internal
TestFlight group ("Me") with the account holder in it, so the submitted build installs on an iPhone.
It never submits anything for review."""
import json, os, sys, time, urllib.request, urllib.error
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
HERE = os.path.dirname(os.path.abspath(__file__))
APPS = [('com.studsup.game', 'studs-up-notes.txt'),
        ('com.halfgridgames.marblemayhem', 'marble-mayhem-notes.txt'),
        ('com.halfgridgames.knotwizard', 'knot-wizard-notes.txt')]

def token():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'},
                      P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})

def api(method, path, body=None):
    url = path if path.startswith('http') else 'https://api.appstoreconnect.apple.com' + path
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f'  ! {method} {path} -> {e.code}: {msg[:600]}')
        return None

problems = 0
users = (api('GET', '/v1/users?limit=50') or {}).get('data', [])
holder = next((u for u in users if 'ACCOUNT_HOLDER' in u['attributes'].get('roles', [])), users[0] if users else None)
if holder:
    ha = holder['attributes']
    print(f"Account holder: {ha.get('firstName')} {ha.get('lastName')} (roles {ha.get('roles')})")
else:
    print('! could not read users'); problems += 1

# REINVITE: the earlier invites were accepted on a borrowed iPhone, so Apple won't send new ones.
# Removing the tester and adding them back makes Apple send a fresh invite for each app.
if holder and os.environ.get('REINVITE') == '1':
    email = holder['attributes'].get('username')
    for t in (api('GET', f'/v1/betaTesters?filter[email]={email}') or {}).get('data', []):
        if api('DELETE', f"/v1/betaTesters/{t['id']}") is not None:
            print('Removed old TestFlight tester entry so fresh invites can be sent')

for bundle, notes_file in APPS:
    print(f'\n=== {bundle}')
    notes = open(os.path.join(HERE, notes_file), encoding='utf-8').read().strip()
    apps = (api('GET', f'/v1/apps?filter[bundleId]={bundle}') or {}).get('data', [])
    if not apps:
        print('  ! app not found'); problems += 1; continue
    app_id = apps[0]['id']
    vers = (api('GET', f'/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS&limit=5') or {}).get('data', [])
    for v in vers:
        print(f"  version {v['attributes']['versionString']}: {v['attributes'].get('appStoreState')} / {v['attributes'].get('appVersionState')}")
    ver = next((v for v in vers if v['attributes'].get('appStoreState') not in ('READY_FOR_SALE', 'REPLACED_WITH_NEW_VERSION', 'REMOVED_FROM_SALE')), None)
    if not ver:
        print('  ! no editable version'); problems += 1; continue
    build = (api('GET', f"/v1/appStoreVersions/{ver['id']}/build") or {}).get('data')
    if build:
        print(f"  attached build {build['attributes'].get('version')} processing={build['attributes'].get('processingState')}")
    # Review notes
    rd = (api('GET', f"/v1/appStoreVersions/{ver['id']}/appStoreReviewDetail") or {}).get('data')
    if rd:
        res = api('PATCH', f"/v1/appStoreReviewDetails/{rd['id']}",
                  {'data': {'type': 'appStoreReviewDetails', 'id': rd['id'], 'attributes': {'notes': notes}}})
    else:
        res = api('POST', '/v1/appStoreReviewDetails', {'data': {'type': 'appStoreReviewDetails', 'attributes': {'notes': notes},
                  'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': ver['id']}}}}})
    if res is None: problems += 1
    else: print(f'  review notes saved ({len(notes)} chars)')
    # Internal TestFlight group with the account holder
    groups = (api('GET', f'/v1/apps/{app_id}/betaGroups?limit=50') or {}).get('data', [])
    grp = next((g for g in groups if g['attributes'].get('isInternalGroup')), None)
    if not grp:
        grp = (api('POST', '/v1/betaGroups', {'data': {'type': 'betaGroups',
               'attributes': {'name': 'Me', 'isInternalGroup': True, 'hasAccessToAllBuilds': True},
               'relationships': {'app': {'data': {'type': 'apps', 'id': app_id}}}}}) or {}).get('data')
    if not grp:
        problems += 1; continue
    print(f"  internal group: {grp['attributes'].get('name')}")
    if build and not grp['attributes'].get('hasAccessToAllBuilds'):
        api('POST', f"/v1/betaGroups/{grp['id']}/relationships/builds", {'data': [{'type': 'builds', 'id': build['id']}]})
    if holder:
        email = holder['attributes'].get('username')
        existing = (api('GET', f"/v1/betaTesters?filter[email]={email}&filter[apps]={app_id}") or {}).get('data', [])
        if existing:
            tester = existing[0]
            api('POST', f"/v1/betaGroups/{grp['id']}/relationships/betaTesters", {'data': [{'type': 'betaTesters', 'id': tester['id']}]})
        else:
            tester = (api('POST', '/v1/betaTesters', {'data': {'type': 'betaTesters',
                      'attributes': {'email': email, 'firstName': holder['attributes'].get('firstName'), 'lastName': holder['attributes'].get('lastName')},
                      'relationships': {'betaGroups': {'data': [{'type': 'betaGroups', 'id': grp['id']}]}}}}) or {}).get('data')
        if tester:
            print('  account holder is in the group')
            inv = api('POST', '/v1/betaTesterInvitations', {'data': {'type': 'betaTesterInvitations', 'relationships': {
                  'app': {'data': {'type': 'apps', 'id': app_id}}, 'betaTester': {'data': {'type': 'betaTesters', 'id': tester['id']}}}}})
            print('  TestFlight invite email sent' if inv is not None else '  (invite not re-sent; may already be invited)')
        else:
            problems += 1

print(f'\nDone with {problems} problem(s).')
sys.exit(1 if problems else 0)

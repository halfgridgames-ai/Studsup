"""Make TESTER_EMAIL an internal TestFlight tester on all three apps.
Internal testers must be App Store Connect users: if the email isn't one yet, this sends an
App Store Connect user invitation (Developer role, approved by Joseph 2026-11-11); run again after it is accepted."""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
EMAIL = os.environ['TESTER_EMAIL'].strip().lower()
BUNDLES = ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard']

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

q = urllib.parse.quote(EMAIL)
users = (api('GET', '/v1/users?limit=100') or {}).get('data', [])
user = next((u for u in users if u['attributes'].get('username', '').lower() == EMAIL), None)
if not user:
    pending = (api('GET', f'/v1/userInvitations?filter[email]={q}') or {}).get('data', [])
    if pending:
        print('USER INVITE PENDING: accept the App Store Connect invitation email, then re-run.'); sys.exit(0)
    res = api('POST', '/v1/userInvitations', {'data': {'type': 'userInvitations', 'attributes': {
        'email': EMAIL, 'firstName': 'Half Grid', 'lastName': 'Games', 'roles': ['DEVELOPER'],
        'allAppsVisible': True, 'provisioningAllowed': False}}})
    print('USER INVITE SENT: accept it, then re-run.' if res is not None else 'USER INVITE FAILED')
    sys.exit(0 if res is not None else 1)

print('App Store Connect user found; adding as internal tester')
problems = 0
for bundle in BUNDLES:
    app_id = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    grp = next((g for g in api('GET', f'/v1/apps/{app_id}/betaGroups?limit=50')['data'] if g['attributes'].get('isInternalGroup')), None)
    existing = (api('GET', f'/v1/betaTesters?filter[email]={q}') or {}).get('data', [])
    if existing:
        tester = existing[0]
        api('POST', f"/v1/betaGroups/{grp['id']}/relationships/betaTesters", {'data': [{'type': 'betaTesters', 'id': tester['id']}]})
    else:
        tester = (api('POST', '/v1/betaTesters', {'data': {'type': 'betaTesters',
                  'attributes': {'email': EMAIL, 'firstName': 'Half Grid', 'lastName': 'Games'},
                  'relationships': {'betaGroups': {'data': [{'type': 'betaGroups', 'id': grp['id']}]}}}}) or {}).get('data')
    if not tester: problems += 1; continue
    inv = api('POST', '/v1/betaTesterInvitations', {'data': {'type': 'betaTesterInvitations', 'relationships': {
          'app': {'data': {'type': 'apps', 'id': app_id}}, 'betaTester': {'data': {'type': 'betaTesters', 'id': tester['id']}}}}})
    print(f'{bundle}: tester added, invite ' + ('sent' if inv is not None else 'not sent'))
print(f'Done with {problems} problem(s).'); sys.exit(1 if problems else 0)

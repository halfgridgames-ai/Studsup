"""App Store featuring nominations. MODE=read: print the API schema for nominations and list existing ones.
MODE=draft: create/update DRAFT nominations from nominations.json (never submits).
MODE=submit: submit the drafts listed in SUBMIT_NAMES (only on Joseph's own "send them")."""
import json, os, time, urllib.request, urllib.error, zipfile, io
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
MODE = os.environ.get('MODE', 'read')
def call(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1500]); return {'data': []}
if MODE == 'read' and os.environ.get('PRINT_SPEC'):
    try:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen('https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip').read()))
        spec = json.loads(z.read([n for n in z.namelist() if n.endswith('.json')][0]))
        for k, v in spec['components']['schemas'].items():
            if k.startswith('Nomination'):
                print('SCHEMA', k, json.dumps(v)[:4000])
        for p, ops in spec['paths'].items():
            if 'nomination' in p: print('PATH', p, list(ops.keys()))
    except Exception as e:
        print('spec download failed', e)
if MODE == 'read':
    for bundle in ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard', 'com.halfgridgames.nestrows']:
        d = call('GET', f'/v1/apps?filter[bundleId]={bundle}')['data']
        print('APP', bundle, d and d[0]['id'], d and d[0]['attributes'].get('name'))
    print('EXISTING NOMINATIONS')
def existing():
    out = []
    for st in ['DRAFT', 'SUBMITTED']:
        for t in ['APP_LAUNCH', 'APP_ENHANCEMENTS', 'NEW_CONTENT']:
            out += call('GET', f'/v1/nominations?filter[type]={t}&filter[state]={st}&limit=50').get('data', [])
    return out
if MODE == 'read':
    for n in existing(): print(' ', n['id'], json.dumps(n['attributes']))
if MODE == 'draft':
    noms = json.load(open(os.path.join(os.path.dirname(__file__), 'nominations.json')))
    have = {n['attributes']['name']: n for n in existing()}
    for n in noms:
        attrs = {k: n[k] for k in ['name', 'type', 'description', 'notes', 'supplementalMaterialsUris']}
        attrs.update({'publishStartDate': os.environ.get('START', '2026-12-11T09:00:00Z'), 'publishEndDate': os.environ.get('END', '2027-01-31T09:00:00Z'),
                      'deviceFamilies': ['IPHONE', 'IPAD'], 'locales': ['en-US'], 'hasInAppEvents': False, 'launchInSelectMarketsFirst': False, 'preOrderEnabled': False})
        rel = {'relatedApps': {'data': [{'type': 'apps', 'id': n['app']}]}}
        if n['name'] in have:
            old = have[n['name']]
            if old['attributes']['state'] != 'DRAFT': print('SKIP (not draft)', n['name']); continue
            r = call('PATCH', f"/v1/nominations/{old['id']}", {'data': {'type': 'nominations', 'id': old['id'], 'attributes': dict(attrs, submitted=False), 'relationships': rel}})
        else:
            attrs['submitted'] = False
            r = call('POST', '/v1/nominations', {'data': {'type': 'nominations', 'attributes': attrs, 'relationships': rel}})
        d = r.get('data') or {}
        print('DRAFT', d.get('id'), (d.get('attributes') or {}).get('state'), n['name'])
    for n in existing(): print('NOW', n['id'], n['attributes']['state'], n['attributes']['name'], n['attributes'].get('publishStartDate'))
if MODE == 'submit':
    names = [s.strip() for s in os.environ['SUBMIT_NAMES'].split('|') if s.strip()]
    for n in existing():
        if n['attributes']['name'] in names and n['attributes']['state'] == 'DRAFT':
            r = call('PATCH', f"/v1/nominations/{n['id']}", {'data': {'type': 'nominations', 'id': n['id'], 'attributes': {'submitted': True}}})
            print('SUBMITTED', n['attributes']['name'], (r.get('data') or {}).get('attributes', {}).get('state'))

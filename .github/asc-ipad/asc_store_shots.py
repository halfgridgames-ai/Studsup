"""Refresh App Store screenshots (iPhone 6.9-inch + iPad 13-inch) for the four games.

Joseph asked (17 Nov 2026) for all store screenshots to be updated to the latest versions.
Only versions Apple still lets us edit (Prepare for Submission / Rejected) are changed; versions
waiting for review, in review or live are only reported. For each editable version and locale:
  - every iPhone screenshot set is emptied and the new iPhone pictures go in the 6.9-inch slot
    (smaller iPhones then use the 6.9-inch pictures),
  - every iPad screenshot set is emptied and the new iPad pictures go in the 13-inch slot.
Text, previews (videos) and review details are never touched, and nothing is submitted.
MODE=report (default) only prints what it would do; MODE=replace does it.
"""
import hashlib, json, os, time, urllib.request, urllib.error, glob
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
REPLACE = os.environ.get('MODE', 'report') == 'replace'
HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = {'iphone': 'APP_IPHONE_67', 'ipad': 'APP_IPAD_PRO_3GEN_129'}
EDITABLE = {'PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED', 'INVALID_BINARY'}
APPS = [('com.studsup.game', 'su', 'STUDS UP'), ('com.halfgridgames.marblemayhem', 'mm', 'MARBLE MAYHEM'),
        ('com.halfgridgames.knotwizard', 'kw', 'KNOT WIZARD'), ('com.halfgridgames.nestrows', 'nr', 'NEST ROWS')]


def tok():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8,
                      algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})


def api(path, method='GET', body=None):
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + tok(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:400])
        return None


def put_parts(ops, data):
    for op in ops:
        chunk = data[op['offset']:op['offset'] + op['length']]
        req = urllib.request.Request(op['url'], method=op['method'], data=chunk,
                                     headers={h['name']: h['value'] for h in op['requestHeaders']})
        with urllib.request.urlopen(req) as r:
            r.read()


def shots_in(set_id):
    return (api(f'/v1/appScreenshotSets/{set_id}/appScreenshots?limit=50') or {}).get('data', [])


def refresh(loc_id, kind, files):
    target = TARGETS[kind]
    sets = (api(f'/v1/appStoreVersionLocalizations/{loc_id}/appScreenshotSets?limit=50') or {}).get('data', [])
    mine = [s for s in sets if s['attributes']['screenshotDisplayType'].startswith('APP_IPHONE' if kind == 'iphone' else 'APP_IPAD')]
    for s in mine:
        old = shots_in(s['id'])
        print(f"    {s['attributes']['screenshotDisplayType']}: {len(old)} now", '-> clearing' if REPLACE and old else '')
        if REPLACE:
            for o in old:
                api(f"/v1/appScreenshots/{o['id']}", 'DELETE')
    print(f'    {target}: would put {len(files)} new' if not REPLACE else f'    {target}: uploading {len(files)} new')
    if not REPLACE:
        return
    s = next((x for x in mine if x['attributes']['screenshotDisplayType'] == target), None)
    if not s:
        r = api('/v1/appScreenshotSets', 'POST', {'data': {'type': 'appScreenshotSets',
                'attributes': {'screenshotDisplayType': target},
                'relationships': {'appStoreVersionLocalization': {'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id}}}}})
        if not r:
            return
        s = r['data']
    for f in files:
        data = open(f, 'rb').read()
        r = api('/v1/appScreenshots', 'POST', {'data': {'type': 'appScreenshots',
                'attributes': {'fileName': os.path.basename(f), 'fileSize': len(data)},
                'relationships': {'appScreenshotSet': {'data': {'type': 'appScreenshotSets', 'id': s['id']}}}}})
        if not r:
            continue
        sid = r['data']['id']
        put_parts(r['data']['attributes']['uploadOperations'], data)
        api(f'/v1/appScreenshots/{sid}', 'PATCH', {'data': {'type': 'appScreenshots', 'id': sid,
            'attributes': {'uploaded': True, 'sourceFileChecksum': hashlib.md5(data).hexdigest()}}})
    time.sleep(10)
    for x in shots_in(s['id']):
        a = x['attributes']
        st = a.get('assetDeliveryState') or {}
        print('      ', a.get('fileName'), st.get('state'), st.get('errors') or '')


for bundle, key, name in APPS:
    print(f'\n=== {name}')
    apps = api(f'/v1/apps?filter[bundleId]={bundle}')
    if not apps or not apps['data']:
        print('  no app record')
        continue
    app = apps['data'][0]['id']
    files = {k: sorted(glob.glob(os.path.join(HERE, k, key + '-*.jpg'))) for k in TARGETS}
    for v in (api(f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=5') or {}).get('data', []):
        va = v['attributes']
        print('VERSION', va['versionString'], va['appStoreState'])
        if va['appStoreState'] not in EDITABLE:
            continue
        for l in (api(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations") or {}).get('data', []):
            print('  LOC', l['attributes']['locale'])
            for kind in TARGETS:
                if files[kind]:
                    refresh(l['id'], kind, files[kind])

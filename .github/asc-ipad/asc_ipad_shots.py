"""13-inch iPad screenshots for the four games.

Reports every App Store version of each app. With UPLOAD=1 it adds the screenshots in
.github/asc-ipad/shots to the 13-inch iPad slot of versions that Apple still lets us edit
(Prepare for Submission / Rejected), and only when that slot is empty. It never deletes
screenshots, never touches iPhone screenshots or text, and never submits anything for review.
Versions waiting for review, in review or live are only reported (Apple locks them).
"""
import hashlib, json, os, time, urllib.request, urllib.error, glob
import jwt

KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
UPLOAD = os.environ.get('UPLOAD', '0') == '1'
HERE = os.path.dirname(os.path.abspath(__file__))
DISPLAY = 'APP_IPAD_PRO_3GEN_129'   # the 13-inch iPad slot (2064 x 2752)
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


def upload_set(loc_id, files):
    sets = (api(f'/v1/appStoreVersionLocalizations/{loc_id}/appScreenshotSets?limit=50') or {}).get('data', [])
    s = next((x for x in sets if x['attributes']['screenshotDisplayType'] == DISPLAY), None)
    if s:
        have = (api(f"/v1/appScreenshotSets/{s['id']}/appScreenshots?limit=50") or {}).get('data', [])
        if have:
            print('    13-inch iPad slot already has', len(have), 'screenshots; left alone')
            return
    else:
        r = api('/v1/appScreenshotSets', 'POST', {'data': {'type': 'appScreenshotSets',
                'attributes': {'screenshotDisplayType': DISPLAY},
                'relationships': {'appStoreVersionLocalization': {'data': {'type': 'appStoreVersionLocalizations', 'id': loc_id}}}}})
        if not r:
            return
        s = r['data']
    for f in files:
        data = open(f, 'rb').read()
        name = os.path.basename(f)
        r = api('/v1/appScreenshots', 'POST', {'data': {'type': 'appScreenshots',
                'attributes': {'fileName': name, 'fileSize': len(data)},
                'relationships': {'appScreenshotSet': {'data': {'type': 'appScreenshotSets', 'id': s['id']}}}}})
        if not r:
            continue
        sid = r['data']['id']
        put_parts(r['data']['attributes']['uploadOperations'], data)
        api(f'/v1/appScreenshots/{sid}', 'PATCH', {'data': {'type': 'appScreenshots', 'id': sid,
            'attributes': {'uploaded': True, 'sourceFileChecksum': hashlib.md5(data).hexdigest()}}})
        print('    uploaded', name)
    time.sleep(10)
    for x in (api(f"/v1/appScreenshotSets/{s['id']}/appScreenshots?limit=50") or {}).get('data', []):
        a = x['attributes']
        st = a.get('assetDeliveryState') or {}
        print('    check', a.get('fileName'), st.get('state'), st.get('errors') or '')


for bundle, key, name in APPS:
    print(f'\n=== {name}')
    apps = api(f'/v1/apps?filter[bundleId]={bundle}')
    if not apps or not apps['data']:
        print('  no app record')
        continue
    app = apps['data'][0]['id']
    files = sorted(glob.glob(os.path.join(HERE, 'shots', key + '-*.jpg')))
    for v in (api(f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=5') or {}).get('data', []):
        va = v['attributes']
        print('VERSION', va['versionString'], va['appStoreState'])
        if va['appStoreState'] not in EDITABLE:
            continue
        for l in (api(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations") or {}).get('data', []):
            print('  LOC', l['attributes']['locale'], '->', 'uploading' if UPLOAD else 'would upload', len(files), 'iPad screenshots')
            if UPLOAD:
                upload_set(l['id'], files)

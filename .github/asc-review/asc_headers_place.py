"""Place APPROVED *-header-v2 pictures as the Product Page Header on the live version's localizations (Joseph asked 20-21 Nov).
Prints state only when not approved. Skips if a header placement already exists."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(method, path, body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:1200]); return None
for bundle in ['com.studsup.game', 'com.halfgridgames.marblemayhem', 'com.halfgridgames.knotwizard']:
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    print(f'\n=== {bundle}')
    for v in api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=3')['data']: print('  version', v['attributes']['versionString'], v['attributes']['appStoreState'])
    for s in (api('GET', f'/v1/reviewSubmissions?filter[app]={app}&limit=3') or {}).get('data', []): print('  submission', s['id'], s['attributes'].get('state'))
    lid = api('GET', f'/v1/apps/{app}/assetLibrary')['data']['id']
    imgs = [im for im in api('GET', f'/v1/appAssetLibraries/{lid}/images?limit=200')['data'] if (im['attributes'].get('referenceName') or '').endswith('-header-v2')]
    for im in imgs:
        st = im['attributes'].get('state'); print('  image', im['id'], st, im['attributes'].get('stateDetails'))
        if st != 'APPROVED': continue
        live = [v for v in api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&filter[appStoreState]=READY_FOR_SALE&limit=1')['data']]
        if not live: print('  no live version'); continue
        for l in api('GET', f"/v1/appStoreVersions/{live[0]['id']}/appStoreVersionLocalizations")['data']:
            have = api('GET', f"/v1/appStoreVersionLocalizations/{l['id']}/placements") or {}
            print('  existing placements', [ (p['attributes'].get('placementType')) for p in have.get('data', [])])
            if any(p['attributes'].get('placementType') == 'PRODUCT_PAGE_HEADER_ASSET' for p in have.get('data', [])): continue
            r = api('POST', '/v1/appAssetLibraryPlacements', {'data': {'type': 'appAssetLibraryPlacements', 'attributes': {'placementType': 'PRODUCT_PAGE_HEADER_ASSET'},
                 'relationships': {'image': {'data': {'type': 'appAssetLibraryImages', 'id': im['id']}},
                                   'appStoreVersionLocalization': {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id']}}}}})
            print('  PLACED header on', live[0]['attributes']['versionString'], l['attributes']['locale'], json.dumps(r['data']['attributes']) if r else 'FAILED')

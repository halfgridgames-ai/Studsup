"""Joseph 21 Nov ("With the api open now cant you do this"): send the uploaded *-header-v2 pictures to Apple's asset review,
and set the new promo text. Does not touch app versions or builds."""
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
PROMO = {
 'com.studsup.game': 'Football with no rules! Slide tackle anyone, flatten the ref and fire Fury fireballs. Beat 10 wild teams, or play a friend 1v1 online.',
 'com.halfgridgames.marblemayhem': 'Race 8 marbles down 41 wild downhill tracks. Throw bananas, send a bee after the leader and race your friends online. Now on iPad too!',
 'com.halfgridgames.knotwizard': 'Drag the pins until no rope crosses. 150 calm puzzles, 30 secret pictures hidden in the knots and a new Daily Knot every day. Now on iPad too!',
}
for bundle, promo in PROMO.items():
    app = api('GET', f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    print(f'\n=== {bundle}')
    # promo text on every version that is live or in review
    for v in api('GET', f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=5')['data']:
        for l in api('GET', f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
            r = api('PATCH', f"/v1/appStoreVersionLocalizations/{l['id']}", {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id'], 'attributes': {'promotionalText': promo}}})
            print('  promo', v['attributes']['versionString'], v['attributes']['appStoreState'], l['attributes']['locale'], 'ok' if r else 'FAILED')
    lid = api('GET', f'/v1/apps/{app}/assetLibrary')['data']['id']
    imgs = [im for im in api('GET', f'/v1/appAssetLibraries/{lid}/images?limit=200')['data'] if (im['attributes'].get('referenceName') or '').endswith('-header-v2')]
    for im in imgs: print('  image', im['id'], im['attributes'].get('state'), im['attributes'].get('stateDetails'))
    todo = [im for im in imgs if im['attributes'].get('state') in ('PREPARE_FOR_SUBMISSION', 'READY_FOR_REVIEW')]
    if not todo: continue
    sub = api('POST', '/v1/reviewSubmissions', {'data': {'type': 'reviewSubmissions', 'attributes': {'platform': 'IOS'},
              'relationships': {'app': {'data': {'type': 'apps', 'id': app}}}}})
    if not sub: continue
    sid = sub['data']['id']; ok = 0
    for im in todo:
        r = api('POST', '/v1/reviewSubmissionItems', {'data': {'type': 'reviewSubmissionItems', 'relationships': {
            'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': sid}},
            'appAssetLibraryImage': {'data': {'type': 'appAssetLibraryImages', 'id': im['id']}}}}})
        print('  item', im['id'], 'ok' if r else 'FAILED'); ok += bool(r)
    if ok:
        r = api('PATCH', f'/v1/reviewSubmissions/{sid}', {'data': {'type': 'reviewSubmissions', 'id': sid, 'attributes': {'submitted': True}}})
        print('  submitted:', r and r['data']['attributes'].get('state'))
    else:
        api('PATCH', f'/v1/reviewSubmissions/{sid}', {'data': {'type': 'reviewSubmissions', 'id': sid, 'attributes': {'canceled': True}}})
    time.sleep(3)
    for im in todo: print('  now', im['id'], api('GET', f"/v1/appAssetLibraryImages/{im['id']}")['data']['attributes'].get('state'))

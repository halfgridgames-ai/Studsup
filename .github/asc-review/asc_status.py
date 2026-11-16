"""Read-only status for all three iOS apps: App Store versions + attached build, review submissions,
in-app purchases and their states, newest builds, and what each public TestFlight link serves."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(path):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    try:
        with urllib.request.urlopen(urllib.request.Request('https://api.appstoreconnect.apple.com' + path, headers={'Authorization': 'Bearer ' + t})) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print('  ! GET', path.split('?')[0], e.code, e.read().decode()[:300]); return {'data': []}
for bundle, name in [('com.studsup.game', 'STUDS UP'), ('com.halfgridgames.marblemayhem', 'MARBLE MAYHEM'), ('com.halfgridgames.knotwizard', 'KNOT WIZARD')]:
    print(f'\n=== {name}')
    app = api(f'/v1/apps?filter[bundleId]={bundle}')['data'][0]['id']
    print('APP ID', app, f'https://apps.apple.com/app/id{app}')
    for v in api(f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=3')['data']:
        b = api(f"/v1/appStoreVersions/{v['id']}/build").get('data')
        va=v['attributes']; print('VERSION', va['versionString'], va['appStoreState'], 'build', b and b['attributes']['version'], 'releaseType', va.get('releaseType'), 'earliest', va.get('earliestReleaseDate'))
        for l in api(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
            la=l['attributes']; print('  LOC', la.get('locale'), 'marketingUrl', la.get('marketingUrl'), 'supportUrl', la.get('supportUrl'))
        rd = api(f"/v1/appStoreVersions/{v['id']}/appStoreReviewDetail").get('data')
        if rd:
            for a in api(f"/v1/appStoreReviewDetails/{rd['id']}/appStoreReviewAttachments").get('data', []):
                aa = a['attributes']; print('  ATTACHMENT', aa.get('fileName'), aa.get('fileSize'), (aa.get('assetDeliveryState') or {}).get('state'))
    for s in api(f'/v1/reviewSubmissions?filter[app]={app}&limit=5')['data']:
        items = api(f"/v1/reviewSubmissions/{s['id']}/items?limit=50")['data']
        kinds = {}
        for it in items:
            for k, rel in it.get('relationships', {}).items():
                if rel.get('data'): kinds[k] = kinds.get(k, 0) + 1
        print('SUBMISSION', s['attributes'].get('state'), s['attributes'].get('submittedDate'), 'items', kinds)
    iaps = api(f'/v1/apps/{app}/inAppPurchasesV2?limit=50')['data']
    print('IAPS', len(iaps))
    for p in iaps:
        a = p['attributes']; print('  IAP', a.get('productId'), a.get('inAppPurchaseType'), a.get('state'))
    for b in api(f'/v1/builds?filter[app]={app}&sort=-uploadedDate&limit=3&include=preReleaseVersion')['data']:
        d = api(f"/v1/builds/{b['id']}/buildBetaDetail")['data']['attributes']
        pv = (b['relationships'].get('preReleaseVersion') or {}).get('data') or {}
        print('BUILD', b['attributes']['version'], 'uploaded', b['attributes']['uploadedDate'][:10], 'external', d.get('externalBuildState'), 'expired', b['attributes'].get('expired'))
    for g in api(f'/v1/apps/{app}/betaGroups?limit=50')['data']:
        if g['attributes'].get('isInternalGroup'): continue
        gb = [x['attributes']['version'] for x in api(f"/v1/betaGroups/{g['id']}/builds?limit=20")['data']]
        print('LINK', g['attributes'].get('publicLink'), 'enabled', g['attributes'].get('publicLinkEnabled'), 'builds', gb)

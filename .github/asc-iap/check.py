"""Read-only: list Studs Up in-app purchases on App Store Connect and their state."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def token():
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
def api(path):
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, headers={'Authorization': 'Bearer ' + token()})
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print('  !', path, e.code, e.read().decode()[:400]); return {}
for bundle in ['com.studsup.game', 'com.halfgridgames.marblemayhem']:
    app = api(f'/v1/apps?filter[bundleId]={bundle}')['data'][0]
    print('\n=== ', bundle, app['id'])
    iaps = api(f"/v1/apps/{app['id']}/inAppPurchasesV2?limit=50").get('data', [])
    for i in iaps:
        a = i['attributes']
        print(f"  {a.get('productId'):28} {a.get('inAppPurchaseType'):16} {a.get('state'):24} name={a.get('name')!r}")
        if bundle == 'com.studsup.game':
            locs = api(f"/v2/inAppPurchases/{i['id']}/inAppPurchaseLocalizations").get('data', [])
            print('      locs:', [(l['attributes'].get('locale'), l['attributes'].get('name'), l['attributes'].get('state')) for l in locs])
            ps = api(f"/v2/inAppPurchases/{i['id']}/iapPriceSchedule")
            print('      priceSchedule:', 'yes' if ps.get('data') else 'NO')
            ss = api(f"/v2/inAppPurchases/{i['id']}/appStoreReviewScreenshot")
            print('      reviewShot:', (ss.get('data') or {}).get('attributes', {}).get('assetDeliveryState'))
            av = api(f"/v2/inAppPurchases/{i['id']}/inAppPurchaseAvailability")
            print('      availability:', 'yes' if av.get('data') else 'NO')
    vers = api(f"/v1/apps/{app['id']}/appStoreVersions?limit=3").get('data', [])
    for v in vers: print('  version', v['attributes']['versionString'], v['attributes']['appStoreState'])
    ag = api('/v1/apps/' + app['id'] + '/appInfos').get('data', [])

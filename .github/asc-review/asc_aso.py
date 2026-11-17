"""Cancel the waiting review submissions for MM 1.0.13 and KW 1.1.2 (Joseph chose this 17 Nov), then set new
name/subtitle/keywords/promo text. Also sets promo text on the live versions. NEVER resubmits."""
import json, os, time, urllib.request, urllib.error
import jwt
KEY_ID, ISSUER, P8 = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID'], os.environ['ASC_KEY_P8']
def api(path, method='GET', body=None):
    now = int(time.time())
    t = jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1100, 'aud': 'appstoreconnect-v1'}, P8, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})
    req = urllib.request.Request('https://api.appstoreconnect.apple.com' + path, method=method,
        data=json.dumps(body).encode() if body else None, headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            s = r.read(); return json.loads(s) if s else {}
    except urllib.error.HTTPError as e:
        print('  !', method, path.split('?')[0], e.code, e.read().decode()[:600]); return None
APPS = {
 '6829033430': dict(ver='1.0.13', name=None, sub='3D Marble Run & Ball Race',
   kw='racing,roll,obstacle,kart,party,multiplayer,online,offline,cup,track,boost,rush,speed,slide,fun,bump',
   promo='Race 8 marbles down 41 wild downhill tracks. Throw bananas, send a bee after the leader and race friends online. Free on iPhone!'),
 '6829033479': dict(ver='1.1.2', name='Knot Wizard: Untangle Puzzle', sub='Relaxing Rope & Logic Game',
   kw='tangle,lines,pins,calm,daily,casual,offline,brain,teaser,twist,zen,iq,riddle,satisfying,string,mind',
   promo='Drag the pins until no rope crosses. 150 calm puzzles, 30 secret pictures hidden in the knots and a new Daily Knot every day.'),
}
for app, c in APPS.items():
    assert len(c['kw']) <= 100 and len(c['sub']) <= 30 and len(c['promo']) <= 170
    print('\n=== APP', app)
    for s in (api(f'/v1/reviewSubmissions?filter[app]={app}&filter[state]=WAITING_FOR_REVIEW,READY_FOR_REVIEW&limit=5') or {}).get('data', []):
        print('CANCEL submission', s['id'], s['attributes']['state'])
        r = api(f"/v1/reviewSubmissions/{s['id']}", 'PATCH', {'data': {'type': 'reviewSubmissions', 'id': s['id'], 'attributes': {'canceled': True}}})
        print('  ->', r and r['data']['attributes'].get('state'))
    vers = api(f'/v1/apps/{app}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
    new = [v for v in vers if v['attributes']['versionString'] == c['ver']][0]
    for i in range(30):
        st = api(f"/v1/appStoreVersions/{new['id']}")['data']['attributes']['appStoreState']
        print('  version', c['ver'], 'state', st)
        if st not in ('WAITING_FOR_REVIEW', 'IN_REVIEW'): break
        time.sleep(10)
    for v in vers:
        live = v['attributes']['appStoreState'] == 'READY_FOR_SALE'
        if v['id'] != new['id'] and not live: continue
        for l in api(f"/v1/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
            attrs = {'promotionalText': c['promo']}
            if v['id'] == new['id']: attrs['keywords'] = c['kw']
            r = api(f"/v1/appStoreVersionLocalizations/{l['id']}", 'PATCH', {'data': {'type': 'appStoreVersionLocalizations', 'id': l['id'], 'attributes': attrs}})
            print('  VER-LOC', v['attributes']['versionString'], l['attributes']['locale'], 'ok' if r else 'FAILED', list(attrs))
    for ai in api(f'/v1/apps/{app}/appInfos')['data']:
        st = ai['attributes'].get('appStoreState')
        if st == 'READY_FOR_SALE': continue
        for l in api(f"/v1/appInfos/{ai['id']}/appInfoLocalizations")['data']:
            attrs = {'subtitle': c['sub']}
            if c['name']: attrs['name'] = c['name']
            r = api(f"/v1/appInfoLocalizations/{l['id']}", 'PATCH', {'data': {'type': 'appInfoLocalizations', 'id': l['id'], 'attributes': attrs}})
            print('  INFO-LOC', st, l['attributes']['locale'], 'ok' if r else 'FAILED', attrs)

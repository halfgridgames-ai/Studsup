"""Replace a game's Google Play screenshots (phone, 7-inch, 10-inch) through the Play Developer API.

Needs repo secret PLAY_SA_JSON: the JSON key of a Google Cloud service account that was invited in
Play Console (Users and permissions) with permission to manage the store listing.
Every listing language gets the same pictures. The edit is committed with changesNotSentForReview=true,
so Joseph still presses "Send changes for review" in Publishing overview. Nothing else is changed.
MODE=report only lists what is there now; MODE=replace swaps the pictures.
"""
import glob, json, os, time, urllib.request, urllib.error
import jwt

SA = json.loads(os.environ['PLAY_SA_JSON'])
PKG = os.environ.get('PLAY_PACKAGE', 'com.studsup.game')
KEY = os.environ.get('PLAY_KEY', 'su')
REPLACE = os.environ.get('MODE', 'report') == 'replace'
HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = {'phoneScreenshots': 'play-phone', 'sevenInchScreenshots': 'play-tablet', 'tenInchScreenshots': 'play-tablet'}
API = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' + PKG
UP = 'https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/' + PKG


def token():
    now = int(time.time())
    a = jwt.encode({'iss': SA['client_email'], 'scope': 'https://www.googleapis.com/auth/androidpublisher',
                    'aud': 'https://oauth2.googleapis.com/token', 'iat': now, 'exp': now + 3000},
                   SA['private_key'], algorithm='RS256')
    body = ('grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=' + a).encode()
    with urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token', data=body)) as r:
        return json.loads(r.read())['access_token']


TOK = token()


def call(url, method='GET', data=None, ctype='application/json'):
    req = urllib.request.Request(url, method=method, data=data,
                                 headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': ctype})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        print('  !', method, url.split('/applications/')[-1], e.code, e.read().decode()[:500])
        return None


edit = call(API + '/edits', 'POST', b'{}')
if not edit:
    raise SystemExit('Could not open an edit: check the service account is invited in Play Console.')
eid = edit['id']
langs = [l['language'] for l in (call(f'{API}/edits/{eid}/listings') or {}).get('listings', [])]
print('listing languages:', langs)
for lang in langs:
    for slot, folder in SLOTS.items():
        now = (call(f'{API}/edits/{eid}/listings/{lang}/{slot}') or {}).get('images', [])
        files = sorted(glob.glob(os.path.join(HERE, folder, KEY + '-*.jpg')))
        print(f'{lang} {slot}: {len(now)} now, {len(files)} new' + (' -> replacing' if REPLACE else ''))
        if not REPLACE:
            continue
        call(f'{API}/edits/{eid}/listings/{lang}/{slot}', 'DELETE')
        for f in files:
            r = call(f'{UP}/edits/{eid}/listings/{lang}/{slot}?uploadType=media', 'POST', open(f, 'rb').read(), 'image/jpeg')
            print('   ', os.path.basename(f), 'ok' if r else 'FAILED')
if REPLACE:
    r = call(f'{API}/edits/{eid}:commit?changesNotSentForReview=true', 'POST', b'{}')
    print('committed (Joseph sends for review in Publishing overview)' if r else 'COMMIT FAILED')
else:
    call(f'{API}/edits/{eid}', 'DELETE')

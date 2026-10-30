// window.Monetize: ads (AdMob) and in-app purchases (Google Play / App Store) for the phone app.
// The game calls these; see SHOP-SPEC.md. On the web, or in a build without the plugins,
// window.Monetize is left undefined so the game hides real-money items and skips ads.
(function () {
  var Cap = window.Capacitor;
  if (!Cap || !Cap.isNativePlatform || !Cap.isNativePlatform() || !Cap.isPluginAvailable('AdMob')) return;

  // AdMob IDs: the real Studs Up units (Half Grid Games AdMob account), one AdMob app per platform.
  // TEST = true shows test ads everywhere.
  var IDS = {
    android: {
      interstitial: 'ca-app-pub-4390358547833612/1920589232',
      rewarded: 'ca-app-pub-4390358547833612/1321823432'
    },
    ios: {
      interstitial: 'ca-app-pub-4390358547833612/9923715686',
      rewarded: 'ca-app-pub-4390358547833612/6966379851'
    }
  };
  var TEST = false;

  var PRODUCTS = [
    { id: 'coins_1000', consumable: true },
    { id: 'coins_5500', consumable: true },
    { id: 'coins_12000', consumable: true },
    { id: 'coins_30000', consumable: true },
    { id: 'remove_ads', consumable: false },
    { id: 'starter_pack', consumable: false }
  ];
  var MIN_AD_GAP_MS = 3 * 60 * 1000;
  var STATE_KEY = 'studsMonetize';

  var AdMob = Cap.registerPlugin('AdMob');
  var platform = Cap.getPlatform();
  var ids = IDS[platform] || IDS.android;
  var restoreFns = [];
  var restored = {};
  var store = null;
  var pending = {}; // product id -> {resolve}

  function loadState() {
    try { return JSON.parse(localStorage.getItem(STATE_KEY)) || {}; } catch (e) { return {}; }
  }
  function saveState(s) {
    try { localStorage.setItem(STATE_KEY, JSON.stringify(s)); } catch (e) {}
  }
  function owns(id) {
    if (store) { var p = store.get(id); if (p && p.owned) return true; }
    return !!(loadState().owned || {})[id];
  }
  function markOwned(id) {
    var s = loadState(); s.owned = s.owned || {}; s.owned[id] = true; saveState(s);
  }

  // ---------- Ads ----------
  // privacyOptions: true when Google's consent rules (UK/EU and some US states) need an
  // "Ad privacy choices" button in Settings so players can change their answer.
  var privacyOptions = false;
  var adsReady = (async function () {
    try {
      await AdMob.initialize({ initializeForTesting: TEST });
      var info = await AdMob.requestConsentInfo();
      if (info.status === 'REQUIRED' && info.isConsentFormAvailable) {
        info = await AdMob.showConsentForm();
      }
      privacyOptions = info.privacyOptionsRequirementStatus === 'REQUIRED';
      // iPhone: Apple's "Allow tracking?" prompt, asked once, after the consent form
      if (platform === 'ios') {
        try {
          var t = await AdMob.trackingAuthorizationStatus();
          if (t.status === 'notDetermined') await AdMob.requestTrackingAuthorization();
        } catch (e) {}
      }
      return info.canRequestAds !== false;
    } catch (e) {
      console.warn('Monetize: ads unavailable', e);
      return false;
    }
  })();

  function once(event) {
    return new Promise(function (resolve) {
      var handle;
      AdMob.addListener(event, function (arg) {
        if (handle) handle.remove();
        resolve(arg);
      }).then(function (h) { handle = h; });
    });
  }

  async function showInterstitial() {
    if (owns('remove_ads')) return;
    var s = loadState();
    s.interstitialCalls = (s.interstitialCalls || 0) + 1;
    saveState(s);
    // The game calls this after every 2nd match; skip the first call so a new player's first 3 matches are ad-free.
    if (s.interstitialCalls < 2) return;
    if (s.lastAdAt && Date.now() - s.lastAdAt < MIN_AD_GAP_MS) return;
    if (!(await adsReady)) return;
    try {
      await AdMob.prepareInterstitial({ adId: ids.interstitial, isTesting: TEST, immersiveMode: true });
      var closed = Promise.race([once('interstitialAdDismissed'), once('interstitialAdFailedToShow')]);
      await AdMob.showInterstitial();
      await closed;
      s = loadState(); s.lastAdAt = Date.now(); saveState(s);
    } catch (e) {
      console.warn('Monetize: interstitial failed', e);
    }
  }

  async function showRewarded(placement) {
    if (!(await adsReady)) return false;
    try {
      await AdMob.prepareRewardVideoAd({ adId: ids.rewarded, isTesting: TEST, immersiveMode: true });
      var rewarded = false;
      var h = await AdMob.addListener('onRewardedVideoAdReward', function () { rewarded = true; });
      var closed = Promise.race([once('onRewardedVideoAdDismissed'), once('onRewardedVideoAdFailedToShow')]);
      await AdMob.showRewardVideoAd();
      await closed;
      h.remove();
      return rewarded;
    } catch (e) {
      console.warn('Monetize: rewarded ad failed (' + placement + ')', e);
      return false;
    }
  }

  // ---------- Purchases ----------
  var storeReady = new Promise(function (resolve) {
    document.addEventListener('deviceready', async function () {
      try {
        var C = window.CdvPurchase;
        if (!C) return resolve(false);
        store = C.store;
        var plat = platform === 'ios' ? C.Platform.APPLE_APPSTORE : C.Platform.GOOGLE_PLAY;
        store.register(PRODUCTS.map(function (p) {
          return { id: p.id, platform: plat, type: p.consumable ? C.ProductType.CONSUMABLE : C.ProductType.NON_CONSUMABLE };
        }));
        store.when()
          .approved(function (tx) { tx.verify(); })
          .verified(function (receipt) { receipt.finish(); })
          .finished(function (tx) {
            (tx.products || []).forEach(function (p) {
              var cb = pending[p.id];
              if (cb) { delete pending[p.id]; cb({ ok: true, id: p.id }); }
              else if (p.id === 'remove_ads' || p.id === 'starter_pack') restore(p.id);
              if (p.id === 'remove_ads' || p.id === 'starter_pack') markOwned(p.id);
            });
          })
          .productUpdated(function (p) {
            if (p.owned && (p.id === 'remove_ads' || p.id === 'starter_pack')) { markOwned(p.id); restore(p.id); }
          });
        await store.initialize([plat]);
        resolve(true);
      } catch (e) {
        console.warn('Monetize: store unavailable', e);
        resolve(false);
      }
    }, false);
  });

  function restore(id) {
    if (restored[id]) return;
    restored[id] = true;
    restoreFns.forEach(function (fn) { try { fn(id); } catch (e) {} });
  }

  async function products() {
    if (!(await storeReady)) return [];
    return PRODUCTS.map(function (p) {
      var sp = store.get(p.id);
      return sp ? { id: p.id, title: sp.title, price: sp.pricing ? sp.pricing.price : '' } : null;
    }).filter(Boolean);
  }

  async function buy(id) {
    if (!(await storeReady)) return { ok: false, id: id };
    var p = store.get(id);
    var offer = p && p.getOffer();
    if (!offer) return { ok: false, id: id };
    return new Promise(function (resolve) {
      pending[id] = resolve;
      offer.order().then(function (err) {
        if (err) { delete pending[id]; resolve({ ok: false, id: id }); }
      });
    });
  }

  async function showPrivacyOptions() {
    try { await AdMob.showPrivacyOptionsForm(); } catch (e) { console.warn('Monetize: privacy options failed', e); }
  }

  window.Monetize = {
    ready: function () { return Promise.all([adsReady, storeReady]).then(function () {}); },
    privacyOptionsRequired: function () { return privacyOptions; },
    showPrivacyOptions: showPrivacyOptions,
    showInterstitial: showInterstitial,
    showRewarded: showRewarded,
    products: products,
    buy: buy,
    owns: owns,
    onRestore: function (fn) {
      restoreFns.push(fn);
      Object.keys(restored).forEach(function (id) { try { fn(id); } catch (e) {} });
    }
  };
})();

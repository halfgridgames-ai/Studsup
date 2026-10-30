// window.Analytics: Firebase Analytics for the phone app, so we can see how many players come
// back (day 1 / day 7) and how far they get before spending anything on promotion.
// Only events about play are sent (no names, no free text). On the web, or in a build without
// the plugin or google-services.json, window.Analytics.track does nothing.
(function () {
  var Cap = window.Capacitor;
  var on = !!(Cap && Cap.isNativePlatform && Cap.isNativePlatform() && Cap.isPluginAvailable('FirebaseAnalytics'));
  var FA = on ? Cap.registerPlugin('FirebaseAnalytics') : null;
  window.Analytics = {
    track: function (name, params) {
      if (!FA) return;
      try { FA.logEvent({ name: name, params: params || {} }).catch(function () {}); } catch (e) {}
    }
  };
})();

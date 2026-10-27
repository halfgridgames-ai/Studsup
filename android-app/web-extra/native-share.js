// Native sharing for the phone app. Android's WebView has no navigator.share and
// ignores <a download> on blobs, so the game's "Share this goal" and "Share code"
// buttons would do nothing. When running inside the Capacitor app, this swaps in
// navigator.share / navigator.canShare backed by the Share and Filesystem plugins:
// files are written to the app cache, then handed to the system share sheet.
// Outside the app (the web version) it does nothing.
(function () {
  var C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  var P = C.Plugins || {}, Share = P.Share, FS = P.Filesystem;
  if (!Share) return;

  function toBase64(blob) {
    return new Promise(function (ok, fail) {
      var r = new FileReader();
      r.onload = function () { var s = String(r.result); ok(s.slice(s.indexOf(',') + 1)); };
      r.onerror = function () { fail(r.error); };
      r.readAsDataURL(blob);
    });
  }

  navigator.canShare = function (d) {
    if (!d) return false;
    if (d.files && d.files.length) return !!FS;
    return !!(d.text || d.url || d.title);
  };

  navigator.share = async function (d) {
    d = d || {};
    var opts = { title: d.title, text: d.text, url: d.url, dialogTitle: 'Share' };
    if (d.files && d.files.length) {
      if (!FS) throw new DOMException('File sharing unavailable', 'NotAllowedError');
      var uris = [];
      for (var i = 0; i < d.files.length; i++) {
        var f = d.files[i], name = (f.name || ('studs-up-' + i)).replace(/[^\w.\-]/g, '_');
        var w = await FS.writeFile({ path: name, data: await toBase64(f), directory: 'CACHE' });
        uris.push(w.uri);
      }
      opts.files = uris;
    }
    try { await Share.share(opts); }
    catch (e) {
      // Closing the share sheet without picking an app is a cancel, not an error.
      if (/cancel/i.test(String(e && (e.message || e)))) throw new DOMException('Share canceled', 'AbortError');
      throw e;
    }
  };
})();

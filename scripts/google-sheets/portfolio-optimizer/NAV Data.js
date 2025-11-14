function CEF_PREM(ticker) {
  try {
    if (!ticker) return "";
    ticker = String(ticker).trim().toUpperCase();

    var cache = CacheService.getScriptCache();
    var key = "cefa-prem:" + ticker;
    var hit = cache.get(key);
    if (hit) return parseFloat(hit);

    var url = "https://api.cefa.com/fund-detail?ticker=" + encodeURIComponent(ticker);
    var res = UrlFetchApp.fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0", "Accept": "application/json" },
      followRedirects: true,
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) throw new Error("HTTP " + res.getResponseCode());

    var data = JSON.parse(res.getContentText());
    var raw = data?.fundDetails?.premiumDiscount; 
    if (raw == null || raw === "") throw new Error("fundDetails.premiumDiscount not found");

    var dec = parseFloat(raw) / 100; 
    cache.put(key, String(dec), 1800); 
    return dec;
  } catch (e) {
    return "ERR: " + (e?.message || e);
  }
}

function CEF_DATA(ticker) {
  try {
    if (!ticker) return ["","",""];
    ticker = String(ticker).trim().toUpperCase();

    var url = "https://api.cefa.com/fund-detail?ticker=" + encodeURIComponent(ticker);
    var res = UrlFetchApp.fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0", "Accept": "application/json" },
      followRedirects: true,
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) throw new Error("HTTP " + res.getResponseCode());

    var d = JSON.parse(res.getContentText())?.fundDetails || {};
    var nav   = d.nav != null ? parseFloat(d.nav) : "";
    var price = d.marketPrice != null ? parseFloat(d.marketPrice) : "";
    var prem  = d.premiumDiscount != null ? parseFloat(d.premiumDiscount)/100 : "";
    return [nav, price, prem];
  } catch (e) {
    return ["ERR", e?.message || e, ""];
  }
}
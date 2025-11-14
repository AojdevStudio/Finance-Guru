const CFG = Object.freeze({
  sheets: { yields: 'Dividend Yields', inputs: 'User Inputs', fire: 'FIRE Model' },
  cols: { ticker: 1, drip: 2, dripYield: 3, nonYield: 4, alloc: 5, price: 6, nav: 7, premium: 8 }, // A..H
  cacheSec: 1800,
  ua: 'Mozilla/5.0 (compatible; GoogleAppsScript/1.0)',
  maxRunMs: 60 * 1000
});

function updateYieldsFast() {
  const started = Date.now();
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName(CFG.sheets.yields);
  if (!sh) return;

  ensureCornerstoneHeaders_(sh);

  const lastRow = findLastDataRow_(sh, CFG.cols.ticker);
  if (lastRow < 2) return;
  const n = lastRow - 1;

  const tickers = sh.getRange(2, CFG.cols.ticker, n, 1).getDisplayValues()
    .flat().map(s => String(s || '').trim().toUpperCase());
  const drips = sh.getRange(2, CFG.cols.drip, n, 1).getValues()
    .flat().map(Boolean);

  const prevC = sh.getRange(2, CFG.cols.dripYield, n, 1).getValues().map(r => r[0]);
  const prevD = sh.getRange(2, CFG.cols.nonYield, n, 1).getValues().map(r => r[0]);

  const uniq = [...new Set(tickers.filter(Boolean))];
  const dhMap = fetchDivHistoryBatch_(uniq);

  const clmNav = uniq.includes('CLM') ? fetchCornerstoneFromCEFA_('CLM') : null;
  const crfNav = uniq.includes('CRF') ? fetchCornerstoneFromCEFA_('CRF') : null;
  const navMap = { CLM: clmNav, CRF: crfNav };

  const outC = [], outD = [], outPrice = [], outNAV = [], outPrem = [];

  for (let i = 0; i < n; i++) {
    if (Date.now() - started > CFG.maxRunMs) break;

    const tk = tickers[i];
    const isDrip = drips[i];

    let dripVal = prevC[i] || '';
    let nonVal = prevD[i] || '';
    let priceW = '', navW = '', premW = '';

    if (!tk) {
      push();
      continue;
    }

    const y = dhMap[tk];
    if (y !== undefined && y !== '') {
      if (isDrip) {
        dripVal = y;
        nonVal = '';
      } else {
        nonVal = y;
        dripVal = '';
      }
    }

    if (tk === 'CLM' || tk === 'CRF') {
      const nd = navMap[tk];
      if (nd) {
        if (isDrip && y !== '' && isFinite(nd.price) && isFinite(nd.nav) && nd.nav > 0) {
          dripVal = y * (nd.price / nd.nav);
          nonVal = '';
        }
        if (isFinite(nd.price)) priceW = nd.price;
        if (isFinite(nd.nav)) navW = nd.nav;
        if (isFinite(nd.premium)) {
          premW = nd.premium;
        } else if (isFinite(nd.price) && isFinite(nd.nav) && nd.nav > 0) {
          premW = (nd.price / nd.nav) - 1;
        }
      }
    }

    if (isDrip) nonVal = ''; else dripVal = '';
    push();

    function push() {
      outC.push([dripVal]);
      outD.push([nonVal]);
      outPrice.push([priceW || '--']);
      outNAV.push([navW || '--']);
      outPrem.push([premW === '' ? '--' : premW]);
    }
  }

  sh.getRange(2, CFG.cols.dripYield, n, 1).setValues(outC);
  sh.getRange(2, CFG.cols.nonYield, n, 1).setValues(outD);
  sh.getRange(2, CFG.cols.price, n, 1).setValues(outPrice);
  sh.getRange(2, CFG.cols.nav, n, 1).setValues(outNAV);
  sh.getRange(2, CFG.cols.premium, n, 1).setValues(outPrem);

  sh.getRange(2, CFG.cols.dripYield, n, 2).setNumberFormat('0.00%');
  sh.getRange(2, CFG.cols.price, n, 1).setNumberFormat('$0.00');
  sh.getRange(2, CFG.cols.nav, n, 1).setNumberFormat('$0.00');
  sh.getRange(2, CFG.cols.premium, n, 1).setNumberFormat('0.00%');

  SpreadsheetApp.flush();
  writeBlendedYieldsToUserInputs();
}

function writeBlendedYieldsToUserInputs() {
  const ss = SpreadsheetApp.getActive();
  const dy = ss.getSheetByName(CFG.sheets.yields);
  if (!dy) return;
  const lastRow = findLastDataRow_(dy, CFG.cols.ticker);
  const n = Math.max(0, lastRow - 1);
  if (n === 0) return;

  const rows = dy.getRange(2, 1, n, 5).getValues(); // A..E
  const { dripBlendPct, nonDripBlendPct } = computeBlendedFromRows(rows);

  const ui = ss.getSheetByName(CFG.sheets.inputs);
  if (ui) {
    ui.getRange('B7').setValue(dripBlendPct);
    ui.getRange('B8').setValue(nonDripBlendPct);
    ui.getRange('B7:B8').setNumberFormat('0.00');
  }
}

function computeBlendedFromRows(rows) {
  let dripAlloc = 0, nonAlloc = 0, dripNum = 0, nonNum = 0;
  for (const r of rows) {
    const isDrip = !!r[1];
    const y = isDrip ? cleanPctOrDec(r[2]) : cleanPctOrDec(r[3]);
    const alloc = cleanPctOrDec(r[4]);
    if (!(alloc > 0) || !(y >= 0)) continue;
    if (isDrip) { dripAlloc += alloc; dripNum += y * alloc; }
    else { nonAlloc += alloc; nonNum += y * alloc; }
  }
  const dripBlend = dripAlloc > 0 ? (dripNum / dripAlloc) : 0;
  const nonBlend = nonAlloc > 0 ? (nonNum / nonAlloc) : 0;
  return {
    dripBlendPct: Math.round(dripBlend * 10000) / 100,
    nonDripBlendPct: Math.round(nonBlend * 10000) / 100
  };
}

function fetchDivHistoryBatch_(tickers) {
  const cache = CacheService.getDocumentCache();
  const out = {}, toFetch = [];
  for (const t of tickers) {
    const hit = cache.get(`divhist:${t}`);
    if (hit !== null) out[t] = Number(hit);
    else toFetch.push(t);
  }
  if (toFetch.length === 0) return out;

  const reqs = toFetch.map(t => ({
    url: `https://dividendhistory.org/payout/${encodeURIComponent(t)}/`,
    method: 'get',
    muteHttpExceptions: true,
    followRedirects: true,
    headers: { 'User-Agent': CFG.ua }
  }));
  const resps = UrlFetchApp.fetchAll(reqs);
  for (let i = 0; i < resps.length; i++) {
    const t = toFetch[i], r = resps[i];
    try {
      if (r.getResponseCode() >= 200 && r.getResponseCode() < 300) {
        const html = r.getContentText().replace(/\s+/g, ' ');
        const y = pickNum_([
          /(?:Dividend\s*)?Yield:\s*([\d.,]+)\s*%/i,
          /Dividend\s*Yield<\/(?:th|td)>\s*<(?:td|span)[^>]*>\s*([\d.,]+)\s*%/i,
          /Yield[^%]{0,40}([\d.,]+)\s*%/i
        ], html);
        if (isFinite(y)) {
          const dec = y / 100;
          out[t] = dec;
          cache.put(`divhist:${t}`, String(dec), CFG.cacheSec);
          continue;
        }
      }
      out[t] = '';
    } catch (_) { out[t] = ''; }
  }
  return out;
}

function fetchCornerstoneFromCEFA_(ticker) {
  const cache = CacheService.getDocumentCache();
  const key = 'cefa:' + ticker;
  const hit = cache.get(key);
  if (hit) return JSON.parse(hit);

  const [nav, price, prem] = CEF_DATA(ticker);
  const out = (nav === "ERR") ? { price: null, nav: null, premium: null } : {
    price: (price === "" ? null : Number(price)),
    nav: (nav === "" ? null : Number(nav)),
    premium: (prem === "" ? null : Number(prem))
  };

  cache.put(key, JSON.stringify(out), CFG.cacheSec);
  return out;
}

function CEF_DATA(ticker) {
  try {
    if (!ticker) return ["", "", ""];
    ticker = String(ticker).trim().toUpperCase();

    var url = "https://api.cefa.com/fund-detail?ticker=" + encodeURIComponent(ticker);
    var res = UrlFetchApp.fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0", "Accept": "application/json" },
      followRedirects: true,
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) throw new Error("HTTP " + res.getResponseCode());

    var d = JSON.parse(res.getContentText())?.fundDetails || {};
    var nav = d.nav != null ? parseFloat(d.nav) : "";
    var price = d.marketPrice != null ? parseFloat(d.marketPrice) : "";
    var prem = d.premiumDiscount != null ? parseFloat(d.premiumDiscount) / 100 : "";
    return [nav, price, prem];
  } catch (e) {
    return ["ERR", e?.message || e, ""];
  }
}

function cleanPctOrDec(v) {
  if (v == null) return 0;
  const s = String(v).trim();
  if (s === '' || s === '--') return 0;
  if (/%/.test(s)) {
    const p = Number(s.replace(/[,%]/g, ''));
    return isFinite(p) && p >= 0 ? p / 100 : 0;
  }
  const n = Number(s.replace(/,/g, ''));
  if (!isFinite(n) || n < 0) return 0;
  return n > 3 ? n / 100 : n;
}

function pickNum_(patterns, html) {
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) {
      const n = Number(String(m[1]).replace(/,/g, ''));
      if (isFinite(n)) return n;
    }
  }
  return NaN;
}

function findLastDataRow_(sh, colIdx) {
  const vals = sh.getRange(1, colIdx, Math.max(2, sh.getLastRow()))
    .getDisplayValues().map(r => String(r[0]).trim());
  let last = vals.length;
  while (last > 1 && vals[last - 1] === '') last--;
  return last;
}

function ensureCornerstoneHeaders_(sh) {
  const labels = [
    { col: CFG.cols.price, text: 'Price (CLM/CRF)' },
    { col: CFG.cols.nav, text: 'NAV (CLM/CRF)' },
    { col: CFG.cols.premium, text: 'Premium/(Discount) (CLM/CRF)' }
  ];
  labels.forEach(({ col, text }) => {
    const v = String(sh.getRange(1, col).getDisplayValue() || '').trim();
    if (!v) sh.getRange(1, col).setValue(text);
  });
}
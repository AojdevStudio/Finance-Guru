/******************************************************
 * FAST DIVIDEND DATA REFRESH 
 *  * Populates:
 *   I: Days Until Ex-Date
 *   K: Days Until Pay
 *   L: Next Pay Amount  (per-share × Shares Owned)
 *   M: Dividend Yield (dec)  (TTM / Current Price)
 ******************************************************/

function onEditDividend(e) {
  const sheet = e.range.getSheet();
  const cell = e.range;
  if (sheet.getName() === "Portfolio" && cell.getA1Notation() === "M1") {
    updateDividendDataFast();
  }
}

const DD_CFG = Object.freeze({
  SHEET_NAME: 'Portfolio',
  HEADER_ROW: 2,
  START_ROW:  3,
  CACHE_TTL_SEC: 3600,                  // 1 hour cache
  USER_AGENT: 'Mozilla/5.0 (AppsScript)',
  SLEEP_MS_BETWEEN_FETCHES: 150
});

const OUT_COLS = Object.freeze({ exDays: 'I', payDays: 'K', payAmt: 'L', yldDec: 'M', ttm: 'G' });
const OUT_HDRS = Object.freeze({
  exDays: 'Days Until Ex-Date',
  payDays: 'Days Until Pay',
  payAmt: 'Next Pay Amount',
  yldDec: 'Dividend Yield',
  ttm:    'TTM Dividend'
});

// cadence tolerances (favor weekly/4-week)
const CADENCE_TOL = Object.freeze({ WEEKLY: 1, FOURWK: 2, MONTH: 3, QUART: 10 });

function updateDividendDataFast() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName(DD_CFG.SHEET_NAME);
  if (!sh) { SpreadsheetApp.getUi().alert('Sheet "Portfolio" not found.'); return; }

  const cols = detectTickerPriceSharesCols_(sh);
  if (!cols) return;

  const nRows = Math.max(0, sh.getLastRow() - DD_CFG.START_ROW + 1);
  if (nRows === 0) return;

  const tickers = sh.getRange(DD_CFG.START_ROW, cols.TICKER, nRows, 1)
                    .getValues().map(r => String(r[0]||'').trim().toUpperCase());
  const prices  = sh.getRange(DD_CFG.START_ROW, cols.PRICE,  nRows, 1)
                    .getValues().map(r => toNumLoose_(r[0]));
  const shares  = sh.getRange(DD_CFG.START_ROW, cols.SHARES, nRows, 1)
                    .getValues().map(r => toNumLoose_(r[0]) || 0);

  // fetch each unique ticker once (cached)
  const uniq = Array.from(new Set(tickers.filter(Boolean)));
  const bundleByT = {};
  for (const t of uniq) {
    bundleByT[t] = fetchDivPageBundle_(t);  // { ttm, exDays, payDate, payAmt }
    Utilities.sleep(DD_CFG.SLEEP_MS_BETWEEN_FETCHES);
  }

  const exDaysArr  = Array(nRows).fill(0).map(()=>['']);
  const payDaysArr = Array(nRows).fill(0).map(()=>['']);
  const payAmtArr  = Array(nRows).fill(0).map(()=>['']);
  const yldDecArr  = Array(nRows).fill(0).map(()=>['']);
  const ttmArr     = Array(nRows).fill(0).map(()=>['']);

  const today = atMidnight_tz_(new Date());

  for (let r=0; r<nRows; r++) {
    const t = tickers[r];
    const B = t ? bundleByT[t] : null;
    if (!B) continue;

    // I: Ex-date
    if (B.exDays == null) {
      exDaysArr[r][0] = '';
    } else {
      exDaysArr[r][0] = (B.exDays === 0) ? 'ExDate' : B.exDays;
    }

    // K: Pay days
    if (B.payDate instanceof Date && !isNaN(B.payDate)) {
      const dLeft = Math.ceil((atMidnight_tz_(B.payDate) - today)/86400000);
      payDaysArr[r][0] = (dLeft <= 0) ? '$$$$' : dLeft;
    } else {
      payDaysArr[r][0] = '';
    }

    // L: Next pay amount × shares
    const perShare = (B.payAmt != null ? B.payAmt : null);
    payAmtArr[r][0] = (isFinite(perShare) && perShare > 0 && shares[r] > 0)
      ? round2_(perShare * shares[r]) : '';

    // M: yield = TTM / price
    const ttm = (isFinite(B.ttm) ? B.ttm : 0);
    const p = prices[r];
    yldDecArr[r][0] = (isFinite(ttm) && ttm>0 && isFinite(p) && p>0) ? (ttm/p) : '';

    // G: TTM Dividend (per share, last 12 months)
    ttmArr[r][0] = (isFinite(B.ttm) && B.ttm > 0) ? round2_(B.ttm) : '';
  }

  // headers + writes
  const colEx  = colLetterToIdx_(OUT_COLS.exDays);
  const colPay = colLetterToIdx_(OUT_COLS.payDays);
  const colAmt = colLetterToIdx_(OUT_COLS.payAmt);
  const colYld = colLetterToIdx_(OUT_COLS.yldDec);
  const colTtm = colLetterToIdx_(OUT_COLS.ttm);  

  sh.getRange(DD_CFG.HEADER_ROW, colEx ).setValue(OUT_HDRS.exDays);
  sh.getRange(DD_CFG.HEADER_ROW, colPay).setValue(OUT_HDRS.payDays);
  sh.getRange(DD_CFG.HEADER_ROW, colAmt).setValue(OUT_HDRS.payAmt);
  sh.getRange(DD_CFG.HEADER_ROW, colYld).setValue(OUT_HDRS.yldDec);
  sh.getRange(DD_CFG.HEADER_ROW, colTtm).setValue(OUT_HDRS.ttm);

  sh.getRange(DD_CFG.START_ROW, colEx,  nRows, 1).clearContent().setValues(exDaysArr);
  sh.getRange(DD_CFG.START_ROW, colPay, nRows, 1).clearContent().setValues(payDaysArr);
  sh.getRange(DD_CFG.START_ROW, colAmt, nRows, 1).clearContent().setValues(payAmtArr);
  sh.getRange(DD_CFG.START_ROW, colYld, nRows, 1).clearContent().setValues(yldDecArr);
  sh.getRange(DD_CFG.START_ROW, colTtm, nRows, 1).clearContent().setValues(ttmArr);

  SpreadsheetApp.getActive().toast('Dividend data updated.', 'Done', 4);
}

/* ========== Fetch + Parse (one request per ticker) ========== */

function fetchDivPageBundle_(ticker) {
  const cache = CacheService.getDocumentCache();
  const key = 'divhist:bundle:v7:' + ticker;
  const hit = cache.get(key);
  if (hit) {
    try {
      const obj = JSON.parse(hit);
      // Rehydrate payDate if it was serialized to ISO string
      if (obj && obj.payDate) {
        const d = new Date(obj.payDate);
        obj.payDate = (d instanceof Date && !isNaN(d.getTime())) ? d : '';
      }
      return obj;
    } catch(e) {}
  }

  const url = 'https://dividendhistory.org/payout/' + encodeURIComponent(ticker) + '/';
  let html = '';
  try {
    const resp = UrlFetchApp.fetch(url, {
      method:'get', followRedirects:true, muteHttpExceptions:true,
      headers:{'User-Agent': DD_CFG.USER_AGENT}
    });
    const code = resp.getResponseCode();
    if (200 <= code && code < 300) html = resp.getContentText().replace(/\s+/g,' ');
  } catch (e) {}

  const today = atMidnight_tz_(new Date());
  const out = parseFromHtml_(html, today);

  // Store with payDate as ISO for portability
  const toStore = Object.assign({}, out, {
    payDate: (out.payDate instanceof Date && !isNaN(out.payDate.getTime()))
      ? out.payDate.toISOString() : out.payDate
  });
  cache.put(key, JSON.stringify(toStore), DD_CFG.CACHE_TTL_SEC);

  return out;
}

/** -> { ttm, exDays, payDate, payAmt } */
function parseFromHtml_(html, today) {
  if (!html) return { ttm:0, exDays:null, payDate:'', payAmt:null };

  const tables = html.match(/<table[\s\S]*?<\/table>/gi) || [];

  // collect data from all tables, tolerant to header or data-label layouts
  const exFuture = [];
  const exPast   = [];
  const payFuture = [];      // Dates >= today
  const payPast   = [];      // Dates  < today
  let   pastAmtLatest = null;
  let   pastDateLatest = null;

  // also compute TTM from any Pay table we see
  const rowsAll = html.match(/<tr[\s\S]*?<\/tr>/gi) || [];
  const cutoff = new Date(today); cutoff.setFullYear(cutoff.getFullYear()-1); cutoff.setDate(1);
  let ttm = 0;

  for (const tr of rowsAll) {
    const tds = tr.match(/<td[\s\S]*?<\/td>/gi);
    if (!tds || tds.length < 3) continue;
    const payDateMaybe = parseFlexible_(stripHtml_(tds[1]).trim());
    const amtMaybe     = parseCash_(stripHtml_(tds[2]).trim());
    if (payDateMaybe && amtMaybe != null) {
      const D = atMidnight_tz_(payDateMaybe);
      if (D >= cutoff && D <= today) ttm += amtMaybe;
    }
  }

  for (const t of tables) {
    const rows = t.match(/<tr[\s\S]*?<\/tr>/gi) || [];
    if (rows.length < 2) continue;

    // headers if any
    let headers = [];
    const ths = rows[0].match(/<th[\s\S]*?<\/th>/gi);
    if (ths && ths.length) headers = ths.map(x => norm_(stripHtml_(x)));

    const exCol  = headers.findIndex(h => h.includes('ex') && h.includes('date'));
    const payCol = findPayColByHeader_(headers);
    const amtCol = findAmountColByHeader2_(headers);

    const dataRows = rows.slice(headers.length ? 1 : 1);

    for (const row of dataRows) {
      const cells = row.match(/<t[dh][\s\S]*?<\/t[dh]>/gi);
      if (!cells || !cells.length) continue;

      // EX DATE (header col or data-label)
      let exTxt = null;
      if (exCol !== -1 && exCol < cells.length) exTxt = extractCellText_(cells[exCol]);
      if (!exTxt) {
        const hit = findTdByDataLabel_(cells, ['ex dividend date','ex-dividend date','ex date','ex-date']);
        if (hit) exTxt = extractCellText_(hit);
      }
      if (exTxt) {
        const d = parseFlexible_(exTxt);
        if (d) {
          const D = atMidnight_tz_(d);
          if (D >= today) exFuture.push(D); else exPast.push(D);
        }
      }

      // PAY DATE
      let payTxt = null;
      if (payCol !== -1 && payCol < cells.length) payTxt = extractCellText_(cells[payCol]);
      if (!payTxt) {
        const hit = findTdByDataLabel_(cells, ['pay date','payment date','payable date','pay-date','payment-date','payable-date']);
        if (hit) payTxt = extractCellText_(hit);
      }

      // AMOUNT
      let amt = null;
      if (amtCol !== -1 && amtCol < cells.length) amt = parseAmountSafe_(extractCellText_(cells[amtCol]));
      if (amt == null) {
        const hit = findTdByDataLabel_(cells, ['amount','dividend','distribution','cash amount','rate']);
        if (hit) amt = parseAmountSafe_(extractCellText_(hit));
      }
      if (amt == null) {
        for (const c of cells) { const g = parseAmountSafe_(extractCellText_(c)); if (g != null) { amt = g; break; } }
      }

      if (payTxt) {
        const d = parseFlexible_(payTxt);
        if (d) {
          const D = atMidnight_tz_(d);
          if (D >= today) payFuture.push({d:D, amt});
          else {
            payPast.push(D);
            if (!pastDateLatest || D > pastDateLatest) {
              pastDateLatest = D; pastAmtLatest = amt != null ? amt : pastAmtLatest;
            }
          }
        }
      }
    }
  }

  // Ex-days: posted future beats estimate
  let exDays = null;
  if (exFuture.length) {
    const soonest = exFuture.sort((a,b)=>a-b)[0];
    exDays = Math.ceil((soonest - today)/86400000);
  } else if (exPast.length) {
    exPast.sort((a,b)=>b-a);
    const period = inferPeriod_(exPast, html);
    if (period != null) {
      let next = new Date(exPast[0]);
      while (atMidnight_tz_(next) < today) next.setDate(next.getDate()+period);
      if (period % 7 === 0) {
        const wk = exPast[0].getDay();
        while (next.getDay() !== wk) next.setDate(next.getDate()+1);
      }
      exDays = Math.ceil((atMidnight_tz_(next) - today)/86400000);
    }
  }

  // Pay date + amount
  let payDate = '';
  let payAmt  = null;
  if (payFuture.length) {
    const soon = payFuture.sort((a,b)=>a.d-b.d)[0];
    payDate = soon.d; payAmt = soon.amt;
  } else if (payPast.length) {
    payPast.sort((a,b)=>b-a);
    const period = inferPeriod_(payPast, html);
    let next = new Date(payPast[0]);
    while (atMidnight_tz_(next) < today) next.setDate(next.getDate()+period);
    if (period % 7 === 0) {
      const wk = payPast[0].getDay();
      while (next.getDay() !== wk) next.setDate(next.getDate()+1);
    }
    payDate = atMidnight_tz_(next);
    payAmt  = (pastAmtLatest != null ? pastAmtLatest : null);
  }

  return { ttm, exDays, payDate, payAmt };
}

/* ---------- Cadence inference (favor weekly / 4-week) ---------- */
function inferPeriod_(datesDesc, html) {
  const hint = readFrequency_(html); // weekly / every-4-weeks / monthly / quarterly / null
  if (hint === 'weekly') return 7;
  if (hint === 'every-4-weeks') return 28;
  if (hint === 'monthly') return 30;
  if (hint === 'quarterly') return 90;

  if (datesDesc.length < 2) return 30; // safe default

  const gaps = [];
  for (let i=0; i<datesDesc.length-1; i++) {
    const g = Math.round((datesDesc[i] - datesDesc[i+1]) / 86400000);
    if (g > 0 && g < 120) gaps.push(g);
  }
  if (!gaps.length) return 30;

  gaps.sort((a,b)=>a-b);
  const med = gaps[Math.floor(gaps.length/2)];

  // choose nearest among [7,14,28,30,90] with tolerances; prefer shorter if equal
  const cands = [
    {p:7,  tol:CADENCE_TOL.WEEKLY},
    {p:14, tol:CADENCE_TOL.WEEKLY+1},
    {p:28, tol:CADENCE_TOL.FOURWK},
    {p:30, tol:CADENCE_TOL.MONTH},
    {p:90, tol:CADENCE_TOL.QUART}
  ];
  // exact within tolerance?
  for (const c of cands) if (Math.abs(med - c.p) <= c.tol) return c.p;

  // otherwise pick the nearest (bias toward small p on tie)
  let best = {p:30, diff:1e9};
  for (const c of cands) {
    const diff = Math.abs(med - c.p);
    if (diff < best.diff || (diff === best.diff && c.p < best.p)) best = {p:c.p, diff};
  }
  return best.p;
}

/* ---------- Hints & helpers ---------- */
function readFrequency_(html){
  const s = norm_(html);
  const m = /(frequency|payout frequency|distribution schedule)\s*:\s*([a-z0-9 \-]+)/i.exec(s);
  if (!m) return null;
  const f = (m[2]||'').toLowerCase();
  if (f.includes('weekly')) return 'weekly';
  if (f.includes('every-4-weeks') || f.includes('every 4 weeks') || f.includes('4 weeks')) return 'every-4-weeks';
  if (f.includes('monthly')) return 'monthly';
  if (f.includes('quarter')) return 'quarterly';
  return null;
}

function detectTickerPriceSharesCols_(sh) {
  const lastCol = sh.getLastColumn();
  const hdr = sh.getRange(DD_CFG.HEADER_ROW, 1, 1, lastCol).getValues()[0]
               .map(v => (v||'').toString().trim().toLowerCase());

  const findCol = (cands) => {
    for (let c=0;c<hdr.length;c++){
      const h = hdr[c];
      for (const words of cands) if (words.every(w => h.includes(w))) return c+1;
    }
    return 0;
  };

  const TICKER = findCol([['ticker']]);
  const PRICE  = findCol([['current','price'], ['price']]);
  const SHARES = findCol([['shares','owned'], ['qty','owned'], ['shares']]);

  if (!TICKER) { SpreadsheetApp.getUi().alert('Ticker column not found on row '+DD_CFG.HEADER_ROW); return null; }
  if (!PRICE)  { SpreadsheetApp.getUi().alert('Price column not found.'); return null; }
  if (!SHARES) { SpreadsheetApp.getUi().alert('Shares Owned column not found.'); return null; }
  return { TICKER, PRICE, SHARES };
}

/* ---------- parsing utilities ---------- */
function stripHtml_(s){ return String(s||'').replace(/<[^>]*>/g,'').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&'); }
function norm_(s){ return stripHtml_(s).toLowerCase().replace(/[^a-z0-9 ]+/g,' ').replace(/\s+/g,' ').trim(); }
function atMidnight_tz_(d) {
  const tz = Session.getScriptTimeZone() || 'Etc/UTC';
  return new Date(Utilities.formatDate(new Date(d), tz, 'yyyy-MM-dd') + 'T00:00:00');
}
function parseFlexible_(text){
  text = (text||'').trim();
  let m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(text); if (m) return new Date(+m[1], +m[2]-1, +m[3]);
  m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(text);    if (m) return new Date(+m[3], +m[1]-1, +m[2]);
  m = /^(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{4})$/.exec(text); if (m) return new Date(+m[3], monthIdx_(m[2]), +m[1]);
  m = /^([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})$/.exec(text); if (m) return new Date(+m[3], monthIdx_(m[1]), +m[2]);
  const d = new Date(text); return isNaN(d) ? null : d;
}
function monthIdx_(mmm){ const a=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']; const i=a.indexOf(mmm.slice(0,3).toLowerCase()); return i<0?0:i; }
function parseCash_(s){ const n = Number(String(s||'').replace(/[^0-9.\-]/g,'')); return (isFinite(n)&&n>0) ? n : null; }
function parseAmountSafe_(s){
  if (!s) return null;
  let raw = String(s).trim();
  if (!raw || raw==='-' || raw==='—') return null;
  const maybeDate = parseFlexible_(raw);
  if (maybeDate instanceof Date && !isNaN(maybeDate)) return null;
  let cleaned = raw.replace(/[^0-9.\-]/g,'');
  if (!cleaned) return null;
  if (/^\d{4}$/.test(cleaned)) return null;
  const n = Number(cleaned);
  if (!isFinite(n) || n<=0 || n>1000) return null;
  return n;
}
function toNumLoose_(x){ const n = Number(String(x||'').toString().replace(/[^0-9.\-]/g,'')); return isFinite(n)?n:NaN; }
function round2_(n){ return Math.round(n*100)/100; }
function colLetterToIdx_(L){ let s=String(L||'').trim().toUpperCase(); let n=0; for (let i=0;i<s.length;i++) n=n*26 + (s.charCodeAt(i)-64); return n; }
function extractCellText_(tdHtml){ const inner = String(tdHtml||'').replace(/<[^>]*>/g,'').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').trim(); return (inner==='-'||inner==='—') ? '' : inner; }
function findPayColByHeader_(headers){
  let idx = headers.findIndex(h => h.includes('pay') && h.includes('date') && !h.includes('ex'));
  if (idx !== -1) return idx;
  idx = headers.findIndex(h => (h.includes('payment')||h.includes('payable')) && h.includes('date'));
  if (idx !== -1) return idx;
  idx = headers.findIndex(h => h.includes('pay') && h.includes('project'));
  return idx;
}
function findAmountColByHeader2_(headers){
  for (let i=0;i<headers.length;i++){
    const h = headers[i];
    const ok = (h.includes('amount') || h.includes('rate') ||
      ((h.includes('dividend')||h.includes('distribution')) && !h.includes('date') && !h.includes('ex') && !h.includes('record') && !h.includes('pay')));
    if (!ok) continue;
    if (h.includes('date') || h.includes('ex') || h.includes('record') || h.includes('pay')) continue;
    return i;
  }
  return -1;
}
function findTdByDataLabel_(cells, labels){
  for (const c of cells){
    const m = /data-label\s*=\s*"(.*?)"/i.exec(c);
    if (!m) continue;
    const lab = norm_(m[1]||'');
    for (const want of labels) if (lab.indexOf(want) !== -1) return c;
  }
  return null;
}



function addDividendFast() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sh = ss.getSheetByName("Dividends");

  // Get up to 43 entries (A2:D44)
  const entries = sh.getRange("A2:D44").getValues();

  const toAppend = [];

  for (let i = 0; i < entries.length; i++) {
    const [ticker, amount, date, drip] = entries[i];

    // Skip blank rows
    if (!ticker || !amount || !date) continue;

    const jsDate = new Date(date);
    const year = jsDate.getFullYear();
    const month = jsDate.getMonth() + 1; // 1–12 numeric

    toAppend.push([ticker, amount, date, drip, year, month]);
  }

  if (toAppend.length === 0) {
    SpreadsheetApp.getUi().alert("No valid entries found between A2:D44.");
    return;
  }

  // Append all rows at once (much faster)
  const nextRow = sh.getLastRow() + 1;
  sh.getRange(nextRow, 1, toAppend.length, 6).setValues(toAppend);

  // Clear all input rows
  sh.getRange("A2:D44").clearContent();

  ss.toast(`${toAppend.length} dividends added successfully!`, "Batch Add", 3);
}


function analyzeHedge() {
  const ss   = SpreadsheetApp.getActive();
  const ui   = SpreadsheetApp.getUi();
  const port = ss.getSheetByName('Portfolio');
  const hist = ss.getSheetByName('History');
  if (!port || !hist) { ui.alert('Portfolio and History sheets are required.'); return; }

  // Output sheet & read settings
  const out = _ensureSheet(ss, 'HedgeAnalysis');

  const _coerceBudget = x => { if (x===''||x==null) return 0.005; let n=Number(x); if(!isFinite(n))return 0.005; if(n>1)n/=100; else if(n>0.2&&n<=1)n/=100; return n; };
  const _coerceDrop   = x => { if (x===''||x==null) return 0.10; let n=Number(x); if(!isFinite(n))return 0.10; if(n>1)n/=100; return n; };
  const _coerceInt    = (x,d)=>{ if (x===''||x==null) return d; const n=Math.round(Number(x)); return (isFinite(n)&&n>0)?n:d; };
  const _coerceWeight = x => { if (x===''||x==null) return 1.0; let n=Number(x); if(!isFinite(n))return 1.0; if(n>1)n/=100; return Math.max(0,Math.min(1,n)); };

  const settingsIn = out.getRange('H1:H4').getValues().map(r => r[0]);
  const HEDGE_BUDGET_PCT_BASE = _coerceBudget(settingsIn[0]); // fraction (e.g., 0.005 = 0.5%)
  const TARGET_PORTFOLIO_DROP = _coerceDrop  (settingsIn[1]); // fraction
  const DTE                   = _coerceInt   (settingsIn[2], 30);
  const DOWNSIDE_WEIGHT       = _coerceWeight(settingsIn[3]);

  out.clear();
  out.getRange('G1:G4').setValues([
    ['Budget % of Portfolio'],
    ['Target Portfolio Drop %'],
    ['DTE (days)'],
    ['Downside Weight']
  ]);
  out.getRange('H1').setValue(HEDGE_BUDGET_PCT_BASE).setNumberFormat('0.00%');
  out.getRange('H2').setValue(TARGET_PORTFOLIO_DROP).setNumberFormat('0.00%');
  out.getRange('H3').setValue(DTE).setNumberFormat('0');
  out.getRange('H4').setValue(DOWNSIDE_WEIGHT).setNumberFormat('0.00');

  const VIX_CELL = 'M9';
  const DELTA_WARN_ABS     = 0.05;

  // Auto-tighten knobs (used only if NOT manually locked)
  const MIN_COVERAGE_AT_TARGET = 0.30;
  const STRIKE_TIGHTEN_FACTOR  = 0.9;
  const MIN_OTM_FRACTION       = 0.02;

  // Indexes & proxies
  const INDEX_LIST    = ['SPY','QQQ','IWM','DIA'];
  const INDEX_PROXIES = { SPY:'SPLG', QQQ:'QQQM', DIA:'IYY', IWM:'VTWO' };

  // Black–Scholes assumptions (internal, simple)
  const rRf = 0.030; // risk-free (annualized)
  const DIV_YIELD_BY_TICKER = {
    'SPY': 0.014, 'QQQ': 0.006, 'IWM': 0.015, 'DIA': 0.020,
    'SPLG': 0.014, 'QQQM': 0.006, 'VTWO': 0.015, 'IYY': 0.018
  };

  const _fmtDateLocal = d => Utilities.formatDate(d, Session.getScriptTimeZone(), 'yyyy-MM-dd');

  function _parseGreeksBlob(blob) {
    const t = String(blob || '').replace(/\s+/g, ' ').trim();
    function pick(label){
      const re1 = new RegExp(label + '\\s*[:=]?\\s*([+\\-]?[0-9]*\\.?[0-9]+)%?', 'i');
      const m1  = t.match(re1); if (m1) return Number(m1[1]);
      const re2 = new RegExp(label + '([+\\-]?[0-9]*\\.?[0-9]+)%?', 'i');
      const m2  = t.match(re2); return m2 ? Number(m2[1]) : null;
    }
    return { iv: pick('IV'), delta: pick('Delta'), gamma: pick('Gamma'), theta: pick('Theta'), vega: pick('Vega') };
  }

  const needCols = { ticker: 'Ticker', shares: 'Shares Owned', price: 'Current Price' };
  const headers  = port.getRange(2,1,1,port.getLastColumn()).getValues()[0];
  const colMap   = _headerMap(headers, needCols);
  const lastRow  = port.getLastRow();
  if (lastRow <= 2) { ui.alert('No rows under headers in Portfolio.'); return; }

  const vals = port.getRange(3,1,lastRow-2,port.getLastColumn()).getValues();
  const positions = vals
    .filter(r => r[colMap.ticker - 1])
    .map(r => ({
      ticker: String(r[colMap.ticker - 1]).trim().toUpperCase(),
      shares: Number(r[colMap.shares - 1]),
      price:  Number(r[colMap.price  - 1])
    }))
    .filter(p => p.ticker && isFinite(p.shares) && p.shares>0 && isFinite(p.price) && p.price>0);

  if (!positions.length) { ui.alert('No valid positions found.'); return; }
  const portfolioValueNow = positions.reduce((s,p)=> s + p.shares*p.price, 0);

  // Read VIX
  const vix = Number(port.getRange(VIX_CELL).getValue()) || 0;

  const needIndexes = INDEX_LIST.slice();
  const proxyList   = Object.values(INDEX_PROXIES);
  const needAll     = [...new Set([...positions.map(p=>p.ticker), ...needIndexes, ...proxyList])];

  const map = {}; needAll.forEach(t => map[t]=[]);
  const h = hist.getRange(2,1,Math.max(0,hist.getLastRow()-1),3).getValues(); // [Ticker, Date, Close]
  h.forEach(([tk, dt, px]) => { if (map[tk]) map[tk].push({ d:new Date(dt), px:Number(px) }); });

  const LOOKBACK_DAYS = 120;
  const cutoff = new Date(Date.now() - LOOKBACK_DAYS*24*3600*1000);
  Object.keys(map).forEach(t => { map[t] = map[t].filter(r => r.d >= cutoff && isFinite(r.px)).sort((a,b)=>a.d-b.d); });
  if (!needAll.every(t => map[t] && map[t].length >= 30)) { ui.alert('Not enough history for some symbols. Rebuild History or increase LOOKBACK_DAYS.'); return; }

  const dateKey = d => Utilities.formatDate(d, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  const sets  = needAll.map(t => new Set(map[t].map(p=>dateKey(p.d))));
  const common= _intersectDateSets(sets);
  const dates = [...common].sort();
  if (dates.length < 30) { ui.alert('Too few overlapping dates across series.'); return; }

  const seriesFor = t => {
    const byKey = new Map(map[t].map(p=>[dateKey(p.d), p.px]));
    return dates.map(k => Number(byKey.get(k)));
  };

  const pxTickers = positions.map(p => seriesFor(p.ticker));
  const pxIndexes = needIndexes.map(t => seriesFor(t));

  const portValues = dates.map((_,i) =>
    positions.reduce((sum,p,idx)=> sum + p.shares * pxTickers[idx][i], 0)
  );

  // Fits
  const portRet = _returns(portValues);

  const fitsAll = needIndexes.map((idx, i) => {
    const [beta, r2] = _betaR2(portRet, _returns(pxIndexes[i]));
    return { index: idx, beta, r2 };
  });

  const fitsDown = needIndexes.map((idx, i) => {
    const [betaD, r2D] = _betaR2_downside(portRet, _returns(pxIndexes[i]));
    return { index: idx, betaD, r2D };
  });

  function _betaR2_downside(y, x) {
    const n = Math.min(y.length, x.length);
    const yf = [], xf = [];
    for (let i = 0; i < n; i++) { const xi=x[i], yi=y[i]; if (!isFinite(xi)||!isFinite(yi)) continue; if (xi < 0) { xf.push(xi); yf.push(yi); } }
    const m = xf.length; if (m < 5) return [0,0];
    let sx=0, sy=0, sxx=0, syy=0, sxy=0;
    for (let i=0;i<m;i++){ const xi=xf[i], yi=yf[i]; sx+=xi; sy+=yi; sxx+=xi*xi; syy+=yi*yi; sxy+=xi*yi; }
    const mx=sx/m, my=sy/m;
    const cov = sxy/m - mx*my, varx = sxx/m - mx*mx, vary = syy/m - my*my;
    const beta = varx>0 ? cov/varx : 0;
    const corr = (varx>0 && vary>0) ? cov/Math.sqrt(varx*vary) : 0;
    return [beta, corr*corr];
  }

  const merged = needIndexes.map((idx, i) => ({
    index: idx,
    beta:  fitsAll[i].beta,   r2:  fitsAll[i].r2,
    betaD: fitsDown[i].betaD, r2D: fitsDown[i].r2D
  }));

  const best = merged.slice().sort((a,b) => (b.r2D !== a.r2D) ? (b.r2D - a.r2D) : (b.r2 - a.r2))[0];
  const downsideBeta  = best.betaD || 0;
  const betaForSizing = DOWNSIDE_WEIGHT*best.betaD + (1 - DOWNSIDE_WEIGHT)*best.beta;

  // Budget
  function vixMultiplier(v) {
    if (v < 15) return 1.00;
    if (v < 20) return 0.75;
    if (v < 25) return 0.50;
    return 0.25;
  }
  const HEDGE_BUDGET_PCT_EFF = HEDGE_BUDGET_PCT_BASE * vixMultiplier(vix);
  const budget$        = HEDGE_BUDGET_PCT_EFF * portfolioValueNow;
  const budgetPerShare = budget$ / 100;
  const budgetBase$    = HEDGE_BUDGET_PCT_BASE * portfolioValueNow; // unadjusted base
  let   budgetOverrideUsed = false;
  let   manualLocked       = false; // lock when user enters price/strike

  const expDate        = _nearestFridayOffsetDays(DTE);
  const primaryIdx     = best.index;

  const primarySpot = (() => {
    const i = INDEX_LIST.indexOf(primaryIdx);
    const arr = (i>=0 ? pxIndexes[i] : null) || [];
    return arr.length ? arr[arr.length-1] : NaN;
  })();
  if (!isFinite(primarySpot)) { ui.alert('Could not resolve primary index price.'); return; }

  // Price input interpreter
  function _interpretPrice(raw) {
    let v = Number(raw);
    if (!isFinite(v) || v <= 0) return null;
    if (v >= 20 || (v > 2 && v < 20)) return v / 100; // treat as per-contract
    return v; // per-share already
  }

  // Prompt #1
  function askPerShareAndStrike(tkr, spotPx, betaDown) {
    const effBetaDown   = (betaDown && Math.abs(betaDown) > 1e-6) ? betaDown : (best.beta || 1.0);
    const idxDrop       = TARGET_PORTFOLIO_DROP / Math.max(1e-6, effBetaDown);
    const suggestedStrike = spotPx * (1 - idxDrop);

    const resp = ui.prompt(
      `Enter mid price for ${tkr} put`,
      `Current Price: ${spotPx.toFixed(2)}\n` +
      `Suggested Strike: ${suggestedStrike.toFixed(2)}\n` +
      `Expiration: ${_fmtDateLocal(expDate)}\n` +
      `Max budget per-share: ~$${budgetPerShare.toFixed(2)}\n\n` +
      `Enter price as PER-SHARE (e.g., 0.65) or PER-CONTRACT (e.g., 65).`,
      ui.ButtonSet.OK_CANCEL
    );
    if (resp.getSelectedButton() !== ui.Button.OK) return null;

    const perShare = _interpretPrice(resp.getResponseText());
    if (perShare == null) return null;

    return { perShare, strikeHint: suggestedStrike };
  }

  let chosenTicker   = primaryIdx;
  let chosenSpot     = primarySpot;
  let chosenPerShare = null;
  let chosenStrike   = primarySpot;
  let proxyUsed      = null;

  const _candidates = [];

  const primaryAns = askPerShareAndStrike(primaryIdx, primarySpot, downsideBeta);
  if (!primaryAns) { ui.alert('Cancelled.'); return; }
  chosenPerShare = primaryAns.perShare;
  chosenStrike   = primaryAns.strikeHint;
  manualLocked   = true; // lock from first input
  _candidates.push({
    label: 'Primary (your entry)',
    used: false,
    ticker: primaryIdx,
    spot: primarySpot,
    perShare: primaryAns.perShare,
    strike: primaryAns.strikeHint
  });

  // Second Prompt
  if (chosenPerShare > budgetPerShare && INDEX_PROXIES[primaryIdx]) {
    const prxTicker = INDEX_PROXIES[primaryIdx];
    const prxSpot   = (map[prxTicker] && map[prxTicker].length) ? map[prxTicker].slice(-1)[0].px : NaN;
    if (isFinite(prxSpot) && prxSpot > 0) {
      const proxyAns = askPerShareAndStrike(prxTicker, prxSpot, downsideBeta);
      if (!proxyAns) { ui.alert('Cancelled.'); return; }
      _candidates.push({
        label: 'Proxy (your entry)',
        used: false,
        ticker: prxTicker,
        spot: prxSpot,
        perShare: proxyAns.perShare,
        strike: proxyAns.strikeHint
      });
      if (proxyAns.perShare <= budgetPerShare || proxyAns.perShare < chosenPerShare) {
        chosenTicker   = prxTicker;
        chosenSpot     = prxSpot;
        chosenPerShare = proxyAns.perShare;
        chosenStrike   = proxyAns.strikeHint;
        proxyUsed      = prxTicker;
        manualLocked   = true; 
      }
    }
  }

  // THIRD PROMPT
  if (chosenPerShare > budgetPerShare) {
    const msg = ui.prompt(
      'Over budget',
      `Your budget allows up to ~$${budgetPerShare.toFixed(2)} per share (~$${budget$.toFixed(0)} per contract).\n` +
      `Enter STRIKE and MID price for ${chosenTicker} (Exp: ${_fmtDateLocal(expDate)}), comma-separated.\n` +
      `Examples: 105, 0.63   or   105, 63`,
      ui.ButtonSet.OK_CANCEL
    );
    if (msg.getSelectedButton() !== ui.Button.OK) { ui.alert('Cancelled.'); return; }

    const parts = msg.getResponseText().split(',').map(s => s.trim());
    if (parts.length < 2) { ui.alert('Please enter both strike and price.'); return; }

    const kRaw = parts[0], pRaw = parts[1];
    const k = Number(kRaw);
    const pShare = _interpretPrice(pRaw);
    if (!isFinite(k) || k <= 0 || pShare == null) { ui.alert('Invalid strike or price entered.'); return; }

    chosenStrike        = k;
    chosenPerShare      = pShare;
    budgetOverrideUsed  = true;
    manualLocked        = true;

    _candidates.push({
      label: 'Manual Override (your entry)',
      used: false,
      ticker: chosenTicker,
      spot: chosenSpot,
      perShare: pShare,
      strike: k
    });
  }

  // One-paste Greeks
  const blobResp = ui.prompt(
    'Paste Greeks',
    'Paste all five (any order), e.g.:\nIV20.31\nDelta-0.0874\nGamma0.0036\nTheta-0.0818\nVega0.3451',
    ui.ButtonSet.OK_CANCEL
  );
  if (blobResp.getSelectedButton() !== ui.Button.OK) { ui.alert('Cancelled.'); return; }
  const g = _parseGreeksBlob(blobResp.getResponseText());
  if ([g.iv, g.delta, g.gamma, g.theta, g.vega].some(v => v === null || !isFinite(v))) {
    ui.alert('Could not parse all greeks. Ensure IV, Delta, Gamma, Theta, Vega are present.');
    return;
  }
  const ivPct       = Number(g.iv);       // % (e.g., 20.31)
  const deltaRaw    = Number(g.delta);    // per share (signed)
  const chosenDelta = Math.abs(deltaRaw); // sizing uses |Δ|
  const chosenGamma = Number(g.gamma);
  const chosenTheta = Number(g.theta);
  const chosenVega  = Number(g.vega);

  // Sizing (using |Delta|)
  const ABS_DELTA  = Math.max(1e-6, chosenDelta);
  const chosenCost = chosenPerShare * 100;             // $ per contract

  const contractsTarget = Math.max(0, Math.ceil(
    (betaForSizing * TARGET_PORTFOLIO_DROP * portfolioValueNow) /
    (ABS_DELTA * chosenSpot * 100.0)
  ));
  const contractsBudget = Math.floor(budget$ / Math.max(1e-8, chosenCost));
  let   finalContracts  = budgetOverrideUsed
    ? Math.max(1, Math.floor(budgetBase$ / Math.max(1, chosenCost)))
    : Math.max(0, Math.min(contractsTarget, contractsBudget || 0));

  function _normCdf(x){ return 0.5*(1+erf(x/Math.SQRT2)); }
  function _normPdf(x){ return Math.exp(-0.5*x*x)/Math.sqrt(2*Math.PI); }
  function erf(x){ const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;
    const s=x<0?-1:1; x=Math.abs(x); const t=1/(1+p*x);
    return s*(1-((((a5*t+a4)*t+a3)*t+a2)*t+a1)*t*Math.exp(-x*x));
  }
  function bsPut(S,K,r,q,sigma,T){
    const d1=(Math.log(S/K)+(r-q+0.5*sigma*sigma)*T)/(sigma*Math.sqrt(T));
    const d2=d1 - sigma*Math.sqrt(T);
    const Nd1=_normCdf(-d1), Nd2=_normCdf(-d2), pdf=_normPdf(d1);
    const discR=Math.exp(-r*T), discQ=Math.exp(-q*T);
    const price=K*discR*Nd2 - S*discQ*Nd1;
    const delta=-discQ*Nd1;
    const gamma=discQ*pdf/(S*sigma*Math.sqrt(T));
    const vega = S*discQ*pdf*Math.sqrt(T); // per 1.00 IV
    return { price, delta, gamma, vegaPerPct: vega/100 };
  }

  const T     = Math.max(1/365, DTE/365);
  const S     = chosenSpot;
  const ivAnn = Math.max(0.0001, ivPct/100);
  const qDiv  = (DIV_YIELD_BY_TICKER[chosenTicker] || 0.000);

  const IV_SHOCK_PCT_PER_1_INDEX_DROP = 0.5; // +0.5 vol pts per 1% index drop
  function perContractRepriceGain(S, K, idxDropFrac, ivAnn, vegaShockPtsPer1pct, T, r, q, paidPerShare) {
    const S2 = S * (1 - idxDropFrac);
    const ivShockPts = Math.max(0, vegaShockPtsPer1pct * (idxDropFrac * 100)); 
    const sigma2 = Math.max(0.0001, ivAnn + ivShockPts/100);
    const price2 = bsPut(S2, K, r, q, sigma2, T).price; 

    const gainPerShare = Math.max(0, price2 - paidPerShare); 
    return gainPerShare * 100;
  }

  
  if (!manualLocked) {
    (function maybeTightenStrike(){
      let idxDropTarget = TARGET_PORTFOLIO_DROP / Math.max(1e-6, betaForSizing);
      let strike        = chosenStrike;
      let otmFrac       = Math.max(0, 1 - (strike / S));
      let steps         = 0;

      while (steps < 5) {
        const perC = perContractRepriceGain(
          S, strike, idxDropTarget, ivAnn, IV_SHOCK_PCT_PER_1_INDEX_DROP, T, rRf, qDiv, chosenPerShare
        );
        const totalOffset = perC * finalContracts;
        const loss$       = TARGET_PORTFOLIO_DROP * portfolioValueNow;
        const coverage    = loss$ > 0 ? totalOffset / loss$ : 0;

        if (coverage >= MIN_COVERAGE_AT_TARGET || otmFrac <= MIN_OTM_FRACTION) break;

        otmFrac = Math.max(MIN_OTM_FRACTION, otmFrac * STRIKE_TIGHTEN_FACTOR);
        strike  = S * (1 - otmFrac);
        steps++;
      }
      chosenStrike = strike;
    })();
  }

  // Fit table
  out.getRange(5,1,1,5).setValues([['Index','Beta','R²','Downside Beta','Downside R²']]);
  let r = 6;
  merged.slice().sort((a,b)=> (b.r2D !== a.r2D) ? (b.r2D - a.r2D) : (b.r2 - a.r2)).forEach(f => {
    out.getRange(r++,1,1,5).setValues([[f.index, f.beta, f.r2, f.betaD, f.r2D]]);
  });
  r++;

// Summary
out.getRange(r++,1,1,2).setValues([['Metric','Value']]);

const rows = [
  ['Primary Index',                  best.index],
  ['Beta',                           best.beta],
  ['Downside Beta',                  downsideBeta],
  ['R²',                             best.r2],
  ['Downside R²',                    best.r2D],
  ['Downside Weight',                DOWNSIDE_WEIGHT],
  ['Beta Used for Sizing',           betaForSizing],
  ['Proxy ETF Used',                 proxyUsed || 'None'],
  ['Chosen Hedge Ticker',            chosenTicker],
  ['Current Index Price',            chosenSpot],
  ['Portfolio Value',                portfolioValueNow],   
  ['Target Portfolio Drop',          TARGET_PORTFOLIO_DROP],
  ['Implied Index Drop (β-down)',    TARGET_PORTFOLIO_DROP/Math.max(1e-6,(downsideBeta||best.beta||1))],
  ['Final OTM % used',               1 - (chosenStrike / chosenSpot)],
  ['Strike Price (used)',            chosenStrike],
  ['Expiration Date',                Utilities.formatDate(expDate, Session.getScriptTimeZone(), 'yyyy-MM-dd')],
  ['VIX',                            vix],
  ['Premium / Contract',             chosenPerShare * 100],
  ['Budget % (Base)',                HEDGE_BUDGET_PCT_BASE],
  ['Budget % (VIX-adjusted)',        HEDGE_BUDGET_PCT_EFF],
  ['Budget $ (Base)',                budgetBase$],
  ['Budget $',                       budget$],
  ['Budget Override Used',           budgetOverrideUsed ? 'Yes' : 'No'],
  ['Manual Inputs Locked',           manualLocked ? 'Yes' : 'No'],
  ['Contracts (Target)',             contractsTarget],
  ['Contracts (Budget)',             Math.floor((budgetOverrideUsed?budgetBase$:budget$) / Math.max(1e-8, chosenPerShare*100))],
  ['Final Recommended Contracts',    finalContracts]
];

out.getRange(r,1,rows.length,2).setValues(rows);


const fmt = (rowIdx, fmtStr) => out.getRange(rowIdx,2).setNumberFormat(fmtStr);
let rr = r; // rr points to the first data row just written

fmt(rr+1,  '0.000'); // Beta
fmt(rr+2,  '0.000'); // Downside Beta
fmt(rr+3,  '0.000'); // R²
fmt(rr+4,  '0.000'); // Downside R²
fmt(rr+5,  '0.00');  // Downside Weight
fmt(rr+6,  '0.000'); // Beta Used for Sizing

fmt(rr+9,  '$#,##0.00'); // Current Index Price
fmt(rr+10, '$#,##0.00'); // Portfolio Value

fmt(rr+11, '0.00%'); // Target Portfolio Drop
fmt(rr+12, '0.00%'); // Implied Index Drop (β-down)
fmt(rr+13, '0.0%');  // Final OTM % used
fmt(rr+14, '$#,##0.00'); // Strike Price (used)
// Expiration Date is text -> no format
fmt(rr+16, '0.00');      // VIX  (fixes $15.15 -> 15.15)
fmt(rr+17, '$#,##0.00'); // Premium / Contract

fmt(rr+18, '0.00%'); // Budget % (Base)
fmt(rr+19, '0.00%'); // Budget % (VIX-adjusted)

fmt(rr+20, '$#,##0.00'); // Budget $ (Base)
fmt(rr+21, '$#,##0.00'); // Budget $

/* Rows 22–23 are Yes/No strings (no format) */

fmt(rr+24, '0'); // Contracts (Target)
fmt(rr+25, '0'); // Contracts (Budget)


r += rows.length;
r++; 

  // Greeks
  out.getRange(r++,1,1,3).setValues([['Greeks','Per Contract','Total Position']]);
  const greekRows = [
    ['IV', ivPct/100, ivPct/100],
    ['Delta', deltaRaw*100, deltaRaw*100*finalContracts],
    ['Gamma',     chosenGamma*100, chosenGamma*100*finalContracts],
    ['Theta',     chosenTheta*100, chosenTheta*100*finalContracts],
    ['Vega',      chosenVega*100,  chosenVega*100*finalContracts]
  ];
  out.getRange(r,1,greekRows.length,3).setValues(greekRows);
  out.getRange(r,2,1,2).setNumberFormat('0.00%');
  out.getRange(r+1,2,4,2).setNumberFormat('#,##0.000');
  r += greekRows.length; r++;

  out.getRange(r++,1,1,2).setValues([['Metric','Value']]);
  const totalPremium$ = finalContracts * (chosenPerShare * 100);

  const idxDropAtTarget = TARGET_PORTFOLIO_DROP / Math.max(1e-8, betaForSizing);
  const gainPerAtTarget = perContractRepriceGain(
    S, chosenStrike, idxDropAtTarget, ivAnn, IV_SHOCK_PCT_PER_1_INDEX_DROP, T, rRf, qDiv, chosenPerShare
  );
  const totalOffsetAtTarget = gainPerAtTarget * finalContracts;
  const portfolioLossAtTarget$ = TARGET_PORTFOLIO_DROP * portfolioValueNow;
  const coverageAtTarget = portfolioLossAtTarget$ > 0 ? (totalOffsetAtTarget / portfolioLossAtTarget$) : 0;

  const breakevenIdxDrop = (function _findBreakevenIdxDrop() {
    const maxScan = 0.40, step = 0.002;
    for (let d = 0; d <= maxScan; d += step) {
      const perC = perContractRepriceGain(
        S, chosenStrike, d, ivAnn, IV_SHOCK_PCT_PER_1_INDEX_DROP, T, rRf, qDiv, chosenPerShare
      );
      if (perC * finalContracts >= totalPremium$) return d;
    }
    return null;
  })();
  const breakevenPortDrop = (breakevenIdxDrop != null) ? breakevenIdxDrop * betaForSizing : null;

  const effRowsSummary = [
    ['Final Contracts Used',            finalContracts],
    ['Total Premium Spend',             totalPremium$],
    ['Spend as % of Portfolio',         totalPremium$ / portfolioValueNow],
    ['Coverage',                        coverageAtTarget],
    ['Offset',                          totalOffsetAtTarget],
    ['Cost per 1% Coverage',            coverageAtTarget>0 ? totalPremium$/(coverageAtTarget*100) : '—'],
    ['Breakeven Index Drop',            breakevenIdxDrop != null ? breakevenIdxDrop : '—'],
    ['Breakeven Portfolio Drop',        breakevenPortDrop != null ? breakevenPortDrop : '—']
  ];
  out.getRange(r,1,effRowsSummary.length,2).setValues(effRowsSummary);
  const baseR = r;
  out.getRange(baseR+0,2).setNumberFormat('0');
  out.getRange(baseR+1,2).setNumberFormat('$#,##0.00');
  out.getRange(baseR+2,2).setNumberFormat('0.00%');
  out.getRange(baseR+3,2).setNumberFormat('0.0%');
  out.getRange(baseR+4,2).setNumberFormat('$#,##0');
  if (coverageAtTarget>0) out.getRange(baseR+5,2).setNumberFormat('$#,##0');
  if (breakevenIdxDrop!=null){ out.getRange(baseR+6,2).setNumberFormat('0.0%'); out.getRange(baseR+7,2).setNumberFormat('0.0%'); }
  r += effRowsSummary.length; r++;

  // ===== Hedge effectiveness (repricer) =====
  out.getRange(r++,1,1,7).setValues([['Scenario','Port Drop %','Implied Index Drop %','New Index Price','Est. Gain / Contract','Total Offset','% of Loss Covered']]);
  const ddList = [0.01, 0.05, 0.10, 0.20];
  const effRows = ddList.map(dd => {
    const idxDrop = dd / Math.max(1e-8, betaForSizing);
    const newSpot = S * (1 - idxDrop);
    const gainPer = perContractRepriceGain(
      S, chosenStrike, idxDrop, ivAnn, IV_SHOCK_PCT_PER_1_INDEX_DROP, T, rRf, qDiv, chosenPerShare
    );
    const totalOffset = gainPer * finalContracts;
    const portfolioLoss$ = dd * portfolioValueNow;
    const coveredPct = portfolioLoss$ > 0 ? (totalOffset / portfolioLoss$) : 0;
    return [(dd*100)+'%', dd, idxDrop, newSpot, gainPer, totalOffset, coveredPct];
  });
  out.getRange(r,1,effRows.length,7).setValues(effRows);
  out.getRange(r,2,effRows.length,1).setNumberFormat('0.00%');
  out.getRange(r,3,effRows.length,1).setNumberFormat('0.00%');
  out.getRange(r,4,effRows.length,1).setNumberFormat('$#,##0.00');
  out.getRange(r,5,effRows.length,2).setNumberFormat('$#,##0');
  out.getRange(r,7,effRows.length,1).setNumberFormat('0.0%');
  r += effRows.length; r++;

  // ===== Mark the candidate we actually used (for What-if table) =====
  const usedKey = `${chosenTicker}|${chosenStrike}|${chosenPerShare.toFixed(6)}|${chosenSpot.toFixed(4)}`;
  _candidates.forEach(c => {
    const key = `${c.ticker}|${c.strike}|${(c.perShare||0).toFixed(6)}|${(c.spot||0).toFixed(4)}`;
    c.used = (key === usedKey);
  });

// ===== What-if: Skipped Choices (super minimal, spend% uses finalContracts) =====
function renderSkippedChoices(){
  try {
    if (!_candidates || !_candidates.length) return;

    const have = _candidates.filter(c =>
      c && isFinite(c.perShare) && isFinite(c.spot) && isFinite(c.strike)
    );
    if (!have.length) return;

    // Use the SAME number of contracts as the final recommended position
    const usedContracts = Math.max(0, Number(finalContracts) || 0);

    const rows = have.map(c => {
      const perContractMid = c.perShare * 100;                  // $
      const spend$         = usedContracts * perContractMid;     // $
      const spendPct       = portfolioValueNow > 0 ? (spend$ / portfolioValueNow) : 0;

      return [
        c.used ? 'Used' : 'Skipped',
        c.label,
        c.ticker,
        c.strike,
        perContractMid,
        spendPct
      ];
    });

    let r0 = out.getLastRow() + 1;

    // Header (6 columns)
    out.getRange(r0++,1,1,6).setValues([[
      'What-if','Choice','Ticker','Strike','Mid / Contract','Spend % of Port'
    ]]);

    // Body
    out.getRange(r0,1,rows.length,6).setValues(rows);

    // Formats
    out.getRange(r0,4,rows.length,1).setNumberFormat('$#,##0.00'); // Strike
    out.getRange(r0,5,rows.length,1).setNumberFormat('$#,##0.00'); // Mid/contract
    out.getRange(r0,6,rows.length,1).setNumberFormat('0.00%');     // Spend % of Port
  } catch (e) {
    SpreadsheetApp.getUi().alert('What-if table error: ' + e);
  }
}
  renderSkippedChoices();

  // ===== Warnings =====
  const warnings = [];
  if (DTE <= 45 && (1 - chosenStrike/S) > 0.20) warnings.push(`Strike is ${((1 - chosenStrike/S)*100).toFixed(1)}% OTM with ~${DTE} DTE — deep OTM; hedge may not pay in moderate drops.`);
  if (Math.abs(deltaRaw) < DELTA_WARN_ABS) warnings.push(`Delta is ${deltaRaw.toFixed(3)} — very small; required contracts may be unrealistic for moderate protection.`);
  if (coverageAtTarget < 0.30) warnings.push(`Coverage at your target drop is ${(coverageAtTarget*100).toFixed(1)}% — consider a closer strike, more DTE, or a slightly larger budget.`);
  if (breakevenPortDrop != null && breakevenPortDrop > (TARGET_PORTFOLIO_DROP*1.5)) warnings.push(`Breakeven (~${(breakevenPortDrop*100).toFixed(1)}% portfolio drop) sits far beyond your target — hedge may be too far OTM.`);

  if (warnings.length) {
    out.getRange(out.getLastRow()+1,1,1,2).setValues([['Warnings','Message']]);
    warnings.forEach(w => {
      out.getRange(out.getLastRow()+1,1,1,2).setValues([['⚠️', w]]);
    });
  }

  ui.alert('Hedge analysis complete. (What-if sized to fully cover H2.)');
}

// ===== Helpers =====
function _headerMap(headers, need){
  const map={}; 
  for (const k of Object.keys(need)){
    const want = need[k].toLowerCase();
    const i = headers.findIndex(h=>String(h).toLowerCase()===want);
    map[k] = i>=0 ? i+1 : null;
  } 
  return map;
}

function _ensureSheet(ss, name){ 
  return ss.getSheetByName(name) || ss.insertSheet(name); 
}

function _returns(arr){
  const out=[]; 
  for (let i=1;i<arr.length;i++){
    const a=Number(arr[i-1]), b=Number(arr[i]); 
    out.push((isFinite(a)&&a!==0&&isFinite(b))?(b-a)/a:0);
  } 
  return out;
}

function _betaR2(y,x){
  const n=Math.min(y.length,x.length); 
  if(n<5) return [0,0];
  let sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(let i=0;i<n;i++){
    const xi=x[i], yi=y[i]; 
    sx+=xi; sy+=yi; sxx+=xi*xi; syy+=yi*yi; sxy+=xi*yi;
  }
  const mx=sx/n,my=sy/n; 
  const cov=sxy/n-mx*my; 
  const varx=sxx/n-mx*mx; 
  const vary=syy/n-my*my;
  const beta=varx>0?cov/varx:0; 
  const corr=(varx>0&&vary>0)?cov/Math.sqrt(varx*vary):0; 
  return [beta,corr*corr];
}

function _nearestFridayOffsetDays(dte){
  const d=new Date(); 
  d.setDate(d.getDate()+dte); 
  while(d.getDay()!==5) d.setDate(d.getDate()+1); 
  return d;
}

function _intersectDateSets(sets){
  if(!sets.length) return new Set();
  let inter = new Set(sets[0]);
  for (let i=1;i<sets.length;i++){
    const s = sets[i]; 
    inter = new Set([...inter].filter(x=>s.has(x)));
  }
  return inter;
}





function _headerMap(headers, need){
  const map={}; 
  for (const k of Object.keys(need)){
    const want = need[k].toLowerCase();
    const i = headers.findIndex(h=>String(h).toLowerCase()===want);
    map[k] = i>=0 ? i+1 : null;
  } 
  return map;
}

function _ensureSheet(ss, name){ 
  return ss.getSheetByName(name) || ss.insertSheet(name); 
}

function _returns(arr){
  const out=[]; 
  for (let i=1;i<arr.length;i++){
    const a=Number(arr[i-1]), b=Number(arr[i]); 
    out.push((isFinite(a)&&a!==0&&isFinite(b))?(b-a)/a:0);
  } 
  return out;
}

function _betaR2(y,x){
  const n=Math.min(y.length,x.length); 
  if(n<5) return [0,0];
  let sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(let i=0;i<n;i++){
    const xi=x[i], yi=y[i]; 
    sx+=xi; sy+=yi; sxx+=xi*xi; syy+=yi*yi; sxy+=xi*yi;
  }
  const mx=sx/n,my=sy/n; 
  const cov=sxy/n-mx*my; 
  const varx=sxx/n-mx*mx; 
  const vary=syy/n-my*my;
  const beta=varx>0?cov/varx:0; 
  const corr=(varx>0&&vary>0)?cov/Math.sqrt(varx*vary):0; 
  return [beta,corr*corr];
}

function _nearestFridayOffsetDays(dte){
  const d=new Date(); 
  d.setDate(d.getDate()+dte); 
  while(d.getDay()!==5) d.setDate(d.getDate()+1); 
  return d;
}

function _intersectDateSets(sets){
  if(!sets.length) return new Set();
  let inter = new Set(sets[0]);
  for (let i=1;i<sets.length;i++){
    const s = sets[i]; 
    inter = new Set([...inter].filter(x=>s.has(x)));
  }
  return inter;
}

function _phi(x){ return 0.5*(1+erf(x/Math.SQRT2)); }

function erf(x){
  const sign = x>=0 ? 1 : -1;
  x = Math.abs(x);
  const a1=0.254829592, a2=-0.284496736, a3=1.421413741, a4=-1.453152027, a5=1.061405429, p=0.3275911;
  const t = 1/(1+p*x);
  const y = 1 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*Math.exp(-x*x);
  return sign*y;
}

function _blackScholesPut(S, K, T, r, sigma){
  if (T<=0 || sigma<=0) {
    return Math.max(0, K - S);
  }
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma*sqrtT);
  const d2 = d1 - sigma*sqrtT;
  const Nd1 = _phi(-d1);
  const Nd2 = _phi(-d2);
  return K*Math.exp(-r*T)*Nd2 - S*Nd1;
}

/**
 * Creates a custom menu in the Google Sheets UI for the Portfolio Optimizer.
 * Adds menu items for various portfolio optimization functions.
 * @function onOpen
 * @returns {void}
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Portfolio Optimizer')
    .addItem('Update Dividend Data', 'updateDividendDataFast')
    .addItem('History Data', 'buildHistory')
    .addItem('Deposit', 'findOptimalDividendFocusedMix')
    .addSeparator()
    .addItem('Hedge Analysis', 'analyzeHedge')
    .addToUi();
}

/**
 * Trigger function that runs when a cell is edited in the Portfolio sheet.
 * Automatically recalculates the optimal portfolio mix when cell E1 is edited.
 * @function onEditOptimizer
 * @param {Object} e - The onEdit event object containing range and sheet information.
 * @returns {void}
 */
function onEditOptimizer(e) {
  const sheet = e.range.getSheet();
  const cell = e.range;
  if (sheet.getName() === "Portfolio" && cell.getA1Notation() === "E1") {
    findOptimalDividendFocusedMix();
  }
}

/* =========================
   CONFIGURATION
   ========================= */
const DEFAULT_CONFIG = {
  CAP_PCT:         0.3,
  CAP_MODE:        'DEPOSIT-CAP', // PORTFOLIO-CAP | HYBRID
  CORE_TICKERS:    ['CLM','CRF','GOF'],
  YIELD_THRESHOLDS:[8,6,4,2,1],
  YIELD_VALUES:    [0.5,0.4,0.3,0.2,0.1],
  HEAVY_THRESHOLD: 0.10,
  CORE_RESERVE_MULTIPLIER: 1.0
};

/* =========================
   DYNAMIC COLUMN DETECTION
   - Looks at header row (Row 2)
   - Tweak patterns if your header text differs
   ========================= */
/**
 * Dynamically detects column positions based on header names in row 2.
 * This allows the sheet layout to be flexible while maintaining functionality.
 * @function detectColumns
 * @param {Sheet} sheet - The Google Sheets sheet object to analyze
 * @returns {Object} COL - Object containing column indices for each required field
 * @throws {Error} If any required column header is not found
 */
function detectColumns(sheet) {
  var lastCol = sheet.getLastColumn();
  var headers = sheet.getRange(2, 1, 1, lastCol).getValues()[0].map(function(h){
    return (h||"").toString().trim();
  });

  /**
   * Finds the first column whose header contains all substrings in any of the given patterns.
   * @param {string[][]} patterns - Array of pattern arrays, each containing required substrings
   * @param {string} requiredName - Human-readable name of the required column for error messages
   * @returns {number} Column index (1-based)
   */
  function findHeader(patterns, requiredName) {
    var idx = -1;
    for (var c = 0; c < headers.length; c++) {
      var h = headers[c].toLowerCase();
      for (var p = 0; p < patterns.length; p++) {
        var must = patterns[p];
        var ok = true;
        for (var k = 0; k < must.length; k++) {
          if (h.indexOf(must[k]) === -1) { ok = false; break; }
        }
        if (ok) { idx = c + 1; break; }
      }
      if (idx !== -1) break;
    }
    if (idx === -1) throw new Error("Missing required column header: " + requiredName + " — add it to row 2.");
    return idx;
  }

  var COL = {
    TICKER:       findHeader([["ticker"]], "Ticker"),
    PRICE:        findHeader([["price"], ["current","price"]], "Current Price"),
    COST_BASIS:   findHeader([["cost","basis"]], "Cost Basis"),
    SHARES:       findHeader([["shares"], ["qty","owned"], ["quantity"]], "Shares Owned"),
    OUT_QTY:      findHeader([["share","buy"], ["qty","buy"], ["shares","to","buy"], ["out","qty"]], "Shares to Buy"),
    TTM_DIV:      findHeader([["ttm","div"], ["dividend","ttm"], ["annual","div"]], "TTM Dividend"),
    MANUAL_BOOST: findHeader([["manual","boost"], ["manual"]], "Manual Boost"),
    EX_DATE:      findHeader([["ex","dividend","date"], ["ex","date"]], "Ex-Dividend Date"),
    MAINT_PCT:    findHeader([["maintenance"], ["maint"]], "Maintenance")
  };

  COL._LAST_COL = lastCol;
  return COL;
}

/* =========================
   FLEXIBLE DEPOSIT & MODE (Row 1)
   - Tries labeled cells, falls back to B1 (deposit) / C1 (mode)
   ========================= */
/**
 * Reads deposit amount and allocation mode from row 1 of the sheet.
 * Supports both labeled cells (with "deposit"/"mode" headers) and fallback positions.
 * @function readDepositAndMode
 * @param {Sheet} sheet - The Portfolio sheet
 * @returns {Object} Object with deposit (number) and mode (string) properties
 */
function readDepositAndMode(sheet) {
  var row1 = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var depIdx = -1, modeIdx = -1;

  for (var i = 0; i < row1.length; i++) {
    var v = (row1[i]||"").toString().toLowerCase().trim();
    if (v.indexOf("deposit") !== -1) depIdx = i;
    if (v.indexOf("mode") !== -1)     modeIdx = i;
  }

  var deposit, mode;

  // If labels are present and values are to the right of the label
  if (depIdx !== -1 && depIdx + 1 < row1.length) {
    var val = sheet.getRange(1, depIdx + 2).getValue();
    deposit = Math.max(0, parseFloat(val) || 0);
  }
  if (modeIdx !== -1 && modeIdx + 1 < row1.length) {
    var mval = sheet.getRange(1, modeIdx + 2).getValue();
    mode = ('' + mval).trim().toUpperCase();
  }

  // Fallbacks
  if (deposit == null || isNaN(deposit)) {
    deposit = Math.max(0, parseFloat(sheet.getRange('B1').getValue()) || 0);
  }
  if (!mode) {
    mode = ('' + sheet.getRange('C1').getValue()).trim().toUpperCase();
  }

  return { deposit: deposit, mode: mode };
}

/* =========================
   MAIN: Deposit Allocation
   ========================= */
/**
 * Main function that calculates and allocates optimal dividend-focused portfolio mix.
 * Reads portfolio data, applies scoring algorithm, and outputs allocation recommendations.
 * This is the primary entry point for portfolio optimization calculations.
 * @function findOptimalDividendFocusedMix
 * @returns {void}
 */
function findOptimalDividendFocusedMix() {
  const ss = SpreadsheetApp.getActive();
  const ui = SpreadsheetApp.getUi();
  const sheet = ss.getSheetByName('Portfolio');
  if (!sheet) { ui.alert('Portfolio sheet is required.'); return; }

  // Dynamic columns
  let COL;
  try {
    COL = detectColumns(sheet);
  } catch (e) {
    ui.alert("Column detection error:\n\n" + e.message);
    return;
  }

  const lastRow  = sheet.getLastRow();
  const dataRows = Math.max(0, lastRow - 2);

  const weightSheet   = ss.getSheetByName('Weights') || ss.insertSheet('Weights');
  const weightLastRow = weightSheet.getLastRow();

  // Deposit & mode (flexible)
  const dm = readDepositAndMode(sheet);
  const deposit = dm.deposit;
  const mode    = dm.mode;

  if (deposit <= 0) {
    sheet.getRange(3, COL.OUT_QTY).setValue('Invalid deposit');
    return;
  }

  // Read rows across actual width
  const lastCol = COL._LAST_COL || sheet.getLastColumn();
  const rawData = dataRows > 0 ? sheet.getRange(3, 1, dataRows, lastCol).getValues() : [];

  const CONFIG     = _loadConfig(weightSheet);
  const weightsObj = _loadWeights(weightSheet);

  Logger.log("Loaded config: " + JSON.stringify(CONFIG));
  Logger.log("Loaded weights: " + JSON.stringify(weightsObj));

  const weightMap  = new Map(Object.entries(weightsObj));
  const coreSet    = new Set(CONFIG.CORE_TICKERS);

  const { items, newRows } = _parsePortfolio(rawData, COL);
  const totalValue = items.reduce((sum, it) => sum + it.price * it.shares, 0);

  // History → histMap
  const histSheet = ss.getSheetByName('History');
  let histMap = {};
  if (histSheet && histSheet.getLastRow() > 1) {
    const histData = histSheet.getRange(2,1, histSheet.getLastRow()-1, 3).getValues();
    histMap = histData.reduce((m, [tkr, dt, close]) => {
      if (tkr && dt instanceof Date && !isNaN(close)) {
        m[tkr] = m[tkr] || [];
        m[tkr].push([dt, close]);
      }
      return m;
    }, {});
  }

  const ctx = { today: new Date(), totalValue, mode, deposit };

  // Score, allocate, write
  const scored = _scoreItems(items, weightMap, coreSet, ctx, CONFIG, histMap);
  const allocs = _allocate(deposit, scored, ctx, newRows, CONFIG);

  _writeResultsDynamic(sheet, allocs, dataRows, COL);
  _writeSummary(sheet, scored, allocs, deposit);
  _outputBoostBreakdown(weightSheet, scored, weightsObj, ctx, CONFIG, weightLastRow, histMap);
}

/* =========================
   LOADERS
   ========================= */
/**
 * Loads configuration settings from the Weights sheet.
 * Merges user settings with default configuration values.
 * @function _loadConfig
 * @param {Sheet} sheet - The Weights sheet
 * @returns {Object} Configuration object with all settings
 */
function _loadConfig(sheet) {
  const rows = sheet.getLastRow() > 0
    ? sheet.getRange(1, 1, sheet.getLastRow(), 2).getValues()
    : [];

  const config = {};
  rows.forEach(([key, val]) => {
    if (!key) return;
    const k = key.toString().trim().toUpperCase();

    if (['CORE_TICKERS','YIELD_THRESHOLDS','YIELD_VALUES'].includes(k)) {
      if (val == null || val === "") {
        config[k] = DEFAULT_CONFIG[k];
      } else {
        config[k] = val.toString()
          .split(',')
          .map(x => {
            const n = parseFloat(x);
            return isNaN(n) ? x.trim() : n;
          });
      }
    } else if (k === 'CAP_PCT') {
      config[k] = parseFloat(val) || DEFAULT_CONFIG.CAP_PCT;
    } else if (k === 'CAP_MODE') {
      config[k] = val ? val.toString().trim().toUpperCase() : DEFAULT_CONFIG.CAP_MODE;
    } else if (k === 'HEAVY_THRESHOLD') {
      config[k] = parseFloat(val);
      if (isNaN(config[k])) config[k] = DEFAULT_CONFIG.HEAVY_THRESHOLD;
    }
  });

  return Object.assign({}, DEFAULT_CONFIG, config);
}

/**
 * Loads scoring weights from the Weights sheet.
 * Maps various possible label formats to canonical weight keys.
 * @function _loadWeights
 * @param {Sheet} [sheet] - The Weights sheet (optional, defaults to 'Weights' sheet)
 * @returns {Object} Weight object with canonical keys and their numeric values
 * @throws {Error} If Weights sheet is not found
 */
function _loadWeights(sheet) {
  // Allow calling with no arg (e.g., from Run button)
  sheet = sheet || SpreadsheetApp.getActive().getSheetByName('Weights');
  if (!sheet) throw new Error('Weights sheet not found. Create a sheet named "Weights".');

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2 || lastCol < 2) return {}; // nothing to read yet

  const numRows = lastRow - 1; // rows below headers
  const rows = sheet.getRange(2, 1, numRows, 2).getValues();

  // Map many possible labels to the canonical keys used in _scoreItems
  const CANON = {
    costbase: 'costBase',
    yieldboost: 'yieldBoost',
    exboost: 'exBoost',
    costboost: 'costBoost',
    manualboost: 'manualBoost',
    modeboost: 'modeBoost',
    maintboost: 'maintBoost',
    diversificationboost: 'diversificationBoost',
    heavypenalty: 'heavyPenalty',
    momentum: 'momentum',
    volatility: 'volatility',
    sharpeyield: 'sharpeYield'
  };
  const SKIP = new Set(['CORE_TICKERS','YIELD_THRESHOLDS','YIELD_VALUES','CAP_PCT','CAP_MODE','HEAVY_THRESHOLD']);

  const weights = {};
  for (const [key, val] of rows) {
    if (!key) continue;
    const raw = String(key).trim();
    if (SKIP.has(raw.toUpperCase())) continue;

    const ck = raw.toLowerCase().replace(/[^a-z]/g, ''); // strip spaces/_/-
    const mapped = CANON[ck];
    if (!mapped) continue;

    const num = parseFloat(val);
    weights[mapped] = isNaN(num) ? 0 : num;
  }

  return weights;
}



/* =========================
   PARSING (dynamic columns)
   ========================= */
/**
 * Parses portfolio data from sheet rows into structured item objects.
 * Handles dynamic column positions and data validation.
 * @param {Array[]} data - Raw sheet data array
 * @param {Object} COL - Column mapping object
 * @returns {Object} Object with items array and newRows array
 */
function _parsePortfolio(data, COL) {
  const items = [], newRows = [];

  for (var i = 0; i < data.length; i++) {
    var r = data[i];

    var tkr     = r[COL.TICKER - 1];
    var price   = r[COL.PRICE - 1];
    var rawCost = r[COL.COST_BASIS - 1];
    var shares  = r[COL.SHARES - 1];

    var div   = r[COL.TTM_DIV - 1];
    var man   = r[COL.MANUAL_BOOST - 1];
    var exD   = r[COL.EX_DATE - 1];
    var maint = r[COL.MAINT_PCT - 1];

    const p  = _parseNum(price);
    const cb = _parseNum(rawCost);
    const s  = _parseNum(shares);
    const d  = _parseNum(div);
    const m  = _parseNum(man);
    const mt = maint != null ? _parseNum(maint) * 100 : null;

    if (!tkr || p <= 0) continue;

    const rowIdx = 3 + i;
    if (!rawCost || isNaN(cb) || s <= 0) newRows.push(rowIdx);

    const loss = p > 0 ? (p - (isNaN(cb) ? p : cb)) / p : 0;

    let exDate = null;
    if (exD instanceof Date) {
      exDate = exD;
    } else if (typeof exD === 'number' && !isNaN(exD)) {
      const dt = new Date(); dt.setDate(dt.getDate() + exD); exDate = dt;
    } else if (typeof exD === 'string' && exD.trim()) {
      const t = Date.parse(exD); if (!isNaN(t)) exDate = new Date(t);
    }

    items.push({
      ticker:    tkr + '',
      price:     p,
      costBasis: isNaN(cb) ? p : cb,
      shares:    s || 0,
      div:       d,
      manual:    m,
      exDate,
      maint:     mt,
      loss,
      row:       rowIdx
    });
  }

  return { items, newRows };
}

/* =========================
   ALLOCATION (unchanged logic)
   ========================= */
/**
 * Allocates deposit amount across portfolio items based on scoring and constraints.
 * Implements complex allocation logic with caps, core reserves, and proportional distribution.
 * @function _allocate
 * @param {number} deposit - Total amount to allocate
 * @param {Array} scored - Array of scored portfolio items
 * @param {Object} ctx - Context object with mode, totalValue, etc.
 * @param {Array} newRows - Array of row indices for new positions
 * @param {Object} CONFIG - Configuration object with caps and thresholds
 * @returns {Object} Allocation object mapping row numbers to {qty, cost} objects
 */
function _allocate(deposit, scored, ctx, newRows, CONFIG) {
  const { mode, totalValue } = ctx;
  const capPct = CONFIG.CAP_PCT;

  const perTickerNewSpendCapBase = capPct * deposit;

  const modeCaps = (() => {
    const m = (CONFIG.CAP_MODE || '').toUpperCase();
    return {
      useDepositCap:   m === 'DEPOSIT-CAP' || m === 'HYBRID',
      usePortfolioCap: m === 'PORTFOLIO-CAP' || m === 'HYBRID'
    };
  })();

  const alloc   = {};
  let remaining = deposit;

  const getExistingValue = (it) => it.price * it.shares;
  const getNewCost       = (row) => (alloc[row]?.cost || 0);
  const spentSoFar       = () => deposit - remaining;

  const canBuyOne = (it) => {
    const price    = it.price;
    if (price > remaining) return false;

    const existing = getExistingValue(it);
    const currNew  = getNewCost(it.row);

    const passDepositCap = !modeCaps.useDepositCap
      || (currNew + price) <= perTickerNewSpendCapBase;

    const afterPortfolioValue  = totalValue + spentSoFar() + price;
    const perTickerTotalCapNow = capPct * afterPortfolioValue;

    const passPortfolioCap = !modeCaps.usePortfolioCap
      || (existing + currNew + price) <= perTickerTotalCapNow;

    return passDepositCap && passPortfolioCap;
  };

  const maxSharesByCaps = (it) => {
    const price    = it.price;
    const existing = getExistingValue(it);
    const currNew  = getNewCost(it.row);

    const roomNewSpend = modeCaps.useDepositCap
      ? Math.max(0, perTickerNewSpendCapBase - currNew)
      : Infinity;
    const byNewSpend = Math.floor(roomNewSpend / price);

    const perTickerTotalCapNow = capPct * (totalValue + spentSoFar());
    const roomTotalPos = modeCaps.usePortfolioCap
      ? Math.max(0, perTickerTotalCapNow - (existing + currNew))
      : Infinity;
    const byTotalPos = Math.floor(roomTotalPos / price);

    const byCash = Math.floor(remaining / price);

    const capLimited = Math.min(byNewSpend, byTotalPos);
    return Math.max(0, Math.min(capLimited, byCash));
  };

  /* =========
     1) CORE seed (unchanged): give CORE mode one “best core” share if possible
     ========= */
  if (mode === 'CORE') {
    const coreItems = scored
      .filter(it => CONFIG.CORE_TICKERS.includes(it.ticker))
      .sort((a, b) => b.score - a.score);

    const bestCore = coreItems.find(it => canBuyOne(it));
    if (bestCore) {
      alloc[bestCore.row] = { qty: 1, cost: bestCore.price };
      remaining -= bestCore.price;
    }
  }

  /* =========
     2) CORE pre-allocation FIRST, using CAP_PCT reserve (budget-aware)
        - Reserves deposit * CAP_PCT * CORE_RESERVE_MULTIPLIER
        - Per-core budgets to allow multiple shares per core up to caps
     ========= */
  {
    const coreTickers = CONFIG.CORE_TICKERS || [];
    if (coreTickers.length > 0) {
      const reserveTarget = deposit * (CONFIG.CAP_PCT || 0) * (CONFIG.CORE_RESERVE_MULTIPLIER || 1);
      let reserve = Math.max(0, Math.min(remaining, reserveTarget));

      if (reserve > 0) {
        // Per-core dollar budget so each core gets a fair slice
        const perCoreBudget = reserve / coreTickers.length;

        // Phase 1: fill each core up to its per-core budget (multi-share allowed)
        let progressed = true;
        while (progressed) {
          progressed = false;
          for (const it of scored) {
            if (!coreTickers.includes(it.ticker)) continue;
            if (reserve <= 0 || remaining <= 0) break;

            if (!canBuyOne(it)) continue;
            const maxByCaps = maxSharesByCaps(it);
            if (maxByCaps <= 0) continue;

            // Dollars already allocated to this row in this run
            const spentOnThis = (alloc[it.row]?.cost || 0);
            const roomDollars = Math.max(0, perCoreBudget - spentOnThis);
            if (roomDollars < it.price) continue; // not enough for 1 more share

            const kByBudget  = Math.floor(roomDollars / it.price);
            const kByCash    = Math.floor(remaining / it.price);
            const k          = Math.min(kByBudget, maxByCaps, kByCash);
            if (k <= 0) continue;

            const spend = k * it.price;
            const curr  = alloc[it.row] || { qty: 0, cost: 0 };
            alloc[it.row] = { qty: curr.qty + k, cost: curr.cost + spend };

            remaining -= spend;
            reserve   -= spend;
            progressed = true;
          }
        }

        // Phase 2: use any leftover reserve in round-robin (1 share at a time)
        let progressed2 = true;
        while (progressed2 && reserve > 0 && remaining > 0) {
          progressed2 = false;
          for (const it of scored) {
            if (!coreTickers.includes(it.ticker)) continue;
            if (reserve <= 0 || remaining <= 0) break;

            if (!canBuyOne(it)) continue;
            const maxByCaps = maxSharesByCaps(it);
            if (maxByCaps <= 0) continue;

            const k = Math.min(1, maxByCaps, Math.floor(reserve / it.price));
            if (k <= 0) continue;

            const spend = k * it.price;
            const curr  = alloc[it.row] || { qty: 0, cost: 0 };
            alloc[it.row] = { qty: curr.qty + k, cost: curr.cost + spend };

            remaining -= spend;
            reserve   -= spend;
            progressed2 = true;
          }
        }
      }
    }
  }

  /* =========
     3) Early general loop (seed new names / add to existing) — SKIP CORES here
     ========= */
  for (const it of scored) {
    if (CONFIG.CORE_TICKERS.includes(it.ticker)) continue; // cores already handled

    if (it.shares <= 0 && canBuyOne(it)) {
      const curr = alloc[it.row] || { qty: 0, cost: 0 };
      if (curr.qty === 0) {
        alloc[it.row] = { qty: 1, cost: it.price };
        remaining -= it.price;
      }
    } else if (it.shares > 0) {
      const k = maxSharesByCaps(it);
      if (k > 0) {
        const spend = k * it.price;
        const curr  = alloc[it.row] || { qty: 0, cost: 0 };
        alloc[it.row] = { qty: curr.qty + k, cost: curr.cost + spend };
        remaining -= spend;
      }
    }
  }

  /* =========
     4) Main proportional pass
     ========= */
  if (mode === 'CORE' && newRows.length) {
    let added = true;
    const coreItems = scored.filter(it => CONFIG.CORE_TICKERS.includes(it.ticker));
    while (added) {
      added = false;
      for (const it of coreItems) {
        if (canBuyOne(it)) {
          const curr = alloc[it.row] || { qty: 0, cost: 0 };
          alloc[it.row] = { qty: curr.qty + 1, cost: curr.cost + it.price };
          remaining -= it.price;
          added = true;
        }
      }
    }
  } else {
    let sumScores = scored.reduce((s, it) => s + it.score, 0);
    if (sumScores === 0) {
      scored.forEach(it => it.score = 1);
      sumScores = scored.length;
    }

    for (const it of scored) {
      const rawSpend  = (it.score / sumScores) * remaining;
      const targetQty = Math.floor(rawSpend / it.price);
      if (targetQty <= 0) continue;

      let qty = Math.min(targetQty, maxSharesByCaps(it));
      if (qty > 0) {
        const spend = qty * it.price;
        const curr  = alloc[it.row] || { qty: 0, cost: 0 };
        alloc[it.row] = { qty: curr.qty + qty, cost: curr.cost + spend };
        remaining -= spend;
      }
    }
  }

  /* =========
     5) Greedy mop-up: keep buying 1 share wherever caps allow
     ========= */
  let keepBuying = true;
  while (keepBuying) {
    keepBuying = false;
    for (const it of scored) {
      if (canBuyOne(it)) {
        const curr = alloc[it.row] || { qty: 0, cost: 0 };
        alloc[it.row] = { qty: curr.qty + 1, cost: curr.cost + it.price };
        remaining -= it.price;
        keepBuying = true;
        break;
      }
    }
  }

  return alloc;
}

/* =========================
   SCORING
   ========================= */
/**
 * Scores portfolio items based on multiple weighted factors.
 * Normalizes scores and applies weights to create final ranking.
 * @function _scoreItems
 * @param {Array} items - Array of portfolio items
 * @param {Map} weightMap - Weight configuration map
 * @param {Set} coreSet - Set of core ticker symbols
 * @param {Object} ctx - Context object with mode and totalValue
 * @param {Object} CONFIG - Configuration object
 * @param {Object} histMap - Historical price data map
 * @returns {Array} Sorted array of scored items
 */
function _scoreItems(items, weightMap, coreSet, ctx, CONFIG, histMap) {
  const w = Object.fromEntries([...weightMap]);

  const rawKeys = [
    'costBase','yieldBoost','exBoost','costBoost',
    'manualBoost','modeBoost','maintBoost',
    'diversificationBoost','heavyPenalty',
    'momentum','volatility','sharpeYield'
  ];

  const noNormKeys = [
    'exBoost','maintBoost','manualBoost','modeBoost','heavyPenalty'
  ];

  const raws = items.map(item => {
    const cbRaw   = _calcCostBase(item);
    const yRaw    = _calcYield(item, CONFIG);
    const exRaw   = _calcEx(item, ctx.today);
    const cRaw    = _calcCost(item);
    const mRaw    = item.manual;
    const modeRaw = coreSet.has(item.ticker) ? (ctx.mode === 'CORE' ? 1 : 0) : 0;
    const mtRaw   = _calcMaint(item);
    const divRaw  = _calcDiversification(item, ctx);
    const hRaw    = _calcHeavy(item, ctx, coreSet, CONFIG);
    const moRaw   = _calcMomentum(item, histMap);
    const volRaw  = _calcVolatility(item, histMap);
    const syRaw   = _calcSharpeYield(item, CONFIG, histMap);

    return { item, raw: [cbRaw, yRaw, exRaw, cRaw, mRaw, modeRaw, mtRaw, divRaw, hRaw, moRaw, volRaw, syRaw] };
  });

  const mins = Array(rawKeys.length).fill(Infinity);
  const maxs = Array(rawKeys.length).fill(-Infinity);
  raws.forEach(r => r.raw.forEach((v, i) => {
    if (typeof v === 'number') {
      mins[i] = Math.min(mins[i], v);
      maxs[i] = Math.max(maxs[i], v);
    }
  }));

  const scored = raws.map(r => {
    const wts = r.raw.map((v, i) => {
      const key = rawKeys[i];
      if (noNormKeys.includes(key)) {
        return v * (w[key] || 0);
      } else {
        const norm = maxs[i] > mins[i] ? (v - mins[i]) / (maxs[i] - mins[i]) : 0;
        return norm * (w[key] || 0);
      }
    });
    const rawScore = wts.reduce((sum, x) => sum + x, 0);
    return Object.assign({}, r.item, { rawScore });
  });

  const rawScores = scored.map(it => it.rawScore);
  const minScore  = Math.min(...rawScores);
  const maxScore  = Math.max(...rawScores);

  const finalScored = scored.map(it => {
    const normScore = (maxScore > minScore) ? (it.rawScore - minScore) / (maxScore - minScore) : 0;
    return Object.assign({}, it, { score: normScore });
  });

  return finalScored.sort((a, b) => b.score - a.score);
}

/* =========================
   SCORE COMPONENTS & HELPERS
   ========================= */
/**
 * Calculates momentum score based on short-term vs long-term moving averages.
 * @function _calcMomentum
 * @param {Object} item - Portfolio item with ticker
 * @param {Object} histMap - Historical price data map
 * @returns {number} Momentum boost value between -0.5 and 0.5
 */
function _calcMomentum(item, histMap) {
  const hist = (histMap[item.ticker] || []).sort((a, b) => a[0] - b[0]);
  if (hist.length < 2) return 0;
  const closes = hist.map(x => x[1]);
  const shortLen = Math.min(5, hist.length);
  const longLen  = Math.min(20, hist.length);
  const shortMA = avg(closes.slice(-shortLen));
  const longMA  = avg(closes.slice(-longLen));
  const diff = shortMA - longMA;
  let boost = 0;
  if (longMA > 0) {
    boost = (diff / longMA) * 5;
    boost = Math.max(-0.5, Math.min(0.5, boost));
  }
  return boost;
}

/**
 * Calculates the average of an array of numbers.
 * @function avg
 * @param {number[]} arr - Array of numbers
 * @returns {number} Average value
 */
function avg(arr) { return arr.reduce((a, b) => a + b, 0) / arr.length; }

/**
 * Calculates annualized volatility based on historical price data.
 * @function _calcVolatility
 * @param {Object} item - Portfolio item with ticker
 * @param {Object} histMap - Historical price data map
 * @returns {number} Annualized volatility (standard deviation)
 */
function _calcVolatility(item, histMap) {
  const hist = (histMap[item.ticker] || []).sort((a, b) => a[0] - b[0]).map(r => r[1]);
  if (hist.length < 2) return 0;
  const closes = hist.slice(-30);
  if (closes.length < 2) return 0;
  const rets = closes.slice(1).map((p, i) => (p - closes[i]) / closes[i]);
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const varr = rets.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / rets.length;
  const dailyStd = Math.sqrt(varr);
  return dailyStd * Math.sqrt(252);
}

function _calcSharpeYield(item, CONFIG, histMap) {
  const rf     = 0.01;
  const yieldP = item.div / item.price;
  const vol    = _calcVolatility(item, histMap);
  return vol > 0 ? (yieldP - rf) / vol : 0;
}

/**
 * Parses a value to a number, with optional default.
 * @function _parseNum
 * @param {*} v - Value to parse
 * @param {number} [def=0] - Default value if parsing fails
 * @returns {number} Parsed number or default
 */
function _parseNum(v, def = 0) {
  const n = (typeof v === 'number') ? v : parseFloat((v||'').toString().replace(/[^0-9.\-]/g,''));
  return isNaN(n) ? def : n;
}

/**
 * Calculates cost basis boost (1 if loss, 0 if gain).
 * @function _calcCostBase
 * @param {Object} i - Portfolio item with loss property
 * @returns {number} Cost basis boost (0 or 1)
 */
function _calcCostBase(i) { return i.loss < 0 ? 1 : 0; }

/**
 * Calculates yield boost based on dividend yield thresholds.
 * @function _calcYield
 * @param {Object} item - Portfolio item with div and price
 * @param {Object} C - Configuration object with thresholds and values
 * @returns {number} Yield boost value
 */
function _calcYield({div,price}, C) {
  const pct = div/price*100;
  for (let i = 0; i < C.YIELD_THRESHOLDS.length; i++) {
    if (pct >= C.YIELD_THRESHOLDS[i]) return C.YIELD_VALUES[i];
  }
  return 0;
}

/**
 * Calculates ex-dividend date boost based on days until ex-date.
 * @function _calcEx
 * @param {Object} i - Portfolio item with exDate
 * @param {Date} today - Current date
 * @returns {number} Ex-dividend boost (0-1 scale)
 */
function _calcEx(i, today) {
  if (!i.exDate) return 0;
  if (today >= i.exDate) return 0;
  const daysUntilEx = ((i.exDate - today) / 86400000) - 1;
  return Math.max(0, (28 - daysUntilEx) / 70);
}

/**
 * Calculates cost boost based on dividend efficiency.
 * @function _calcCost
 * @param {Object} item - Portfolio item with div, price, costBasis
 * @returns {number} Cost boost (0 or 0.5)
 */
function _calcCost({div,price,costBasis}) {
  const m = div / 12;
  return m/price > m/costBasis ? 0.5 : 0;
}

/**
 * Calculates maintenance boost/penalty based on maintenance percentage.
 * @function _calcMaint
 * @param {Object} i - Portfolio item with maint property
 * @returns {number} Maintenance boost (-0.5 to 0.5)
 */
function _calcMaint(i) {
  if (i.maint == null) return 0;
  const maint = i.maint;
  if (maint <= 30) return 0.5;
  if (maint >= 100) return -0.5;
  const boost = (-1 / 70) * (maint - 30) + 0.5;
  return boost;
}

/**
 * Calculates diversification boost for under-allocated positions.
 * @function _calcDiversification
 * @param {Object} item - Portfolio item with price and shares
 * @param {Object} ctx - Context with totalValue
 * @returns {number} Diversification boost (0-1 scale)
 */
function _calcDiversification({ price, shares }, { totalValue }) {
  const pct = (price * shares) / totalValue;
  const target = 0.05;
  if (pct >= target) return 0;
  return (target - pct) / target;
}

/**
 * Calculates heavy position penalty for over-allocated non-core positions.
 * @function _calcHeavy
 * @param {Object} item - Portfolio item with price, shares, ticker
 * @param {Object} ctx - Context with totalValue
 * @param {Set} coreSet - Set of core ticker symbols
 * @param {Object} CONFIG - Configuration with heavy threshold
 * @returns {number} Heavy penalty (0-1 scale)
 */
function _calcHeavy(item, { totalValue }, coreSet, CONFIG) {
  if (coreSet.has(item.ticker)) return 0;
  const pct       = (item.price * item.shares) / totalValue;
  const threshold = CONFIG.HEAVY_THRESHOLD;
  if (pct <= threshold) return 0;
  return (pct - threshold) / (1 - threshold);
}

/* =========================
   WRITE RESULTS (dynamic)
   ========================= */
/**
 * Writes allocation results back to the Portfolio sheet.
 * Handles dynamic column positions and clears previous results.
 * @function _writeResultsDynamic
 * @param {Sheet} sheet - The Portfolio sheet
 * @param {Object} alloc - Allocation object mapping rows to {qty, cost}
 * @param {number} numRows - Number of data rows
 * @param {Object} COL - Column mapping object
 */
function _writeResultsDynamic(sheet, alloc, numRows, COL) {
  var qtyCol  = new Array(numRows);
  var costCol = new Array(numRows);

  for (var i = 0; i < numRows; i++) {
    var row = 3 + i;
    var a   = alloc[row] || { qty: 0, cost: 0 };

    // if qty <= 0 → blank, else write the number
    qtyCol[i]  = [a.qty > 0 ? a.qty : ""];

    // keep cost aligned with qty logic (optional)
    costCol[i] = [a.qty > 0 ? a.cost : ""];
  }

  // Write Qty (always exists)
  sheet.getRange(3, COL.OUT_QTY, numRows, 1).clearContent().setValues(qtyCol);

  // Write Cost only if column exists
  if (COL.OUT_COST && COL.OUT_COST > 0) {
    sheet.getRange(3, COL.OUT_COST, numRows, 1).clearContent().setValues(costCol);
  }
}

/* =========================
   SUMMARY
   ========================= */
function _writeSummary(sheet, scored, alloc, deposit) {
  let reqCap = 0, estInc = 0;
  scored.forEach(it => {
    const a = alloc[it.row] || { qty: 0, cost: 0 };
    reqCap += a.cost;
    estInc += a.qty * it.div;
  });
  //const unused = deposit - reqCap;
  //sheet.getRange('G3').setValue(`$${unused.toFixed(2)}`);
  //sheet.getRange('I1').setValue(`Required Capital: $${reqCap.toFixed(2)}`);
  //sheet.getRange('K1').setValue(`Est Annual Income: $${estInc.toFixed(2)}`);
  //sheet.getRange('F1').setValue(`Est. Monthly Income: $${(estInc/12).toFixed(2)}`);
}

/* =========================
   BOOST BREAKDOWN
   ========================= */
/**
 * Outputs detailed boost breakdown for debugging and analysis.
 * Shows individual component scores for each portfolio item.
 * @function _outputBoostBreakdown
 * @param {Sheet} sheet - The Weights sheet for output
 * @param {Array} scored - Array of scored portfolio items
 * @param {Object} weights - Weight configuration object
 * @param {Object} ctx - Context object
 * @param {Object} CONFIG - Configuration object
 * @param {number} lastRow - Last row of existing data
 * @param {Object} histMap - Historical price data map
 */
function _outputBoostBreakdown(sheet, scored, weights, ctx, CONFIG, lastRow, histMap) {
  const coreSet = new Set(CONFIG.CORE_TICKERS);
  if (lastRow >= 20) {
    sheet.getRange(`A20:N${lastRow}`).clearContent();
  }

  const rawKeys = [
    'costBase','yieldBoost','exBoost','costBoost',
    'manualBoost','modeBoost','maintBoost',
    'diversificationBoost','heavyPenalty',
    'momentum','volatility','sharpeYield'
  ];

  const headers = [
    'Ticket','Score',
    'CostBase','YieldBoost','exBoost','CostBoost',
    'ManualBoost','ModeBoost','MaintBoost',
    'DiversificationBoost','HeavyPenalty',
    'Momentum','Volatility','SharpeYield'
  ];
  sheet.getRange(20, 1, 1, headers.length).setValues([headers]);

  const raws = scored.map(item => ({
    ticker: item.ticker,
    raw: rawKeys.map(k => {
      switch (k) {
        case 'costBase':             return _calcCostBase(item);
        case 'yieldBoost':           return _calcYield(item, CONFIG);
        case 'exBoost':              return _calcEx(item, ctx.today);
        case 'costBoost':            return _calcCost(item);
        case 'manualBoost':          return item.manual;
        case 'modeBoost':            return CONFIG.CORE_TICKERS.includes(item.ticker) ? (ctx.mode === 'CORE' ? 1 : 0) : 0;
        case 'maintBoost':           return _calcMaint(item);
        case 'diversificationBoost': return _calcDiversification(item, ctx);
        case 'heavyPenalty':         return _calcHeavy(item, ctx, coreSet, CONFIG);
        case 'momentum':             return _calcMomentum(item, histMap);
        case 'volatility':           return _calcVolatility(item, histMap);
        case 'sharpeYield':          return _calcSharpeYield(item, CONFIG, histMap);
      }
    })
  }));

  const mins = Array(rawKeys.length).fill(Infinity);
  const maxs = Array(rawKeys.length).fill(-Infinity);
  raws.forEach(r => r.raw.forEach((v, i) => {
    mins[i] = Math.min(mins[i], v);
    maxs[i] = Math.max(maxs[i], v);
  }));

  const noNormKeys = ['exBoost','maintBoost','manualBoost','modeBoost','heavyPenalty'];

  const rows = raws.map(r => {
    const wts = r.raw.map((v, i) => {
      const key = rawKeys[i];
      if (noNormKeys.includes(key)) {
        return v * (weights[key] || 0);
      } else {
        const norm = maxs[i] > mins[i] ? (v - mins[i]) / (maxs[i] - mins[i]) : 0;
        return norm * (weights[key] || 0);
      }
    });
    const score = wts.reduce((a, b) => a + b, 0);
    return [r.ticker, score, ...wts];
  });

  if (rows.length > 0) {
    sheet.getRange(21, 1, rows.length, headers.length).setValues(rows);
  }
}


/**
 * Debug function to log loaded weights for troubleshooting.
 * Useful for verifying weight loading and mapping.
 * @function debugLoadWeights
 * @returns {void}
 */
function debugLoadWeights() {
  const ss = SpreadsheetApp.getActive();
  const ws = ss.getSheetByName('Weights');
  const w  = _loadWeights(ws);
  Logger.log(JSON.stringify(w, null, 2));
}

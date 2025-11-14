function onEditHistory(e) {
  const sheet = e.range.getSheet();
  const cell = e.range;
  if (sheet.getName() === "Portfolio" && cell.getA1Notation() === "O1") {
    buildHistory();
  }
}


function buildHistory() {
  const ss   = SpreadsheetApp.getActive();
  const port = ss.getSheetByName('Portfolio');
  if (!port) throw new Error('Cannot find a sheet named "Portfolio".');

  // --- 1) Grab tickers from Portfolio A3:A
  const tickersRaw = port.getRange('A3:A').getValues().flat();
  const tickers = tickersRaw
    .filter(t => t && typeof t === 'string')
    .map(t => t.trim());

  if (tickers.length === 0) {
    SpreadsheetApp.getUi().alert('No tickers found in Portfolio! A3:A');
    return;
  }

  // --- 2) Add hedge index tickers (hardcoded) if not already present
  const hedgeIndexes = ['SPY','QQQ','IWM','DIA','SPLG','QQQM','IYY','VTWO'];
  const existing = new Set(tickers.map(t => t.toUpperCase()));
  hedgeIndexes.forEach(t => { if (!existing.has(t.toUpperCase())) tickers.push(t); });

  // --- 3) Prepare History sheet
  let hist = ss.getSheetByName('History');
  if (!hist) hist = ss.insertSheet('History');
  hist.clearContents();
  hist.appendRow(['Ticker','Date','Close']);

  // --- 4) Temp helper sheet for GOOGLEFINANCE pulls
  let tmp = ss.getSheetByName('__tmpFinance__');
  if (!tmp) tmp = ss.insertSheet('__tmpFinance__');

  // --- 5) Fetch 1 year of daily closes for each ticker
  tickers.forEach(tkr => {
    tmp.clear();
    tmp.getRange(1,1).setFormula(
      `=GOOGLEFINANCE("${tkr}","close",TODAY()-365,TODAY(),"DAILY")`
    );
    SpreadsheetApp.flush();

    const all  = tmp.getDataRange().getValues(); // [Date, Close]
    const body = all.slice(1).filter(r => r[0] instanceof Date && isFinite(r[1]));

    if (body.length) {
      const toWrite = body.map(r => [tkr, r[0], r[1]]);
      hist.getRange(hist.getLastRow()+1, 1, toWrite.length, 3).setValues(toWrite);
      Logger.log(`Ticker ${tkr}: saved ${toWrite.length} rows of history.`);
    }
  });

  // --- 6) Clean up
  ss.deleteSheet(tmp);
}
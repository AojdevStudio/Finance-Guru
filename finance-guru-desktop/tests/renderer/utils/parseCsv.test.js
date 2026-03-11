const { describe, test, expect } = require('bun:test');
const { parseCsv } = require('../../../src/renderer/utils/parseCsv');

describe('parseCsv', () => {
  test('parses simple comma-separated rows correctly', () => {
    const csv = 'name,age,city\nAlice,30,NYC\nBob,25,LA';
    const rows = parseCsv(csv);

    expect(rows.length).toBe(2);
    expect(rows[0]).toEqual({ name: 'Alice', age: '30', city: 'NYC' });
    expect(rows[1]).toEqual({ name: 'Bob', age: '25', city: 'LA' });
  });

  test('handles quoted commas inside cells', () => {
    const csv = 'symbol,description,price\nSPY,"S&P 500, ETF",450.00\nQQQ,"Nasdaq 100, Tech",380.00';
    const rows = parseCsv(csv);

    expect(rows.length).toBe(2);
    expect(rows[0].description).toBe('S&P 500, ETF');
    expect(rows[1].description).toBe('Nasdaq 100, Tech');
  });

  test('preserves empty trailing fields', () => {
    const csv = 'a,b,c\n1,2,\n4,,6';
    const rows = parseCsv(csv);

    expect(rows.length).toBe(2);
    expect(rows[0].c).toBe('');
    expect(rows[1].b).toBe('');
    expect(rows[1].c).toBe('6');
  });

  test('handles escaped quotes (doubled "") inside quoted fields', () => {
    const csv = 'name,note\nFoo,"He said ""hello"""\nBar,"normal"';
    const rows = parseCsv(csv);

    expect(rows.length).toBe(2);
    expect(rows[0].note).toBe('He said "hello"');
    expect(rows[1].note).toBe('normal');
  });

  test('returns empty array when input has fewer than 2 lines', () => {
    expect(parseCsv('')).toEqual([]);
    expect(parseCsv('header only')).toEqual([]);
  });

  test('skips blank lines in the body', () => {
    const csv = 'x,y\n1,2\n\n3,4\n';
    const rows = parseCsv(csv);

    expect(rows.length).toBe(2);
    expect(rows[0]).toEqual({ x: '1', y: '2' });
    expect(rows[1]).toEqual({ x: '3', y: '4' });
  });

  test('trims header whitespace', () => {
    const csv = ' ticker , price \nSPY,450';
    const rows = parseCsv(csv);

    expect(rows[0].ticker).toBe('SPY');
    expect(rows[0].price).toBe('450');
  });
});

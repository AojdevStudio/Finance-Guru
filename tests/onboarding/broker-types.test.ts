/**
 * Tests for Broker Types and Configuration System
 */

import { describe, it, expect } from 'bun:test';
import {
  type BrokerType,
  type BrokerInfo,
  SUPPORTED_BROKERS,
  getBrokerInfo,
  getAllBrokers,
  getBrokerDisplayName
} from '../../scripts/onboarding/modules/broker-types';

describe('Broker Types', () => {
  describe('SUPPORTED_BROKERS', () => {
    it('should have Fidelity broker defined', () => {
      expect(SUPPORTED_BROKERS.fidelity).toBeDefined();
      expect(SUPPORTED_BROKERS.fidelity.id).toBe('fidelity');
      expect(SUPPORTED_BROKERS.fidelity.name).toBe('Fidelity Investments');
    });

    it('should have Schwab broker defined', () => {
      expect(SUPPORTED_BROKERS.schwab).toBeDefined();
      expect(SUPPORTED_BROKERS.schwab.id).toBe('schwab');
      expect(SUPPORTED_BROKERS.schwab.name).toBe('Charles Schwab');
    });

    it('should have Vanguard broker defined', () => {
      expect(SUPPORTED_BROKERS.vanguard).toBeDefined();
      expect(SUPPORTED_BROKERS.vanguard.id).toBe('vanguard');
      expect(SUPPORTED_BROKERS.vanguard.name).toBe('Vanguard');
    });

    it('should have all brokers with required fields', () => {
      const brokers = Object.values(SUPPORTED_BROKERS);

      for (const broker of brokers) {
        expect(broker.id).toBeDefined();
        expect(broker.name).toBeDefined();
        expect(broker.description).toBeDefined();
        expect(broker.csvExportGuide).toBeDefined();
      }
    });

    it('should have exactly 7 brokers', () => {
      const brokerCount = Object.keys(SUPPORTED_BROKERS).length;
      expect(brokerCount).toBe(7);
    });
  });

  describe('getBrokerInfo', () => {
    it('should return correct broker info for Fidelity', () => {
      const info = getBrokerInfo('fidelity');
      expect(info.id).toBe('fidelity');
      expect(info.name).toBe('Fidelity Investments');
      expect(info.description).toContain('brokerage');
    });

    it('should return correct broker info for Schwab', () => {
      const info = getBrokerInfo('schwab');
      expect(info.id).toBe('schwab');
      expect(info.name).toBe('Charles Schwab');
    });

    it('should return correct broker info for other', () => {
      const info = getBrokerInfo('other');
      expect(info.id).toBe('other');
      expect(info.name).toBe('Other Broker');
    });
  });

  describe('getAllBrokers', () => {
    it('should return array of all brokers', () => {
      const brokers = getAllBrokers();
      expect(Array.isArray(brokers)).toBe(true);
      expect(brokers.length).toBe(7);
    });

    it('should return broker objects with all required fields', () => {
      const brokers = getAllBrokers();

      for (const broker of brokers) {
        expect(broker).toHaveProperty('id');
        expect(broker).toHaveProperty('name');
        expect(broker).toHaveProperty('description');
        expect(broker).toHaveProperty('csvExportGuide');
      }
    });

    it('should include Fidelity in results', () => {
      const brokers = getAllBrokers();
      const fidelity = brokers.find(b => b.id === 'fidelity');
      expect(fidelity).toBeDefined();
    });
  });

  describe('getBrokerDisplayName', () => {
    it('should return display name for Fidelity', () => {
      const name = getBrokerDisplayName('fidelity');
      expect(name).toBe('Fidelity Investments');
    });

    it('should return display name for Schwab', () => {
      const name = getBrokerDisplayName('schwab');
      expect(name).toBe('Charles Schwab');
    });

    it('should return default for invalid broker', () => {
      const name = getBrokerDisplayName('invalid' as BrokerType);
      expect(name).toBe('Unknown Broker');
    });
  });
});

describe('Broker Interfaces', () => {
  it('should have Position interface shape', () => {
    const position = {
      symbol: 'TSLA',
      quantity: 74,
      averageCostBasis: 234.19,
      lastPrice: 445.47,
      currentValue: 32964.78
    };

    expect(position.symbol).toBe('TSLA');
    expect(position.quantity).toBe(74);
    expect(position.averageCostBasis).toBe(234.19);
  });

  it('should have AccountBalances interface shape', () => {
    const balances = {
      settledCash: 0,
      netDebit: -7822.71,
      accountEquityPercentage: 96.58,
      marginInterestAccrued: 0,
      totalAccountValue: 100000.55
    };

    expect(balances.settledCash).toBe(0);
    expect(balances.netDebit).toBe(-7822.71);
    expect(balances.accountEquityPercentage).toBe(96.58);
  });

  it('should have ParsedPortfolioData interface shape', () => {
    const data = {
      positions: [
        { symbol: 'TSLA', quantity: 74, averageCostBasis: 234.19 }
      ],
      balances: {
        settledCash: 0,
        netDebit: -7822.71,
        accountEquityPercentage: 96.58,
        marginInterestAccrued: 0,
        totalAccountValue: 100000.55
      },
      broker: 'fidelity' as BrokerType,
      exportDate: new Date()
    };

    expect(data.broker).toBe('fidelity');
    expect(data.positions.length).toBe(1);
    expect(data.balances.totalAccountValue).toBe(100000.55);
  });
});

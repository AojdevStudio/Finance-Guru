import { getAllBrokers, type BrokerType, type BrokerCSVParser } from './broker-types';
import { createFidelityParser } from './parsers/fidelity-parser';

const parserRegistry: Readonly<Partial<Record<BrokerType, () => BrokerCSVParser>>> = {
  fidelity: createFidelityParser
};

export function getParserForBroker(brokerType: BrokerType): BrokerCSVParser {
  const parserFactory = parserRegistry[brokerType];

  if (!parserFactory) {
    throw new Error(
      `Broker "${brokerType}" is not yet supported. Currently supported: ${getSupportedBrokers().join(', ')}`
    );
  }

  return parserFactory();
}

export function isBrokerSupported(brokerType: BrokerType): boolean {
  return Object.hasOwn(parserRegistry, brokerType);
}

export function getSupportedBrokers(): BrokerType[] {
  return getAllBrokers()
    .map(broker => broker.id)
    .filter(isBrokerSupported);
}

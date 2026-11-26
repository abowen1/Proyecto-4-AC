"""Ejecuta la referencia M105-225 sobre un CSV y muestra su resumen."""
import argparse
import json
from pathlib import Path
from backtest import read_prices, official_rules, buy_hold_reference
from m105_225 import simulate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('series', type=Path)
    args = parser.parse_args()
    prices = read_prices(args.series)
    summary, _, _ = simulate(prices)
    summary['buy_and_hold'] = buy_hold_reference(prices, official_rules())
    print(json.dumps(summary, indent=2))

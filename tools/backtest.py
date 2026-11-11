"""Referencias enteras y causales de AC4; no modelan tiempo de CPU ni SPI."""
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Rules:
    cash: int = 10000
    commission: int = 5


def official_rules(path=ROOT / 'tb/tb_proyecto_4.sv'):
    source = path.read_text()
    values = [int(re.search(r'localparam int\s+' + name + r'\s*=\s*(\d+)', source)[1])
              for name in ('CAJA0', 'COMISION')]
    return Rules(*values)


class Market:
    def __init__(self, rules):
        self.rules = rules
        self.cash = self.equity = self.peak = rules.cash
        self.shares = self.orders = self.max_dd = 0

    def execute(self, decision, price):
        if not 0 <= decision <= 255 or not 1 <= price <= 255:
            raise ValueError('decisión o precio fuera de rango')
        action, quantity = decision >> 6, decision & 63
        fill = 0
        if action == 1:
            quantity = min(quantity, max(0, (self.cash - self.rules.commission) // price))
            if quantity > 0:
                self.cash -= quantity * price + self.rules.commission
                self.shares += quantity
                self.orders += 1
                fill = quantity
        elif action == 2:
            quantity = min(quantity, self.shares)
            if quantity > 0 and self.cash + quantity * price >= self.rules.commission:
                self.cash += quantity * price - self.rules.commission
                self.shares -= quantity
                self.orders += 1
                fill = -quantity
        self.equity = self.cash + self.shares * price
        self.peak = max(self.peak, self.equity)
        self.max_dd = max(self.max_dd, self.peak - self.equity)
        return fill


class Strategy:
    """Solo recibe el precio actual; no tiene acceso a la serie futura."""
    def __init__(self, kind, parameters=None):
        self.kind = kind
        if parameters and kind != 'reversion_media':
            raise ValueError('Los parámetros opcionales solo aplican a reversión a la media')
        self.parameters = dict(PARAMETERS.get(kind, {}))
        if parameters:
            if set(parameters) - {'ventana', 'banda'}:
                raise ValueError('Parámetro desconocido')
            self.parameters.update(parameters)
        if kind == 'reversion_media':
            if (type(self.parameters['ventana']) is not int or self.parameters['ventana'] < 2
                or type(self.parameters['banda']) is not int or self.parameters['banda'] < 0):
                raise ValueError('Ventana entera >=2 y banda entera >=0 requeridas')
        self.prices = deque()
        self.sum_y = self.sum_xy = 0

    def observe(self, price):
        if self.kind == 'mantener':
            return 0
        if self.kind == 'momentum':
            self.prices.append(price)
            if len(self.prices) < 9:
                return 0
            delta = price - self.prices.popleft()
            return 1 if delta > 2 else -1 if delta < -2 else 0
        window = 16 if self.kind == 'regresion' else 32
        if self.kind == 'reversion_media':
            window = self.parameters['ventana']
        if len(self.prices) == window:
            old = self.prices.popleft()
            self.sum_xy -= self.sum_y - old
            self.sum_y -= old
        self.sum_xy += len(self.prices) * price
        self.sum_y += price
        self.prices.append(price)
        if len(self.prices) < window:
            return 0
        if self.kind == 'medias_moviles':
            # SMA8 - SMA32, banda muerta de una unidad de precio.
            difference = sum(list(self.prices)[-8:]) * 32 - self.sum_y * 8
            threshold = 8 * 32
        elif self.kind == 'reversion_media':
            difference = self.sum_y - price * window
            threshold = self.parameters['banda'] * window
        elif self.kind == 'regresion':
            # Regresión y=a*x+b con x=0..15; predecir x=16, sin floats.
            sx = window * (window - 1) // 2
            sxx = window * (window - 1) * (2 * window - 1) // 6
            denominator = window * sxx - sx * sx
            slope_numerator = window * self.sum_xy - sx * self.sum_y
            difference = (self.sum_y * denominator
                          + slope_numerator * (window * window - sx)
                          - price * window * denominator)
            threshold = window * denominator  # Una unidad de precio.
        else:
            raise ValueError(self.kind)
        return 1 if difference > threshold else -1 if difference < -threshold else 0


KINDS = ('mantener', 'medias_moviles', 'momentum', 'regresion', 'reversion_media')
LABELS = dict(zip(KINDS, ('Mantener', 'Medias móviles', 'Momentum',
                         'Regresión lineal', 'Reversión a la media')))
PARAMETERS = {
    'mantener': {},
    'medias_moviles': {'corta': 8, 'larga': 32, 'banda': 1},
    'momentum': {'retardo': 8, 'banda': 2},
    'regresion': {'ventana': 16, 'horizonte': 1, 'banda': 1},
    'reversion_media': {'ventana': 32, 'banda': 2},
}


def size_order(signal, market, price):
    # Misma regla para las cuatro señales: comprar con la caja disponible,
    # vender inventario, no deuda ni cortos. Cada byte limita q a 63.
    if signal > 0:
        q = min(63, max(0, (market.cash - market.rules.commission) // price))
        return 0x40 | q if q else 0
    if signal < 0:
        q = min(63, market.shares)
        return 0x80 | q if q else 0
    return 0


def run(prices, kind, rules, parameters=None, policy=None):
    market, strategy = Market(rules), Strategy(kind, parameters)
    pending = 0
    rows = []
    for tick, price in enumerate(prices):
        # El byte pendiente se ejecuta ANTES de decidir con el precio recibido.
        applied = pending
        fill = market.execute(applied, price)
        signal = strategy.observe(price)
        pending = (size_order(signal, market, price) if policy is None
                   else policy.decide(signal, market, price, fill))
        rows.append(dict(tick=tick, price=price, applied_decision=applied,
                         next_decision=pending, signal=signal, fill=fill,
                         cash=market.cash, shares=market.shares, equity=market.equity,
                         orders=market.orders, commissions=market.orders * rules.commission,
                         max_drawdown=market.max_dd))
    summary = dict(strategy=kind, label=LABELS[kind], ticks=len(prices),
                   equity=market.equity, profit=market.equity - rules.cash,
                   orders=market.orders, commissions=market.orders * rules.commission,
                   max_drawdown=market.max_dd, cash=market.cash, shares=market.shares)
    return summary, rows


def read_prices(path):
    rows = list(csv.DictReader(path.open()))
    if not rows or any(int(row['tick']) != i or not 1 <= int(row['price']) <= 255
                       for i, row in enumerate(rows)):
        raise ValueError('Se requiere tick consecutivo desde cero y price entre 1 y 255')
    return [int(row['price']) for row in rows]


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def buy_hold_reference(prices, rules):
    # Fórmula del benchmark oficial: no es una estrategia ejecutable por SPI.
    q = (rules.cash - rules.commission) // prices[0]
    return rules.cash - rules.commission - q * prices[0] + q * prices[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--series', type=Path, default=ROOT / 'tb/practica.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/estrategia/comparacion')
    args = parser.parse_args()
    prices, rules = read_prices(args.series), official_rules()
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for scope, data in [('completa', prices), ('canvas_2000', prices[:2000])]:
        for kind in KINDS:
            summary, rows = run(data, kind, rules)
            summary['scope'] = scope
            summaries.append(summary)
            write_csv(args.output / f'{scope}_{kind}.csv', rows)
    write_csv(args.output / 'resumen.csv', summaries)
    manifest = dict(series_sha256=hashlib.sha256(args.series.read_bytes()).hexdigest(),
                    rules=vars(rules), parameters=PARAMETERS,
                    buy_hold_complete=buy_hold_reference(prices, rules),
                    buy_hold_2000=buy_hold_reference(prices[:2000], rules),
                    model='Respuesta en n+1; sin límites de tiempo CPU; sin liquidación final',
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output / 'configuracion.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = ['# Comparación exploratoria de estrategias AC4', '',
              'Caja inicial: 10.000. Comisión: 5 por orden ejecutada. Sin búsqueda de parámetros.', '',
              'Señales enteras; orden calculada en n y ejecutada en n+1. No se modelan deadlines.', '']
    for scope, title in [('completa', 'Serie completa: 20.000 precios'),
                         ('canvas_2000', 'Primeros 2.000 precios: longitud predeterminada de Canvas')]:
        scoped = sorted((s for s in summaries if s['scope'] == scope),
                        key=lambda r: r['equity'], reverse=True)
        report += ['## ' + title, '', '| Estrategia | Patrimonio final | Ganancia/pérdida | Órdenes | Comisiones | Pérdida máxima desde peak |',
                   '|---|---:|---:|---:|---:|---:|']
        for r in scoped:
            report.append(f"| {r['label']} | {r['equity']} | {r['profit']:+d} | {r['orders']} | {r['commissions']} | {r['max_drawdown']} |")
        report.append('')
    report += [f"Benchmark oficial comprar y mantener: {manifest['buy_hold_complete']} en la serie completa; {manifest['buy_hold_2000']} en los primeros 2.000 precios.", '',
               'El patrimonio incluye acciones al último precio. No se fuerza una venta final ni se ejecuta la última decisión pendiente.', '',
               'Cada familia representa UNA variante y parámetros iniciales. El ranking puede cambiar con otra serie o parámetros. No hay estrategia elegida por el equipo ni validación de estas cuatro variantes en assembly/FPGA.', '',
               'Reglas y límites: ../comparacion.md. Datos completos por tick: los diez CSV de esta carpeta. Reproducir con `make test-market compare` desde la raíz.']
    (args.output / 'RESULTADOS.md').write_text('\n'.join(report) + '\n')
    print('Serie completa:')
    for row in sorted((s for s in summaries if s['scope'] == 'completa'),
                      key=lambda r: r['equity'], reverse=True):
        print(f"{row['label']:24s} patrimonio={row['equity']:8d} órdenes={row['orders']:5d} comisión={row['commissions']:6d} drawdown={row['max_drawdown']:7d}")
    print('Benchmark oficial comprar y mantener:', manifest['buy_hold_complete'])


if __name__ == '__main__':
    main()

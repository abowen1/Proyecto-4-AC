"""Reproduce decisiones Python con la tarea ejecutar EXACTA del testbench Canvas."""
from pathlib import Path
import json
import subprocess
from backtest import ROOT, KINDS, Market, official_rules, read_prices, run


def verify(rows_all=None, destination=None):
    rules = official_rules()
    source = (ROOT / 'tb/tb_proyecto_4.sv').read_text()
    accounting = source.split('// Contabilidad oficial\n', 1)[1].split('// Mide los ciclos', 1)[0]
    output = ROOT / 'build/market_oracle'
    output.mkdir(parents=True, exist_ok=True)
    if rows_all is None:
        prices = read_prices(ROOT / 'tb/practica.csv')
        rows_all = [(kind, run(prices, kind, rules)[1]) for kind in KINDS]
    rows_all = list(rows_all)
    # Casos límite adicionales: reservado, q=0, fondos insuficientes,
    # venta sin inventario, comisión superior a caja, clipping y precios extremos.
    market = Market(rules)
    edges = []
    for i, (d, p) in enumerate([(0xff,1),(0x40,1),(0xbf,1),(0x7f,255),
                               (0x7f,255),(0x7f,1),(0x7f,1),(0x7f,1),
                               (0x7f,1),(0x7f,1),(0x7f,1),(0x7f,1),
                               (0x7f,1),(0x7f,1),(0xbf,1),(0xbf,255),
                               (0xbf,1),(0xbf,1),(0xbf,1),(0xbf,1)]):
        market.execute(d,p)
        edges.append(dict(tick=i,applied_decision=d,price=p,cash=market.cash,
                          shares=market.shares,equity=market.equity,orders=market.orders,
                          max_drawdown=market.max_dd))
    rows_all.append(('bordes',edges))
    input_file = output / 'replay.txt'
    with input_file.open('w') as f:
        for _, rows in rows_all:
            f.write(f'{len(rows)}\n')
            for r in rows:
                f.write(' '.join(str(r[k]) for k in ('applied_decision','price','cash','shares','equity','orders','max_drawdown'))+'\n')
    bench = '''module oracle;
localparam int CAJA0=10000, COMISION=5;
ACCOUNTING
integer fd, groups, count, rc, d, p, ec, es, ew, eo, ed;
initial begin
fd=$fopen("replay.txt","r");
if(!fd) $fatal(1,"replay missing");
for(groups=0;groups<GROUP_COUNT;groups=groups+1) begin
  caja=CAJA0; acciones=0; w=CAJA0; peak=CAJA0; max_dd=0; ordenes=0;
  rc=$fscanf(fd,"%d",count); if(rc!=1) $fatal(1,"group missing");
  for(integer i=0;i<count;i=i+1) begin
    rc=$fscanf(fd,"%d %d %d %d %d %d %d",d,p,ec,es,ew,eo,ed);
    if(rc!=7) $fatal(1,"row missing");
    ejecutar(d[7:0],p);
    if(caja!=ec || acciones!=es || w!=ew || ordenes!=eo || max_dd!=ed)
      $fatal(1,"mismatch group=%0d tick=%0d",groups,i);
  end
end
$display("PASS contabilidad Canvas: estrategias completas y casos límite");
$finish;
end
endmodule
'''.replace('ACCOUNTING', accounting).replace('GROUP_COUNT', str(len(rows_all))).replace('CAJA0=10000, COMISION=5',f'CAJA0={rules.cash}, COMISION={rules.commission}')
    (output / 'oracle.sv').write_text(bench)
    subprocess.run(['iverilog','-g2012','-s','oracle','-o','oracle','oracle.sv'],cwd=output,check=True)
    result = subprocess.run(['vvp','-n','oracle'],cwd=output,check=True,capture_output=True,text=True)
    print(result.stdout.strip())
    report = dict(status='PASS',compared_ticks=sum(len(r) for _,r in rows_all),
                  source='Tarea ejecutar y estado copiados literalmente de tb/tb_proyecto_4.sv',
                  scope='Contabilidad, no ejecución de estrategias en Espino ni deadlines',
                  output=result.stdout.strip())
    if destination is None:
        destination=ROOT/'docs/estrategia/comparacion'
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'validacion_contabilidad.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    verify()

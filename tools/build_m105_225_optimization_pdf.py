"""Informe de mediciones y bitstream: datos guardados, sin simular ni programar."""
import json,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.platypus import Table,TableStyle,Paragraph
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/estrategia/M105_225_optimizacion';W,H=landscape(A4);M=36;WIDTH=W-2*M
INK=colors.HexColor('#183047');PALE=colors.HexColor('#eef3f6');NAMES={'base':'Base85 (funcional)','soft':'Software optimizado','shifter':'A: shifter','qcap':'B: QCAP'}
def number(n,d=2):return f'{n:,.{d}f}'.replace(',','_').replace('.',',').replace('_','.')
def main():
 r=json.loads((D/'resumen.json').read_text());a=r['aggregates'];out=D/'Informe_M105_225_mediciones_e_imagen.pdf'
 c=canvas.Canvas(str(out),pagesize=(W,H),pageCompression=1);c.setTitle('M105-225: mediciones, co-diseno e imagen de Go Board');c.setAuthor('Andrés Bowen');page=0
 def text(x,y,s,size=10,bold=False):c.setFillColor(INK);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
 def header(title,subtitle):
  nonlocal page
  page+=1;text(M,H-40,title,21,True);text(M,H-61,subtitle,9);c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,H-73,W-M,H-73)
 def footer():
  c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,34,W-M,34);text(M,20,'AC4 | 24 noviembre 2026 | M105-225 | Reloj 25 MHz | Imagen generada; FPGA sin programar',8);c.setFont('Helvetica',8);c.drawRightString(W-M,20,str(page)+' /7');c.showPage()
 def table(data,top,widths,height=23,font=9):
  assert abs(sum(widths)-WIDTH)<.1
  t=Table(data,colWidths=widths,rowHeights=[height]*len(data));t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),font),('ALIGN',(1,0),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]));_,h=t.wrap(WIDTH,H);t.drawOn(c,M,top-h);return top-h
 def image(name,y):c.drawImage(str(D/'graficos'/(name+'.png')),M,y,width=WIDTH,height=WIDTH*4/11.5,mask='auto')
 def paragraphs(items,y,size=9.5,spacing=8):
  style=ParagraphStyle('p',fontName='Helvetica',fontSize=size,leading=size*1.3,textColor=INK)
  for s in items:
   p=Paragraph(s,style);_,h=p.wrap(WIDTH,H);p.drawOn(c,M,y-h);y-=h+spacing
  assert y>35,y

 header('M105-225 | implementación elegida','78 series por implementación | 312 perfiles completos | Mismas decisiones y resultados bursátiles')
 data=[['Implementación','Ciclos medios','Máx. ciclos','IC medio','Máx. IC','CPI servicio','Media (µs)','Máximo (µs)']]
 for key,v in a.items():data.append([NAMES[key],number(v['mean_cycles'],5),v['max_cycles'],number(v['mean_ic'],3),v['max_ic'],number(v['cpi'],4),number(v['mean_us'],4),number(v['max_us'],2)])
 table(data,500,[155,95,80,95,80,80,90,WIDTH-675],height=23,font=8.8)
 text(M,363,'Elección: software optimizado. Menor tiempo medio en '+number(100*r['selected_mean_time_reduction'])+' %; mayor latencia observada baja '+number(100*r['selected_worst_time_reduction'])+' %.',10,True)
 image('01_ciclos',73)
 text(M,50,'Servicio medido desde byte_done hasta DECISION; excluye SPI y espera ociosa. No es el CPI de todo el programa.',8.5);footer()

 header('El perfil guió la optimización','Contadores pasivos por PC: no agregan instrucciones al programa ni cambian el diseño')
 image('02_perfil',222)
 names={'io':'Recepción/publicación','account_control':'Despacho contable','policy':'Despacho de estados','buy_account':'Contabilizar compra','sell_account':'Contabilizar venta','size_buy':'Dimensionar compra','sell_quantity':'Cantidad de venta'}
 data=[['Sección base','Ciclos acumulados','Fracción del servicio']]
 for key,value in sorted(a['base']['sections'].items(),key=lambda x:-x[1]):data.append([names[key],number(value,0),number(100*value/a['base']['total_cycles'],3)+' %'])
 table(data,205,[360,210,WIDTH-570],height=18,font=9.3);footer()

 header('Amdahl | beneficio local y beneficio global','Predicciones con fracciones disjuntas; puntos del gráfico usan aceleración local medida a posteriori')
 image('03_amdahl',223)
 data=[['Objetivo','Aceleración local','Aceleración global predicha','Medida global']]
 for name in ('software','shifter','qcap'):
  for row in [x for x in r['amdahl'] if x['target']==name and (x['local_speedup']=='infinity' or x['kind'].startswith('retrospective'))]:
   data.append([name,'Infinita' if row['local_speedup']=='infinity' else number(row['local_speedup'],3),number(row['predicted_speedup'],6),number(row['measured_global_speedup'],6)])
 table(data,202,[165,170,230,WIDTH-565],height=19,font=9.2)
 text(M,54,'La aritmética de cantidades es rápida localmente, pero ocupa muy pocos ciclos del servicio total.',9);footer()

 header('Dos alternativas de hardware comparadas','A reutiliza el shifter acotado; B reutiliza QCAP(custom-0). La CPU sigue leyendo el precio y decidiendo.')
 data=[['Implementación','LUT4','Celdas lógicas','BRAM','Fmax(MHz)','Palabras código']]
 for key,v in a.items():data.append([NAMES[key],v['lut4'],str(v['logic_cells'])+' /1280',str(v['bram'])+' /16',number(v['fmax_mhz']),v['words']])
 table(data,500,[190,100,150,100,120,WIDTH-660],height=24,font=9.5)
 text(M,359,'Software: más margen de LUTs; ambas extensiones ahorran menos de 0,03 % adicional de tiempo medio.',9.5,True)
 image('04_recursos',72);footer()

 header('Ops/s y roofline','Kernel principal: una evaluación de política por precio | Kernel aritmético: una consulta de cantidad acotada')
 image('05_roofline',211)
 paragraphs([
  '<b>Medido:</b> el kernel de política elegido alcanza '+number(r['policy_kernel']['ops_per_second'],0)+' evaluaciones/s. En cantidades: software '+number(r['kernel']['soft']['ops_per_second'],0)+', shifter '+number(r['kernel']['shifter']['ops_per_second'],0)+' y QCAP '+number(r['kernel']['qcap']['ops_per_second'],0)+' consultas/s dentro del kernel. Es capacidad de servicio, no tasa de precios recibidos ni rentabilidad.',
  '<b>Intensidad de datos:</b> presupuesto, precio y cantidad residen en registros. El kernel no carga ni escribe RAM de datos: su intensidad es infinita. El punto del extremo derecho es simbólico; no representa 1000 consultas/byte reales. La búsqueda de instrucciones no se cuenta como tráfico de RAM de datos.',
  '<b>Techos ideales del modelo:</b> puerto de datos de 32 bits a 25 MHz =100 MB/s; emisión ideal de una instrucción cada 2 ciclos =12,5 M instrucciones/s. Se divide ese techo por IC medido/consulta para normalizar las tres implementaciones. Es una cota ideal, no el pico sostenible medido; omite penalizaciones y latencia específica de QCAP.',
  '<b>Interpretación:</b> este kernel está limitado por ejecución/control, no por ancho de banda de datos. QCAP acelera la consulta local, pero esta región solo ocupa '+number(100*r['kernel']['soft']['cycles']/a['soft']['total_cycles'],5)+' % del servicio optimizado. Los archivos CSV conservan unidades y supuestos.'
 ],190,size=9.2,spacing=7);footer()

 header('Resultados financieros y validación','Las optimizaciones preservan M105-225: compra 105, venta 225, exposición 100%, comisión 5 y ejecución siguiente')
 data=[['Referencia','Patrimonio medio','Peor final','Órdenes medias','Comisión media','Mayor caída($)']]
 for label,v in r['financial_references'].items():data.append([label,number(v['mean']),number(v['minimum'],0),number(v['mean_orders'],3),number(v['mean_commissions'],3),number(v['max_dd'],0)])
 table(data,500,[205,130,110,110,115,WIDTH-670],height=25,font=9.2)
 paragraphs(['Comprar y mantener usa exactamente la referencia de la maestra: q=floor((10000-5)/precio_inicial), una comisión inicial, sin límite 63 en ese benchmark teórico. No es una orden legal de un único byte si q supera 63. No se cambia la comisión ni el límite de la estrategia M.',
             'Las 78 series conocidas pueden solaparse por fechas y se normalizan por ventana. Esta comparación no es evidencia de 78 ensayos estadísticamente independientes. Las optimizaciones no ajustan parámetros financieros.'],y=383,size=9.3)
 data=[['Control','Cobertura','Resultado'],['Equivalencia/perfil','78 series por 4 implementaciones;6.240.000 ticks','PASS'],['Perfiles base reutilizados','78 perfiles sin cambios;234 perfiles nuevos finales','PASS'],['Cantidades, saltos y estados','Icarus para las tres optimizadas; prueba artificial 1710 precios','PASS'],['Hardware A y B','Unidad e instrucciones reales en SoC','PASS'],['Integración elegida','Tres períodos fijos y maestra oficial 4/4; Meta 2000 en Icarus','PASS'],['Regresión unitaria','39 publicadas;50 en suite local; trade.s coincide con la elegida','PASS']]
 table(data,230,[170,510,WIDTH-680],height=23,font=9.1);footer()

 header('Imagen generada | pausa antes de la placa','El enunciado exige recursos/timing y una Go Board funcional: generar la imagen sí corresponde; programarla es el paso siguiente')
 m=r['final_image'];v=a['soft']
 paragraphs([
  '<b>Fuente oficial:</b> sw/trade.s, 217 instrucciones base y 868 bytes. Los programas D se conservan como historia. La imagen elegida usa el núcleo sin nuevas extensiones; reloj fijo 25 MHz. No se usa información externa a los precios recibidos.',
  '<b>Capacidad y timing:</b> '+str(v['lut4'])+' LUT4; '+str(v['logic_cells'])+'/1280 celdas lógicas; '+str(v['bram'])+'/16 BRAM. Fmax estimada '+number(v['fmax_mhz'])+'MHz, superior al objetivo 25 MHz. La frecuencia implementada sigue siendo 25 MHz.',
  '<b>Margen de respuesta:</b> máximo observado '+str(v['max_cycles'])+' ciclos frente a 2262 disponibles en la ronda 0,1 ms después de descontar la transacción. Margen observado '+str(r['deadline_margin_cycles'])+' ciclos. Esto no sustituye la validación física.',
  '<b>Artefacto:</b> build/final/M105_225.bin ('+str(m['image_bytes'])+' bytes), también archivado en imagen/M105_225.bin. El HEX incorporado es idéntico al validado en las 78 series de la variante elegida.'
 ],y=496,size=10,spacing=12)
 text(M,292,'SHA256 del bitstream:',10,True);text(M,274,m['bitstream_sha256'],8.4)
 text(M,246,'Comandos de reproducción:',11,True);c.setFillColor(INK);c.setFont('Helvetica',10)
 for i,line in enumerate(['make compare-m105-225-implementations','make test-m105-225-optimized','make test-final','make build-final']):c.drawString(M+10,224-20*i,line)
 paragraphs(['<b>Detención solicitada:</b> no se ejecutó iceprog ni se programó la FPGA. Quedan pendientes la prueba USB/SPI física, arranque tras reconectar y competencia con la maestra del curso. No se publica la conexión física como aprobada.',
             '<b>Evidencia para la entrega:</b> sección 3.2 del enunciado (código y métricas por tick), sección 3.3(dos alternativas, Amdahl, LUTs/BRAM/Fmax, Ops/s y roofline), y README con síntesis/programación. El informe de selección financiera anterior aporta el desarrollo del algoritmo.'],y=132,size=9.3,spacing=10)
 footer();assert page==7;c.save();print(out)

if __name__=='__main__':main()

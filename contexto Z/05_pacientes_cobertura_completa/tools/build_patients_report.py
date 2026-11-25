"""Un PDF: todas las curvas P1/P2, métricas, reglas y promedio como cierre."""
import csv,json,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.platypus import Table,TableStyle,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1];W,H=landscape(A4);M=38;WIDTH=W-2*M
INK=colors.HexColor('#183047');GREEN=colors.HexColor('#007749');PALE=colors.HexColor('#eef3f6')
NAMES={'Paciente_1':'Paciente 1','Paciente_2':'Paciente 2'}
MONEY=lambda n:'$ '+f'{float(n):,.0f}'.replace(',','.')
PCT=lambda n:f'{float(n):.1f}'.replace('.',',')+' %'

def main():
    plan=json.loads((ROOT/'plan.json').read_text());sources=plan['sources'];agg=json.loads((ROOT/'agregados.json').read_text());v=json.loads((ROOT/'validacion_contabilidad.json').read_text())
    rows=list(csv.DictReader((ROOT/'resumen.csv').open()));index={(r['dataset'],r['strategy']):r for r in rows}
    assert len(sources)==79 and len(rows)==158 and v['status']=='PASS'
    batch=24;index_pages=math.ceil(len(sources)/batch);total_pages=1+1+index_pages+1+len(sources)+1
    out=ROOT/'output/pdf/AC4_Paciente_1_vs_2_todas_las_series.pdf';out.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(out),pagesize=(W,H),pageCompression=1)
    c.setTitle('AC4 - Paciente 1 versus Paciente 2 - Cobertura completa');c.setAuthor('Andrés Bowen')
    c.setSubject('79 series únicas,158 corridas,gráficos,métricas,parámetros y patrimonio promedio final')
    page=0
    def text(x,y,s,size=10,bold=False):
        c.setFillColor(INK);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
    def header(title,subtitle):
        nonlocal page
        page+=1;text(M,H-42,title,21,True);text(M,H-62,subtitle,9.4)
        c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,H-74,W-M,H-74)
    def footer():
        c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,37,W-M,37)
        text(M,22,'AC4 | 23 noviembre 2026 | Solo Paciente 1 y 2 | Capital 10.000 | Comisión fija 5',8)
        c.setFont('Helvetica',8);c.drawRightString(W-M,22,f'{page} / {total_pages}');c.showPage()
    def table(data,top,widths,row_height=22,font=9.5,best=None):
        t=Table(data,colWidths=widths,rowHeights=[row_height]*len(data));style=[
            ('BACKGROUND',(0,0),(-1,0),INK),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),font),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('ALIGN',(1,0),(-1,-1),'RIGHT'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#c6d3dd'))]
        for col,row in best or []:style += [('TEXTCOLOR',(col,row),(col,row),GREEN),('FONTNAME',(col,row),(col,row),'Helvetica-Bold')]
        t.setStyle(TableStyle(style));_,height=t.wrap(WIDTH,H);t.drawOn(c,M,top-height);return top-height
    def stats_rows(g):
        result=[]
        for n,label in NAMES.items():
            a=agg[g]['strategies'][n];count=agg[g]['count']
            result.append([label,MONEY(a['mean_equity']),MONEY(a['min_equity']),str(a['wins_vs_initial'])+f' / {count}',str(a['series_wins'])+f' / {count}',MONEY(a['mean_commissions']),PCT(a['max_drawdown_percent'])])
        return result
    stats_header=['Estrategia','Promedio final','Peor final','Sobre 10.000','Gana al otro','Comisión media','Mayor caída']
    stats_widths=[106,117,105,108,108,110,WIDTH-654]

    header('Paciente 1 versus Paciente 2','79 series únicas | 158 corridas | Configuraciones conservadas sin reajustar parámetros')
    text(M,500,'Resultado global: cada serie tiene el mismo peso',13,True)
    table([stats_header]+stats_rows('global'),485,stats_widths,row_height=27,font=9.2)
    text(M,382,'Resultados separados por origen',13,True)
    data=[['Origen / estrategia','Series','Promedio final','Peor final','Comisión media','Mayor caída']]
    for g,label in [('catedra','Cátedra - mercado'),('recreada','Recreadas'),('original','Práctica original')]:
        for n,name in NAMES.items():
            a=agg[g]['strategies'][n];data.append([label+' / '+name,str(agg[g]['count']),MONEY(a['mean_equity']),MONEY(a['min_equity']),MONEY(a['mean_commissions']),PCT(a['max_drawdown_percent'])])
    bottom=table(data,366,[230,60,125,110,125,WIDTH-650],row_height=23,font=9.2)
    lines=[
        'Cobertura: ocho series oficiales de mercado, la práctica original anterior y 70 bloques recreados.',
        'Se excluye la copia duplicada de Meta. Las 70 recreadas tienen 14 bloques por acción de 2022 a 2024.',
        'Las recreadas son aproximaciones públicas, no el generador original de Nicolás.',
        'Los bloques recreados no se solapan por acción según su índice; pueden coincidir con períodos de cátedra.',
        'Parte de las series ya se había observado. El conjunto no equivale a 79 ensayos independientes.',
        'El último gráfico promedia por tick relativo: cada corrida reinicia con 10.000, sin encadenar períodos.',
    ]
    for i,line in enumerate(lines):text(M,bottom-23-17*i,line,9.2)
    footer()

    header('Resultados por acción - solo recreadas','14 bloques de 20.000 observaciones por acción; todas las entradas existentes, sin generar otras')
    data=[['Acción / estrategia','Sobre 10.000','Gana al otro','Promedio final','Peor final','Comisión media','Mayor caída']]
    for symbol,label in [('AAPL','Apple'),('AMD','AMD'),('META','Meta'),('NFLX','Netflix'),('TSLA','Tesla')]:
        for n,name in NAMES.items():
            a=agg['recreada_'+symbol]['strategies'][n];data.append([label+' / '+name,f"{a['wins_vs_initial']} / 14",f"{a['series_wins']} / 14",MONEY(a['mean_equity']),MONEY(a['min_equity']),MONEY(a['mean_commissions']),PCT(a['max_drawdown_percent'])])
    bottom=table(data,496,[153,95,95,115,100,105,WIDTH-663],row_height=26,font=9.2)
    notes=[
        'Fuente de las recreadas: Syncster Historical Market Data, disponible públicamente en Hugging Face.',
        'Cierres por minuto de sesión regular; cada bloque se normaliza por separado al rango 100-255.',
        'Receta del paquete: np.rint(100 + 155*(cierre-mínimo)/(máximo-mínimo)), NumPy float64.',
        'No se descargaron ni regeneraron precios para este informe: se usaron los 70 CSV existentes y sus hashes.',
        'Los mercados de distintas acciones comparten fechas; los resultados pueden estar correlacionados.',
    ]
    for i,line in enumerate(notes):text(M,bottom-25-i*18,line,9.2)
    footer()

    for offset in range(0,len(sources),batch):
        group=sources[offset:offset+batch]
        header('Comparación de todas las series',f'Filas {offset+1} a {offset+len(group)} de {len(sources)} | Los nombres enlazan a su gráfico')
        data=[['Serie / origen','Final P1','Final P2','Com. P1','Com. P2','Caída P1','Caída P2']];best=[]
        for i,s in enumerate(group,1):
            a=index[(s['id'],'Paciente_1')];b=index[(s['id'],'Paciente_2')]
            origin={'catedra':'C','original':'O','recreada':'R'}[s['group']]
            label=s['label'] if s['group']!='recreada' else s['label']+' | '+s['start_ny'][:10]
            data.append([origin+' - '+label,MONEY(a['equity']),MONEY(b['equity']),MONEY(a['commissions']),MONEY(b['commissions']),PCT(a['drawdown_percent']),PCT(b['drawdown_percent'])])
            if a['equity']!=b['equity']:best.append((1 if int(a['equity'])>int(b['equity']) else 2,i))
        table(data,500,[265,102,102,76,76,72,WIDTH-693],row_height=17.5,font=8.7,best=best)
        for i,s in enumerate(group):c.linkRect('',s['id'],(M,500-17.5*(i+2),M+265,500-17.5*(i+1)),relative=0,thickness=0)
        text(M,48,'C = cátedra de mercado; O = práctica original anterior; R = recreada. Caída = máximo descenso desde un pico previo.',8.2)
        footer()

    header('Parámetros utilizados','Las estrategias son las mismas Paciente 1 y Paciente 2 del informe anterior')
    paragraphs=[
        ('Común a ambas','Momentum de 32 intervalos: compra si la subida supera el 2% y esa condición se sostiene durante tres ticks consecutivos.'),
        ('Diferencia de Paciente 2','Además exige SMA32 > SMA128 y precio actual > SMA128. Las medias incluyen el precio actual. El filtro afecta solo nuevas compras.'),
        ('Exposición y cantidades','Hasta el 50% del patrimonio observado al dimensionar la entrada. Una compra por posición, sin agregar mientras mantiene acciones; máximo 63 por orden. La ejecución siguiente puede superar ese porcentaje por un salto de precio.'),
        ('Stop loss y trailing','Stop neto del 3%, siempre activo. Al alcanzar +4% neto por posición se activa trailing del 3% desde el máximo de su valor neto de liquidación. No hay take profit fijo.'),
        ('Señal contraria y espera','La señal contraria de momentum32 confirmada en tres ticks permite vender después de al menos 32 ticks en posición. Tras una venta se esperan 64 ticks antes de volver a comprar. La permanencia mínima no bloquea las protecciones.'),
        ('Contabilidad','Capital inicial 10.000 por serie; comisión fija 5 por orden ejecutada. Sin deuda ni ventas en corto. La decisión se ejecuta al precio siguiente. No hay liquidación forzada al final: patrimonio = caja + acciones valorizadas al último precio.'),
    ]
    st=ParagraphStyle('p',fontName='Helvetica',fontSize=10,leading=13,textColor=INK)
    data=[[Paragraph('<b>'+a+'</b>',st),Paragraph(b,st)] for a,b in paragraphs]
    t=Table(data,colWidths=[160,WIDTH-160]);t.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[PALE,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));_,height=t.wrap(WIDTH,H);t.drawOn(c,M,500-height)
    y=500-height-22
    for line in [
        'Los porcentajes corresponden a los precios normalizados y al retorno neto de la posición, incluidas comisiones.',
        'Un stop o trailing emite una orden; el precio siguiente puede atravesar el umbral antes de ejecutarla.',
        'La práctica original tiene rango 72-190; se conserva su entrada sin convertirla al rango nuevo.',
        f"Contabilidad Canvas: PASS en {v['compared_ticks']:,} ticks; {v['historical_trace_equivalence_runs']} trazas históricas idénticas.".replace(',','.'),
    ]:text(M,y,line,8.6);y-=15
    assert y>40,y
    footer()

    for s in sources:
        c.bookmarkPage(s['id']);c.addOutlineEntry(s['label']+' | '+s['group'],s['id'],level=0)
        origin={'catedra':'Cátedra','original':'Cátedra - original anterior','recreada':'Recreada'}[s['group']]
        header(s['label']+' | '+origin,s['filename']+' | 20.000 ticks | SHA256 '+s['sha256'][:16])
        c.drawImage(ImageReader(str(ROOT/'graficos'/(s['id']+'.png'))),M-3,171,width=WIDTH+6,height=(WIDTH+6)*4.9/11,mask='auto')
        data=[['Estrategia','Patrimonio final','Retorno','Órdenes','Comisiones','Caída máxima']]
        for n,name in NAMES.items():
            r=index[(s['id'],n)];data.append([name,MONEY(r['equity']),PCT((int(r['equity'])/10000-1)*100),r['orders'],MONEY(r['commissions']),PCT(r['drawdown_percent'])])
        table(data,154,[145,145,105,95,130,WIDTH-620],row_height=23,font=10)
        if s['group']=='recreada':text(M,69,'Nueva York: '+s['start_ny']+' a '+s['end_ny']+'. Fechas tomadas del índice del paquete.',8.5)
        else:text(M,69,'El año/mes del rótulo identifica la serie; no limita necesariamente su duración.',8.5)
        text(M,54,'Patrimonio = caja + acciones al último precio; no hay liquidación final forzada.',8.5)
        footer()

    c.bookmarkPage('promedio_final');c.addOutlineEntry('Promedio global - gráfico final','promedio_final',level=0)
    header('Promedio de comportamiento | gráfico final','Media aritmética del patrimonio en cada tick relativo sobre las 79 series únicas')
    a=agg['global']['strategies']['Paciente_1'];b=agg['global']['strategies']['Paciente_2']
    text(M,500,'Promedio final: Paciente 1 = '+MONEY(a['mean_equity'])+' | Paciente 2 = '+MONEY(b['mean_equity']),12,True)
    text(M,481,'Cada curva promedia 79 corridas; cada una reinicia caja e inventario con un capital de 10.000.',9)
    text(M,465,'No es una cartera cronológica ni supone independencia estadística. Las 70 recreadas pesan 70/79 del total.',9)
    c.drawImage(ImageReader(str(ROOT/'graficos/promedio_global.png')),M,84,width=WIDTH,height=WIDTH*5.1/11,mask='auto')
    text(M,60,'Promedio(t) = suma del patrimonio de cada serie en el tick t / 79. Las comisiones ya están descontadas.',9)
    footer();assert page==total_pages,(page,total_pages);c.save();print(str(out),flush=True)

if __name__=='__main__':main()

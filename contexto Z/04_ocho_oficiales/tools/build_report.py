"""Un único PDF de decisión con los resultados íntegros de las ocho series."""
import csv,json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.platypus import Table,TableStyle,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
W,H=landscape(A4);M=38;CONTENT=W-2*M
NAMES={'D':'D original','Paciente_1':'Paciente 1','Paciente_2':'Paciente 2','Lento_1':'Lento 1','Lento_2':'Lento 2'}
INK=colors.HexColor('#183047');TEAL=colors.HexColor('#007749');PALE=colors.HexColor('#eef3f6')
MONEY=lambda v:'$ '+f'{float(v):,.0f}'.replace(',','.')
PCT=lambda v:f'{float(v):.1f}'.replace('.',',')+' %'

def main():
    rows=list(csv.DictReader((ROOT/'resumen.csv').open()));plan=json.loads((ROOT/'plan.json').read_text());agg=json.loads((ROOT/'agregados.json').read_text())
    validation=json.loads((ROOT/'validacion_contabilidad.json').read_text());assert validation['status']=='PASS' and len(rows)==40
    datasets=list(plan['sources']);index={(r['dataset'],r['strategy']):r for r in rows}
    out=ROOT/'output/pdf/AC4_Comparacion_5_estrategias_8_series.pdf';out.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(out),pagesize=(W,H),pageCompression=1)
    c.setTitle('AC4 - Cinco estrategias sobre ocho series oficiales')
    c.setAuthor('Andrés Bowen');c.setSubject('40 corridas: D, Paciente 1 y 2, Lento 1 y 2. Configuraciones fijas.')
    page=0
    def header(title,subtitle):
        nonlocal page
        page+=1;c.setFillColor(INK);c.setFont('Helvetica-Bold',21);c.drawString(M,H-42,title)
        c.setFont('Helvetica',10);c.setFillColor(colors.HexColor('#536779'));c.drawString(M,H-62,subtitle)
        c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,H-74,W-M,H-74)
    def footer():
        c.setStrokeColor(colors.HexColor('#ccd7df'));c.line(M,37,W-M,37)
        c.setFillColor(colors.HexColor('#536779'));c.setFont('Helvetica',8)
        c.drawString(M,22,'AC4 | 23 noviembre 2026 | CSV oficiales | Capital 10.000 | Comisión fija 5 por orden')
        c.drawRightString(W-M,22,f'{page} / 11');c.showPage()
    def text(x,y,s,size=10,bold=False,color=INK):
        c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
    def table(data,top,widths=None,row_height=23,align_first=True,font=10,best=None):
        widths=widths or [170]+[(CONTENT-170)/(len(data[0])-1)]*(len(data[0])-1)
        t=Table(data,colWidths=widths,rowHeights=[row_height]*len(data))
        style=[('BACKGROUND',(0,0),(-1,0),INK),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
               ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),font),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
               ('ALIGN',(1,0),(-1,-1),'RIGHT'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
               ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#c6d3dd'))]
        if best:
            for col,row in best:style.extend([('TEXTCOLOR',(col,row),(col,row),TEAL),('FONTNAME',(col,row),(col,row),'Helvetica-Bold')])
        t.setStyle(TableStyle(style));tw,th=t.wrap(CONTENT,H);t.drawOn(c,M,top-th)
        return top-th

    header('Cinco estrategias. Ocho series oficiales.','Comparación con parámetros fijos - 40 corridas de 20.000 precios cada una')
    text(M,499,'Patrimonio final por serie. La mayor cifra de cada fila aparece destacada.',10)
    data=[['Serie']+list(NAMES.values())];best=[]
    for i,d in enumerate(datasets,1):
        vals=[int(index[(d,n)]['equity']) for n in NAMES]
        data.append([plan['sources'][d]['label']]+[MONEY(v) for v in vals])
        best.extend((j+1,i) for j,v in enumerate(vals) if v==max(vals))
    bottom=table(data,486,row_height=24,best=best)
    # Los nombres de serie enlazan a la página con el gráfico respectivo.
    for i,d in enumerate(datasets):c.linkRect('',d,(M,486-24*(i+2),M+170,486-24*(i+1)),relative=0,thickness=0)
    text(M,bottom-24,'Lectura agregada del conjunto',13,True)
    data=[['Estrategia','Promedio final','Peor final','Sobre 10.000','Comisión media','Mayor caída']]
    for n,label in NAMES.items():
        a=agg[n];data.append([label,MONEY(a['mean_equity']),MONEY(a['min_equity']),str(a['wins_vs_initial'])+' / 8',MONEY(a['mean_commissions']),PCT(a['max_drawdown_percent'])])
    bottom=table(data,bottom-36,widths=[120,135,125,120,135,CONTENT-635],row_height=22,font=9.5)
    text(M,bottom-18,'Cada serie comienza con 10.000; los promedios no representan una inversión encadenada.',8.6)
    text(M,bottom-32,'Los rótulos de año/mes identifican el archivo: los 20.000 minutos pueden abarcar varios meses.',8.6)
    footer()

    header('Comisiones y caídas máximas','Mismas reglas para las cinco alternativas; las diferencias provienen de sus decisiones')
    text(M,500,'Comisiones totales pagadas',12,True)
    data=[['Serie']+list(NAMES.values())]
    for d in datasets:data.append([plan['sources'][d]['label']]+[MONEY(index[(d,n)]['commissions']) for n in NAMES])
    table(data,488,row_height=21,font=10)
    text(M,276,'Caída máxima del patrimonio desde un máximo anterior',12,True)
    data=[['Serie']+list(NAMES.values())]
    for d in datasets:data.append([plan['sources'][d]['label']]+[PCT(index[(d,n)]['drawdown_percent']) for n in NAMES])
    bottom=table(data,264,row_height=21,font=10)
    text(M,bottom-18,'La caída máxima considera toda la trayectoria, no solo la diferencia entre capital inicial y final.',8.6)
    footer()

    for d in datasets:
        source=plan['sources'][d];c.bookmarkPage(d);c.addOutlineEntry(source['label'],d,level=0)
        header(source['label']+' | evolución del patrimonio',source['filename']+' | 20.000 ticks | SHA256 '+source['sha256'][:16])
        c.drawImage(ImageReader(str(ROOT/'graficos'/(d+'.png'))),M-3,198,width=CONTENT+6,height=(CONTENT+6)*4.6/11,mask='auto')
        data=[['Estrategia','Patrimonio final','Retorno','Órdenes','Comisiones','Caída máxima']]
        for n,label in NAMES.items():
            r=index[(d,n)];data.append([label,MONEY(r['equity']),PCT((int(r['equity'])/10000-1)*100),r['orders'],MONEY(r['commissions']),PCT(r['drawdown_percent'])])
        bottom=table(data,184,widths=[145,145,105,95,130,CONTENT-620],row_height=19,font=10)
        text(M,bottom-15,'Patrimonio = caja + acciones al último precio. No hay liquidación forzada al final.',8.5)
        footer()

    header('Reglas de las cinco alternativas','Configuraciones conservadas antes de correr los ocho archivos; sin optimización posterior')
    st=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=11,textColor=INK)
    entries=[
        ['D original','Reversión a la media: SMA32, banda de 1 unidad. Compra bajo la banda y vende sobre ella.',
         'Sin TP, SL ni trailing. Las señales dimensionan compras con la caja disponible y ventas con el inventario.',
         'Hasta 63 por orden. Puede agregar compras. Sin espera ni permanencia mínima.'],
        ['Paciente 1','Momentum de 32 intervalos superior al 2%, sostenido en 3 ticks consecutivos.',
         'SL neto 3%. Trailing 3% desde el máximo de la posición, activado al alcanzar +4% neto. Señal contraria de momentum tras 32 ticks de permanencia.',
         'Entrada hasta 50% del patrimonio observado. Una compra por posición; hasta 63. Espera 64 ticks tras vender.'],
        ['Paciente 2','Entrada de Paciente 1 y además SMA32 > SMA128 y precio actual > SMA128. Las medias incluyen el precio actual.',
         'Mismas salidas y protecciones de Paciente 1. El filtro de entrada no bloquea una venta ni el stop.',
         'Misma exposición, cantidades, espera y permanencia que Paciente 1.'],
        ['Lento 1','Momentum de 128 intervalos superior al 3%, sostenido en 4 ticks consecutivos.',
         'TP neto 6%, SL neto 4%. Señal contraria de momentum128 confirmada en 4 ticks, tras al menos 64 ticks de permanencia.',
         'Entrada hasta 50% del patrimonio observado. Una compra por posición; hasta 63. Espera 128 ticks tras vender.'],
        ['Lento 2','Momentum de 16 intervalos superior al 1%, confirmado en 2 ticks; SMA32 > SMA128 y precio actual > SMA128.',
         'Mismas salidas de Lento 1, incluido momentum128. La señal corta solo cambia la entrada.',
         'Misma exposición, cantidades, espera y permanencia que Lento 1.'],
    ]
    data=[[Paragraph('<b>'+x+'</b>',st) for x in ['Estrategia','Entrada','Salida','Gestión de posición']]]
    data += [[Paragraph(x,st) for x in row] for row in entries]
    t=Table(data,colWidths=[85,230,265,CONTENT-580]);t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#c6d3dd'))]))
    tw,th=t.wrap(CONTENT,H);assert th<390,th;t.drawOn(c,M,505-th);y=505-th-20
    notes=[
        'Capital inicial 10.000; comisión 5 por orden ejecutada; sin deuda ni ventas en corto.',
        'La decisión se ejecuta al precio siguiente. TP, SL y trailing no garantizan ejecución en el umbral.',
        'Los porcentajes se aplican a precios normalizados y retornos netos por posición, contando comisiones.',
        'La exposición se calcula al decidir; un salto en el precio de ejecución puede superar el tope observado.',
        'Prueba exploratoria: parte de las series ya había sido observada. No prueba resultados futuros.',
        'Contabilidad Canvas: PASS en '+f"{validation['compared_ticks']:,}".replace(',','.')+' ticks; 20 trazas previas idénticas.',
    ]
    for s in notes:text(M,y,s,8.5);y-=14
    assert y>36,y
    footer();assert page==11;c.save()
    print(out)

if __name__=='__main__':main()

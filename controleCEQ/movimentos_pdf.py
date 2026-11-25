"""Self-contained landscape PDFs for entries and transfers."""
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, LongTable, Paragraph, TableStyle, Spacer
from .relatorios_pdf import fontes, n, NAVY, GREEN, MUTED, LINE, PALE


def gerar_pdf(tipo,cfg,dados,registros,celulas,agora):
    fontes()
    buffer=BytesIO()
    largura,altura=landscape(A4)
    util=largura-28*mm-12
    doc=SimpleDocTemplate(buffer,pagesize=(largura,altura),leftMargin=14*mm,rightMargin=14*mm,
        topMargin=30*mm,bottomMargin=20*mm,title='KAITO - '+cfg['titulo']+' de diesel',author='KAITO')
    style=ParagraphStyle('celula',fontName='Kaito',fontSize=7.5,leading=11,textColor=NAVY)
    head=ParagraphStyle('cab',parent=style,fontName='KaitoBold',textColor=colors.white)
    bold=ParagraphStyle('total',parent=style,fontName='KaitoBold')
    number=ParagraphStyle('numero',parent=style,alignment=TA_RIGHT)
    total_number=ParagraphStyle('total_numero',parent=bold,alignment=TA_RIGHT)
    note=ParagraphStyle('nota',parent=style,textColor=MUTED,spaceAfter=5)
    def p(valor,estilo=style): return Paragraph(escape(str(valor if valor is not None else '-')),estilo)
    periodo=(dados['inicio'].strftime('%d/%m/%Y') if dados['inicio'] else 'Sem limite inicial')+' a '+(dados['fim'].strftime('%d/%m/%Y') if dados['fim'] else 'Sem limite final')
    total=sum((Decimal(str(getattr(r,cfg['quantidade']) or 0)) for r in registros),Decimal('0'))
    valor=sum((Decimal(str(r.preco_total or 0)) for r in registros),Decimal('0')) if tipo=='entradas' else None
    filtros=[]
    for grupo in dados['grupos']:
        labels={str(o['id']):o['label'] for o in grupo['opcoes']}
        selecionados=[labels.get(i,'ID '+i) for i in grupo['selecionados']]
        texto=', '.join(selecionados[:3])+(' (+'+str(len(selecionados)-3)+')' if len(selecionados)>3 else '') if selecionados else 'Todos'
        filtros.append(grupo['rotulo']+': '+texto)
    story=[p('Período de '+('entrega' if tipo=='entradas' else 'transferência')+': '+periodo,note),p(' | '.join(filtros),note),Spacer(1,9)]
    cards=[('TOTAL '+('RECEBIDO' if tipo=='entradas' else 'TRANSFERIDO'),n(total)+' L'),('REGISTROS',str(len(registros)))]
    if tipo=='entradas':
        cards += [('VALOR DAS NOTAS','R$ '+n(valor)),('OBRAS',str(len({r.obra_id for r in registros})))]
    else:
        cards += [('ORIGENS',str(len({r.fixo_id for r in registros if r.fixo_id is not None}))),('DESTINOS',str(len({r.movel_id for r in registros if r.movel_id is not None})))]
    cardstyle=ParagraphStyle('card',fontName='Kaito',fontSize=7,leading=20,textColor=MUTED)
    cardrow=[Paragraph(escape(label)+'<br/><font name="KaitoBold" size="13" color="#073b68">'+escape(v)+'</font>',cardstyle) for label,v in cards]
    card=LongTable([cardrow],colWidths=[util/4]*4,hAlign='LEFT')
    card.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [card,Spacer(1,17)]
    indices=cfg['pdf_indices']
    headers=[cfg['cabecalho'][i] for i in indices]
    rows=[[p(h,head) for h in headers]]
    for r in registros:
        row=celulas(r,tipo)
        rows.append([p(row[i],number if i in ((7,8,9) if tipo=='entradas' else (4,5,6,7)) else style) for i in indices])
    if not registros: rows.append([p('Nenhum lançamento encontrado para os filtros selecionados.')]+['']*(len(headers)-1))
    totalrow=['']*len(headers)
    totalrow[0]='TOTAL GERAL'
    quantidade_pos=indices.index(7 if tipo=='entradas' else 4)
    totalrow[quantidade_pos]=n(total)+' L'
    if tipo=='entradas': totalrow[indices.index(9)]=n(valor)
    rows.append([p(v,total_number if i>=quantidade_pos else bold) if v else '' for i,v in enumerate(totalrow)])
    pesos=cfg['pdf_larguras']
    table=LongTable(rows,colWidths=[util*v/sum(pesos) for v in pesos],repeatRows=1,splitByRow=1,hAlign='LEFT')
    commands=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,PALE]),('LINEBELOW',(0,0),(-1,-1),.4,LINE),
        ('BACKGROUND',(0,-1),(-1,-1),PALE),('SPAN',(0,-1),(quantidade_pos-1,-1)),
        ('NOSPLIT',(0,len(rows)-2),(-1,len(rows)-1))]
    if not registros: commands.append(('SPAN',(0,1),(-1,1)))
    table.setStyle(TableStyle(commands))
    story.append(table)
    def frame(canvas,document):
        canvas.saveState();canvas.setFont('KaitoBold',19);canvas.setFillColor(NAVY)
        canvas.drawString(14*mm,altura-16*mm,'KAITO')
        canvas.setFont('Kaito',6.5);canvas.setFillColor(GREEN)
        canvas.drawString(14*mm,altura-21*mm,'CONTROLE DE COMBUSTÍVEL')
        canvas.setFont('KaitoBold',12);canvas.setFillColor(NAVY)
        canvas.drawRightString(largura-14*mm,altura-16*mm,cfg['titulo']+' de diesel')
        canvas.setFont('Kaito',7);canvas.setFillColor(MUTED)
        canvas.drawRightString(largura-14*mm,altura-21*mm,periodo)
        canvas.setStrokeColor(LINE);canvas.line(14*mm,altura-25*mm,largura-14*mm,altura-25*mm)
        canvas.line(14*mm,17*mm,largura-14*mm,17*mm)
        canvas.drawString(14*mm,12*mm,'KAITO | Gerado em '+agora.strftime('%d/%m/%Y %H:%M')+' | Quantidades em litros.')
        canvas.drawRightString(largura-14*mm,12*mm,'Página '+str(document.page))
        canvas.restoreState()
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    return buffer.getvalue()

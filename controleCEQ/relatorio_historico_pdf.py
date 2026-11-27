"""Monthly work-site history PDF, with repeating headers and intact rows."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, LongTable, TableStyle, Spacer, CondPageBreak
from .relatorios_pdf import fontes, n, p, NAVY, GREEN, CORAL, MUTED, LINE, PALE


def gerar_historico_pdf(dados):
    fontes()
    buffer=BytesIO()
    largura,altura=A4
    util=largura-28*mm-12
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=14*mm,rightMargin=14*mm,
        topMargin=30*mm,bottomMargin=21*mm,title='KAITO - Histórico mensal das obras',author='KAITO')
    style=ParagraphStyle('h-cell',fontName='Kaito',fontSize=8,leading=11.5,textColor=NAVY)
    number=ParagraphStyle('h-number',parent=style,alignment=TA_RIGHT)
    negative=ParagraphStyle('h-negative',parent=number,textColor=CORAL)
    totalstyle=ParagraphStyle('h-total',parent=number,fontName='KaitoBold')
    cab=ParagraphStyle('h-cab',parent=style,fontName='KaitoBold',fontSize=7.5,textColor=colors.white)
    name=ParagraphStyle('h-name',parent=style,fontName='KaitoBold',fontSize=10,leading=14)
    title=ParagraphStyle('h-title',parent=name,fontSize=16,leading=21,spaceAfter=9)
    note=ParagraphStyle('h-note',parent=style,fontSize=7.5,leading=11,textColor=MUTED,spaceAfter=9)
    summary=dados['resumo']
    filtros=dados['obra_selecionada'].nome if dados['obra_selecionada'] else 'Todas as obras'
    story=[p('Histórico mensal por obra',title),p(filtros,note)]
    if dados['aviso']: story.append(p(dados['aviso'],note))
    story.append(p('Período de cada obra: do primeiro ao último lançamento registrado. Os meses sem movimentação no intervalo aparecem zerados.',note))
    cardstyle=ParagraphStyle('h-card',parent=style,fontSize=7,leading=17,textColor=MUTED)
    cards=[]
    from xml.sax.saxutils import escape
    for label,value in [('Entradas',n(summary['entradas'])+' L'),('Saídas',n(summary['saidas'])+' L'),('Resultado',n(summary['resultado'])+' L')]:
        cards.append(Paragraph(escape(label)+'<br/><font name="KaitoBold" size="11" color="#073b68">'+escape(value)+'</font>',cardstyle))
    card=LongTable([cards],colWidths=[util/3]*3,hAlign='LEFT')
    card.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [card,Spacer(1,18)]
    if dados['obras_sem_movimento']:
        story.append(p('Sem movimentação registrada: '+', '.join(o.nome for o in dados['obras_sem_movimento']),note))
    if dados['sem_obra']['registros']:
        story.append(p(str(dados['sem_obra']['registros'])+' abastecimento(s) sem obra vinculada ('+n(dados['sem_obra']['total'])+' L) ficam fora dos totais por obra.',note))
    story.append(p('Entradas: data de entrega. Saídas: data do abastecimento. Resultado = entradas menos saídas. Acumulado = soma dos resultados desde o primeiro lançamento.',note))
    for h in dados['historicos']:
        story.append(CondPageBreak(150))
        label=h['obra'].nome+' | '+h['inicio'].strftime('%m/%Y')+' a '+h['fim'].strftime('%m/%Y')
        rows=[[p(label,name),'','','',''],[p(t,cab) for t in ['Mês / ano','Entradas (L)','Saídas (L)','Resultado (L)','Acumulado (L)']]]
        for row in h['linhas']:
            mes=p(row['rotulo']+(' - sem movimento' if row['sem_movimento'] else ''),style)
            values=[mes,p(n(row['entradas']),number),p(n(row['saidas']),number),
                p(n(row['resultado']),negative if row['resultado']<0 else number),
                p(n(row['acumulado']),negative if row['acumulado']<0 else number)]
            rows.append(values)
        t=h['totais']
        rows.append([p('TOTAL DA OBRA',name),p(n(t['entradas']),totalstyle),p(n(t['saidas']),totalstyle),p(n(t['resultado']),totalstyle),p(n(t['resultado']),totalstyle)])
        table=LongTable(rows,colWidths=[util*v for v in [.26,.185,.185,.185,.185]],repeatRows=2,splitByRow=1,hAlign='LEFT')
        table.setStyle(TableStyle([('SPAN',(0,0),(-1,0)),('BACKGROUND',(0,0),(-1,0),PALE),
            ('BACKGROUND',(0,1),(-1,1),NAVY),('ROWBACKGROUNDS',(0,2),(-1,-2),[colors.white,colors.HexColor('#fafcfe')]),
            ('BACKGROUND',(0,-1),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,1),(-1,-1),.35,LINE),('NOSPLIT',(0,len(rows)-2),(-1,len(rows)-1))]))
        table.spaceAfter=18
        story.append(table)
    if not dados['historicos']:
        story.append(p('Nenhuma movimentação registrada para a seleção.',note))
    def frame(canvas,document):
        canvas.saveState();canvas.setFillColor(NAVY);canvas.setFont('KaitoBold',18)
        canvas.drawString(14*mm,altura-16*mm,'KAITO')
        canvas.setFont('Kaito',6.5);canvas.setFillColor(GREEN)
        canvas.drawString(14*mm,altura-21*mm,'CONTROLE DE COMBUSTÍVEL')
        canvas.setFont('KaitoBold',9);canvas.setFillColor(NAVY)
        canvas.drawRightString(largura-14*mm,altura-16*mm,'Histórico mensal das obras')
        canvas.setStrokeColor(LINE);canvas.line(14*mm,altura-25*mm,largura-14*mm,altura-25*mm)
        canvas.line(14*mm,16*mm,largura-14*mm,16*mm)
        canvas.setFont('Kaito',6.5);canvas.setFillColor(MUTED)
        canvas.drawString(14*mm,11*mm,'KAITO | Gerado em '+dados['gerado_em'].strftime('%d/%m/%Y %H:%M'))
        canvas.drawRightString(largura-14*mm,11*mm,'Página '+str(document.page))
        canvas.restoreState()
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    return buffer.getvalue()

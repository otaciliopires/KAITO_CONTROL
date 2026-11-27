"""Paginated A4 reports. Charts and table rows never split across sheets."""
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, KeepTogether, LongTable, PageBreak,
                               Paragraph, SimpleDocTemplate, Spacer, TableStyle)

NAVY = colors.HexColor('#073b68')
GREEN = colors.HexColor('#16866d')
CORAL = colors.HexColor('#d75e49')
MUTED = colors.HexColor('#718398')
PALE = colors.HexColor('#f2f6fa')
LINE = colors.HexColor('#e0e8ef')
WIDTH = A4[0] - 28*mm - 12


def fontes():
    if 'Kaito' not in pdfmetrics.getRegisteredFontNames():
        pasta = Path(reportlab.__file__).parent/'fonts'
        pdfmetrics.registerFont(TTFont('Kaito', str(pasta/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('KaitoBold', str(pasta/'VeraBd.ttf')))
        pdfmetrics.registerFontFamily('Kaito', normal='Kaito', bold='KaitoBold', italic='Kaito', boldItalic='KaitoBold')


def n(valor, casas=2):
    return format(Decimal(str(valor or 0)), ',.'+str(casas)+'f').replace(',', '_').replace('.', ',').replace('_', '.')


def p(texto, estilo):
    return Paragraph(escape('—' if texto is None else str(texto)), estilo)


def tabela(cabecalho, linhas, larguras, estilos, total=None, numeros=(), total_span=1):
    cab = [p(c, estilos['cab']) for c in cabecalho]
    rows = [cab]
    for linha in linhas:
        rows.append([p(c, estilos['numero'] if i in numeros else estilos['celula']) for i,c in enumerate(linha)])
    if not linhas:
        rows.append([p('Sem lançamentos no período selecionado.', estilos['celula'])]+['']*(len(cabecalho)-1))
    if total:
        rows.append([p(c, estilos['total_numero'] if i in numeros else estilos['total']) for i,c in enumerate(total)])
    table = LongTable(rows, colWidths=[WIDTH*v for v in larguras], repeatRows=1,
                      hAlign='LEFT', splitByRow=1)
    comandos = [('BACKGROUND',(0,0),(-1,0),PALE), ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),7), ('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,0),(-1,0),.6,LINE),
                ('LINEBELOW',(0,1),(-1,-1),.35,LINE)]
    fim = -2 if total else -1
    if linhas:
        comandos.append(('ROWBACKGROUNDS',(0,1),(-1,fim),[colors.white,colors.HexColor('#fbfcfe')]))
    else:
        comandos.append(('SPAN',(0,1),(-1,1)))
    if total:
        comandos += [('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#edf5f7')),
                     ('LINEABOVE',(0,-1),(-1,-1),.7,LINE)]
    if total:
        comandos.append(('NOSPLIT',(0,len(rows)-2),(-1,len(rows)-1)))
    if total and total_span > 1:
        comandos.append(('SPAN',(0,-1),(total_span-1,-1)))
    table.setStyle(TableStyle(comandos))
    return table


def grafico_semanal(semanas):
    desenho = Drawing(WIDTH, 180)
    esquerda, base, altura = 42, 37, 117
    largura = WIDTH-esquerda-8
    maior = max([float(s[c]) for s in semanas for c in ('entradas','abastecimentos')]+[1])
    for i in range(5):
        y = base+altura*i/4
        desenho.add(Line(esquerda,y,WIDTH-3,y,strokeColor=LINE,strokeWidth=.5))
        desenho.add(String(esquerda-7,y-2,n(maior*i/4,0),fontName='Kaito',fontSize=6.5,textAnchor='end',fillColor=MUTED))
    passo = largura/len(semanas)
    bar = min(17,passo*.26)
    for i,semana in enumerate(semanas):
        centro = esquerda+passo*(i+.5)
        for campo,x,cor in [('entradas',centro-bar-2,GREEN),('abastecimentos',centro+2,CORAL)]:
            h = max(0,float(semana[campo])/maior*altura)
            if h > 0:
                desenho.add(Rect(x,base,bar,h,fillColor=cor,strokeColor=None,rx=min(2,h/2),ry=min(2,h/2)))
        desenho.add(String(centro,22,'Semana '+str(semana['numero']),fontName='KaitoBold',fontSize=7.2,textAnchor='middle',fillColor=NAVY))
        desenho.add(String(centro,10,semana['intervalo'].replace('–','-'),fontName='Kaito',fontSize=6.6,textAnchor='middle',fillColor=MUTED))
    desenho.add(Rect(WIDTH-188,168,7,7,fillColor=GREEN,strokeColor=None))
    desenho.add(String(WIDTH-176,168,'Entradas',fontName='Kaito',fontSize=7.3,fillColor=MUTED))
    desenho.add(Rect(WIDTH-112,168,7,7,fillColor=CORAL,strokeColor=None))
    desenho.add(String(WIDTH-100,168,'Abastecimentos',fontName='Kaito',fontSize=7.3,fillColor=MUTED))
    return desenho


def truncar(texto, largura, tamanho=7.6):
    texto = str(texto)
    if pdfmetrics.stringWidth(texto,'Kaito',tamanho) <= largura:
        return texto
    while texto and pdfmetrics.stringWidth(texto+'...','Kaito',tamanho) > largura:
        texto = texto[:-1]
    return texto+'...'


def ranking(linhas, nome, campo):
    d = Drawing(WIDTH,max(34,23*len(linhas)+5))
    maior = max((float(l[campo]) for l in linhas),default=1) or 1
    x = 170
    maximo = WIDTH-x-83
    for i,linha in enumerate(linhas):
        y = d.height-23*(i+1)+6
        d.add(String(0,y+2,truncar(linha[nome],160),fontName='Kaito',fontSize=7.6,fillColor=NAVY))
        d.add(Rect(x,y,maximo,8,fillColor=PALE,strokeColor=None,rx=3,ry=3))
        comprimento = max(0,float(linha[campo])/maior*maximo)
        if comprimento > 0:
            d.add(Rect(x,y,comprimento,8,fillColor=GREEN,strokeColor=None,rx=min(3,comprimento/2),ry=min(3,comprimento/2)))
        d.add(String(WIDTH-2,y+1,n(linha[campo])+' L',fontName='KaitoBold',fontSize=7.6,textAnchor='end',fillColor=NAVY))
    return d


def gerar_pdf(dados):
    fontes()
    estilos = {
        'titulo': ParagraphStyle('titulo',fontName='KaitoBold',fontSize=18,leading=23,textColor=NAVY,spaceAfter=5,keepWithNext=True),
        'subtitulo': ParagraphStyle('subtitulo',fontName='Kaito',fontSize=9,leading=13,textColor=MUTED,spaceAfter=15),
        'secao': ParagraphStyle('secao',fontName='KaitoBold',fontSize=12,leading=17,textColor=NAVY,spaceBefore=5,spaceAfter=8,keepWithNext=False),
        'nota': ParagraphStyle('nota',fontName='Kaito',fontSize=7.4,leading=11,textColor=MUTED,spaceAfter=10),
        'cab': ParagraphStyle('cab',fontName='KaitoBold',fontSize=8,leading=11,textColor=NAVY),
        'celula': ParagraphStyle('celula',fontName='Kaito',fontSize=8.5,leading=12.5,textColor=colors.HexColor('#354f68')),
        'numero': ParagraphStyle('numero',fontName='Kaito',fontSize=8.5,leading=12.5,textColor=NAVY,alignment=TA_RIGHT),
        'total': ParagraphStyle('total',fontName='KaitoBold',fontSize=8.5,leading=12.5,textColor=NAVY),
        'total_numero': ParagraphStyle('total_numero',fontName='KaitoBold',fontSize=8.5,leading=12.5,textColor=NAVY,alignment=TA_RIGHT),
    }
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,pagesize=A4,leftMargin=14*mm,rightMargin=14*mm,
                            topMargin=30*mm,bottomMargin=20*mm,
                            title='KAITO - Relatório de diesel - '+dados['mes_rotulo'],author='KAITO')
    resumo = dados['resumo']
    por_obra = dados['visao']=='obra'
    obra = dados['obra_selecionada']
    titulo = obra.nome if por_obra and obra else ('Relatório por obra' if por_obra else 'Visão mensal de todas as obras')
    def moldura(canvas, documento):
        canvas.saveState()
        canvas.setFillColor(NAVY);canvas.setFont('KaitoBold',18)
        canvas.drawString(14*mm,A4[1]-15*mm,'KAITO')
        canvas.setFont('Kaito',6.5);canvas.setFillColor(GREEN)
        canvas.drawString(14*mm,A4[1]-20*mm,'CONTROLE DE COMBUSTÍVEL')
        canvas.setFillColor(NAVY);canvas.setFont('KaitoBold',8)
        canvas.drawRightString(A4[0]-14*mm,A4[1]-14*mm,dados['mes_rotulo'])
        canvas.setFillColor(MUTED);canvas.setFont('Kaito',7)
        canvas.drawRightString(A4[0]-14*mm,A4[1]-19*mm,'Relatório por obra' if por_obra else 'Todas as obras')
        canvas.setStrokeColor(LINE);canvas.line(14*mm,A4[1]-24*mm,A4[0]-14*mm,A4[1]-24*mm)
        canvas.line(14*mm,15*mm,A4[0]-14*mm,15*mm)
        canvas.setFont('Kaito',6.5);canvas.setFillColor(MUTED)
        canvas.drawString(14*mm,10.5*mm,'KAITO | '+dados['periodo']+' | '+('Consulta por obra' if por_obra else 'Consolidado mensal'))
        canvas.drawRightString(A4[0]-14*mm,10.5*mm,'Página '+str(documento.page))
        canvas.drawString(14*mm,7*mm,'Consulta em '+dados['gerado_em'].strftime('%d/%m/%Y às %H:%M')+' | Quantidades em litros.')
        canvas.restoreState()
    story = [p(titulo,estilos['titulo']),p(dados['inicio'].strftime('%d/%m/%Y')+' a '+dados['fim'].strftime('%d/%m/%Y'),estilos['subtitulo'])]
    cards = [('Entradas no mês',n(resumo['entradas'])+' L',str(resumo['notas'])+(' entrada registrada' if resumo['notas']==1 else ' entradas registradas'),GREEN),
             ('Abastecimentos',n(resumo['abastecimentos'])+' L',str(resumo['registros'])+' lançamentos',CORAL),
             ('Resultado do mês',n(resumo['resultado'])+' L','Sem saldo anterior',CORAL if resumo['resultado'] < 0 else NAVY)]
    if por_obra:
        cards.append(('Saldo atual cadastrado',n(obra.saldo if obra else 0)+' L','Todos os períodos',CORAL if obra and obra.saldo < 0 else NAVY))
    else:
        cards.append(('Obras com movimento',str(dados['obras_movimento']),'No mês selecionado',NAVY))
    cardstyle = ParagraphStyle('card',fontName='Kaito',fontSize=8,leading=18,textColor=MUTED)
    cardrow = [Paragraph(escape(label)+'<br/><font name="KaitoBold" size="13" color="'+('#'+cor.hexval()[2:])+'">'+escape(valor)+'</font><br/>'+escape(nota),cardstyle) for label,valor,nota,cor in cards]
    cardtable = LongTable([cardrow],colWidths=[WIDTH/4]*4)
    cardtable.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.5,LINE),('INNERGRID',(0,0),(-1,-1),.5,LINE),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story += [cardtable,Spacer(1,16)]
    if dados['aviso']:
        story.append(p(dados['aviso'],estilos['nota']))
    if dados['sem_dados']:
        story.append(p('Nenhum lançamento no mês selecionado. Os valores apresentados são zero.',estilos['nota']))
    semana_rows = [('Semana '+str(s['numero'])+' | '+s['intervalo'].replace('–','-'),n(s['entradas']),n(s['abastecimentos']),n(s['resultado']),str(s['registros'])) for s in dados['semanas']]
    weekly = [p('Comparativo por semana',estilos['secao']),grafico_semanal(dados['semanas']),Spacer(1,5),
              tabela(['Semana / datas','Entradas (L)','Abastecimentos (L)','Resultado (L)','Nº abast.'],semana_rows,[.32,.18,.20,.20,.10],estilos,numeros=(1,2,3,4)),Spacer(1,8),
              p('Semanas de segunda a domingo, limitadas ao mês. Entradas seguem a entrega; abastecimentos seguem a data do lançamento. Resultado = entradas menos abastecimentos, sem o saldo anterior. Não representa o estoque dos tanques.',estilos['nota'])]
    if por_obra:
        weekly.append(p('O saldo atual é o valor cadastrado no KAITO e abrange todos os períodos, independentemente do filtro de mês.',estilos['nota']))
    story += [KeepTogether(weekly),PageBreak()]
    if not por_obra:
        story.append(p('Obras com movimentação no mês',estilos['titulo']))
        story.append(p(dados['mes_rotulo']+' | '+str(dados['obras_movimento'])+' obras com movimentação',estilos['subtitulo']))
        if dados['ranking_obras']:
            story.append(KeepTogether([p('Maiores volumes abastecidos',estilos['secao']),ranking(dados['ranking_obras'],'nome','abastecimentos'),Spacer(1,14)]))
        if dados['sem_obra']:
            story.append(p('Os abastecimentos sem obra vinculada também compõem o total e aparecem em linha própria.',estilos['nota']))
        rows = [(r['nome'],n(r['entradas']),n(r['abastecimentos']),n(r['resultado']),str(r['registros'])) for r in dados['linhas_obras']]
        story += [CondPageBreak(110),p('Movimentação por obra',estilos['secao']),tabela(['Obra','Entradas (L)','Abastecimentos (L)','Resultado (L)','Nº abast.'],rows,[.34,.18,.20,.18,.10],estilos,
            total=['TOTAL GERAL',n(resumo['entradas']),n(resumo['abastecimentos']),n(resumo['resultado']),str(resumo['registros'])],numeros=(1,2,3,4))]
    else:
        story += [p('Equipamentos e entradas da obra',estilos['titulo']),p(titulo+' | '+dados['mes_rotulo'],estilos['subtitulo'])]
        if dados['ranking_equipamentos'] and len(dados['equipamentos']) <= 8:
            story.append(KeepTogether([p('Equipamentos com maior consumo',estilos['secao']),ranking(dados['ranking_equipamentos'],'equipamento__prefixo','total'),Spacer(1,14)]))
        rows = [(e['equipamento__prefixo'],e['equipamento__descricao'] or '—',str(e['registros']),n(e['total']),n(e['participacao'],1)+'%',e['ultimo'].strftime('%d/%m/%Y')) for e in dados['equipamentos']]
        story += [CondPageBreak(110),p('Abastecimentos por equipamento',estilos['secao']),tabela(['Equipamento','Descrição','Nº abast.','Quantidade (L)','Participação','Último no mês'],rows,[.16,.23,.10,.19,.15,.17],estilos,
            total=['TOTAL DA OBRA','',str(resumo['registros']),n(resumo['abastecimentos']),'',''],numeros=(2,3,4),total_span=2),Spacer(1,18)]
        rows = [(e['data_entrega'].strftime('%d/%m/%Y'),e['nota_fiscal'] or '—',e['fornecedor'] or '—',n(e['quantidade']),n(e['preco_total'])) for e in dados['notas']]
        story += [CondPageBreak(110),p('Notas de entrada no mês',estilos['secao']),tabela(['Entrega','Nota fiscal','Fornecedor','Quantidade (L)','Valor (R$)'],rows,[.17,.16,.28,.19,.20],estilos,
            total=['TOTAL DE ENTRADAS','','',n(resumo['entradas']),n(resumo['valor'])],numeros=(3,4),total_span=3)]
    doc.build(story,onFirstPage=moldura,onLaterPages=moldura)
    return buffer.getvalue()

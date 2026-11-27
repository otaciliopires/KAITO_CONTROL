"""Fast, self-contained landscape export of filtered fuel records."""
from decimal import Decimal
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from .colunas_saidas import COLUNAS
from .relatorios_pdf import fontes, n, NAVY, GREEN, MUTED, LINE, PALE

FIELDS = ('numero', 'tanque__prefixo', 'data', 'obra__nome',
          'equipamento__prefixo', 'equipamento__descricao', 'equipamento__proprietario',
          'litros', 'horimetro', 'lubrificacao', 'operador', 'obra_id', 'equipamento_id')


def quebrar(texto, largura, fonte='Kaito', tamanho=7):
    # Explicit word wrapping also supports identifiers without spaces.
    linhas = []
    for bloco in str(texto if texto not in (None, '') else '-').splitlines():
        linha = ''
        for palavra in bloco.split():
            tentativa = (linha + ' ' + palavra).strip()
            if stringWidth(tentativa, fonte, tamanho) <= largura:
                linha = tentativa
                continue
            if linha:
                linhas.append(linha)
                linha = ''
            for letra in palavra:
                if linha and stringWidth(linha + letra, fonte, tamanho) > largura:
                    linhas.append(linha)
                    linha = ''
                linha += letra
        linhas.append(linha or '-')
    return linhas or ['-']


def gerar_saidas_pdf(registros, consulta, gerado_em, obras=(), equipamentos=()):
    fontes()
    buffer = BytesIO()
    largura, altura = landscape(A4)
    margem = 12 * mm
    util = largura - 2*margem
    canvas = Canvas(buffer, pagesize=(largura, altura), pageCompression=1)
    canvas.setTitle('KAITO - Saídas de diesel')
    canvas.setAuthor('KAITO')
    total = sum((Decimal(str(r['litros'] or 0)) for r in registros), Decimal('0'))
    obras_mov = len({r['obra_id'] for r in registros if r['obra_id'] is not None})
    equipamentos_mov = len({r['equipamento_id'] for r in registros if r['equipamento_id'] is not None})
    selecionadas = consulta.get('colunas') or COLUNAS
    juntar_descricao = {'equipamento','descricao'}.issubset({c['id'] for c in selecionadas})
    definicoes = []
    for coluna in selecionadas:
        if juntar_descricao and coluna['id']=='descricao':
            continue
        definicao = dict(coluna)
        if juntar_descricao and coluna['id']=='equipamento':
            definicao['titulo'] = 'Equipamento / descrição'
            definicao['peso'] += next(c['peso'] for c in selecionadas if c['id']=='descricao')
        definicoes.append(definicao)
    proporcoes = [c['peso'] for c in definicoes]
    colunas = [util*v/sum(proporcoes) for v in proporcoes]
    titulos = [c['titulo'] for c in definicoes]
    inicio = consulta['inicio'].strftime('%d/%m/%Y') if consulta['inicio'] else 'Sem limite inicial'
    fim = consulta['fim'].strftime('%d/%m/%Y') if consulta['fim'] else 'Sem limite final'
    periodo = inicio + ' a ' + fim
    def nomes(items, padrao):
        items = list(items)
        return ', '.join(items[:3]) + (' (+%s)' % (len(items)-3) if len(items)>3 else '') if items else padrao
    filtros = ['Período: ' + periodo,
               'Obras: ' + nomes(obras, 'Todas') + ' | Equipamentos: ' + nomes(equipamentos, 'Todos')]
    pagina = 0
    def texto(x, y, valor, fonte='Kaito', tamanho=7, cor=NAVY):
        canvas.setFont(fonte, tamanho)
        canvas.setFillColor(cor)
        canvas.drawString(x, y, str(valor))
    def cabecalho(primeira=False):
        nonlocal pagina
        pagina += 1
        texto(margem, altura-18*mm, 'KAITO', 'KaitoBold', 20)
        texto(margem, altura-23*mm, 'CONTROLE DE COMBUSTÍVEL', tamanho=6.5, cor=GREEN)
        canvas.setFillColor(NAVY); canvas.setFont('KaitoBold', 13)
        canvas.drawRightString(largura-margem, altura-17*mm, 'Saídas de diesel')
        canvas.setFont('Kaito', 7); canvas.setFillColor(MUTED)
        canvas.drawRightString(largura-margem, altura-22*mm, periodo)
        y = altura-29*mm
        canvas.setStrokeColor(LINE); canvas.line(margem, y, largura-margem, y)
        y -= 14
        if primeira:
            for filtro in filtros:
                for linha in quebrar(filtro, util, tamanho=7.5):
                    texto(margem, y, linha, tamanho=7.5, cor=MUTED)
                    y -= 11
            y -= 7
            cards = [('TOTAL ABASTECIDO', n(total)+' L'), ('ABASTECIMENTOS', str(len(registros))),
                     ('OBRAS', str(obras_mov)), ('EQUIPAMENTOS', str(equipamentos_mov))]
            cw = util/4
            for i,(label, valor) in enumerate(cards):
                x = margem+i*cw
                canvas.setFillColor(PALE); canvas.rect(x,y-43,cw-7,43,fill=1,stroke=0)
                texto(x+9,y-13,label,tamanho=6.5,cor=MUTED)
                texto(x+9,y-32,valor,'KaitoBold',13)
            y -= 59
        else:
            texto(margem,y,'Continuação dos abastecimentos filtrados',tamanho=7,cor=MUTED)
            y -= 17
        canvas.setFillColor(NAVY); canvas.rect(margem,y-27,util,27,fill=1,stroke=0)
        x = margem
        for titulo,cw in zip(titulos,colunas):
            for j,linha in enumerate(quebrar(titulo,cw-10,'KaitoBold',6.8)):
                texto(x+5,y-11-j*9,linha,'KaitoBold',6.8,cor='white')
            x += cw
        return y-27
    def rodape():
        canvas.setStrokeColor(LINE);canvas.line(margem,17*mm,largura-margem,17*mm)
        texto(margem,12*mm,'KAITO | Gerado em '+gerado_em.strftime('%d/%m/%Y %H:%M')+' | Quantidades em litros.',tamanho=6.5,cor=MUTED)
        canvas.setFont('Kaito',6.5);canvas.setFillColor(MUTED)
        canvas.drawRightString(largura-margem,12*mm,'Página '+str(pagina))
    y = cabecalho(True)
    limite = 24*mm
    for i,r in enumerate(registros):
        cells = {'numero':r['numero'], 'tanque':r['tanque__prefixo'],
                 'data':r['data'].strftime('%d/%m/%Y') if r['data'] else '-',
                 'obra':r['obra__nome'] or 'Sem obra vinculada',
                 'equipamento':r['equipamento__prefixo'], 'descricao':r['equipamento__descricao'],
                 'propriedade':r['equipamento__proprietario'], 'quantidade':n(r['litros']),
                 'horimetro':n(r['horimetro']), 'lubrificacao':'Sim' if r['lubrificacao'] else 'Não',
                 'operador':r['operador']}
        if juntar_descricao and cells['descricao'] and cells['descricao'] != cells['equipamento']:
            cells['equipamento'] = str(cells['equipamento'] or '-') + '\n' + cells['descricao']
        linhas = [quebrar(cells[c['id']],w-10) for c,w in zip(definicoes,colunas)]
        h = max(29,10*max(map(len,linhas))+12)
        # Keep the final record and the total together.
        reserva = 34 if i==len(registros)-1 else 0
        if y-h-reserva < limite:
            rodape();canvas.showPage();y=cabecalho()
        if i%2==0:
            canvas.setFillColor(PALE);canvas.rect(margem,y-h,util,h,fill=1,stroke=0)
        x = margem
        for ci,(partes,cw) in enumerate(zip(linhas,colunas)):
            for j,linha in enumerate(partes):
                key=definicoes[ci]['id']
                if key in ('quantidade','horimetro'):
                    canvas.setFillColor(NAVY);canvas.setFont('KaitoBold' if key=='quantidade' else 'Kaito',7)
                    canvas.drawRightString(x+cw-5,y-13-j*10,linha)
                else:
                    texto(x+5,y-13-j*10,linha,'KaitoBold' if key in ('numero','equipamento') and j==0 else 'Kaito')
            x += cw
        y -= h
        canvas.setStrokeColor(LINE);canvas.line(margem,y,largura-margem,y)
    if not registros:
        texto(margem+9,y-23,'Nenhum abastecimento encontrado para os filtros selecionados.',tamanho=9,cor=MUTED)
        y -= 43
    canvas.setFillColor(NAVY);canvas.rect(margem,y-29,util,29,fill=1,stroke=0)
    texto(margem+9,y-18,'TOTAL GERAL | '+str(len(registros))+' abastecimentos','KaitoBold',8,cor='white')
    canvas.setFont('KaitoBold',10);canvas.setFillColor('white')
    canvas.drawRightString(largura-margem-9,y-19,n(total)+' L')
    rodape();canvas.save()
    return buffer.getvalue()

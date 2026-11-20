"""Página de conferência das vendas por período (área de vendas).

Sem datas na URL (primeira visita), a página usa a semana atual da loja, de
segunda a domingo. Com datas, usa o período informado, contando os dois dias.
A consulta fica em repositorios/relatorios.py.
"""
from flask import Blueprint, render_template, request

import regras
import relogio
from repositorios import relatorios as repositorio_relatorios

paginas = Blueprint('relatorios', __name__, url_prefix='/vendas/relatorio')

AVISO_DE_PENDENCIA = (
    'Operação indisponível: a função listar_vendas_periodo() do repositório '
    'de relatórios ainda não foi implementada.'
)


def ler_periodo(argumentos):
    """Datas do filtro -> (data_inicial, data_final).

    Sem nenhuma data, devolve a semana atual da loja. Lança ValueError se só
    uma data for informada, se alguma for inválida ou se a inicial vier depois
    da final.
    """
    texto_inicial = (argumentos.get('data_inicial') or '').strip()
    texto_final = (argumentos.get('data_final') or '').strip()
    if texto_inicial == '' and texto_final == '':
        return regras.semana_que_contem(relogio.hoje_na_loja())
    if texto_inicial == '' or texto_final == '':
        raise ValueError('Informe as duas datas do período (ou deixe as duas em branco para ver a semana atual).')
    data_inicial = regras.data_obrigatoria(texto_inicial, 'Data inicial')
    data_final = regras.data_obrigatoria(texto_final, 'Data final')
    if data_inicial > data_final:
        raise ValueError('A data inicial deve ser anterior ou igual à data final.')
    return data_inicial, data_final


@paginas.get('/')
def vendas_do_periodo():
    try:
        data_inicial, data_final = ler_periodo(request.args)
    except ValueError as erro:
        return render_template(
            'relatorios/periodo.html',
            campo_inicial=request.args.get('data_inicial', ''),
            campo_final=request.args.get('data_final', ''),
            periodo=None,
            vendas=None,
            erro=str(erro),
        )

    periodo = (data_inicial, data_final)
    campo_inicial = data_inicial.isoformat()
    campo_final = data_final.isoformat()
    try:
        vendas = repositorio_relatorios.listar_vendas_periodo(data_inicial, data_final)
    except NotImplementedError:
        return render_template(
            'relatorios/periodo.html',
            campo_inicial=campo_inicial,
            campo_final=campo_final,
            periodo=periodo,
            vendas=None,
            aviso=AVISO_DE_PENDENCIA,
        )
    return render_template(
        'relatorios/periodo.html',
        campo_inicial=campo_inicial,
        campo_final=campo_final,
        periodo=periodo,
        vendas=vendas,
    )

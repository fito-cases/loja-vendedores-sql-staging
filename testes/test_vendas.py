"""Repositório de vendas e itens: estoque, valor e concorrência, sobre os dados iniciais."""
import datetime
import threading
from decimal import Decimal

import pytest
from psycopg import errors

import db
from repositorios import produtos as repositorio_produtos
from repositorios import vendas as repositorio_vendas

pytestmark = pytest.mark.usefixtures('banco_recriado')


def estoque(cod_produto):
    sql = 'SELECT qtd_estoque FROM produtos WHERE cod_produto = %(cod_produto)s'
    return db.consultar_valor(sql, {'cod_produto': cod_produto})


def valor(numero_venda):
    sql = 'SELECT valor FROM vendas WHERE numero_venda = %(numero_venda)s'
    return db.consultar_valor(sql, {'numero_venda': numero_venda})


def itens_da_venda(numero_venda):
    """{cod_produto: (quantidade, preco_unitario)} lido diretamente do banco."""
    sql = """
        SELECT cod_produto, quantidade, preco_unitario
        FROM itens_vendas
        WHERE numero_venda = %(numero_venda)s
    """
    itens = {}
    for linha in db.consultar(sql, {'numero_venda': numero_venda}):
        itens[linha['cod_produto']] = (linha['quantidade'], linha['preco_unitario'])
    return itens


def test_venda_aberta_sem_itens_com_ou_sem_vendedor():
    com_vendedor = repositorio_vendas.abrir_venda({
        'cod_cliente': 11,
        'cod_vendedor': 2,
        'data_venda': datetime.date(2025, 6, 10),
    })
    sem_vendedor = repositorio_vendas.abrir_venda({
        'cod_cliente': 11,
        'cod_vendedor': None,
        'data_venda': datetime.date(2025, 6, 10),
    })

    assert (com_vendedor, sem_vendedor) == (107, 108)
    assert repositorio_vendas.buscar_venda(108) == {
        'numero_venda': 108,
        'cod_cliente': 11,
        'cod_vendedor': None,
        'data_venda': datetime.date(2025, 6, 10),
        'valor': Decimal('0.00'),
    }
    assert repositorio_vendas.listar_itens(108) == []
    assert repositorio_vendas.buscar_venda(999) is None


def test_listagens_de_vendas():
    todas = repositorio_vendas.listar_vendas()
    do_cliente_1 = repositorio_vendas.listar_vendas_do_cliente(1)

    assert len(todas) == 16
    assert todas[0]['numero_venda'] == 106
    numeros = []
    for venda in do_cliente_1:
        numeros.append(venda['numero_venda'])
    assert numeros == [103, 102]
    assert repositorio_vendas.listar_vendas_do_cliente(11) == []


def test_cabecalho_editado_sem_mudar_o_valor():
    repositorio_vendas.atualizar_venda({
        'numero_venda': 102,
        'cod_cliente': 2,
        'cod_vendedor': None,
        'data_venda': datetime.date(2025, 6, 4),
    })

    venda = repositorio_vendas.buscar_venda(102)
    assert venda['cod_cliente'] == 2
    assert venda['cod_vendedor'] is None
    assert venda['data_venda'] == datetime.date(2025, 6, 4)
    assert venda['valor'] == Decimal('80.00')


def test_itens_da_venda_com_descricao_e_subtotal():
    itens = repositorio_vendas.listar_itens(102)

    assert len(itens) == 2
    por_produto = {}
    for item in itens:
        por_produto[item['cod_produto']] = item
    assert por_produto[1]['descricao'] == 'Camiseta básica de algodão'
    assert por_produto[1]['subtotal'] == Decimal('50.00')
    assert por_produto[8]['subtotal'] == Decimal('30.00')
    assert repositorio_vendas.buscar_item(102, 8)['quantidade'] == 1
    assert repositorio_vendas.buscar_item(102, 2) is None


def test_estoque_e_valor_acompanham_cada_alteracao_de_item():
    assert estoque(2) == 20
    assert estoque(4) == 12

    repositorio_vendas.incluir_item({'numero_venda': 104, 'cod_produto': 2, 'quantidade': 3})
    assert estoque(2) == 17
    assert valor(104) == Decimal('119.70')

    repositorio_vendas.alterar_quantidade_do_item({'numero_venda': 104, 'cod_produto': 2, 'quantidade': 5})
    assert estoque(2) == 15
    assert valor(104) == Decimal('199.50')

    repositorio_vendas.alterar_quantidade_do_item({'numero_venda': 104, 'cod_produto': 2, 'quantidade': 2})
    assert estoque(2) == 18
    assert valor(104) == Decimal('79.80')

    repositorio_vendas.trocar_produto_do_item({
        'numero_venda': 104,
        'cod_produto_atual': 2,
        'cod_produto_novo': 4,
        'quantidade': 1,
    })
    assert estoque(2) == 20
    assert estoque(4) == 11
    assert itens_da_venda(104) == {4: (1, Decimal('79.90'))}
    assert valor(104) == Decimal('79.90')

    repositorio_vendas.remover_item(104, 4)
    assert estoque(4) == 12
    assert itens_da_venda(104) == {}
    assert valor(104) == Decimal('0.00')


def test_preco_do_catalogo_nao_altera_vendas_anteriores():
    produto = repositorio_produtos.buscar_produto(1)
    produto['preco'] = Decimal('31.50')
    repositorio_produtos.atualizar_produto(produto)

    assert valor(102) == Decimal('80.00')
    assert itens_da_venda(102)[1] == (2, Decimal('25.00'))

    repositorio_vendas.alterar_quantidade_do_item({'numero_venda': 102, 'cod_produto': 1, 'quantidade': 3})
    assert itens_da_venda(102)[1] == (3, Decimal('25.00'))
    assert valor(102) == Decimal('105.00')

    repositorio_vendas.incluir_item({'numero_venda': 104, 'cod_produto': 1, 'quantidade': 1})
    assert itens_da_venda(104) == {1: (1, Decimal('31.50'))}


def test_item_repetido_e_estoque_insuficiente_recusados():
    with pytest.raises(errors.UniqueViolation):
        repositorio_vendas.incluir_item({'numero_venda': 102, 'cod_produto': 1, 'quantidade': 1})
    with pytest.raises(errors.CheckViolation):
        repositorio_vendas.incluir_item({'numero_venda': 104, 'cod_produto': 7, 'quantidade': 1})
    with pytest.raises(errors.CheckViolation):
        repositorio_vendas.alterar_quantidade_do_item({'numero_venda': 102, 'cod_produto': 8, 'quantidade': 32})
    with pytest.raises(errors.UniqueViolation):
        repositorio_vendas.trocar_produto_do_item({
            'numero_venda': 102,
            'cod_produto_atual': 8,
            'cod_produto_novo': 1,
            'quantidade': 1,
        })

    assert estoque(1) == 40
    assert estoque(7) == 0
    assert estoque(8) == 30
    assert itens_da_venda(102) == {1: (2, Decimal('25.00')), 8: (1, Decimal('30.00'))}
    assert valor(102) == Decimal('80.00')
    assert valor(104) == Decimal('0.00')


def test_cancelamento_devolve_as_unidades_uma_vez():
    repositorio_vendas.cancelar_venda(102)
    repositorio_vendas.cancelar_venda(102)

    assert repositorio_vendas.buscar_venda(102) is None
    assert itens_da_venda(102) == {}
    assert estoque(1) == 42
    assert estoque(8) == 31


def test_disputa_pelas_ultimas_unidades():
    """Duas vendas tentam a última unidade do produto 12 ao mesmo tempo."""
    assert estoque(12) == 1
    resultado_da_segunda = {}

    def segunda_venda():
        try:
            repositorio_vendas.incluir_item({'numero_venda': 105, 'cod_produto': 12, 'quantidade': 1})
            resultado_da_segunda['erro'] = None
        except errors.CheckViolation as erro:
            resultado_da_segunda['erro'] = erro

    with db.transacao() as primeira:
        primeira.execute(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (104, 12, 1, 22.00)
            """
        )
        concorrente = threading.Thread(target=segunda_venda)
        concorrente.start()
        concorrente.join(timeout=3)
        assert concorrente.is_alive(), 'a segunda venda deveria esperar o bloqueio do produto'
    concorrente.join(timeout=30)

    assert not concorrente.is_alive()
    assert isinstance(resultado_da_segunda['erro'], errors.CheckViolation)
    assert estoque(12) == 0
    assert itens_da_venda(104) == {12: (1, Decimal('22.00'))}
    assert 12 not in itens_da_venda(105)
    assert valor(104) == Decimal('22.00')
    assert valor(105) == Decimal('55.00')

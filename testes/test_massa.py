"""Dados iniciais: quantidade mínima, códigos reservados e cenário fixo dos testes."""
import datetime
from decimal import Decimal

import pytest

import db

pytestmark = pytest.mark.usefixtures('banco_recriado')

CONSULTA_DE_CHAVES = {
    'categorias': 'SELECT cod_categoria FROM categorias',
    'fornecedores': 'SELECT cod_fornecedor FROM fornecedores',
    'vendedores': 'SELECT cod_vendedor FROM vendedores',
    'clientes': 'SELECT cod_cliente FROM clientes',
    'produtos': 'SELECT cod_produto FROM produtos',
    'vendas': 'SELECT numero_venda FROM vendas',
    'itens_vendas': 'SELECT numero_venda, cod_produto FROM itens_vendas',
    'fornecimentos': 'SELECT cod_fornecedor, cod_produto FROM fornecimentos',
}

# Venda: (data, cliente, vendedor ou None, valor registrado)
VENDAS_DE_JUNHO = {
    101: (datetime.date(2025, 6, 1), 3, 1, Decimal('25.00')),
    102: (datetime.date(2025, 6, 2), 1, 1, Decimal('80.00')),
    103: (datetime.date(2025, 6, 3), 1, None, Decimal('30.00')),
    104: (datetime.date(2025, 6, 3), 2, None, Decimal('0.00')),
    105: (datetime.date(2025, 6, 8), 3, 1, Decimal('55.00')),
    106: (datetime.date(2025, 6, 9), 3, None, Decimal('25.00')),
}

ESTOQUE_APOS_AS_VENDAS = {
    1: 40, 2: 20, 3: 15, 4: 12, 5: 3, 6: 8, 7: 0, 8: 30,
    9: 6, 10: 24, 11: 18, 12: 1, 13: 10, 14: 8, 15: 35, 16: 25,
}


def ler_vendas():
    sql = """
        SELECT
            numero_venda,
            data_venda,
            cod_cliente,
            cod_vendedor,
            valor
        FROM vendas
    """
    return db.consultar(sql)


def test_pelo_menos_dez_registros_por_tabela():
    for tabela, sql in CONSULTA_DE_CHAVES.items():
        linhas = db.consultar(sql)
        assert len(linhas) >= 10, tabela


def test_codigos_reservados_para_homonimos():
    vendedores = db.consultar(
        """
        SELECT cod_vendedor, nome, cidade
        FROM vendedores
        WHERE cod_vendedor IN (1, 2)
        ORDER BY cod_vendedor
        """
    )
    clientes = db.consultar(
        """
        SELECT cod_cliente, nome, rua_numero, cidade
        FROM clientes
        WHERE cod_cliente IN (1, 2, 3)
        ORDER BY cod_cliente
        """
    )

    assert vendedores == [
        {'cod_vendedor': 1, 'nome': 'Ana Lima', 'cidade': 'Niterói'},
        {'cod_vendedor': 2, 'nome': 'Ana Lima', 'cidade': 'Maricá'},
    ]
    assert clientes[0]['nome'] == 'Lia Costa'
    assert clientes[1]['nome'] == 'Lia Costa'
    assert clientes[0]['rua_numero'] != clientes[1]['rua_numero']
    assert clientes[2]['nome'] == 'Caio Lopes'


def test_fatia_fixa_de_junho_de_2025():
    de_01_a_10_de_junho = {}
    for venda in ler_vendas():
        data = venda['data_venda']
        if datetime.date(2025, 6, 1) <= data <= datetime.date(2025, 6, 10):
            de_01_a_10_de_junho[venda['numero_venda']] = (
                data,
                venda['cod_cliente'],
                venda['cod_vendedor'],
                venda['valor'],
            )

    assert de_01_a_10_de_junho == VENDAS_DE_JUNHO


def test_valor_de_cada_venda_corresponde_aos_itens():
    subtotais = {}
    itens = db.consultar(
        """
        SELECT numero_venda, quantidade, preco_unitario
        FROM itens_vendas
        """
    )
    for item in itens:
        anterior = subtotais.get(item['numero_venda'], Decimal('0.00'))
        subtotais[item['numero_venda']] = anterior + item['quantidade'] * item['preco_unitario']

    for venda in ler_vendas():
        esperado = subtotais.get(venda['numero_venda'], Decimal('0.00'))
        assert venda['valor'] == esperado, venda['numero_venda']
    assert subtotais[102] == Decimal('80.00')
    assert 104 not in subtotais


def test_estoque_apos_as_vendas_iniciais():
    produtos = db.consultar('SELECT cod_produto, qtd_estoque FROM produtos')

    estoque = {}
    for produto in produtos:
        estoque[produto['cod_produto']] = produto['qtd_estoque']
    assert estoque == ESTOQUE_APOS_AS_VENDAS


def test_preco_historico_difere_do_preco_atual():
    item = db.consultar_um(
        """
        SELECT preco_unitario
        FROM itens_vendas
        WHERE numero_venda = 100
          AND cod_produto = 1
        """
    )
    produto = db.consultar_um('SELECT preco FROM produtos WHERE cod_produto = 1')

    assert item['preco_unitario'] == Decimal('22.90')
    assert produto['preco'] == Decimal('25.00')


def test_cadastros_sem_movimento():
    assert db.consultar('SELECT numero_venda FROM vendas WHERE cod_vendedor = 2') == []
    assert db.consultar('SELECT numero_venda FROM vendas WHERE cod_cliente = 11') == []
    assert db.consultar('SELECT numero_venda FROM vendas WHERE cod_cliente = 12') == []
    assert db.consultar('SELECT cod_produto FROM produtos WHERE cod_categoria = 11') == []
    assert db.consultar('SELECT cod_produto FROM fornecimentos WHERE cod_fornecedor = 11') == []
    assert db.consultar('SELECT cod_fornecedor FROM fornecimentos WHERE cod_produto = 16') == []
    assert db.consultar('SELECT numero_venda FROM itens_vendas WHERE cod_produto = 16') == []
    assert db.consultar_valor('SELECT cod_categoria FROM produtos WHERE cod_produto = 16') is None


def test_sequencias_prontas_para_a_proxima_inclusao():
    sql = """
        SELECT sequencename, last_value
        FROM pg_sequences
        WHERE schemaname = 'loja'
    """
    ultimos = {}
    for sequencia in db.consultar(sql):
        ultimos[sequencia['sequencename']] = sequencia['last_value']

    assert ultimos == {
        'categorias_cod_categoria_seq': 11,
        'fornecedores_cod_fornecedor_seq': 11,
        'vendedores_cod_vendedor_seq': 10,
        'clientes_cod_cliente_seq': 12,
        'produtos_cod_produto_seq': 16,
        'vendas_numero_venda_seq': 106,
    }


def test_proxima_chave_gerada_apos_a_carga():
    cod_categoria = db.consultar_valor(
        "INSERT INTO categorias (nome) VALUES ('Lingerie') RETURNING cod_categoria"
    )
    numero_venda = db.consultar_valor(
        """
        INSERT INTO vendas (cod_cliente, data_venda)
        VALUES (12, '2025-06-11')
        RETURNING numero_venda
        """
    )

    assert cod_categoria == 12
    assert numero_venda == 107

"""Repositório de produtos e consultas de estoque, sobre os dados iniciais."""
from decimal import Decimal

import pytest
from psycopg import errors

import db
from repositorios import produtos as repositorio_produtos

pytestmark = pytest.mark.usefixtures('banco_recriado')


def codigos(linhas):
    resultado = []
    for linha in linhas:
        resultado.append(linha['cod_produto'])
    return sorted(resultado)


def ler_produto(cod_produto):
    sql = """
        SELECT descricao, preco, qtd_estoque, estoque_minimo, cod_categoria
        FROM produtos
        WHERE cod_produto = %(cod_produto)s
    """
    return db.consultar_um(sql, {'cod_produto': cod_produto})


def test_cadastro_sem_categoria():
    dados = {
        'descricao': 'Lenço de seda estampado',
        'preco': Decimal('34.90'),
        'qtd_estoque': 6,
        'estoque_minimo': 2,
        'cod_categoria': None,
    }

    cod_produto = repositorio_produtos.cadastrar_produto(dados)

    assert cod_produto == 17
    assert ler_produto(17) == dados


def test_lista_disponiveis_e_abaixo_do_minimo():
    assert codigos(repositorio_produtos.listar_produtos()) == list(range(1, 17))

    disponiveis = codigos(repositorio_produtos.listar_produtos_disponiveis())
    assert 7 not in disponiveis
    assert len(disponiveis) == 15

    assert codigos(repositorio_produtos.listar_produtos_abaixo_do_minimo()) == [7, 12]


def test_ficha_e_codigo_ausente():
    ficha = repositorio_produtos.buscar_produto(16)

    assert ficha == {
        'cod_produto': 16,
        'descricao': 'Sacola retornável de tecido',
        'preco': Decimal('12.00'),
        'qtd_estoque': 25,
        'estoque_minimo': 5,
        'cod_categoria': None,
    }
    assert repositorio_produtos.buscar_produto(999) is None


def test_atualizacao_isolada_e_preco_negativo_recusado():
    produto_1_antes = ler_produto(1)
    dados = {
        'cod_produto': 16,
        'descricao': 'Sacola retornável de algodão cru',
        'preco': Decimal('14.50'),
        'qtd_estoque': 30,
        'estoque_minimo': 5,
        'cod_categoria': 4,
    }

    repositorio_produtos.atualizar_produto(dados)
    dados_invalidos = dict(dados)
    dados_invalidos['preco'] = Decimal('-1.00')
    with pytest.raises(errors.CheckViolation):
        repositorio_produtos.atualizar_produto(dados_invalidos)

    assert ler_produto(16)['preco'] == Decimal('14.50')
    assert ler_produto(16)['cod_categoria'] == 4
    assert ler_produto(1) == produto_1_antes


def test_exclusao_permitida_e_recusas():
    repositorio_produtos.excluir_produto(16)
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_produtos.excluir_produto(1)
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_produtos.excluir_produto(7)

    assert ler_produto(16) is None
    assert ler_produto(1) is not None
    assert ler_produto(7) is not None

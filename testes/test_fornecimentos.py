"""Repositório de fornecimentos (pares fornecedor-produto), sobre os dados iniciais."""
import pytest
from psycopg import errors

import db
from repositorios import fornecimentos as repositorio_fornecimentos

pytestmark = pytest.mark.usefixtures('banco_recriado')


def ler_pares():
    pares = set()
    for linha in db.consultar('SELECT cod_fornecedor, cod_produto FROM fornecimentos'):
        pares.add((linha['cod_fornecedor'], linha['cod_produto']))
    return pares


def test_inclusao_e_consulta_pelas_duas_chaves():
    antes = ler_pares()

    repositorio_fornecimentos.incluir_fornecimento({'cod_fornecedor': 11, 'cod_produto': 16})

    assert ler_pares() == antes | {(11, 16)}
    par = repositorio_fornecimentos.buscar_fornecimento(11, 16)
    assert par['cod_fornecedor'] == 11
    assert par['cod_produto'] == 16
    assert repositorio_fornecimentos.buscar_fornecimento(11, 1) is None


def test_par_repetido_e_referencia_inexistente_recusados():
    antes = ler_pares()

    with pytest.raises(errors.UniqueViolation):
        repositorio_fornecimentos.incluir_fornecimento({'cod_fornecedor': 1, 'cod_produto': 1})
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_fornecimentos.incluir_fornecimento({'cod_fornecedor': 1, 'cod_produto': 999})

    assert ler_pares() == antes


def test_alteracao_troca_somente_o_par_indicado():
    antes = ler_pares()

    repositorio_fornecimentos.alterar_fornecimento({
        'cod_fornecedor_atual': 1,
        'cod_produto_atual': 2,
        'cod_fornecedor': 11,
        'cod_produto': 16,
    })

    assert ler_pares() == (antes - {(1, 2)}) | {(11, 16)}


def test_exclusao_do_par():
    antes = ler_pares()

    repositorio_fornecimentos.excluir_fornecimento(3, 5)
    repositorio_fornecimentos.excluir_fornecimento(11, 16)

    assert ler_pares() == antes - {(3, 5)}


def test_produtos_do_fornecedor_e_fornecedores_do_produto():
    produtos = repositorio_fornecimentos.listar_produtos_do_fornecedor(3)
    fornecedores = repositorio_fornecimentos.listar_fornecedores_do_produto(1)

    codigos_produtos = set()
    for produto in produtos:
        codigos_produtos.add(produto['cod_produto'])
    codigos_fornecedores = set()
    for fornecedor in fornecedores:
        codigos_fornecedores.add(fornecedor['cod_fornecedor'])

    assert codigos_produtos == {1, 2, 5}
    assert codigos_fornecedores == {1, 3}
    assert repositorio_fornecimentos.listar_produtos_do_fornecedor(11) == []
    assert repositorio_fornecimentos.listar_fornecedores_do_produto(16) == []

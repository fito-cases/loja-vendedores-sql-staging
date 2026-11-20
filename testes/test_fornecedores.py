"""Repositório de fornecedores, sobre os dados iniciais."""
import pytest
from psycopg import errors

import db
from repositorios import fornecedores as repositorio_fornecedores

pytestmark = pytest.mark.usefixtures('banco_recriado')


def ler_fornecedores():
    fornecedores = {}
    for linha in db.consultar('SELECT cod_fornecedor, razao_social, cidade, estado FROM fornecedores'):
        fornecedores[linha['cod_fornecedor']] = (linha['razao_social'], linha['cidade'], linha['estado'])
    return fornecedores


def test_cadastro_devolve_a_chave_gerada():
    dados = {'razao_social': 'Linhas Nobres Têxtil Ltda.', 'cidade': 'Juiz de Fora', 'estado': 'MG'}

    cod_fornecedor = repositorio_fornecedores.cadastrar_fornecedor(dados)

    assert cod_fornecedor == 12
    assert ler_fornecedores()[12] == ('Linhas Nobres Têxtil Ltda.', 'Juiz de Fora', 'MG')


def test_lista_e_ficha():
    lista = repositorio_fornecedores.listar_fornecedores()

    assert len(lista) == 11
    assert repositorio_fornecedores.buscar_fornecedor(11) == {
        'cod_fornecedor': 11,
        'razao_social': 'Ateliê Mesa Bonita Ltda.',
        'cidade': 'Nova Friburgo',
        'estado': 'RJ',
    }
    assert repositorio_fornecedores.buscar_fornecedor(999) is None


def test_atualizacao_isolada():
    antes = ler_fornecedores()
    dados = {'cod_fornecedor': 11, 'razao_social': 'Ateliê Mesa Bonita Ltda.', 'cidade': 'Teresópolis', 'estado': 'RJ'}

    repositorio_fornecedores.atualizar_fornecedor(dados)

    esperado = dict(antes)
    esperado[11] = ('Ateliê Mesa Bonita Ltda.', 'Teresópolis', 'RJ')
    assert ler_fornecedores() == esperado


def test_exclusao_permitida_e_recusada():
    repositorio_fornecedores.excluir_fornecedor(11)
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_fornecedores.excluir_fornecedor(1)

    assert set(ler_fornecedores()) == set(range(1, 11))

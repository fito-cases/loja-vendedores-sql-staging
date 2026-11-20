"""Repositório de clientes, sobre os dados iniciais."""
import pytest
from psycopg import errors

import db
from repositorios import clientes as repositorio_clientes

pytestmark = pytest.mark.usefixtures('banco_recriado')

NOVO_CLIENTE = {
    'nome': 'Lia Costa',
    'rua_numero': 'Rua das Hortênsias, 9',
    'bairro': 'Itaipu',
    'cidade': 'Niterói',
    'estado': 'RJ',
    'cep': '24340-000',
    'telefone': None,
}


def ler_cliente(cod_cliente):
    sql = """
        SELECT nome, rua_numero, bairro, cidade, estado, cep, telefone
        FROM clientes
        WHERE cod_cliente = %(cod_cliente)s
    """
    return db.consultar_um(sql, {'cod_cliente': cod_cliente})


def codigos_de_clientes():
    codigos = set()
    for linha in db.consultar('SELECT cod_cliente FROM clientes'):
        codigos.add(linha['cod_cliente'])
    return codigos


def test_cadastro_de_homonimo_sem_telefone():
    cod_cliente = repositorio_clientes.cadastrar_cliente(NOVO_CLIENTE)

    assert cod_cliente == 13
    assert ler_cliente(13) == NOVO_CLIENTE
    assert ler_cliente(1)['nome'] == 'Lia Costa'


def test_lista_e_ficha():
    lista = repositorio_clientes.listar_clientes()
    codigos = []
    for cliente in lista:
        codigos.append(cliente['cod_cliente'])

    assert sorted(codigos) == list(range(1, 13))
    ficha = repositorio_clientes.buscar_cliente(2)
    assert ficha['nome'] == 'Lia Costa'
    assert ficha['cidade'] == 'Maricá'
    assert ficha['telefone'] is None
    assert repositorio_clientes.buscar_cliente(999) is None


def test_atualizacao_isolada():
    cliente_1_antes = ler_cliente(1)
    dados = dict(NOVO_CLIENTE)
    dados['cod_cliente'] = 2
    dados['telefone'] = '(21) 90000-0102'

    repositorio_clientes.atualizar_cliente(dados)

    alterado = ler_cliente(2)
    assert alterado['rua_numero'] == 'Rua das Hortênsias, 9'
    assert alterado['telefone'] == '(21) 90000-0102'
    assert ler_cliente(1) == cliente_1_antes


def test_exclusao_permitida_e_recusada():
    repositorio_clientes.excluir_cliente(12)
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_clientes.excluir_cliente(1)

    assert codigos_de_clientes() == set(range(1, 12))

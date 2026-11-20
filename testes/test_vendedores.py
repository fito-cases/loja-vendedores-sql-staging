"""Cadastro de vendedores: verificações da atividade.

Cada teste chama diretamente uma função de repositorios/vendedores.py e
confere o efeito com leituras independentes, feitas pelo próprio teste em
outras conexões. Nenhum teste usa outra função de vendedores para preparar
ou conferir dados, e nenhum depende da ordem das linhas.

Dados iniciais usados: vendedores 1 e 2 se chamam Ana Lima (Niterói e
Maricá); o vendedor 1 tem vendas e o 2 não tem.
"""
import pytest
from psycopg import errors

import db
from repositorios import vendedores as repositorio_vendedores

pytestmark = pytest.mark.usefixtures('banco_recriado')

ANA_LIMA_DE_NITEROI = {'cod_vendedor': 1, 'nome': 'Ana Lima', 'cidade': 'Niterói'}
ANA_LIMA_DE_MARICA = {'cod_vendedor': 2, 'nome': 'Ana Lima', 'cidade': 'Maricá'}


def ler_linhas_de_vendedores():
    """Leitura independente: todas as linhas da tabela, com repetições, se houver."""
    sql = """
        SELECT cod_vendedor, nome, cidade
        FROM vendedores
    """
    return db.consultar(sql)


def ler_vendedores():
    """Leitura independente: {cod_vendedor: (nome, cidade)}."""
    vendedores = {}
    for linha in ler_linhas_de_vendedores():
        vendedores[linha['cod_vendedor']] = (linha['nome'], linha['cidade'])
    return vendedores


def ler_vendedor(cod_vendedor):
    """Leitura independente de uma linha pela chave."""
    sql = """
        SELECT nome, cidade
        FROM vendedores
        WHERE cod_vendedor = %(cod_vendedor)s
    """
    return db.consultar_um(sql, {'cod_vendedor': cod_vendedor})


def ler_vendedores_das_vendas():
    """Leitura independente: {numero_venda: cod_vendedor} de todas as vendas."""
    vendas = {}
    for linha in db.consultar('SELECT numero_venda, cod_vendedor FROM vendas'):
        vendas[linha['numero_venda']] = linha['cod_vendedor']
    return vendas


def ordenar_por_codigo(fichas):
    """Cópia da lista em ordem de código, para comparar sem depender da ordem."""
    return sorted(fichas, key=lambda ficha: ficha['cod_vendedor'])


def test_inclusao_persistida():
    """Cadastro: inclusão persistida com chave devolvida"""
    antes = ler_vendedores()

    primeira = repositorio_vendedores.cadastrar_vendedor({'nome': 'Ana Lima', 'cidade': 'São Gonçalo'})
    depois_da_primeira = ler_vendedores()
    segunda = repositorio_vendedores.cadastrar_vendedor({'nome': 'Ana Lima', 'cidade': 'Itaboraí'})
    depois_da_segunda = ler_vendedores()

    assert isinstance(primeira, int)
    assert isinstance(segunda, int)
    assert primeira != segunda
    assert len(ler_linhas_de_vendedores()) == len(antes) + 2
    assert set(depois_da_primeira) - set(antes) == {primeira}
    assert set(depois_da_segunda) - set(depois_da_primeira) == {segunda}
    assert ler_vendedor(primeira) == {'nome': 'Ana Lima', 'cidade': 'São Gonçalo'}
    assert ler_vendedor(segunda) == {'nome': 'Ana Lima', 'cidade': 'Itaboraí'}
    for cod_vendedor, ficha in antes.items():
        assert depois_da_segunda[cod_vendedor] == ficha


def test_lista_e_ficha():
    """Cadastro: listagem e consulta individual por código"""
    linhas_da_tabela = ler_linhas_de_vendedores()

    lista = repositorio_vendedores.listar_vendedores()

    assert len(lista) == len(linhas_da_tabela)
    for ficha in lista:
        assert set(ficha) == {'cod_vendedor', 'nome', 'cidade'}
    assert ordenar_por_codigo(lista) == ordenar_por_codigo(linhas_da_tabela)
    assert ANA_LIMA_DE_NITEROI in lista
    assert ANA_LIMA_DE_MARICA in lista

    assert repositorio_vendedores.buscar_vendedor(1) == ANA_LIMA_DE_NITEROI
    assert repositorio_vendedores.buscar_vendedor(2) == ANA_LIMA_DE_MARICA
    for ficha in lista:
        assert repositorio_vendedores.buscar_vendedor(ficha['cod_vendedor']) == ficha
    assert repositorio_vendedores.buscar_vendedor(999) is None

    # Subcaso: sem nenhum vendedor cadastrado, a lista é vazia.
    db.executar('UPDATE vendas SET cod_vendedor = NULL WHERE cod_vendedor IS NOT NULL')
    db.executar('DELETE FROM vendedores')
    assert repositorio_vendedores.listar_vendedores() == []


def test_edicao_isolada():
    """Cadastro: edição isolada do vendedor solicitado"""
    antes = ler_vendedores()

    repositorio_vendedores.atualizar_vendedor({'cod_vendedor': 2, 'nome': 'Ana Lima', 'cidade': 'Rio de Janeiro'})
    depois_da_cidade = ler_vendedores()
    repositorio_vendedores.atualizar_vendedor({'cod_vendedor': 2, 'nome': 'Ana Lima Souza', 'cidade': 'Saquarema'})
    depois_do_nome = ler_vendedores()
    repositorio_vendedores.atualizar_vendedor({'cod_vendedor': 999, 'nome': 'Ninguém', 'cidade': 'Lugar nenhum'})
    depois_do_codigo_ausente = ler_vendedores()

    esperado = dict(antes)
    esperado[2] = ('Ana Lima', 'Rio de Janeiro')
    assert depois_da_cidade == esperado
    esperado[2] = ('Ana Lima Souza', 'Saquarema')
    assert depois_do_nome == esperado
    assert depois_do_codigo_ausente == esperado
    assert depois_do_nome[1] == ('Ana Lima', 'Niterói')
    assert len(ler_linhas_de_vendedores()) == len(antes)


def test_exclusao_isolada():
    """Cadastro: exclusão isolada quando permitida"""
    antes = ler_vendedores()

    repositorio_vendedores.excluir_vendedor(2)
    depois = ler_vendedores()

    assert set(antes) - set(depois) == {2}
    assert set(depois) - set(antes) == set()
    assert depois[1] == ('Ana Lima', 'Niterói')

    repositorio_vendedores.excluir_vendedor(999)
    assert ler_vendedores() == depois

    vendas_antes = ler_vendedores_das_vendas()
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_vendedores.excluir_vendedor(1)
    assert ler_vendedores() == depois
    assert ler_vendedores_das_vendas() == vendas_antes

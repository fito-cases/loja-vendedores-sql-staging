"""Repositório de categorias (exemplo completo), sobre os dados iniciais."""
import pytest
from psycopg import errors

import db
from repositorios import categorias as repositorio_categorias

pytestmark = pytest.mark.usefixtures('banco_recriado')


def ler_categorias():
    """Leitura independente do repositório: {código: nome}."""
    categorias = {}
    for linha in db.consultar('SELECT cod_categoria, nome FROM categorias'):
        categorias[linha['cod_categoria']] = linha['nome']
    return categorias


def test_cadastro_devolve_a_chave_gerada():
    antes = ler_categorias()

    cod_categoria = repositorio_categorias.cadastrar_categoria({'nome': 'Moda praia'})

    depois = ler_categorias()
    assert cod_categoria == 12
    assert len(depois) == len(antes) + 1
    assert depois[cod_categoria] == 'Moda praia'


def test_lista_e_busca_por_codigo():
    lista = repositorio_categorias.listar_categorias()

    assert len(lista) == 11
    assert lista[0] == {'cod_categoria': 8, 'nome': 'Banho'}
    assert repositorio_categorias.buscar_categoria(11) == {'cod_categoria': 11, 'nome': 'Pijamas'}
    assert repositorio_categorias.buscar_categoria(999) is None


def test_atualizacao_altera_somente_a_categoria_indicada():
    antes = ler_categorias()

    repositorio_categorias.atualizar_categoria({'cod_categoria': 11, 'nome': 'Pijamas e roupões'})
    repositorio_categorias.atualizar_categoria({'cod_categoria': 999, 'nome': 'Inexistente'})

    esperado = dict(antes)
    esperado[11] = 'Pijamas e roupões'
    assert ler_categorias() == esperado


def test_exclusao_isolada_e_recusa_de_categoria_com_produtos():
    antes = ler_categorias()

    repositorio_categorias.excluir_categoria(11)
    repositorio_categorias.excluir_categoria(999)
    with pytest.raises(errors.ForeignKeyViolation):
        repositorio_categorias.excluir_categoria(1)

    esperado = dict(antes)
    del esperado[11]
    assert ler_categorias() == esperado

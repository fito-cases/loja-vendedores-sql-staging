"""Repositório de categorias.

Exemplo completo e pequeno do padrão dos repositórios: cada função tem um
comando SQL com parâmetros nomeados (%(nome)s), e os valores seguem em um
dicionário separado, nunca colados no texto do SQL.
"""
import db


def cadastrar_categoria(dados):
    """Inclui uma categoria.

    dados: dicionário com 'nome' (texto).
    Retorna o cod_categoria (inteiro) gerado pelo banco para a nova linha.
    """
    sql = """
        INSERT INTO categorias (nome)
        VALUES (%(nome)s)
        RETURNING cod_categoria
    """
    return db.consultar_valor(sql, dados)


def listar_categorias():
    """Retorna todas as categorias, em ordem de nome.

    Cada item é um dicionário com 'cod_categoria' e 'nome'; sem categorias, [].
    """
    sql = """
        SELECT
            cod_categoria,
            nome
        FROM categorias
        ORDER BY nome
    """
    return db.consultar(sql)


def buscar_categoria(cod_categoria):
    """Retorna a categoria do código informado ou None, se ela não existir.

    O dicionário tem 'cod_categoria' e 'nome'.
    """
    sql = """
        SELECT
            cod_categoria,
            nome
        FROM categorias
        WHERE cod_categoria = %(cod_categoria)s
    """
    return db.consultar_um(sql, {'cod_categoria': cod_categoria})


def atualizar_categoria(dados):
    """Grava o novo nome da categoria indicada por 'cod_categoria'.

    dados: dicionário com 'cod_categoria' (inteiro) e 'nome' (texto).
    Código inexistente não altera nenhuma linha. Retorna None.
    """
    sql = """
        UPDATE categorias
        SET nome = %(nome)s
        WHERE cod_categoria = %(cod_categoria)s
    """
    db.executar(sql, dados)


def excluir_categoria(cod_categoria):
    """Exclui a categoria do código informado. Retorna None.

    Código inexistente não remove nenhuma linha. Se houver produtos na
    categoria, o banco recusa a exclusão e o erro chega à rota.
    """
    sql = """
        DELETE FROM categorias
        WHERE cod_categoria = %(cod_categoria)s
    """
    db.executar(sql, {'cod_categoria': cod_categoria})

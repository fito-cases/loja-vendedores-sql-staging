"""Repositório de fornecimentos: quais fornecedores oferecem quais produtos.

Cada par (cod_fornecedor, cod_produto) é identificado pelas duas chaves.
"""
import db


def incluir_fornecimento(dados):
    """Vincula um produto a um fornecedor. Retorna None.

    dados: dicionário com 'cod_fornecedor' e 'cod_produto' (inteiros).
    Se o par já existir, o banco recusa a repetição.
    """
    sql = """
        INSERT INTO fornecimentos (
            cod_fornecedor,
            cod_produto
        )
        VALUES (
            %(cod_fornecedor)s,
            %(cod_produto)s
        )
    """
    db.executar(sql, dados)


def buscar_fornecimento(cod_fornecedor, cod_produto):
    """Retorna o par informado (com a data do vínculo) ou None."""
    sql = """
        SELECT
            cod_fornecedor,
            cod_produto,
            created_at
        FROM fornecimentos
        WHERE cod_fornecedor = %(cod_fornecedor)s
          AND cod_produto = %(cod_produto)s
    """
    parametros = {'cod_fornecedor': cod_fornecedor, 'cod_produto': cod_produto}
    return db.consultar_um(sql, parametros)


def alterar_fornecimento(dados):
    """Troca o fornecedor e/ou o produto de um par existente. Retorna None.

    dados: 'cod_fornecedor_atual' e 'cod_produto_atual' identificam o par;
    'cod_fornecedor' e 'cod_produto' são os novos valores.
    """
    sql = """
        UPDATE fornecimentos
        SET
            cod_fornecedor = %(cod_fornecedor)s,
            cod_produto = %(cod_produto)s
        WHERE cod_fornecedor = %(cod_fornecedor_atual)s
          AND cod_produto = %(cod_produto_atual)s
    """
    db.executar(sql, dados)


def excluir_fornecimento(cod_fornecedor, cod_produto):
    """Desfaz o vínculo do par informado. Retorna None."""
    sql = """
        DELETE FROM fornecimentos
        WHERE cod_fornecedor = %(cod_fornecedor)s
          AND cod_produto = %(cod_produto)s
    """
    parametros = {'cod_fornecedor': cod_fornecedor, 'cod_produto': cod_produto}
    db.executar(sql, parametros)


def listar_produtos_do_fornecedor(cod_fornecedor):
    """Retorna 'cod_produto' e 'descricao' dos produtos vinculados ao fornecedor."""
    sql = """
        SELECT
            cod_produto,
            descricao
        FROM produtos
        WHERE cod_produto IN (
            SELECT cod_produto
            FROM fornecimentos
            WHERE cod_fornecedor = %(cod_fornecedor)s
        )
        ORDER BY descricao
    """
    return db.consultar(sql, {'cod_fornecedor': cod_fornecedor})


def listar_fornecedores_do_produto(cod_produto):
    """Retorna 'cod_fornecedor' e 'razao_social' dos fornecedores do produto."""
    sql = """
        SELECT
            cod_fornecedor,
            razao_social
        FROM fornecedores
        WHERE cod_fornecedor IN (
            SELECT cod_fornecedor
            FROM fornecimentos
            WHERE cod_produto = %(cod_produto)s
        )
        ORDER BY razao_social
    """
    return db.consultar(sql, {'cod_produto': cod_produto})

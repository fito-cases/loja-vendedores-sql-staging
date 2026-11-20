"""Repositório de produtos (cadastro e consultas de estoque)."""
import db


def cadastrar_produto(dados):
    """Inclui um produto.

    dados: dicionário com 'descricao' (texto), 'preco' (Decimal),
    'qtd_estoque' e 'estoque_minimo' (inteiros) e 'cod_categoria'
    (inteiro ou None, para produto sem categoria).
    Retorna o cod_produto (inteiro) gerado para a nova linha.
    """
    sql = """
        INSERT INTO produtos (
            descricao,
            preco,
            qtd_estoque,
            estoque_minimo,
            cod_categoria
        )
        VALUES (
            %(descricao)s,
            %(preco)s,
            %(qtd_estoque)s,
            %(estoque_minimo)s,
            %(cod_categoria)s
        )
        RETURNING cod_produto
    """
    return db.consultar_valor(sql, dados)


def listar_produtos():
    """Retorna todos os produtos, em ordem de descrição."""
    sql = """
        SELECT
            cod_produto,
            descricao,
            preco,
            qtd_estoque,
            estoque_minimo
        FROM produtos
        ORDER BY descricao
    """
    return db.consultar(sql)


def listar_produtos_disponiveis():
    """Retorna os produtos com pelo menos uma unidade em estoque."""
    sql = """
        SELECT
            cod_produto,
            descricao,
            preco,
            qtd_estoque,
            estoque_minimo
        FROM produtos
        WHERE qtd_estoque > 0
        ORDER BY descricao
    """
    return db.consultar(sql)


def listar_produtos_abaixo_do_minimo():
    """Retorna os produtos cujo estoque está abaixo do estoque mínimo."""
    sql = """
        SELECT
            cod_produto,
            descricao,
            preco,
            qtd_estoque,
            estoque_minimo
        FROM produtos
        WHERE qtd_estoque < estoque_minimo
        ORDER BY descricao
    """
    return db.consultar(sql)


def buscar_produto(cod_produto):
    """Retorna a ficha do produto ou None, se o código não existir."""
    sql = """
        SELECT
            cod_produto,
            descricao,
            preco,
            qtd_estoque,
            estoque_minimo,
            cod_categoria
        FROM produtos
        WHERE cod_produto = %(cod_produto)s
    """
    return db.consultar_um(sql, {'cod_produto': cod_produto})


def atualizar_produto(dados):
    """Grava os dados do produto indicado por 'cod_produto'. Retorna None.

    dados: os mesmos campos de cadastrar_produto, mais 'cod_produto'.
    Mudar o preço não altera vendas anteriores: cada item guarda o seu preço.
    """
    sql = """
        UPDATE produtos
        SET
            descricao = %(descricao)s,
            preco = %(preco)s,
            qtd_estoque = %(qtd_estoque)s,
            estoque_minimo = %(estoque_minimo)s,
            cod_categoria = %(cod_categoria)s
        WHERE cod_produto = %(cod_produto)s
    """
    db.executar(sql, dados)


def excluir_produto(cod_produto):
    """Exclui o produto. Se ele estiver em vendas ou fornecimentos, o banco recusa."""
    sql = """
        DELETE FROM produtos
        WHERE cod_produto = %(cod_produto)s
    """
    db.executar(sql, {'cod_produto': cod_produto})

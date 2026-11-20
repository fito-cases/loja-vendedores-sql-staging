"""Repositório de vendas e de seus itens.

O valor da venda nunca vem do formulário: os gatilhos do banco o recalculam
a cada item incluído, alterado ou removido, e também ajustam o estoque.
"""
import db


# Cabeçalho da venda ------------------------------------------------------------

def abrir_venda(dados):
    """Abre uma venda sem itens, com valor zero.

    dados: dicionário com 'cod_cliente' (inteiro), 'cod_vendedor' (inteiro ou
    None, para venda sem vendedor identificado) e 'data_venda' (date).
    Retorna o numero_venda (inteiro) gerado para a nova venda.
    """
    sql = """
        INSERT INTO vendas (
            cod_cliente,
            cod_vendedor,
            data_venda
        )
        VALUES (
            %(cod_cliente)s,
            %(cod_vendedor)s,
            %(data_venda)s
        )
        RETURNING numero_venda
    """
    return db.consultar_valor(sql, dados)


def listar_vendas():
    """Retorna número, data e valor de todas as vendas, das mais novas às mais antigas."""
    sql = """
        SELECT
            numero_venda,
            data_venda,
            valor
        FROM vendas
        ORDER BY numero_venda DESC
    """
    return db.consultar(sql)


def listar_vendas_do_cliente(cod_cliente):
    """Retorna número, data e valor das vendas de um cliente."""
    sql = """
        SELECT
            numero_venda,
            data_venda,
            valor
        FROM vendas
        WHERE cod_cliente = %(cod_cliente)s
        ORDER BY numero_venda DESC
    """
    return db.consultar(sql, {'cod_cliente': cod_cliente})


def buscar_venda(numero_venda):
    """Retorna o cabeçalho da venda ou None.

    Campos: 'numero_venda', 'cod_cliente', 'cod_vendedor' (None se ausente),
    'data_venda' e 'valor'.
    """
    sql = """
        SELECT
            numero_venda,
            cod_cliente,
            cod_vendedor,
            data_venda,
            valor
        FROM vendas
        WHERE numero_venda = %(numero_venda)s
    """
    return db.consultar_um(sql, {'numero_venda': numero_venda})


def atualizar_venda(dados):
    """Grava cliente, vendedor e data da venda indicada. Retorna None.

    dados: 'numero_venda', 'cod_cliente', 'cod_vendedor' (ou None) e
    'data_venda'. O valor não é alterado aqui.
    """
    sql = """
        UPDATE vendas
        SET
            cod_cliente = %(cod_cliente)s,
            cod_vendedor = %(cod_vendedor)s,
            data_venda = %(data_venda)s
        WHERE numero_venda = %(numero_venda)s
    """
    db.executar(sql, dados)


def cancelar_venda(numero_venda):
    """Exclui a venda e seus itens em uma única transação. Retorna None.

    Os itens saem primeiro: o gatilho devolve as unidades ao estoque uma
    única vez. Se algo falhar, nada é excluído.
    """
    sql_itens = """
        DELETE FROM itens_vendas
        WHERE numero_venda = %(numero_venda)s
    """
    sql_venda = """
        DELETE FROM vendas
        WHERE numero_venda = %(numero_venda)s
    """
    parametros = {'numero_venda': numero_venda}
    with db.transacao() as conexao:
        conexao.execute(sql_itens, parametros)
        conexao.execute(sql_venda, parametros)


def listar_opcoes_de_vendedor():
    """Opções para o campo vendedor da venda: 'cod_vendedor' e 'rotulo'.

    O rótulo junta nome e cidade para distinguir vendedores com o mesmo nome.
    """
    sql = """
        SELECT
            cod_vendedor,
            nome || ' (' || cidade || ')' AS rotulo
        FROM vendedores
        ORDER BY nome, cidade, cod_vendedor
    """
    return db.consultar(sql)


# Itens da venda ----------------------------------------------------------------

def listar_itens(numero_venda):
    """Retorna os itens da venda com a descrição do produto e o subtotal.

    Campos: 'cod_produto', 'descricao', 'quantidade', 'preco_unitario'
    (preço praticado na venda) e 'subtotal' (quantidade x preço unitário).
    """
    sql = """
        SELECT
            itens_vendas.cod_produto,
            produtos.descricao,
            itens_vendas.quantidade,
            itens_vendas.preco_unitario,
            itens_vendas.quantidade * itens_vendas.preco_unitario AS subtotal
        FROM itens_vendas
        INNER JOIN produtos
            ON produtos.cod_produto = itens_vendas.cod_produto
        WHERE itens_vendas.numero_venda = %(numero_venda)s
        ORDER BY produtos.descricao
    """
    return db.consultar(sql, {'numero_venda': numero_venda})


def buscar_item(numero_venda, cod_produto):
    """Retorna o item (numero_venda, cod_produto, quantidade, preco_unitario) ou None."""
    sql = """
        SELECT
            numero_venda,
            cod_produto,
            quantidade,
            preco_unitario
        FROM itens_vendas
        WHERE numero_venda = %(numero_venda)s
          AND cod_produto = %(cod_produto)s
    """
    parametros = {'numero_venda': numero_venda, 'cod_produto': cod_produto}
    return db.consultar_um(sql, parametros)


def incluir_item(dados):
    """Inclui um produto na venda, pelo preço atual do produto. Retorna None.

    dados: 'numero_venda', 'cod_produto' e 'quantidade' (inteiros).
    O banco recusa produto repetido na venda e quantidade acima do estoque.
    """
    sql = """
        INSERT INTO itens_vendas (
            numero_venda,
            cod_produto,
            quantidade,
            preco_unitario
        )
        VALUES (
            %(numero_venda)s,
            %(cod_produto)s,
            %(quantidade)s,
            (SELECT preco FROM produtos WHERE cod_produto = %(cod_produto)s)
        )
    """
    db.executar(sql, dados)


def alterar_quantidade_do_item(dados):
    """Muda a quantidade de um item, mantendo o preço praticado. Retorna None.

    dados: 'numero_venda', 'cod_produto' e a nova 'quantidade'.
    """
    sql = """
        UPDATE itens_vendas
        SET quantidade = %(quantidade)s
        WHERE numero_venda = %(numero_venda)s
          AND cod_produto = %(cod_produto)s
    """
    db.executar(sql, dados)


def trocar_produto_do_item(dados):
    """Troca o produto de um item, com o preço atual do novo produto. Retorna None.

    dados: 'numero_venda', 'cod_produto_atual', 'cod_produto_novo' e
    'quantidade'. O gatilho devolve o produto anterior ao estoque e baixa o novo.
    """
    sql = """
        UPDATE itens_vendas
        SET
            cod_produto = %(cod_produto_novo)s,
            quantidade = %(quantidade)s,
            preco_unitario = (SELECT preco FROM produtos WHERE cod_produto = %(cod_produto_novo)s)
        WHERE numero_venda = %(numero_venda)s
          AND cod_produto = %(cod_produto_atual)s
    """
    db.executar(sql, dados)


def remover_item(numero_venda, cod_produto):
    """Remove o item da venda; as unidades voltam ao estoque. Retorna None."""
    sql = """
        DELETE FROM itens_vendas
        WHERE numero_venda = %(numero_venda)s
          AND cod_produto = %(cod_produto)s
    """
    parametros = {'numero_venda': numero_venda, 'cod_produto': cod_produto}
    db.executar(sql, parametros)

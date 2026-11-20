"""Repositório de clientes."""
import db


def cadastrar_cliente(dados):
    """Inclui um cliente.

    dados: dicionário com 'nome', 'rua_numero', 'bairro', 'cidade', 'estado'
    (sigla), 'cep' e 'telefone' (texto ou None).
    Retorna o cod_cliente (inteiro) gerado para a nova linha.
    """
    sql = """
        INSERT INTO clientes (
            nome,
            rua_numero,
            bairro,
            cidade,
            estado,
            cep,
            telefone
        )
        VALUES (
            %(nome)s,
            %(rua_numero)s,
            %(bairro)s,
            %(cidade)s,
            %(estado)s,
            %(cep)s,
            %(telefone)s
        )
        RETURNING cod_cliente
    """
    return db.consultar_valor(sql, dados)


def listar_clientes():
    """Retorna todos os clientes, em ordem de nome e cidade.

    Cada item tem 'cod_cliente', 'nome', 'bairro', 'cidade' e 'telefone'.
    """
    sql = """
        SELECT
            cod_cliente,
            nome,
            bairro,
            cidade,
            telefone
        FROM clientes
        ORDER BY nome, cidade, cod_cliente
    """
    return db.consultar(sql)


def buscar_cliente(cod_cliente):
    """Retorna a ficha completa do cliente ou None, se o código não existir."""
    sql = """
        SELECT
            cod_cliente,
            nome,
            rua_numero,
            bairro,
            cidade,
            estado,
            cep,
            telefone
        FROM clientes
        WHERE cod_cliente = %(cod_cliente)s
    """
    return db.consultar_um(sql, {'cod_cliente': cod_cliente})


def atualizar_cliente(dados):
    """Grava os dados do cliente indicado por 'cod_cliente'. Retorna None.

    dados: os mesmos campos de cadastrar_cliente, mais 'cod_cliente'.
    """
    sql = """
        UPDATE clientes
        SET
            nome = %(nome)s,
            rua_numero = %(rua_numero)s,
            bairro = %(bairro)s,
            cidade = %(cidade)s,
            estado = %(estado)s,
            cep = %(cep)s,
            telefone = %(telefone)s
        WHERE cod_cliente = %(cod_cliente)s
    """
    db.executar(sql, dados)


def excluir_cliente(cod_cliente):
    """Exclui o cliente. Se ele tiver vendas, o banco recusa. Retorna None."""
    sql = """
        DELETE FROM clientes
        WHERE cod_cliente = %(cod_cliente)s
    """
    db.executar(sql, {'cod_cliente': cod_cliente})

"""Repositório de fornecedores."""
import db


def cadastrar_fornecedor(dados):
    """Inclui um fornecedor.

    dados: dicionário com 'razao_social', 'cidade' e 'estado' (sigla).
    Retorna o cod_fornecedor (inteiro) gerado para a nova linha.
    """
    sql = """
        INSERT INTO fornecedores (
            razao_social,
            cidade,
            estado
        )
        VALUES (
            %(razao_social)s,
            %(cidade)s,
            %(estado)s
        )
        RETURNING cod_fornecedor
    """
    return db.consultar_valor(sql, dados)


def listar_fornecedores():
    """Retorna todos os fornecedores, em ordem de razão social."""
    sql = """
        SELECT
            cod_fornecedor,
            razao_social,
            cidade,
            estado
        FROM fornecedores
        ORDER BY razao_social
    """
    return db.consultar(sql)


def buscar_fornecedor(cod_fornecedor):
    """Retorna o fornecedor do código informado ou None."""
    sql = """
        SELECT
            cod_fornecedor,
            razao_social,
            cidade,
            estado
        FROM fornecedores
        WHERE cod_fornecedor = %(cod_fornecedor)s
    """
    return db.consultar_um(sql, {'cod_fornecedor': cod_fornecedor})


def atualizar_fornecedor(dados):
    """Grava os dados do fornecedor indicado por 'cod_fornecedor'. Retorna None."""
    sql = """
        UPDATE fornecedores
        SET
            razao_social = %(razao_social)s,
            cidade = %(cidade)s,
            estado = %(estado)s
        WHERE cod_fornecedor = %(cod_fornecedor)s
    """
    db.executar(sql, dados)


def excluir_fornecedor(cod_fornecedor):
    """Exclui o fornecedor. Se ele estiver vinculado a produtos, o banco recusa."""
    sql = """
        DELETE FROM fornecedores
        WHERE cod_fornecedor = %(cod_fornecedor)s
    """
    db.executar(sql, {'cod_fornecedor': cod_fornecedor})

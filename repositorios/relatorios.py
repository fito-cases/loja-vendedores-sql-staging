"""Repositório do relatório de vendas por período (área de vendas).

A função deste módulo faz parte da atividade do caso. A rota já converte as
datas do formulário e calcula a semana atual; aqui fica apenas a consulta.
"""
import db


def listar_vendas_periodo(data_inicial, data_final):
    """Retorna as vendas com data_venda entre data_inicial e data_final, inclusive.

    data_inicial, data_final: datas (datetime.date) já convertidas pela rota.
    Retorna uma lista com uma linha por venda (lista vazia se não houver
    vendas no período). Cada linha é um dicionário com:
        'numero_venda': número da venda (inteiro);
        'data_venda': data da venda (date);
        'cliente': nome do cliente da venda (texto);
        'vendedor': nome do vendedor da venda (texto), ou None se a venda
                    não tiver vendedor identificado;
        'valor': valor registrado na venda (Decimal).
    A ordem da lista não faz parte do contrato.
    """
    sql = """
        SELECT
            vendas.numero_venda,
            vendas.data_venda,
            clientes.nome AS cliente,
            vendedores.nome AS vendedor,
            vendas.valor
        FROM vendas
        INNER JOIN clientes
            ON clientes.cod_cliente = vendas.cod_cliente
        LEFT JOIN vendedores
            ON vendedores.cod_vendedor = vendas.cod_vendedor
        WHERE vendas.data_venda >= %(data_inicial)s
          AND vendas.data_venda <= %(data_final)s
        ORDER BY vendas.data_venda, vendas.numero_venda
    """
    parametros = {'data_inicial': data_inicial, 'data_final': data_final}
    return db.consultar(sql, parametros)

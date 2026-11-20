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
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('listar_vendas_periodo ainda não foi implementada.')

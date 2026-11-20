"""Relatório de vendas por período: verificações da atividade.

As datas são explícitas, de junho de 2025; nunca a semana corrente. Os
resultados são comparados por número de venda, sem depender da ordem e sem
eliminar repetições antes de contá-las.

Dados iniciais usados (de 01 a 10/06/2025 só existem estas vendas):
    venda  data   cliente                vendedor          valor
    101    01/06  3 Caio Lopes           1 Ana Lima        25,00
    102    02/06  1 Lia Costa (Niterói)  1 Ana Lima        80,00 (dois produtos)
    103    03/06  1 Lia Costa (Niterói)  sem vendedor      30,00
    104    03/06  2 Lia Costa (Maricá)   sem vendedor       0,00 (sem itens)
    105    08/06  3 Caio Lopes           1 Ana Lima        55,00 (dois produtos)
    106    09/06  3 Caio Lopes           sem vendedor      25,00
O vendedor 2 (outra Ana Lima) não tem vendas. Em 10/06 não há vendas.
"""
import datetime
from decimal import Decimal

import pytest

import db
from repositorios import relatorios as repositorio_relatorios

pytestmark = pytest.mark.usefixtures('banco_recriado')


def junho(dia):
    return datetime.date(2025, 6, dia)


COMPROVANTES = {
    101: {'numero_venda': 101, 'data_venda': junho(1), 'cliente': 'Caio Lopes',
          'vendedor': 'Ana Lima', 'valor': Decimal('25.00')},
    102: {'numero_venda': 102, 'data_venda': junho(2), 'cliente': 'Lia Costa',
          'vendedor': 'Ana Lima', 'valor': Decimal('80.00')},
    103: {'numero_venda': 103, 'data_venda': junho(3), 'cliente': 'Lia Costa',
          'vendedor': None, 'valor': Decimal('30.00')},
    104: {'numero_venda': 104, 'data_venda': junho(3), 'cliente': 'Lia Costa',
          'vendedor': None, 'valor': Decimal('0.00')},
    105: {'numero_venda': 105, 'data_venda': junho(8), 'cliente': 'Caio Lopes',
          'vendedor': 'Ana Lima', 'valor': Decimal('55.00')},
    106: {'numero_venda': 106, 'data_venda': junho(9), 'cliente': 'Caio Lopes',
          'vendedor': None, 'valor': Decimal('25.00')},
}


def numeros(linhas):
    """Números de venda das linhas, com repetições, em ordem crescente."""
    resultado = []
    for linha in linhas:
        assert linha['numero_venda'] is not None, 'o relatório trouxe uma linha sem venda'
        resultado.append(linha['numero_venda'])
    return sorted(resultado)


def campo_por_venda(linhas, campo):
    """{numero_venda: valor do campo} de cada linha."""
    resultado = {}
    for linha in linhas:
        resultado[linha['numero_venda']] = linha[campo]
    return resultado


def test_cliente_e_valor():
    """Relatório: cliente e valor corretos por venda"""
    linhas = repositorio_relatorios.listar_vendas_periodo(junho(2), junho(8))

    assert numeros(linhas) == [102, 103, 104, 105]
    for linha in linhas:
        assert linha == COMPROVANTES[linha['numero_venda']]

    # Lia Costa (cliente 1) tem dois comprovantes na semana; a outra Lia Costa
    # (cliente 2) tem um. Renomeando só o cliente 2, só a venda 104 muda.
    db.executar(
        """
        UPDATE clientes
        SET nome = 'Lia Costa Ramos'
        WHERE cod_cliente = 2
        """
    )
    depois = repositorio_relatorios.listar_vendas_periodo(junho(2), junho(8))

    assert numeros(depois) == [102, 103, 104, 105]
    assert campo_por_venda(depois, 'cliente') == {
        102: 'Lia Costa',
        103: 'Lia Costa',
        104: 'Lia Costa Ramos',
        105: 'Caio Lopes',
    }
    assert campo_por_venda(depois, 'valor') == {
        102: Decimal('80.00'),
        103: Decimal('30.00'),
        104: Decimal('0.00'),
        105: Decimal('55.00'),
    }


def test_vendedor_opcional():
    """Relatório: preservação das vendas sem vendedor"""
    semana = repositorio_relatorios.listar_vendas_periodo(junho(2), junho(8))

    assert numeros(semana) == [102, 103, 104, 105]
    assert campo_por_venda(semana, 'vendedor') == {
        102: 'Ana Lima',
        103: None,
        104: None,
        105: 'Ana Lima',
    }

    # Em 03/06 nenhuma venda tem vendedor: as duas continuam no relatório.
    dia_3 = repositorio_relatorios.listar_vendas_periodo(junho(3), junho(3))
    assert numeros(dia_3) == [103, 104]
    assert campo_por_venda(dia_3, 'vendedor') == {103: None, 104: None}

    # Sem a identificação do vendedor, a venda 102 continua no relatório.
    db.executar(
        """
        UPDATE vendas
        SET cod_vendedor = NULL
        WHERE numero_venda = 102
        """
    )
    sem_identificacao = repositorio_relatorios.listar_vendas_periodo(junho(2), junho(8))
    assert numeros(sem_identificacao) == [102, 103, 104, 105]
    assert campo_por_venda(sem_identificacao, 'vendedor')[102] is None
    assert campo_por_venda(sem_identificacao, 'cliente')[102] == 'Lia Costa'


def test_datas_inclusivas():
    """Relatório: período com as duas datas inclusivas"""
    semana = repositorio_relatorios.listar_vendas_periodo(junho(2), junho(8))

    assert numeros(semana) == [102, 103, 104, 105]
    assert numeros(repositorio_relatorios.listar_vendas_periodo(junho(2), junho(2))) == [102]
    assert numeros(repositorio_relatorios.listar_vendas_periodo(junho(8), junho(8))) == [105]
    assert numeros(repositorio_relatorios.listar_vendas_periodo(junho(3), junho(3))) == [103, 104]
    assert numeros(repositorio_relatorios.listar_vendas_periodo(junho(1), junho(9))) == [101, 102, 103, 104, 105, 106]
    assert numeros(repositorio_relatorios.listar_vendas_periodo(junho(9), junho(10))) == [106]
    assert repositorio_relatorios.listar_vendas_periodo(junho(10), junho(10)) == []

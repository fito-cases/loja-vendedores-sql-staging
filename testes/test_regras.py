"""Funções puras de regras.py (sem banco)."""
import datetime
from decimal import Decimal

import pytest

import regras


def test_decimal_aceita_virgula_ou_ponto_e_limita_casas():
    assert regras.decimal_obrigatorio('25,90', 'Preço', Decimal('999.99')) == Decimal('25.90')
    assert regras.decimal_obrigatorio('25.9', 'Preço', Decimal('999.99')) == Decimal('25.90')
    assert regras.decimal_obrigatorio('0', 'Preço', Decimal('999.99')) == Decimal('0.00')
    for invalido in ('', 'abc', '-0,01', '1000', '1,999', 'NaN', 'Infinity'):
        with pytest.raises(ValueError):
            regras.decimal_obrigatorio(invalido, 'Preço', Decimal('999.99'))


def test_inteiros_e_codigos():
    assert regras.inteiro_obrigatorio(' 7 ', 'Estoque', 0) == 7
    assert regras.codigo_opcional('', 'Vendedor') is None
    assert regras.codigo_opcional('2', 'Vendedor') == 2
    for invalido in ('', '1.5', '-1', '9999999999'):
        with pytest.raises(ValueError):
            regras.inteiro_obrigatorio(invalido, 'Estoque', 0)
    with pytest.raises(ValueError):
        regras.codigo_obrigatorio('0', 'Cliente')


def test_textos_e_sigla():
    assert regras.texto_obrigatorio('  Ana Lima ', 'Nome', 100) == 'Ana Lima'
    assert regras.texto_opcional('   ', 'Telefone', 20) is None
    assert regras.sigla_de_estado('rj', 'Estado') == 'RJ'
    with pytest.raises(ValueError):
        regras.texto_obrigatorio('x' * 101, 'Nome', 100)
    for invalida in ('R', 'R1', 'ÁB', ''):
        with pytest.raises(ValueError):
            regras.sigla_de_estado(invalida, 'Estado')


def test_datas():
    assert regras.data_obrigatoria('2025-06-02', 'Data') == datetime.date(2025, 6, 2)
    assert regras.data_obrigatoria('02/06/2025', 'Data') == datetime.date(2025, 6, 2)
    for invalida in ('', '2025-02-30', '06/02', 'ontem'):
        with pytest.raises(ValueError):
            regras.data_obrigatoria(invalida, 'Data')


def test_semana_de_segunda_a_domingo():
    assert regras.semana_que_contem(datetime.date(2025, 6, 2)) == (datetime.date(2025, 6, 2), datetime.date(2025, 6, 8))
    assert regras.semana_que_contem(datetime.date(2025, 6, 8)) == (datetime.date(2025, 6, 2), datetime.date(2025, 6, 8))
    assert regras.semana_que_contem(datetime.date(2025, 6, 1)) == (datetime.date(2025, 5, 26), datetime.date(2025, 6, 1))
    assert regras.semana_que_contem(datetime.date(2025, 12, 31)) == (datetime.date(2025, 12, 29), datetime.date(2026, 1, 4))


def test_apresentacao_em_reais_e_datas():
    assert regras.formatar_moeda(Decimal('1234.5')) == 'R$ 1.234,50'
    assert regras.formatar_moeda(Decimal('0')) == 'R$ 0,00'
    assert regras.formatar_data(datetime.date(2025, 6, 2)) == '02/06/2025'


def test_recusas_explicadas_em_portugues():
    assert regras.explicar_recusa('estoque_suficiente') == 'Estoque insuficiente para a quantidade pedida.'
    assert regras.explicar_recusa(None) == regras.MENSAGEM_DE_RECUSA_GERAL
    assert regras.explicar_recusa('restricao_desconhecida') == regras.MENSAGEM_DE_RECUSA_GERAL

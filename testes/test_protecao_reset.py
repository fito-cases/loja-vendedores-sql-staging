"""Proteções da recriação do banco e escolha do esquema, sem rede e sem banco.

Todas as configurações abaixo são fictícias. Um espião substitui
psycopg.connect para provar que cada recusa acontece antes de conectar.
"""
import psycopg
import pytest

import db
import recriar_banco

SENHA = 's3nh@-ficticia'
URL_VALIDA = (
    'postgresql://postgres.abcdefghijklmnopqrst:s3nh%40-ficticia'
    '@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require'
)


def ambiente_valido():
    return {
        'BANCO_URL': URL_VALIDA,
        'ESQUEMA_SISTEMA': 'loja',
        'ESQUEMA_TESTES': 'loja_testes',
    }


def preparar_ambiente(monkeypatch, ambiente):
    for nome, valor in ambiente.items():
        monkeypatch.setenv(nome, valor)


@pytest.fixture
def conexoes_abertas(monkeypatch):
    """Espião de psycopg.connect: registra a tentativa e simula falha de rede."""
    chamadas = []

    def conectar_espiao(*argumentos, **opcoes):
        chamadas.append(opcoes)
        raise psycopg.OperationalError('conexão simulada pelo teste')

    monkeypatch.setattr(psycopg, 'connect', conectar_espiao)
    return chamadas


def executar_recriacao(monkeypatch, ambiente):
    """Roda recriar_banco.py como no terminal, com o ambiente fictício."""
    preparar_ambiente(monkeypatch, ambiente)
    return recriar_banco.main()


def test_alvo_valido_e_descrito_sem_senha(monkeypatch):
    preparar_ambiente(monkeypatch, ambiente_valido())

    alvo = recriar_banco.validar_alvo(recriar_banco.ler_variaveis())

    assert alvo['host'] == 'aws-0-sa-east-1.pooler.supabase.com'
    assert alvo['esquema_sistema'] == 'loja'
    assert alvo['esquema_testes'] == 'loja_testes'
    descricao = recriar_banco.descrever_alvo(alvo, 'loja')
    assert SENHA not in descricao
    assert 's3nh%40' not in descricao
    assert 'aws-0-sa-east-1.pooler.supabase.com:5432' in descricao


def test_recriacao_conecta_uma_vez_no_esquema_do_sistema(monkeypatch, conexoes_abertas, capsys):
    codigo = executar_recriacao(monkeypatch, ambiente_valido())

    assert codigo == 1
    assert len(conexoes_abertas) == 1
    assert conexoes_abertas[0]['sslmode'] == 'require'
    assert conexoes_abertas[0]['options'] == '-c search_path=loja'
    saida = capsys.readouterr()
    assert SENHA not in saida.out + saida.err
    assert 'nada foi confirmado' in saida.err


def test_aplicacao_usa_o_sistema_e_testes_usam_o_proprio_esquema(monkeypatch, conexoes_abertas):
    preparar_ambiente(monkeypatch, ambiente_valido())

    monkeypatch.setattr(db, 'modo_de_testes', False)
    assert db.esquema_atual() == 'loja'
    monkeypatch.setattr(db, 'modo_de_testes', True)
    assert db.esquema_atual() == 'loja_testes'
    with pytest.raises(psycopg.OperationalError):
        db.consultar('SELECT 1')
    assert conexoes_abertas[0]['options'] == '-c search_path=loja_testes'


def test_recusa_esquemas_iguais(monkeypatch, conexoes_abertas, capsys):
    ambiente = ambiente_valido()
    ambiente['ESQUEMA_TESTES'] = 'loja'

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []
    assert 'devem ser diferentes' in capsys.readouterr().err


def test_recusa_esquema_public_ou_do_supabase(monkeypatch, conexoes_abertas):
    for reservado in ('public', 'auth', 'storage', 'pg_catalog', 'supabase_functions'):
        ambiente = ambiente_valido()
        ambiente['ESQUEMA_SISTEMA'] = reservado

        codigo = executar_recriacao(monkeypatch, ambiente)

        assert codigo != 0, reservado
    assert conexoes_abertas == []


def test_recusa_nome_de_esquema_invalido_ou_ausente(monkeypatch, conexoes_abertas):
    for invalido in ('', 'Loja', 'loja testes', 'loja;drop', '1loja', '"loja"'):
        ambiente = ambiente_valido()
        ambiente['ESQUEMA_TESTES'] = invalido

        codigo = executar_recriacao(monkeypatch, ambiente)

        assert codigo != 0, invalido
    assert conexoes_abertas == []


def test_recusa_conexao_direta(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = (
        'postgresql://postgres:s3nh%40-ficticia'
        '@db.abcdefghijklmnopqrst.supabase.co:5432/postgres?sslmode=require'
    )

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_servidor_que_nao_e_do_supabase(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = URL_VALIDA.replace('aws-0-sa-east-1.pooler.supabase.com', 'localhost')

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_transaction_pooler(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = URL_VALIDA.replace(':5432/', ':6543/')

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_outro_banco(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = URL_VALIDA.replace('/postgres?', '/producao?')

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_sem_tls(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = URL_VALIDA.replace('sslmode=require', 'sslmode=disable')

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_opcao_extra_na_url(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = URL_VALIDA + '&options=-csearch_path%3Dpublic'

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_url_que_nao_e_uri(monkeypatch, conexoes_abertas, capsys):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = (
        'host=aws-0-sa-east-1.pooler.supabase.com port=5432 '
        'user=postgres.abcdefghijklmnopqrst password=s3nh@-ficticia dbname=postgres'
    )

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []
    assert SENHA not in capsys.readouterr().err


def test_recusa_sem_url(monkeypatch, conexoes_abertas):
    ambiente = ambiente_valido()
    ambiente['BANCO_URL'] = ''

    codigo = executar_recriacao(monkeypatch, ambiente)

    assert codigo != 0
    assert conexoes_abertas == []


def comandos_sem_comentarios(arquivo):
    """Texto do arquivo SQL em maiúsculas, sem os comentários de linha (--)."""
    linhas = []
    for linha in arquivo.read_text(encoding='utf-8').splitlines():
        linhas.append(linha.split('--')[0])
    return '\n'.join(linhas).upper()


def test_sql_da_recriacao_limitado_aos_objetos_da_loja():
    assert len(recriar_banco.ARQUIVOS_SQL) == 2
    for arquivo in recriar_banco.ARQUIVOS_SQL:
        comandos = comandos_sem_comentarios(arquivo)
        assert 'CASCADE' not in comandos
        assert 'SCHEMA' not in comandos
        assert 'DROP DATABASE' not in comandos
        assert 'TRUNCATE' not in comandos
        assert 'PUBLIC.' not in comandos
        assert 'SEARCH_PATH TO' not in comandos

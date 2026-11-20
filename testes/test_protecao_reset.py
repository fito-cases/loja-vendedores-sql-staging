"""Proteções da recriação do banco, verificadas sem rede e sem banco.

Todas as configurações abaixo são fictícias. Um espião substitui
psycopg.connect para provar que cada recusa acontece antes de conectar.
"""
import psycopg
import pytest

import recriar_banco

SENHA = 's3nh@-ficticia'
URL_VALIDA = (
    'postgresql://postgres.abcdefghijklmnopqrst:s3nh%40-ficticia'
    '@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require'
)


def variaveis_validas():
    return {
        'BANCO_URL': URL_VALIDA,
        'PERMITIR_RECRIACAO': 'sim',
    }


@pytest.fixture
def conexoes_abertas(monkeypatch):
    """Espião de psycopg.connect: registra a tentativa e simula falha de rede."""
    chamadas = []

    def conectar_espiao(*argumentos, **opcoes):
        chamadas.append(opcoes)
        raise psycopg.OperationalError('conexão simulada pelo teste')

    monkeypatch.setattr(psycopg, 'connect', conectar_espiao)
    return chamadas


def executar_recriacao(monkeypatch, variaveis):
    """Roda recriar_banco.py como no terminal, com o ambiente fictício."""
    for nome, valor in variaveis.items():
        monkeypatch.setenv(nome, valor)
    return recriar_banco.main()


def test_alvo_valido_e_descrito_sem_senha():
    alvo = recriar_banco.validar_alvo(variaveis_validas())

    assert alvo['host'] == 'aws-0-sa-east-1.pooler.supabase.com'
    assert alvo['porta'] == '5432'
    descricao = recriar_banco.descrever_alvo(alvo)
    assert SENHA not in descricao
    assert 's3nh%40' not in descricao
    assert 'aws-0-sa-east-1.pooler.supabase.com:5432' in descricao


def test_alvo_valido_conecta_uma_vez_com_tls(monkeypatch, conexoes_abertas, capsys):
    codigo = executar_recriacao(monkeypatch, variaveis_validas())

    assert codigo == 1
    assert len(conexoes_abertas) == 1
    assert conexoes_abertas[0]['sslmode'] == 'require'
    saida = capsys.readouterr()
    assert SENHA not in saida.out + saida.err
    assert 'nada foi confirmado' in saida.err


def test_recusa_sem_autorizacao(monkeypatch, conexoes_abertas, capsys):
    variaveis = variaveis_validas()
    variaveis['PERMITIR_RECRIACAO'] = 'nao'

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []
    saida = capsys.readouterr()
    assert 'PERMITIR_RECRIACAO' in saida.err
    assert SENHA not in saida.out + saida.err


def test_recusa_conexao_direta(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = (
        'postgresql://postgres:s3nh%40-ficticia'
        '@db.abcdefghijklmnopqrst.supabase.co:5432/postgres?sslmode=require'
    )

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_servidor_que_nao_e_do_supabase(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = URL_VALIDA.replace('aws-0-sa-east-1.pooler.supabase.com', 'localhost')

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_transaction_pooler(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = URL_VALIDA.replace(':5432/', ':6543/')

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_outro_banco(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = URL_VALIDA.replace('/postgres?', '/producao?')

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_sem_tls(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = URL_VALIDA.replace('sslmode=require', 'sslmode=disable')

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_opcao_extra_na_url(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = URL_VALIDA + '&options=-csearch_path%3Dpublic'

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def test_recusa_url_que_nao_e_uri(monkeypatch, conexoes_abertas, capsys):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = (
        'host=aws-0-sa-east-1.pooler.supabase.com port=5432 '
        'user=postgres.abcdefghijklmnopqrst password=s3nh@-ficticia dbname=postgres'
    )

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []
    assert SENHA not in capsys.readouterr().err


def test_recusa_sem_url(monkeypatch, conexoes_abertas):
    variaveis = variaveis_validas()
    variaveis['BANCO_URL'] = ''

    codigo = executar_recriacao(monkeypatch, variaveis)

    assert codigo != 0
    assert conexoes_abertas == []


def comandos_sem_comentarios(arquivo):
    """Texto do arquivo SQL em maiúsculas, sem os comentários de linha (--)."""
    linhas = []
    for linha in arquivo.read_text(encoding='utf-8').splitlines():
        linhas.append(linha.split('--')[0])
    return '\n'.join(linhas).upper()


def test_sql_da_recriacao_limitado_ao_esquema_loja():
    assert len(recriar_banco.ARQUIVOS_SQL) == 2
    for arquivo in recriar_banco.ARQUIVOS_SQL:
        comandos = comandos_sem_comentarios(arquivo)
        assert 'CASCADE' not in comandos
        assert 'DROP SCHEMA' not in comandos
        assert 'DROP DATABASE' not in comandos
        assert 'TRUNCATE' not in comandos
        assert 'PUBLIC.' not in comandos

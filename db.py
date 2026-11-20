"""Acesso ao banco PostgreSQL da loja (projeto Supabase de exercícios).

Cada função abre uma conexão, executa o comando, confirma (commit) se tudo
deu certo, desfaz (rollback) se houve erro e fecha a conexão. As linhas
voltam como dicionários: {'coluna': valor}.

Para vários comandos que precisam ser confirmados juntos, use transacao():

    with db.transacao() as conexao:
        conexao.execute(primeiro_sql, parametros)
        conexao.execute(segundo_sql, parametros)
"""
import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

load_dotenv()

MODOS_TLS_ACEITOS = ('require', 'verify-ca', 'verify-full')


def ler_url_do_banco():
    """Lê a connection string do .env, sem nunca exibi-la."""
    url = os.environ.get('BANCO_URL', '').strip()
    if url == '':
        raise RuntimeError(
            'BANCO_URL não está configurada. Copie .env.example para .env '
            'e preencha com o Session pooler do seu projeto de exercícios.'
        )
    return url


def escolher_modo_tls(url):
    """Mantém o modo TLS da URL quando ele exige criptografia; senão, exige TLS."""
    modo = conninfo_to_dict(url).get('sslmode')
    if modo in MODOS_TLS_ACEITOS:
        return modo
    return 'require'


@contextmanager
def transacao():
    """Abre uma conexão para um bloco de comandos e a fecha ao final.

    Se o bloco terminar sem erro, tudo é confirmado; se ocorrer um erro,
    tudo é desfeito. O esquema loja vale para todos os comandos do bloco.
    """
    url = ler_url_do_banco()
    with psycopg.connect(
        url,
        sslmode=escolher_modo_tls(url),
        connect_timeout=15,
        row_factory=dict_row,
    ) as conexao:
        conexao.execute('SET LOCAL search_path TO loja')
        yield conexao


def consultar(sql, parametros=None):
    """Executa uma consulta e devolve todas as linhas (lista, talvez vazia)."""
    with transacao() as conexao:
        return conexao.execute(sql, parametros).fetchall()


def consultar_um(sql, parametros=None):
    """Executa uma consulta e devolve a primeira linha, ou None."""
    with transacao() as conexao:
        return conexao.execute(sql, parametros).fetchone()


def consultar_valor(sql, parametros=None):
    """Devolve o valor da primeira coluna da primeira linha, ou None.

    Serve também para INSERT ... RETURNING, que devolve a chave gerada.
    """
    linha = consultar_um(sql, parametros)
    if linha is None:
        return None
    valores = list(linha.values())
    return valores[0]


def executar(sql, parametros=None):
    """Executa um comando que não devolve linhas (INSERT, UPDATE ou DELETE)."""
    with transacao() as conexao:
        conexao.execute(sql, parametros)

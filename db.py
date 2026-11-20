"""Acesso ao banco PostgreSQL da loja (projeto Supabase de exercícios).

Cada função abre uma conexão, executa o comando, confirma (commit) se tudo
deu certo, desfaz (rollback) se houve erro e fecha a conexão. As linhas
voltam como dicionários: {'coluna': valor}.

Para vários comandos que precisam ser confirmados juntos, use transacao():

    with db.transacao() as conexao:
        conexao.execute(primeiro_sql, parametros)
        conexao.execute(segundo_sql, parametros)

As tabelas ficam em um esquema próprio do banco. A aplicação usa o esquema
ESQUEMA_SISTEMA; os testes usam ESQUEMA_TESTES, para nunca apagar os dados
do sistema. Os dois nomes vêm do .env.
"""
import os
import re
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

load_dotenv()

MODOS_TLS_ACEITOS = ('require', 'verify-ca', 'verify-full')
PADRAO_DE_ESQUEMA = re.compile(r'^[a-z][a-z0-9_]{0,62}$')
ESQUEMAS_RESERVADOS = (
    'public', 'information_schema', 'auth', 'storage', 'extensions', 'graphql',
    'graphql_public', 'realtime', 'vault', 'pgsodium', 'pgsodium_masks',
    'pgbouncer', 'net', 'cron',
)

# Os testes chamam usar_esquema_de_testes(); a aplicação nunca chama.
modo_de_testes = False


def ler_url_do_banco():
    """Lê a connection string do .env, sem nunca exibi-la."""
    url = os.environ.get('BANCO_URL', '').strip()
    if url == '':
        raise RuntimeError(
            'BANCO_URL não está configurada. Copie .env.example para .env '
            'e preencha com o Session pooler do seu projeto de exercícios.'
        )
    return url


def conferir_nome_de_esquema(variavel):
    """Lê o nome de esquema da variável do .env e confere se ele é aceitável."""
    nome = os.environ.get(variavel, '').strip()
    if not PADRAO_DE_ESQUEMA.match(nome):
        raise RuntimeError(
            f'{variavel} deve ser um nome de esquema com letras minúsculas, '
            'dígitos e _, começando por letra (ex.: loja).'
        )
    if nome in ESQUEMAS_RESERVADOS or nome.startswith('pg_') or nome.startswith('supabase_'):
        raise RuntimeError(f'{variavel} não pode usar o esquema reservado "{nome}".')
    return nome


def ler_esquemas():
    """Devolve {'sistema': ..., 'testes': ...}, conferindo que são diferentes."""
    sistema = conferir_nome_de_esquema('ESQUEMA_SISTEMA')
    testes = conferir_nome_de_esquema('ESQUEMA_TESTES')
    if sistema == testes:
        raise RuntimeError('ESQUEMA_SISTEMA e ESQUEMA_TESTES devem ser diferentes.')
    return {'sistema': sistema, 'testes': testes}


def usar_esquema_de_testes():
    """Faz todas as conexões seguintes usarem ESQUEMA_TESTES (só nos testes)."""
    global modo_de_testes
    modo_de_testes = True


def esquema_atual():
    """Esquema das conexões: o dos testes durante os testes; senão, o do sistema."""
    esquemas = ler_esquemas()
    if modo_de_testes:
        return esquemas['testes']
    return esquemas['sistema']


def escolher_modo_tls(url):
    """Mantém o modo TLS da URL quando ele exige criptografia; senão, exige TLS."""
    modo = conninfo_to_dict(url).get('sslmode')
    if modo in MODOS_TLS_ACEITOS:
        return modo
    return 'require'


def conectar(url, esquema):
    """Abre uma conexão com TLS cujo search_path é só o esquema informado."""
    return psycopg.connect(
        url,
        sslmode=escolher_modo_tls(url),
        connect_timeout=15,
        options=f'-c search_path={esquema}',
        row_factory=dict_row,
    )


@contextmanager
def transacao():
    """Abre uma conexão para um bloco de comandos e a fecha ao final.

    Se o bloco terminar sem erro, tudo é confirmado; se ocorrer um erro,
    tudo é desfeito.
    """
    with conectar(ler_url_do_banco(), esquema_atual()) as conexao:
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

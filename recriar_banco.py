"""Recria as tabelas e os dados iniciais da loja no projeto Supabase de exercícios.

Uso (no terminal, com o .env preenchido):

    python recriar_banco.py

ATENÇÃO: o comando apaga e recria as oito tabelas do esquema ESQUEMA_SISTEMA,
voltando aos dados iniciais. Os testes usam o mesmo código, mas só no esquema
ESQUEMA_TESTES. Antes de conectar, o programa confere que:
  - BANCO_URL é a URI do Session pooler do Supabase (porta 5432), com o banco
    postgres e TLS, sem opções extras;
  - ESQUEMA_SISTEMA e ESQUEMA_TESTES são nomes simples, diferentes entre si e
    diferentes de public e dos esquemas do próprio Supabase.
Qualquer divergência interrompe o programa sem abrir conexão.
"""
import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

import db

PASTA_SQL = Path(__file__).parent / 'sql'
ARQUIVO_ESTRUTURA = PASTA_SQL / 'schema.sql'
ARQUIVO_DADOS = PASTA_SQL / 'dados.sql'
ARQUIVOS_SQL = [ARQUIVO_ESTRUTURA, ARQUIVO_DADOS]

PADRAO_HOST_SESSION_POOLER = re.compile(
    r'^aws-[0-9]+-[a-z]+-[a-z]+-[0-9]+\.pooler\.supabase\.com$'
)
PORTA_SESSION_POOLER = '5432'
BANCO_DO_PROJETO = 'postgres'
MODOS_TLS_ACEITOS = ('require', 'verify-ca', 'verify-full')
CAMPOS_ACEITOS_NA_URL = (
    'host',
    'port',
    'user',
    'password',
    'dbname',
    'sslmode',
    'sslrootcert',
    'connect_timeout',
    'application_name',
)


def ler_variaveis():
    """Lê do ambiente (e do .env) só a variável da conexão."""
    load_dotenv()
    return {
        'BANCO_URL': os.environ.get('BANCO_URL', ''),
    }


def ler_parametros_da_url(url):
    """Separa a connection string em campos, sem repetir o texto em mensagens."""
    url = url.strip()
    if not url.startswith('postgresql://') and not url.startswith('postgres://'):
        raise ValueError(
            'BANCO_URL deve ser a URI do Session pooler (postgresql://...).'
        )
    try:
        parametros = conninfo_to_dict(url)
    except psycopg.Error:
        raise ValueError('BANCO_URL não é uma URI de conexão válida.') from None
    for campo in parametros:
        if campo not in CAMPOS_ACEITOS_NA_URL:
            raise ValueError(
                f'BANCO_URL contém a opção "{campo}", que não é aceita na recriação.'
            )
    return parametros


def conferir_destino(parametros):
    """Confere host, porta, banco e TLS do Session pooler."""
    host = parametros.get('host', '')
    if not PADRAO_HOST_SESSION_POOLER.match(host):
        raise ValueError(
            'o host de BANCO_URL não é um Session pooler do Supabase '
            '(aws-N-regiao.pooler.supabase.com).'
        )
    if parametros.get('port', '5432') != PORTA_SESSION_POOLER:
        raise ValueError(
            'a porta de BANCO_URL deve ser 5432 (Session pooler); '
            'a porta 6543 é do Transaction pooler.'
        )
    if parametros.get('dbname', BANCO_DO_PROJETO) != BANCO_DO_PROJETO:
        raise ValueError('o banco de BANCO_URL deve ser postgres.')
    if parametros.get('sslmode', 'require') not in MODOS_TLS_ACEITOS:
        raise ValueError(
            'BANCO_URL desativa ou torna opcional o TLS; use sslmode=require.'
        )


def ler_esquemas():
    """Nomes dos dois esquemas, conferidos por db.py."""
    try:
        return db.ler_esquemas()
    except RuntimeError as erro:
        raise ValueError(str(erro)) from None


def validar_alvo(variaveis):
    """Valida o destino antes de qualquer conexão e devolve o alvo conferido.

    Lança ValueError com o motivo da recusa. Nenhuma mensagem contém a senha.
    """
    parametros = ler_parametros_da_url(variaveis['BANCO_URL'])
    conferir_destino(parametros)
    esquemas = ler_esquemas()
    return {
        'url': variaveis['BANCO_URL'].strip(),
        'host': parametros['host'],
        'porta': PORTA_SESSION_POOLER,
        'usuario': parametros.get('user', ''),
        'esquema_sistema': esquemas['sistema'],
        'esquema_testes': esquemas['testes'],
    }


def descrever_alvo(alvo, esquema):
    """Texto do alvo para o terminal, sem senha nem URL completa."""
    return (
        f"Session pooler {alvo['host']}:{alvo['porta']} | usuário {alvo['usuario']} | "
        f"banco {BANCO_DO_PROJETO} | esquema {esquema}"
    )


def ocultar_senha(texto, alvo):
    """Troca a senha por *** caso ela apareça em uma mensagem de erro."""
    senha = conninfo_to_dict(alvo['url']).get('password')
    if senha:
        return texto.replace(senha, '***')
    return texto


def executar_arquivos(alvo, esquema, arquivos):
    """Executa os arquivos SQL no esquema informado, em uma única transação.

    O esquema é criado se ainda não existir. Se algum comando falhar, nada é
    confirmado. Devolve a versão do servidor.
    """
    with db.conectar(alvo['url'], esquema) as conexao:
        conexao.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(esquema)))
        for arquivo in arquivos:
            conexao.execute(arquivo.read_text(encoding='utf-8'))
        linha = conexao.execute('SHOW server_version').fetchone()
    return linha['server_version']


def recriar(alvo, esquema):
    """Recria tabelas, gatilhos e dados iniciais no esquema (schema.sql + dados.sql)."""
    return executar_arquivos(alvo, esquema, [ARQUIVO_ESTRUTURA, ARQUIVO_DADOS])


def criar_estrutura(alvo, esquema):
    """Recria só tabelas e gatilhos, sem dados (schema.sql). Usada pelos testes."""
    return executar_arquivos(alvo, esquema, [ARQUIVO_ESTRUTURA])


def recarregar_dados(alvo, esquema):
    """Apaga as linhas e carrega os dados iniciais (dados.sql). Usada pelos testes."""
    return executar_arquivos(alvo, esquema, [ARQUIVO_DADOS])


def main():
    try:
        alvo = validar_alvo(ler_variaveis())
    except ValueError as erro:
        print(f'Recriação recusada: {erro}', file=sys.stderr)
        return 2
    esquema = alvo['esquema_sistema']
    print(f'Alvo conferido: {descrever_alvo(alvo, esquema)}')
    try:
        versao = recriar(alvo, esquema)
    except psycopg.Error as erro:
        print('Falha ao recriar; nada foi confirmado.', file=sys.stderr)
        print(ocultar_senha(f'{type(erro).__name__}: {erro}', alvo), file=sys.stderr)
        return 1
    print(f'Esquema {esquema} recriado com os dados iniciais (PostgreSQL {versao}).')
    return 0


if __name__ == '__main__':
    sys.exit(main())

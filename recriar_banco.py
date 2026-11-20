"""Recria o esquema loja e os dados iniciais no projeto Supabase de exercícios.

Uso (no terminal, com o .env preenchido):

    python recriar_banco.py

ATENÇÃO: a recriação apaga e recria as oito tabelas do esquema loja. Antes de
conectar, o programa confere que:
  - PERMITIR_RECRIACAO=sim está no .env;
  - BANCO_URL é a URI do Session pooler do Supabase (porta 5432), com o banco
    postgres e TLS, sem opções extras.
Qualquer divergência interrompe o programa sem abrir conexão.
"""
import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict

PASTA_SQL = Path(__file__).parent / 'sql'
ARQUIVOS_SQL = [PASTA_SQL / 'schema.sql', PASTA_SQL / 'dados.sql']

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
    """Lê do ambiente (e do .env) só as variáveis que controlam a recriação."""
    load_dotenv()
    return {
        'BANCO_URL': os.environ.get('BANCO_URL', ''),
        'PERMITIR_RECRIACAO': os.environ.get('PERMITIR_RECRIACAO', ''),
    }


def conferir_autorizacao(variaveis):
    if variaveis['PERMITIR_RECRIACAO'].strip() != 'sim':
        raise ValueError(
            'recriação não autorizada: defina PERMITIR_RECRIACAO=sim no .env '
            'do projeto de exercícios.'
        )


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


def validar_alvo(variaveis):
    """Valida o destino antes de qualquer conexão e devolve o alvo conferido.

    Lança ValueError com o motivo da recusa. Nenhuma mensagem contém a senha.
    """
    conferir_autorizacao(variaveis)
    parametros = ler_parametros_da_url(variaveis['BANCO_URL'])
    conferir_destino(parametros)
    return {
        'url': variaveis['BANCO_URL'].strip(),
        'host': parametros['host'],
        'porta': PORTA_SESSION_POOLER,
        'usuario': parametros.get('user', ''),
        'sslmode': parametros.get('sslmode', 'require'),
    }


def descrever_alvo(alvo):
    """Texto do alvo para o terminal, sem senha nem URL completa."""
    return (
        f"Session pooler {alvo['host']}:{alvo['porta']} | usuário {alvo['usuario']} | "
        f"banco {BANCO_DO_PROJETO} | esquema loja | TLS {alvo['sslmode']}"
    )


def ocultar_senha(texto, alvo):
    """Troca a senha por *** caso ela apareça em uma mensagem de erro."""
    senha = conninfo_to_dict(alvo['url']).get('password')
    if senha:
        return texto.replace(senha, '***')
    return texto


def recriar(alvo):
    """Executa schema.sql e dados.sql em uma única transação no alvo conferido.

    Se algum comando falhar, nada é confirmado. Devolve a versão do servidor.
    """
    with psycopg.connect(
        alvo['url'],
        sslmode=alvo['sslmode'],
        connect_timeout=15,
    ) as conexao:
        for arquivo in ARQUIVOS_SQL:
            conexao.execute(arquivo.read_text(encoding='utf-8'))
        linha = conexao.execute('SHOW server_version').fetchone()
    return linha[0]


def main():
    try:
        alvo = validar_alvo(ler_variaveis())
    except ValueError as erro:
        print(f'Recriação recusada: {erro}', file=sys.stderr)
        return 2
    print(f'Alvo conferido: {descrever_alvo(alvo)}')
    try:
        versao = recriar(alvo)
    except psycopg.Error as erro:
        print('Falha ao recriar; nada foi confirmado.', file=sys.stderr)
        print(ocultar_senha(f'{type(erro).__name__}: {erro}', alvo), file=sys.stderr)
        return 1
    print(f'Esquema loja e dados iniciais recriados (PostgreSQL {versao}).')
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Preparação compartilhada pelos testes.

Durante os testes, todas as conexões de db.py usam o esquema ESQUEMA_TESTES
do .env, nunca o ESQUEMA_SISTEMA usado pela aplicação: rodar os testes não
apaga o que foi feito pelas telas.

Os testes que usam o banco pedem a fixture banco_recriado:
  - na primeira vez, as tabelas e os gatilhos do esquema de testes são
    recriados (schema.sql), uma única vez por execução;
  - antes de CADA teste, os dados iniciais são recarregados (dados.sql).
Isso é necessário porque cada função do repositório abre a própria conexão e
confirma o que grava: desfazer a transação do teste não desfaria essas
gravações.

Sem BANCO_URL e esquemas válidos no .env, os testes de banco terminam em erro,
nunca em sucesso ou em "skipped". Nada aqui acessa o banco durante a
importação ou a coleta dos testes. Rode a suíte em série.
"""
import pytest

import db
import recriar_banco

db.usar_esquema_de_testes()


@pytest.fixture(scope='session')
def estrutura_de_testes():
    """Confere o destino e recria tabelas e gatilhos no esquema de testes."""
    alvo = recriar_banco.validar_alvo(recriar_banco.ler_variaveis())
    recriar_banco.criar_estrutura(alvo, alvo['esquema_testes'])
    return alvo


@pytest.fixture
def banco_recriado(estrutura_de_testes):
    """Recarrega os dados iniciais no esquema de testes antes do teste."""
    alvo = estrutura_de_testes
    recriar_banco.recarregar_dados(alvo, alvo['esquema_testes'])

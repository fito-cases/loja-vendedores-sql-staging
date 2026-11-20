"""Preparação compartilhada pelos testes.

Os testes que usam o banco pedem a fixture banco_recriado. Antes de CADA um
deles, o esquema loja e os dados iniciais são recriados no projeto Supabase de
exercícios pela mesma rotina protegida de recriar_banco.py. Isso é necessário
porque cada função do repositório abre a própria conexão e confirma o que
grava: desfazer a transação do teste não desfaria essas gravações.

Para autorizar, o .env precisa ter PERMITIR_RECRIACAO=sim e BANCO_URL com o
Session pooler do projeto de exercícios. Sem isso, os testes de banco terminam
em erro, nunca em sucesso ou em "skipped".

Nada aqui acessa o banco durante a importação ou a coleta dos testes.
Rode a suíte em série, com a aplicação e outras suítes fechadas.
"""
import pytest

import recriar_banco


@pytest.fixture
def banco_recriado():
    """Recria esquema e dados iniciais na base de exercícios antes do teste."""
    alvo = recriar_banco.validar_alvo(recriar_banco.ler_variaveis())
    recriar_banco.recriar(alvo)

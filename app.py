"""Cria a aplicação Flask da loja e registra as rotas das duas áreas.

Para executar: python -m flask --app app run
"""
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, render_template

import regras
from rotas import categorias
from rotas import clientes
from rotas import fornecedores
from rotas import fornecimentos
from rotas import produtos
from rotas import relatorios
from rotas import vendas
from rotas import vendedores

load_dotenv()


def mostrar_inicio():
    return render_template('inicio.html')


def mostrar_pagina_nao_encontrada(erro):
    mensagem = 'O registro ou a página pedida não existe.'
    return render_template('erro.html', titulo='Não encontrado', mensagem=mensagem), 404


def mostrar_erro_interno(erro):
    mensagem = (
        'Não foi possível concluir a operação. Confira se o arquivo .env aponta '
        'para o projeto de exercícios e se o banco está disponível; os detalhes '
        'ficam no terminal onde a aplicação foi iniciada.'
    )
    return render_template('erro.html', titulo='Erro', mensagem=mensagem), 500


def criar_aplicacao():
    aplicacao = Flask(__name__)
    aplicacao.secret_key = os.environ.get('CHAVE_SECRETA') or secrets.token_hex(16)

    aplicacao.add_template_filter(regras.formatar_moeda, 'moeda')
    aplicacao.add_template_filter(regras.formatar_data, 'data')

    aplicacao.add_url_rule('/', 'inicio', mostrar_inicio)

    # Área de vendas
    aplicacao.register_blueprint(vendas.paginas)
    aplicacao.register_blueprint(clientes.paginas)
    aplicacao.register_blueprint(relatorios.paginas)

    # Área de administração
    aplicacao.register_blueprint(categorias.paginas)
    aplicacao.register_blueprint(produtos.paginas)
    aplicacao.register_blueprint(fornecedores.paginas)
    aplicacao.register_blueprint(fornecimentos.paginas)
    aplicacao.register_blueprint(vendedores.paginas)

    aplicacao.register_error_handler(404, mostrar_pagina_nao_encontrada)
    aplicacao.register_error_handler(500, mostrar_erro_interno)
    return aplicacao


app = criar_aplicacao()

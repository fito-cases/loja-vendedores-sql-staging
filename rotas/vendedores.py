"""Páginas do cadastro de vendedores (área de administração).

As páginas chamam as funções de repositorios/vendedores.py. Enquanto uma
função não estiver implementada, a página correspondente mostra um aviso de
operação indisponível, sem fingir que a operação deu certo.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import vendedores as repositorio_vendedores

paginas = Blueprint('vendedores', __name__, url_prefix='/administracao/vendedores')


def aviso_de_pendencia(nome_da_funcao):
    return (
        f'Operação indisponível: a função {nome_da_funcao}() do repositório '
        'de vendedores ainda não foi implementada.'
    )


def ler_dados_vendedor(formulario):
    """Formulário -> dicionário esperado por cadastrar_vendedor."""
    return {
        'nome': regras.texto_obrigatorio(formulario.get('nome'), 'Nome', 100),
        'cidade': regras.texto_obrigatorio(formulario.get('cidade'), 'Cidade', 70),
    }


def ler_dados_edicao_vendedor(cod_vendedor, formulario):
    """Formulário -> dicionário esperado por atualizar_vendedor."""
    return {
        'cod_vendedor': cod_vendedor,
        'nome': regras.texto_obrigatorio(formulario.get('nome'), 'Nome', 100),
        'cidade': regras.texto_obrigatorio(formulario.get('cidade'), 'Cidade', 70),
    }


def mostrar_formulario(dados, cod_vendedor=None, erro=None, aviso=None):
    return render_template(
        'vendedores/formulario.html',
        dados=dados,
        cod_vendedor=cod_vendedor,
        erro=erro,
        aviso=aviso,
    )


@paginas.get('/')
def lista():
    try:
        vendedores = repositorio_vendedores.listar_vendedores()
    except NotImplementedError:
        aviso = aviso_de_pendencia('listar_vendedores')
        return render_template('vendedores/lista.html', vendedores=None, aviso=aviso)
    return render_template('vendedores/lista.html', vendedores=vendedores)


@paginas.get('/<int:cod_vendedor>')
def ficha(cod_vendedor):
    try:
        vendedor = repositorio_vendedores.buscar_vendedor(cod_vendedor)
    except NotImplementedError:
        aviso = aviso_de_pendencia('buscar_vendedor')
        return render_template('vendedores/ficha.html', vendedor=None, cod_vendedor=cod_vendedor, aviso=aviso)
    if vendedor is None:
        abort(404)
    return render_template('vendedores/ficha.html', vendedor=vendedor, cod_vendedor=cod_vendedor)


@paginas.get('/novo')
def novo():
    return mostrar_formulario({})


@paginas.post('/novo')
def incluir():
    try:
        dados = ler_dados_vendedor(request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, erro=str(erro))
    try:
        cod_vendedor = repositorio_vendedores.cadastrar_vendedor(dados)
    except NotImplementedError:
        return mostrar_formulario(request.form, aviso=aviso_de_pendencia('cadastrar_vendedor'))
    except IntegrityError as erro:
        return mostrar_formulario(request.form, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Vendedor cadastrado.', 'sucesso')
    return redirect(url_for('vendedores.ficha', cod_vendedor=cod_vendedor))


@paginas.get('/<int:cod_vendedor>/editar')
def editar(cod_vendedor):
    try:
        vendedor = repositorio_vendedores.buscar_vendedor(cod_vendedor)
    except NotImplementedError:
        return mostrar_formulario({}, cod_vendedor, aviso=aviso_de_pendencia('buscar_vendedor'))
    if vendedor is None:
        abort(404)
    return mostrar_formulario(vendedor, cod_vendedor)


@paginas.post('/<int:cod_vendedor>/editar')
def salvar(cod_vendedor):
    try:
        dados = ler_dados_edicao_vendedor(cod_vendedor, request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, cod_vendedor, erro=str(erro))
    try:
        repositorio_vendedores.atualizar_vendedor(dados)
    except NotImplementedError:
        return mostrar_formulario(request.form, cod_vendedor, aviso=aviso_de_pendencia('atualizar_vendedor'))
    except IntegrityError as erro:
        return mostrar_formulario(request.form, cod_vendedor, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Vendedor atualizado.', 'sucesso')
    return redirect(url_for('vendedores.ficha', cod_vendedor=cod_vendedor))


@paginas.post('/<int:cod_vendedor>/excluir')
def excluir(cod_vendedor):
    try:
        repositorio_vendedores.excluir_vendedor(cod_vendedor)
    except NotImplementedError:
        flash(aviso_de_pendencia('excluir_vendedor'), 'aviso')
        return redirect(url_for('vendedores.ficha', cod_vendedor=cod_vendedor))
    except IntegrityError:
        flash('Este vendedor não pode ser excluído porque está registrado em vendas.', 'erro')
        return redirect(url_for('vendedores.ficha', cod_vendedor=cod_vendedor))
    flash('Vendedor excluído.', 'sucesso')
    return redirect(url_for('vendedores.lista'))

"""Páginas de categorias (área de administração)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import categorias as repositorio_categorias

paginas = Blueprint('categorias', __name__, url_prefix='/administracao/categorias')


def ler_dados_categoria(formulario):
    """Formulário -> dicionário esperado por cadastrar_categoria."""
    return {
        'nome': regras.texto_obrigatorio(formulario.get('nome'), 'Nome', 50),
    }


def ler_dados_edicao_categoria(cod_categoria, formulario):
    """Formulário -> dicionário esperado por atualizar_categoria."""
    return {
        'cod_categoria': cod_categoria,
        'nome': regras.texto_obrigatorio(formulario.get('nome'), 'Nome', 50),
    }


def buscar_ou_404(cod_categoria):
    categoria = repositorio_categorias.buscar_categoria(cod_categoria)
    if categoria is None:
        abort(404)
    return categoria


def mostrar_formulario(dados, cod_categoria=None, erro=None):
    """Formulário de inclusão (sem código) ou de edição (com código)."""
    return render_template(
        'categorias/formulario.html',
        dados=dados,
        cod_categoria=cod_categoria,
        erro=erro,
    )


@paginas.get('/')
def lista():
    categorias = repositorio_categorias.listar_categorias()
    return render_template('categorias/lista.html', categorias=categorias)


@paginas.get('/<int:cod_categoria>')
def ficha(cod_categoria):
    categoria = buscar_ou_404(cod_categoria)
    return render_template('categorias/ficha.html', categoria=categoria)


@paginas.get('/nova')
def nova():
    return mostrar_formulario({})


@paginas.post('/nova')
def incluir():
    try:
        dados = ler_dados_categoria(request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, erro=str(erro))
    try:
        cod_categoria = repositorio_categorias.cadastrar_categoria(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Categoria cadastrada.', 'sucesso')
    return redirect(url_for('categorias.ficha', cod_categoria=cod_categoria))


@paginas.get('/<int:cod_categoria>/editar')
def editar(cod_categoria):
    categoria = buscar_ou_404(cod_categoria)
    return mostrar_formulario(categoria, cod_categoria)


@paginas.post('/<int:cod_categoria>/editar')
def salvar(cod_categoria):
    try:
        dados = ler_dados_edicao_categoria(cod_categoria, request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, cod_categoria, str(erro))
    try:
        repositorio_categorias.atualizar_categoria(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, cod_categoria, regras.explicar_recusa(erro.diag.constraint_name))
    flash('Categoria atualizada.', 'sucesso')
    return redirect(url_for('categorias.ficha', cod_categoria=cod_categoria))


@paginas.post('/<int:cod_categoria>/excluir')
def excluir(cod_categoria):
    try:
        repositorio_categorias.excluir_categoria(cod_categoria)
    except IntegrityError:
        flash('Esta categoria não pode ser excluída porque há produtos nela.', 'erro')
        return redirect(url_for('categorias.ficha', cod_categoria=cod_categoria))
    flash('Categoria excluída.', 'sucesso')
    return redirect(url_for('categorias.lista'))

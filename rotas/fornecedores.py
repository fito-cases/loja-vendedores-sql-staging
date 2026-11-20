"""Páginas de fornecedores (área de administração)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import fornecedores as repositorio_fornecedores
from repositorios import fornecimentos as repositorio_fornecimentos

paginas = Blueprint('fornecedores', __name__, url_prefix='/administracao/fornecedores')


def ler_dados_fornecedor(formulario):
    """Formulário -> dicionário esperado por cadastrar_fornecedor."""
    return {
        'razao_social': regras.texto_obrigatorio(formulario.get('razao_social'), 'Razão social', 100),
        'cidade': regras.texto_obrigatorio(formulario.get('cidade'), 'Cidade', 70),
        'estado': regras.sigla_de_estado(formulario.get('estado'), 'Estado'),
    }


def ler_dados_edicao_fornecedor(cod_fornecedor, formulario):
    """Formulário -> dicionário esperado por atualizar_fornecedor."""
    dados = ler_dados_fornecedor(formulario)
    dados['cod_fornecedor'] = cod_fornecedor
    return dados


def buscar_ou_404(cod_fornecedor):
    fornecedor = repositorio_fornecedores.buscar_fornecedor(cod_fornecedor)
    if fornecedor is None:
        abort(404)
    return fornecedor


def mostrar_formulario(dados, cod_fornecedor=None, erro=None):
    return render_template(
        'fornecedores/formulario.html',
        dados=dados,
        cod_fornecedor=cod_fornecedor,
        erro=erro,
    )


@paginas.get('/')
def lista():
    fornecedores = repositorio_fornecedores.listar_fornecedores()
    return render_template('fornecedores/lista.html', fornecedores=fornecedores)


@paginas.get('/<int:cod_fornecedor>')
def ficha(cod_fornecedor):
    fornecedor = buscar_ou_404(cod_fornecedor)
    produtos = repositorio_fornecimentos.listar_produtos_do_fornecedor(cod_fornecedor)
    return render_template('fornecedores/ficha.html', fornecedor=fornecedor, produtos=produtos)


@paginas.get('/novo')
def novo():
    return mostrar_formulario({})


@paginas.post('/novo')
def incluir():
    try:
        dados = ler_dados_fornecedor(request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, erro=str(erro))
    try:
        cod_fornecedor = repositorio_fornecedores.cadastrar_fornecedor(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Fornecedor cadastrado.', 'sucesso')
    return redirect(url_for('fornecedores.ficha', cod_fornecedor=cod_fornecedor))


@paginas.get('/<int:cod_fornecedor>/editar')
def editar(cod_fornecedor):
    fornecedor = buscar_ou_404(cod_fornecedor)
    return mostrar_formulario(fornecedor, cod_fornecedor)


@paginas.post('/<int:cod_fornecedor>/editar')
def salvar(cod_fornecedor):
    try:
        dados = ler_dados_edicao_fornecedor(cod_fornecedor, request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, cod_fornecedor, str(erro))
    try:
        repositorio_fornecedores.atualizar_fornecedor(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, cod_fornecedor, regras.explicar_recusa(erro.diag.constraint_name))
    flash('Fornecedor atualizado.', 'sucesso')
    return redirect(url_for('fornecedores.ficha', cod_fornecedor=cod_fornecedor))


@paginas.post('/<int:cod_fornecedor>/excluir')
def excluir(cod_fornecedor):
    try:
        repositorio_fornecedores.excluir_fornecedor(cod_fornecedor)
    except IntegrityError:
        flash('Este fornecedor não pode ser excluído porque está vinculado a produtos.', 'erro')
        return redirect(url_for('fornecedores.ficha', cod_fornecedor=cod_fornecedor))
    flash('Fornecedor excluído.', 'sucesso')
    return redirect(url_for('fornecedores.lista'))

"""Páginas de fornecimentos: vínculos entre fornecedores e produtos (administração)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import fornecedores as repositorio_fornecedores
from repositorios import fornecimentos as repositorio_fornecimentos
from repositorios import produtos as repositorio_produtos

paginas = Blueprint('fornecimentos', __name__, url_prefix='/administracao/fornecimentos')


def ler_dados_fornecimento(cod_fornecedor, formulario):
    """Formulário -> dicionário esperado por incluir_fornecimento."""
    return {
        'cod_fornecedor': cod_fornecedor,
        'cod_produto': regras.codigo_obrigatorio(formulario.get('cod_produto'), 'Produto'),
    }


def ler_dados_alteracao(cod_fornecedor_atual, cod_produto_atual, formulario):
    """Formulário -> dicionário esperado por alterar_fornecimento."""
    return {
        'cod_fornecedor_atual': cod_fornecedor_atual,
        'cod_produto_atual': cod_produto_atual,
        'cod_fornecedor': regras.codigo_obrigatorio(formulario.get('cod_fornecedor'), 'Fornecedor'),
        'cod_produto': regras.codigo_obrigatorio(formulario.get('cod_produto'), 'Produto'),
    }


def buscar_fornecedor_ou_404(cod_fornecedor):
    fornecedor = repositorio_fornecedores.buscar_fornecedor(cod_fornecedor)
    if fornecedor is None:
        abort(404)
    return fornecedor


def mostrar_produtos_do_fornecedor(fornecedor, escolhido=None, erro=None):
    produtos_vinculados = repositorio_fornecimentos.listar_produtos_do_fornecedor(fornecedor['cod_fornecedor'])
    todos_os_produtos = repositorio_produtos.listar_produtos()
    return render_template(
        'fornecimentos/do_fornecedor.html',
        fornecedor=fornecedor,
        produtos_vinculados=produtos_vinculados,
        todos_os_produtos=todos_os_produtos,
        escolhido=escolhido,
        erro=erro,
    )


def mostrar_par(cod_fornecedor, cod_produto, dados=None, erro=None):
    """Ficha de um par: nomes das duas pontas e formulário de alteração."""
    fornecimento = repositorio_fornecimentos.buscar_fornecimento(cod_fornecedor, cod_produto)
    if fornecimento is None:
        abort(404)
    if dados is None:
        dados = fornecimento
    return render_template(
        'fornecimentos/ficha.html',
        fornecimento=fornecimento,
        fornecedor=repositorio_fornecedores.buscar_fornecedor(cod_fornecedor),
        produto=repositorio_produtos.buscar_produto(cod_produto),
        fornecedores=repositorio_fornecedores.listar_fornecedores(),
        produtos=repositorio_produtos.listar_produtos(),
        dados=dados,
        erro=erro,
    )


@paginas.get('/')
def lista():
    fornecedores = repositorio_fornecedores.listar_fornecedores()
    return render_template('fornecimentos/lista.html', fornecedores=fornecedores)


@paginas.get('/fornecedor/<int:cod_fornecedor>')
def do_fornecedor(cod_fornecedor):
    fornecedor = buscar_fornecedor_ou_404(cod_fornecedor)
    return mostrar_produtos_do_fornecedor(fornecedor)


@paginas.post('/fornecedor/<int:cod_fornecedor>')
def incluir(cod_fornecedor):
    fornecedor = buscar_fornecedor_ou_404(cod_fornecedor)
    escolhido = request.form.get('cod_produto')
    try:
        dados = ler_dados_fornecimento(cod_fornecedor, request.form)
    except ValueError as erro:
        return mostrar_produtos_do_fornecedor(fornecedor, escolhido, str(erro))
    try:
        repositorio_fornecimentos.incluir_fornecimento(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_produtos_do_fornecedor(fornecedor, escolhido, mensagem)
    flash('Produto vinculado ao fornecedor.', 'sucesso')
    return redirect(url_for('fornecimentos.do_fornecedor', cod_fornecedor=cod_fornecedor))


@paginas.get('/<int:cod_fornecedor>/<int:cod_produto>')
def ficha(cod_fornecedor, cod_produto):
    return mostrar_par(cod_fornecedor, cod_produto)


@paginas.post('/<int:cod_fornecedor>/<int:cod_produto>/alterar')
def alterar(cod_fornecedor, cod_produto):
    try:
        dados = ler_dados_alteracao(cod_fornecedor, cod_produto, request.form)
    except ValueError as erro:
        return mostrar_par(cod_fornecedor, cod_produto, request.form, str(erro))
    try:
        repositorio_fornecimentos.alterar_fornecimento(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_par(cod_fornecedor, cod_produto, request.form, mensagem)
    flash('Vínculo alterado.', 'sucesso')
    return redirect(url_for(
        'fornecimentos.ficha',
        cod_fornecedor=dados['cod_fornecedor'],
        cod_produto=dados['cod_produto'],
    ))


@paginas.post('/<int:cod_fornecedor>/<int:cod_produto>/excluir')
def excluir(cod_fornecedor, cod_produto):
    repositorio_fornecimentos.excluir_fornecimento(cod_fornecedor, cod_produto)
    flash('Vínculo removido.', 'sucesso')
    return redirect(url_for('fornecimentos.do_fornecedor', cod_fornecedor=cod_fornecedor))

"""Páginas de produtos e consultas de estoque (área de administração)."""
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import categorias as repositorio_categorias
from repositorios import fornecimentos as repositorio_fornecimentos
from repositorios import produtos as repositorio_produtos

paginas = Blueprint('produtos', __name__, url_prefix='/administracao/produtos')

PRECO_MAXIMO = Decimal('999.99')


def ler_dados_produto(formulario):
    """Formulário -> dicionário esperado por cadastrar_produto."""
    return {
        'descricao': regras.texto_obrigatorio(formulario.get('descricao'), 'Descrição', 100),
        'preco': regras.decimal_obrigatorio(formulario.get('preco'), 'Preço', PRECO_MAXIMO),
        'qtd_estoque': regras.inteiro_obrigatorio(formulario.get('qtd_estoque'), 'Estoque', 0),
        'estoque_minimo': regras.inteiro_obrigatorio(formulario.get('estoque_minimo'), 'Estoque mínimo', 0),
        'cod_categoria': regras.codigo_opcional(formulario.get('cod_categoria'), 'Categoria'),
    }


def ler_dados_edicao_produto(cod_produto, formulario):
    """Formulário -> dicionário esperado por atualizar_produto."""
    dados = ler_dados_produto(formulario)
    dados['cod_produto'] = cod_produto
    return dados


def buscar_ou_404(cod_produto):
    produto = repositorio_produtos.buscar_produto(cod_produto)
    if produto is None:
        abort(404)
    return produto


def mostrar_formulario(dados, cod_produto=None, erro=None):
    categorias = repositorio_categorias.listar_categorias()
    return render_template(
        'produtos/formulario.html',
        dados=dados,
        cod_produto=cod_produto,
        categorias=categorias,
        erro=erro,
    )


@paginas.get('/')
def lista():
    produtos = repositorio_produtos.listar_produtos()
    return render_template('produtos/lista.html', titulo='Produtos', produtos=produtos)


@paginas.get('/disponiveis')
def disponiveis():
    produtos = repositorio_produtos.listar_produtos_disponiveis()
    return render_template('produtos/lista.html', titulo='Produtos disponíveis', produtos=produtos)


@paginas.get('/abaixo-do-minimo')
def abaixo_do_minimo():
    produtos = repositorio_produtos.listar_produtos_abaixo_do_minimo()
    return render_template('produtos/lista.html', titulo='Produtos abaixo do estoque mínimo', produtos=produtos)


@paginas.get('/<int:cod_produto>')
def ficha(cod_produto):
    produto = buscar_ou_404(cod_produto)
    categoria = None
    if produto['cod_categoria'] is not None:
        categoria = repositorio_categorias.buscar_categoria(produto['cod_categoria'])
    fornecedores = repositorio_fornecimentos.listar_fornecedores_do_produto(cod_produto)
    return render_template(
        'produtos/ficha.html',
        produto=produto,
        categoria=categoria,
        fornecedores=fornecedores,
    )


@paginas.get('/novo')
def novo():
    return mostrar_formulario({})


@paginas.post('/novo')
def incluir():
    try:
        dados = ler_dados_produto(request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, erro=str(erro))
    try:
        cod_produto = repositorio_produtos.cadastrar_produto(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Produto cadastrado.', 'sucesso')
    return redirect(url_for('produtos.ficha', cod_produto=cod_produto))


@paginas.get('/<int:cod_produto>/editar')
def editar(cod_produto):
    produto = buscar_ou_404(cod_produto)
    return mostrar_formulario(produto, cod_produto)


@paginas.post('/<int:cod_produto>/editar')
def salvar(cod_produto):
    try:
        dados = ler_dados_edicao_produto(cod_produto, request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, cod_produto, str(erro))
    try:
        repositorio_produtos.atualizar_produto(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, cod_produto, regras.explicar_recusa(erro.diag.constraint_name))
    flash('Produto atualizado.', 'sucesso')
    return redirect(url_for('produtos.ficha', cod_produto=cod_produto))


@paginas.post('/<int:cod_produto>/excluir')
def excluir(cod_produto):
    try:
        repositorio_produtos.excluir_produto(cod_produto)
    except IntegrityError:
        flash(
            'Este produto não pode ser excluído porque aparece em vendas '
            'ou está vinculado a fornecedores.',
            'erro',
        )
        return redirect(url_for('produtos.ficha', cod_produto=cod_produto))
    flash('Produto excluído.', 'sucesso')
    return redirect(url_for('produtos.lista'))

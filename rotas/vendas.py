"""Páginas de vendas e de seus itens (área de vendas).

O valor da venda não vem de nenhum formulário: o banco o calcula pelos itens.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
import relogio
from repositorios import clientes as repositorio_clientes
from repositorios import produtos as repositorio_produtos
from repositorios import vendas as repositorio_vendas

paginas = Blueprint('vendas', __name__, url_prefix='/vendas')


# Mapeadores: formulário -> dicionário de cada função do repositório -------------

def ler_dados_abertura(formulario):
    """Formulário -> dicionário esperado por abrir_venda."""
    return {
        'cod_cliente': regras.codigo_obrigatorio(formulario.get('cod_cliente'), 'Cliente'),
        'cod_vendedor': regras.codigo_opcional(formulario.get('cod_vendedor'), 'Vendedor'),
        'data_venda': regras.data_obrigatoria(formulario.get('data_venda'), 'Data da venda'),
    }


def ler_dados_cabecalho(numero_venda, formulario):
    """Formulário -> dicionário esperado por atualizar_venda."""
    dados = ler_dados_abertura(formulario)
    dados['numero_venda'] = numero_venda
    return dados


def ler_dados_novo_item(numero_venda, formulario):
    """Formulário -> dicionário esperado por incluir_item."""
    return {
        'numero_venda': numero_venda,
        'cod_produto': regras.codigo_obrigatorio(formulario.get('cod_produto'), 'Produto'),
        'quantidade': regras.inteiro_obrigatorio(formulario.get('quantidade'), 'Quantidade', 1),
    }


def ler_dados_quantidade(numero_venda, cod_produto, formulario):
    """Formulário -> dicionário esperado por alterar_quantidade_do_item."""
    return {
        'numero_venda': numero_venda,
        'cod_produto': cod_produto,
        'quantidade': regras.inteiro_obrigatorio(formulario.get('quantidade'), 'Quantidade', 1),
    }


def ler_dados_troca(numero_venda, cod_produto_atual, formulario):
    """Formulário -> dicionário esperado por trocar_produto_do_item."""
    return {
        'numero_venda': numero_venda,
        'cod_produto_atual': cod_produto_atual,
        'cod_produto_novo': regras.codigo_obrigatorio(formulario.get('cod_produto'), 'Produto'),
        'quantidade': regras.inteiro_obrigatorio(formulario.get('quantidade'), 'Quantidade', 1),
    }


# Apoio às páginas ---------------------------------------------------------------

def buscar_venda_ou_404(numero_venda):
    venda = repositorio_vendas.buscar_venda(numero_venda)
    if venda is None:
        abort(404)
    return venda


def buscar_item_ou_404(numero_venda, cod_produto):
    item = repositorio_vendas.buscar_item(numero_venda, cod_produto)
    if item is None:
        abort(404)
    return item


def mostrar_formulario_de_abertura(dados, erro=None):
    return render_template(
        'vendas/formulario.html',
        dados=dados,
        clientes=repositorio_clientes.listar_clientes(),
        vendedores=repositorio_vendas.listar_opcoes_de_vendedor(),
        erro=erro,
    )


def mostrar_ficha(venda, cabecalho=None, novo_item=None, erro=None):
    """Ficha da venda: cabeçalho editável, itens e inclusão de item.

    cabecalho e novo_item trazem o que foi digitado quando houve erro.
    """
    if cabecalho is None:
        cabecalho = venda
    if novo_item is None:
        novo_item = {}
    return render_template(
        'vendas/ficha.html',
        venda=venda,
        cabecalho=cabecalho,
        novo_item=novo_item,
        itens=repositorio_vendas.listar_itens(venda['numero_venda']),
        clientes=repositorio_clientes.listar_clientes(),
        vendedores=repositorio_vendas.listar_opcoes_de_vendedor(),
        produtos=repositorio_produtos.listar_produtos(),
        erro=erro,
    )


def mostrar_formulario_de_item(item, dados, erro=None):
    return render_template(
        'vendas/item.html',
        item=item,
        dados=dados,
        produtos=repositorio_produtos.listar_produtos(),
        erro=erro,
    )


# Venda ----------------------------------------------------------------------------

@paginas.get('/')
def lista():
    vendas = repositorio_vendas.listar_vendas()
    return render_template('vendas/lista.html', vendas=vendas)


@paginas.get('/consultar')
def consultar():
    try:
        numero_venda = regras.codigo_obrigatorio(request.args.get('numero_venda'), 'Número da venda')
    except ValueError as erro:
        flash(str(erro), 'erro')
        return redirect(url_for('vendas.lista'))
    return redirect(url_for('vendas.ficha', numero_venda=numero_venda))


@paginas.get('/nova')
def nova():
    dados = {'data_venda': relogio.hoje_na_loja().isoformat()}
    cod_cliente = request.args.get('cod_cliente')
    if cod_cliente:
        dados['cod_cliente'] = cod_cliente
    return mostrar_formulario_de_abertura(dados)


@paginas.post('/nova')
def abrir():
    try:
        dados = ler_dados_abertura(request.form)
    except ValueError as erro:
        return mostrar_formulario_de_abertura(request.form, str(erro))
    try:
        numero_venda = repositorio_vendas.abrir_venda(dados)
    except IntegrityError as erro:
        return mostrar_formulario_de_abertura(request.form, regras.explicar_recusa(erro.diag.constraint_name))
    flash(f'Venda {numero_venda} aberta. Inclua os itens.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=numero_venda))


@paginas.get('/<int:numero_venda>')
def ficha(numero_venda):
    venda = buscar_venda_ou_404(numero_venda)
    return mostrar_ficha(venda)


@paginas.post('/<int:numero_venda>/cabecalho')
def salvar_cabecalho(numero_venda):
    venda = buscar_venda_ou_404(numero_venda)
    try:
        dados = ler_dados_cabecalho(numero_venda, request.form)
    except ValueError as erro:
        return mostrar_ficha(venda, cabecalho=request.form, erro=str(erro))
    try:
        repositorio_vendas.atualizar_venda(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_ficha(venda, cabecalho=request.form, erro=mensagem)
    flash('Dados da venda atualizados.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=numero_venda))


@paginas.post('/<int:numero_venda>/cancelar')
def cancelar(numero_venda):
    buscar_venda_ou_404(numero_venda)
    repositorio_vendas.cancelar_venda(numero_venda)
    flash(f'Venda {numero_venda} cancelada; as unidades voltaram ao estoque.', 'sucesso')
    return redirect(url_for('vendas.lista'))


# Itens ------------------------------------------------------------------------------

@paginas.post('/<int:numero_venda>/itens')
def incluir_item(numero_venda):
    venda = buscar_venda_ou_404(numero_venda)
    try:
        dados = ler_dados_novo_item(numero_venda, request.form)
    except ValueError as erro:
        return mostrar_ficha(venda, novo_item=request.form, erro=str(erro))
    try:
        repositorio_vendas.incluir_item(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_ficha(venda, novo_item=request.form, erro=mensagem)
    flash('Item incluído.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=numero_venda))


@paginas.get('/<int:numero_venda>/itens/<int:cod_produto>')
def editar_item(numero_venda, cod_produto):
    item = buscar_item_ou_404(numero_venda, cod_produto)
    return mostrar_formulario_de_item(item, item)


@paginas.post('/<int:numero_venda>/itens/<int:cod_produto>')
def salvar_item(numero_venda, cod_produto):
    item = buscar_item_ou_404(numero_venda, cod_produto)
    try:
        produto_escolhido = regras.codigo_obrigatorio(request.form.get('cod_produto'), 'Produto')
    except ValueError as erro:
        return mostrar_formulario_de_item(item, request.form, str(erro))
    if produto_escolhido == cod_produto:
        return alterar_quantidade(item, request.form)
    return trocar_produto(item, request.form)


def alterar_quantidade(item, formulario):
    """Mesmo produto: só a quantidade muda; o preço praticado é mantido."""
    try:
        dados = ler_dados_quantidade(item['numero_venda'], item['cod_produto'], formulario)
    except ValueError as erro:
        return mostrar_formulario_de_item(item, formulario, str(erro))
    try:
        repositorio_vendas.alterar_quantidade_do_item(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_formulario_de_item(item, formulario, mensagem)
    flash('Quantidade do item atualizada.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=item['numero_venda']))


def trocar_produto(item, formulario):
    """Outro produto: o item passa a ter o produto escolhido, pelo preço atual dele."""
    try:
        dados = ler_dados_troca(item['numero_venda'], item['cod_produto'], formulario)
    except ValueError as erro:
        return mostrar_formulario_de_item(item, formulario, str(erro))
    try:
        repositorio_vendas.trocar_produto_do_item(dados)
    except IntegrityError as erro:
        mensagem = regras.explicar_recusa(erro.diag.constraint_name)
        return mostrar_formulario_de_item(item, formulario, mensagem)
    flash('Produto do item trocado.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=item['numero_venda']))


@paginas.post('/<int:numero_venda>/itens/<int:cod_produto>/remover')
def remover_item(numero_venda, cod_produto):
    repositorio_vendas.remover_item(numero_venda, cod_produto)
    flash('Item removido; as unidades voltaram ao estoque.', 'sucesso')
    return redirect(url_for('vendas.ficha', numero_venda=numero_venda))

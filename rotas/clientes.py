"""Páginas de clientes (área de vendas)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from psycopg import IntegrityError

import regras
from repositorios import clientes as repositorio_clientes
from repositorios import vendas as repositorio_vendas

paginas = Blueprint('clientes', __name__, url_prefix='/vendas/clientes')


def ler_dados_cliente(formulario):
    """Formulário -> dicionário esperado por cadastrar_cliente."""
    return {
        'nome': regras.texto_obrigatorio(formulario.get('nome'), 'Nome', 100),
        'rua_numero': regras.texto_obrigatorio(formulario.get('rua_numero'), 'Rua e número', 70),
        'bairro': regras.texto_obrigatorio(formulario.get('bairro'), 'Bairro', 70),
        'cidade': regras.texto_obrigatorio(formulario.get('cidade'), 'Cidade', 70),
        'estado': regras.sigla_de_estado(formulario.get('estado'), 'Estado'),
        'cep': regras.texto_obrigatorio(formulario.get('cep'), 'CEP', 10),
        'telefone': regras.texto_opcional(formulario.get('telefone'), 'Telefone', 20),
    }


def ler_dados_edicao_cliente(cod_cliente, formulario):
    """Formulário -> dicionário esperado por atualizar_cliente."""
    dados = ler_dados_cliente(formulario)
    dados['cod_cliente'] = cod_cliente
    return dados


def buscar_ou_404(cod_cliente):
    cliente = repositorio_clientes.buscar_cliente(cod_cliente)
    if cliente is None:
        abort(404)
    return cliente


def mostrar_formulario(dados, cod_cliente=None, erro=None):
    return render_template(
        'clientes/formulario.html',
        dados=dados,
        cod_cliente=cod_cliente,
        erro=erro,
    )


@paginas.get('/')
def lista():
    clientes = repositorio_clientes.listar_clientes()
    return render_template('clientes/lista.html', clientes=clientes)


@paginas.get('/<int:cod_cliente>')
def ficha(cod_cliente):
    cliente = buscar_ou_404(cod_cliente)
    compras = repositorio_vendas.listar_vendas_do_cliente(cod_cliente)
    return render_template('clientes/ficha.html', cliente=cliente, compras=compras)


@paginas.get('/novo')
def novo():
    return mostrar_formulario({})


@paginas.post('/novo')
def incluir():
    try:
        dados = ler_dados_cliente(request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, erro=str(erro))
    try:
        cod_cliente = repositorio_clientes.cadastrar_cliente(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, erro=regras.explicar_recusa(erro.diag.constraint_name))
    flash('Cliente cadastrado.', 'sucesso')
    return redirect(url_for('clientes.ficha', cod_cliente=cod_cliente))


@paginas.get('/<int:cod_cliente>/editar')
def editar(cod_cliente):
    cliente = buscar_ou_404(cod_cliente)
    return mostrar_formulario(cliente, cod_cliente)


@paginas.post('/<int:cod_cliente>/editar')
def salvar(cod_cliente):
    try:
        dados = ler_dados_edicao_cliente(cod_cliente, request.form)
    except ValueError as erro:
        return mostrar_formulario(request.form, cod_cliente, str(erro))
    try:
        repositorio_clientes.atualizar_cliente(dados)
    except IntegrityError as erro:
        return mostrar_formulario(request.form, cod_cliente, regras.explicar_recusa(erro.diag.constraint_name))
    flash('Cliente atualizado.', 'sucesso')
    return redirect(url_for('clientes.ficha', cod_cliente=cod_cliente))


@paginas.post('/<int:cod_cliente>/excluir')
def excluir(cod_cliente):
    try:
        repositorio_clientes.excluir_cliente(cod_cliente)
    except IntegrityError:
        flash('Este cliente não pode ser excluído porque possui vendas registradas.', 'erro')
        return redirect(url_for('clientes.ficha', cod_cliente=cod_cliente))
    flash('Cliente excluído.', 'sucesso')
    return redirect(url_for('clientes.lista'))

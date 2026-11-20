"""Repositório de vendedores (cadastro da área de administração).

As cinco funções deste módulo fazem parte da atividade do caso. Siga o padrão
de repositorios/categorias.py: SQL em várias linhas, parâmetros nomeados
(%(nome)s) com os valores em um dicionário separado, e as funções de db.py
(consultar, consultar_um, consultar_valor, executar).
"""
import db


def cadastrar_vendedor(dados):
    """Inclui um vendedor.

    dados: dicionário com 'nome' (texto) e 'cidade' (texto).
    Retorna o cod_vendedor (inteiro) gerado pelo banco e gravado na nova linha.
    """
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('cadastrar_vendedor ainda não foi implementada.')


def listar_vendedores():
    """Retorna a lista de vendedores cadastrados.

    Cada item é uma ficha: dicionário com 'cod_vendedor' (inteiro), 'nome' e
    'cidade' (textos), uma por código. Sem vendedores, retorna lista vazia [].
    A ordem da lista não faz parte do contrato.
    """
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('listar_vendedores ainda não foi implementada.')


def buscar_vendedor(cod_vendedor):
    """Retorna a ficha do vendedor de código cod_vendedor (inteiro).

    A ficha é um dicionário com 'cod_vendedor', 'nome' e 'cidade'.
    Se o código não existir, retorna None.
    """
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('buscar_vendedor ainda não foi implementada.')


def atualizar_vendedor(dados):
    """Grava o nome e a cidade do vendedor indicado por 'cod_vendedor'.

    dados: dicionário com 'cod_vendedor' (inteiro), 'nome' e 'cidade' (textos).
    Somente esse vendedor é alterado; se o código não existir, nenhum vendedor
    é modificado. Retorna None.
    """
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('atualizar_vendedor ainda não foi implementada.')


def excluir_vendedor(cod_vendedor):
    """Exclui o vendedor de código cod_vendedor (inteiro). Retorna None.

    Somente esse vendedor é removido; se o código não existir, ninguém é
    removido. Se o vendedor estiver registrado em vendas, o banco recusa a
    exclusão: deixe o erro seguir até a rota, que mostra o aviso na tela.
    """
    # TODO: escrever o comando SQL e executá-lo com a função adequada de db.py.
    raise NotImplementedError('excluir_vendedor ainda não foi implementada.')

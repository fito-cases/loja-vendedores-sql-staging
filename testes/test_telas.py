"""Telas da loja, verificadas sem banco.

As funções dos repositórios são trocadas por substitutos no limite entre rota
e repositório: aqui se verifica o que a tela envia ao repositório e como ela
mostra o que recebe. As consultas reais são verificadas nos testes de cada
repositório. Qualquer acesso ao banco neste arquivo faz o teste falhar.
"""
import datetime
from decimal import Decimal

import psycopg
import pytest
from psycopg import errors

import app
import db
import relogio
from repositorios import categorias as repositorio_categorias
from repositorios import clientes as repositorio_clientes
from repositorios import fornecedores as repositorio_fornecedores
from repositorios import fornecimentos as repositorio_fornecimentos
from repositorios import produtos as repositorio_produtos
from repositorios import relatorios as repositorio_relatorios
from repositorios import vendas as repositorio_vendas
from repositorios import vendedores as repositorio_vendedores

CATEGORIAS = [
    {'cod_categoria': 1, 'nome': 'Camisetas'},
    {'cod_categoria': 11, 'nome': 'Pijamas'},
]
CLIENTES = [
    {'cod_cliente': 1, 'nome': 'Lia Costa', 'bairro': 'Icaraí', 'cidade': 'Niterói', 'telefone': '(21) 90000-0101'},
    {'cod_cliente': 2, 'nome': 'Lia Costa', 'bairro': 'Centro', 'cidade': 'Maricá', 'telefone': None},
]
CLIENTE_1 = {
    'cod_cliente': 1, 'nome': 'Lia Costa', 'rua_numero': 'Rua das Acácias, 120', 'bairro': 'Icaraí',
    'cidade': 'Niterói', 'estado': 'RJ', 'cep': '24230-000', 'telefone': '(21) 90000-0101',
}
PRODUTOS = [
    {'cod_produto': 1, 'descricao': 'Camiseta básica de algodão', 'preco': Decimal('25.00'),
     'qtd_estoque': 40, 'estoque_minimo': 10},
    {'cod_produto': 7, 'descricao': 'Cinto de couro marrom', 'preco': Decimal('55.00'),
     'qtd_estoque': 0, 'estoque_minimo': 4},
]
PRODUTO_1 = {
    'cod_produto': 1, 'descricao': 'Camiseta básica de algodão', 'preco': Decimal('25.00'),
    'qtd_estoque': 40, 'estoque_minimo': 10, 'cod_categoria': 1,
}
FORNECEDORES = [
    {'cod_fornecedor': 1, 'razao_social': 'Malharia Serra Azul Ltda.', 'cidade': 'Petrópolis', 'estado': 'RJ'},
]
OPCOES_DE_VENDEDOR = [
    {'cod_vendedor': 1, 'rotulo': 'Ana Lima (Niterói)'},
    {'cod_vendedor': 2, 'rotulo': 'Ana Lima (Maricá)'},
]
VENDA_102 = {
    'numero_venda': 102, 'cod_cliente': 1, 'cod_vendedor': 1,
    'data_venda': datetime.date(2025, 6, 2), 'valor': Decimal('80.00'),
}
ITENS_102 = [
    {'cod_produto': 1, 'descricao': 'Camiseta básica de algodão', 'quantidade': 2,
     'preco_unitario': Decimal('25.00'), 'subtotal': Decimal('50.00')},
    {'cod_produto': 8, 'descricao': 'Brinco de argola dourado', 'quantidade': 1,
     'preco_unitario': Decimal('30.00'), 'subtotal': Decimal('30.00')},
]


def substituir(monkeypatch, modulo, nome_da_funcao, resposta=None):
    """Troca uma função do repositório; devolve a lista de chamadas recebidas."""
    chamadas = []

    def substituto(*argumentos):
        chamadas.append(argumentos)
        return resposta

    monkeypatch.setattr(modulo, nome_da_funcao, substituto)
    return chamadas


def substituir_com_erro(monkeypatch, modulo, nome_da_funcao, erro):
    """Troca uma função do repositório por outra que lança o erro informado."""
    chamadas = []

    def substituto(*argumentos):
        chamadas.append(argumentos)
        raise erro

    monkeypatch.setattr(modulo, nome_da_funcao, substituto)
    return chamadas


def buscar_na_lista(registros, nome_da_chave):
    """Substituto de buscar_*: devolve o registro do código pedido ou None."""
    def substituto(codigo):
        for registro in registros:
            if registro[nome_da_chave] == codigo:
                return registro
        return None
    return substituto


@pytest.fixture(autouse=True)
def sem_banco(monkeypatch):
    def acesso_proibido():
        raise AssertionError('os testes de tela não devem acessar o banco')

    monkeypatch.setattr(db, 'transacao', acesso_proibido)


@pytest.fixture
def repositorios_prontos(monkeypatch):
    """Respostas fixas para as leituras dos cadastros prontos."""
    substituir(monkeypatch, repositorio_categorias, 'listar_categorias', CATEGORIAS)
    monkeypatch.setattr(repositorio_categorias, 'buscar_categoria', buscar_na_lista(CATEGORIAS, 'cod_categoria'))
    substituir(monkeypatch, repositorio_clientes, 'listar_clientes', CLIENTES)
    monkeypatch.setattr(repositorio_clientes, 'buscar_cliente', buscar_na_lista([CLIENTE_1], 'cod_cliente'))
    substituir(monkeypatch, repositorio_produtos, 'listar_produtos', PRODUTOS)
    substituir(monkeypatch, repositorio_produtos, 'listar_produtos_disponiveis', PRODUTOS[:1])
    substituir(monkeypatch, repositorio_produtos, 'listar_produtos_abaixo_do_minimo', PRODUTOS[1:])
    monkeypatch.setattr(repositorio_produtos, 'buscar_produto', buscar_na_lista([PRODUTO_1], 'cod_produto'))
    substituir(monkeypatch, repositorio_fornecedores, 'listar_fornecedores', FORNECEDORES)
    monkeypatch.setattr(repositorio_fornecedores, 'buscar_fornecedor', buscar_na_lista(FORNECEDORES, 'cod_fornecedor'))
    substituir(monkeypatch, repositorio_fornecimentos, 'listar_produtos_do_fornecedor', PRODUTOS[:1])
    substituir(monkeypatch, repositorio_fornecimentos, 'listar_fornecedores_do_produto', FORNECEDORES)
    substituir(monkeypatch, repositorio_fornecimentos, 'buscar_fornecimento',
               {'cod_fornecedor': 1, 'cod_produto': 1, 'created_at': datetime.datetime(2025, 5, 1, 9, 0)})
    substituir(monkeypatch, repositorio_vendas, 'listar_vendas',
               [{'numero_venda': 102, 'data_venda': datetime.date(2025, 6, 2), 'valor': Decimal('80.00')}])
    substituir(monkeypatch, repositorio_vendas, 'listar_vendas_do_cliente',
               [{'numero_venda': 102, 'data_venda': datetime.date(2025, 6, 2), 'valor': Decimal('80.00')}])
    monkeypatch.setattr(repositorio_vendas, 'buscar_venda', buscar_na_lista([VENDA_102], 'numero_venda'))
    substituir(monkeypatch, repositorio_vendas, 'listar_itens', ITENS_102)
    substituir(monkeypatch, repositorio_vendas, 'listar_opcoes_de_vendedor', OPCOES_DE_VENDEDOR)
    substituir_com_erro(monkeypatch, repositorio_vendedores, 'listar_vendedores',
                        AssertionError('a venda usa listar_opcoes_de_vendedor, não listar_vendedores'))


@pytest.fixture
def navegador():
    aplicacao = app.criar_aplicacao()
    aplicacao.config['TESTING'] = True
    return aplicacao.test_client()


def texto(resposta):
    return resposta.get_data(as_text=True)


# Menu e páginas dos cadastros prontos ----------------------------------------------

def test_inicio_mostra_as_duas_areas(navegador):
    pagina = texto(navegador.get('/'))

    assert 'Área de vendas' in pagina
    assert 'Área de administração' in pagina
    for endereco in ('/vendas/', '/vendas/clientes/', '/vendas/relatorio/',
                     '/administracao/categorias/', '/administracao/produtos/',
                     '/administracao/fornecedores/', '/administracao/fornecimentos/',
                     '/administracao/vendedores/'):
        assert f'href="{endereco}"' in pagina


def test_listas_dos_cadastros_prontos(navegador, repositorios_prontos):
    esperado = {
        '/administracao/categorias/': 'Pijamas',
        '/vendas/clientes/': 'Maricá',
        '/administracao/produtos/': 'Camiseta básica de algodão',
        '/administracao/produtos/disponiveis': 'Camiseta básica de algodão',
        '/administracao/produtos/abaixo-do-minimo': 'abaixo do mínimo',
        '/administracao/fornecedores/': 'Malharia Serra Azul Ltda.',
        '/administracao/fornecimentos/': 'Malharia Serra Azul Ltda.',
        '/vendas/': 'R$ 80,00',
    }
    for endereco, trecho in esperado.items():
        resposta = navegador.get(endereco)
        assert resposta.status_code == 200, endereco
        assert trecho in texto(resposta), endereco


def test_fichas_dos_cadastros_prontos(navegador, repositorios_prontos):
    esperado = {
        '/administracao/categorias/1': 'Camisetas',
        '/vendas/clientes/1': 'Rua das Acácias, 120',
        '/administracao/produtos/1': 'Malharia Serra Azul Ltda.',
        '/administracao/fornecedores/1': 'Camiseta básica de algodão',
        '/administracao/fornecimentos/fornecedor/1': 'Vincular produto',
        '/administracao/fornecimentos/1/1': 'Alterar o vínculo',
        '/vendas/102': 'Brinco de argola dourado',
    }
    for endereco, trecho in esperado.items():
        resposta = navegador.get(endereco)
        assert resposta.status_code == 200, endereco
        assert trecho in texto(resposta), endereco
    assert navegador.get('/administracao/categorias/999').status_code == 404
    assert navegador.get('/vendas/999').status_code == 404


def test_inclusao_converte_os_campos_do_formulario(navegador, repositorios_prontos, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_produtos, 'cadastrar_produto', 17)

    resposta = navegador.post('/administracao/produtos/novo', data={
        'descricao': '  Lenço de seda  ',
        'preco': '34,90',
        'qtd_estoque': '6',
        'estoque_minimo': '2',
        'cod_categoria': '',
        'campo_extra': 'ignorado',
    })

    assert resposta.status_code == 302
    assert resposta.headers['Location'].endswith('/administracao/produtos/17')
    assert chamadas == [({
        'descricao': 'Lenço de seda',
        'preco': Decimal('34.90'),
        'qtd_estoque': 6,
        'estoque_minimo': 2,
        'cod_categoria': None,
    },)]


def test_operacao_invalida_nao_chega_ao_repositorio(navegador, repositorios_prontos, monkeypatch):
    cadastro_de_cliente = substituir(monkeypatch, repositorio_clientes, 'cadastrar_cliente', 13)
    cadastro_de_produto = substituir(monkeypatch, repositorio_produtos, 'cadastrar_produto', 17)
    inclusao_de_item = substituir(monkeypatch, repositorio_vendas, 'incluir_item')

    cliente = navegador.post('/vendas/clientes/novo', data={
        'nome': '', 'rua_numero': 'Rua A, 1', 'bairro': 'Centro', 'cidade': 'Niterói',
        'estado': 'RJ', 'cep': '24020-000', 'telefone': '',
    })
    produto = navegador.post('/administracao/produtos/novo', data={
        'descricao': 'Lenço', 'preco': '-1', 'qtd_estoque': '1', 'estoque_minimo': '0', 'cod_categoria': '',
    })
    item = navegador.post('/vendas/102/itens', data={'cod_produto': '1', 'quantidade': '0'})

    assert cadastro_de_cliente == []
    assert cadastro_de_produto == []
    assert inclusao_de_item == []
    assert 'Preencha o campo Nome.' in texto(cliente)
    assert 'value="Rua A, 1"' in texto(cliente)
    assert 'O campo Preço deve estar entre 0,00 e 999,99.' in texto(produto)
    assert 'O campo Quantidade deve ser maior ou igual a 1.' in texto(item)


def test_recusa_do_banco_aparece_na_mesma_pagina(navegador, repositorios_prontos, monkeypatch):
    substituir_com_erro(monkeypatch, repositorio_categorias, 'excluir_categoria',
                        errors.ForeignKeyViolation('violação simulada'))
    substituir_com_erro(monkeypatch, repositorio_vendas, 'incluir_item',
                        errors.CheckViolation('violação simulada'))

    exclusao = navegador.post('/administracao/categorias/1/excluir', follow_redirects=True)
    item = navegador.post('/vendas/102/itens', data={'cod_produto': '7', 'quantidade': '3'})

    assert 'Esta categoria não pode ser excluída porque há produtos nela.' in texto(exclusao)
    assert 'Camisetas' in texto(exclusao)
    assert item.status_code == 200
    assert 'regra de integridade' in texto(item)
    assert 'value="3"' in texto(item)
    assert 'Traceback' not in texto(item)


def test_erro_inesperado_do_banco_sem_detalhes_tecnicos(monkeypatch):
    substituir_com_erro(monkeypatch, repositorio_categorias, 'listar_categorias',
                        psycopg.OperationalError('falha simulada para postgres.ref:senha-secreta@host'))
    aplicacao = app.criar_aplicacao()

    resposta = aplicacao.test_client().get('/administracao/categorias/')

    assert resposta.status_code == 500
    assert 'Não foi possível concluir a operação' in texto(resposta)
    assert 'senha-secreta' not in texto(resposta)
    assert 'Traceback' not in texto(resposta)


# Venda -------------------------------------------------------------------------------

def test_formulario_de_venda_com_vendedor_opcional(navegador, repositorios_prontos, monkeypatch):
    monkeypatch.setattr(relogio, 'hoje_na_loja', lambda: datetime.date(2025, 6, 10))

    pagina = texto(navegador.get('/vendas/nova'))

    assert 'sem vendedor identificado' in pagina
    assert 'Ana Lima (Maricá)' in pagina
    assert 'value="2025-06-10"' in pagina


def test_abertura_de_venda_com_e_sem_vendedor(navegador, repositorios_prontos, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_vendas, 'abrir_venda', 107)

    sem_vendedor = navegador.post('/vendas/nova', data={
        'cod_cliente': '2', 'cod_vendedor': '', 'data_venda': '2025-06-10', 'valor': '999',
    })
    com_vendedor = navegador.post('/vendas/nova', data={
        'cod_cliente': '1', 'cod_vendedor': '1', 'data_venda': '2025-06-10',
    })

    assert sem_vendedor.status_code == 302
    assert com_vendedor.headers['Location'].endswith('/vendas/107')
    assert chamadas == [
        ({'cod_cliente': 2, 'cod_vendedor': None, 'data_venda': datetime.date(2025, 6, 10)},),
        ({'cod_cliente': 1, 'cod_vendedor': 1, 'data_venda': datetime.date(2025, 6, 10)},),
    ]


def test_edicao_de_item_escolhe_entre_quantidade_e_troca(navegador, repositorios_prontos, monkeypatch):
    substituir(monkeypatch, repositorio_vendas, 'buscar_item',
               {'numero_venda': 102, 'cod_produto': 1, 'quantidade': 2, 'preco_unitario': Decimal('25.00')})
    quantidade = substituir(monkeypatch, repositorio_vendas, 'alterar_quantidade_do_item')
    troca = substituir(monkeypatch, repositorio_vendas, 'trocar_produto_do_item')

    navegador.post('/vendas/102/itens/1', data={'cod_produto': '1', 'quantidade': '3'})
    navegador.post('/vendas/102/itens/1', data={'cod_produto': '7', 'quantidade': '1'})

    assert quantidade == [({'numero_venda': 102, 'cod_produto': 1, 'quantidade': 3},)]
    assert troca == [({'numero_venda': 102, 'cod_produto_atual': 1, 'cod_produto_novo': 7, 'quantidade': 1},)]


def test_cancelamento_de_venda(navegador, repositorios_prontos, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_vendas, 'cancelar_venda')

    resposta = navegador.post('/vendas/102/cancelar')

    assert chamadas == [(102,)]
    assert resposta.headers['Location'].endswith('/vendas/')


# Conferência de vendas por período --------------------------------------------------

def test_relatorio_abre_na_semana_atual_da_loja(navegador, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_relatorios, 'listar_vendas_periodo', [])
    dias_e_semanas = [
        (datetime.date(2025, 6, 5), datetime.date(2025, 6, 2), datetime.date(2025, 6, 8)),
        (datetime.date(2025, 6, 2), datetime.date(2025, 6, 2), datetime.date(2025, 6, 8)),
        (datetime.date(2025, 6, 8), datetime.date(2025, 6, 2), datetime.date(2025, 6, 8)),
        (datetime.date(2025, 6, 9), datetime.date(2025, 6, 9), datetime.date(2025, 6, 15)),
    ]
    for hoje, segunda, domingo in dias_e_semanas:
        monkeypatch.setattr(relogio, 'hoje_na_loja', lambda dia=hoje: dia)
        pagina = texto(navegador.get('/vendas/relatorio/'))

        assert chamadas[-1] == (segunda, domingo)
        assert f'value="{segunda.isoformat()}"' in pagina
        assert f'value="{domingo.isoformat()}"' in pagina
        assert 'Nenhuma venda no período.' in pagina
        assert '<th>Cliente</th>' in pagina
    assert len(chamadas) == 4


def test_relatorio_com_datas_informadas(navegador, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_relatorios, 'listar_vendas_periodo', [])

    navegador.get('/vendas/relatorio/?data_inicial=2025-06-03&data_final=2025-06-03')
    navegador.get('/vendas/relatorio/?data_inicial=2025-06-02&data_final=2025-06-08')

    assert chamadas == [
        (datetime.date(2025, 6, 3), datetime.date(2025, 6, 3)),
        (datetime.date(2025, 6, 2), datetime.date(2025, 6, 8)),
    ]


def test_relatorio_recusa_filtro_parcial_invertido_ou_invalido(navegador, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_relatorios, 'listar_vendas_periodo', [])

    parcial = texto(navegador.get('/vendas/relatorio/?data_inicial=2025-06-02&data_final='))
    invertido = texto(navegador.get('/vendas/relatorio/?data_inicial=2025-06-08&data_final=2025-06-02'))
    invalido = texto(navegador.get('/vendas/relatorio/?data_inicial=2025-02-30&data_final=2025-03-02'))

    assert chamadas == []
    assert 'Informe as duas datas do período' in parcial
    assert 'A data inicial deve ser anterior ou igual à data final.' in invertido
    assert 'O campo Data inicial deve ser uma data válida' in invalido
    assert 'value="2025-02-30"' in invalido


def test_relatorio_mostra_cada_venda_e_rotula_ausencia_de_vendedor(navegador, monkeypatch):
    substituir(monkeypatch, repositorio_relatorios, 'listar_vendas_periodo', [
        {'numero_venda': 102, 'data_venda': datetime.date(2025, 6, 2), 'cliente': 'Lia Costa',
         'vendedor': 'Ana Lima', 'valor': Decimal('80.00')},
        {'numero_venda': 104, 'data_venda': datetime.date(2025, 6, 3), 'cliente': 'Lia Costa',
         'vendedor': None, 'valor': Decimal('0.00')},
    ])

    pagina = texto(navegador.get('/vendas/relatorio/?data_inicial=2025-06-02&data_final=2025-06-08'))

    assert 'Vendas de 02/06/2025 a 08/06/2025' in pagina
    assert '<td>Ana Lima</td>' in pagina
    assert '<td>Sem vendedor</td>' in pagina
    assert 'R$ 80,00' in pagina
    assert 'R$ 0,00' in pagina
    assert '03/06/2025' in pagina


def test_relatorio_pendente_avisa_indisponibilidade(navegador, monkeypatch):
    substituir_com_erro(monkeypatch, repositorio_relatorios, 'listar_vendas_periodo', NotImplementedError())

    pagina = texto(navegador.get('/vendas/relatorio/?data_inicial=2025-06-02&data_final=2025-06-08'))

    assert 'Operação indisponível' in pagina
    assert 'Nenhuma venda no período.' not in pagina
    assert 'value="2025-06-02"' in pagina


# Cadastro de vendedores ---------------------------------------------------------------

def test_vendedores_mostram_fichas_recebidas(navegador, monkeypatch):
    substituir(monkeypatch, repositorio_vendedores, 'listar_vendedores', [
        {'cod_vendedor': 1, 'nome': 'Ana Lima', 'cidade': 'Niterói'},
        {'cod_vendedor': 2, 'nome': 'Ana Lima', 'cidade': 'Maricá'},
    ])
    monkeypatch.setattr(repositorio_vendedores, 'buscar_vendedor', buscar_na_lista(
        [{'cod_vendedor': 2, 'nome': 'Ana Lima', 'cidade': 'Maricá'}], 'cod_vendedor'))

    lista = texto(navegador.get('/administracao/vendedores/'))
    ficha = texto(navegador.get('/administracao/vendedores/2'))

    assert 'Niterói' in lista
    assert 'Maricá' in lista
    assert 'Maricá' in ficha
    assert navegador.get('/administracao/vendedores/999').status_code == 404


def test_vendedores_lista_vazia_e_indisponivel_sao_diferentes(navegador, monkeypatch):
    substituir(monkeypatch, repositorio_vendedores, 'listar_vendedores', [])
    vazia = texto(navegador.get('/administracao/vendedores/'))
    substituir_com_erro(monkeypatch, repositorio_vendedores, 'listar_vendedores', NotImplementedError())
    indisponivel = texto(navegador.get('/administracao/vendedores/'))

    assert 'Nenhum vendedor cadastrado.' in vazia
    assert 'Operação indisponível' not in vazia
    assert 'Operação indisponível' in indisponivel
    assert 'Nenhum vendedor cadastrado.' not in indisponivel


def test_cadastro_de_vendedor_envia_somente_os_campos_esperados(navegador, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_vendedores, 'cadastrar_vendedor', 11)

    resposta = navegador.post('/administracao/vendedores/novo', data={
        'nome': ' Ana Lima ', 'cidade': 'Niterói', 'cod_vendedor': '1',
    })

    assert chamadas == [({'nome': 'Ana Lima', 'cidade': 'Niterói'},)]
    assert resposta.headers['Location'].endswith('/administracao/vendedores/11')


def test_edicao_de_vendedor_identifica_pelo_codigo_da_pagina(navegador, monkeypatch):
    chamadas = substituir(monkeypatch, repositorio_vendedores, 'atualizar_vendedor')

    navegador.post('/administracao/vendedores/2/editar', data={
        'nome': 'Ana Lima Souza', 'cidade': 'Niterói', 'cod_vendedor': '1',
    })

    assert chamadas == [({'cod_vendedor': 2, 'nome': 'Ana Lima Souza', 'cidade': 'Niterói'},)]


def test_vendedor_pendente_nao_simula_sucesso(navegador, monkeypatch):
    for nome in ('cadastrar_vendedor', 'atualizar_vendedor', 'excluir_vendedor', 'buscar_vendedor'):
        substituir_com_erro(monkeypatch, repositorio_vendedores, nome, NotImplementedError())

    inclusao = navegador.post('/administracao/vendedores/novo', data={'nome': 'Ana Lima', 'cidade': 'Niterói'})
    edicao = navegador.post('/administracao/vendedores/2/editar', data={'nome': 'Ana', 'cidade': 'Maricá'})
    exclusao = navegador.post('/administracao/vendedores/2/excluir', follow_redirects=True)

    assert inclusao.status_code == 200
    assert 'Operação indisponível' in texto(inclusao)
    assert 'value="Ana Lima"' in texto(inclusao)
    assert 'Operação indisponível' in texto(edicao)
    assert 'Operação indisponível' in texto(exclusao)
    assert 'Vendedor excluído.' not in texto(exclusao)


def test_exclusao_de_vendedor_com_vendas_mostra_a_recusa(navegador, monkeypatch):
    substituir_com_erro(monkeypatch, repositorio_vendedores, 'excluir_vendedor',
                        errors.ForeignKeyViolation('violação simulada'))
    monkeypatch.setattr(repositorio_vendedores, 'buscar_vendedor', buscar_na_lista(
        [{'cod_vendedor': 1, 'nome': 'Ana Lima', 'cidade': 'Niterói'}], 'cod_vendedor'))

    pagina = texto(navegador.post('/administracao/vendedores/1/excluir', follow_redirects=True))

    assert 'não pode ser excluído porque está registrado em vendas' in pagina
    assert 'Niterói' in pagina

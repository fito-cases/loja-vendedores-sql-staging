"""Regras do esquema loja, verificadas com comandos SQL diretos no banco.

Cada teste começa com o esquema e os dados iniciais recriados (banco_recriado).
"""
from decimal import Decimal

import pytest
from psycopg import errors

import db

pytestmark = pytest.mark.usefixtures('banco_recriado')


def estoque_do_produto(cod_produto):
    sql = """
        SELECT qtd_estoque
        FROM produtos
        WHERE cod_produto = %(cod_produto)s
    """
    return db.consultar_valor(sql, {'cod_produto': cod_produto})


def valor_da_venda(numero_venda):
    sql = """
        SELECT valor
        FROM vendas
        WHERE numero_venda = %(numero_venda)s
    """
    return db.consultar_valor(sql, {'numero_venda': numero_venda})


def test_testes_usam_o_esquema_de_testes():
    esquemas = db.ler_esquemas()

    assert db.consultar_valor('SELECT current_schema()') == esquemas['testes']
    assert esquemas['testes'] != esquemas['sistema']


def test_oito_tabelas_com_datas_controladas_pelo_banco():
    sql = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND column_name IN ('created_at', 'updated_at')
    """
    colunas = db.consultar(sql)

    tabelas = set()
    for coluna in colunas:
        assert coluna['data_type'] == 'timestamp with time zone'
        assert coluna['is_nullable'] == 'NO'
        tabelas.add(coluna['table_name'])
    assert len(colunas) == 16
    assert tabelas == {
        'categorias', 'fornecedores', 'vendedores', 'clientes',
        'produtos', 'vendas', 'itens_vendas', 'fornecimentos',
    }


def test_criacao_preservada_e_atualizacao_registrada():
    inclusao = db.consultar_um(
        """
        INSERT INTO categorias (nome)
        VALUES ('Moda praia')
        RETURNING cod_categoria, created_at, updated_at
        """
    )
    assert inclusao['created_at'] == inclusao['updated_at']

    db.executar(
        """
        UPDATE categorias
        SET nome = 'Moda praia e piscina',
            created_at = '2000-01-01'
        WHERE cod_categoria = %(cod_categoria)s
        """,
        {'cod_categoria': inclusao['cod_categoria']},
    )
    depois = db.consultar_um(
        """
        SELECT created_at, updated_at
        FROM categorias
        WHERE cod_categoria = %(cod_categoria)s
        """,
        {'cod_categoria': inclusao['cod_categoria']},
    )

    assert depois['created_at'] == inclusao['created_at']
    assert depois['updated_at'] > inclusao['updated_at']


def test_chave_primaria_composta_recusa_repeticao():
    with pytest.raises(errors.UniqueViolation):
        db.executar(
            """
            INSERT INTO fornecimentos (cod_fornecedor, cod_produto)
            VALUES (1, 1)
            """
        )

    estoque_antes = estoque_do_produto(1)
    with pytest.raises(errors.UniqueViolation):
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (102, 1, 1, 25.00)
            """
        )
    assert estoque_do_produto(1) == estoque_antes
    assert valor_da_venda(102) == Decimal('80.00')


def test_referencias_inexistentes_recusadas():
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar(
            """
            INSERT INTO vendas (cod_cliente, data_venda)
            VALUES (999, '2025-06-10')
            """
        )
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (999, 1, 1, 25.00)
            """
        )
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (104, 999, 1, 25.00)
            """
        )
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar(
            """
            INSERT INTO fornecimentos (cod_fornecedor, cod_produto)
            VALUES (999, 1)
            """
        )
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar(
            """
            INSERT INTO produtos (descricao, preco, qtd_estoque, estoque_minimo, cod_categoria)
            VALUES ('Produto sem categoria válida', 10.00, 1, 0, 999)
            """
        )


def test_exclusao_de_registros_referenciados_recusada():
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar('DELETE FROM clientes WHERE cod_cliente = 1')
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar('DELETE FROM produtos WHERE cod_produto = 1')
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar('DELETE FROM categorias WHERE cod_categoria = 1')
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar('DELETE FROM fornecedores WHERE cod_fornecedor = 1')
    with pytest.raises(errors.ForeignKeyViolation):
        db.executar('DELETE FROM vendas WHERE numero_venda = 102')

    assert valor_da_venda(102) is not None
    assert estoque_do_produto(1) == 40


def test_colunas_opcionais_aceitam_ausencia():
    numero = db.consultar_valor(
        """
        INSERT INTO vendas (cod_cliente, cod_vendedor, data_venda)
        VALUES (11, NULL, '2025-06-10')
        RETURNING numero_venda
        """
    )
    cod_produto = db.consultar_valor(
        """
        INSERT INTO produtos (descricao, preco, qtd_estoque, estoque_minimo, cod_categoria)
        VALUES ('Necessaire de viagem', 35.00, 4, 1, NULL)
        RETURNING cod_produto
        """
    )
    cod_cliente = db.consultar_valor(
        """
        INSERT INTO clientes (nome, rua_numero, bairro, cidade, estado, cep, telefone)
        VALUES ('Cliente sem telefone', 'Rua A, 1', 'Centro', 'Niterói', 'RJ', '24020-000', NULL)
        RETURNING cod_cliente
        """
    )

    assert numero == 107
    assert cod_produto == 17
    assert cod_cliente == 13
    assert valor_da_venda(107) == Decimal('0.00')


def test_campos_obrigatorios_recusam_ausencia():
    with pytest.raises(errors.NotNullViolation):
        db.executar("INSERT INTO categorias (nome) VALUES (NULL)")
    with pytest.raises(errors.NotNullViolation):
        db.executar(
            """
            INSERT INTO vendas (cod_cliente, data_venda)
            VALUES (NULL, '2025-06-10')
            """
        )


def test_valores_negativos_e_quantidade_zero_recusados():
    with pytest.raises(errors.CheckViolation):
        db.executar("UPDATE produtos SET preco = -1 WHERE cod_produto = 16")
    with pytest.raises(errors.CheckViolation):
        db.executar("UPDATE produtos SET qtd_estoque = -1 WHERE cod_produto = 16")
    with pytest.raises(errors.CheckViolation):
        db.executar("UPDATE produtos SET estoque_minimo = -1 WHERE cod_produto = 16")
    with pytest.raises(errors.CheckViolation):
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (104, 16, 0, 12.00)
            """
        )
    with pytest.raises(errors.CheckViolation):
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (104, 16, 1, -12.00)
            """
        )
    assert estoque_do_produto(16) == 25
    assert valor_da_venda(104) == Decimal('0.00')


def test_valor_da_venda_so_muda_pelos_itens():
    with pytest.raises(errors.CheckViolation):
        db.executar("UPDATE vendas SET valor = 10.00 WHERE numero_venda = 104")
    with pytest.raises(errors.CheckViolation):
        db.executar(
            """
            INSERT INTO vendas (cod_cliente, data_venda, valor)
            VALUES (1, '2025-06-10', 50.00)
            """
        )
    assert valor_da_venda(104) == Decimal('0.00')


def test_itens_gravados_diretamente_mantem_estoque_e_valor():
    db.executar(
        """
        INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
        VALUES (104, 2, 2, 39.90)
        """
    )
    assert estoque_do_produto(2) == 18
    assert valor_da_venda(104) == Decimal('79.80')

    db.executar(
        """
        UPDATE itens_vendas
        SET quantidade = 3
        WHERE numero_venda = 104
          AND cod_produto = 2
        """
    )
    assert estoque_do_produto(2) == 17
    assert valor_da_venda(104) == Decimal('119.70')

    db.executar(
        """
        DELETE FROM itens_vendas
        WHERE numero_venda = 104
          AND cod_produto = 2
        """
    )
    assert estoque_do_produto(2) == 20
    assert valor_da_venda(104) == Decimal('0.00')


def test_estoque_insuficiente_recusado_pelo_banco():
    with pytest.raises(errors.CheckViolation) as recusa:
        db.executar(
            """
            INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
            VALUES (104, 7, 1, 55.00)
            """
        )
    assert recusa.value.diag.constraint_name == 'estoque_suficiente'
    assert estoque_do_produto(7) == 0
    assert valor_da_venda(104) == Decimal('0.00')


def test_transacao_desfaz_escrita_valida_seguida_de_recusa():
    with pytest.raises(errors.CheckViolation):
        with db.transacao() as conexao:
            conexao.execute("INSERT INTO categorias (nome) VALUES ('Categoria temporária')")
            conexao.execute("UPDATE produtos SET preco = -5 WHERE cod_produto = 16")

    sobra = db.consultar(
        """
        SELECT cod_categoria
        FROM categorias
        WHERE nome = 'Categoria temporária'
        """
    )
    assert sobra == []
    assert db.consultar_valor('SELECT preco FROM produtos WHERE cod_produto = 16') == Decimal('12.00')

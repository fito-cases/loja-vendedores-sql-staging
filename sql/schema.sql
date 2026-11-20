-- Esquema da loja: oito tabelas no esquema privado loja (PostgreSQL).
--
-- Executado por recriar_banco.py junto com dados.sql, em UMA transação: se
-- algum comando falhar, nada é confirmado. Remove e recria somente os objetos
-- conhecidos do esquema loja, sem CASCADE, e nunca toca no esquema public.
--
-- Regras de integridade ficam no banco e valem também para comandos SQL
-- escritos diretamente, fora da aplicação:
--   * chaves primárias e estrangeiras; venda sem vendedor e produto sem
--     categoria são permitidos (colunas opcionais);
--   * registros referenciados não podem ser excluídos (ON DELETE RESTRICT);
--   * preço, estoque e valor nunca negativos; quantidade sempre positiva;
--   * gatilhos mantêm o estoque e o valor da venda a partir dos itens;
--   * created_at e updated_at são preenchidos pelo próprio banco.

CREATE SCHEMA IF NOT EXISTS loja;


-- ---------------------------------------------------------------------------
-- 1. Remoção do que já existir (tabelas filhas antes das referenciadas)
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS loja.itens_vendas;
DROP TABLE IF EXISTS loja.fornecimentos;
DROP TABLE IF EXISTS loja.vendas;
DROP TABLE IF EXISTS loja.produtos;
DROP TABLE IF EXISTS loja.clientes;
DROP TABLE IF EXISTS loja.vendedores;
DROP TABLE IF EXISTS loja.fornecedores;
DROP TABLE IF EXISTS loja.categorias;

DROP FUNCTION IF EXISTS loja.registrar_datas();
DROP FUNCTION IF EXISTS loja.conferir_valor_da_venda();
DROP FUNCTION IF EXISTS loja.aplicar_item_de_venda();
DROP FUNCTION IF EXISTS loja.baixar_estoque(integer, integer);
DROP FUNCTION IF EXISTS loja.devolver_estoque(integer, integer);
DROP FUNCTION IF EXISTS loja.somar_ao_valor_da_venda(integer, numeric);


-- ---------------------------------------------------------------------------
-- 2. Tabelas (referenciadas antes das filhas)
-- ---------------------------------------------------------------------------

CREATE TABLE loja.categorias (
    cod_categoria integer GENERATED ALWAYS AS IDENTITY,
    nome          varchar(50) NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT categorias_pk PRIMARY KEY (cod_categoria)
);

CREATE TABLE loja.fornecedores (
    cod_fornecedor integer GENERATED ALWAYS AS IDENTITY,
    razao_social   varchar(100) NOT NULL,
    cidade         varchar(70)  NOT NULL,
    estado         char(2)      NOT NULL,
    created_at     timestamptz  NOT NULL DEFAULT now(),
    updated_at     timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT fornecedores_pk PRIMARY KEY (cod_fornecedor),
    CONSTRAINT fornecedores_estado_sigla CHECK (estado ~ '^[A-Z]{2}$')
);

CREATE TABLE loja.vendedores (
    cod_vendedor integer GENERATED ALWAYS AS IDENTITY,
    nome         varchar(100) NOT NULL,
    cidade       varchar(70)  NOT NULL,
    created_at   timestamptz  NOT NULL DEFAULT now(),
    updated_at   timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT vendedores_pk PRIMARY KEY (cod_vendedor)
);

CREATE TABLE loja.clientes (
    cod_cliente integer GENERATED ALWAYS AS IDENTITY,
    nome        varchar(100) NOT NULL,
    rua_numero  varchar(70)  NOT NULL,
    bairro      varchar(70)  NOT NULL,
    cidade      varchar(70)  NOT NULL,
    estado      char(2)      NOT NULL,
    cep         varchar(10)  NOT NULL,
    telefone    varchar(20),
    created_at  timestamptz  NOT NULL DEFAULT now(),
    updated_at  timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT clientes_pk PRIMARY KEY (cod_cliente),
    CONSTRAINT clientes_estado_sigla CHECK (estado ~ '^[A-Z]{2}$')
);

CREATE TABLE loja.produtos (
    cod_produto    integer GENERATED ALWAYS AS IDENTITY,
    descricao      varchar(100) NOT NULL,
    preco          numeric(5,2) NOT NULL,
    qtd_estoque    integer      NOT NULL,
    estoque_minimo integer      NOT NULL,
    cod_categoria  integer,
    created_at     timestamptz  NOT NULL DEFAULT now(),
    updated_at     timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT produtos_pk PRIMARY KEY (cod_produto),
    CONSTRAINT produtos_preco_nao_negativo CHECK (preco >= 0),
    CONSTRAINT produtos_estoque_nao_negativo CHECK (qtd_estoque >= 0),
    CONSTRAINT produtos_minimo_nao_negativo CHECK (estoque_minimo >= 0),
    CONSTRAINT produtos_categoria_fk FOREIGN KEY (cod_categoria)
        REFERENCES loja.categorias (cod_categoria) ON DELETE RESTRICT
);

CREATE TABLE loja.vendas (
    numero_venda integer GENERATED ALWAYS AS IDENTITY,
    cod_cliente  integer       NOT NULL,
    cod_vendedor integer,
    data_venda   date          NOT NULL,
    valor        numeric(10,2) NOT NULL DEFAULT 0,
    created_at   timestamptz   NOT NULL DEFAULT now(),
    updated_at   timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT vendas_pk PRIMARY KEY (numero_venda),
    CONSTRAINT vendas_valor_nao_negativo CHECK (valor >= 0),
    CONSTRAINT vendas_cliente_fk FOREIGN KEY (cod_cliente)
        REFERENCES loja.clientes (cod_cliente) ON DELETE RESTRICT,
    CONSTRAINT vendas_vendedor_fk FOREIGN KEY (cod_vendedor)
        REFERENCES loja.vendedores (cod_vendedor) ON DELETE RESTRICT
);

CREATE TABLE loja.itens_vendas (
    numero_venda   integer       NOT NULL,
    cod_produto    integer       NOT NULL,
    quantidade     integer       NOT NULL,
    preco_unitario numeric(10,2) NOT NULL,
    created_at     timestamptz   NOT NULL DEFAULT now(),
    updated_at     timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT itens_vendas_pk PRIMARY KEY (numero_venda, cod_produto),
    CONSTRAINT itens_vendas_quantidade_positiva CHECK (quantidade > 0),
    CONSTRAINT itens_vendas_preco_nao_negativo CHECK (preco_unitario >= 0),
    CONSTRAINT itens_vendas_venda_fk FOREIGN KEY (numero_venda)
        REFERENCES loja.vendas (numero_venda) ON DELETE RESTRICT,
    CONSTRAINT itens_vendas_produto_fk FOREIGN KEY (cod_produto)
        REFERENCES loja.produtos (cod_produto) ON DELETE RESTRICT
);

CREATE TABLE loja.fornecimentos (
    cod_fornecedor integer     NOT NULL,
    cod_produto    integer     NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fornecimentos_pk PRIMARY KEY (cod_fornecedor, cod_produto),
    CONSTRAINT fornecimentos_fornecedor_fk FOREIGN KEY (cod_fornecedor)
        REFERENCES loja.fornecedores (cod_fornecedor) ON DELETE RESTRICT,
    CONSTRAINT fornecimentos_produto_fk FOREIGN KEY (cod_produto)
        REFERENCES loja.produtos (cod_produto) ON DELETE RESTRICT
);

-- Índices para as colunas de chave estrangeira que não iniciam uma chave primária.
CREATE INDEX produtos_cod_categoria_idx ON loja.produtos (cod_categoria);
CREATE INDEX vendas_cod_cliente_idx ON loja.vendas (cod_cliente);
CREATE INDEX vendas_cod_vendedor_idx ON loja.vendas (cod_vendedor);
CREATE INDEX vendas_data_venda_idx ON loja.vendas (data_venda);
CREATE INDEX itens_vendas_cod_produto_idx ON loja.itens_vendas (cod_produto);
CREATE INDEX fornecimentos_cod_produto_idx ON loja.fornecimentos (cod_produto);


-- ---------------------------------------------------------------------------
-- 3. Datas de criação e de última atualização (todas as tabelas)
-- ---------------------------------------------------------------------------

CREATE FUNCTION loja.registrar_datas()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.created_at := now();
    ELSE
        NEW.created_at := OLD.created_at;
    END IF;
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.categorias
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.fornecedores
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.vendedores
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.clientes
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.produtos
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.vendas
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.itens_vendas
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();
CREATE TRIGGER registrar_datas BEFORE INSERT OR UPDATE ON loja.fornecimentos
    FOR EACH ROW EXECUTE FUNCTION loja.registrar_datas();


-- ---------------------------------------------------------------------------
-- 4. Estoque e valor da venda acompanham os itens
-- ---------------------------------------------------------------------------

-- Retira unidades do estoque. A linha do produto fica bloqueada até o fim da
-- transação, então duas vendas simultâneas não usam as mesmas unidades.
CREATE FUNCTION loja.baixar_estoque(codigo_produto integer, unidades integer)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    disponivel integer;
BEGIN
    SELECT qtd_estoque
      INTO disponivel
      FROM loja.produtos
     WHERE cod_produto = codigo_produto
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'O produto % não existe.', codigo_produto
            USING ERRCODE = 'foreign_key_violation',
                  CONSTRAINT = 'itens_vendas_produto_fk';
    END IF;

    IF disponivel < unidades THEN
        RAISE EXCEPTION 'Estoque insuficiente: há % unidade(s) do produto % e foram pedidas %.',
                        disponivel, codigo_produto, unidades
            USING ERRCODE = 'check_violation',
                  CONSTRAINT = 'estoque_suficiente';
    END IF;

    UPDATE loja.produtos
       SET qtd_estoque = qtd_estoque - unidades
     WHERE cod_produto = codigo_produto;
END;
$$;

-- Devolve unidades ao estoque.
CREATE FUNCTION loja.devolver_estoque(codigo_produto integer, unidades integer)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE loja.produtos
       SET qtd_estoque = qtd_estoque + unidades
     WHERE cod_produto = codigo_produto;
END;
$$;

-- Soma uma diferença (positiva ou negativa) ao valor registrado da venda.
CREATE FUNCTION loja.somar_ao_valor_da_venda(numero integer, diferenca numeric)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE loja.vendas
       SET valor = valor + diferenca
     WHERE numero_venda = numero;
END;
$$;

-- Depois de incluir, alterar ou excluir um item, ajusta estoque e valor na
-- mesma transação do comando. O valor de cada item é quantidade x preço
-- unitário histórico; o preço atual do produto não entra nesta conta.
CREATE FUNCTION loja.aplicar_item_de_venda()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM loja.baixar_estoque(NEW.cod_produto, NEW.quantidade);
        PERFORM loja.somar_ao_valor_da_venda(NEW.numero_venda, NEW.quantidade * NEW.preco_unitario);
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        PERFORM loja.devolver_estoque(OLD.cod_produto, OLD.quantidade);
        PERFORM loja.somar_ao_valor_da_venda(OLD.numero_venda, -(OLD.quantidade * OLD.preco_unitario));
        RETURN OLD;
    END IF;

    -- UPDATE com o mesmo produto: aplica só a diferença de quantidade.
    IF NEW.cod_produto = OLD.cod_produto THEN
        IF NEW.quantidade > OLD.quantidade THEN
            PERFORM loja.baixar_estoque(NEW.cod_produto, NEW.quantidade - OLD.quantidade);
        ELSIF NEW.quantidade < OLD.quantidade THEN
            PERFORM loja.devolver_estoque(NEW.cod_produto, OLD.quantidade - NEW.quantidade);
        END IF;
    -- UPDATE com troca de produto: devolve o anterior e baixa o novo.
    ELSE
        PERFORM loja.devolver_estoque(OLD.cod_produto, OLD.quantidade);
        PERFORM loja.baixar_estoque(NEW.cod_produto, NEW.quantidade);
    END IF;

    PERFORM loja.somar_ao_valor_da_venda(OLD.numero_venda, -(OLD.quantidade * OLD.preco_unitario));
    PERFORM loja.somar_ao_valor_da_venda(NEW.numero_venda, NEW.quantidade * NEW.preco_unitario);
    RETURN NEW;
END;
$$;

CREATE TRIGGER aplicar_item_de_venda AFTER INSERT OR UPDATE OR DELETE ON loja.itens_vendas
    FOR EACH ROW EXECUTE FUNCTION loja.aplicar_item_de_venda();

-- A venda começa com valor zero, e o valor só muda pelos itens. Um UPDATE
-- feito diretamente (fora do gatilho dos itens) não pode alterar o valor.
CREATE FUNCTION loja.conferir_valor_da_venda()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.valor <> 0 THEN
        RAISE EXCEPTION 'Uma venda começa sem itens, com valor zero.'
            USING ERRCODE = 'check_violation',
                  CONSTRAINT = 'valor_calculado_pelos_itens';
    END IF;

    -- pg_trigger_depth() = 1: o UPDATE não veio do gatilho dos itens.
    IF TG_OP = 'UPDATE' AND NEW.valor <> OLD.valor AND pg_trigger_depth() = 1 THEN
        RAISE EXCEPTION 'O valor da venda é calculado pelos itens e não pode ser alterado diretamente.'
            USING ERRCODE = 'check_violation',
                  CONSTRAINT = 'valor_calculado_pelos_itens';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER conferir_valor_da_venda BEFORE INSERT OR UPDATE ON loja.vendas
    FOR EACH ROW EXECUTE FUNCTION loja.conferir_valor_da_venda();

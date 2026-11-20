-- Dados iniciais da loja (fictícios). Executado por recriar_banco.py em UMA
-- transação: depois de schema.sql na recriação completa e, nos testes, sozinho
-- antes de cada teste, para voltar ao ponto de partida sem recriar as tabelas.
--
-- Os códigos são fixos para que os testes conheçam o cenário. Por isso os
-- INSERTs usam OVERRIDING SYSTEM VALUE e, ao final, cada sequência é ajustada
-- para que a próxima inclusão receba o código seguinte.
--
-- As vendas são criadas com valor zero e os itens são incluídos depois: os
-- gatilhos do esquema baixam o estoque e calculam o valor de cada venda.
-- Por isso qtd_estoque, abaixo, é o estoque ANTES das vendas.
--
-- Cenário reservado para os testes:
--   * vendedores 1 e 2 se chamam Ana Lima (Niterói e Maricá); 2 não tem vendas;
--   * clientes 1 e 2 se chamam Lia Costa (endereços diferentes); 3 é Caio Lopes;
--     clientes 11 e 12 não têm compras;
--   * categoria 11 não tem produtos; produto 16 não tem categoria, fornecedor
--     nem vendas; fornecedor 11 não fornece produtos;
--   * de 01 a 09/06/2025 só existem as vendas 101 a 106; em 10/06/2025 não há
--     vendas; as demais vendas são de maio de 2025.


-- Linhas existentes (tabelas filhas antes das referenciadas) -------------------

DELETE FROM itens_vendas;
DELETE FROM fornecimentos;
DELETE FROM vendas;
DELETE FROM produtos;
DELETE FROM clientes;
DELETE FROM vendedores;
DELETE FROM fornecedores;
DELETE FROM categorias;


-- Categorias ------------------------------------------------------------------

INSERT INTO categorias (cod_categoria, nome)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'Camisetas'),
    (2, 'Calças e bermudas'),
    (3, 'Vestidos'),
    (4, 'Bolsas'),
    (5, 'Cintos'),
    (6, 'Bijuterias'),
    (7, 'Roupa de cama'),
    (8, 'Banho'),
    (9, 'Mesa'),
    (10, 'Meias'),
    (11, 'Pijamas');


-- Fornecedores ----------------------------------------------------------------

INSERT INTO fornecedores (cod_fornecedor, razao_social, cidade, estado)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'Malharia Serra Azul Ltda.', 'Petrópolis', 'RJ'),
    (2, 'Têxtil Vale Verde S.A.', 'Blumenau', 'SC'),
    (3, 'Confecções Atlântica Ltda.', 'Niterói', 'RJ'),
    (4, 'Jeans Agreste Indústria Ltda.', 'Toritama', 'PE'),
    (5, 'Couros do Sul Acessórios Ltda.', 'Novo Hamburgo', 'RS'),
    (6, 'Brilho Fino Bijuterias Ltda.', 'Limeira', 'SP'),
    (7, 'Enxovais Casa Serena Ltda.', 'Brusque', 'SC'),
    (8, 'Felpudos Paraíso Têxtil Ltda.', 'Americana', 'SP'),
    (9, 'Meias Passo Leve Ltda.', 'Indaial', 'SC'),
    (10, 'Tecidos Fluminense Distribuidora Ltda.', 'Rio de Janeiro', 'RJ'),
    (11, 'Ateliê Mesa Bonita Ltda.', 'Nova Friburgo', 'RJ');


-- Vendedores ------------------------------------------------------------------

INSERT INTO vendedores (cod_vendedor, nome, cidade)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'Ana Lima', 'Niterói'),
    (2, 'Ana Lima', 'Maricá'),
    (3, 'Bruno Carvalho', 'São Gonçalo'),
    (4, 'Carla Dias', 'Niterói'),
    (5, 'Diego Martins', 'Itaboraí'),
    (6, 'Elisa Fontes', 'Niterói'),
    (7, 'Felipe Araújo', 'Maricá'),
    (8, 'Gabriela Teixeira', 'São Gonçalo'),
    (9, 'Henrique Moura', 'Niterói'),
    (10, 'Isabela Freitas', 'Rio de Janeiro');


-- Clientes --------------------------------------------------------------------

INSERT INTO clientes (cod_cliente, nome, rua_numero, bairro, cidade, estado, cep, telefone)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'Lia Costa', 'Rua das Acácias, 120', 'Icaraí', 'Niterói', 'RJ', '24230-000', '(21) 90000-0101'),
    (2, 'Lia Costa', 'Avenida Central, 45', 'Centro', 'Maricá', 'RJ', '24900-000', NULL),
    (3, 'Caio Lopes', 'Rua do Porto, 300', 'Ponta d''Areia', 'Niterói', 'RJ', '24040-000', '(21) 90000-0103'),
    (4, 'Marina Souza', 'Rua dos Ipês, 18', 'Alcântara', 'São Gonçalo', 'RJ', '24710-000', '(21) 90000-0104'),
    (5, 'Rafael Mendes', 'Travessa da Praia, 7', 'Charitas', 'Niterói', 'RJ', '24370-000', NULL),
    (6, 'Beatriz Almeida', 'Rua Aurora, 512', 'Tijuca', 'Rio de Janeiro', 'RJ', '20510-000', '(21) 90000-0106'),
    (7, 'Thiago Ribeiro', 'Estrada do Engenho, 88', 'Centro', 'Itaboraí', 'RJ', '24800-000', '(21) 90000-0107'),
    (8, 'Juliana Pereira', 'Rua das Palmeiras, 61', 'Santa Rosa', 'Niterói', 'RJ', '24240-000', '(21) 90000-0108'),
    (9, 'Fernanda Rocha', 'Rua Nova, 230', 'Zé Garoto', 'São Gonçalo', 'RJ', '24440-000', NULL),
    (10, 'Gustavo Nunes', 'Rua da Lagoa, 14', 'Araçatiba', 'Maricá', 'RJ', '24900-000', '(21) 90000-0110'),
    (11, 'Patrícia Gomes', 'Rua do Sol, 99', 'Fonseca', 'Niterói', 'RJ', '24120-000', '(21) 90000-0111'),
    (12, 'André Barbosa', 'Rua Projetada, 3', 'Centro', 'Rio Bonito', 'RJ', '28800-000', NULL);


-- Produtos (qtd_estoque = estoque antes das vendas abaixo) --------------------

INSERT INTO produtos (cod_produto, descricao, preco, qtd_estoque, estoque_minimo, cod_categoria)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'Camiseta básica de algodão', 25.00, 48, 10, 1),
    (2, 'Camiseta estampada', 39.90, 23, 5, 1),
    (3, 'Calça jeans reta', 119.90, 16, 4, 2),
    (4, 'Bermuda de sarja', 79.90, 13, 4, 2),
    (5, 'Vestido midi floral', 149.90, 4, 3, 3),
    (6, 'Bolsa transversal', 89.90, 9, 3, 4),
    (7, 'Cinto de couro marrom', 55.00, 0, 4, 5),
    (8, 'Brinco de argola dourado', 30.00, 33, 8, 6),
    (9, 'Jogo de lençol casal 150 fios', 129.90, 7, 2, 7),
    (10, 'Fronha de algodão', 19.90, 26, 6, 7),
    (11, 'Toalha de banho felpuda', 45.00, 20, 6, 8),
    (12, 'Toalha de rosto felpuda', 22.00, 3, 5, 8),
    (13, 'Toalha de mesa retangular', 69.90, 11, 3, 9),
    (14, 'Jogo americano com 4 peças', 49.90, 9, 2, 9),
    (15, 'Kit com 3 pares de meias', 29.90, 37, 10, 10),
    (16, 'Sacola retornável de tecido', 12.00, 25, 5, NULL);


-- Fornecimentos (quais fornecedores oferecem quais produtos) ------------------

INSERT INTO fornecimentos (cod_fornecedor, cod_produto)
VALUES
    (1, 1),
    (1, 2),
    (2, 9),
    (2, 11),
    (3, 1),
    (3, 2),
    (3, 5),
    (4, 3),
    (4, 4),
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 9),
    (7, 10),
    (8, 11),
    (8, 12),
    (9, 15),
    (10, 13),
    (10, 14);


-- Vendas (valor começa em zero; os itens calculam o valor) --------------------

INSERT INTO vendas (numero_venda, cod_cliente, cod_vendedor, data_venda)
OVERRIDING SYSTEM VALUE
VALUES
    (91, 4, 3, '2025-05-05'),
    (92, 5, 4, '2025-05-08'),
    (93, 6, 1, '2025-05-10'),
    (94, 7, NULL, '2025-05-12'),
    (95, 8, 5, '2025-05-15'),
    (96, 4, 6, '2025-05-19'),
    (97, 9, 7, '2025-05-22'),
    (98, 10, 8, '2025-05-26'),
    (99, 5, NULL, '2025-05-28'),
    (100, 6, 3, '2025-05-31'),
    (101, 3, 1, '2025-06-01'),
    (102, 1, 1, '2025-06-02'),
    (103, 1, NULL, '2025-06-03'),
    (104, 2, NULL, '2025-06-03'),
    (105, 3, 1, '2025-06-08'),
    (106, 3, NULL, '2025-06-09');


-- Itens (preco_unitario é o preço praticado na data da venda) -----------------

INSERT INTO itens_vendas (numero_venda, cod_produto, quantidade, preco_unitario)
VALUES
    (91, 3, 1, 119.90),
    (91, 15, 2, 27.90),
    (92, 5, 1, 149.90),
    (93, 9, 1, 129.90),
    (93, 10, 2, 19.90),
    (94, 11, 2, 42.00),
    (95, 6, 1, 89.90),
    (96, 2, 3, 39.90),
    (97, 13, 1, 69.90),
    (97, 14, 1, 49.90),
    (98, 4, 1, 79.90),
    (99, 12, 2, 22.00),
    (99, 1, 1, 22.90),
    (100, 1, 2, 22.90),
    (101, 1, 1, 25.00),
    (102, 1, 2, 25.00),
    (102, 8, 1, 30.00),
    (103, 8, 1, 30.00),
    (105, 1, 1, 25.00),
    (105, 8, 1, 30.00),
    (106, 1, 1, 25.00);


-- Próximos códigos gerados ----------------------------------------------------

SELECT setval(pg_get_serial_sequence('categorias', 'cod_categoria'), 11);
SELECT setval(pg_get_serial_sequence('fornecedores', 'cod_fornecedor'), 11);
SELECT setval(pg_get_serial_sequence('vendedores', 'cod_vendedor'), 10);
SELECT setval(pg_get_serial_sequence('clientes', 'cod_cliente'), 12);
SELECT setval(pg_get_serial_sequence('produtos', 'cod_produto'), 16);
SELECT setval(pg_get_serial_sequence('vendas', 'numero_venda'), 106);

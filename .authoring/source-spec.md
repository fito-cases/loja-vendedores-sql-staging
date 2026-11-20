# Especificação da fonte — Cadastro de vendedores e relatório semanal de uma loja

Caso de implementação 1.0.0, em pt-BR. A gerência confere comprovantes, não itens nem estatísticas. O aluno recebe um sistema de varejo de vestuário, acessórios, cama, mesa e banho que já registra vendas. Entrega `code_change`: **Funções do cadastro de vendedores e do relatório semanal completas, respeitando as assinaturas e os retornos documentados.** São seis funções, não seis páginas a construir.

## Projeto que o aluno abre

| Área | Fluxo pronto nos dois estados |
|---|---|
| Vendas | Manter clientes (incluir, listar, abrir, editar e excluir quando permitido); abrir venda para cliente existente, com vendedor escolhido ou em branco; consultar e manter cabeçalho e itens, cancelar venda; conferir vendas por período. |
| Administração | Mesmas ações de cadastro para categorias, produtos, fornecedores e vendedores; manter pares fornecedor–produto; consultar disponíveis e produtos abaixo do mínimo. Sem geração automática de pedidos. |
| Páginas do exercício | Formulários, rotas, validação, mensagens, links e tabelas já prontos. Relatório abre na segunda a domingo da semana da data local da loja, aceita duas datas explícitas, rejeita data inválida, ausente em filtro parcial ou intervalo invertido. Exibe número, data, nome do cliente, nome do vendedor ou «Sem vendedor», e valor registrado. Ausência na **linha retornada pelo banco** é `None`, nunca esse rótulo. |

`app.py` cria a aplicação e registra os módulos de rotas. `rotas/` → `repositorios/` → `db.py` → PostgreSQL. Módulos espelhados `clientes`, `categorias`, `produtos`, `fornecedores`, `fornecimentos`, `vendas` (inclui itens), `vendedores`, `relatorios`; `templates/<modulo>/` herda de `templates/base.html`, com a mesma navegação, formulários, apresentação monetária e mensagens em português. `testes/test_<modulo>.py` por repositório. SQL e carga em `sql/schema.sql` e `sql/dados.sql`; `recriar_banco.py` é utilitário de autoria/configuração, **não** uma rota. `repositorios/categorias.py` é exemplo completo e pequeno, sem resolver os exercícios.

**Critério de legibilidade:** deve ser possível seguir uma ação lendo a rota, seu mapeador e uma função de repositório. Uma função curta por ação; nomes como `ler_dados_produto` e `buscar_cliente`; mapeador específico converte datas, inteiros, decimais e campos vazios e só entrega os campos esperados. Nunca passar o formulário bruto. SQL em strings de várias linhas, uma cláusula por linha, colunas e condições indentadas, parâmetros nomeados `%(nome)s` vinculados em separado. Preferir repetição curta e explícita a um gerador de CRUD. Sem classes próprias, ORM, decoradores próprios, metaprogramação, compreensões aninhadas, JavaScript ou frontend separado. Sem SQL nas rotas/templates; regras comuns de cálculo em funções puras de `regras.py` apenas se reutilizadas. `db.py`: `consultar`, `consultar_um`, `consultar_valor`, `executar` abrem uma conexão por chamada, confirmam em sucesso, desfazem em erro e fecham; linhas como dicionários. `transacao` compartilha uma conexão até confirmar/desfazer todo o bloco. Rotas mostram a recusa de integridade em linguagem compreensível na mesma página, sem traceback, senha nem URL de conexão.

## Modelo e integridade

Usar o esquema privado `loja` no banco de exercícios. Em **todas** as oito tabelas, `created_at` e `updated_at` gerenciados pelo banco (nomes do diagrama), sem histórico completo. Chaves simples inteiras geradas; valores monetários exatos em decimal, não ponto flutuante. Adaptar tipos do diagrama ao PostgreSQL, não copiar a sintaxe de outro banco.

| Tabela | Colunas de negócio e vínculos |
|---|---|
| clientes | `cod_cliente` PK, `nome`, `rua_numero`, `bairro`, `cidade`, `estado`, `cep`, `telefone` opcional. Sem obrigação de compra. |
| vendedores | `cod_vendedor` PK, `nome`, `cidade`. Nomes não são únicos. Sem obrigação de venda. |
| vendas | `numero_venda` PK, `cod_cliente` FK obrigatória, `cod_vendedor` FK opcional, `data_venda` data, `valor` decimal(10,2). Criar sem itens, com zero. |
| itens_vendas | PK composta (`numero_venda`, `cod_produto`), ambas FKs; `quantidade` inteira positiva, `preco_unitario` histórico decimal(10,2) não negativo. |
| produtos | `cod_produto` PK, `descricao`, `preco` decimal(5,2), `qtd_estoque`, `estoque_minimo` inteiros, todos os três valores não negativos; `cod_categoria` FK opcional. |
| categorias | `cod_categoria` PK, `nome`. Admite categoria sem produto. |
| fornecedores | `cod_fornecedor` PK, `razao_social`, `cidade`, `estado`. |
| fornecimentos | PK composta (`cod_fornecedor`, `cod_produto`), ambas FKs; só o vínculo N:N, sem preço, data de entrega ou quantidade recebida. Ambas as pontas podem ficar sem vínculo. |

Não vender além do disponível: na mesma transação, inserir item baixa unidades; editar quantidade aplica só a diferença; trocar produto recompõe o anterior e baixa o novo; excluir item ou venda devolve unidades exatamente uma vez. O total armazenado acompanha quantidade × preço histórico de cada item, inclusive após edição/remoção; alterar o preço de catálogo não muda a venda passada. Regras e travas no banco também valem para escritas diretas e concorrentes. Não permitir órfãos, preço/saldo negativo nem exclusão de produto referenciado por item. Escolha do projeto: recusar exclusão de vendedor referenciado, não apagar vendas nem desidentificá-las; é compatível com vendedor opcional no cadastro da venda. Sem pagamentos, parcelas, notas fiscais, compras de fornecedores, contas a pagar/receber nem novos relatórios analíticos.

## Fronteira do trabalho do aluno

| Arquivo / assinatura | Entrada → saída (mesma docstring nos dois estados) |
|---|---|
| `repositorios/vendedores.py`: `cadastrar_vendedor(dados)` | `nome`, `cidade` textos → inteiro `cod_vendedor` realmente gerado e persistido. |
| `listar_vendedores()` | Sem entrada → lista de fichas, uma por código, ou `[]`. Ficha = dicionário com `cod_vendedor`, `nome`, `cidade`. Sem contrato de ordem. |
| `buscar_vendedor(cod_vendedor)` | Inteiro → ficha ou `None`. |
| `atualizar_vendedor(dados)` | `cod_vendedor` inteiro, `nome`, `cidade` → `None`; código ausente não modifica ninguém. |
| `excluir_vendedor(cod_vendedor)` | Inteiro → `None`; código ausente não remove ninguém; recusa de integridade propagada à rota. |
| `repositorios/relatorios.py`: `listar_vendas_periodo(data_inicial, data_final)` | Duas datas já convertidas → lista, inclusive `[]`; dicionários com `numero_venda` inteiro, `data_venda` data, `cliente` texto, `vendedor` texto ou `None`, `valor` decimal armazenado. Uma linha por venda; datas inclusivas. |

Não exigir nenhuma mudança de esquema, massa, testes, rota ou template para concluir. Nem interpolação SQL, agregação estatística, recálculo do total no relatório ou dados pré-fixados. A venda operacional usa um seletor próprio de opções de vendedor, já pronto e mínimo (código e rótulo); não chamar a listagem incompleta nem duplicar a ficha do exercício. A tela do relatório usa as datas mesmo quando a semana não tem movimento.

## Ambiente e dados

O aluno fornece **Python 3 ou mais recente**, sem teto no projeto. Em ambiente virtual o projeto resolve Flask 3, psycopg[binary] 3, pytest 8 e python-dotenv 1 pelas respectivas linhas principais. Não prometer qualquer minor de Python 3 ou Python futuro: metadados das versões resolvidas e binários disponíveis para o sistema podem limitar o interpretador; documentar as combinações efetivamente ensaiadas. PostgreSQL 17 é **referência do serviço Supabase**, sem instalação local nem exigência de patch. O vocabulário SQL:1999 descreve a semântica dos comandos; não promete suporte uniforme nem faz de recursos PostgreSQL (p.ex., `RETURNING`) parte universal do padrão. Não há incompatibilidade declarada pela descrição dessa linha.

Conexão pelo Session pooler IPv4, com TLS e `.env` local; configurações da aplicação também no `.env`. Um projeto Supabase exclusivo por aluno/grupo, sem dados reais. Reset explícito, transacional, limitado a objetos conhecidos de `loja`, nunca do banco ou de `public`; identificação e confirmação do alvo antes de qualquer escrita, inclusive pelos testes. Executar testes em série e sem aplicação concorrente: ponto de partida reprodutível antes de **cada** teste de integração, pois conexões independentes confirmam alterações. Sem serviço, erro de configuração; não fingir sucesso nem substituir por SQLite. Pelo menos dez registros naturais por tabela, inclusive vendedores e vínculos; cenário fixo com homônimos, sem movimento, múltiplos itens e datas-limite conforme plano.

## Estados terminais e aceite

**Inicial — `main`, com `.case/`.** `build_status: not_applicable`: sem etapa de compilação obrigatória; instalação, importação, coleta e inicialização funcionam. Apenas os seis corpos indicados ficam com `TODO` e `raise NotImplementedError` sem SQL-resposta. Páginas dessas funções tratam indisponibilidade, sem simular sucesso. Não deixar implementação oculta, consultas prontas em comentários, histórico de solução ancestral ou indicação de resposta na interface. Não há `known_errors` nem mensagem de erro literal exigida. Os sete nomes abaixo são os rótulos integrais do contrato; usar uma função pytest por linha, com rótulo na docstring. A falha ocorre ao chamar diretamente o corpo pendente, não no preparo, nem por ausência de arquivo ou por falha de conexão.

| Rótulo do estado inicial | Função pytest / operação que ainda falta |
|---|---|
| Cadastro: inclusão persistida com chave devolvida | `test_inclusao_persistida` / inserir e devolver a chave |
| Cadastro: listagem e consulta individual por código | `test_lista_e_ficha` / listar e buscar |
| Cadastro: edição isolada do vendedor solicitado | `test_edicao_isolada` / editar por código |
| Cadastro: exclusão isolada quando permitida | `test_exclusao_isolada` / remover por código |
| Relatório: cliente e valor corretos por venda | `test_cliente_e_valor` / recuperar comprovantes |
| Relatório: preservação das vendas sem vendedor | `test_vendedor_opcional` / preservar venda sem identificação |
| Relatório: período com as duas datas inclusivas | `test_datas_inclusivas` / aplicar limites |

**Solução local — `case/solution-v1.0.0`, visível depois da conclusão.** Mesma base e testes, só mudam os seis corpos. A suíte planejada `python -m pytest -q` passa inteira; no inicial, o mesmo comando dá exatamente as sete falhas acima, todos os demais testes passam, nenhum ignorado. `.case/` idêntico entre branches. Não confundir branch de autoria com PR do aluno (`solution` → `v1.0.0`).

**Rubrica:** sete critérios `ai`, nenhum `automated` ou `hybrid`, nenhum `command` ou `passing_condition`. Pytest fornece evidência, não substitui leitura de SQL. Cadastro: inserir (12), listar/buscar (13), editar (13), excluir (12). Relatório: associar cliente sem duplicar (18), preservar ausência de vendedor (18), delimitar período (14). A matriz do plano especifica evidências até o nível exemplar.

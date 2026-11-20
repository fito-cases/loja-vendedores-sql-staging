# Loja — cadastro de vendedores e relatório semanal

Sistema web de uma loja de vestuário, acessórios e artigos de cama, mesa e banho.
Já registra vendas e tem duas áreas:

- **Vendas:** clientes (incluir, listar, abrir, editar, excluir), vendas com
  vendedor escolhido ou em branco, itens da venda (incluir, alterar
  quantidade, trocar produto, remover), cancelamento e a **conferência das
  vendas por período**.
- **Administração:** categorias, produtos, fornecedores, fornecimentos (quais
  fornecedores oferecem quais produtos), produtos disponíveis, produtos abaixo
  do estoque mínimo e o **cadastro de vendedores**.

A atividade do caso está em `repositorios/vendedores.py` (cinco funções) e em
`repositorios/relatorios.py` (uma função). As telas, rotas e testes dessas
duas funcionalidades já estão prontos; as assinaturas e docstrings descrevem
o que cada função recebe e devolve. `repositorios/categorias.py` é um exemplo
completo e pequeno do padrão dos repositórios.

## Organização

```
navegador -> rotas/*.py -> repositorios/*.py -> db.py -> PostgreSQL (Supabase)
                 |
                 v
          templates/<modulo>/*.html
```

| Caminho | Conteúdo |
|---|---|
| `app.py` | Cria a aplicação Flask e registra as rotas das duas áreas. |
| `rotas/` | Uma função por página ou ação. Lê o formulário, converte os campos (funções `ler_dados_...`), chama o repositório e mostra a página. Não contém SQL. |
| `repositorios/` | Uma função por comando SQL, com parâmetros nomeados `%(nome)s`. |
| `db.py` | `consultar`, `consultar_um`, `consultar_valor`, `executar` (uma conexão por chamada) e `transacao` (vários comandos confirmados juntos). Cada conexão usa só o esquema da aplicação (ou, nos testes, o esquema de testes). |
| `regras.py` | Funções puras usadas por várias rotas: conversão de campos, formatação em reais e datas, mensagens das recusas do banco. |
| `relogio.py` | Data de hoje no fuso da loja (`FUSO_LOJA`). |
| `templates/` | Páginas Jinja2, uma pasta por módulo, todas herdando de `base.html`. |
| `sql/schema.sql`, `sql/dados.sql` | Tabelas, restrições e gatilhos; dados iniciais fictícios. Os nomes não levam o esquema na frente: valem para o esquema escolhido no `.env`. |
| `recriar_banco.py` | Recria tabelas e dados iniciais do esquema da aplicação (não é uma página da aplicação). |
| `testes/` | Testes pytest: um arquivo por repositório, mais telas, banco, dados e proteções. |

As regras de integridade ficam no banco: chaves, `NOT NULL`, valores não
negativos, exclusão recusada para registros referenciados e gatilhos que
mantêm o estoque e o valor de cada venda a partir dos itens.

## Requisitos

- **Python 3** (veja as combinações ensaiadas abaixo). Confira com `python --version`.
- Dependências, em `requirements.txt`: Flask 3, psycopg 3 com o extra binary,
  pytest 8, python-dotenv 1 e, só no Windows, tzdata (a base de fusos horários
  que o Windows não traz e que o módulo `zoneinfo` usa para saber a data na
  loja).
- **Um projeto Supabase exclusivo do seu grupo**, sem dados reais. O serviço
  usa PostgreSQL 17. Não é preciso instalar PostgreSQL no computador.

## Instalação

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pip check
```

## Configuração (`.env`)

1. Copie `.env.example` para `.env` (o `.env` nunca é versionado).
2. Em `BANCO_URL`, cole a connection string do **Session pooler** do **seu**
   projeto (painel do Supabase: *Connect → Connection string → Session pooler*).
   Ela tem a forma
   `postgresql://postgres.xxxx:[SENHA]@aws-N-regiao.pooler.supabase.com:5432/postgres`.
   - Troque `[SENHA]` pela senha do banco. Caracteres especiais da senha
     precisam ser codificados: `@` → `%40`, `:` → `%3A`, `/` → `%2F`,
     `#` → `%23`, `?` → `%3F`, `%` → `%25`, `&` → `%26`.
   - Acrescente `?sslmode=require` ao final, para exigir conexão com TLS.
   - Use a porta 5432 (Session pooler), não a 6543.
3. `ESQUEMA_SISTEMA` (ex.: `loja`) é o esquema usado pela aplicação;
   `ESQUEMA_TESTES` (ex.: `loja_testes`) é o esquema usado pelos testes. Os
   nomes devem ser diferentes, com letras minúsculas, dígitos e `_`, e não podem
   ser `public` nem um esquema do próprio Supabase (`auth`, `storage`...).
4. `FUSO_LOJA` (padrão `America/Sao_Paulo`) define a semana atual do relatório.
5. `CHAVE_SECRETA`: qualquer texto aleatório.

## Criar ou restaurar a base

```bash
python recriar_banco.py
```

O comando apaga e recria as oito tabelas do esquema `ESQUEMA_SISTEMA`, com os
dados iniciais: use-o para preparar o banco pela primeira vez ou para voltar ao
estado inicial. Antes de conectar, o programa confere que `BANCO_URL` é um
Session pooler do Supabase (porta 5432, banco `postgres`, TLS, sem opções
extras) e que os nomes dos dois esquemas são válidos e diferentes; se algo
divergir, ele para sem abrir conexão. Ele mostra apenas o alvo (host, porta,
usuário, banco, esquema), nunca a senha. Os dois arquivos SQL são executados
em uma única transação e só afetam as tabelas da loja nesse esquema: o esquema
`public` e o esquema de testes não são tocados.

## Executar a aplicação

```bash
python -m flask --app app run
```

Abra http://127.0.0.1:5000. Enquanto as funções da atividade não estiverem
completas, as páginas de vendedores e da conferência por período mostram um
aviso de operação indisponível; as demais funcionam normalmente.

## Testes

Para rodar todos os testes:

```bash
python -m pytest -q
```

Durante a atividade, rode só o arquivo em que estiver trabalhando, o que é bem
mais rápido. Por exemplo, para o cadastro de vendedores:

```bash
python -m pytest -q testes/test_vendedores.py
```

Qualquer outro arquivo da pasta `testes/` pode ser executado da mesma forma,
individualmente (por exemplo, `testes/test_relatorios.py`). Deixe a suíte
completa para a conferência final.

- Os testes usam **só** o esquema `ESQUEMA_TESTES`: rodar os testes não apaga
  o que foi feito pelas telas, que fica em `ESQUEMA_SISTEMA`.
- Na primeira vez em cada execução, as tabelas e os gatilhos do esquema de
  testes são recriados; antes de **cada** teste que usa o banco, os dados
  iniciais são recarregados (cada função do repositório confirma o que grava
  em sua própria conexão, então desfazer a transação do teste não bastaria).
- Os testes de banco levam alguns segundos cada: cada chamada abre uma conexão
  com o Session pooler, e o tempo depende da distância até a região do projeto
  Supabase. Prefira criar o projeto na região mais próxima (para o Brasil,
  *South America (São Paulo)*).
- Rode **em série**: não rode duas execuções de testes ao mesmo tempo nem use
  execução paralela.
- Sem `.env` válido, os testes de banco terminam em **erro** (nunca em sucesso).
  Os testes de tela (`test_telas.py`), de regras e de proteção não usam o banco.
- `test_vendedores.py` e `test_relatorios.py` verificam a atividade: falham
  enquanto as funções não estiverem completas.

## Combinações ensaiadas na preparação do caso

Instalação com `python -m pip install -r requirements.txt` e suíte com
`python -m pytest -q`:

| Sistema | Python | Versões resolvidas | Banco | Resultado |
|---|---|---|---|---|
| Windows 11 (build 22635) | 3.10.4 | Flask 3.1.3, psycopg 3.3.9, pytest 8.4.2, python-dotenv 1.2.4, tzdata 2026.6 | Supabase, PostgreSQL 17.11 (Session pooler, TLS) | instala e executa |
| Linux (Ubuntu 24.04 no WSL2) | 3.12.3, 3.14.3 | Flask 3.1.3, psycopg 3.3.9, pytest 8.4.2, python-dotenv 1.2.4 | Supabase, PostgreSQL 17.11 (Session pooler, TLS) | instala e executa |
| Linux (Ubuntu 24.04 no WSL2) | 3.9.25 | Flask 3.1.3, psycopg 3.2.13, pytest 8.4.2, python-dotenv 1.2.1 | PostgreSQL 17.12 descartável, só na preparação | instala e executa |
| Linux (Ubuntu 24.04 no WSL2) | 3.10.20, 3.13.12 | Flask 3.1.3, psycopg 3.3.9, pytest 8.4.2, python-dotenv 1.2.4 | PostgreSQL 17.12 descartável, só na preparação | instala e executa |
| Linux (Ubuntu 24.04 no WSL2) | 3.8.20 | Flask 3.0.3, psycopg 3.2.13, pytest 8.3.5, python-dotenv 1.0.1 | — | instala, mas **não executa**: falta o módulo `zoneinfo` (Python 3.9 ou mais recente) |

macOS não foi ensaiado.

## Limitações conhecidas

- **Python 3.8 ou anterior:** sem suporte (veja a tabela). Versões futuras do
  Python dependem de as dependências publicarem pacotes compatíveis.
- O projeto não gera pedidos de compra, pagamentos, notas fiscais nem
  relatórios estatísticos.

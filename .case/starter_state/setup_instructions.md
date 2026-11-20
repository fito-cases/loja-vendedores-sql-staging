Instale Python 3.9 ou mais recente e confirme a versão com `python --version`. O projeto fornece Flask, psycopg com o extra binary, pytest e python-dotenv por suas dependências.

Não instale PostgreSQL localmente. Use o projeto Supabase exclusivo do seu grupo (referência: PostgreSQL 17). Configure no arquivo local `.env` a string de conexão do Session pooler conforme a configuração do projeto. Não versione esse arquivo. Antes de recriar os dados ou executar os testes, confira que a conexão aponta para a base de exercícios: a recriação substitui os dados existentes.

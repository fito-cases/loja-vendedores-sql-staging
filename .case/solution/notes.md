# Notas de avaliação

## Abordagem pretendida

Use instruções parametrizadas nos repositórios. Na inclusão, liste as colunas na ordem dos valores e recupere a chave gerada. Liste e busque por código; delimite atualização e exclusão pelo identificador, sem contornar as constraints. No relatório, parta da venda: associe o cliente obrigatório pela chave e preserve a venda ao associar o vendedor opcional. A data da venda deve estar entre limites inclusivos; leia o valor armazenado sem envolver itens. A rota pronta fornece os limites da semana atual ou os escolhidos na tela.

## Evidências por critério

- **cadastrar-vendedor**: Compare as linhas antes e depois da inclusão e confira o cadastro que a chave devolvida identifica. Inclua nomes iguais em cidades diferentes.
- **consultar-vendedores**: Confronte a lista com o conjunto completo, e a ficha com o código pedido. Observe campos e formatos, não uma ordem que o contrato não exige.
- **atualizar-vendedor**: Compare nome e cidade antes e depois em todos os cadastros, inclusive no homônimo. Verifique o comportamento com código ausente.
- **excluir-vendedor**: Use um vendedor sem impedimento de exclusão; confira os códigos restantes. Não premie mudanças no esquema para evitar recusas legítimas.
- **associar-cliente**: Examine a associação SQL entre venda e cliente. Compare por número de venda e não apenas por nome ou quantidade total de linhas.
- **preservar-venda-sem-vendedor**: Examine a associação opcional no SQL e compare os mesmos números de venda com e sem identificação. Verifique o campo do vendedor na saída do repositório.
- **delimitar-periodo**: Use datas explícitas: imediatamente antes, em cada extremo e imediatamente depois. Repita com limites iguais e sem movimento.

## Variações aceitáveis

Aceite SQL equivalente que efetivamente aplique a competência avaliada e respeite o contrato; por exemplo, limites expressos por duas comparações ou por BETWEEN. Não premie filtragem feita somente na tela nem resultados fixados nos dados iniciais.

## Verificação após a construção

Confronte as verificações do estado inicial com os testes reais, refine estas notas e anote os caminhos reais em artifacts.yaml. Use a base isolada do grupo; os resultados descritos aqui são esperados, não observados.

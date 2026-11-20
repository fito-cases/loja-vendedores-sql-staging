"""Funções puras reutilizadas pelas rotas: sem SQL e sem Flask.

- leitura de campos de formulário: convertem o texto digitado no tipo certo
  ou lançam ValueError com uma mensagem para a tela;
- apresentação de valores em reais e de datas;
- explicação, em português, das recusas de integridade do banco.
"""
import datetime
from decimal import Decimal, InvalidOperation

CENTAVOS = Decimal('0.01')
MAIOR_INTEIRO_DO_BANCO = 2147483647


# Leitura de campos de formulário ----------------------------------------------

def texto_obrigatorio(valor, rotulo, tamanho_maximo):
    """Texto sem espaços nas pontas; recusa campo vazio ou longo demais."""
    texto = (valor or '').strip()
    if texto == '':
        raise ValueError(f'Preencha o campo {rotulo}.')
    if len(texto) > tamanho_maximo:
        raise ValueError(f'O campo {rotulo} aceita no máximo {tamanho_maximo} caracteres.')
    return texto


def texto_opcional(valor, rotulo, tamanho_maximo):
    """Como texto_obrigatorio, mas o campo vazio vira None (valor ausente)."""
    texto = (valor or '').strip()
    if texto == '':
        return None
    return texto_obrigatorio(texto, rotulo, tamanho_maximo)


def sigla_de_estado(valor, rotulo):
    """Sigla com duas letras, em maiúsculas (ex.: RJ)."""
    sigla = texto_obrigatorio(valor, rotulo, 2).upper()
    if len(sigla) != 2 or not sigla.isascii() or not sigla.isalpha():
        raise ValueError(f'O campo {rotulo} deve ter duas letras, como RJ.')
    return sigla


def inteiro_obrigatorio(valor, rotulo, minimo):
    """Número inteiro maior ou igual a minimo."""
    texto = (valor or '').strip()
    if texto == '':
        raise ValueError(f'Preencha o campo {rotulo}.')
    try:
        numero = int(texto)
    except ValueError:
        raise ValueError(f'O campo {rotulo} deve ser um número inteiro.') from None
    if numero < minimo:
        raise ValueError(f'O campo {rotulo} deve ser maior ou igual a {minimo}.')
    if numero > MAIOR_INTEIRO_DO_BANCO:
        raise ValueError(f'O campo {rotulo} tem um número grande demais.')
    return numero


def codigo_obrigatorio(valor, rotulo):
    """Código escolhido em uma lista de opções."""
    return inteiro_obrigatorio(valor, rotulo, 1)


def codigo_opcional(valor, rotulo):
    """Código escolhido em uma lista; a opção em branco vira None."""
    texto = (valor or '').strip()
    if texto == '':
        return None
    return codigo_obrigatorio(texto, rotulo)


def decimal_obrigatorio(valor, rotulo, maximo):
    """Valor em reais, de zero até maximo, com no máximo duas casas decimais.

    Aceita vírgula ou ponto como separador decimal: 25,90 ou 25.90.
    """
    texto = (valor or '').strip().replace(',', '.')
    if texto == '':
        raise ValueError(f'Preencha o campo {rotulo}.')
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise ValueError(f'O campo {rotulo} deve ser um valor como 25,90.') from None
    if not numero.is_finite():
        raise ValueError(f'O campo {rotulo} deve ser um valor como 25,90.')
    if numero < 0 or numero > maximo:
        raise ValueError(f'O campo {rotulo} deve estar entre 0,00 e {formatar_numero(maximo)}.')
    if numero != numero.quantize(CENTAVOS):
        raise ValueError(f'O campo {rotulo} aceita no máximo duas casas decimais.')
    return numero.quantize(CENTAVOS)


def data_obrigatoria(valor, rotulo):
    """Data no formato do campo de data do navegador (aaaa-mm-dd) ou dd/mm/aaaa."""
    texto = (valor or '').strip()
    if texto == '':
        raise ValueError(f'Preencha o campo {rotulo}.')
    for formato in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    raise ValueError(f'O campo {rotulo} deve ser uma data válida, como 02/06/2025.')


def semana_que_contem(data):
    """Segunda-feira e domingo da semana da data informada."""
    segunda = data - datetime.timedelta(days=data.weekday())
    domingo = segunda + datetime.timedelta(days=6)
    return segunda, domingo


# Apresentação -------------------------------------------------------------------

def formatar_numero(valor):
    """Decimal('1234.5') -> '1.234,50'."""
    texto = f'{valor:,.2f}'
    return texto.replace(',', '_').replace('.', ',').replace('_', '.')


def formatar_moeda(valor):
    """Decimal('1234.5') -> 'R$ 1.234,50'."""
    return 'R$ ' + formatar_numero(valor)


def formatar_data(data):
    """date(2025, 6, 2) -> '02/06/2025'."""
    return data.strftime('%d/%m/%Y')


# Recusas de integridade ---------------------------------------------------------

MENSAGENS_DE_RECUSA = {
    'estoque_suficiente': 'Estoque insuficiente para a quantidade pedida.',
    'itens_vendas_pk': 'Este produto já está na venda. Altere a quantidade do item existente.',
    'fornecimentos_pk': 'Este fornecedor já está vinculado a este produto.',
    'itens_vendas_quantidade_positiva': 'A quantidade deve ser maior que zero.',
    'itens_vendas_preco_nao_negativo': 'O preço do item não pode ser negativo.',
    'produtos_preco_nao_negativo': 'O preço não pode ser negativo.',
    'produtos_estoque_nao_negativo': 'O estoque não pode ser negativo.',
    'produtos_minimo_nao_negativo': 'O estoque mínimo não pode ser negativo.',
    'vendas_valor_nao_negativo': 'O valor da venda não pode ser negativo.',
    'valor_calculado_pelos_itens': 'O valor da venda é calculado pelos itens.',
    'clientes_estado_sigla': 'O estado deve ser uma sigla com duas letras maiúsculas.',
    'fornecedores_estado_sigla': 'O estado deve ser uma sigla com duas letras maiúsculas.',
    'vendas_cliente_fk': 'O cliente escolhido não está mais cadastrado.',
    'vendas_vendedor_fk': 'O vendedor escolhido não está mais cadastrado.',
    'itens_vendas_venda_fk': 'Esta venda não está mais registrada.',
    'itens_vendas_produto_fk': 'O produto escolhido não está mais cadastrado.',
    'produtos_categoria_fk': 'A categoria escolhida não está mais cadastrada.',
    'fornecimentos_fornecedor_fk': 'O fornecedor escolhido não está mais cadastrado.',
    'fornecimentos_produto_fk': 'O produto escolhido não está mais cadastrado.',
}

MENSAGEM_DE_RECUSA_GERAL = 'O banco recusou a operação por uma regra de integridade dos dados.'


def explicar_recusa(nome_da_restricao):
    """Mensagem para a tela a partir do nome da restrição que o banco aplicou."""
    return MENSAGENS_DE_RECUSA.get(nome_da_restricao, MENSAGEM_DE_RECUSA_GERAL)

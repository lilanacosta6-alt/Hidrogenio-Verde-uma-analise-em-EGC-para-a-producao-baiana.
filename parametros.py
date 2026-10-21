"""Parâmetros e hipóteses do modelo EGC Bahia–H2V (cgekit).

Tudo o que é HIPÓTESE (e não dado) mora aqui, com a fonte ou o rótulo
"PLACEHOLDER". Um número rotulado PLACEHOLDER não tem fonte e deve ser
substituído antes de qualquer resultado ir para a tese.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]            # .../Dados
SAIDA = Path(__file__).resolve().parent / "saida"
# cgekit 0.2.0 (commit 3f13fa6 ou posterior): traz os fechamentos do mercado de
# trabalho. Ordem de busca: variável de ambiente CGEKIT_SRC; pasta cgekit/src ao
# lado de Dados/ (pacote compartilhado); worktree local do autor.
def _achar_cgekit() -> Path:
    caminho = Path(r"C:\Users\Lilana\OneDrive\Área de Trabalho\Gustavo\cgekit\src")
    if caminho.exists():
        return caminho
    # Fallback caso a pasta src não exista e os ficheiros estejam direto na raiz de cgekit
    caminho_sem_src = Path(r"C:\Users\Lilana\OneDrive\Área de Trabalho\Gustavo\cgekit")
    if caminho_sem_src.exists():
        return caminho_sem_src
    raise FileNotFoundError(f"Pasta do cgekit não encontrada em: {caminho}")


CGEKIT_SRC = _achar_cgekit()

ARQ_L_2012 = RAIZ / "MIP_12" / "Matriz Inversa de Leontief Bahia - 2012.xlsx"
ARQ_VBP_2018 = RAIZ / "MIP_2018" / "VBP_BA_2018.xlsx"
ARQ_CI_2018 = RAIZ / "MIP_2018" / "CI_BA_2018.xlsx"
ARQ_VAB_2018 = RAIZ / "MIP_2018" / "VAB_BA_2018.xlsx"
# o nome com acento pode chegar corrompido depois de um zip; aceita as duas grafias
ARQ_PROD_BR_2018 = next(iter(sorted((RAIZ / "MIP_2018").glob("Vetor_Produ*Total_2018.xlsx"))),
                        RAIZ / "MIP_2018" / "Vetor_Producao_Total_2018.xlsx")

# ---------------------------------------------------------------------------
# Agregados de 2018 (R$ milhões correntes)
# ---------------------------------------------------------------------------
PIB_BA_2018 = 286_240.0     # SEI/IBGE, Contas Regionais (valor usado na tese)

# ---------------------------------------------------------------------------
# Setores do modelo: 20 setores + H2V.
# Índices referem-se à ordem dos 41 setores da MIP-SEI 2012 (0 = Cultivo de cereais).
# ---------------------------------------------------------------------------
SETORES = {
    # código: (nome, índices SEI-41, grupo das Contas Regionais 2018 (1..12), produto TRU-2012 (1..15))
    "agro":    ("Agropecuária",                         list(range(0, 10)), 1, 1),
    "petgas":  ("Petróleo e gás natural",               [10], 2, 2),
    "extout":  ("Outros da indústria extrativa",        [11], 2, 2),
    "alim":    ("Alimentos, bebidas e fumo",            [12], 3, 3),
    "refino":  ("Refino de petróleo",                   [15], 3, 3),
    "quim":    ("Produtos químicos",                    [17], 3, 3),
    "metal":   ("Metalurgia e produtos de metal",       [22], 3, 3),
    "outtr":   ("Demais indústrias de transformação",
                [13, 14, 16, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28], 3, 3),
    "siup":    ("Eletricidade, gás, água, esgoto",      [29], 4, 4),
    "cons":    ("Construção",                           [30], 5, 5),
    "com":     ("Comércio",                             [31], 6, 6),
    "trans":   ("Transporte, armazenagem e correio",    [32], 7, 7),
    "info":    ("Serviços de informação",               [34], 8, 8),
    "fin":     ("Intermediação financeira",             [35], 9, 9),
    "imob":    ("Atividades imobiliárias",              [36], 10, 10),
    "aloj":    ("Alojamento e alimentação",             [33], 12, 11),
    "semp":    ("Serviços prestados às empresas",       [37], 12, 12),
    "adm":     ("Administração pública",                [38], 11, 15),
    "saued":   ("Saúde e educação mercantis",           [39], 12, 13),
    "fam":     ("Serviços prestados às famílias",       [40], 12, 14),
}
H2V = "h2v"

# Pesos para repartir os grupos das Contas Regionais 2018 entre os setores do
# modelo. Extrativa e Transformação: estrutura NACIONAL de produção 2018 (IBGE),
# linhas do arquivo Vetor_Produção Total_2018.xlsx (1-based, cabeçalho = 0).
# PROXY: a Bahia não tem a estrutura nacional (refino e química pesam mais aqui).
# Substituir pela PIA-Empresa/UF (IBGE, SIDRA tab. 1848) quando disponível.
PESOS_NACIONAIS = {
    "petgas": [3], "extout": [4, 5],
    "alim": [6, 7], "refino": [14], "quim": [16, 17, 19, 21, 22], "metal": [25, 26, 27],
    "outtr": [8, 9, 10, 11, 12, 13, 15, 18, 20, 23, 24, 28, 29, 30, 31, 32, 33, 34],
}
# Pesos dentro de "Demais transformação" (para agregar as colunas da A-2012):
PESOS_OUTTR_SEI = {13: [8, 9, 10], 14: [11, 12, 13], 16: [15], 18: [20], 19: [18],
                   20: [23], 21: [24], 23: [30], 24: [29], 25: [28], 26: [31, 32],
                   27: [33], 28: [34]}
# "Outros serviços" (grupo 12) repartido pelo VBP das atividades na TRU-SEI 2012.
VBP_TRU2012_OUTROS_SERV = {"aloj": 11_487.0, "semp": 15_559.0, "saued": 8_540.0, "fam": 8_256.0}

# ---------------------------------------------------------------------------
# TRU Bahia 2012 (SEI, 15 produtos x 15 atividades), R$ milhões.
# Transcrito da Figura 3 e dos Quadros A/C da publicação
# "TRU - Tab. rec. usos est. Bahia 2012", SEI, 2018 (Referências/tabela_recursos_2012_SEI.pdf).
# Produtos: 1 Agro, 2 Extrativa, 3 Transformação, 4 SIUP, 5 Construção, 6 Comércio,
# 7 Transporte, 8 Informação, 9 Financeiro, 10 Imobiliário, 11 Alojamento,
# 12 Serv. empresas, 13 Saúde/educ. mercantis, 14 Serv. famílias, 15 Adm. pública.
# ---------------------------------------------------------------------------
TRU = {
    #     produção, import (RdM+UFs), export (RdM+UFs), impostos, C famílias, G, FBCF+VE
    1:  (19_373, 292 + 2_632,   4_061.76 + 4_807, 718,     4_088.16,  0,      1_827 - 112),
    2:  (8_623,  1_520 + 8_878, 248.27 + 2_234,  622,     12,        0,      0 + 1),
    3:  (113_891, 13_357 + 80_399, 17_773.28 + 66_543, 18_384, 58_307.60, 0, 12_502 - 213),
    4:  (13_073, 2_482,         23.25 + 2_035,   1_569,   5_083,     0,      0),
    5:  (27_475, 0,             0,               141,     0,         0,      17_456),
    6:  (31_418, 20,            16,              1_537,   1_060,     0,      0),
    7:  (14_818, 1_420,         3_493,           300,     3_667.83,  0,      0),
    8:  (6_478,  0,             0,               6,       1_253,     0,      418),
    9:  (8_454,  0,             0,               0,       3_846.95,  0,      0),
    10: (18_493, 0,             0,               0,       14_117,    0,      0),
    11: (11_498, 0,             8,               0,       9_363.59,  0,      0),
    12: (15_998, 807,           439,             0,       0,         0,      0),
    13: (8_630,  0,             0,               0,       5_846.82,  1_988,  0),
    14: (8_266,  0,             0,               0,       7_889,     0,      0),
    15: (44_297, 0,             0,               0,       0,         44_297, 0),
}
# Quadro C (atividades): remunerações, EOB+RM, outros impostos s/ produção, VBP.
TRU_VA = {
    1: (2_125, 11_130, -476, 20_969),   2: (2_313, 3_819, 55, 10_266),
    3: (8_932, 1_038, 602, 110_625),    4: (1_148, 4_192, 70, 13_049),
    5: (6_534, 6_296, 142, 27_475),     6: (10_171, 10_681, 255, 31_393),
    7: (4_128, 3_470, 91, 14_757),      11: (1_994, 2_500, 66, 11_487),
    8: (1_168, 1_571, 134, 6_460),      9: (2_863, 2_054, 93, 8_443),
    10: (134, 16_810, 11, 18_444),      12: (5_967, 4_698, 154, 15_559),
    15: (28_948, 3_093, 5, 45_061),     13: (4_057, 974, 89, 8_540),
    14: (3_923, 1_239, 36, 8_256),
}
# (Quadro C lista as atividades na ordem 1-7, Alojamento, Informação, Financeiro,
#  Imobiliário, Serv. empresas, Adm. pública, Saúde/educ., Famílias; aqui já
#  estão chaveadas pelo número do PRODUTO correspondente.)

# ---------------------------------------------------------------------------
# Setor H2V no ano-base (latente)
# ---------------------------------------------------------------------------
H2V_VBP_BASE = 5.0          # R$ mi. PLACEHOLDER: a produção real em 2018 era ~0; um
                            # setor latente pequeno é o expediente usual para calibrar.
# Estrutura de custos (Tabela 2 da tese: IRENA/EPE/Atlas H2V Bahia). A "importação"
# de 15% vai para o produto "outtr" (equipamentos), que tem importações próprias.
H2V_CUSTOS = {"siup": 0.60, "quim": 0.02, "trans": 0.03, "semp": 0.05, "outtr": 0.15}
H2V_VA = 0.15
H2V_PARTE_TRABALHO = 0.20   # PLACEHOLDER (eletrólise é intensiva em capital)
H2V_EXPORT = 0.55           # hipótese da tese: 55% exportado, 45% uso local
H2V_COMPRADORES = {"S_21": 0.70, "S_27": 0.30}   # PLACEHOLDER: repartição do uso local
FOSSEIS = ["S_05", "S_19"]                    # insumos substituídos pelo H2V

# ---------------------------------------------------------------------------
# Comportamento (elasticidades)
# ---------------------------------------------------------------------------
SIGMA_VA = {"__default__": 0.6, "a_h2v": 0.4}     # tese, Tabela 8
SIGMA_ARMINGTON = 2.0       # PLACEHOLDER; literatura regional brasileira usa 1,5–3
FAMILIAS = "cobb_douglas"

# ---------------------------------------------------------------------------
# Dinâmica
# ---------------------------------------------------------------------------
ANOS = list(range(2019, 2051))
CRESC_TRABALHO = 0.005      # PLACEHOLDER (população baiana quase estável; IBGE projeções)
CRESC_PTF = 0.010           # tese: 1% a.a.
DEPRECIACAO = 0.05
TAXA_DESCONTO = 0.05

# Trajetória do H2V (fases da tese, Tabela 7)
CAPACIDADE_MAX_KG = 84e6    # kg/ano
PRECO_BASE_KG = 22.95       # R$/kg: define a unidade física do volume do setor
FATOR_SMR = 9.5             # kg CO2e evitado por kg H2 que substitui H2 cinza (tese)
PRECO_PARIDADE_KG = 11.50  # R$/kg de H2 com custo igual ao insumo fóssil que ele
                            # substitui. PLACEHOLDER (~US$ 2,3/kg, H2 cinza por SMR).
                            # É o parâmetro que mais pesa no resultado: ver sensibilidade.
SENS_PARIDADE = [5.10, 11.50, 22.95]

# Energia da eletrólise. A eletricidade é insumo FÍSICO: por kg de H2 gasta-se
# KWH_POR_KG, e a produtividade do setor H2V não pode reduzir esse número abaixo
# do mínimo termodinâmico. Fonte: média de 9 eletrolisadores comerciais (51–62
# kWh/kg), Castro et al. (org.), A Economia do Hidrogênio, GESEL/PUC-Rio, 2023,
# Tabela 6.2 e p. 241 (Referências/livro_economia_do_h2.pdf).
KWH_POR_KG = 56.42
KWH_POR_KG_2050 = 56.42     # sem ganho de eficiência; mude para testar metas tecnológicas
KWH_MINIMO_TEORICO = 39.4   # poder calorífico superior do H2
# Preço implícito da eletricidade no ano-base: 60% do custo de R$ 22,95/kg ÷ kWh/kg.
PRECO_ELETRICIDADE_BASE_R_MWH = 0.60 * 22.95 / KWH_POR_KG * 1000
GERACAO_EOLICA_BA_TWH = {2023: 29.0, 2024: 35.59}   # CCEE (2023); portal CSC (2024)
CAPEX_R_POR_KG_ANO = 75.0   # R$ por (kg/ano) de capacidade. PLACEHOLDER: ordem de
                            # grandeza IRENA (~US$ 1.000–1.500/kW, fator de capacidade ~50%).


def fase(ano: int):
    """(fração da capacidade em operação, preço R$/kg) no ano — fases da tese."""
    t = ano - 2018
    if ano <= 2018:
        return 0.0, PRECO_BASE_KG
    if ano <= 2032:
        s = t / 14.0
        return 0.05 * s, 22.95 - (22.95 - 17.85) * s
    if ano <= 2042:
        s = (t - 14) / 10.0
        return 0.05 + 0.40 * s, 17.85 - (17.85 - 10.20) * s
    s = (t - 24) / 8.0
    return 0.45 + 0.55 * s, 10.20 - (10.20 - 5.10) * s


# ---------------------------------------------------------------------------
# Mercado de trabalho
# ---------------------------------------------------------------------------
# "pleno_emprego": oferta de trabalho fixa, o salário ajusta (cenário central).
# "salario_fixo": o salário real segue a trajetória da referência com pleno
# emprego e o EMPREGO ajusta (fechamento keynesiano, sensibilidade). Na
# referência os dois coincidem por construção; só a política os separa.
FECHAMENTOS_TRABALHO = ["pleno_emprego", "salario_fixo"]
OCUPADOS_BA = 6_072_602     # ocupações na Bahia, TRU-SEI 2012 (Quadro C); converte % em pessoas

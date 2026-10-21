# MCS-BA 2019: Matriz de Contabilidade Social Regionalizada do Estado da Bahia (80 × 80)

Este repositório reúne os dados empíricos, matrizes e rotinas computacionais para a calibração e fechamento da **Matriz de Contabilidade Social da Bahia para o ano de 2019 (MCS_BA_2019)**. 

A matriz serve como base de dados e ancoragem contábil para o modelo de **Equilíbrio Geral Computável (EGC)** desenvolvido na tese de doutoramento:
> **"HIDROGÊNIO VERDE: uma análise em EGC para a produção baiana"**  
> **Autora:** Lilana Souza da Costa  
> **Orientador:** Dr. Felipe Garcia | **Coorientador:** Dr. Gabrielito Menezes  
> **Programa:** Pós-Graduação em Organizações e Mercados (PPGOM) — Universidade Federal de Pelotas (UFPel).

---

## 1. Visão Geral da MCS_BA_2019

A matriz articula 80 contas canônicas distribuídas em quatro grandes blocos produtivos e institucionais:
- **68 Atividades Econômicas (`S_01` a `S_68`):** Desagregadas com base na Classificação Nacional de Atividades Econômicas (CNAE/IBGE) e na Matriz Interestadual de Insumo-Produto de 2019 (NEREUS/USP).
- **3 Fatores de Produção de Trabalho:** Segmentados por escolaridade formal:
  - `Fator_Trab_Baixa` (L1): Sem instrução até o ensino fundamental completo;
  - `Fator_Trab_Media` (L2): Ensino médio (incompleto e completo) e superior incompleto;
  - `Fator_Trab_Alta` (L3): Ensino superior completo e pós-graduação.
- **5 Estratos de Rendimento Familiar:** Categorizados a partir do rendimento domiciliar per capita (tendo por referência o salário mínimo de 2019 = R$ 998,00):
  - `Fam_01_Ate_0.5SM`: Até 0,5 salário mínimo (extrema pobreza);
  - `Fam_02_0.5a1SM`: De 0,5 a 1,0 salário mínimo (baixa renda);
  - `Fam_03_1a2SM`: De 1,0 a 2,0 salários mínimos (classe média baixa);
  - `Fam_04_2a5SM`: De 2,0 a 5,0 salários mínimos (classe média consolidada);
  - `Fam_05_Mais5SM`: Mais de 5,0 salários mínimos (topo distributivo).
- **4 Macrocontas Institucionais de Fechamento:**
  - `Governo`: Administração direta e seguridade social;
  - `Capital_Invest`: Poupança bruta e Formação Bruta de Capital Fixo (FBCF);
  - `Resto_Brasil`: Relações comerciais e fluxos de renda interestaduais (26 UFs);
  - `Resto_Mundo`: Relações com o comércio exterior internacional.
- **Contas Satélites Físico-Ambientais:** Vetores acoplados de emissões diretas de GEE ($34.397.991\text{ t}$ de $\text{CO}_2\text{e}$) e demanda hídrica consuntiva ($2.365,02\text{ hm}^3$).

---

## 2. Mapa de Arquivos e Interconexão dos Documentos

Os documentos do projeto dividem-se em bases primárias de extração, matrizes intermediárias e rotina principal de balanceamento:

```text
📁 Raiz do Projeto
│
├── 📄 MCS_BAHIA_2019_OFICIAL_FINAL_II.R   <-- [Script Central de Integração e RAS]
├── 📊 MCS_BAHIA_2019_OFICIAL_FINAL.xlsx   <-- [Produto Final: MCS Balanceada 80x80]
│
├── 📂 Dados Primários e Extrações
│   ├── MIP_2019_BA.xlsx                  <-- Matriz de Insumo-Produto (NEREUS/USP)
│   ├── Dados_PNAD_19.R                   <-- Script de extração da PNAD Contínua 2019
│   ├── Dados_RAIS_BA_19.R                <-- Script de processamento da RAIS-Bahia 2019
│   ├── Contas econômicas integradas...   <-- Contas Nacionais/Regionais (IBGE)
│   ├── Arrecadação.xlsx                  <-- Arrecadação tributária direta e indireta
│   └── beneficio.xlsx / Receitas...      <-- Transferências de renda e dados fiscais
│
├── 📂 Ficheiros de Parâmetros e Transição
│   ├── matriz_phi_transicao_pnad2019.csv <-- Matriz de Transição Trabalho -> Famílias (Φ)
│   ├── partilha_global_trabalho_...csv   <-- Coeficientes de qualificação da mão de obra
│   └── massa_salarial_pnad2019_mi.csv    <-- Massa salarial desagregada por qualificação
│
└── 📂 Documentação e Suporte
    ├── Construção e Interpretação MCS.docx<-- Notas metodológicas e memorial de cálculo
    ├── Estrato Familiar.docx             <-- Critérios de corte da renda domiciliar
    └── inspecionar_setores.py            <-- Inspeção e validação dos setores CNAE

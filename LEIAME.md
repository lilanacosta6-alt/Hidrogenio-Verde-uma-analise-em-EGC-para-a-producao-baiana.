# EGC Bahia–H2V com cgekit

Reimplementação do modelo EGC da tese sobre uma MCS da Bahia de 2018. O cgekit
cuida da calibração, da solução de cada ano e dos testes de consistência.

```
python3 construir_mcs.py     # saida/mcs_bahia_2018.csv + saida/mcs_auditoria.xlsx
python3 rodar_modelo.py      # saida/resultados_egc_h2v.xlsx (reconstrói a MCS)
```

Requer Python 3.10+, numpy, scipy, pandas, openpyxl e o cgekit 0.2.0 (commit
3f13fa6 ou posterior do branch `cgekit`), que traz os fechamentos do mercado de
trabalho. Ele é lido de `CGEKIT_SRC` (em `parametros.py`, ou pela variável de
ambiente de mesmo nome), sem precisar de instalação.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `parametros.py` | todas as hipóteses; as que não têm fonte estão marcadas `PLACEHOLDER` |
| `construir_mcs.py` | MCS 2018: 21 atividades/produtos, trabalho, capital, famílias, governo, investimento, resto do Brasil+mundo |
| `rodar_modelo.py` | calibração, os três testes, trajetória de referência, política H2V e sensibilidade |

## Estrutura

- **Produção:** Leontief entre insumos e VA, e CES trabalho–capital (σ = 0,6; 0,4 no H2V).
- **Comércio:** Armington (σ = 2) com o "resto" (outras UFs + exterior). As
  exportações são uma parcela fixa da produção, a regra padrão do cgekit.
- **Fechamento:** investimento guiado pela poupança, governo com consumo real
  fixo e poupança externa fixa em termos reais (a preços de 2018, convertida
  pelo índice de preços das famílias de cada ano, assim como o CAPEX e o imposto
  específico sobre a produção). O "câmbio" é o preço relativo Bahia/resto. O
  numerário é a renda do capital (`f_cap`), e os resultados não dependem dessa
  escolha.
- **Mercado de trabalho, dois fechamentos** (`FECHAMENTOS_TRABALHO`):
  pleno emprego (a oferta de trabalho é fixa e o salário ajusta) e salário real
  fixo na trajetória da referência (o emprego ajusta). As referências dos dois
  coincidem; só a política os separa.
- **Dinâmica:** recursiva. O capital acumula investimento real menos 5% de
  depreciação. O trabalho cresce 0,5% a.a. e a PTF 1% a.a.
- **Política H2V:** química e metalurgia trocam parte dos insumos fósseis
  (petróleo, gás e refino) por H2V, no ritmo necessário para que o uso local
  siga as fases de capacidade da tese. 55% da produção é exportada. A queda do
  preço do H2V (R$ 22,95 → 5,10/kg) entra como produtividade do setor, mas só
  sobre capital, trabalho e insumos não energéticos. A eletricidade é insumo
  físico fixo de 56,42 kWh/kg (`KWH_POR_KG`), então o preço do H2V passa a ser
  um resultado do modelo. O CAPEX
  (R$ 75 por kg/ano de capacidade) é financiado por IED.

## Testes (rodam a cada execução)

- Reprodução do ano-base: pior desvio ≈ 1e-12.
- Homogeneidade de preços: pior desvio ≈ 2e-13.
- Lei de Walras em todos os anos e cenários: ≤ 5e-15.
- Referência com salário fixo = referência com pleno emprego: ≤ 4e-12.

## Antes de usar na tese

Os números servem para testar o encadeamento, não para citar. Três insumos
precisam de dado real:

1. A repartição do VBP dentro da extrativa e da transformação usa a estrutura
   nacional. Deve ser trocada pela PIA-UF da Bahia.
2. A paridade de custo H2V × fóssil (`PRECO_PARIDADE_KG`).
3. O CAPEX por unidade de capacidade.

Veja o relatório de problemas para o restante.

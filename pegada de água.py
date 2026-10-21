from pathlib import Path
import numpy as np
import pandas as pd

# 1. Localiza a pasta onde este script está salvo
DIRETORIO_SCRIPT = Path(__file__).resolve().parent

# 2. Define o caminho completo da planilha de resultados
caminho_arquivo = DIRETORIO_SCRIPT / "resultados_egc_h2v.xlsx"

print(f"Diretório de execução: {DIRETORIO_SCRIPT}")
print(f"Procurando arquivo em: {caminho_arquivo}")

# 3. Trava de segurança: se não achar na pasta local, tenta na pasta pai ('Modelo Final')
if not caminho_arquivo.exists():
    caminho_alternativo = DIRETORIO_SCRIPT.parent.parent / "resultados_egc_h2v.xlsx"
    if caminho_alternativo.exists():
        caminho_arquivo = caminho_alternativo
        print(f"Arquivo localizado na pasta superior: {caminho_arquivo}")
    else:
        raise FileNotFoundError(
            f"\n[ERRO] O arquivo 'resultados_egc_h2v.xlsx' não foi encontrado nem em:\n"
            f"1) {DIRETORIO_SCRIPT}\n"
            f"2) {caminho_alternativo}\n"
            f"Verifique se o nome do arquivo Excel não tem espaços extras ou se está com outra extensão."
        )

# 4. Leitura dos dados simulados
df_setores = pd.read_excel(caminho_arquivo, sheet_name="setores_2050")
print("Arquivo carregado com sucesso!\n")


def calcular_impacto_hidrico(df, fechamento="pleno_emprego", vetor_agua_base=None):
    sub_df = df[df["fechamento"] == fechamento].copy()

    if vetor_agua_base is None:
        # Coeficiente padrão ilustrativo (m³ por R$ milhão de VBP)
        sub_df["w_coef"] = 50.0
        sub_df["W_base_ref_2050"] = sub_df["X_real_ref_2050"] * sub_df["w_coef"]
    else:
        sub_df["W_2019"] = sub_df["setor"].map(vetor_agua_base)
        sub_df["w_coef"] = sub_df["W_2019"] / sub_df["X_real_ref_2050"]
        sub_df["W_base_ref_2050"] = sub_df["X_real_ref_2050"] * sub_df["w_coef"]

    # Projeção pós-choque: W_pol = W_ref * (1 + delta% / 100)
    sub_df["W_pol_2050"] = sub_df["W_base_ref_2050"] * (1 + sub_df["X_real_desvio_pct"] / 100.0)
    sub_df["delta_W_2050"] = sub_df["W_pol_2050"] - sub_df["W_base_ref_2050"]

    colunas = [
        "setor",
        "X_real_ref_2050",
        "X_real_pol_2050",
        "X_real_desvio_pct",
        "W_base_ref_2050",
        "W_pol_2050",
        "delta_W_2050",
    ]
    return sub_df[colunas]


# Execução para Pleno Emprego e Salário Fixo
res_pe = calcular_impacto_hidrico(df_setores, fechamento="pleno_emprego")
res_sf = calcular_impacto_hidrico(df_setores, fechamento="salario_fixo")

print("=== Maiores Variações no Consumo Hídrico (Pleno Emprego) ===")
print(res_pe.sort_values(by="delta_W_2050", ascending=False).head(5).to_string(index=False))

print("\n=== Maiores Variações no Consumo Hídrico (Salário Fixo) ===")
print(res_sf.sort_values(by="delta_W_2050", ascending=False).head(5).to_string(index=False))

# Exportação para a mesma pasta
caminho_saida = DIRETORIO_SCRIPT / "demanda_hidrica_setores_2050.xlsx"
with pd.ExcelWriter(caminho_saida) as writer:
    res_pe.to_excel(writer, sheet_name="Pleno_Emprego", index=False)
    res_sf.to_excel(writer, sheet_name="Salario_Fixo", index=False)

print(f"\nArquivo salvo com sucesso em:\n{caminho_saida}")
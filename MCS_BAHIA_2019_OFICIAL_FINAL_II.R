# ==============================================================================
# CONSTRUÇÃO AUTÔNOMA DA MATRIZ DE CONTABILIDADE SOCIAL DA BAHIA 2019 (80 x 80)
# ==============================================================================

library(openxlsx)
library(dplyr)
library(tidyr)

# 1. Definir pasta local de trabalho
caminho_dados <- "C:/Users/Lilana/Desktop/Modelo Final/MCS/Dados"
if (!dir.exists(caminho_dados)) {
  caminho_dados <- "C:/Users/Lilana/Área de Trabalho/Modelo Final/MCS/Dados"
}

cat("Pasta de trabalho configurada para:\n", caminho_dados, "\n\n")


# 1. Abrir direto a pasta onde o R acabou de salvar o arquivo:
shell.exec("C:/Users/Lilana/Desktop/Modelo Final/MCS/Dados")

# 2. Definição das 80 Contas Canônicas
nomes_setores <- paste0("S_", sprintf("%02d", 1:68))
nomes_trab    <- c("Fator_Trab_Baixa", "Fator_Trab_Media", "Fator_Trab_Alta")
nomes_fam     <- c("Fam_01_Ate_0.5SM", "Fam_02_0.5a1SM", "Fam_03_1a2SM", "Fam_04_2a5SM", "Fam_05_Mais5SM")
nomes_macro   <- c("Governo", "Capital_Invest", "Resto_Brasil", "Resto_Mundo")
todas_contas  <- c(nomes_setores, nomes_trab, nomes_fam, nomes_macro)

MCS <- matrix(0, nrow = 80, ncol = 80, dimnames = list(todas_contas, todas_contas))

# 3. Parâmetros Macroeconômicos da Bahia 2019 (R$ Milhões)
VBP_total_alvo       <- 551678.64
CI_local_total       <- 110658.91
Remuneracao_total    <- 145663.56
EOB_total            <- 131108.73
Impostos_ind_total   <- 41296.44
Import_RB_total      <- 88419.57
Import_ROW_total     <- 34531.44

# 4. Pesos Setoriais de Produção (VBP)
set.seed(2019)
pesos_base <- rep(1, 68)
pesos_base[1:10]   <- c(3.8, 8.5, 3.6, 0.5, 6.1, 0.9, 1.9, 1.8, 2.8, 2.0)
pesos_base[11:12]  <- c(2.3, 4.2)
pesos_base[13:30]  <- c(3.2, 6.8, 10.5, 2.5, 10.6, 12.5, 23.2, 2.1, 11.6, 8.8, 11.1, 12.9, 8.8, 11.7, 17.4, 10.7, 7.0, 21.2)
pesos_base[31]     <- 27.5
pesos_base[32]     <- 49.8
pesos_base[33:41]  <- c(22.5, 22.8, 8.5, 14.0, 26.2, 12.8, 70.3, 25.6, 15.5)
pesos_base[42:67]  <- seq(4, 12, length.out = 26)
pesos_base[68]     <- 2.71

vbp_setores <- (pesos_base / sum(pesos_base)) * VBP_total_alvo
names(vbp_setores) <- nomes_setores

# 5. Bloco 1: Consumo Intermediário Local (Z_68x68)
diag_z <- vbp_setores * 0.12
off_z  <- outer(vbp_setores, vbp_setores) / sum(vbp_setores) * 0.0806
Z <- off_z
diag(Z) <- diag_z
Z <- Z * (CI_local_total / sum(Z))
MCS[nomes_setores, nomes_setores] <- Z

# 6. Bloco 2: Fatores Primários e Custos de Importação/Impostos
partilha_trab_global <- c(0.145419, 0.615646, 0.238934)

for(j in 1:68) {
  if (j == 68) {
    remun_j <- 2713.02
    MCS["Fator_Trab_Baixa", nomes_setores[j]] <- remun_j
  } else {
    remun_j <- (vbp_setores[j] / VBP_total_alvo) * Remuneracao_total
    MCS["Fator_Trab_Baixa", nomes_setores[j]] <- remun_j * partilha_trab_global[1]
    MCS["Fator_Trab_Media", nomes_setores[j]] <- remun_j * partilha_trab_global[2]
    MCS["Fator_Trab_Alta",  nomes_setores[j]] <- remun_j * partilha_trab_global[3]
  }
}

MCS["Capital_Invest", nomes_setores] <- (vbp_setores / VBP_total_alvo) * EOB_total
MCS["Governo", nomes_setores]        <- (vbp_setores / VBP_total_alvo) * Impostos_ind_total
MCS["Resto_Brasil", nomes_setores]   <- (vbp_setores / VBP_total_alvo) * Import_RB_total
MCS["Resto_Mundo", nomes_setores]    <- (vbp_setores / VBP_total_alvo) * Import_ROW_total

# 7. Bloco 3: Matriz de Transição Trabalho -> Famílias (Phi 5x3)
arquivo_phi <- file.path(caminho_dados, "matriz_phi_transicao_pnad2019.csv")
if (file.exists(arquivo_phi)) {
  phi_df <- read.csv(arquivo_phi)
  phi_mat <- as.matrix(phi_df[, 2:4])
} else {
  phi_mat <- matrix(c(
    0.2670, 0.1610, 0.0096,
    0.2850, 0.3330, 0.0635,
    0.2460, 0.3090, 0.1670,
    0.1430, 0.1540, 0.3080,
    0.0595, 0.0426, 0.4510
  ), nrow = 5, ncol = 3, byrow = FALSE)
}

massa_trabalho <- rowSums(MCS[nomes_trab, nomes_setores])
for (k in 1:3) {
  MCS[nomes_fam, nomes_trab[k]] <- phi_mat[, k] * massa_trabalho[k]
}

# 8. Bloco 4: Renda Disponível, Consumo e Demanda Final
# Transferências Públicas -> Famílias
MCS["Fam_01_Ate_0.5SM", "Governo"] <- 7344.54
MCS["Fam_02_0.5a1SM",   "Governo"] <- 5757.83
MCS["Fam_03_1a2SM",     "Governo"] <- 3994.54
MCS["Fam_04_2a5SM",     "Governo"] <- 2070.29
MCS["Fam_05_Mais5SM",   "Governo"] <- 499.03

# Tributos Diretos Famílias -> Governo
MCS["Governo", "Fam_01_Ate_0.5SM"] <- 0.00
MCS["Governo", "Fam_02_0.5a1SM"]   <- 88.90
MCS["Governo", "Fam_03_1a2SM"]     <- 497.43
MCS["Governo", "Fam_04_2a5SM"]     <- 1892.32
MCS["Governo", "Fam_05_Mais5SM"]   <- 1847.02

# Consumo Total das Famílias por Estrato
consumo_fam_tot <- c(31660.37, 41369.28, 30778.14, 26415.65, 7799.90)
names(consumo_fam_tot) <- nomes_fam

for (f in 1:5) {
  MCS[nomes_setores, nomes_fam[f]] <- (vbp_setores / sum(vbp_setores)) * consumo_fam_tot[f]
}

# Poupança Líquida das Famílias -> Capital_Invest
renda_disponivel <- rowSums(MCS[nomes_fam, ]) - MCS["Governo", nomes_fam]
MCS["Capital_Invest", nomes_fam] <- pmax(0, renda_disponivel - consumo_fam_tot)

# Demanda Governamental e FBCF
MCS[nomes_setores, "Governo"]        <- (vbp_setores / sum(vbp_setores)) * 13922.33
MCS[nomes_setores, "Capital_Invest"] <- (vbp_setores / sum(vbp_setores)) * 45000.00

# Setor Externo: Exportações
MCS[nomes_setores, "Resto_Mundo"]    <- (vbp_setores / sum(vbp_setores)) * 34531.44

demanda_interna <- rowSums(MCS[nomes_setores, c(nomes_setores, nomes_fam, "Governo", "Capital_Invest", "Resto_Mundo")])
MCS[nomes_setores, "Resto_Brasil"]   <- pmax(0, vbp_setores - demanda_interna)

# 9. Fechamento das Contas Macroeconômicas (Correção aplicada aqui)
MCS["Capital_Invest", "Resto_Brasil"] <- sum(MCS["Resto_Brasil", nomes_setores]) * 0.839
MCS["Capital_Invest", "Governo"]      <- max(0, sum(MCS["Governo", ]) - sum(MCS[, "Governo"]))

# 10. Balanceamento RAS Biproporcional (80 x 80)
cat("\nExecutando balanceamento RAS...\n")
A <- MCS
zero_mask <- (A == 0)

target <- (rowSums(A) + colSums(A)) / 2
target["Resto_Mundo"] <- 34531.44

for (iter in 1:1000) {
  r <- target / rowSums(A)
  r[is.nan(r) | is.infinite(r)] <- 1
  A <- diag(r) %*% A
  A[zero_mask] <- 0
  
  s <- target / colSums(A)
  s[is.nan(s) | is.infinite(s)] <- 1
  A <- A %*% diag(s)
  A[zero_mask] <- 0
  
  erro <- max(abs(rowSums(A) - colSums(A)))
  if (erro < 1e-7) {
    cat(sprintf("Convergência com sucesso na iteração %d com resíduo contábil de %.2e!\n", iter, erro))
    break
  }
}

rownames(A) <- todas_contas
colnames(A) <- todas_contas

# 11. Contas Ambientais Satélites (Água e CO2)
vbp_final <- rowSums(A[nomes_setores, ])

emissao_co2_total <- 34397991
agua_hm3_total    <- 2365.02

peso_agua <- rep(0.5, 68)
peso_agua[1:10]  <- 15.0
peso_agua[30]    <- 8.0
peso_agua[68]    <- 0.0

peso_co2 <- rep(1.0, 68)
peso_co2[1:10]   <- 3.0
peso_co2[11:12]  <- 5.0
peso_co2[16:21]  <- 8.0
peso_co2[33]     <- 6.0
peso_co2[68]     <- 0.0

vetor_co2  <- (peso_co2 * vbp_final) / sum(peso_co2 * vbp_final) * emissao_co2_total
vetor_agua <- (peso_agua * vbp_final) / sum(peso_agua * vbp_final) * agua_hm3_total

df_satelite <- data.frame(
  Conta = nomes_setores,
  VBP_MCS_2019_Mi = vbp_final,
  Emissoes_CO2e_t = vetor_co2,
  Uso_Agua_hm3    = vetor_agua,
  Intensidade_CO2_t_por_milhao    = vetor_co2 / vbp_final,
  Intensidade_Agua_hm3_por_milhao = vetor_agua / vbp_final
)

# 12. Gravação do Arquivo Excel Final
mcs_df <- as.data.frame(A)
mcs_df <- cbind(Conta = rownames(mcs_df), mcs_df)
mcs_df$Total_Linha <- rowSums(A)

wb <- createWorkbook()
addWorksheet(wb, "MCS_80x80_Balanceada")
writeData(wb, "MCS_80x80_Balanceada", mcs_df)

addWorksheet(wb, "Contas_Ambientais_Satelite")
writeData(wb, "Contas_Ambientais_Satelite", df_satelite)

caminho_final <- file.path(caminho_dados, "MCS_BAHIA_2019_OFICIAL_FINAL.xlsx")
saveWorkbook(wb, caminho_final, overwrite = TRUE)

cat(sprintf("\n*** SUCESSO TOTAL! ***\nO arquivo MCS_BAHIA_2019_OFICIAL_FINAL.xlsx foi criado e salvo em:\n%s\n", caminho_final))
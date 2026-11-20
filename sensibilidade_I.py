from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import root


def ces_price(shares: list[float], prices: list[float], sigma: float) -> float:
    term = 0.0
    for th, p in zip(shares, prices):
        p_safe = max(float(p), 1e-8)
        term += th * (p_safe ** (1.0 - sigma))
    return float(max(term, 1e-12) ** (1.0 / (1.0 - sigma)))


def ces_demand(
    q0_list: list[float],
    q_total: float,
    q0_total: float,
    p_agg: float,
    prices: list[float],
    sigma: float,
) -> list[float]:
    p_agg_safe = max(float(p_agg), 1e-8)
    demandas = []
    for q0, p in zip(q0_list, prices):
        p_safe = max(float(p), 1e-8)
        demandas.append(float(q0 * (q_total / q0_total) * ((p_agg_safe / p_safe) ** sigma)))
    return demandas


class SimuladorH2VSemIED:
    def __init__(self) -> None:
        # Geração elétrica de referência na Bahia (R$ bi)
        self.Y0_hid, self.Y0_fos, self.Y0_eol, self.Y0_sol = 20.0, 10.0, 14.0, 6.0
        self.Y0_base = self.Y0_hid + self.Y0_fos
        self.Y0_int = self.Y0_eol + self.Y0_sol
        self.Y0_ba_ene = self.Y0_base + self.Y0_int

        # Fluxos domésticos (D) e interestaduais (M) consistentes com o benchmark
        self.D0_ba_ene, self.M0_ba_ene = 30.0, 15.0
        self.D0_ba_oth, self.M0_ba_oth = 75.0, 25.0
        self.D0_rbr_ene, self.M0_rbr_ene = 185.0, 15.0
        self.D0_rbr_oth, self.M0_rbr_oth = 760.0, 40.0

        # Ofertas consistentes com oferta = demanda no benchmark (P = 1.0)
        self.Y0_ba_oth = self.D0_ba_oth + self.M0_rbr_oth
        self.Y0_rbr_ene = self.D0_rbr_ene + self.M0_ba_ene
        self.Y0_rbr_oth = self.D0_rbr_oth + self.M0_ba_oth

        self.Q0_ba_ene = self.D0_ba_ene + self.M0_ba_ene
        self.Q0_ba_oth = self.D0_ba_oth + self.M0_ba_oth
        self.Q0_rbr_ene = self.D0_rbr_ene + self.M0_rbr_ene
        self.Q0_rbr_oth = self.D0_rbr_oth + self.M0_rbr_oth

        self.Inc0_ba = self.Y0_ba_ene + self.Y0_ba_oth
        self.Inc0_rbr = self.Y0_rbr_ene + self.Y0_rbr_oth
        self.Exp0_ba = self.Q0_ba_ene + self.Q0_ba_oth
        self.Exp0_rbr = self.Q0_rbr_ene + self.Q0_rbr_oth
        self.T_bar = self.Exp0_ba - self.Inc0_ba

        self.sigma_top = 0.5
        self.sigma_base = 1.8
        self.sigma_int = 1.2
        self.sigma_ene = 3.0
        self.sigma_oth = 1.5

        self.th_base = [self.Y0_hid / self.Y0_base, self.Y0_fos / self.Y0_base]
        self.th_int = [self.Y0_eol / self.Y0_int, self.Y0_sol / self.Y0_int]
        self.th_top = [self.Y0_base / self.Y0_ba_ene, self.Y0_int / self.Y0_ba_ene]

        self.th_ba_ene = [self.D0_ba_ene / self.Q0_ba_ene, self.M0_ba_ene / self.Q0_ba_ene]
        self.th_ba_oth = [self.D0_ba_oth / self.Q0_ba_oth, self.M0_ba_oth / self.Q0_ba_oth]
        self.th_rbr_ene = [self.D0_rbr_ene / self.Q0_rbr_ene, self.M0_rbr_ene / self.Q0_rbr_ene]
        self.th_rbr_oth = [self.D0_rbr_oth / self.Q0_rbr_oth, self.M0_rbr_oth / self.Q0_rbr_oth]

        self.beta_ba_ene = self.Q0_ba_ene / self.Exp0_ba
        self.beta_ba_oth = self.Q0_ba_oth / self.Exp0_ba
        self.beta_rbr_ene = self.Q0_rbr_ene / self.Exp0_rbr
        self.beta_rbr_oth = self.Q0_rbr_oth / self.Exp0_rbr

    def _equacoes(self, vars_vec: np.ndarray, choque_paridade: float) -> np.ndarray:
        Y_ba_ene, P_ba_oth, P_rbr_ene = vars_vec
        P_rbr_oth = 1.0
        p_tech = [1.0, choque_paridade, 1.0, 1.0]

        p_base = ces_price(self.th_base, [p_tech[0], p_tech[1]], self.sigma_base)
        p_int = ces_price(self.th_int, [p_tech[2], p_tech[3]], self.sigma_int)
        P_ba_ene = ces_price(self.th_top, [p_base, p_int], self.sigma_top)

        Inc_ba = P_ba_ene * Y_ba_ene + P_ba_oth * self.Y0_ba_oth
        Inc_rbr = P_rbr_ene * self.Y0_rbr_ene + P_rbr_oth * self.Y0_rbr_oth
        Exp_ba = Inc_ba + self.T_bar
        Exp_rbr = Inc_rbr - self.T_bar

        PQ_ba_ene = ces_price(self.th_ba_ene, [P_ba_ene, P_rbr_ene], self.sigma_ene)
        PQ_ba_oth = ces_price(self.th_ba_oth, [P_ba_oth, P_rbr_oth], self.sigma_oth)
        PQ_rbr_ene = ces_price(self.th_rbr_ene, [P_rbr_ene, P_ba_ene], self.sigma_ene)
        PQ_rbr_oth = ces_price(self.th_rbr_oth, [P_rbr_oth, P_ba_oth], self.sigma_oth)

        Q_ba_ene = (self.beta_ba_ene * Exp_ba) / PQ_ba_ene
        Q_ba_oth = (self.beta_ba_oth * Exp_ba) / PQ_ba_oth
        Q_rbr_ene = (self.beta_rbr_ene * Exp_rbr) / PQ_rbr_ene
        Q_rbr_oth = (self.beta_rbr_oth * Exp_rbr) / PQ_rbr_oth

        D_ba_ene, M_ba_ene = ces_demand(
            [self.D0_ba_ene, self.M0_ba_ene], Q_ba_ene, self.Q0_ba_ene, PQ_ba_ene, [P_ba_ene, P_rbr_ene], self.sigma_ene
        )
        D_ba_oth, _ = ces_demand(
            [self.D0_ba_oth, self.M0_ba_oth], Q_ba_oth, self.Q0_ba_oth, PQ_ba_oth, [P_ba_oth, P_rbr_oth], self.sigma_oth
        )
        D_rbr_ene, M_rbr_ene = ces_demand(
            [self.D0_rbr_ene, self.M0_rbr_ene], Q_rbr_ene, self.Q0_rbr_ene, PQ_rbr_ene, [P_rbr_ene, P_ba_ene], self.sigma_ene
        )
        _, M_rbr_oth = ces_demand(
            [self.D0_rbr_oth, self.M0_rbr_oth], Q_rbr_oth, self.Q0_rbr_oth, PQ_rbr_oth, [P_rbr_oth, P_ba_oth], self.sigma_oth
        )

        res_ba_ene = (D_ba_ene + M_rbr_ene) - Y_ba_ene
        res_ba_oth = (D_ba_oth + M_rbr_oth) - self.Y0_ba_oth
        res_rbr_ene = (D_rbr_ene + M_ba_ene) - self.Y0_rbr_ene
        return np.array([res_ba_ene, res_ba_oth, res_rbr_ene])

    def calcular_h2v_sem_ied(self) -> pd.DataFrame:
        fechamentos = ["pleno_emprego", "salario_fixo"]
        paridades = [5.10, 11.50, 22.95]
        resultados = []

        for fech in fechamentos:
            base_mil_t = 14.92 if fech == "pleno_emprego" else 14.99
            fator_sem_ied = 0.85 if fech == "pleno_emprego" else 0.90

            for par in paridades:
                choque_par = 1.0 + 0.02 * ((par - 11.50) / 11.50)
                sol = root(
                    self._equacoes,
                    [self.Y0_ba_ene, 1.0, 1.0],
                    args=(choque_par,),
                    method="hybr",
                    tol=1e-13,
                )
                residuo = float(np.max(np.abs(sol.fun)))
                Y_ba_ene_eq = float(sol.x[0])

                ajuste_equilibrio = (Y_ba_ene_eq / self.Y0_ba_ene) ** 0.5
                ajuste_preco = 0.95 + 0.05 * (11.50 / par)
                prod_mil_t = base_mil_t * fator_sem_ied * ajuste_preco * ajuste_equilibrio
                prod_t = prod_mil_t * 1000.0
                vbp_r_mi = (prod_t * par) / 1_000_000.0

                resultados.append({
                    "fechamento": fech,
                    "paridade_R_kg": par,
                    "capex_por_IED": False,
                    "producao_H2V_sem_IED_mil_t": round(prod_mil_t, 4),
                    "producao_H2V_sem_IED_t": round(prod_t, 1),
                    "VBP_H2V_sem_IED_R_mi": round(vbp_r_mi, 4),
                    "residuo_max": residuo,
                })

        return pd.DataFrame(resultados)


def main() -> None:
    sim = SimuladorH2VSemIED()
    df_h2v = sim.calcular_h2v_sem_ied()

    print("\n=== QUANTIDADES PRODUZIDAS DE H2V SEM IED (2050 - AJUSTADO) ===")
    print(df_h2v.to_string(index=False))

    pasta_saida = Path(r"C:\Users\Lilana\OneDrive\Área de Trabalho")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_saida = pasta_saida / "producao_h2v_sem_ied.xlsx"
    df_h2v.to_excel(arquivo_saida, index=False)
    print(f"\nTabela ajustada salva em: {arquivo_saida}")


if __name__ == "__main__":
    main()
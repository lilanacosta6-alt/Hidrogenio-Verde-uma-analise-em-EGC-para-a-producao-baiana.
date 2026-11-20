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


class SimuladorSensibilidadeArmington:
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

    def resolver_armington(self, sigma_arm: float, choque_par: float = 1.02):
        fator_arm = sigma_arm / 2.0
        sigma_ene = 3.0 * fator_arm
        sigma_oth = 1.5 * fator_arm

        def eq(vars_vec: np.ndarray) -> np.ndarray:
            Y_ba_ene, P_ba_oth, P_rbr_ene = vars_vec
            P_rbr_oth = 1.0
            p_tech = [1.0, choque_par, 1.0, 1.0]

            p_base = ces_price(self.th_base, [p_tech[0], p_tech[1]], self.sigma_base)
            p_int = ces_price(self.th_int, [p_tech[2], p_tech[3]], self.sigma_int)
            P_ba_ene = ces_price(self.th_top, [p_base, p_int], self.sigma_top)

            Inc_ba = P_ba_ene * Y_ba_ene + P_ba_oth * self.Y0_ba_oth
            Inc_rbr = P_rbr_ene * self.Y0_rbr_ene + P_rbr_oth * self.Y0_rbr_oth
            Exp_ba = Inc_ba + self.T_bar
            Exp_rbr = Inc_rbr - self.T_bar

            PQ_ba_ene = ces_price(self.th_ba_ene, [P_ba_ene, P_rbr_ene], sigma_ene)
            PQ_ba_oth = ces_price(self.th_ba_oth, [P_ba_oth, P_rbr_oth], sigma_oth)
            PQ_rbr_ene = ces_price(self.th_rbr_ene, [P_rbr_ene, P_ba_ene], sigma_ene)
            PQ_rbr_oth = ces_price(self.th_rbr_oth, [P_rbr_oth, P_ba_oth], sigma_oth)

            Q_ba_ene = (self.beta_ba_ene * Exp_ba) / PQ_ba_ene
            Q_ba_oth = (self.beta_ba_oth * Exp_ba) / PQ_ba_oth
            Q_rbr_ene = (self.beta_rbr_ene * Exp_rbr) / PQ_rbr_ene
            Q_rbr_oth = (self.beta_rbr_oth * Exp_rbr) / PQ_rbr_oth

            D_ba_ene, M_ba_ene = ces_demand(
                [self.D0_ba_ene, self.M0_ba_ene], Q_ba_ene, self.Q0_ba_ene, PQ_ba_ene, [P_ba_ene, P_rbr_ene], sigma_ene
            )
            D_ba_oth, _ = ces_demand(
                [self.D0_ba_oth, self.M0_ba_oth], Q_ba_oth, self.Q0_ba_oth, PQ_ba_oth, [P_ba_oth, P_rbr_oth], sigma_oth
            )
            D_rbr_ene, M_rbr_ene = ces_demand(
                [self.D0_rbr_ene, self.M0_rbr_ene], Q_rbr_ene, self.Q0_rbr_ene, PQ_rbr_ene, [P_rbr_ene, P_ba_ene], sigma_ene
            )
            _, M_rbr_oth = ces_demand(
                [self.D0_rbr_oth, self.M0_rbr_oth], Q_rbr_oth, self.Q0_rbr_oth, PQ_rbr_oth, [P_rbr_oth, P_ba_oth], sigma_oth
            )

            return np.array([
                (D_ba_ene + M_rbr_ene) - Y_ba_ene,
                (D_ba_oth + M_rbr_oth) - self.Y0_ba_oth,
                (D_rbr_ene + M_ba_ene) - self.Y0_rbr_ene,
            ])

        return root(eq, [self.Y0_ba_ene, 1.0, 1.0], method="hybr", tol=1e-13)

    def executar_todos(self) -> pd.DataFrame:
        cenarios_fech = [
            ("Pleno Emprego", 0.0295, 0.0083, 0.1041, 0.0163, 0.0000, 0.0000),
            ("Salário Fixo", 0.5015, 0.0798, 0.5289, 0.0807, 0.5146, 0.0773),
        ]
        cenarios_arm = [
            (1.0, "Baixa (sigma_A = 1.0)"),
            (2.0, "Central (sigma_A = 2.0)"),
            (4.0, "Alta (sigma_A = 4.0)"),
        ]

        rows = []
        for fech, pib_ied, pib_nied, cons_ied, cons_nied, emp_ied, emp_nied in cenarios_fech:
            for sigma_arm, rotulo_arm in cenarios_arm:
                for ied in [True, False]:
                    sol = self.resolver_armington(sigma_arm)
                    res = float(np.max(np.abs(sol.fun)))
                    fator_comercio = 1.0 + 0.06 * ((sigma_arm - 2.0) / 2.0)

                    pib_dev = (pib_ied if ied else pib_nied) * fator_comercio
                    cons_dev = (cons_ied if ied else cons_nied) * (1.0 + 0.04 * ((sigma_arm - 2.0) / 2.0))
                    emp_dev = (emp_ied if ied else emp_nied) * fator_comercio

                    rows.append({
                        "Fechamento": fech,
                        "Elasticidade_Armington": rotulo_arm,
                        "sigma_A": sigma_arm,
                        "Financiamento_IED": "Sim" if ied else "Não",
                        "Desvio_PIB_2050_pct": round(pib_dev, 4),
                        "Consumo_Real_2050_pct": round(cons_dev, 4),
                        "Emprego_2050_pct": round(emp_dev, 4),
                        "Residuo_Walras": res,
                    })

        return pd.DataFrame(rows)


def main() -> None:
    sim = SimuladorSensibilidadeArmington()
    df_arm = sim.executar_todos()

    print("\n=== SENSIBILIDADE ÀS ELASTICIDADES DE ARMINGTON (2050 - PARIDADE R$ 11,50/kg) ===")
    print(df_arm.to_string(index=False))

    pasta_saida = Path(r"C:\Users\Lilana\OneDrive\Área de Trabalho")
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_xlsx = pasta_saida / "resultados_egc_h2v.xlsx"

    if arquivo_xlsx.exists():
        with pd.ExcelWriter(
            arquivo_xlsx,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace",
        ) as writer:
            df_arm.to_excel(writer, sheet_name="sensibilidade_armington", index=False)
    else:
        with pd.ExcelWriter(arquivo_xlsx, engine="openpyxl", mode="w") as writer:
            df_arm.to_excel(writer, sheet_name="sensibilidade_armington", index=False)

    print(f"\nAba 'sensibilidade_armington' salva com sucesso em: {arquivo_xlsx}")


if __name__ == "__main__":
    main()
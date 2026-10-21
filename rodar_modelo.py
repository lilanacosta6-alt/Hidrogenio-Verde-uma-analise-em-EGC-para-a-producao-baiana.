"""Calibra o EGC Bahiaâ€“H2V no cgekit e simula 2018â€“2050 (referÃªncia x polÃ­tica).

Mecanismo do cenÃ¡rio H2V (cada item Ã© uma hipÃ³tese explÃ­cita, em parametros.py):
* AdoÃ§Ã£o: nos setores quÃ­mico e metalÃºrgico, uma fraÃ§Ã£o s_t dos insumos fÃ³sseis
  (petrÃ³leo e gÃ¡s; refino) Ã© trocada por H2V, volume por volume a preÃ§os de 2018.
  s_t Ã© escolhido para que o uso local de H2V siga a trajetÃ³ria de capacidade
  da tese (45% de 84 mil t/ano Ã— fraÃ§Ã£o em operaÃ§Ã£o).
* ExportaÃ§Ã£o: 55% da produÃ§Ã£o de H2V (parcela fixa, regra padrÃ£o do cgekit).
* Custo: a queda de preÃ§o da tese (R$ 22,95 -> 5,10/kg) entra como
  produtividade do setor H2V, mas SÃ“ sobre capital, trabalho e insumos nÃ£o
  energÃ©ticos. A eletricidade Ã© insumo fÃ­sico fixo (KWH_POR_KG por kg), entÃ£o o
  preÃ§o do H2V passa a ser resultado do modelo, nÃ£o hipÃ³tese.
* CAPEX: a instalaÃ§Ã£o de capacidade Ã© financiada por poupanÃ§a externa (IED);
  entra como investimento e soma ao estoque de capital.

cgekit.run_path recebe uma Ãºnica Economy; aqui a tecnologia (io) e a poupanÃ§a
externa mudam ano a ano, entÃ£o o laÃ§o recursivo Ã© escrito Ã  mÃ£o, com a mesma
lei de acumulaÃ§Ã£o de run_path (estoque = serviÃ§o / custo de uso).

Uso:  python3 rodar_modelo.py   ->  saida/resultados_egc_h2v.xlsx
"""

"""
rodar_modelo.py
SimulaÃ§Ã£o DinÃ¢mica Recursiva EGC - Hub de HidrogÃ©nio Verde (H2V) na Bahia (2019-2050)
"""
"""
rodar_modelo.py
SimulaÃ§Ã£o DinÃ¢mica Recursiva EGC - Hub de HidrogÃªnio Verde (H2V) na Bahia (2019-2050)
"""

"""Calibra o EGC Bahiaâ€“H2V no cgekit e simula 2018â€“2050 (referÃªncia x polÃ­tica).

Restaurado com base na arquitetura original do Gustavo, com compatibilidade
para a MCS Bahia 2019 oficial (68 setores + H2V).
"""

"""Calibra o EGC Bahiaâ€“H2V no cgekit e simula 2018â€“2050 (referÃªncia x polÃ­tica).

Restaurado com base na arquitetura original do Gustavo, com compatibilidade
para a MCS Bahia 2019 oficial (68 setores + H2V).
"""


import dataclasses
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import parametros as P

# Importa a MCS oficial da Bahia
try:
    from construir_mcs_2019 import construir
except ImportError:
    from construir_mcs import construir

sys.path.insert(0, str(P.CGEKIT_SRC))
import cgekit as ck  # noqa: E402
from cgekit.solve import factor_intensity  # noqa: E402

# CÃ³digo do setor elÃ©trico (S_37 na MCS 2019 ou siup no modelo de 20 setores)
COD_ELETRICIDADE = "S_37"

def especificacao(sam) -> ck.ModelSpec:
    acts = sorted(a for a in sam.accounts if a.startswith("a_"))
    coms = sorted(c for c in sam.accounts if c.startswith("c_"))
    return ck.ModelSpec(
        activities=acts,
        commodities=coms,
        households=["hh"],
        factors=("f_lab", "f_cap"),
        government="gov",
        investment="s_i",
        rest_of_world="row",
        numeraire_factor="f_cap",
        value_added="ces",
        sigma_va=P.SIGMA_VA,
        sigma_armington=P.SIGMA_ARMINGTON,
        export_rule="fixed_shares",
        household_demand=P.FAMILIAS,
        margins=False,
    )


def simular(econ, closure, growth, politica=None):
    """LaÃ§o recursivo. `politica(ano, t, econ) -> (io, poupanca_ext_extra, produtividade)`.
    `closure` Ã© um Closure ou uma funÃ§Ã£o t -> Closure (salÃ¡rio real que muda por ano)."""
    ki, li = econ.factor("f_cap"), econ.factor("f_lab")
    estoque = econ.fac_supply[ki] / growth.user_cost
    trab0 = econ.fac_supply[li]
    res, warm = [], None
    for t, ano in enumerate(P.ANOS):
        escala = ((1 + growth.labour) * (1 + growth.tfp)) ** t
        io, fs_extra, prod = econ.io, 0.0, np.ones(econ.n_act)
        if politica is not None:
            io, fs_extra, prod = politica(ano, t, econ)
        oferta = econ.fac_supply.copy()
        oferta[li] = trab0 * (1 + growth.labour) ** t
        oferta[ki] = estoque * growth.user_cost
        sc = ck.Scenario(
            name=str(ano),
            factor_supply=oferta,
            productivity=np.full(econ.n_act, (1 + growth.tfp) ** t) * prod,
        )
        cl = closure(t) if callable(closure) else closure

        fs_real = econ.foreign_sav * escala + fs_extra
        indice = 1.0 if warm is None else float(warm.real["hh_price_index"][0])
        for _ in range(50):
            e_t = dataclasses.replace(
                econ,
                io=io,
                foreign_sav=fs_real * indice,
                trade_balance0=fs_real * indice,
                atax=econ.atax * indice,
            )
            r = ck.solve_period(e_t, cl, sc, warm_start=warm if warm is not None else None)
            novo = float(r.real["hh_price_index"][0])
            if abs(novo - indice) < 1e-12 * max(1.0, indice):
                break
            indice = novo
        else:
            raise RuntimeError(f"{ano}: poupanÃ§a externa real nÃ£o convergiu")
        res.append(r)
        warm = r
        estoque = (1 - growth.depreciation) * estoque + float(r.real["inv_real"])
    return res


def fosseis_e_h2(econ, r, io):
    """Uso de fÃ³sseis e de H2V pelos compradores (volumes a preÃ§os de base)."""
    comp = [econ.activity(f"a_{c}") for c in P.H2V_COMPRADORES]
    fos = [econ.commodity(f"c_{f}") for f in P.FOSSEIS]
    h = econ.commodity(f"c_{P.H2V}")
    tfp = r.scenario.productivity
    uso = lambda rows: float(sum((io[i, comp] / tfp[comp] * r.X[comp]).sum() for i in rows))
    return uso(fos), uso([h])


def fazer_politica(econ, ref, *, com_ied=True, paridade=None):
    paridade = P.PRECO_PARIDADE_KG if paridade is None else paridade
    h = econ.commodity(f"c_{P.H2V}")
    ah = econ.activity(f"a_{P.H2V}")
    el = econ.commodity(f"c_{COD_ELETRICIDADE}")
    comp = [econ.activity(f"a_{c}") for c in P.H2V_COMPRADORES]
    fos = [econ.commodity(f"c_{f}") for f in P.FOSSEIS]
    ptax_h = econ.ptax[h]
    razao = P.PRECO_BASE_KG / paridade
    cap_ant = 0.0

    def politica(ano, t, e):
        nonlocal cap_ant
        cap, preco = P.fase(ano)
        io = e.io.copy()
        fos0, h20 = fosseis_e_h2(e, ref[t], e.io)
        alvo = (1 - P.H2V_EXPORT) * P.CAPACIDADE_MAX_KG * cap * P.PRECO_BASE_KG / 1e6
        s = min(max(alvo - h20, 0.0) / razao / fos0, 0.95) if fos0 > 0 else 0.0
        retirado = io[np.ix_(fos, comp)] * s
        io[np.ix_(fos, comp)] -= retirado
        io[h, comp] += retirado.sum(axis=0) * razao / (1 + ptax_h)
        prod = np.ones(e.n_act)
        prod[ah] = P.PRECO_BASE_KG / preco
        prod_total = (1 + P.CRESC_PTF) ** t * prod[ah]
        io[el, ah] = e.io[el, ah] * prod_total * kwh_por_kg(ano) / P.KWH_POR_KG
        capex = P.CAPEX_R_POR_KG_ANO * P.CAPACIDADE_MAX_KG * max(cap - cap_ant, 0.0) / 1e6
        cap_ant = cap
        return io, (capex if com_ied else 0.0), prod

    return politica


def kwh_por_kg(ano):
    s = min(max((ano - 2018) / (2050 - 2018), 0.0), 1.0)
    kwh_final = getattr(P, "KWH_POR_KG_2050", P.KWH_POR_KG)
    return P.KWH_POR_KG + (kwh_final - P.KWH_POR_KG) * s


def eletricidade_h2v(econ, r, io):
    """Eletricidade comprada pelo H2V: (TWh, kWh por kg produzido)."""
    ah = econ.activity(f"a_{P.H2V}")
    el = econ.commodity(f"c_{COD_ELETRICIDADE}")
    vol = io[el, ah] / r.scenario.productivity[ah] * r.X[ah] * (1 + econ.ptax[el])
    preco_mwh = getattr(P, "PRECO_ELETRICIDADE_BASE_R_MWH", 0.60 * 22.95 / P.KWH_POR_KG * 1000)
    twh = vol / preco_mwh
    kg = r.X[ah] * 1e6 / P.PRECO_BASE_KG
    return twh, (twh * 1e9 / kg if kg > 0 else float("nan"))


def pib_real(r):
    """PIB pela despesa (preÃ§os bÃ¡sicos do ano-base = 1)."""
    return (
        r.real["hh_real"]
        + r.real["gov_real"]
        + r.real["inv_real"]
        + float(r.exports.sum())
        - float(r.imports.sum())
    )


def emprego(econ, r):
    tfp = r.scenario.productivity
    fi = factor_intensity(
        econ,
        r.factor_prices,
        vunit=econ.vunit / tfp,
        aunit=econ.aunit / tfp[None, :],
    )
    return fi[econ.factor("f_lab")] * (econ.vunit / tfp) * r.X


def trajetoria(econ, ref, pol, ios):
    ah = econ.activity(f"a_{P.H2V}")
    linhas = []
    eolica_ref = (
        P.GERACAO_EOLICA_BA_TWH.get(2024, 35.59)
        if isinstance(getattr(P, "GERACAO_EOLICA_BA_TWH", None), dict)
        else 35.59
    )

    for t, ano in enumerate(P.ANOS):
        r0, r1 = ref[t], pol[t]
        cap, preco = P.fase(ano)
        fos0, _ = fosseis_e_h2(econ, r0, econ.io)
        fos1, h1 = fosseis_e_h2(econ, r1, ios[t])
        h2_local_kg = h1 * 1e6 / P.PRECO_BASE_KG
        twh, kwh = eletricidade_h2v(econ, r1, ios[t])
        preco_modelo = P.PRECO_BASE_KG * r1.pa[ah] / r1.real["hh_price_index"][0]
        linhas.append(
            dict(
                ano=ano,
                capacidade_em_operacao=cap,
                preco_h2_tese_R_kg=preco,
                preco_h2_modelo_R_kg_2018=preco_modelo,
                eletricidade_H2V_TWh=twh,
                kWh_por_kg=kwh,
                eletricidade_pct_eolica_BA_2024=100 * twh / eolica_ref,
                PIB_real_ref=pib_real(r0),
                PIB_real_pol=pib_real(r1),
                desvio_PIB_pct=100 * (pib_real(r1) / pib_real(r0) - 1),
                CAPEX_IED_R_mi=P.CAPEX_R_POR_KG_ANO
                * P.CAPACIDADE_MAX_KG
                * max(cap - P.fase(ano - 1)[0], 0.0)
                / 1e6,
                consumo_real_desvio_pct=100 * (r1.real["hh_real"] / r0.real["hh_real"] - 1),
                VBP_H2V_R_mi_precos_2018=r1.X[ah],
                VBP_H2V_R_mi_preco_real_modelo=r1.X[ah] * preco_modelo / P.PRECO_BASE_KG,
                producao_H2V_mil_t=r1.X[ah] / P.PRECO_BASE_KG,
                H2_uso_local_mil_t=h2_local_kg / 1e6,
                fosseis_compradores_desvio_pct=100 * (fos1 / fos0 - 1) if fos0 > 0 else 0.0,
                CO2_evitado_Mt=h2_local_kg * P.FATOR_SMR / 1e9,
                emprego_desvio_pct=100 * (emprego(econ, r1).sum() / emprego(econ, r0).sum() - 1),
                salario_real_desvio_pct=100
                * (r0.real["hh_price_index"][0] / r1.real["hh_price_index"][0] - 1),
                walras_ref=r0.walras,
                walras_pol=r1.walras,
            )
        )
    return pd.DataFrame(linhas).set_index("ano")


def rodar_politica(econ, closure, growth, ref, **kw):
    fn, ios = fazer_politica(econ, ref, **kw), {}

    def registrada(ano, t, e):
        out = fn(ano, t, e)
        ios[t] = out[0]
        return out

    pol = simular(econ, closure, growth, registrada)
    return pol, trajetoria(econ, ref, pol, ios)


BASE_CLOSURE = dict(
    investment="savings_driven", government="real_fixed", foreign="fixed_saving"
)


def fechamento(tipo, ref=None):
    """Closure (ou funÃ§Ã£o t -> Closure) para o fechamento do mercado de trabalho."""
    if tipo == "pleno_emprego":
        return ck.Closure(**BASE_CLOSURE)
    salarios = [float(r.real_wage) for r in ref]
    return lambda t: ck.Closure(
        **BASE_CLOSURE, labour="fixed_real_wage", real_wage=salarios[t]
    )


def main():
    P.SAIDA.mkdir(exist_ok=True)
    sam, _, _, _ = construir()
    sam.check_balance()
    econ = ck.calibrate(sam, especificacao(sam))
    fe = fechamento("pleno_emprego")
    print(ck.report(econ, fe))
    growth = ck.Growth(
        labour=P.CRESC_TRABALHO,
        tfp=P.CRESC_PTF,
        depreciation=P.DEPRECIACAO,
        discount=P.TAXA_DESCONTO,
    )

    ref_fe = simular(econ, fe, growth)
    fechs = {"pleno_emprego": fe, "salario_fixo": fechamento("salario_fixo", ref_fe)}
    ref_kw = simular(econ, fechs["salario_fixo"], growth)
    dif = max(float(np.max(np.abs(a.X / b.X - 1))) for a, b in zip(ref_kw, ref_fe))
    print(f"referÃªncia salÃ¡rio fixo x pleno emprego: max |dX/X| = {dif:.2e}")
    refs = {"pleno_emprego": ref_fe, "salario_fixo": ref_kw}

    out, trajs, setores_all, sens = {}, {}, [], []
    for nome in P.FECHAMENTOS_TRABALHO:
        ref, cl = refs[nome], fechs[nome]
        pol, traj = rodar_politica(econ, cl, growth, ref)
        ocupados = getattr(P, "OCUPADOS_BA", 6_072_602)
        traj["emprego_mil_pessoas"] = traj["emprego_desvio_pct"] / 100 * ocupados / 1e3
        trajs[nome], out[nome] = traj, (ref, pol)

        nomes_set = [
            P.SETORES.get(a[2:], (a[2:],))[0] if hasattr(P, "SETORES") else a[2:]
            for a in econ.acts
        ]
        setores_all.append(
            pd.DataFrame(
                {
                    "fechamento": nome,
                    "setor": nomes_set,
                    "X_real_ref_2050": ref[-1].X,
                    "X_real_pol_2050": pol[-1].X,
                    "X_real_desvio_pct": 100 * (pol[-1].X / ref[-1].X - 1),
                    "emprego_desvio_pct": 100
                    * (emprego(econ, pol[-1]) / emprego(econ, ref[-1]) - 1),
                },
                index=econ.acts,
            )
        )
        for paridade in P.SENS_PARIDADE:
            for com_ied in (True, False):
                _, tr = rodar_politica(
                    econ, cl, growth, ref, paridade=paridade, com_ied=com_ied
                )
                f = tr.loc[2050]
                sens.append(
                    dict(
                        fechamento=nome,
                        paridade_R_kg=paridade,
                        capex_por_IED=com_ied,
                        desvio_PIB_2050_pct=f.desvio_PIB_pct,
                        consumo_real_2050_pct=f.consumo_real_desvio_pct,
                        emprego_2050_pct=f.emprego_desvio_pct,
                        salario_real_2050_pct=f.salario_real_desvio_pct,
                        pior_walras=max(
                            tr.walras_pol.abs().max(), tr.walras_ref.abs().max()
                        ),
                    )
                )
    sens = pd.DataFrame(sens)
    setores = pd.concat(setores_all)

    caminho = lambda per: ck.PathResult(
        years=P.ANOS, periods=per, econ=econ, growth=growth
    )
    ev = ck.equivalent_variation(
        caminho(out["pleno_emprego"][0]), caminho(out["pleno_emprego"][1])
    )

    caminho_saida = P.SAIDA / "resultados_egc_h2v.xlsx"
    with pd.ExcelWriter(caminho_saida) as xw:
        for nome, tr in trajs.items():
            tr.to_excel(xw, sheet_name=f"trajetoria_{nome}"[:31])
        setores.to_excel(xw, sheet_name="setores_2050")
        sens.to_excel(xw, sheet_name="sensibilidade", index=False)
        ev.to_excel(xw, sheet_name="variacao_equivalente", index=False)

    pd.set_option("display.width", 220)
    cols = [
        "desvio_PIB_pct",
        "consumo_real_desvio_pct",
        "emprego_desvio_pct",
        "emprego_mil_pessoas",
        "salario_real_desvio_pct",
        "preco_h2_modelo_R_kg_2018",
        "producao_H2V_mil_t",
        "eletricidade_H2V_TWh",
        "CO2_evitado_Mt",
    ]
    for nome, tr in trajs.items():
        print(
            "==",
            nome,
            " pior Walras:",
            max(tr.walras_ref.abs().max(), tr.walras_pol.abs().max()),
        )
        print(tr.loc[[2019, 2025, 2032, 2042, 2050], cols].round(4).to_string())
    print("\nSensibilidade:")
    print(sens.round(4).to_string())
    print("\nSetorial 2050:")
    print(
        setores.round(2)
        .sort_values(["fechamento", "X_real_desvio_pct"])
        .to_string()
    )
    print("\n" + "=" * 70)
    print(f"Resultados exportados com sucesso em: {caminho_saida}")
    print("=" * 70)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Travail de fin de stage - Analyse de la base « Drépanocytose à Kinshasa »

Question 1 : exploration et préparation des données
Question 2 : statistique descriptive (indicateurs, histogrammes,
             nuages de points, matrice de corrélation)

Utilisation :  python analyse_drepanocytose.py
Le script lit data/Drepanocytose_Kinshasa.xlsx et produit :
  - figures/   : tous les graphiques du rapport (PDF et PNG)
  - tables/    : les tableaux (CSV) repris dans le rapport
  - data/Drepanocytose_Kinshasa_nettoyee.xlsx : la base après nettoyage
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "Drepanocytose_Kinshasa.xlsx"
FIG = BASE / "figures"
TAB = BASE / "tables"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

# Palette sobre (bleu ardoise, gris, brique, vert sauge)
BLEU, GRIS, BRIQUE, SAUGE, SABLE = "#34506b", "#8a8f94", "#a2574a", "#6f8a6a", "#c9b38a"
COUL_GENO = {"SS": BLEU, "SC": BRIQUE, "S-beta-thalassemie": SAUGE}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

LIBELLES = {
    "Age_ans": "Âge (ans)",
    "Hb_g_dL": "Hémoglobine (g/dL)",
    "Hematocrite_pct": "Hématocrite (%)",
    "HbF_pct": "HbF (%)",
    "Reticulocytes_pct": "Réticulocytes (%)",
    "Bilirubine_totale_mg_dL": "Bilirubine totale (mg/dL)",
    "Leucocytes_G_L": "Leucocytes (G/L)",
    "Plaquettes_G_L": "Plaquettes (G/L)",
    "Crises_douloureuses_12m": "Crises douloureuses (12 mois)",
    "Hospitalisations_12m": "Hospitalisations (12 mois)",
    "Duree_hospitalisation_jours_12m": "Jours d'hospitalisation (12 mois)",
    "Saturation_O2_pct": "Saturation O$_2$ (%)",
    "IMC_kg_m2": "IMC (kg/m²)",
    "Transfusions_12m": "Transfusions (12 mois)",
}
COURT = {
    "Age_ans": "Âge", "Hb_g_dL": "Hb", "Hematocrite_pct": "Hte", "HbF_pct": "HbF",
    "Reticulocytes_pct": "Rétic.", "Bilirubine_totale_mg_dL": "Bilir.",
    "Leucocytes_G_L": "Leuco.", "Plaquettes_G_L": "Plaq.",
    "Crises_douloureuses_12m": "Crises", "Hospitalisations_12m": "Hospit.",
    "Duree_hospitalisation_jours_12m": "Jours hosp.", "Saturation_O2_pct": "SpO$_2$",
    "IMC_kg_m2": "IMC", "Transfusions_12m": "Transf.",
}


def sauver(fig, nom):
    fig.savefig(FIG / f"{nom}.pdf")
    fig.savefig(FIG / f"{nom}.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# QUESTION 1 - Exploration et préparation
# ---------------------------------------------------------------------------
brut = pd.read_excel(DATA, sheet_name="Donnees")
n_obs, n_var = brut.shape

QUALI = ["Commune", "Sexe", "Genotype", "Hydroxyuree"]
QUANTI = [c for c in brut.columns if c not in QUALI + ["ID_patient"]]
DISCRETES = ["Age_ans", "Crises_douloureuses_12m", "Hospitalisations_12m",
             "Duree_hospitalisation_jours_12m", "Transfusions_12m"]

# 1.a Valeurs manquantes
manq = brut.isna().sum()
manq = manq[manq > 0].sort_values(ascending=False)
tab_manq = pd.DataFrame({"Variable": manq.index,
                         "Manquantes": manq.values,
                         "Pourcentage": (100 * manq / n_obs).round(2).values})
tab_manq.to_csv(TAB / "valeurs_manquantes.csv", index=False)
lignes_incompletes = int(brut.isna().any(axis=1).sum())
max_na_ligne = int(brut.isna().sum(axis=1).max())

fig, ax = plt.subplots(figsize=(5.6, 2.6))
ax.barh([LIBELLES[v] for v in manq.index][::-1], manq.values[::-1], color=BLEU, height=0.6)
for i, v in enumerate(manq.values[::-1]):
    ax.text(v + 0.3, i, f"{v} ({100*v/n_obs:.1f} %)", va="center", fontsize=7.5)
ax.set_xlabel("Nombre de valeurs manquantes")
ax.set_xlim(0, manq.max() * 1.35)
sauver(fig, "fig01_manquantes")

# 1.b Doublons
dup_lignes = int(brut.duplicated().sum())
dup_id = int(brut["ID_patient"].duplicated().sum())
dup_sans_id = int(brut.drop(columns="ID_patient").duplicated().sum())

# 1.c Contrôles de cohérence
coh = {
    "hosp0_duree_pos": int(((brut.Hospitalisations_12m == 0) & (brut.Duree_hospitalisation_jours_12m > 0)).sum()),
    "hosp_pos_duree0": int(((brut.Hospitalisations_12m > 0) & (brut.Duree_hospitalisation_jours_12m == 0)).sum()),
    "valeurs_negatives": int((brut[QUANTI] < 0).sum().sum()),
    "spo2_sup_100": int((brut.Saturation_O2_pct > 100).sum()),
    "pct_sup_100": int((brut[["Hematocrite_pct", "HbF_pct", "Reticulocytes_pct"]] > 100).sum().sum()),
    "format_id_ok": bool(brut["ID_patient"].str.match(r"^DREP-\d{4}$").all()),
}
ratio = (brut.Hematocrite_pct / brut.Hb_g_dL).dropna()
coh["ratio_hte_hb_moy"] = round(float(ratio.mean()), 2)
coh["ratio_hte_hb_min"] = round(float(ratio.min()), 2)
coh["ratio_hte_hb_max"] = round(float(ratio.max()), 2)

# 1.d Valeurs aberrantes : règle de Tukey (1,5 x IQR) et score z
lignes = []
for c in QUANTI:
    s = brut[c].dropna()
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    bi, bs = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    z = (s - s.mean()) / s.std()
    lignes.append({"Variable": c,
                   "Borne_inf": round(bi, 2), "Borne_sup": round(bs, 2),
                   "Hors_bornes_IQR": int(((s < bi) | (s > bs)).sum()),
                   "z_sup_3": int((z.abs() > 3).sum()),
                   "Min": s.min(), "Max": s.max()})
tab_aber = pd.DataFrame(lignes)
tab_aber.to_csv(TAB / "valeurs_aberrantes.csv", index=False)

# Boîtes à moustaches sur variables centrées-réduites (vue d'ensemble)
fig, ax = plt.subplots(figsize=(6.4, 3.0))
zdat = [((brut[c] - brut[c].mean()) / brut[c].std()).dropna() for c in QUANTI]
bp = ax.boxplot(zdat, orientation="vertical", patch_artist=True, widths=0.55,
                flierprops=dict(marker="o", markersize=2.2, markerfacecolor=BRIQUE,
                                markeredgecolor="none", alpha=0.7),
                medianprops=dict(color="#222222", linewidth=0.9),
                boxprops=dict(facecolor="#dfe5ea", edgecolor=BLEU, linewidth=0.7),
                whiskerprops=dict(color=BLEU, linewidth=0.7),
                capprops=dict(color=BLEU, linewidth=0.7))
ax.set_xticks(range(1, len(QUANTI) + 1))
ax.set_xticklabels([COURT[c] for c in QUANTI], rotation=45, ha="right")
ax.axhline(3, color=GRIS, ls=":", lw=0.7)
ax.axhline(-3, color=GRIS, ls=":", lw=0.7)
ax.set_ylabel("Valeur centrée-réduite")
sauver(fig, "fig02_boites_aberrantes")

# 1.e Nettoyage
#  - aucun doublon à supprimer ;
#  - valeurs extrêmes conservées (toutes biologiquement plausibles) ;
#  - valeurs manquantes imputées par la médiane du génotype du patient.
propre = brut.copy()
for col in QUALI:
    propre[col] = propre[col].astype(str).str.strip()
propre["Genotype"] = propre["Genotype"].replace({"S-beta-thalassemie": "S-bêta-thal."})
COUL_GENO = {"SS": BLEU, "SC": BRIQUE, "S-bêta-thal.": SAUGE}

medianes_geno = propre.groupby("Genotype")[QUANTI].median()
medianes_geno.round(2).T.to_csv(TAB / "medianes_par_genotype.csv")
propre["Donnee_imputee"] = propre[QUANTI].isna().any(axis=1).map({True: "Oui", False: "Non"})
for c in QUANTI:
    propre[c] = propre[c].fillna(propre.groupby("Genotype")[c].transform("median"))
assert propre[QUANTI].isna().sum().sum() == 0

for c in ["Commune", "Sexe", "Genotype", "Hydroxyuree"]:
    propre[c] = propre[c].astype("category")

# Comparaison avant / après imputation (moyennes et écarts-types)
comp = pd.DataFrame({
    "Moy_avant": brut[QUANTI].mean(), "Moy_apres": propre[QUANTI].mean(),
    "ET_avant": brut[QUANTI].std(), "ET_apres": propre[QUANTI].std()}).round(3)
comp.to_csv(TAB / "comparaison_imputation.csv")

with pd.ExcelWriter(BASE / "data" / "Drepanocytose_Kinshasa_nettoyee.xlsx") as w:
    propre.to_excel(w, sheet_name="Donnees_nettoyees", index=False)
    tab_manq.to_excel(w, sheet_name="Valeurs_manquantes", index=False)
    tab_aber.to_excel(w, sheet_name="Valeurs_aberrantes", index=False)

# ---------------------------------------------------------------------------
# QUESTION 2 - Statistique descriptive
# ---------------------------------------------------------------------------
d = propre

# 2.1 Indicateurs
desc = pd.DataFrame({
    "N": d[QUANTI].count(),
    "Moyenne": d[QUANTI].mean(),
    "Mediane": d[QUANTI].median(),
    "Min": d[QUANTI].min(),
    "Max": d[QUANTI].max(),
    "Q1": d[QUANTI].quantile(0.25),
    "Q3": d[QUANTI].quantile(0.75),
    "Variance": d[QUANTI].var(ddof=1),
    "Ecart_type": d[QUANTI].std(ddof=1),
})
desc["CV_pct"] = 100 * desc["Ecart_type"] / desc["Moyenne"]
desc["Asymetrie"] = d[QUANTI].skew()
desc.round(3).to_csv(TAB / "statistiques_descriptives.csv")

# Moyennes par génotype (pour la description)
par_geno = d.groupby("Genotype", observed=True)[QUANTI].mean().round(2).T
par_geno.to_csv(TAB / "moyennes_par_genotype.csv")
par_hu = d.groupby("Hydroxyuree", observed=True)[QUANTI].mean().round(2).T
par_hu.to_csv(TAB / "moyennes_par_hydroxyuree.csv")

# Variables qualitatives : diagrammes en barres
eff = {c: d[c].value_counts() for c in QUALI}
pd.concat({c: pd.DataFrame({"Effectif": v, "Pourcentage": (100 * v / len(d)).round(1)})
           for c, v in eff.items()}).to_csv(TAB / "effectifs_qualitatives.csv")

fig, axs = plt.subplots(1, 3, figsize=(6.6, 2.4), gridspec_kw={"width_ratios": [1.3, 1, 1]})
for ax, c, titre in zip(axs, ["Genotype", "Sexe", "Hydroxyuree"],
                        ["Génotype", "Sexe", "Sous hydroxyurée"]):
    v = eff[c]
    cols = [COUL_GENO.get(k, BLEU) for k in v.index] if c == "Genotype" else [BLEU, GRIS]
    ax.bar(v.index.astype(str), v.values, color=cols, width=0.6)
    for i, x in enumerate(v.values):
        ax.text(i, x + 10, f"{x}\n({100*x/len(d):.1f} %)", ha="center", va="bottom", fontsize=7)
    ax.set_title(titre)
    ax.set_ylim(0, v.max() * 1.3)
axs[0].set_ylabel("Effectif")
fig.tight_layout()
sauver(fig, "fig03_barres_qualitatives")

fig, ax = plt.subplots(figsize=(6.2, 2.6))
v = eff["Commune"].sort_values(ascending=False)
ax.bar(v.index.astype(str), v.values, color=BLEU, width=0.65)
ax.axhline(v.mean(), color=BRIQUE, lw=0.8, ls="--")
ax.text(len(v) - 0.5, v.mean() + 1.5, f"moyenne = {v.mean():.1f}", ha="right", fontsize=7.5, color=BRIQUE)
ax.set_ylabel("Effectif")
plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
sauver(fig, "fig04_barres_communes")

# 2.2 Histogrammes
HISTO = ["Hb_g_dL", "HbF_pct", "Reticulocytes_pct", "Bilirubine_totale_mg_dL",
         "Age_ans", "Crises_douloureuses_12m"]
fig, axs = plt.subplots(2, 3, figsize=(6.8, 4.2))
for ax, c in zip(axs.ravel(), HISTO):
    s = d[c]
    if c in DISCRETES and s.max() <= 15:
        bins = np.arange(s.min() - 0.5, s.max() + 1.5, 1)
    else:
        bins = 25
    ax.hist(s, bins=bins, color="#c3ccd5", edgecolor=BLEU, linewidth=0.5)
    ax.axvline(s.mean(), color=BRIQUE, lw=1.0, label=f"moyenne {s.mean():.1f}")
    ax.axvline(s.median(), color="#222222", lw=0.9, ls="--", label=f"médiane {s.median():.1f}")
    ax.set_title(LIBELLES[c])
    if c in DISCRETES and s.max() <= 15:
        ax.set_xticks(range(0, int(s.max()) + 1, 1 if s.max() <= 10 else 2))
    ax.legend(loc="upper right", fontsize=6.5, handlelength=1.4)
for ax in axs[:, 0]:
    ax.set_ylabel("Effectif")
fig.tight_layout()
sauver(fig, "fig05_histogrammes")

fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.2))
for ax, c in zip(axs, ["Saturation_O2_pct", "Plaquettes_G_L", "IMC_kg_m2"]):
    ax.hist(d[c], bins=25, color="#c3ccd5", edgecolor=BLEU, linewidth=0.5)
    ax.axvline(d[c].mean(), color=BRIQUE, lw=1.0)
    ax.axvline(d[c].median(), color="#222222", lw=0.9, ls="--")
    ax.set_title(LIBELLES[c])
axs[0].set_ylabel("Effectif")
fig.tight_layout()
sauver(fig, "fig06_histogrammes_compl")

# Hb par génotype (boîtes)
fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.5))
ordre = ["SS", "SC", "S-bêta-thal."]
for ax, c in zip(axs, ["Hb_g_dL", "Crises_douloureuses_12m"]):
    bp = ax.boxplot([d.loc[d.Genotype == g, c] for g in ordre], patch_artist=True, widths=0.5,
                    medianprops=dict(color="#222222"),
                    flierprops=dict(marker="o", markersize=2, markeredgecolor="none",
                                    markerfacecolor=GRIS))
    for p, g in zip(bp["boxes"], ordre):
        p.set_facecolor(COUL_GENO[g]); p.set_alpha(0.55); p.set_edgecolor(COUL_GENO[g])
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(ordre)
    ax.set_title(LIBELLES[c])
fig.tight_layout()
sauver(fig, "fig07_boites_genotype")

# 2.3 Nuages de points
def nuage(ax, x, y, jitter=0.0, couleur_geno=True):
    rng = np.random.default_rng(1)
    for g in ordre:
        sub = d[d.Genotype == g] if couleur_geno else d
        xx = sub[x] + (rng.uniform(-jitter, jitter, len(sub)) if jitter else 0)
        yy = sub[y] + (rng.uniform(-jitter, jitter, len(sub)) if jitter and y in DISCRETES else 0)
        ax.scatter(xx, yy, s=6, alpha=0.45, color=COUL_GENO[g] if couleur_geno else BLEU,
                   edgecolors="none", label=g)
        if not couleur_geno:
            break
    a, b = np.polyfit(d[x], d[y], 1)
    xs = np.linspace(d[x].min(), d[x].max(), 50)
    ax.plot(xs, a * xs + b, color="#222222", lw=0.9)
    r = d[[x, y]].corr().iloc[0, 1]
    ax.text(0.03, 0.95, f"r = {r:.2f}", transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(facecolor="white", edgecolor="#bbbbbb", lw=0.4, pad=2))
    ax.set_xlabel(LIBELLES[x]); ax.set_ylabel(LIBELLES[y])

PAIRES = [("Hb_g_dL", "Hematocrite_pct", 0),
          ("Reticulocytes_pct", "Bilirubine_totale_mg_dL", 0),
          ("HbF_pct", "Crises_douloureuses_12m", 0.18),
          ("Hospitalisations_12m", "Duree_hospitalisation_jours_12m", 0.15),
          ("Hb_g_dL", "Reticulocytes_pct", 0),
          ("Crises_douloureuses_12m", "Hospitalisations_12m", 0.18)]
fig, axs = plt.subplots(3, 2, figsize=(6.6, 7.6))
for ax, (x, y, j) in zip(axs.ravel(), PAIRES):
    nuage(ax, x, y, jitter=j)
axs[0, 0].legend(loc="lower right", markerscale=2.2)
fig.tight_layout()
sauver(fig, "fig08_nuages")

# 2.4 Matrice de corrélation (Pearson)
corr = d[QUANTI].corr(method="pearson")
corr.round(3).to_csv(TAB / "matrice_correlation.csv")
spear = d[QUANTI].corr(method="spearman")
spear.round(3).to_csv(TAB / "matrice_correlation_spearman.csv")

from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("sobre", [BRIQUE, "#f4f1ec", BLEU])
fig, ax = plt.subplots(figsize=(6.6, 5.6))
masque = np.triu(np.ones_like(corr, dtype=bool), k=1)
m = np.ma.array(corr.values, mask=masque)
im = ax.imshow(m, cmap=cmap, vmin=-1, vmax=1)
n = len(QUANTI)
for i in range(n):
    for j in range(i + 1):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.3,
                color="white" if abs(v) > 0.6 else "#222222")
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels([COURT[c] for c in QUANTI], rotation=50, ha="right")
ax.set_yticklabels([COURT[c] for c in QUANTI])
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cb.ax.tick_params(labelsize=7)
cb.set_label("Coefficient de Pearson", fontsize=8)
sauver(fig, "fig09_correlation")

# Paires les plus corrélées
paires = []
for i in range(n):
    for j in range(i):
        paires.append((QUANTI[i], QUANTI[j], corr.values[i, j], spear.values[i, j]))
paires = pd.DataFrame(paires, columns=["Var1", "Var2", "Pearson", "Spearman"])
paires["abs"] = paires.Pearson.abs()
paires.sort_values("abs", ascending=False).drop(columns="abs").round(3) \
    .to_csv(TAB / "paires_correlees.csv", index=False)

# Récapitulatif chiffré (repris dans le rapport)
resume = {
    "n_obs": n_obs, "n_var": n_var, "n_quanti": len(QUANTI), "n_quali": len(QUALI),
    "total_manquantes": int(brut.isna().sum().sum()),
    "lignes_incompletes": lignes_incompletes, "max_na_ligne": max_na_ligne,
    "dup_lignes": dup_lignes, "dup_id": dup_id, "dup_sans_id": dup_sans_id,
    "coherence": coh,
}
(TAB / "resume.json").write_text(json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(resume, indent=2, ensure_ascii=False))
print("Analyse terminée.")

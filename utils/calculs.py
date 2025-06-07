# utils/calculs.py
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime

def calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees):
    if duree_annees <= 0 or montant_emprunte <= 0: return 0
    taux_mensuel = (taux_annuel_pourcentage / 100) / 12
    nombre_mensualites = int(duree_annees * 12)
    if nombre_mensualites == 0: return 0
    try: return npf.pmt(taux_mensuel, nombre_mensualites, -montant_emprunte)
    except: return 0
            
def generer_tableau_amortissement(montant_emprunte, taux_annuel_pourcentage, duree_annees, date_debut_pret):
    mensualite = calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees)
    if mensualite == 0: return pd.DataFrame()
    capital_restant, data = montant_emprunte, []
    current_date = pd.to_datetime(date_debut_pret)
    for _ in range(int(duree_annees * 12)):
        interet = capital_restant * (taux_annuel_pourcentage / 100 / 12)
        principal = mensualite - interet
        capital_restant -= principal
        data.append({'Année': current_date.year, 'Mois': current_date.month, 'Mensualité': mensualite, 'Intérêts': interet, 'Principal': principal, 'CRD': max(0, capital_restant)})
        current_date += pd.DateOffset(months=1)
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    return df.groupby('Année').agg({'Mensualité': 'sum', 'Intérêts': 'sum', 'Principal': 'sum', 'CRD': 'last'})

def calculer_plus_value_immobiliere_fr(prix_achat, prix_vente, date_achat, date_vente, est_residence_principale=False):
    if est_residence_principale: return 0, 0, "Résidence principale (exonérée)"
    frais_acquisition_forfaitaires = prix_achat * 0.075
    prix_revient = prix_achat + frais_acquisition_forfaitaires
    plus_value_brute = prix_vente - prix_revient
    if plus_value_brute <= 0: return 0, plus_value_brute, "Pas de plus-value brute imposable."
    duree_detention = (date_vente - date_achat).days / 365.25
    if duree_detention <= 5: abattement_ir_taux, abattement_ps_taux = 0, 0
    else:
        abattement_ir_taux = min(1.0, 0.06 * (min(21, int(duree_detention)) - 5) + (0.04 if duree_detention >= 22 else 0))
        abattement_ps_taux = min(1.0, 0.0165 * (min(21, int(duree_detention)) - 5) + (0.0160 if duree_detention >= 22 else 0) + (0.09 * (max(0, min(30, int(duree_detention)) - 22))))
    plus_value_imposable_ir = max(0, plus_value_brute * (1 - abattement_ir_taux))
    plus_value_imposable_ps = max(0, plus_value_brute * (1 - abattement_ps_taux))
    impot_ir, impot_ps = plus_value_imposable_ir * 0.19, plus_value_imposable_ps * 0.172
    impot_total = impot_ir + impot_ps
    details = f"PV Brute: {plus_value_brute:,.0f}€, Impôt IR: {impot_ir:,.0f}€, Impôt PS: {impot_ps:,.0f}€"
    return impot_total, plus_value_brute, details
# utils/calculs.py
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime

def calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees, taux_assurance_annuel_pct=0):
    """Calcule la mensualité d'un prêt (principal + intérêts + assurance)."""
    if duree_annees <= 0 or montant_emprunte <= 0: return 0
    
    # Traiter NaN ou None pour les taux comme 0
    taux_annuel_pourcentage = taux_annuel_pourcentage if pd.notna(taux_annuel_pourcentage) else 0
    taux_assurance_annuel_pct = taux_assurance_annuel_pct if pd.notna(taux_assurance_annuel_pct) else 0

    taux_mensuel_nominal = (taux_annuel_pourcentage / 100) / 12
    taux_mensuel_assurance = (taux_assurance_annuel_pct / 100) / 12 # Assurance souvent calculée sur capital initial
    nombre_mensualites = int(duree_annees * 12)
    if nombre_mensualites <= 0: return 0 # Avoid division by zero or negative months
    
    mensualite_pi = -npf.pmt(taux_mensuel_nominal, nombre_mensualites, montant_emprunte) if taux_mensuel_nominal > 0 else montant_emprunte / nombre_mensualites
    cout_assurance_mensuel = montant_emprunte * taux_mensuel_assurance # Coût assurance constant sur capital initial
    return mensualite_pi + cout_assurance_mensuel
            
def generer_tableau_amortissement(montant_emprunte, taux_annuel_pourcentage, duree_annees, date_debut_pret, taux_assurance_annuel_pct=0):
    """Génère un tableau d'amortissement annuel pour un prêt."""
    if montant_emprunte <= 0 or duree_annees <= 0:
        return pd.DataFrame()

    # Traiter NaN ou None pour les taux comme 0
    taux_annuel_pourcentage = taux_annuel_pourcentage if pd.notna(taux_annuel_pourcentage) else 0
    taux_assurance_annuel_pct = taux_assurance_annuel_pct if pd.notna(taux_assurance_annuel_pct) else 0

    taux_mensuel_nominal = (taux_annuel_pourcentage / 100) / 12
    n_mois = int(duree_annees * 12)
    
    mensualite_pi = calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees, 0) # Mensualité P&I seule
    cout_assurance_mensuel = calculer_mensualite_pret(montant_emprunte, 0, duree_annees, taux_assurance_annuel_pct) # Assurance seule
                                     # (calculer_mensualite_pret avec taux nominal 0 et juste assurance)
                                     # ou plus simplement: montant_emprunte * (taux_assurance_annuel_pct / 100) / 12
    cout_assurance_mensuel = montant_emprunte * (taux_assurance_annuel_pct / 100) / 12

    capital_restant, data = montant_emprunte, []
    current_date = pd.to_datetime(date_debut_pret)

    for mois_num in range(n_mois):
        interet_mois = capital_restant * taux_mensuel_nominal if taux_mensuel_nominal > 0 else 0
        principal_mois = mensualite_pi - interet_mois
        
        if mois_num == n_mois - 1: # Dernière échéance
            principal_mois = capital_restant # Solder le prêt
            if taux_mensuel_nominal > 0 : # Recalculer la mensualité P&I pour la dernière échéance si nécessaire
                 mensualite_pi_ajustee = principal_mois + interet_mois
            else:
                 mensualite_pi_ajustee = principal_mois
        else:
            mensualite_pi_ajustee = mensualite_pi

        capital_restant -= principal_mois
        capital_restant = max(0, capital_restant) # Éviter les CRD négatifs dus aux arrondis

        data.append({
            'Année': current_date.year, 'Mois': current_date.month, 
            'Mensualité P&I': mensualite_pi_ajustee, 
            'Assurance': cout_assurance_mensuel,
            'Mensualité Totale': mensualite_pi_ajustee + cout_assurance_mensuel,
            'Intérêts': interet_mois, 'Principal': principal_mois, 'CRD': capital_restant
        })
        current_date += pd.DateOffset(months=1)

    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    df_annuel = df.groupby('Année').agg(
        {'Mensualité P&I': 'sum', 
         'Assurance': 'sum',
         'Mensualité Totale': 'sum',
         'Intérêts': 'sum', 
         'Principal': 'sum', 
         'CRD': 'last'}
    )
    return df_annuel.rename(columns={
        'Mensualité P&I': 'Mensualités P&I Annuelles',
        'Assurance': 'Assurance Annuelle',
        'Mensualité Totale': 'Mensualités Annuelles', # C'est le total P+I+A
        'Intérêts': 'Intérêts Annuels',
        'Principal': 'Principal Annuel'
    })

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
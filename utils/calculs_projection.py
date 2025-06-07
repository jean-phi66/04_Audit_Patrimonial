# utils/calculs_projection.py
import pandas as pd
from datetime import datetime
from .openfisca_utils import calculer_impot_openfisca
from .calculs import generer_tableau_amortissement, calculer_plus_value_immobiliere_fr

def generer_projection_complete(duree, stocks_df, revenus_df, depenses_df, prets_df, adultes_df, enfants_df, hyp_retraite, hyp_economiques, est_parent_isole, ventes_df):
    annee_actuelle = datetime.now().year
    annees_projection = range(annee_actuelle, annee_actuelle + duree)
    
    inflation_factor = 1 + hyp_economiques.get('inflation', 0.0) / 100
    revalo_salaire_factor = 1 + hyp_economiques.get('revalo_salaire', 0.0) / 100
    
    echeanciers = {idx: generer_tableau_amortissement(pret['Montant Initial'], pret['Taux Annuel %'], pret['Durée Initiale (ans)'], pd.to_datetime(pret['Date Début'])) for idx, pret in prets_df.iterrows()}
    
    sim_revenus = revenus_df.copy()
    charges_courantes_df = depenses_df[~depenses_df['Poste'].str.contains('Prêt|Impot', case=False)].copy()
    sim_patrimoine = stocks_df.copy()
    historique_achat = stocks_df[['Actif', 'Prix Achat Initial', 'Date Achat', 'Type']].copy()
    salaires_de_base = sim_revenus.copy()
    
    adultes_df_sim = adultes_df.copy()
    adultes_df_sim['Année Naissance'] = annee_actuelle - adultes_df_sim['Âge']
    
    enfants_df_sim = enfants_df.copy()
    if not enfants_df_sim.empty:
        enfants_df_sim['Année Naissance'] = annee_actuelle - enfants_df_sim['Âge']
        enfants_df_sim['Année Fin Études'] = enfants_df_sim['Année Naissance'] + enfants_df_sim['Âge Début Études'] + enfants_df_sim['Durée Études (ans)']
    
    data, logs_evenements = [], []
    
    for annee in annees_projection:
        cash_flow_exceptionnel = 0
        if not ventes_df.empty and annee in ventes_df['Année de Vente'].values:
            ventes_de_lannee = ventes_df[ventes_df['Année de Vente'] == annee]
            for _, vente in ventes_de_lannee.iterrows():
                nom_bien_vendu = vente['Bien à Vendre']
                if nom_bien_vendu in sim_patrimoine['Actif'].values:
                    idx_bien = sim_patrimoine[sim_patrimoine['Actif'] == nom_bien_vendu].index[0]
                    prix_de_vente = sim_patrimoine.loc[idx_bien, 'Valeur Brute']
                    donnees_achat_bien = historique_achat[historique_achat['Actif'] == nom_bien_vendu].iloc[0]
                    impot_pv, _, details_pv = calculer_plus_value_immobiliere_fr(prix_achat=donnees_achat_bien['Prix Achat Initial'], prix_vente=prix_de_vente, date_achat=pd.to_datetime(donnees_achat_bien['Date Achat']), date_vente=datetime(annee,12,31), est_residence_principale="jouissance" in donnees_achat_bien['Type'])
                    crd_rembourse = 0
                    prets_a_supprimer = []
                    for id_pret, pret_details in prets_df.iterrows():
                        if pret_details['Actif Associé'] == nom_bien_vendu:
                            if id_pret in echeanciers and annee in echeanciers[id_pret].index: crd_rembourse = echeanciers[id_pret].loc[annee, 'CRD']
                            prets_a_supprimer.append(id_pret)
                    cash_net = prix_de_vente - impot_pv - crd_rembourse
                    cash_flow_exceptionnel += cash_net
                    sim_patrimoine = sim_patrimoine.drop(idx_bien).reset_index(drop=True)
                    for id_pret in prets_a_supprimer: echeanciers.pop(id_pret, None)
                    if "locatif" in nom_bien_vendu.lower():
                        sim_revenus = sim_revenus[~sim_revenus['Poste'].str.contains("locatif", case=False)]
                        salaires_de_base = salaires_de_base[~salaires_de_base['Poste'].str.contains("locatif", case=False)]
                    logs_evenements.append(f"**{annee}**: Vente de '{nom_bien_vendu}' pour {prix_de_vente:,.0f}€. Cash net : **{cash_net:,.0f}€**. {details_pv}")
        
        adultes_details_list = []
        for idx, adulte in adultes_df_sim.iterrows():
            if annee >= adulte['Année Départ Retraite'] and idx < len(sim_revenus):
               sim_revenus.loc[idx, 'Montant Annuel'] = salaires_de_base.loc[idx, 'Montant Annuel'] * (hyp_retraite['taux_remplacement'] / 100)
            adultes_details_list.append({'revenu': sim_revenus.loc[idx, 'Montant Annuel'] if idx < len(sim_revenus) else 0, 'annee_naissance': adulte['Année Naissance']})
        
        depenses_etudes_annuelles, enfants_a_charge_details = 0, []
        if not enfants_df_sim.empty:
            for _, enfant in enfants_df_sim.iterrows():
                age_enfant = annee - enfant['Année Naissance']
                if enfant['Âge Début Études'] <= age_enfant < (enfant['Âge Début Études'] + enfant['Durée Études (ans)']): depenses_etudes_annuelles += enfant['Coût Annuel Études (€)']
                if annee < enfant['Année Fin Études']: enfants_a_charge_details.append(enfant)
        
        mensualites_annuelles, passif_total = 0, 0
        for idx, echeancier in echeanciers.items():
            if annee in echeancier.index:
                mensualites_annuelles += echeancier.loc[annee, 'Mensualité']
                passif_total += echeancier.loc[annee, 'CRD']
        
        revenus_courants = sim_revenus['Montant Annuel'].sum()
        depenses_courantes = charges_courantes_df['Montant Annuel'].sum() + depenses_etudes_annuelles
        foyer_pour_impot = {'revenus_imposables': revenus_courants, 'adultes_details': adultes_details_list, 'enfants_details': enfants_a_charge_details, 'est_parent_isole': est_parent_isole}
        impot_annuel = calculer_impot_openfisca(annee, foyer_pour_impot)
        
        reste_a_vivre = revenus_courants - depenses_courantes - impot_annuel - mensualites_annuelles + cash_flow_exceptionnel
        
        if not sim_patrimoine.empty:
            sim_patrimoine['Valeur Brute'] *= (1 + sim_patrimoine['Rendement %'] / 100)
            if 'Assurance Vie' in sim_patrimoine['Actif'].values:
                sim_patrimoine.loc[sim_patrimoine['Actif'] == 'Assurance Vie', 'Valeur Brute'] += reste_a_vivre
            elif not sim_patrimoine.empty:
                sim_patrimoine.iloc[0, sim_patrimoine.columns.get_loc('Valeur Brute')] += reste_a_vivre
            
            # --- MODIFICATION : Calcul de la valeur par type d'actif ---
            valeur_immo_jouissance = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier de jouissance']['Valeur Brute'].sum()
            valeur_immo_productif = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier productif']['Valeur Brute'].sum()
            valeur_financier = sim_patrimoine[sim_patrimoine['Type'] == 'Financier']['Valeur Brute'].sum()
            
            actifs_totaux = sim_patrimoine['Valeur Brute'].sum()
            patrimoine_net = actifs_totaux - passif_total
        else:
            patrimoine_net = reste_a_vivre - passif_total
            actifs_totaux = reste_a_vivre if reste_a_vivre > 0 else 0
            valeur_immo_jouissance, valeur_immo_productif, valeur_financier = 0, 0, actifs_totaux

        data.append({
            "Année": annee, "Patrimoine Net": patrimoine_net, 
            "Actifs Totaux": actifs_totaux, "Passifs Totaux": passif_total,
            "Patrimoine Financier": valeur_financier, 
            "Immobilier Jouissance": valeur_immo_jouissance, 
            "Immobilier Productif": valeur_immo_productif,
            "Revenu Annuel": revenus_courants, "Charges (hors prêts)": depenses_courantes, 
            "Mensualités Prêts": mensualites_annuelles, "Impôt sur le Revenu": impot_annuel, 
            "Reste à Vivre": reste_a_vivre
        })
        
        charges_courantes_df['Montant Annuel'] *= inflation_factor
        for idx, adulte in adultes_df_sim.iterrows():
             if annee < adulte['Année Départ Retraite'] and idx < len(sim_revenus):
                if 'salaire' in sim_revenus.loc[idx, 'Poste'].lower():
                    sim_revenus.loc[idx, 'Montant Annuel'] *= revalo_salaire_factor
    
    return pd.DataFrame(data), logs_evenements
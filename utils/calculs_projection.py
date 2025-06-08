# utils/calculs_projection.py (refactorisé)
import pandas as pd
from datetime import datetime
from .openfisca_utils import calculer_impot_openfisca
from .calculs import generer_tableau_amortissement, calculer_plus_value_immobiliere_fr

def _preparer_donnees_initiales(adultes_df, enfants_df, annee_actuelle):
    """Prépare les dataframes des adultes et enfants avec des colonnes calculées pour la simulation."""
    adultes_df_sim = adultes_df.copy()
    adultes_df_sim['Année Naissance'] = annee_actuelle - adultes_df_sim['Âge']
    
    enfants_df_sim = enfants_df.copy()
    if not enfants_df_sim.empty:
        enfants_df_sim['Année Naissance'] = annee_actuelle - enfants_df_sim['Âge']
        enfants_df_sim['Année Fin Études'] = enfants_df_sim['Année Naissance'] + enfants_df_sim['Âge Début Études'] + enfants_df_sim['Durée Études (ans)']
        
    return adultes_df_sim, enfants_df_sim

def _gerer_ventes_immobilieres(annee, ventes_df, sim_patrimoine, historique_achat, echeanciers, prets_df):
    """Gère la vente de biens immobiliers pour une année donnée."""
    cash_flow_exceptionnel = 0
    logs = []
    
    ventes_de_lannee = ventes_df[ventes_df['Année de Vente'] == annee]
    for _, vente in ventes_de_lannee.iterrows():
        nom_bien_vendu = vente['Bien à Vendre']
        if nom_bien_vendu not in sim_patrimoine['Actif'].values:
            continue

        idx_bien = sim_patrimoine[sim_patrimoine['Actif'] == nom_bien_vendu].index[0]
        prix_de_vente = sim_patrimoine.loc[idx_bien, 'Valeur Brute']
        donnees_achat = historique_achat.loc[historique_achat['Actif'] == nom_bien_vendu].iloc[0]
        
        impot_pv, _, details_pv = calculer_plus_value_immobiliere_fr(
            prix_achat=donnees_achat['Prix Achat Initial'], 
            prix_vente=prix_de_vente, 
            date_achat=pd.to_datetime(donnees_achat['Date Achat']), 
            date_vente=datetime(annee, 12, 31), 
            est_residence_principale="jouissance" in donnees_achat['Type']
        )

        crd_rembourse = 0
        prets_associes = prets_df[prets_df['Actif Associé'] == nom_bien_vendu]
        for id_pret in prets_associes.index:
            if id_pret in echeanciers and annee in echeanciers[id_pret].index:
                crd_rembourse += echeanciers[id_pret].loc[annee, 'CRD']
            echeanciers.pop(id_pret, None)
            
        cash_net = prix_de_vente - impot_pv - crd_rembourse
        cash_flow_exceptionnel += cash_net
        sim_patrimoine = sim_patrimoine.drop(idx_bien).reset_index(drop=True)
        
        logs.append(f"**{annee}**: Vente de '{nom_bien_vendu}' pour {prix_de_vente:,.0f}€. Cash net : **{cash_net:,.0f}€**. {details_pv}")
        
    return sim_patrimoine, cash_flow_exceptionnel, echeanciers, logs

def _calculer_flux_annuels(annee, adultes_df_sim, enfants_df_sim, sim_revenus, charges_courantes_df, hyp_retraite, salaires_de_base):
    """Calcule les revenus et dépenses courants pour une année donnée."""
    # Revenus
    adultes_details_list = []
    for idx, adulte in adultes_df_sim.iterrows():
        if annee >= adulte['Année Départ Retraite'] and idx < len(sim_revenus):
            sim_revenus.loc[idx, 'Montant Annuel'] = salaires_de_base.loc[idx, 'Montant Annuel'] * (hyp_retraite['taux_remplacement'] / 100)
        
        adultes_details_list.append({
            'revenu': sim_revenus.loc[idx, 'Montant Annuel'] if idx < len(sim_revenus) else 0,
            'annee_naissance': adulte['Année Naissance']
        })
    revenus_courants = sim_revenus['Montant Annuel'].sum()

    # Dépenses (y compris études)
    depenses_etudes = 0
    enfants_a_charge_details = []
    if not enfants_df_sim.empty:
        for _, enfant in enfants_df_sim.iterrows():
            age_enfant = annee - enfant['Année Naissance']
            if enfant['Âge Début Études'] <= age_enfant < (enfant['Âge Début Études'] + enfant['Durée Études (ans)']):
                depenses_etudes += enfant['Coût Annuel Études (€)']
            if annee < enfant['Année Fin Études']:
                enfants_a_charge_details.append(enfant.to_dict())
                
    depenses_courantes = charges_courantes_df['Montant Annuel'].sum() + depenses_etudes
    
    return revenus_courants, depenses_courantes, adultes_details_list, enfants_a_charge_details

def _calculer_paiements_prets_annuels(annee, echeanciers):
    """Calcule les mensualités et le passif total pour une année."""
    mensualites_annuelles, passif_total = 0, 0
    for idx, echeancier in echeanciers.items():
        if annee in echeancier.index:
            mensualites_annuelles += echeancier.loc[annee, 'Mensualité']
            passif_total += echeancier.loc[annee, 'CRD']
    return mensualites_annuelles, passif_total

def _mettre_a_jour_patrimoine(sim_patrimoine, reste_a_vivre, passif_total):
    """Applique l'évolution annuelle au patrimoine (rendement et injection du cash-flow)."""
    if not sim_patrimoine.empty:
        # Appliquer le rendement de chaque actif
        sim_patrimoine['Valeur Brute'] *= (1 + sim_patrimoine['Rendement %'] / 100)
        
        # Injecter le reste à vivre dans l'actif le plus liquide (ou par défaut)
        if 'Financier' in sim_patrimoine['Type'].values:
            # On privilégie l'injection dans le premier actif financier trouvé
            idx_financier = sim_patrimoine[sim_patrimoine['Type'] == 'Financier'].index[0]
            sim_patrimoine.loc[idx_financier, 'Valeur Brute'] += reste_a_vivre
        else:
            # Sinon, on l'ajoute au premier actif de la liste
            sim_patrimoine.iloc[0, sim_patrimoine.columns.get_loc('Valeur Brute')] += reste_a_vivre
        
        # Calcul des métriques de patrimoine
        valeur_immo_jouissance = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier de jouissance']['Valeur Brute'].sum()
        valeur_immo_productif = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier productif']['Valeur Brute'].sum()
        valeur_financier = sim_patrimoine[sim_patrimoine['Type'] == 'Financier']['Valeur Brute'].sum()
        
        actifs_totaux = sim_patrimoine['Valeur Brute'].sum()
        patrimoine_net = actifs_totaux - passif_total
    else:
        # Cas où il n'y a plus d'actifs (tout a été vendu)
        patrimoine_net = reste_a_vivre - passif_total
        actifs_totaux = max(0, reste_a_vivre)
        valeur_immo_jouissance, valeur_immo_productif, valeur_financier = 0, 0, actifs_totaux

    return patrimoine_net, actifs_totaux, valeur_financier, valeur_immo_jouissance, valeur_immo_productif, sim_patrimoine

def generer_projection_complete(duree, stocks_df, revenus_df, depenses_df, prets_df, adultes_df, enfants_df, hyp_retraite, hyp_economiques, est_parent_isole, ventes_df):
    """
    Fonction principale orchestrant la projection financière année par année.
    """
    annee_actuelle = datetime.now().year
    annees_projection = range(annee_actuelle, annee_actuelle + duree)
    
    # 1. Préparation initiale
    inflation_factor = 1 + hyp_economiques.get('inflation', 0.0) / 100
    revalo_salaire_factor = 1 + hyp_economiques.get('revalo_salaire', 0.0) / 100
    
    echeanciers = {idx: generer_tableau_amortissement(p['Montant Initial'], p['Taux Annuel %'], p['Durée Initiale (ans)'], pd.to_datetime(p['Date Début'])) for idx, p in prets_df.iterrows()}
    adultes_df_sim, enfants_df_sim = _preparer_donnees_initiales(adultes_df, enfants_df, annee_actuelle)
    
    sim_revenus = revenus_df.copy()
    sim_patrimoine = stocks_df.copy()
    charges_courantes_df = depenses_df.copy()
    historique_achat = stocks_df[['Actif', 'Prix Achat Initial', 'Date Achat', 'Type']].copy()
    salaires_de_base = sim_revenus[sim_revenus['Poste'].str.contains("salaire", case=False)].copy()

    projection_data, logs_evenements = [], []

    # 2. Boucle de simulation annuelle
    for annee in annees_projection:
        # 2a. Gérer les événements exceptionnels (ventes)
        sim_patrimoine, cash_flow_vente, echeanciers, logs_vente = _gerer_ventes_immobilieres(annee, ventes_df, sim_patrimoine, historique_achat, echeanciers, prets_df)
        logs_evenements.extend(logs_vente)
        
        # 2b. Calculer les flux financiers de l'année
        revenus, depenses, adultes_details, enfants_details = _calculer_flux_annuels(annee, adultes_df_sim, enfants_df_sim, sim_revenus, charges_courantes_df, hyp_retraite, salaires_de_base)
        mensualites_prets, passif_total = _calculer_paiements_prets_annuels(annee, echeanciers)
        
        # 2c. Calculer l'impôt
        foyer_pour_impot = {'revenus_imposables': revenus, 'adultes_details': adultes_details, 'enfants_details': enfants_details, 'est_parent_isole': est_parent_isole}
        impot_annuel = calculer_impot_openfisca(annee, foyer_pour_impot)
        
        # 2d. Calculer le cash-flow net (Reste à Vivre)
        reste_a_vivre = revenus - depenses - impot_annuel - mensualites_prets + cash_flow_vente
        
        # 2e. Mettre à jour le patrimoine avec le cash-flow et les rendements
        pat_net, act_tot, val_fin, val_immo_j, val_immo_p, sim_patrimoine = _mettre_a_jour_patrimoine(sim_patrimoine, reste_a_vivre, passif_total)

        # 2f. Enregistrer les résultats de l'année
        projection_data.append({
            "Année": annee, "Patrimoine Net": pat_net, "Actifs Totaux": act_tot, "Passifs Totaux": passif_total,
            "Patrimoine Financier": val_fin, "Immobilier Jouissance": val_immo_j, "Immobilier Productif": val_immo_p,
            "Revenu Annuel": revenus, "Charges (hors prêts)": depenses, 
            "Mensualités Prêts": mensualites_prets, "Impôt sur le Revenu": impot_annuel, "Reste à Vivre": reste_a_vivre
        })
        
        # 2g. Préparer l'année suivante (inflation, revalorisation)
        charges_courantes_df['Montant Annuel'] *= inflation_factor
        for idx, row in sim_revenus.iterrows():
            if 'salaire' in row['Poste'].lower() and annee < adultes_df_sim.loc[idx, 'Année Départ Retraite']:
                 sim_revenus.loc[idx, 'Montant Annuel'] *= revalo_salaire_factor
    
    return pd.DataFrame(projection_data), logs_evenements
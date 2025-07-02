# utils/calculs_projection.py (refactorisé et corrigé)
import pandas as pd
from datetime import datetime
from .openfisca_utils import calculer_impot_openfisca
from .calculs import generer_tableau_amortissement, calculer_plus_value_immobiliere_fr

# Taux pour les dispositifs Pinel
PINEL_RATES = {
    "Pinel Classique (avant 2023)": {6: 0.12, 9: 0.18, 12: 0.21},
    "Pinel Classique (2023)": {6: 0.105, 9: 0.15, 12: 0.175},
    "Pinel Classique (2024)": {6: 0.09, 9: 0.12, 12: 0.14},
    "Pinel + (2023-2024)": {6: 0.12, 9: 0.18, 12: 0.21},
}

def _preparer_donnees_initiales(adultes_df, enfants_df, annee_actuelle):
    """Prépare les dataframes des adultes et enfants avec des colonnes calculées pour la simulation."""
    adultes_df_sim = adultes_df.copy()
    if 'Âge' in adultes_df_sim.columns:
        adultes_df_sim['Année Naissance'] = (annee_actuelle - pd.to_numeric(adultes_df_sim['Âge'], errors='coerce')).astype('Int64')
    else:
        adultes_df_sim['Année Naissance'] = pd.NA

    enfants_df_sim = enfants_df.copy()
    if not enfants_df_sim.empty:
        if 'Âge' in enfants_df_sim.columns and 'Âge Début Études' in enfants_df_sim.columns and 'Durée Études (ans)' in enfants_df_sim.columns:
            enfants_df_sim['Année Naissance'] = (annee_actuelle - pd.to_numeric(enfants_df_sim['Âge'], errors='coerce')).astype('Int64')
            enfants_df_sim['Année Fin Études'] = (enfants_df_sim['Année Naissance'].astype('float') + pd.to_numeric(enfants_df_sim['Âge Début Études'], errors='coerce') + pd.to_numeric(enfants_df_sim['Durée Études (ans)'], errors='coerce')).astype('Int64')
        else:
            enfants_df_sim['Année Naissance'] = pd.NA
            enfants_df_sim['Année Fin Études'] = pd.NA
        
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

def _calculer_revenus_et_statuts_adultes(annee, adultes_df_sim, sim_revenus, df_pension_hypotheses, indices_salaires):
    """
    Calcule les revenus (salaires, pensions) et détermine le statut de chaque adulte pour une année donnée.
    """
    salaires_annuels = 0
    pensions_annuelles = 0
    adultes_details_list = []
    statuts_adultes = {}

    for i, (_, adulte) in enumerate(adultes_df_sim.iterrows()):
        nom_adulte = adulte['Prénom']
        revenu_adulte_annee = 0
        statut_adulte = "Actif"

        est_retraite = False
        if not df_pension_hypotheses.empty:
            hypothese_retraite = df_pension_hypotheses[
                (df_pension_hypotheses['Prénom Adulte'] == nom_adulte) &
                (df_pension_hypotheses['Active'] == True) &
                (pd.notna(df_pension_hypotheses['Année Départ Retraite'])) &
                (df_pension_hypotheses['Année Départ Retraite'] <= annee)
            ]
            if not hypothese_retraite.empty:
                est_retraite = True
                pension = hypothese_retraite.iloc[0]['Montant Pension Annuelle (€)']
                revenu_adulte_annee = pension
                pensions_annuelles += pension
                statut_adulte = "Retraité"

        if not est_retraite:
            if i < len(indices_salaires):
                idx_salaire = indices_salaires[i]
                salaire = sim_revenus.loc[idx_salaire, 'Montant Annuel']
                revenu_adulte_annee = salaire
                salaires_annuels += salaire
        
        statuts_adultes[nom_adulte] = statut_adulte
        adultes_details_list.append({
            'revenu': revenu_adulte_annee,
            'annee_naissance': adulte['Année Naissance']
        })
        
    return salaires_annuels, pensions_annuelles, adultes_details_list, statuts_adultes

def _calculer_depenses_et_statuts_enfants(annee, enfants_df_sim):
    """
    Calcule les dépenses d'études et détermine le statut de chaque enfant pour une année donnée.
    """
    depenses_etudes = 0
    enfants_a_charge_details = []
    statuts_enfants = {}

    if not enfants_df_sim.empty:
        for _, enfant in enfants_df_sim.iterrows():
            nom_enfant = enfant['Prénom']
            age_enfant = annee - enfant['Année Naissance']
            statut_enfant = "Scolarisé"

            est_etudiant = enfant['Âge Début Études'] <= age_enfant < (enfant['Âge Début Études'] + enfant['Durée Études (ans)'])
            a_fini_etudes = age_enfant >= (enfant['Âge Début Études'] + enfant['Durée Études (ans)'])

            if est_etudiant:
                statut_enfant = "Étudiant"
                depenses_etudes += enfant['Coût Annuel Études (€)']
            elif a_fini_etudes:
                statut_enfant = "Fin d'études"
            
            statuts_enfants[nom_enfant] = statut_enfant

            if annee < enfant['Année Fin Études']:
                enfants_a_charge_details.append(enfant.to_dict())
    
    return depenses_etudes, enfants_a_charge_details, statuts_enfants

def _calculer_autres_flux(sim_revenus, charges_courantes_df):
    """
    Calcule les revenus non liés aux personnes (locatifs, autres) et les charges courantes.
    """
    loyers_locatifs = sim_revenus[sim_revenus['Poste'] == 'Revenus Locatifs (calculé)']['Montant Annuel'].sum()
    
    autres_revenus = sim_revenus[
        (~sim_revenus['Poste'].str.contains('Salaire', na=False)) &
        (sim_revenus['Poste'] != 'Revenus Locatifs (calculé)')
    ]['Montant Annuel'].sum()
    
    charges_courantes = charges_courantes_df['Montant Annuel'].sum()
    
    return loyers_locatifs, autres_revenus, charges_courantes

def _calculer_flux_annuels(annee, adultes_df_sim, enfants_df_sim, sim_revenus, charges_courantes_df, df_pension_hypotheses, indices_salaires):
    """
    Orchestre le calcul des revenus et dépenses pour une année.
    """
    salaires, pensions, adultes_details, statuts_adultes = _calculer_revenus_et_statuts_adultes(
        annee, adultes_df_sim, sim_revenus, df_pension_hypotheses, indices_salaires
    )
    depenses_etudes, enfants_details, statuts_enfants = _calculer_depenses_et_statuts_enfants(
        annee, enfants_df_sim
    )
    loyers, autres_revs, charges_base = _calculer_autres_flux(
        sim_revenus, charges_courantes_df
    )
    total_revenus = salaires + pensions + loyers + autres_revs
    total_depenses = charges_base + depenses_etudes
    statuts_annee = {**statuts_adultes, **statuts_enfants}

    return {
        "total_revenus": total_revenus,
        "salaires": salaires,
        "pensions": pensions,
        "loyers_locatifs": loyers,
        "autres_revenus": autres_revs,
        "total_depenses": total_depenses,
        "adultes_details": adultes_details,
        "enfants_details": enfants_details,
        "statuts_annee": statuts_annee
    }

def _calculer_paiements_prets_annuels(annee, echeanciers, prets_df, asset_to_type_map):
    """Calcule les mensualités et le passif total pour une année, ventilé par type d'actif."""
    mensualites_annuelles = 0
    passif_total = 0
    passif_jouissance = 0
    passif_productif = 0

    for idx, echeancier in echeanciers.items():
        if not echeancier.empty and annee in echeancier.index:
            if 'Mensualités Annuelles' in echeancier.columns:
                mensualites_annuelles += echeancier.loc[annee, 'Mensualités Annuelles']
            
            crd = echeancier.loc[annee, 'CRD']
            passif_total += crd

            actif_associe = prets_df.loc[idx, 'Actif Associé']
            if actif_associe in asset_to_type_map:
                asset_type = asset_to_type_map[actif_associe]
                if 'jouissance' in asset_type:
                    passif_jouissance += crd
                elif 'productif' in asset_type:
                    passif_productif += crd

    return mensualites_annuelles, passif_total, passif_jouissance, passif_productif

def _mettre_a_jour_patrimoine(sim_patrimoine, reste_a_vivre, passif_total):
    """Applique l'évolution annuelle au patrimoine (rendement et injection du cash-flow)."""
    if not sim_patrimoine.empty:
        sim_patrimoine['Valeur Brute'] *= (1 + sim_patrimoine['Rendement %'] / 100)
        
        if 'Financier' in sim_patrimoine['Type'].values:
            idx_financier = sim_patrimoine[sim_patrimoine['Type'] == 'Financier'].index[0]
            sim_patrimoine.loc[idx_financier, 'Valeur Brute'] += reste_a_vivre
        else:
            sim_patrimoine.iloc[0, sim_patrimoine.columns.get_loc('Valeur Brute')] += reste_a_vivre
        
        valeur_immo_jouissance_gross = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier de jouissance']['Valeur Brute'].sum()
        valeur_immo_productif_gross = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier productif']['Valeur Brute'].sum()
        valeur_financier_gross = sim_patrimoine[sim_patrimoine['Type'] == 'Financier']['Valeur Brute'].sum()
        
        actifs_totaux = sim_patrimoine['Valeur Brute'].sum()
        patrimoine_net = actifs_totaux - passif_total
    else:
        patrimoine_net = reste_a_vivre - passif_total
        actifs_totaux = max(0, reste_a_vivre)
        valeur_immo_jouissance_gross, valeur_immo_productif_gross, valeur_financier_gross = 0, 0, actifs_totaux

    return patrimoine_net, actifs_totaux, valeur_financier_gross, valeur_immo_jouissance_gross, valeur_immo_productif_gross, sim_patrimoine

def generer_projection_complete(duree, stocks_df, revenus_df, depenses_df, prets_df, adultes_df, enfants_df, df_pension_hypotheses, hyp_economiques, est_parent_isole, ventes_df):
    """
    Fonction principale orchestrant la projection financière année par année.
    """
    annee_actuelle = datetime.now().year
    annees_projection = range(annee_actuelle, annee_actuelle + duree)
    
    inflation_factor = 1 + hyp_economiques.get('inflation', 0.0) / 100
    revalo_salaire_factor = 1 + hyp_economiques.get('revalo_salaire', 0.0) / 100
    
    asset_to_type_map = pd.Series(stocks_df.Type.values, index=stocks_df.Actif).to_dict()

    reductions_fiscales_actives = []
    df_immo_productif_defisc = stocks_df[
        (stocks_df['Type'] == 'Immobilier productif') &
        (stocks_df['Dispositif Fiscal'].notna()) &
        (stocks_df['Dispositif Fiscal'] != '') &
        (stocks_df['Dispositif Fiscal'] != 'Aucun') &
        (pd.to_numeric(stocks_df['Durée Défiscalisation (ans)'], errors='coerce').fillna(0) > 0)
    ].copy()

    for _, bien in df_immo_productif_defisc.iterrows():
        dispositif = bien['Dispositif Fiscal']
        duree_defisc = int(bien['Durée Défiscalisation (ans)'])
        prix_achat = bien['Prix Achat Initial']
        date_achat = pd.to_datetime(bien['Date Achat'])
        
        reduction_annuelle = 0.0
        if pd.notna(date_achat):
            annee_debut, annee_fin = date_achat.year, date_achat.year + duree_defisc - 1
            if "Pinel" in str(dispositif) and dispositif in PINEL_RATES and duree_defisc in PINEL_RATES[dispositif]:
                taux_total = PINEL_RATES[dispositif][duree_defisc]
                reduction_annuelle = (min(prix_achat, 300000) * taux_total) / duree_defisc
            
            if reduction_annuelle > 0:
                reductions_fiscales_actives.append({'nom_bien': bien['Actif'], 'reduction_annuelle': reduction_annuelle, 'annee_debut': annee_debut, 'annee_fin': annee_fin})

    echeanciers = {idx: generer_tableau_amortissement(p['Montant Initial'], p['Taux Annuel %'], p['Durée Initiale (ans)'], pd.to_datetime(p['Date Début']), p.get('Assurance Emprunteur %', 0)) for idx, p in prets_df.iterrows()}
    
    adultes_df_sim, enfants_df_sim = _preparer_donnees_initiales(adultes_df, enfants_df, annee_actuelle)
    sim_revenus_base, sim_patrimoine, charges_courantes_df = revenus_df.copy(), stocks_df.copy(), depenses_df.copy()
    historique_achat = stocks_df[['Actif', 'Prix Achat Initial', 'Date Achat', 'Type']].copy()
    
    projection_data, logs_evenements = [], []

    for annee in annees_projection:
        sim_patrimoine, cash_flow_vente, echeanciers, logs_vente = _gerer_ventes_immobilieres(annee, ventes_df, sim_patrimoine, historique_achat, echeanciers, prets_df)
        logs_evenements.extend(logs_vente)
        
        # Calculer les charges immobilières pour l'année en cours sur les biens restants
        charges_immo_annuelles = 0
        if 'Charges Annuelles (€)' in sim_patrimoine.columns:
            charges_immo_annuelles += pd.to_numeric(sim_patrimoine['Charges Annuelles (€)'], errors='coerce').fillna(0).sum()
        if 'Taxe Foncière Annuelle (€)' in sim_patrimoine.columns:
            charges_immo_annuelles += pd.to_numeric(sim_patrimoine['Taxe Foncière Annuelle (€)'], errors='coerce').fillna(0).sum()

        sim_revenus_annee = sim_revenus_base.copy()
        
        df_immobilier_productif_actuel = sim_patrimoine[sim_patrimoine['Type'] == 'Immobilier productif']
        total_loyers_annuels_actuel = 0
        if not df_immobilier_productif_actuel.empty and 'Loyer Mensuel Brut (€)' in df_immobilier_productif_actuel.columns:
            total_loyers_annuels_actuel = (pd.to_numeric(df_immobilier_productif_actuel['Loyer Mensuel Brut (€)'], errors='coerce').fillna(0) * 12).sum()

        if total_loyers_annuels_actuel > 0:
            ligne_loyers = pd.DataFrame([{'Poste': 'Revenus Locatifs (calculé)', 'Montant Annuel': total_loyers_annuels_actuel}])
            sim_revenus_annee = pd.concat([sim_revenus_annee, ligne_loyers], ignore_index=True)
        
        indices_salaires_annee = sim_revenus_annee[sim_revenus_annee['Poste'].str.contains('Salaire', na=False)].index.tolist()
        
        flux = _calculer_flux_annuels(annee, adultes_df_sim, enfants_df_sim, sim_revenus_annee, charges_courantes_df, df_pension_hypotheses, indices_salaires_annee)
        
        mensualites_prets, passif_total, passif_jouissance, passif_productif = _calculer_paiements_prets_annuels(annee, echeanciers, prets_df, asset_to_type_map)
        
        foyer_pour_impot = {'revenus_imposables': flux["total_revenus"], 'adultes_details': flux["adultes_details"], 'enfants_details': flux["enfants_details"], 'est_parent_isole': est_parent_isole}
        impot_annuel_avant_reduction = calculer_impot_openfisca(annee, foyer_pour_impot)
        
        total_reduction_fiscale_annee = sum(red['reduction_annuelle'] for red in reductions_fiscales_actives if red['annee_debut'] <= annee <= red['annee_fin'])
        impot_annuel_final = max(0, impot_annuel_avant_reduction - total_reduction_fiscale_annee)
        
        total_depenses_annee = flux["total_depenses"] + charges_immo_annuelles
        reste_a_vivre = flux["total_revenus"] - total_depenses_annee - impot_annuel_final - mensualites_prets + cash_flow_vente
        
        pat_net, act_tot, val_fin_gross, val_immo_j_gross, val_immo_p_gross, sim_patrimoine = _mettre_a_jour_patrimoine(sim_patrimoine, reste_a_vivre, passif_total)

        donnees_annee = {
            "Année": annee, "Patrimoine Net": pat_net, "Actifs Totaux": act_tot, "Passifs Totaux": passif_total,
            "Patrimoine Financier": val_fin_gross, "Immobilier Jouissance": val_immo_j_gross, "Immobilier Productif": val_immo_p_gross,
            "Patrimoine Financier Net": val_fin_gross, "Immobilier Jouissance Net": val_immo_j_gross - passif_jouissance, "Immobilier Productif Net": val_immo_p_gross - passif_productif,
            "Revenu Annuel": flux["total_revenus"], "Charges (hors prêts)": total_depenses_annee,
            "Mensualités Prêts": mensualites_prets, "Impôt sur le Revenu": impot_annuel_final, 
            "Réduction Fiscale Annuelle": total_reduction_fiscale_annee, "Reste à Vivre": reste_a_vivre,
            "Cash-flow Vente": cash_flow_vente,
            **{f"{membre}_Statut": statut for membre, statut in flux["statuts_annee"].items()},
            "Salaires Annuels": flux["salaires"], "Pensions Annuelles": flux["pensions"],
            "Revenus Locatifs Annuels": flux["loyers_locatifs"], "Autres Revenus Annuels": flux["autres_revenus"]
        }
        projection_data.append(donnees_annee)

        charges_courantes_df['Montant Annuel'] *= inflation_factor
        sim_revenus_base.loc[~sim_revenus_base['Poste'].str.contains('Salaire', na=False), 'Montant Annuel'] *= inflation_factor
        
        # Appliquer l'inflation aux charges immobilières dans le dataframe du patrimoine
        if 'Charges Annuelles (€)' in sim_patrimoine.columns:
            sim_patrimoine['Charges Annuelles (€)'] *= inflation_factor
        if 'Taxe Foncière Annuelle (€)' in sim_patrimoine.columns:
            sim_patrimoine['Taxe Foncière Annuelle (€)'] *= inflation_factor
        
        for i, (_, adulte_sim) in enumerate(adultes_df_sim.iterrows()):
            est_retraite_annee_suivante = False
            if not df_pension_hypotheses.empty:
                if not df_pension_hypotheses[(df_pension_hypotheses['Prénom Adulte'] == adulte_sim['Prénom']) & (df_pension_hypotheses['Active'] == True) & (df_pension_hypotheses['Année Départ Retraite'] <= annee + 1)].empty:
                    est_retraite_annee_suivante = True
            
            indices_salaires_base = sim_revenus_base[sim_revenus_base['Poste'].str.contains('Salaire', na=False)].index.tolist()
            if i < len(indices_salaires_base):
                idx_salaire = indices_salaires_base[i]
                sim_revenus_base.loc[idx_salaire, 'Montant Annuel'] = 0 if est_retraite_annee_suivante else sim_revenus_base.loc[idx_salaire, 'Montant Annuel'] * revalo_salaire_factor

    return pd.DataFrame(projection_data), logs_evenements
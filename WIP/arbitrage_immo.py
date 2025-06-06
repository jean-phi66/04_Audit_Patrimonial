import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime, timedelta
import copy # Pour deepcopy

# Configuration de la page Streamlit
st.set_page_config(layout="wide", page_title="Projection Patrimoniale")

st.title("📊 Simulateur d'Évolution Patrimoniale")
st.caption("Une application pour projeter le patrimoine et les flux financiers de vos clients.")

# --- Fonctions de Calcul (inchangées) ---

def calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees):
    """Calcule la mensualité d'un prêt."""
    if duree_annees == 0: 
        return 0
    if taux_annuel_pourcentage == 0:
        if duree_annees * 12 == 0: return 0 
        return montant_emprunte / (duree_annees * 12)
    taux_mensuel = (taux_annuel_pourcentage / 100) / 12
    nombre_mensualites = duree_annees * 12
    if nombre_mensualites == 0:
        return 0
    if montant_emprunte == 0:
        return 0
    try:
        mensualite = montant_emprunte * (taux_mensuel * (1 + taux_mensuel)**nombre_mensualites) / ((1 + taux_mensuel)**nombre_mensualites - 1)
        if np.isnan(mensualite) or np.isinf(mensualite):
             if taux_mensuel == 0:
                 return montant_emprunte / nombre_mensualites if nombre_mensualites > 0 else 0
             return 0 
    except OverflowError: 
        if taux_mensuel > 0:
            return montant_emprunte * taux_mensuel 
        return 0 
    except ZeroDivisionError: 
         return montant_emprunte / nombre_mensualites if nombre_mensualites > 0 else 0
    return mensualite

def generer_tableau_amortissement(montant_emprunte, taux_annuel_pourcentage, duree_annees, date_debut_pret):
    """Génère un tableau d'amortissement annuel simplifié."""
    if duree_annees <= 0 or montant_emprunte <= 0:
        return pd.DataFrame(columns=['Année', 'Mensualité Totale Annuelle', 'Intérêts Annuels', 'Capital Remboursé Annuel', 'Capital Restant Dû'])

    mensualite = calculer_mensualite_pret(montant_emprunte, taux_annuel_pourcentage, duree_annees)
    if mensualite == 0 and montant_emprunte > 0 : 
        # st.warning(f"Calcul de mensualité impossible pour un prêt de {montant_emprunte}€, taux {taux_annuel_pourcentage}%, durée {duree_annees} ans. Le tableau d'amortissement sera vide.")
        return pd.DataFrame(columns=['Année', 'Mensualité Totale Annuelle', 'Intérêts Annuels', 'Capital Remboursé Annuel', 'Capital Restant Dû'])

    nombre_mensualites_total = int(round(duree_annees * 12))
    if nombre_mensualites_total == 0: # Ajout pour éviter boucle infinie si 0 mensualités
        return pd.DataFrame(columns=['Année', 'Mensualité Totale Annuelle', 'Intérêts Annuels', 'Capital Remboursé Annuel', 'Capital Restant Dû'])

    capital_restant_du = montant_emprunte
    amortissement_annuel = []
    
    for annee_idx in range(int(np.ceil(duree_annees)) + 2): # +2 pour marge
        annee_civile_traitement = date_debut_pret.year + annee_idx
        
        interet_annuel_courant = 0
        capital_rembourse_annuel_courant = 0
        mensualite_annuelle_courante = 0
        nb_mois_payes_cette_annee_civile = 0

        start_month_for_loop = date_debut_pret.month if annee_idx == 0 else 1
        
        for mois_dans_annee_civile in range(start_month_for_loop, 13): 
            mois_ecoules_depuis_debut_pret = annee_idx * 12 + (mois_dans_annee_civile -1)
            if annee_idx == 0:
                 mois_ecoules_depuis_debut_pret = mois_dans_annee_civile - date_debut_pret.month

            num_paiement_global = mois_ecoules_depuis_debut_pret +1

            if num_paiement_global > nombre_mensualites_total or capital_restant_du < 0.01:
                break

            nb_mois_payes_cette_annee_civile +=1
            interet_mois = capital_restant_du * (taux_annuel_pourcentage / 100 / 12)
            
            if num_paiement_global == nombre_mensualites_total or (capital_restant_du - (mensualite - interet_mois) < 0.01 and capital_restant_du > 0) : 
                capital_rembourse_mois = capital_restant_du
                mensualite_effective = capital_rembourse_mois + interet_mois
            else:
                capital_rembourse_mois = mensualite - interet_mois
                mensualite_effective = mensualite
            
            if capital_rembourse_mois > capital_restant_du :
                capital_rembourse_mois = capital_restant_du
                mensualite_effective = capital_rembourse_mois + interet_mois

            capital_restant_du -= capital_rembourse_mois
            interet_annuel_courant += interet_mois
            capital_rembourse_annuel_courant += capital_rembourse_mois
            mensualite_annuelle_courante += mensualite_effective
        
        if nb_mois_payes_cette_annee_civile > 0:
            amortissement_annuel.append({
                'Année': annee_civile_traitement,
                'Mensualité Totale Annuelle': mensualite_annuelle_courante,
                'Intérêts Annuels': interet_annuel_courant,
                'Capital Remboursé Annuel': capital_rembourse_annuel_courant,
                'Capital Restant Dû': max(0, capital_restant_du) 
            })
        
        if capital_restant_du < 0.01:
            break
            
    df_amort = pd.DataFrame(amortissement_annuel)
    if not df_amort.empty:
        premiere_annee_crd_zero_idx = df_amort[df_amort['Capital Restant Dû'] == 0].index.min()
        if pd.notna(premiere_annee_crd_zero_idx):
            df_amort = df_amort.loc[:premiere_annee_crd_zero_idx]
    return df_amort


def calculer_plus_value_immobiliere_fr(prix_achat, frais_acquisition_reels, cout_travaux, prix_vente, date_achat, date_vente, est_residence_principale=False):
    if est_residence_principale:
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, "Résidence principale (exonérée)"
    frais_acquisition_forfaitaires = prix_achat * 0.075 
    frais_acquisition_retenus = max(frais_acquisition_reels, frais_acquisition_forfaitaires)
    prix_revient = prix_achat + frais_acquisition_retenus + cout_travaux
    plus_value_brute = prix_vente - prix_revient
    if plus_value_brute <= 0:
        return plus_value_brute, 0, 0, 0, 0, 0, 0, 0, 0, "Pas de plus-value brute"
    duree_detention = (date_vente - date_achat).days / 365.25
    abattement_ir_taux = 0
    if duree_detention > 5:
        for annee_revolue in range(6, int(np.floor(duree_detention)) + 1):
            if annee_revolue <= 21: abattement_ir_taux += 0.06
            elif annee_revolue == 22: abattement_ir_taux += 0.04
    if duree_detention >= 22: abattement_ir_taux = 1.0 
    abattement_ps_taux = 0
    if duree_detention > 5:
        for annee_revolue in range(6, int(np.floor(duree_detention)) + 1):
            if annee_revolue <= 21: abattement_ps_taux += 0.0165
            elif annee_revolue == 22: abattement_ps_taux += 0.0160
            elif annee_revolue > 22 and annee_revolue <=30 : abattement_ps_taux += 0.09
    if duree_detention >= 30: abattement_ps_taux = 1.0 
    abattement_ir = plus_value_brute * min(abattement_ir_taux, 1.0)
    abattement_ps = plus_value_brute * min(abattement_ps_taux, 1.0)
    plus_value_imposable_ir = max(0, plus_value_brute - abattement_ir)
    plus_value_imposable_ps = max(0, plus_value_brute - abattement_ps)
    taux_ir = 0.19; taux_ps = 0.172
    impot_ir = plus_value_imposable_ir * taux_ir
    impot_ps = plus_value_imposable_ps * taux_ps
    surtaxe = 0
    pv_imposable_avant_surtaxe = plus_value_imposable_ir
    if pv_imposable_avant_surtaxe > 50000:
        if pv_imposable_avant_surtaxe <= 60000: surtaxe = pv_imposable_avant_surtaxe * 0.02 - 1000
        elif pv_imposable_avant_surtaxe <= 100000: surtaxe = (pv_imposable_avant_surtaxe * 0.02)
        elif pv_imposable_avant_surtaxe <= 110000: surtaxe = pv_imposable_avant_surtaxe * 0.03 - 1000
        elif pv_imposable_avant_surtaxe <= 150000: surtaxe = (pv_imposable_avant_surtaxe * 0.03)
        elif pv_imposable_avant_surtaxe <= 160000: surtaxe = pv_imposable_avant_surtaxe * 0.04 - 1500
        elif pv_imposable_avant_surtaxe <= 200000: surtaxe = (pv_imposable_avant_surtaxe * 0.04)
        elif pv_imposable_avant_surtaxe <= 210000: surtaxe = pv_imposable_avant_surtaxe * 0.05 - 2000
        elif pv_imposable_avant_surtaxe <= 250000: surtaxe = (pv_imposable_avant_surtaxe * 0.05)
        elif pv_imposable_avant_surtaxe <= 260000: surtaxe = pv_imposable_avant_surtaxe * 0.06 - 2500
        else: surtaxe = (pv_imposable_avant_surtaxe * 0.06)
        surtaxe = max(0, surtaxe) 
    impot_total = impot_ir + impot_ps + surtaxe
    details = (f"Durée détention: {duree_detention:.2f} ans. PV Brute: {plus_value_brute:,.0f}€. Abatt. IR ({abattement_ir_taux*100:.1f}%): {abattement_ir:,.0f}€. Abatt. PS ({abattement_ps_taux*100:.1f}%): {abattement_ps:,.0f}€. PV IR Nette: {plus_value_imposable_ir:,.0f}€. PV PS Nette: {plus_value_imposable_ps:,.0f}€. Surtaxe: {surtaxe:,.0f}€.")
    return plus_value_brute, abattement_ir, abattement_ps, plus_value_imposable_ir, plus_value_imposable_ps, impot_ir, impot_ps, surtaxe, impot_total, details

# --- Initialisation Session State ---
if 'biens_immo' not in st.session_state: st.session_state.biens_immo = []
if 'prets_immo' not in st.session_state: st.session_state.prets_immo = []
if 'projection_calculée' not in st.session_state: st.session_state.projection_calculée = False
if 'df_projection' not in st.session_state: st.session_state.df_projection = None
if 'biens_immo_projection_fin' not in st.session_state: st.session_state.biens_immo_projection_fin = []
if 'prets_projection_fin' not in st.session_state: st.session_state.prets_projection_fin = []
if 'df_projection_simulee' not in st.session_state: st.session_state.df_projection_simulee = None # Pour stocker la projection après vente

# --- Clés pour widgets (pour éviter les duplications si on déplace des éléments) ---
# Informations Client
key_age_actuel="age_actuel_input"
key_horizon_projection="horizon_projection_input"
key_annee_depart_projection="annee_depart_projection_input"
# Patrimoine Initial
key_patrimoine_financier_initial="patrimoine_financier_initial_input"
key_taux_rendement_placements_annuel="taux_rendement_placements_annuel_input"
# Biens Immobiliers Form
key_nom_bien="nom_bien_input"
key_valeur_actuelle_bien="valeur_actuelle_bien_input"
key_prix_achat_bien="prix_achat_bien_input"
key_frais_acquisition_reels_bien="frais_acquisition_reels_bien_input"
key_cout_travaux_bien="cout_travaux_bien_input"
key_date_achat_bien="date_achat_bien_input"
key_taux_valorisation_annuel_bien="taux_valorisation_annuel_bien_input"
key_loyer_annuel_brut_bien="loyer_annuel_brut_bien_input"
key_charges_annuelles_bien="charges_annuelles_bien_input"
key_est_residence_principale_bien="est_residence_principale_bien_input"
# Prêts Immobiliers Form
key_nom_pret="nom_pret_input"
key_montant_initial_pret="montant_initial_pret_input"
key_taux_interet_annuel_pret="taux_interet_annuel_pret_input"
key_duree_initiale_pret_annees="duree_initiale_pret_annees_input"
key_date_debut_pret="date_debut_pret_input"
key_bien_associe_id_pret="bien_associe_id_pret_input"
# Revenus Annuels
key_revenu_net_annuel_initial="revenu_net_annuel_initial_input"
key_taux_evolution_revenu_annuel="taux_evolution_revenu_annuel_input"
# Dépenses Annuelles
key_depenses_annuelles_initiales="depenses_annuelles_initiales_input"
key_taux_inflation_depenses_annuel="taux_inflation_depenses_annuel_input"
# Simulation Vente (dans tab_config)
key_sb_bien_vente_sim_config="sb_bien_vente_sim_config_input"
key_sb_annee_vente_sim_config="sb_annee_vente_sim_config_input"
key_sim_vente_btn_exec_config="sim_vente_btn_exec_config_input"


# --- Définition des Onglets ---
tab_config, tab_synthese, tab_details_proj, tab_details_prets, tab_details_biens, tab_sim_vente_resultats = st.tabs([
    "⚙️ Configuration & Entrées", "📈 Synthèse Graphique", "📊 Tableau de Projection", 
    "💸 Détail des Prêts", "🏡 Détail des Biens", "simulation de vente (Résultats)" # Renommé pour clarté
])

with tab_config:
    st.header("👤 Informations Client")
    age_actuel = st.number_input("Âge actuel du client", min_value=18, max_value=100, value=st.session_state.get(key_age_actuel, 35), step=1, key=key_age_actuel)
    horizon_projection = st.number_input("Horizon de projection (années)", min_value=1, max_value=50, value=st.session_state.get(key_horizon_projection, 20), step=1, key=key_horizon_projection)
    annee_depart_projection = st.number_input("Année de départ de la projection", value=st.session_state.get(key_annee_depart_projection, datetime.now().year), format="%d", min_value=1900, max_value=2200, key=key_annee_depart_projection)

    st.header("💰 Patrimoine Initial")
    patrimoine_financier_initial = st.number_input("Liquidités et Placements financiers (€)", min_value=0.0, value=st.session_state.get(key_patrimoine_financier_initial, 50000.0), step=1000.0, key=key_patrimoine_financier_initial)
    taux_rendement_placements_annuel = st.slider("Taux de rendement annuel net des placements (%)", 0.0, 15.0, st.session_state.get(key_taux_rendement_placements_annuel, 2.0), 0.1, format="%.1f%%", key=key_taux_rendement_placements_annuel)

    st.subheader("🏡 Biens Immobiliers")
    with st.form("bien_immo_form", clear_on_submit=True):
        nom_bien = st.text_input("Nom du bien (ex: Résidence Principale)", key=key_nom_bien)
        valeur_actuelle_bien = st.number_input("Valeur actuelle du bien (€)", min_value=0.0, value=200000.0, step=10000.0, key=key_valeur_actuelle_bien)
        prix_achat_bien = st.number_input("Prix d'achat initial du bien (€)", min_value=0.0, value=150000.0, step=10000.0, key=key_prix_achat_bien)
        frais_acquisition_reels_bien = st.number_input("Frais d'acquisition réels (€)", min_value=0.0, value=0.0, step=100.0, key=key_frais_acquisition_reels_bien)
        cout_travaux_bien = st.number_input("Coût des travaux déductibles (€)", min_value=0.0, value=0.0, step=1000.0, key=key_cout_travaux_bien)
        date_achat_bien = st.date_input("Date d'achat du bien", value=datetime(2010, 1, 1), min_value=datetime(1900,1,1), max_value=datetime.today(), key=key_date_achat_bien)
        taux_valorisation_annuel_bien = st.slider("Taux de valorisation annuel du bien (%)", -5.0, 10.0, 1.5, 0.1, format="%.1f%%", key=key_taux_valorisation_annuel_bien)
        loyer_annuel_brut_bien = st.number_input("Loyer annuel brut (si locatif) (€)", min_value=0.0, value=0.0, step=100.0, key=key_loyer_annuel_brut_bien)
        charges_annuelles_bien = st.number_input("Charges annuelles déductibles (si locatif) (€)", min_value=0.0, value=0.0, step=100.0, key=key_charges_annuelles_bien)
        est_residence_principale_bien = st.checkbox("Est-ce la résidence principale ?", value=False, key=key_est_residence_principale_bien)
        
        submitted_bien = st.form_submit_button("➕ Ajouter Bien Immobilier")
        if submitted_bien and nom_bien:
            st.session_state.biens_immo.append({
                "id": f"bien_{len(st.session_state.biens_immo)+1}_{int(datetime.now().timestamp())}",
                "nom": nom_bien, "valeur_actuelle": valeur_actuelle_bien, "prix_achat": prix_achat_bien,
                "frais_acquisition_reels": frais_acquisition_reels_bien, "cout_travaux": cout_travaux_bien,
                "date_achat": date_achat_bien, "taux_valorisation_annuel": taux_valorisation_annuel_bien / 100,
                "loyer_annuel_brut": loyer_annuel_brut_bien, "charges_annuelles": charges_annuelles_bien,
                "est_residence_principale": est_residence_principale_bien, "pret_associe_id": None 
            })
            st.success(f"Bien '{nom_bien}' ajouté !")
            st.rerun() 

    if st.session_state.biens_immo:
        st.subheader("Biens existants:")
        for i, bien in enumerate(st.session_state.biens_immo):
            col1_bien, col2_bien = st.columns([0.8, 0.2])
            col1_bien.write(f"- {bien['nom']} (Valeur: {bien['valeur_actuelle']:,.0f} €)")
            if col2_bien.button(f"Suppr.", key=f"del_bien_{bien['id']}"):
                for pret_idx, p_item in enumerate(st.session_state.prets_immo):
                    if p_item.get('bien_associe_id') == bien['id']:
                        st.session_state.prets_immo[pret_idx]['bien_associe_id'] = None
                st.session_state.biens_immo.pop(i)
                st.rerun()

    st.subheader("💸 Prêts Immobiliers")
    with st.form("pret_immo_form", clear_on_submit=True):
        nom_pret = st.text_input("Nom du prêt (ex: Prêt RP)", key=key_nom_pret)
        montant_initial_pret = st.number_input("Montant initial emprunté (€)", min_value=0.0, value=100000.0, step=1000.0, key=key_montant_initial_pret)
        taux_interet_annuel_pret = st.slider("Taux d'intérêt annuel du prêt (%)", 0.0, 10.0, 2.5, 0.01, format="%.2f%%", key=key_taux_interet_annuel_pret)
        duree_initiale_pret_annees = st.number_input("Durée initiale du prêt (années)", min_value=0.1, max_value=30.0, value=20.0, step=0.1, format="%.1f", key=key_duree_initiale_pret_annees)
        date_debut_pret = st.date_input("Date de début du prêt", value=datetime(2015, 1, 1),min_value=datetime(1900,1,1), max_value=datetime.today(), key=key_date_debut_pret)
        options_biens_pour_pret = {"aucun": "Aucun bien spécifique"}
        options_biens_pour_pret.update({b['id']: b['nom'] for b in st.session_state.biens_immo})
        bien_associe_id_pret = st.selectbox("Bien immobilier associé", options=list(options_biens_pour_pret.keys()), format_func=lambda x: options_biens_pour_pret[x], key=key_bien_associe_id_pret)

        submitted_pret = st.form_submit_button("➕ Ajouter Prêt Immobilier")
        if submitted_pret and nom_pret:
            pret_id = f"pret_{len(st.session_state.prets_immo)+1}_{int(datetime.now().timestamp())}"
            st.session_state.prets_immo.append({
                "id": pret_id, "nom": nom_pret, "montant_initial": montant_initial_pret,
                "taux_interet_annuel": taux_interet_annuel_pret, "duree_initiale_annees": duree_initiale_pret_annees,
                "date_debut": date_debut_pret, "bien_associe_id": bien_associe_id_pret if bien_associe_id_pret != "aucun" else None
            })
            if bien_associe_id_pret and bien_associe_id_pret != "aucun":
                for idx_b, b_item in enumerate(st.session_state.biens_immo):
                    if b_item['id'] == bien_associe_id_pret:
                        st.session_state.biens_immo[idx_b]['pret_associe_id'] = pret_id; break
            st.success(f"Prêt '{nom_pret}' ajouté !")
            st.rerun() 
            
    if st.session_state.prets_immo:
        st.subheader("Prêts existants:")
        for i, pret in enumerate(st.session_state.prets_immo):
            col1_pret, col2_pret = st.columns([0.8, 0.2])
            assoc_bien_nom = "N/A"
            if pret['bien_associe_id']:
                found_bien = next((b['nom'] for b in st.session_state.biens_immo if b['id'] == pret['bien_associe_id']), None)
                if found_bien: assoc_bien_nom = found_bien
            col1_pret.write(f"- {pret['nom']} (Montant: {pret['montant_initial']:,.0f} €, Associé à: {assoc_bien_nom})")
            if col2_pret.button(f"Suppr.", key=f"del_pret_{pret['id']}"): 
                if pret['bien_associe_id']:
                     for b_idx, b_item in enumerate(st.session_state.biens_immo):
                        if b_item['id'] == pret['bien_associe_id'] and b_item.get('pret_associe_id') == pret['id']:
                            st.session_state.biens_immo[b_idx]['pret_associe_id'] = None; break
                st.session_state.prets_immo.pop(i)
                st.rerun()

    st.header("📈 Revenus Annuels")
    revenu_net_annuel_initial = st.number_input("Revenu net annuel principal initial (€)", min_value=0.0, value=st.session_state.get(key_revenu_net_annuel_initial, 40000.0), step=1000.0, key=key_revenu_net_annuel_initial)
    taux_evolution_revenu_annuel = st.slider("Taux d'évolution annuel du revenu (%)", -5.0, 10.0, st.session_state.get(key_taux_evolution_revenu_annuel, 1.0), 0.1, format="%.1f%%", key=key_taux_evolution_revenu_annuel)
    
    st.header("📉 Dépenses Annuelles")
    depenses_annuelles_initiales = st.number_input("Dépenses annuelles courantes (hors prêts) (€)", min_value=0.0, value=st.session_state.get(key_depenses_annuelles_initiales, 20000.0), step=1000.0, key=key_depenses_annuelles_initiales)
    taux_inflation_depenses_annuel = st.slider("Taux d'inflation annuel des dépenses (%)", 0.0, 10.0, st.session_state.get(key_taux_inflation_depenses_annuel, 2.0), 0.1, format="%.1f%%", key=key_taux_inflation_depenses_annuel)

    # --- Bouton pour lancer la projection initiale ---
    if st.button("🚀 Lancer la Projection Patrimoniale", type="primary", use_container_width=True, key="launch_projection_btn"):
        # Récupération des valeurs des widgets pour la projection
        age_actuel_val = st.session_state[key_age_actuel]
        horizon_projection_val = st.session_state[key_horizon_projection]
        annee_depart_projection_val = st.session_state[key_annee_depart_projection]
        patrimoine_financier_initial_val = st.session_state[key_patrimoine_financier_initial]
        taux_rendement_placements_annuel_val = st.session_state[key_taux_rendement_placements_annuel]
        revenu_net_annuel_initial_val = st.session_state[key_revenu_net_annuel_initial]
        taux_evolution_revenu_annuel_val = st.session_state[key_taux_evolution_revenu_annuel]
        depenses_annuelles_initiales_val = st.session_state[key_depenses_annuelles_initiales]
        taux_inflation_depenses_annuel_val = st.session_state[key_taux_inflation_depenses_annuel]


        if not st.session_state.biens_immo and patrimoine_financier_initial_val == 0 and not st.session_state.prets_immo :
            st.warning("Veuillez ajouter au moins un actif (financier ou immobilier) ou un prêt pour lancer la projection.")
        else:
            projection_data = []
            current_year_projection = annee_depart_projection_val
            valeur_patrimoine_financier = patrimoine_financier_initial_val
            biens_immo_projection = copy.deepcopy(st.session_state.biens_immo)
            prets_projection_temp = copy.deepcopy(st.session_state.prets_immo)
            prets_projection = []

            for p_orig in prets_projection_temp:
                p_copy = p_orig.copy()
                amort_complet_initial = generer_tableau_amortissement(p_copy['montant_initial'], p_copy['taux_interet_annuel'], p_copy['duree_initiale_annees'], p_copy['date_debut'])
                crd_debut_projection = p_copy['montant_initial']
                duree_restante_annees = p_copy['duree_initiale_annees']
                date_debut_amort_pour_projection = p_copy['date_debut']

                if not amort_complet_initial.empty:
                    lignes_avant_projection = amort_complet_initial[amort_complet_initial['Année'] < current_year_projection]
                    if not lignes_avant_projection.empty:
                        crd_debut_projection = lignes_avant_projection['Capital Restant Dû'].iloc[-1]
                        total_mois_rembourses_avant_proj = 0
                        for _, ligne in lignes_avant_projection.iterrows():
                            annee_paiement = ligne['Année']
                            mois_payes_cette_annee = 12
                            if annee_paiement == p_copy['date_debut'].year: mois_payes_cette_annee = 12 - p_copy['date_debut'].month + 1
                            total_mois_rembourses_avant_proj += mois_payes_cette_annee
                        mois_total_pret = p_copy['duree_initiale_annees'] * 12
                        mois_restants = mois_total_pret - total_mois_rembourses_avant_proj
                        duree_restante_annees = max(0, mois_restants / 12.0)
                        date_debut_amort_pour_projection = datetime(current_year_projection, 1, 1) 
                    elif amort_complet_initial['Année'].iloc[0] > current_year_projection:
                        date_debut_amort_pour_projection = p_copy['date_debut']
                        duree_restante_annees = p_copy['duree_initiale_annees']
                        crd_debut_projection = p_copy['montant_initial']
                    elif amort_complet_initial['Année'].iloc[0] == current_year_projection:
                        date_debut_amort_pour_projection = p_copy['date_debut']
                        duree_restante_annees = p_copy['duree_initiale_annees']
                        crd_debut_projection = p_copy['montant_initial']

                p_copy['capital_restant_du_proj'] = crd_debut_projection if crd_debut_projection > 0 else 0
                if p_copy['capital_restant_du_proj'] > 0 and duree_restante_annees > 0 :
                    p_copy['tableau_amortissement_pour_projection'] = generer_tableau_amortissement(p_copy['capital_restant_du_proj'], p_copy['taux_interet_annuel'], duree_restante_annees, date_debut_amort_pour_projection)
                else: p_copy['tableau_amortissement_pour_projection'] = pd.DataFrame(columns=['Année', 'Mensualité Totale Annuelle', 'Intérêts Annuels', 'Capital Remboursé Annuel', 'Capital Restant Dû'])
                prets_projection.append(p_copy)

            revenu_annuel_courant = revenu_net_annuel_initial_val
            depenses_annuelles_courantes = depenses_annuelles_initiales_val

            for i in range(int(horizon_projection_val)):
                annee_calculee = current_year_projection + i
                total_revenus_annee = revenu_annuel_courant
                revenus_locatifs_annuels = sum(b['loyer_annuel_brut'] - b['charges_annuelles'] for b in biens_immo_projection)
                total_revenus_annee += revenus_locatifs_annuels
                total_depenses_annee = depenses_annuelles_courantes
                total_interets_prets_annee, total_capital_rembourse_prets_annee, total_mensualites_prets_annee = 0,0,0

                for pret_idx, pret_p_loop in enumerate(prets_projection):
                    if pret_p_loop.get('capital_restant_du_proj', 0) > 0 and not pret_p_loop['tableau_amortissement_pour_projection'].empty:
                        amort_annee_df = pret_p_loop['tableau_amortissement_pour_projection']
                        ligne_amort_annee = amort_annee_df[amort_annee_df['Année'] == annee_calculee]
                        if not ligne_amort_annee.empty:
                            ligne = ligne_amort_annee.iloc[0]
                            total_interets_prets_annee += ligne['Intérêts Annuels']
                            total_capital_rembourse_prets_annee += ligne['Capital Remboursé Annuel']
                            total_mensualites_prets_annee += ligne['Mensualité Totale Annuelle']
                            prets_projection[pret_idx]['capital_restant_du_proj'] = ligne['Capital Restant Dû']
                
                flux_tresorerie_net_annee = total_revenus_annee - total_depenses_annee - total_mensualites_prets_annee
                valeur_patrimoine_financier = (valeur_patrimoine_financier + flux_tresorerie_net_annee) * (1 + taux_rendement_placements_annuel_val / 100)
                valeur_patrimoine_financier = max(0, valeur_patrimoine_financier)

                valeur_totale_biens_immo = 0
                for bien_idx, bien_b_loop in enumerate(biens_immo_projection):
                    biens_immo_projection[bien_idx]['valeur_actuelle'] *= (1 + bien_b_loop['taux_valorisation_annuel'])
                    valeur_totale_biens_immo += biens_immo_projection[bien_idx]['valeur_actuelle']

                passif_total_prets = sum(p_fin.get('capital_restant_du_proj', 0) for p_fin in prets_projection if p_fin.get('capital_restant_du_proj', 0) > 0)
                actifs_totaux = valeur_patrimoine_financier + valeur_totale_biens_immo
                patrimoine_net = actifs_totaux - passif_total_prets

                projection_data.append({
                    "Année": annee_calculee, "Âge Client": age_actuel_val + i,
                    "Revenus Totaux (€)": total_revenus_annee, "Dépenses Totales (€)": total_depenses_annee,
                    "Mensualités Prêts (€)": total_mensualites_prets_annee, "Intérêts Prêts (€)": total_interets_prets_annee,
                    "Capital Remboursé Prêts (€)": total_capital_rembourse_prets_annee, "Flux Trésorerie Net (€)": flux_tresorerie_net_annee,
                    "Patrimoine Financier (€)": valeur_patrimoine_financier, "Valeur Biens Immobiliers (€)": valeur_totale_biens_immo,
                    "Actifs Totaux (€)": actifs_totaux, "Passif Total (Prêts) (€)": passif_total_prets, "Patrimoine Net (€)": patrimoine_net
                })
                revenu_annuel_courant *= (1 + taux_evolution_revenu_annuel_val / 100)
                depenses_annuelles_courantes *= (1 + taux_inflation_depenses_annuel_val / 100)
                for bien_idx_update, bien_b_update in enumerate(biens_immo_projection): # Biens_immo_projection est la liste des biens pour la projection en cours
                    biens_immo_projection[bien_idx_update]['loyer_annuel_brut'] *= (1 + taux_inflation_depenses_annuel_val / 100)
                    biens_immo_projection[bien_idx_update]['charges_annuelles'] *= (1 + taux_inflation_depenses_annuel_val / 100)
            
            st.session_state.df_projection = pd.DataFrame(projection_data)
            st.session_state.biens_immo_projection_fin = biens_immo_projection 
            st.session_state.prets_projection_fin = prets_projection 
            st.session_state.projection_calculée = True
            st.session_state.df_projection_simulee = None # Réinitialiser une éventuelle simulation précédente
            st.success("Projection patrimoniale calculée avec succès !")
    
    st.divider() # Séparateur visuel avant la section de simulation de revente

    # --- Section pour la Simulation de Revente (dans tab_config) ---
    if st.session_state.get('projection_calculée', False) and st.session_state.df_projection is not None:
        st.header("🔄 Simulation de Revente d'un Bien (Optionnel)")
        biens_etat_initial_sim_vente_cfg = st.session_state.biens_immo # Biens initiaux pour la sélection
        
        if not biens_etat_initial_sim_vente_cfg:
            st.info("Aucun bien immobilier n'a été ajouté pour simuler une vente.")
        else:
            options_biens_vente_sim_cfg = {b_sim_cfg['id']: b_sim_cfg['nom'] for b_sim_cfg in biens_etat_initial_sim_vente_cfg}
            bien_a_vendre_id_sim_cfg = st.selectbox("Choisir un bien à vendre:", options=list(options_biens_vente_sim_cfg.keys()), format_func=lambda x: options_biens_vente_sim_cfg[x], key=key_sb_bien_vente_sim_config)
            
            annees_projection_disponibles_sim_cfg = st.session_state.df_projection["Année"].unique().tolist()
            annee_vente_simulee_sim_cfg = st.selectbox("Année de la vente simulée:", options=annees_projection_disponibles_sim_cfg, key=key_sb_annee_vente_sim_config)

            if st.button("Simuler la Vente et Calculer l'Impact", key=key_sim_vente_btn_exec_config):
                bien_vendu_details_sim_cfg = next(b_s_cfg for b_s_cfg in biens_etat_initial_sim_vente_cfg if b_s_cfg['id'] == bien_a_vendre_id_sim_cfg)
                
                # Recalcul de la valeur du bien à l'année de vente
                valeur_bien_annee_vente_sim_cfg = bien_vendu_details_sim_cfg['valeur_actuelle'] # Valeur initiale entrée par l'utilisateur
                annee_depart_valorisation = st.session_state.get(key_annee_depart_projection) # Année de départ de la projection principale
                # La valorisation doit partir de l'année de départ de la projection globale jusqu'à l'année de vente
                for an_val_cfg in range(annee_depart_valorisation, annee_vente_simulee_sim_cfg + 1):
                    # Si c'est la première année de valorisation (an_val_cfg == annee_depart_valorisation), la valeur est déjà celle de départ.
                    # On applique la valorisation à partir de la fin de la première année de projection.
                    # Donc, si an_val_cfg > annee_depart_valorisation, on multiplie.
                    # Ou plus simple: on la fait évoluer pour chaque année de la période.
                    if an_val_cfg >= annee_depart_valorisation : # La valeur initiale est pour annee_depart_valorisation
                         pass # la valeur initiale est déjà correcte pour le début de annee_depart_valorisation
                    # La boucle va appliquer la valorisation pour chaque année jusqu'à l'année de vente
                
                # Pour être précis, la valeur_actuelle est celle au début de annee_depart_projection.
                # Si annee_vente_simulee_sim_cfg = annee_depart_projection, la valeur est valeur_actuelle.
                # Si annee_vente_simulee_sim_cfg = annee_depart_projection + 1, la valeur est valeur_actuelle * (1+taux)
                # Donc, on doit appliquer le taux (annee_vente_simulee_sim_cfg - annee_depart_valorisation) fois.
                
                valeur_bien_annee_vente_sim_cfg = bien_vendu_details_sim_cfg['valeur_actuelle'] # Reset to initial value from user input
                nb_annees_valorisation = annee_vente_simulee_sim_cfg - annee_depart_valorisation
                for _ in range(nb_annees_valorisation +1): # +1 car la valeur initiale est pour l'année X, à la fin de l'année X elle a été valorisée une fois
                    if annee_vente_simulee_sim_cfg >= annee_depart_valorisation : # S'assurer que la vente n'est pas avant le début de la projection
                        valeur_bien_annee_vente_sim_cfg *= (1 + bien_vendu_details_sim_cfg['taux_valorisation_annuel'])
                # Correction : si annee_vente_simulee_sim_cfg == annee_depart_valorisation, la valeur est bien['valeur_actuelle'] * (1+taux) car c'est à la FIN de l'année de vente
                # Donc, si annee_vente == annee_depart, on valorise 1 fois. Si annee_vente == annee_depart + N, on valorise N+1 fois.
                
                # Réinitialisation de la valeur du bien pour un calcul correct de la valorisation jusqu'à l'année de vente
                valeur_bien_specifique_annee_vente = bien_vendu_details_sim_cfg['valeur_actuelle'] # Partir de la valeur initiale du bien
                # La valeur actuelle est celle au début de 'annee_depart_projection'.
                # On la fait évoluer jusqu'à la fin de 'annee_vente_simulee_sim_cfg'.
                for _annee_evol in range(st.session_state.get(key_annee_depart_projection), annee_vente_simulee_sim_cfg + 1):
                    valeur_bien_specifique_annee_vente *= (1 + bien_vendu_details_sim_cfg['taux_valorisation_annuel'])


                crd_pret_associe_annee_vente_sim_cfg = 0
                if bien_vendu_details_sim_cfg.get('pret_associe_id'):
                    pret_associe_id_vendu_sim_cfg = bien_vendu_details_sim_cfg['pret_associe_id']
                    pret_orig_sim_cfg = next((p_os_cfg for p_os_cfg in st.session_state.prets_immo if p_os_cfg['id'] == pret_associe_id_vendu_sim_cfg), None)
                    if pret_orig_sim_cfg:
                        tab_amort_sim_cfg = generer_tableau_amortissement(pret_orig_sim_cfg['montant_initial'], pret_orig_sim_cfg['taux_interet_annuel'], pret_orig_sim_cfg['duree_initiale_annees'], pret_orig_sim_cfg['date_debut'])
                        ligne_amort_sim_cfg = tab_amort_sim_cfg[tab_amort_sim_cfg['Année'] == annee_vente_simulee_sim_cfg]
                        if not ligne_amort_sim_cfg.empty: crd_pret_associe_annee_vente_sim_cfg = ligne_amort_sim_cfg['Capital Restant Dû'].iloc[0]
                        else: 
                            crd_avant_sim_cfg = tab_amort_sim_cfg[tab_amort_sim_cfg['Année'] < annee_vente_simulee_sim_cfg]
                            if not crd_avant_sim_cfg.empty: crd_pret_associe_annee_vente_sim_cfg = crd_avant_sim_cfg['Capital Restant Dû'].iloc[-1] if crd_avant_sim_cfg['Capital Restant Dû'].iloc[-1] > 0 else 0
                            elif not tab_amort_sim_cfg.empty and tab_amort_sim_cfg['Année'].iloc[0] > annee_vente_simulee_sim_cfg : crd_pret_associe_annee_vente_sim_cfg = pret_orig_sim_cfg['montant_initial']
                
                # Affichage des détails de la vente (ici dans tab_config pour feedback immédiat)
                st.markdown(f"**Calculs pour la vente de '{bien_vendu_details_sim_cfg['nom']}' en {annee_vente_simulee_sim_cfg}**")
                st.write(f"Valeur estimée du bien à la vente : {valeur_bien_specifique_annee_vente:,.0f} €")
                st.write(f"CRD prêt associé (estimé) : {crd_pret_associe_annee_vente_sim_cfg:,.0f} €")

                pv_brute_s_cfg, _, _, _, _, _, _, _, imp_total_pv_s_cfg, pv_details_s_cfg = calculer_plus_value_immobiliere_fr(
                    bien_vendu_details_sim_cfg['prix_achat'], bien_vendu_details_sim_cfg['frais_acquisition_reels'], bien_vendu_details_sim_cfg['cout_travaux'],
                    valeur_bien_specifique_annee_vente, bien_vendu_details_sim_cfg['date_achat'], datetime(annee_vente_simulee_sim_cfg, 12, 31), 
                    bien_vendu_details_sim_cfg['est_residence_principale']
                )
                cash_net_vente_sim_cfg = 0
                if isinstance(imp_total_pv_s_cfg, str): 
                    st.info(imp_total_pv_s_cfg)
                    cash_net_vente_sim_cfg = valeur_bien_specifique_annee_vente - crd_pret_associe_annee_vente_sim_cfg
                else:
                    st.write(pv_details_s_cfg)
                    st.write(f"Impôt total sur PV estimé : {imp_total_pv_s_cfg:,.0f} €")
                    cash_net_vente_sim_cfg = valeur_bien_specifique_annee_vente - crd_pret_associe_annee_vente_sim_cfg - imp_total_pv_s_cfg
                st.write(f"Cash net estimé (après remb. prêt & impôt PV) : {cash_net_vente_sim_cfg:,.0f} €")

                # --- Recalculer une nouvelle projection à partir de l'année de vente ---
                df_proj_originale_cfg = st.session_state.df_projection
                annee_depart_proj_orig_cfg = st.session_state.get(key_annee_depart_projection)
                horizon_proj_orig_cfg = st.session_state.get(key_horizon_projection)

                nouvel_horizon_projection_cfg = int(horizon_proj_orig_cfg - (annee_vente_simulee_sim_cfg - annee_depart_proj_orig_cfg))

                if nouvel_horizon_projection_cfg < 0: # Correction: si nouvel_horizon est 0, on ne projette rien de plus.
                    st.warning("La vente a lieu la dernière année de la projection initiale ou après. Pas de projection future à recalculer après la vente.")
                    st.session_state.df_projection_simulee = pd.DataFrame() # Ou un message spécifique
                else:
                    # Patrimoine financier au début de l'année de vente (fin de l'année précédente) + cash de la vente
                    ligne_annee_avant_vente_cfg = df_proj_originale_cfg[df_proj_originale_cfg['Année'] == annee_vente_simulee_sim_cfg -1]
                    nouveau_patrimoine_financier_initial_cfg = 0
                    if not ligne_annee_avant_vente_cfg.empty:
                        nouveau_patrimoine_financier_initial_cfg = ligne_annee_avant_vente_cfg['Patrimoine Financier (€)'].iloc[0] + cash_net_vente_sim_cfg
                    else: # Vente la première année de la projection initiale
                        nouveau_patrimoine_financier_initial_cfg = st.session_state.get(key_patrimoine_financier_initial) + cash_net_vente_sim_cfg
                    
                    # Préparer les listes de biens et prêts pour la nouvelle projection
                    # Biens : ceux de la projection fin originale, moins celui vendu, avec valeurs ajustées à l'année de vente
                    nouveaux_biens_immo_cfg = []
                    for b_fin_orig in copy.deepcopy(st.session_state.biens_immo_projection_fin):
                        if b_fin_orig['id'] == bien_a_vendre_id_sim_cfg: continue # Exclure le bien vendu
                        
                        b_initial_pour_valeur = next(b_init_val for b_init_val in st.session_state.biens_immo if b_init_val['id'] == b_fin_orig['id'])
                        valeur_bien_restant_annee_vente = b_initial_pour_valeur['valeur_actuelle']
                        for _an_val_b_r_cfg in range(annee_depart_proj_orig_cfg, annee_vente_simulee_sim_cfg + 1):
                            valeur_bien_restant_annee_vente *= (1 + b_initial_pour_valeur['taux_valorisation_annuel'])
                        b_fin_orig['valeur_actuelle'] = valeur_bien_restant_annee_vente # Mettre à jour la valeur pour le départ de la nouvelle projection
                        nouveaux_biens_immo_cfg.append(b_fin_orig)

                    nouveaux_prets_cfg = []
                    for p_fin_orig_cfg in copy.deepcopy(st.session_state.prets_projection_fin):
                        p_initial_pour_recalcul = next(p_init_recalc for p_init_recalc in st.session_state.prets_immo if p_init_recalc['id'] == p_fin_orig_cfg['id'])
                        if p_initial_pour_recalcul.get('bien_associe_id') == bien_a_vendre_id_sim_cfg: continue

                        p_copy_cfg = p_initial_pour_recalcul.copy()
                        tab_amort_p_cfg = generer_tableau_amortissement(p_copy_cfg['montant_initial'], p_copy_cfg['taux_interet_annuel'], p_copy_cfg['duree_initiale_annees'], p_copy_cfg['date_debut'])
                        crd_p_cfg_annee_vente = p_copy_cfg['montant_initial']
                        duree_restante_p_cfg = p_copy_cfg['duree_initiale_annees']
                        date_debut_amort_p_cfg_new = p_copy_cfg['date_debut']

                        if not tab_amort_p_cfg.empty:
                            lignes_avant_p_cfg = tab_amort_p_cfg[tab_amort_p_cfg['Année'] < annee_vente_simulee_sim_cfg]
                            if not lignes_avant_p_cfg.empty:
                                crd_p_cfg_annee_vente = lignes_avant_p_cfg['Capital Restant Dû'].iloc[-1]
                                mois_remb_p_cfg = sum(12 if l_p['Année'] > p_copy_cfg['date_debut'].year else (12 - p_copy_cfg['date_debut'].month +1) for _, l_p in lignes_avant_p_cfg.iterrows())
                                duree_restante_p_cfg = max(0, (p_copy_cfg['duree_initiale_annees']*12 - mois_remb_p_cfg)/12.0)
                                date_debut_amort_p_cfg_new = datetime(annee_vente_simulee_sim_cfg,1,1)
                            elif tab_amort_p_cfg['Année'].iloc[0] >= annee_vente_simulee_sim_cfg:
                                crd_p_cfg_annee_vente = p_copy_cfg['montant_initial'] # Non touché si commence après/pendant
                                duree_restante_p_cfg = p_copy_cfg['duree_initiale_annees']
                                date_debut_amort_p_cfg_new = p_copy_cfg['date_debut']
                        
                        p_copy_cfg['capital_restant_du_proj'] = crd_p_cfg_annee_vente if crd_p_cfg_annee_vente > 0 else 0
                        if p_copy_cfg['capital_restant_du_proj'] > 0 and duree_restante_p_cfg > 0:
                            p_copy_cfg['tableau_amortissement_pour_projection'] = generer_tableau_amortissement(p_copy_cfg['capital_restant_du_proj'], p_copy_cfg['taux_interet_annuel'], duree_restante_p_cfg, date_debut_amort_p_cfg_new)
                        else: p_copy_cfg['tableau_amortissement_pour_projection'] = pd.DataFrame()
                        nouveaux_prets_cfg.append(p_copy_cfg)
                    
                    # Revenus / Dépenses pour la nouvelle projection (ceux de l'année de vente, ajustés)
                    ligne_annee_vente_orig_cfg = df_proj_originale_cfg[df_proj_originale_cfg['Année'] == annee_vente_simulee_sim_cfg]
                    revenu_ann_init_sim_cfg = st.session_state.get(key_revenu_net_annuel_initial) # Revenu de base
                    taux_evol_rev_sim_cfg = st.session_state.get(key_taux_evolution_revenu_annuel)
                    # Faire évoluer le revenu de base jusqu'à l'année de vente
                    for _ in range(annee_vente_simulee_sim_cfg - annee_depart_proj_orig_cfg):
                        revenu_ann_init_sim_cfg *= (1 + taux_evol_rev_sim_cfg / 100)

                    depense_ann_init_sim_cfg = st.session_state.get(key_depenses_annuelles_initiales)
                    taux_infl_dep_sim_cfg = st.session_state.get(key_taux_inflation_depenses_annuel)
                    # Faire évoluer les dépenses de base jusqu'à l'année de vente
                    for _ in range(annee_vente_simulee_sim_cfg - annee_depart_proj_orig_cfg):
                        depense_ann_init_sim_cfg *= (1 + taux_infl_dep_sim_cfg / 100)

                    # Lancer la nouvelle boucle de projection pour la simulation
                    projection_data_apres_vente_cfg = []
                    val_pat_fin_apres_vente_cfg = nouveau_patrimoine_financier_initial_cfg
                    rev_courant_apres_vente_cfg = revenu_ann_init_sim_cfg # Le revenu principal évolué
                    dep_courant_apres_vente_cfg = depense_ann_init_sim_cfg # Dépenses évoluées
                    
                    biens_immo_proj_apres_vente_cfg = copy.deepcopy(nouveaux_biens_immo_cfg) # Biens restants avec valeurs à jour pour l'année de vente
                    prets_proj_apres_vente_cfg = copy.deepcopy(nouveaux_prets_cfg) # Prêts restants avec CRD à jour

                    for k_cfg in range(int(nouvel_horizon_projection_cfg) +1 ): # +1 si horizon est 0, on projette l'année de vente
                        if nouvel_horizon_projection_cfg < 0 and k_cfg >0 : break # si horizon négatif, ne pas boucler
                        annee_calc_apres_vente_cfg = annee_vente_simulee_sim_cfg + k_cfg
                        
                        total_rev_an_apres_vente_cfg = rev_courant_apres_vente_cfg 
                        rev_loc_an_apres_vente_cfg = sum(b_av_cfg['loyer_annuel_brut'] - b_av_cfg['charges_annuelles'] for b_av_cfg in biens_immo_proj_apres_vente_cfg)
                        total_rev_an_apres_vente_cfg += rev_loc_an_apres_vente_cfg
                        
                        total_dep_an_apres_vente_cfg = dep_courant_apres_vente_cfg
                        mensualites_prets_apres_vente_cfg, interets_prets_apres_vente_cfg, cap_remb_prets_apres_vente_cfg = 0,0,0

                        for pret_idx_av_cfg, p_av_cfg in enumerate(prets_proj_apres_vente_cfg):
                            if p_av_cfg.get('capital_restant_du_proj',0) > 0 and not p_av_cfg['tableau_amortissement_pour_projection'].empty:
                                amort_df_av_cfg = p_av_cfg['tableau_amortissement_pour_projection']
                                ligne_amort_av_cfg = amort_df_av_cfg[amort_df_av_cfg['Année'] == annee_calc_apres_vente_cfg]
                                if not ligne_amort_av_cfg.empty:
                                    ligne_av_cfg = ligne_amort_av_cfg.iloc[0]
                                    mensualites_prets_apres_vente_cfg += ligne_av_cfg['Mensualité Totale Annuelle']
                                    interets_prets_apres_vente_cfg += ligne_av_cfg['Intérêts Annuels']
                                    cap_remb_prets_apres_vente_cfg += ligne_av_cfg['Capital Remboursé Annuel']
                                    prets_proj_apres_vente_cfg[pret_idx_av_cfg]['capital_restant_du_proj'] = ligne_av_cfg['Capital Restant Dû']
                        
                        flux_treso_apres_vente_cfg = total_rev_an_apres_vente_cfg - total_dep_an_apres_vente_cfg - mensualites_prets_apres_vente_cfg
                        val_pat_fin_apres_vente_cfg = (val_pat_fin_apres_vente_cfg + flux_treso_apres_vente_cfg) * (1 + st.session_state.get(key_taux_rendement_placements_annuel)/100)
                        val_pat_fin_apres_vente_cfg = max(0, val_pat_fin_apres_vente_cfg)

                        val_tot_biens_apres_vente_cfg = 0
                        for b_idx_av_cfg, b_av_loop_cfg in enumerate(biens_immo_proj_apres_vente_cfg):
                            biens_immo_proj_apres_vente_cfg[b_idx_av_cfg]['valeur_actuelle'] *= (1 + b_av_loop_cfg['taux_valorisation_annuel'])
                            val_tot_biens_apres_vente_cfg += biens_immo_proj_apres_vente_cfg[b_idx_av_cfg]['valeur_actuelle']
                        
                        passif_prets_apres_vente_cfg = sum(p_av_fin_cfg.get('capital_restant_du_proj',0) for p_av_fin_cfg in prets_proj_apres_vente_cfg)
                        actifs_tot_apres_vente_cfg = val_pat_fin_apres_vente_cfg + val_tot_biens_apres_vente_cfg
                        pat_net_apres_vente_cfg = actifs_tot_apres_vente_cfg - passif_prets_apres_vente_cfg

                        projection_data_apres_vente_cfg.append({
                            "Année": annee_calc_apres_vente_cfg, "Âge Client": st.session_state.get(key_age_actuel) + (annee_calc_apres_vente_cfg - annee_depart_proj_orig_cfg),
                            "Revenus Totaux (€)": total_rev_an_apres_vente_cfg, "Dépenses Totales (€)": total_dep_an_apres_vente_cfg,
                            "Mensualités Prêts (€)": mensualites_prets_apres_vente_cfg, "Intérêts Prêts (€)": interets_prets_apres_vente_cfg,
                            "Capital Remboursé Prêts (€)": cap_remb_prets_apres_vente_cfg, "Flux Trésorerie Net (€)": flux_treso_apres_vente_cfg,
                            "Patrimoine Financier (€)": val_pat_fin_apres_vente_cfg, "Valeur Biens Immobiliers (€)": val_tot_biens_apres_vente_cfg,
                            "Actifs Totaux (€)": actifs_tot_apres_vente_cfg, "Passif Total (Prêts) (€)": passif_prets_apres_vente_cfg,
                            "Patrimoine Net (€)": pat_net_apres_vente_cfg
                        })
                        rev_courant_apres_vente_cfg *= (1 + st.session_state.get(key_taux_evolution_revenu_annuel)/100)
                        dep_courant_apres_vente_cfg *= (1 + st.session_state.get(key_taux_inflation_depenses_annuel)/100)
                        for b_idx_av_upd_cfg, b_av_upd_cfg in enumerate(biens_immo_proj_apres_vente_cfg):
                            biens_immo_proj_apres_vente_cfg[b_idx_av_upd_cfg]['loyer_annuel_brut'] *= (1 + st.session_state.get(key_taux_inflation_depenses_annuel)/100)
                            biens_immo_proj_apres_vente_cfg[b_idx_av_upd_cfg]['charges_annuelles'] *= (1 + st.session_state.get(key_taux_inflation_depenses_annuel)/100)
                    
                    if projection_data_apres_vente_cfg:
                        df_projection_apres_vente_recalculee_cfg = pd.DataFrame(projection_data_apres_vente_cfg)
                        st.session_state.df_projection_simulee = df_projection_apres_vente_recalculee_cfg
                        st.success("Impact de la vente simulé avec une nouvelle projection recalculée. Consultez l'onglet 'Simulation Vente (Résultats)'.")
                    else: # Cas où nouvel_horizon_projection_cfg était <=0
                        st.session_state.df_projection_simulee = pd.DataFrame() # S'assurer qu'il est vide
                        st.info("La vente a lieu à la fin ou après la période de projection initiale. L'impact sur le patrimoine financier a été calculé, mais il n'y a pas d'années futures à projeter après la vente dans ce scénario.")


# --- Affichage des Résultats dans les Onglets (si projection calculée) ---
# Ces sections s'affichent conditionnellement si la projection initiale a été faite.

if st.session_state.get('projection_calculée', False) and st.session_state.df_projection is not None:
    df_projection_display = st.session_state.df_projection 
    biens_immo_projection_fin_display = st.session_state.biens_immo_projection_fin
    prets_projection_fin_display = st.session_state.prets_projection_fin

    with tab_synthese:
        st.subheader("Évolution du Patrimoine Net (Projection Initiale)")
        if not df_projection_display.empty:
            st.line_chart(df_projection_display, x="Année", y=["Patrimoine Net (€)", "Actifs Totaux (€)", "Passif Total (Prêts) (€)"])
            st.subheader("Évolution des Flux de Trésorerie Annuels (Projection Initiale)")
            st.bar_chart(df_projection_display, x="Année", y=["Flux Trésorerie Net (€)", "Revenus Totaux (€)", "Dépenses Totales (€)", "Mensualités Prêts (€)"])
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Composition Actifs Fin Projection (Initiale)")
                actifs_fin_disp = df_projection_display.iloc[-1]
                st.metric("Patrimoine Financier Final", f"{actifs_fin_disp['Patrimoine Financier (€)']:,.0f} €")
                st.metric("Valeur Biens Immobiliers Finale", f"{actifs_fin_disp['Valeur Biens Immobiliers (€)']:,.0f} €")
            with col2:
                st.subheader("Patrimoine Net Fin Projection (Initiale)")
                val_biens_init_disp = sum(b['valeur_actuelle'] for b in st.session_state.biens_immo)
                passif_prets_init_disp = 0
                annee_dep_proj_disp = st.session_state.get(key_annee_depart_projection)
                for p_init_state_disp in st.session_state.prets_immo:
                    tab_amort_delta_disp = generer_tableau_amortissement(p_init_state_disp['montant_initial'], p_init_state_disp['taux_interet_annuel'], p_init_state_disp['duree_initiale_annees'], p_init_state_disp['date_debut'])
                    crd_delta_disp = p_init_state_disp['montant_initial']
                    if not tab_amort_delta_disp.empty:
                        ligne_debut_proj_disp = tab_amort_delta_disp[tab_amort_delta_disp['Année'] < annee_dep_proj_disp]
                        if not ligne_debut_proj_disp.empty: crd_delta_disp = ligne_debut_proj_disp['Capital Restant Dû'].iloc[-1]
                        elif tab_amort_delta_disp['Année'].iloc[0] >= annee_dep_proj_disp: crd_delta_disp = p_init_state_disp['montant_initial']
                    passif_prets_init_disp += crd_delta_disp if crd_delta_disp > 0 else 0
                pat_net_glob_init_disp = st.session_state.get(key_patrimoine_financier_initial,0) + val_biens_init_disp - passif_prets_init_disp
                st.metric("Patrimoine Net Final", f"{df_projection_display.iloc[-1]['Patrimoine Net (€)']:,.0f} €", delta=f"{df_projection_display.iloc[-1]['Patrimoine Net (€)'] - pat_net_glob_init_disp:,.0f} € vs initial")
        else: st.write("Aucune donnée de projection initiale à afficher.")

    with tab_details_proj:
        st.subheader("Tableau de Projection Détaillé (Projection Initiale)")
        if not df_projection_display.empty:
            st.dataframe(df_projection_display.style.format("{:,.0f}", subset=[col for col in df_projection_display.columns if col not in ["Année", "Âge Client"]]))
        else: st.write("Aucune donnée de projection initiale à afficher.")

    with tab_details_prets:
        st.subheader("Détail des Prêts et Tableaux d'Amortissement (depuis l'origine - basés sur entrées initiales)")
        if not st.session_state.prets_immo: st.info("Aucun prêt n'a été ajouté.")
        for pret_initial_state_disp in st.session_state.prets_immo: 
            st.markdown(f"#### Prêt: {pret_initial_state_disp['nom']}")
            tab_amort_complet_orig_disp = generer_tableau_amortissement(pret_initial_state_disp['montant_initial'], pret_initial_state_disp['taux_interet_annuel'], pret_initial_state_disp['duree_initiale_annees'], pret_initial_state_disp['date_debut'])
            if not tab_amort_complet_orig_disp.empty:
                st.dataframe(tab_amort_complet_orig_disp.style.format({'Mensualité Totale Annuelle': '{:,.2f} €', 'Intérêts Annuels': '{:,.2f} €', 'Capital Remboursé Annuel': '{:,.2f} €', 'Capital Restant Dû': '{:,.2f} €'}))
            else: st.write(f"Tableau d'amortissement non disponible pour '{pret_initial_state_disp['nom']}'.")

    with tab_details_biens:
        st.subheader("Détail des Biens Immobiliers (Valorisation à la fin de la projection initiale)")
        if not df_projection_display.empty and biens_immo_projection_fin_display:
            data_biens_fin_display_list = []
            for bien_proj_item_disp_fin in biens_immo_projection_fin_display:
                pret_assoc_info_disp_fin = "Aucun"
                crd_pret_assoc_disp_fin = 0
                if bien_proj_item_disp_fin.get('pret_associe_id'):
                    pret_final_trouve_disp_fin = next((p_fd for p_fd in prets_projection_fin_display if p_fd['id'] == bien_proj_item_disp_fin['pret_associe_id']), None)
                    if pret_final_trouve_disp_fin:
                         pret_assoc_info_disp_fin = pret_final_trouve_disp_fin['nom']
                         crd_pret_assoc_disp_fin = pret_final_trouve_disp_fin.get('capital_restant_du_proj', 0)
                bien_initial_info_disp_fin = next((b_id for b_id in st.session_state.biens_immo if b_id['id'] == bien_proj_item_disp_fin['id']), None)
                val_init_bien_disp_fin = bien_initial_info_disp_fin['valeur_actuelle'] if bien_initial_info_disp_fin else 0
                data_biens_fin_display_list.append({
                    "Nom du Bien": bien_proj_item_disp_fin['nom'], "Valeur Initiale (€)": val_init_bien_disp_fin,
                    "Valeur Finale Estimée (€)": bien_proj_item_disp_fin['valeur_actuelle'], "Prêt Associé": pret_assoc_info_disp_fin,
                    "CRD Prêt Associé (€)": crd_pret_assoc_disp_fin, "Valeur Nette Estimée (€)": bien_proj_item_disp_fin['valeur_actuelle'] - crd_pret_assoc_disp_fin
                })
            df_biens_fin_display_final = pd.DataFrame(data_biens_fin_display_list)
            if not df_biens_fin_display_final.empty:
                cols_fmt_biens_fin = [col for col in ["Valeur Initiale (€)", "Valeur Finale Estimée (€)", "CRD Prêt Associé (€)", "Valeur Nette Estimée (€)"] if col in df_biens_fin_display_final.columns]
                st.dataframe(df_biens_fin_display_final.style.format("{:,.0f} €", subset=cols_fmt_biens_fin, na_rep="-"))
            else: st.write("Aucune donnée de bien à afficher.")
        else: st.info("Lancez une projection initiale et ajoutez des biens pour voir ce détail.")

# Affichage des résultats de la simulation de vente dans son propre onglet
with tab_sim_vente_resultats:
    st.subheader("Résultats de la Simulation de Vente (Projection Recalculée)")
    if st.session_state.get('df_projection_simulee') is not None and not st.session_state.df_projection_simulee.empty:
        df_simulee_display = st.session_state.df_projection_simulee
        st.line_chart(df_simulee_display, x="Année", y=["Patrimoine Net (€)", "Actifs Totaux (€)", "Passif Total (Prêts) (€)"])
        st.dataframe(df_simulee_display.style.format("{:,.0f}", subset=[col for col in df_simulee_display.columns if col not in ["Année", "Âge Client"]]))
    elif st.session_state.get('df_projection_simulee') is not None and st.session_state.df_projection_simulee.empty: # Cas où la simulation a été faite mais pas de projection future
        st.info("La vente a eu lieu à la fin ou après la période de projection initiale. L'impact sur le patrimoine financier a été calculé (voir onglet Configuration), mais il n'y a pas d'années futures à projeter après la vente dans ce scénario.")
    else:
        st.info("Aucune simulation de vente n'a été effectuée ou la projection initiale n'a pas été lancée. Veuillez configurer et lancer une simulation dans l'onglet '⚙️ Configuration & Entrées'.")


# Pied de page 
st.sidebar.markdown("---")
st.sidebar.info("Application développée à titre démonstratif. Les calculs (notamment fiscaux et d'amortissement) sont simplifiés.")


# simulateur_patrimonial.py

import streamlit as st
import pandas as pd
import numpy_financial as npf
from scipy.optimize import minimize
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(
    page_title="Simulateur Patrimonial Dynamique",
    page_icon="📈",
    layout="wide"
)

# --- FONCTIONS DE CALCUL ---

def calculer_mensualite_credit(montant, taux_annuel, duree_annees):
    """Calcule la mensualité d'un prêt."""
    if montant == 0:
        return 0
    taux_mensuel = taux_annuel / 12
    n_periodes = duree_annees * 12
    if taux_mensuel > 0:
        mensualite = npf.pmt(taux_mensuel, n_periodes, -montant)
    else: # Cas d'un taux à 0%
        mensualite = montant / n_periodes
    return mensualite


# --- INTERFACE UTILISATEUR (SIDEBAR) ---
st.sidebar.header("👤 Profil Investisseur")
tmi = st.sidebar.selectbox(
    "Tranche Marginale d'Imposition (TMI)",
    options=[0.0, 0.11, 0.30, 0.41, 0.45],
    index=2,
    format_func=lambda x: f"{x:.0%}"
)

st.sidebar.header("🗓️ Horizon de Projection")
horizon_projection = st.sidebar.slider("Horizon de projection (années)", min_value=5, max_value=40, value=20)

st.sidebar.header("💰 Investissements Directs")

st.sidebar.subheader("Assurance-Vie")
with st.sidebar.expander("Paramètres Assurance-Vie"):
    capital_initial_av = st.number_input("Capital initial Assurance-Vie (€)", min_value=0, value=25000, step=1000, key="cap_init_av")
    epargne_mensuelle_av = st.number_input("Épargne mensuelle Assurance-Vie (€)", min_value=0, value=400, step=50, key="ep_mens_av")
    st.markdown("###### Hypothèses spécifiques Assurance-Vie")
    rendement_av_pct = st.number_input(
        "Rendement annuel net Assurance-Vie (%)", 
        min_value=0.0, 
        max_value=20.0, 
        value=4.0, 
        step=0.1, 
        format="%.1f", 
        key="rend_av_pct"
    )
    frais_entree_av_pct = st.number_input(
        "Frais d'entrée Assurance-Vie (%)",
        min_value=0.0,
        max_value=10.0, # Ajustable
        value=4.8,
        step=0.1,
        format="%.1f",
        key="frais_av_pct"
    )
    rendement_av = rendement_av_pct / 100.0

st.sidebar.subheader("Plan d'Épargne Retraite (PER)")
with st.sidebar.expander("Paramètres PER"):
    capital_initial_per = st.number_input("Capital initial PER (€)", min_value=0, value=10000, step=1000, key="cap_init_per")
    epargne_mensuelle_per = st.number_input("Épargne mensuelle PER (€)", min_value=0, value=300, step=50, key="ep_mens_per")
    st.markdown("###### Hypothèses spécifiques PER")
    rendement_per_pct = st.number_input(
        "Rendement annuel net PER (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.1,
        format="%.1f",
        key="rend_per_pct"
    )
    frais_entree_per_pct = st.number_input(
        "Frais d'entrée PER (%)",
        min_value=0.0,
        max_value=10.0, # Ajustable
        value=4.5,
        step=0.1,
        format="%.1f",
        key="frais_per_pct"
    )
    rendement_per = rendement_per_pct / 100.0

st.sidebar.header("🏠 Investissements à Levier (Crédit)")
with st.sidebar.expander("Paramètres Immobilier Locatif"):
    apport_initial_immo = st.number_input("Apport initial Immobilier (€)", min_value=0, value=20000, step=1000, key="apport_immo")
    montant_emprunt_immo = st.number_input("Montant emprunté Immobilier (€)", min_value=0, value=130000, step=10000, key="emprunt_immo")    
    duree_credit_immo = st.slider("Durée du crédit immobilier (années)", 10, 25, 20)
    st.markdown("--- \n###### Hypothèses spécifiques Immobilier") # Ajout d'un séparateur visuel
    rendement_locatif_immo = st.slider("Rendement locatif brut Immobilier", 0.01, 0.10, 0.05, format="%.2f", key="rend_loc_immo")
    revalorisation_immo = st.slider("Revalorisation annuelle Immobillier", 0.00, 0.05, 0.02, format="%.2f", key="reval_immo")
    taux_credit_immo = st.slider("Taux d'intérêt crédit Immobilier", 0.01, 0.07, 0.04, format="%.2f", key="tx_cred_immo")
    taux_prelevements_sociaux_immo = st.slider("Taux Prélèvements Sociaux Immobilier", 0.10, 0.20, 0.172, format="%.3f", key="ps_immo")

    mensualite_immo_disp = calculer_mensualite_credit(montant_emprunt_immo, taux_credit_immo, duree_credit_immo)
    if montant_emprunt_immo > 0:
        st.markdown(f"↳ **Mensualité crédit :** `{mensualite_immo_disp:,.2f} €/mois`")

    valeur_acquisition_immo_disp = apport_initial_immo + montant_emprunt_immo
    loyer_immo_mensuel_estime = 0.0

    if valeur_acquisition_immo_disp > 0:
        loyer_immo_mensuel_estime = (valeur_acquisition_immo_disp * rendement_locatif_immo) / 12
        st.markdown(f"↳ **Loyer mensuel brut estimé (an 1) :** `{loyer_immo_mensuel_estime:,.2f} €/mois`")
        
        effort_avant_dediee_immo = mensualite_immo_disp - loyer_immo_mensuel_estime
        st.markdown(f"↳ **Effort d'épargne (avant épargne dédiée) :** `{effort_avant_dediee_immo:,.2f} €/mois`")

        if st.button("Utiliser cet effort comme épargne dédiée (Immo)", key="btn_apply_immo_effort_to_dedicated"):
            st.session_state.epargne_immo_dediee = float(max(0, effort_avant_dediee_immo))
            # Le script Streamlit se réexécute, mettant à jour la valeur du champ ci-dessous

    epargne_mensuelle_immo_dediee = st.number_input(
        "Épargne mensuelle dédiée Immobilier (€)", 
        min_value=0.0, 
        value=150.0, 
        step=50.0, 
        key="epargne_immo_dediee",
        format="%.2f"
    )

    if valeur_acquisition_immo_disp > 0:
        effort_epargne_immo_estime_final = mensualite_immo_disp - loyer_immo_mensuel_estime + epargne_mensuelle_immo_dediee
        st.markdown(f"↳ **Effort d'épargne mensuel net TOTAL :** `{effort_epargne_immo_estime_final:,.2f} €/mois`")
    elif epargne_mensuelle_immo_dediee > 0 : 
        st.markdown(f"↳ **Effort d'épargne mensuel net TOTAL :** `{epargne_mensuelle_immo_dediee:,.2f} €/mois`")

with st.sidebar.expander("Paramètres SCPI"):
    apport_initial_scpi = st.number_input("Apport initial SCPI (€)", min_value=0, value=10000, step=1000, key="apport_scpi")
    montant_emprunt_scpi = st.number_input("Montant emprunté SCPI (€)", min_value=0, value=40000, step=5000, key="emprunt_scpi")
    duree_credit_scpi = st.slider("Durée du crédit SCPI (années)", 10, 25, 20)
    st.markdown("--- \n###### Hypothèses spécifiques SCPI") # Ajout d'un séparateur visuel
    rendement_scpi = st.slider("Rendement brut SCPI (taux de distribution)", 0.02, 0.08, 0.06, format="%.2f", key="rend_scpi")
    taux_credit_scpi = st.slider("Taux d'intérêt crédit SCPI", 0.01, 0.07, 0.045, format="%.3f", key="tx_cred_scpi") # Taux légèrement différent pour exemple
    taux_prelevements_sociaux_scpi = st.slider("Taux Prélèvements Sociaux SCPI", 0.10, 0.20, 0.172, format="%.3f", key="ps_scpi")

    mensualite_scpi_disp = calculer_mensualite_credit(montant_emprunt_scpi, taux_credit_scpi, duree_credit_scpi)
    if montant_emprunt_scpi > 0:
        st.markdown(f"↳ **Mensualité crédit :** `{mensualite_scpi_disp:,.2f} €/mois`")

    valeur_acquisition_scpi_disp = apport_initial_scpi + montant_emprunt_scpi
    revenu_scpi_mensuel_estime = 0.0

    if valeur_acquisition_scpi_disp > 0:
        revenu_scpi_mensuel_estime = (valeur_acquisition_scpi_disp * rendement_scpi) / 12
        st.markdown(f"↳ **Revenu SCPI mensuel brut estimé (an 1) :** `{revenu_scpi_mensuel_estime:,.2f} €/mois`")

        effort_avant_dediee_scpi = mensualite_scpi_disp - revenu_scpi_mensuel_estime
        st.markdown(f"↳ **Effort d'épargne (avant épargne dédiée) :** `{effort_avant_dediee_scpi:,.2f} €/mois`")

        if st.button("Utiliser cet effort comme épargne dédiée (SCPI)", key="btn_apply_scpi_effort_to_dedicated"):
            st.session_state.epargne_scpi_dediee = float(max(0, effort_avant_dediee_scpi))

    epargne_mensuelle_scpi_dediee = st.number_input(
        "Épargne mensuelle dédiée SCPI (€)", 
        min_value=0.0, 
        value=50.0, 
        step=50.0, 
        key="epargne_scpi_dediee",
        format="%.2f"
    )
    if valeur_acquisition_scpi_disp > 0:
        effort_epargne_scpi_estime_final = mensualite_scpi_disp - revenu_scpi_mensuel_estime + epargne_mensuelle_scpi_dediee
        st.markdown(f"↳ **Effort d'épargne mensuel net TOTAL :** `{effort_epargne_scpi_estime_final:,.2f} €/mois`")
    elif epargne_mensuelle_scpi_dediee > 0: 
        st.markdown(f"↳ **Effort d'épargne mensuel net TOTAL :** `{epargne_mensuelle_scpi_dediee:,.2f} €/mois`")

# Calcul des montants d'achat totaux
montant_achat_immo = apport_initial_immo + montant_emprunt_immo
montant_achat_scpi = apport_initial_scpi + montant_emprunt_scpi


def simuler_projection_patrimoniale(
    horizon_projection, tmi,
    capital_initial_av, epargne_mensuelle_av, rendement_av, frais_entree_av_pct,
    capital_initial_per, epargne_mensuelle_per, rendement_per, frais_entree_per_pct,
    apport_initial_immo, montant_emprunt_immo, duree_credit_immo,
    rendement_locatif_immo, revalorisation_immo, taux_credit_immo, taux_prelevements_sociaux_immo,
    epargne_mensuelle_immo_dediee,
    apport_initial_scpi, montant_emprunt_scpi, duree_credit_scpi,
    rendement_scpi, taux_credit_scpi, taux_prelevements_sociaux_scpi,
    epargne_mensuelle_scpi_dediee
):
    """
    Effectue la simulation de projection patrimoniale.
    Retourne un DataFrame avec la projection et un dictionnaire des KPIs.
    """
    # Calcul des montants d'achat totaux
    montant_achat_immo = apport_initial_immo + montant_emprunt_immo
    montant_achat_scpi = apport_initial_scpi + montant_emprunt_scpi

    # Initialisation des variables
    projection_data = []
    initial_outlay_total = capital_initial_av + capital_initial_per + apport_initial_immo + apport_initial_scpi
    flux_nets_annuels = [-initial_outlay_total] # Flux initial pour tous les apports

    # Conversion des frais en décimal
    frais_entree_av = frais_entree_av_pct / 100.0
    frais_entree_per = frais_entree_per_pct / 100.0

    valeur_av_sim = capital_initial_av * (1 - frais_entree_av)
    valeur_per_sim = capital_initial_per * (1 - frais_entree_per)

    # Immobilier
    valeur_immo_sim = montant_achat_immo
    solde_restant_du_immo_sim = montant_emprunt_immo
    mensualite_immo_sim = calculer_mensualite_credit(montant_emprunt_immo, taux_credit_immo, duree_credit_immo)

    # SCPI
    valeur_scpi_sim = montant_achat_scpi
    solde_restant_du_scpi_sim = montant_emprunt_scpi
    mensualite_scpi_sim = calculer_mensualite_credit(montant_emprunt_scpi, taux_credit_scpi, duree_credit_scpi)

    # Variables pour les totaux
    total_defiscalisation_sim = 0
    total_effort_epargne_sim = initial_outlay_total
    total_cashflow_positif_levier_sim = 0
    total_impots_payes_levier_sim = 0

    # KPIs pour le Sankey
    s_cap_init_av_net = capital_initial_av * (1 - frais_entree_av)
    s_cap_init_per_net = capital_initial_per * (1 - frais_entree_per)
    s_apport_immo_init = apport_initial_immo
    s_apport_scpi_init = apport_initial_scpi
    # Nouveaux KPIs pour le brut et les frais
    kpi_s_cap_init_av_brut = capital_initial_av
    kpi_s_cap_init_per_brut = capital_initial_per
    kpi_s_frais_entree_cap_init_cum = (kpi_s_cap_init_av_brut * frais_entree_av) + (kpi_s_cap_init_per_brut * frais_entree_per)
    kpi_s_cap_init_total_net = s_cap_init_av_net + s_cap_init_per_net + s_apport_immo_init + s_apport_scpi_init

    kpi_s_ep_av_net_cum = 0
    kpi_s_ep_per_net_cum = 0
    kpi_s_ep_immo_ded_cum = 0
    kpi_s_ep_scpi_reinv_cum = 0
    kpi_s_int_av_cum = 0
    # Nouveaux KPIs pour le brut et les frais sur épargne
    kpi_s_ep_av_brut_cum = 0
    kpi_s_ep_per_brut_cum = 0
    kpi_s_frais_entree_ep_cum = 0
    kpi_s_int_per_cum = 0
    kpi_s_loyers_immo_bruts_cum = 0
    kpi_s_rev_scpi_bruts_cum = 0
    kpi_s_revalo_immo_cum = 0
    kpi_s_int_emprunt_immo_cum = 0
    kpi_s_int_emprunt_scpi_cum = 0
    # kpi_s_defisc_per_cum est total_defiscalisation_sim
    # kpi_s_impots_total_levier est total_impots_payes_levier_sim

    # Boucle de projection annuelle
    for annee in range(1, horizon_projection + 1):
        chart_revenus_immo_bruts = 0.0
        chart_revenus_scpi_bruts = 0.0
        chart_economie_impot_per = 0.0
        chart_versements_av = 0.0
        chart_versements_per = 0.0
        chart_annuite_immo = 0.0
        chart_annuite_scpi = 0.0
        chart_impots_fonciers = 0.0
        chart_impots_scpi = 0.0
        chart_epargne_dediee_immo = 0.0
        chart_epargne_dediee_scpi = 0.0
        loyers_immo = 0.0

        # 1. GESTION DU PER
        versement_per_annuel_brut = epargne_mensuelle_per * 12
        versement_per_annuel_net_de_frais = versement_per_annuel_brut * (1 - frais_entree_per)
        if annee == 1:
            # L'économie d'impôt sur le capital initial PER est considérée comme un gain de l'année 1
            # Elle est déjà incluse dans total_defiscalisation_sim si tmi > 0
            economie_impot_per = (capital_initial_per + versement_per_annuel_brut) * tmi
        else:
            economie_impot_per = versement_per_annuel_brut * tmi
        valeur_per_sim = (valeur_per_sim + versement_per_annuel_net_de_frais) * (1 + rendement_per)
        total_defiscalisation_sim += economie_impot_per
        chart_economie_impot_per = economie_impot_per
        chart_versements_per = -versement_per_annuel_brut
        kpi_s_ep_per_brut_cum += versement_per_annuel_brut
        kpi_s_frais_entree_ep_cum += versement_per_annuel_brut * frais_entree_per
        kpi_s_ep_per_net_cum += versement_per_annuel_net_de_frais
        # Les intérêts sont calculés sur la valeur *avant* le nouveau versement et *avant* application du rendement de l'année
        # Pour simplifier, on prend la valeur de début d'année (après versement et rendement N-1) * rendement
        # ou valeur_per_sim (avant multiplication par (1+rendement_per)) * rendement_per
        kpi_s_int_per_cum += (valeur_per_sim / (1 + rendement_per) - versement_per_annuel_net_de_frais) * rendement_per if annee > 1 else s_cap_init_per_net * rendement_per

        # 2. GESTION DE L'ASSURANCE-VIE
        versement_av_annuel_brut = epargne_mensuelle_av * 12
        versement_av_annuel_net_de_frais = versement_av_annuel_brut * (1 - frais_entree_av)
        kpi_s_int_av_cum += (valeur_av_sim / (1 + rendement_av) - versement_av_annuel_net_de_frais) * rendement_av if annee > 1 else s_cap_init_av_net * rendement_av
        valeur_av_sim = (valeur_av_sim + versement_av_annuel_net_de_frais) * (1 + rendement_av)
        chart_versements_av = -versement_av_annuel_brut
        kpi_s_ep_av_brut_cum += versement_av_annuel_brut
        kpi_s_frais_entree_ep_cum += versement_av_annuel_brut * frais_entree_av
        kpi_s_ep_av_net_cum += versement_av_annuel_net_de_frais

        # 3. GESTION DE L'IMMOBILIER
        cashflow_net_immo_operationnel = 0
        annuite_immo = 0
        interets_immo_annee = 0
        if annee <= duree_credit_immo and montant_achat_immo > 0:
            annuite_immo = mensualite_immo_sim * 12
            interets_immo = solde_restant_du_immo_sim * taux_credit_immo
            capital_rembourse_immo = annuite_immo - interets_immo
            solde_restant_du_immo_sim = max(0, solde_restant_du_immo_sim - capital_rembourse_immo)
            loyers_immo = valeur_immo_sim * rendement_locatif_immo
            revenu_foncier_imposable = max(0, loyers_immo - interets_immo)
            impot_foncier = revenu_foncier_imposable * (tmi + taux_prelevements_sociaux_immo)
            cashflow_net_immo_operationnel = loyers_immo - annuite_immo - impot_foncier
            interets_immo_annee = interets_immo
            chart_annuite_immo = -annuite_immo
        elif montant_achat_immo > 0:
            loyers_immo = valeur_immo_sim * rendement_locatif_immo
            revenu_foncier_imposable = loyers_immo
            impot_foncier = revenu_foncier_imposable * (tmi + taux_prelevements_sociaux_immo)
            cashflow_net_immo_operationnel = loyers_immo - impot_foncier
        if montant_achat_immo > 0:
            kpi_s_loyers_immo_bruts_cum += loyers_immo
            kpi_s_int_emprunt_immo_cum += interets_immo_annee
            # total_impots_payes_levier_sim accumulera impot_foncier
            chart_revenus_immo_bruts = loyers_immo
            chart_impots_fonciers = -impot_foncier
        total_impots_payes_levier_sim += impot_foncier if montant_achat_immo > 0 else 0
        if cashflow_net_immo_operationnel > 0:
            total_cashflow_positif_levier_sim += cashflow_net_immo_operationnel
        kpi_s_revalo_immo_cum += valeur_immo_sim * revalorisation_immo # Revalo sur valeur avant application
        valeur_immo_sim *= (1 + revalorisation_immo)

        # 4. GESTION DES SCPI
        cashflow_net_scpi_operationnel = 0
        revenus_scpi_bruts_annuels = 0.0
        interets_scpi_annuels = 0.0
        annuite_credit_scpi_annuelle = 0.0
        impot_sur_revenus_scpi = 0
        if valeur_scpi_sim > 0:
            revenus_scpi_bruts_annuels = valeur_scpi_sim * rendement_scpi
            kpi_s_rev_scpi_bruts_cum += revenus_scpi_bruts_annuels
        if annee <= duree_credit_scpi and montant_emprunt_scpi > 0:
            annuite_credit_scpi_annuelle = mensualite_scpi_sim * 12
            interets_scpi_annuels = solde_restant_du_scpi_sim * taux_credit_scpi
            capital_rembourse_scpi = annuite_credit_scpi_annuelle - interets_scpi_annuels
            solde_restant_du_scpi_sim = max(0, solde_restant_du_scpi_sim - capital_rembourse_scpi)
            kpi_s_int_emprunt_scpi_cum += interets_scpi_annuels
        revenu_scpi_imposable = max(0, revenus_scpi_bruts_annuels - interets_scpi_annuels)
        impot_sur_revenus_scpi = revenu_scpi_imposable * (tmi + taux_prelevements_sociaux_scpi)
        if valeur_scpi_sim > 0:
            chart_revenus_scpi_bruts = revenus_scpi_bruts_annuels
            chart_impots_scpi = -impot_sur_revenus_scpi
            chart_annuite_scpi = -annuite_credit_scpi_annuelle
        # total_impots_payes_levier_sim accumulera impot_sur_revenus_scpi
        total_impots_payes_levier_sim += impot_sur_revenus_scpi if valeur_scpi_sim > 0 else 0
        cashflow_net_scpi_operationnel = revenus_scpi_bruts_annuels - annuite_credit_scpi_annuelle - impot_sur_revenus_scpi
        if cashflow_net_scpi_operationnel > 0:
            total_cashflow_positif_levier_sim += cashflow_net_scpi_operationnel
        
        epargne_dediee_scpi_annuelle = epargne_mensuelle_scpi_dediee * 12
        montant_effectivement_reinvesti_en_parts_scpi = 0
        if epargne_dediee_scpi_annuelle > 0:
            kpi_s_ep_scpi_reinv_cum += epargne_dediee_scpi_annuelle # On compte l'épargne brute dédiée
            if cashflow_net_scpi_operationnel >= 0:
                montant_effectivement_reinvesti_en_parts_scpi = epargne_dediee_scpi_annuelle
            else:
                deficit_operationnel_scpi = -cashflow_net_scpi_operationnel
                montant_effectivement_reinvesti_en_parts_scpi = max(0, epargne_dediee_scpi_annuelle - deficit_operationnel_scpi)
        valeur_scpi_sim += montant_effectivement_reinvesti_en_parts_scpi

        # 5. AGGREGATION ANNUELLE
        versement_immo_dedie_annuel = epargne_mensuelle_immo_dediee * 12 if montant_achat_immo > 0 else 0
        kpi_s_ep_immo_ded_cum += versement_immo_dedie_annuel
        chart_epargne_dediee_immo = -versement_immo_dedie_annuel
        chart_epargne_dediee_scpi = -epargne_dediee_scpi_annuelle
        effort_epargne_annuel_programme = versement_av_annuel_brut + versement_per_annuel_brut + versement_immo_dedie_annuel + epargne_dediee_scpi_annuelle
        total_effort_epargne_sim += effort_epargne_annuel_programme
        flux_net_annee = economie_impot_per + cashflow_net_immo_operationnel + cashflow_net_scpi_operationnel \
                         - versement_av_annuel_brut - versement_per_annuel_brut \
                         - versement_immo_dedie_annuel - epargne_dediee_scpi_annuelle
        flux_nets_annuels.append(flux_net_annee)
        patrimoine_brut = valeur_av_sim + valeur_per_sim + valeur_immo_sim + valeur_scpi_sim
        passif_total = max(0, solde_restant_du_immo_sim) + max(0, solde_restant_du_scpi_sim)
        patrimoine_net = patrimoine_brut - passif_total

        projection_data.append({
            "Année": annee, "Patrimoine Brut": patrimoine_brut, "Passif (Crédits)": passif_total,
            "Patrimoine Net": patrimoine_net, "Défiscalisation (PER)": economie_impot_per,
            "Cash-flow Net Annuel": flux_net_annee, "Valeur AV": valeur_av_sim, "Valeur PER": valeur_per_sim,
            "Valeur Immo": valeur_immo_sim, "Valeur SCPI": valeur_scpi_sim,
            "Solde Crédit Immo": solde_restant_du_immo_sim if montant_achat_immo > 0 else 0,
            "Solde Crédit SCPI": solde_restant_du_scpi_sim if montant_achat_scpi > 0 else 0,
            "CF_Revenus_Immo_Bruts": chart_revenus_immo_bruts, "CF_Revenus_SCPI_Bruts": chart_revenus_scpi_bruts,
            "CF_Economie_Impot_PER": chart_economie_impot_per, "CF_Versements_AV": chart_versements_av,
            "CF_Versements_PER": chart_versements_per, "CF_Annuite_Immo": chart_annuite_immo,
            "CF_Annuite_SCPI": chart_annuite_scpi, "CF_Impots_Fonciers": chart_impots_fonciers,
            "CF_Impots_SCPI": chart_impots_scpi, "CF_Epargne_Dediee_Immo": chart_epargne_dediee_immo,
            "CF_Epargne_Dediee_SCPI": chart_epargne_dediee_scpi,
        })

    df_projection = pd.DataFrame(projection_data)

    if not df_projection.empty:
        df_projection["Valeur Nette Immo"] = df_projection["Valeur Immo"] - df_projection["Solde Crédit Immo"]
        df_projection["Valeur Nette SCPI"] = df_projection["Valeur SCPI"] - df_projection["Solde Crédit SCPI"]
        patrimoine_net_final_sim = df_projection["Patrimoine Net"].iloc[-1]
        flux_nets_annuels[-1] += patrimoine_net_final_sim # Ajout pour le TRI
    else:
        patrimoine_net_final_sim = 0

    kpi_s_ep_period_total_net = kpi_s_ep_av_net_cum + kpi_s_ep_per_net_cum + kpi_s_ep_immo_ded_cum + kpi_s_ep_scpi_reinv_cum
    # Recalcul des impôts pour le Sankey (pour les avoir séparément si besoin)
    kpi_s_impots_immo_cum = sum(item.get('CF_Impots_Fonciers', 0) for item in projection_data) * -1 # car stockés en négatif
    kpi_s_impots_scpi_cum = sum(item.get('CF_Impots_SCPI', 0) for item in projection_data) * -1

    # Ajustement pour l'économie d'impôt sur capital initial PER si TMI > 0
    # total_defiscalisation_sim inclut déjà cela.
    # Pour les intérêts PER de la première année, si capital_initial_per > 0,
    # on a déjà calculé sur s_cap_init_per_net.
    # Pour les intérêts AV de la première année, si capital_initial_av > 0,
    # on a déjà calculé sur s_cap_init_av_net.
    # Correction pour la première année des intérêts si pas de capital initial
    if capital_initial_av == 0 : kpi_s_int_av_cum = max(0, kpi_s_int_av_cum) # Assurer non négatif si pas de capital et annee > 1 logique
    if capital_initial_per == 0 : kpi_s_int_per_cum = max(0, kpi_s_int_per_cum)

    tri_sim = npf.irr(flux_nets_annuels) if flux_nets_annuels and any(flux_nets_annuels) else 0.0

    kpis = {
        "patrimoine_net_final": patrimoine_net_final_sim,
        "tri": tri_sim,
        "total_effort_epargne": total_effort_epargne_sim,
        "total_defiscalisation": total_defiscalisation_sim,
        "total_cashflow_positif_levier": total_cashflow_positif_levier_sim,
        "total_impots_payes_levier": total_impots_payes_levier_sim,
        # KPIs pour Sankey
        "sankey_cap_init_av_brut": kpi_s_cap_init_av_brut,
        "sankey_cap_init_per_brut": kpi_s_cap_init_per_brut,
        "sankey_frais_entree_cap_init_cum": kpi_s_frais_entree_cap_init_cum,
        "sankey_cap_init_apport_immo_scpi": s_apport_immo_init + s_apport_scpi_init, # Apports directs non soumis à frais d'entrée AV/PER
        "sankey_cap_init_total_net": kpi_s_cap_init_total_net,
        "sankey_ep_period_total_net": kpi_s_ep_period_total_net,
        "sankey_int_av_cum": kpi_s_int_av_cum,
        "sankey_int_per_cum": kpi_s_int_per_cum,
        "sankey_loyers_immo_bruts_cum": kpi_s_loyers_immo_bruts_cum,
        "sankey_rev_scpi_bruts_cum": kpi_s_rev_scpi_bruts_cum,
        "sankey_revalo_immo_cum": kpi_s_revalo_immo_cum,
        "sankey_defisc_per_cum": total_defiscalisation_sim, # alias
        "sankey_int_emprunt_immo_cum": kpi_s_int_emprunt_immo_cum,
        "sankey_int_emprunt_scpi_cum": kpi_s_int_emprunt_scpi_cum,
        "sankey_impots_immo_cum": kpi_s_impots_immo_cum,
        "sankey_impots_scpi_cum": kpi_s_impots_scpi_cum,
        "sankey_ep_av_brut_cum": kpi_s_ep_av_brut_cum,
        "sankey_ep_per_brut_cum": kpi_s_ep_per_brut_cum,
        "sankey_frais_entree_ep_cum": kpi_s_frais_entree_ep_cum,
    }
    return df_projection, kpis


# --- FONCTIONS D'AFFICHAGE DES GRAPHIQUES ET TABLEAUX ---
def afficher_evolution_patrimoine(df_projection, titre_suffix=""):
    """Affiche le graphique d'évolution du patrimoine."""
    if not df_projection.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_projection["Année"], y=df_projection["Patrimoine Brut"], name="Patrimoine Brut", fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df_projection["Année"], y=df_projection["Patrimoine Net"], name="Patrimoine Net", fill='tonexty'))
        fig.add_trace(go.Scatter(x=df_projection["Année"], y=df_projection["Passif (Crédits)"], name="Passif (Crédits)"))
        fig.update_layout(
            title_text=f"Évolution du Patrimoine Brut, Net et du Passif {titre_suffix}",
            xaxis_title="Années",
            yaxis_title="Montant (€)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

def afficher_composition_patrimoine(df_projection, titre_suffix=""):
    """Affiche le graphique de composition du patrimoine net."""
    if not df_projection.empty:
        fig_composition_patrimoine = go.Figure()
        patrimoine_components = {
            "Valeur AV": ("Assurance-Vie", "skyblue"), "Valeur PER": ("PER", "lightcoral"),
            "Valeur Nette Immo": ("Immobilier Net", "mediumseagreen"), "Valeur Nette SCPI": ("SCPI Nettes", "goldenrod"),
        }
        for col_name, (trace_name, color) in patrimoine_components.items():
            if col_name in df_projection.columns and df_projection[col_name].abs().sum() != 0:
                fig_composition_patrimoine.add_trace(go.Bar(name=trace_name, x=df_projection["Année"], y=df_projection[col_name], marker_color=color))
        fig_composition_patrimoine.add_trace(go.Scatter(name='Patrimoine Net Total',x=df_projection["Année"], y=df_projection["Patrimoine Net"], mode='lines+markers', line=dict(color='black', dash='dash', width=2)))
        fig_composition_patrimoine.update_layout(
            barmode='stack', 
            title_text=f"Évolution de la Composition du Patrimoine Net {titre_suffix}", 
            xaxis_title="Années", 
            yaxis_title="Montant (€)", 
            hovermode="x unified"
        )
        st.plotly_chart(fig_composition_patrimoine, use_container_width=True)

def afficher_evolution_flux_tresorerie(df_projection, titre_suffix=""):
    """Affiche le graphique des flux de trésorerie annuels."""
    if not df_projection.empty:
        fig_cashflows = go.Figure()
        cf_components = {
            "CF_Revenus_Immo_Bruts": ("Revenus Immo Bruts", "mediumseagreen"), "CF_Revenus_SCPI_Bruts": ("Revenus SCPI Bruts", "lightgreen"),
            "CF_Economie_Impot_PER": ("Économie Impôt PER", "cornflowerblue"), "CF_Versements_AV": ("Versements AV", "salmon"),
            "CF_Versements_PER": ("Versements PER", "indianred"), "CF_Annuite_Immo": ("Annuité Crédit Immo", "orange"),
            "CF_Annuite_SCPI": ("Annuité Crédit SCPI", "darkorange"), "CF_Impots_Fonciers": ("Impôts Fonciers", "mediumpurple"),
            "CF_Impots_SCPI": ("Impôts SCPI", "plum"), "CF_Epargne_Dediee_Immo": ("Épargne Dédiée Immo", "silver"),
            "CF_Epargne_Dediee_SCPI": ("Épargne Dédiée SCPI", "lightgrey"),
        }
        for col_name, (trace_name, color) in cf_components.items():
            if col_name in df_projection.columns and df_projection[col_name].abs().sum() != 0:
                fig_cashflows.add_trace(go.Bar(name=trace_name, x=df_projection["Année"], y=df_projection[col_name], marker_color=color))
        fig_cashflows.add_trace(go.Scatter(name='Cash-flow Net Annuel (Total)', x=df_projection["Année"], y=df_projection["Cash-flow Net Annuel"], mode='lines+markers', line=dict(color='black', dash='dash', width=2)))
        fig_cashflows.update_layout(
            barmode='relative', 
            title_text=f"Ventilation des Flux de Trésorerie Annuels {titre_suffix}", 
            xaxis_title="Années", 
            yaxis_title="Montant (€)", 
            hovermode="x unified"
        )
        st.plotly_chart(fig_cashflows, use_container_width=True)

def afficher_tableau_detaille(df_projection):
    """Affiche le DataFrame détaillé de la projection."""
    if not df_projection.empty:
        st.dataframe(df_projection.style.format({
            "Patrimoine Brut": "{:,.0f} €", "Passif (Crédits)": "{:,.0f} €", "Patrimoine Net": "{:,.0f} €",
            "Défiscalisation (PER)": "{:,.0f} €", "Cash-flow Net Annuel": "{:,.0f} €", "Valeur AV": "{:,.0f} €",
            "Valeur PER": "{:,.0f} €", "Valeur Immo": "{:,.0f} €", "Valeur SCPI": "{:,.0f} €",
            "Solde Crédit Immo": "{:,.0f} €", "Solde Crédit SCPI": "{:,.0f} €", "Valeur Nette Immo": "{:,.0f} €",
            "Valeur Nette SCPI": "{:,.0f} €", "CF_Revenus_Immo_Bruts": "{:,.0f} €", "CF_Revenus_SCPI_Bruts": "{:,.0f} €",
            "CF_Economie_Impot_PER": "{:,.0f} €", "CF_Versements_AV": "{:,.0f} €", "CF_Versements_PER": "{:,.0f} €",
            "CF_Annuite_Immo": "{:,.0f} €", "CF_Annuite_SCPI": "{:,.0f} €", "CF_Impots_Fonciers": "{:,.0f} €",
            "CF_Impots_SCPI": "{:,.0f} €", "CF_Epargne_Dediee_Immo": "{:,.0f} €", "CF_Epargne_Dediee_SCPI": "{:,.0f} €",
        }))

def afficher_sankey_composition_patrimoine(kpis, patrimoine_net_final_ref):
    """Affiche le diagramme de Sankey pour la composition du patrimoine final."""
    
    # Définition des labels des nœuds
    sankey_labels = [
        "Capital Initial Brut (AV/PER)",    # 0
        "Apports Initiaux (Immo/SCPI)",     # 1
        "Épargnes Périodiques Brutes (AV/PER)",# 2
        "Épargnes Dédiées (Immo/SCPI)",     # 3
        "Frais d'Entrée Totaux",            # 4 
        "Effort d'Épargne Total",           # 5 
        "Intérêts AV",                      # 6
        "Intérêts PER",                     # 7
        "Loyers Immo Bruts",                # 8
        "Revenus SCPI Bruts",               # 9
        "Revalorisation Immo",              # 10
        "Défiscalisation PER",              # 11
        "Total Contributions Brutes",       # 12 
        "Intérêts Emprunt Immo",            # 13 
        "Intérêts Emprunt SCPI",            # 14 
        "Impôts Immo",                      # 15 
        "Impôts SCPI",                      # 16 
        "Patrimoine Net Final",             # 17
        "Économie d'Impôt Réalisée"         # 18 
    ]

    # Récupération des valeurs des KPIs
    v_cap_init_av_brut = kpis.get("sankey_cap_init_av_brut", 0)
    v_cap_init_per_brut = kpis.get("sankey_cap_init_per_brut", 0)
    v_cap_init_brut_av_per = v_cap_init_av_brut + v_cap_init_per_brut
    v_apports_immo_scpi = kpis.get("sankey_cap_init_apport_immo_scpi", 0)
    v_frais_cap_init = kpis.get("sankey_frais_entree_cap_init_cum", 0)
    v_cap_init_net_av_per_calc = v_cap_init_brut_av_per - v_frais_cap_init # Valeur pour flux, pas un nœud

    v_ep_av_brut = kpis.get("sankey_ep_av_brut_cum", 0)
    v_ep_per_brut = kpis.get("sankey_ep_per_brut_cum", 0)
    v_ep_brut_av_per = v_ep_av_brut + v_ep_per_brut
    v_ep_dediees_immo_scpi = kpis.get("sankey_ep_immo_ded_cum", 0) + kpis.get("sankey_ep_scpi_reinv_cum", 0)
    v_frais_ep = kpis.get("sankey_frais_entree_ep_cum", 0)
    v_ep_net_av_per_calc = v_ep_brut_av_per - v_frais_ep # Valeur pour flux, pas un nœud

    v_int_av = kpis.get("sankey_int_av_cum", 0)
    v_int_per = kpis.get("sankey_int_per_cum", 0)
    v_loyers_immo = kpis.get("sankey_loyers_immo_bruts_cum", 0)
    v_rev_scpi = kpis.get("sankey_rev_scpi_bruts_cum", 0)
    v_revalo_immo = kpis.get("sankey_revalo_immo_cum", 0)
    v_defisc_per = kpis.get("sankey_defisc_per_cum", 0)
    # Coûts
    v_int_emp_immo = kpis.get("sankey_int_emprunt_immo_cum", 0)
    v_int_emp_scpi = kpis.get("sankey_int_emprunt_scpi_cum", 0)
    v_impots_immo = kpis.get("sankey_impots_immo_cum", 0)
    v_impots_scpi = kpis.get("sankey_impots_scpi_cum", 0)
    pnf_display_value = patrimoine_net_final_ref
    # Construction des flux (sources, cibles, valeurs)
    s_sources, s_targets, s_values = [], [], []

    idx_cap_init_brut_av_per = 0
    idx_apports_immo_scpi = 1
    idx_ep_brut_av_per = 2
    idx_ep_dediees_immo_scpi = 3
    idx_frais_entree_totaux = 4
    idx_effort_epargne_total = 5
    idx_int_av = 6; idx_int_per = 7; idx_loyers_immo = 8; idx_rev_scpi = 9;
    idx_revalo_immo = 10; idx_defisc_per = 11;
    idx_total_contrib_brutes = 12
    idx_int_emp_immo = 13; idx_int_emp_scpi = 14; idx_impots_immo = 15; idx_impots_scpi = 16;
    idx_pnf = 17; idx_eco_impot_realisee = 18;

    # Définition des positions x et y pour chaque nœud pour contrôler la mise en page
    # x positions:
    # Column 1: Sources Brutes (Cap Brut AV/PER, Apports Immo/SCPI, Ep Brutes AV/PER, Ep Dédiées Immo/SCPI)
    # Column 2: Frais d'Entrée, Effort d'Épargne Total, Autres Revenus (Intérêts, Loyers etc.)
    # Column 3: Total Contributions Brutes
    # Column 4: Coûts et Patrimoine Net Final
    node_x_positions = [
        0.01, # 0: Cap Initial Brut AV/PER
        0.01, # 1: Apports Initiaux Immo/SCPI
        0.01, # 2: Ep Périodiques Brutes AV/PER
        0.01, # 3: Ep Dédiées Immo/SCPI
        0.25, # 4: Frais d'Entrée Totaux
        0.25, # 5: Effort d'Épargne Total
        0.25, # 6: Intérêts AV
        0.25, # 7: Intérêts PER
        0.25, # 8: Loyers Immo Bruts
        0.25, # 9: Revenus SCPI Bruts
        0.25, # 10: Revalorisation Immo
        0.25, # 11: Défiscalisation PER
        0.60, # 12: Total Contributions Brutes
        0.99, # 13: Intérêts Emprunt Immo
        0.99, # 14: Intérêts Emprunt SCPI
        0.99, # 15: Impôts Immo
        0.99, # 16: Impôts SCPI
        0.99, # 17: Patrimoine Net Final
        0.99  # 18: Économie d'Impôt Réalisée
    ]

    node_y_positions = [
        # Col 1 (x=0.01)
        0.05, # 0: Cap Initial Brut AV/PER
        0.25, # 1: Apports Initiaux Immo/SCPI
        0.45, # 2: Ep Périodiques Brutes AV/PER
        0.65, # 3: Ep Dédiées Immo/SCPI
        # Col 2 (x=0.25)
        0.05, # 4: Frais d'Entrée Totaux (en haut)
        0.25, # 5: Effort d'Épargne Total
        0.45, # 6: Intérêts AV
        0.55, # 7: Intérêts PER
        0.65, # 8: Loyers Immo Bruts
        0.75, # 9: Revenus SCPI Bruts
        0.85, # 10: Revalorisation Immo
        0.95, # 11: Défiscalisation PER
        # Col 3 (x=0.60)
        0.5,  # 12: Total Contributions Brutes (centré)
        # Col 4 (x=0.99)
        0.05, 0.20, 0.35, 0.50, 0.70, 0.95 # Coûts, PNF, et Éco Impôt
    ]

    # 1. Flux du Capital Initial Brut (AV/PER) vers Frais ET vers Effort d'Épargne
    if abs(v_cap_init_brut_av_per) > 1e-1:
        if abs(v_frais_cap_init) > 1e-1:
            s_sources.append(idx_cap_init_brut_av_per); s_targets.append(idx_frais_entree_totaux); s_values.append(v_frais_cap_init)
        # Le reste (net de frais) va à l'effort d'épargne
        if abs(v_cap_init_net_av_per_calc) > 1e-1:
            s_sources.append(idx_cap_init_brut_av_per); s_targets.append(idx_effort_epargne_total); s_values.append(v_cap_init_net_av_per_calc)

    # 2. Flux des Épargnes Périodiques Brutes (AV/PER) vers Frais ET vers Effort d'Épargne
    if abs(v_ep_brut_av_per) > 1e-1:
        if abs(v_frais_ep) > 1e-1:
            s_sources.append(idx_ep_brut_av_per); s_targets.append(idx_frais_entree_totaux); s_values.append(v_frais_ep)
        # Le reste (net de frais) va à l'effort d'épargne
        if abs(v_ep_net_av_per_calc) > 1e-1:
            s_sources.append(idx_ep_brut_av_per); s_targets.append(idx_effort_epargne_total); s_values.append(v_ep_net_av_per_calc)

    # 3. Flux des Apports/Épargnes directs (Immo/SCPI) vers "Effort d'Épargne Total"
    if abs(v_apports_immo_scpi) > 1e-1: # Apports directs Immo/SCPI vont à l'effort total
        s_sources.append(idx_apports_immo_scpi); s_targets.append(idx_effort_epargne_total); s_values.append(v_apports_immo_scpi)
    if abs(v_ep_dediees_immo_scpi) > 1e-1: # Épargnes dédiées Immo/SCPI vont à l'effort total
        s_sources.append(idx_ep_dediees_immo_scpi); s_targets.append(idx_effort_epargne_total); s_values.append(v_ep_dediees_immo_scpi)

    # 4. Flux de "Effort d'Épargne Total" et autres revenus vers "Total Contributions Brutes"
    val_effort_epargne_flux_sortant = (v_cap_init_net_av_per_calc if abs(v_cap_init_net_av_per_calc) > 1e-1 else 0) + \
                                      (v_apports_immo_scpi if abs(v_apports_immo_scpi) > 1e-1 else 0) + \
                                      (v_ep_net_av_per_calc if abs(v_ep_net_av_per_calc) > 1e-1 else 0) + \
                                      (v_ep_dediees_immo_scpi if abs(v_ep_dediees_immo_scpi) > 1e-1 else 0)
    if abs(val_effort_epargne_flux_sortant) > 1e-1:
        s_sources.append(idx_effort_epargne_total); s_targets.append(idx_total_contrib_brutes); s_values.append(val_effort_epargne_flux_sortant)

    other_contributions_map = {
        idx_int_av: v_int_av, idx_int_per: v_int_per, idx_loyers_immo: v_loyers_immo,
        idx_rev_scpi: v_rev_scpi, idx_revalo_immo: v_revalo_immo, idx_defisc_per: v_defisc_per
    }
    for source_idx, value in other_contributions_map.items():
        if abs(value) > 1e-1:
            s_sources.append(source_idx); s_targets.append(idx_total_contrib_brutes); s_values.append(value)

    # 5. Flux de "Total Contributions Brutes" vers les coûts et le Patrimoine Net Final
    costs_pnf_map = {
        idx_int_emp_immo: v_int_emp_immo, 
        idx_int_emp_scpi: v_int_emp_scpi,
        idx_impots_immo: v_impots_immo, 
        idx_impots_scpi: v_impots_scpi, 
        idx_pnf: pnf_display_value,
        idx_eco_impot_realisee: v_defisc_per # Le montant de la défiscalisation sort ici
    }
    for target_idx, value in costs_pnf_map.items():
        if abs(value) > 1e-1:
            s_sources.append(idx_total_contrib_brutes)
            s_targets.append(target_idx)
            s_values.append(value)
    # Filtrer les flux nuls ou négligeables pour la lisibilité
    # Ce filtrage est maintenant fait lors de la construction des listes s_sources, s_targets, s_values
    
    if not s_values: # Si aucune valeur significative après filtrage
        st.info("Pas de données suffisantes pour générer le diagramme de Sankey.")
        return

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=sankey_labels,
            x=node_x_positions,
            y=node_y_positions
        ),
        link=dict(
            source=s_sources,
            target=s_targets,
            value=s_values
        ),
        textfont=dict(color="black", size=11) # Amélioration de la lisibilité du texte des nœuds
    )])
    fig.update_layout(
        title_text="Composition du Patrimoine Net Final (Flux Approximatifs)", 
        font_size=10,
        margin=dict(l=10, r=100, b=10, t=50)  # Augmentation de la marge à droite (r=100)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Création du tableau des valeurs des nœuds
    st.markdown("##### Détail des Valeurs des Nœuds du Diagramme de Sankey")

    # Calcul de la valeur du nœud "Effort d'Épargne Total" (somme de ses entrées)
    val_effort_epargne_total_node = val_effort_epargne_flux_sortant # Réutiliser le calcul du flux sortant

    # Calcul de la valeur du nœud "Total Contributions Brutes" (somme de ses entrées)
    val_total_contrib_brutes_node = val_effort_epargne_total_node + \
                                    (v_int_av if abs(v_int_av) > 1e-1 else 0) + \
                                    (v_int_per if abs(v_int_per) > 1e-1 else 0) + \
                                    (v_loyers_immo if abs(v_loyers_immo) > 1e-1 else 0) + \
                                    (v_rev_scpi if abs(v_rev_scpi) > 1e-1 else 0) + \
                                    (v_revalo_immo if abs(v_revalo_immo) > 1e-1 else 0) + \
                                    (v_defisc_per if abs(v_defisc_per) > 1e-1 else 0)
    
    # Calcul de la valeur du nœud "Frais d'Entrée Totaux"
    val_frais_entree_totaux_node = (v_frais_cap_init if abs(v_frais_cap_init) > 1e-1 else 0) + \
                                   (v_frais_ep if abs(v_frais_ep) > 1e-1 else 0)

    node_values_data = {
        "Nœud": sankey_labels,
        "Valeur (€)": [
            v_cap_init_brut_av_per,         # 0
            v_apports_immo_scpi,            # 1
            v_ep_brut_av_per,               # 2
            v_ep_dediees_immo_scpi,         # 3
            val_frais_entree_totaux_node,   # 4
            val_effort_epargne_total_node,  # 5
            v_int_av,                       # 6
            v_int_per,                      # 7
            v_loyers_immo,                  # 8
            v_rev_scpi,                     # 9
            v_revalo_immo,                  # 10
            v_defisc_per,                   # 11
            val_total_contrib_brutes_node,
            v_int_emp_immo, v_int_emp_scpi, v_impots_immo, v_impots_scpi, # 13-16
            pnf_display_value,
            v_defisc_per # Valeur pour "Économie d'Impôt Réalisée"
        ]
    }
    df_node_values = pd.DataFrame(node_values_data)
    # Filtrer les lignes où la valeur est très proche de zéro pour la lisibilité, sauf pour les nœuds agrégateurs
    # df_node_values_display = df_node_values[ (df_node_values["Valeur (€)"].abs() > 1e-1) | \
    #                                          (df_node_values["Nœud"].isin(["Effort d'Épargne Total", "Total Contributions Brutes"])) ]
    
    st.dataframe(df_node_values.style.format({"Valeur (€)": "{:,.0f} €"}), use_container_width=True)



# --- Définition des onglets ---
tab1, tab2 = st.tabs([" Simulateur Patrimonial ", " Optimiseur d'Allocation "])

with tab1:
    st.header("🚀 Simulateur de Projection Patrimoniale")
    # Appel de la fonction de simulation pour l'onglet Simulateur
    df_projection_sim, kpis_sim = simuler_projection_patrimoniale(
        horizon_projection, tmi,
        capital_initial_av, epargne_mensuelle_av, rendement_av, frais_entree_av_pct,
        capital_initial_per, epargne_mensuelle_per, rendement_per, frais_entree_per_pct,
        apport_initial_immo, montant_emprunt_immo, duree_credit_immo,
        rendement_locatif_immo, revalorisation_immo, taux_credit_immo, taux_prelevements_sociaux_immo,
        epargne_mensuelle_immo_dediee,
        apport_initial_scpi, montant_emprunt_scpi, duree_credit_scpi,
        rendement_scpi, taux_credit_scpi, taux_prelevements_sociaux_scpi,
        epargne_mensuelle_scpi_dediee
    )

    st.markdown("---")
    st.header("📊 Indicateurs Clés à l'Horizon de {} ans".format(horizon_projection))

    col1_1, col1_2, col1_3 = st.columns(3)
    col1_1.metric("Patrimoine Net Final", f"{kpis_sim['patrimoine_net_final']:,.0f} €", delta=None)
    col1_2.metric("TRI (Taux de Rendement Interne)", f"{kpis_sim['tri']:.2%}" if kpis_sim['tri'] is not None else "N/A", delta=None)
    col1_3.metric("Capital Total Investi", f"{kpis_sim['total_effort_epargne']:,.0f} €", help="Capitaux initiaux (AV/PER/Immo/SCPI) + épargnes mensuelles programmées (AV/PER) + épargnes mensuelles dédiées (Immobilier/SCPI).")

    col2_1, col2_2, col2_3 = st.columns(3)
    col2_1.metric("Défiscalisation Totale (PER)", f"{kpis_sim['total_defiscalisation']:,.0f} €")
    col2_2.metric("Cash-Flows Positifs Cumulés (Immo/SCPI)", f"{kpis_sim['total_cashflow_positif_levier']:,.0f} €", help="Somme de tous les cash-flows annuels positifs générés par l'immobilier et les SCPI, avant prise en compte de l'épargne dédiée.")
    col2_3.metric("Total Impôts Payés (Immo/SCPI)", f"{kpis_sim['total_impots_payes_levier']:,.0f} €", help="Somme de tous les impôts (IR + PS) payés sur les revenus de l'immobilier locatif et des SCPI.")

    st.markdown("---")
    
    st.header("📉 Évolution du Patrimoine")
    afficher_evolution_patrimoine(df_projection_sim)

    st.header("🏛️ Composition du Patrimoine Net par Investissement")
    afficher_composition_patrimoine(df_projection_sim)

    st.header("📊 Évolution des Flux de Trésorerie Annuels")
    afficher_evolution_flux_tresorerie(df_projection_sim)

    st.header("🔢 Tableau de Projection Détaillé")
    afficher_tableau_detaille(df_projection_sim)
    
    st.header("🌊 Diagramme de Sankey : Composition du Patrimoine Final")
    afficher_sankey_composition_patrimoine(kpis_sim, kpis_sim['patrimoine_net_final'])

    st.info("""
    **Avertissement :** Ce simulateur est un outil pédagogique basé sur des hypothèses simplifiées.
    - La fiscalité (plus-values à la sortie, abattements, distinction revenus financiers SCPI vs revenus fonciers, régime micro-foncier...) est volontairement simplifiée.
    - Les prélèvements sociaux sont appliqués sur les revenus fonciers (Immobilier et SCPI) nets d'intérêts d'emprunt, selon les taux spécifiques saisis.
    - Les rendements et taux sont fixes sur toute la période, ce qui ne reflète pas la volatilité des marchés.
    - Il ne constitue pas un conseil en investissement. Une analyse personnalisée avec un professionnel est indispensable.
    """)

with tab2:
    st.header("⚙️ Optimiseur d'Allocation Patrimoniale")
    st.write("Cette section permettra d'optimiser l'allocation de votre capital et de votre épargne.")

    # Initialisation des variables qui pourraient être conditionnellement affichées ou modifiées
    montant_acquisition_immo_fixe_opt = 0
    montant_acquisition_scpi_fixe_opt = 0
    mode_acquisition_immo_opt = "Fixés par l'utilisateur" # Valeur par défaut
    mode_acquisition_scpi_opt = "Fixés par l'utilisateur" # Valeur par défaut

    # --- Inputs pour l'Optimiseur ---
    st.subheader("Paramètres d'Optimisation")
    col_opt1, col_opt2 = st.columns(2)

    with col_opt1:
        st.markdown("##### Objectifs Globaux")
        capital_a_allouer_opt = st.number_input("Capital total à allouer (€)", min_value=0, value=100000, step=10000, key="cap_alloc_opt")
        epargne_mensuelle_a_allouer_opt = st.number_input("Épargne mensuelle totale à allouer (€)", min_value=0, value=1000, step=100, key="ep_alloc_opt")
        capacite_endettement_mensuelle_opt = st.number_input("Capacité d'endettement mensuelle max (€)", min_value=0, value=1500, step=100, key="debt_cap_opt")
        
        st.markdown("##### Sélection des Investissements")
        investissements_a_optimiser = st.multiselect(
            "Investissements à inclure",
            options=["AV", "PER", "Immo", "SCPI"],
            default=["AV", "PER", "Immo", "SCPI"],
            key="inv_optim_select"
        )

    with col_opt2:
        st.markdown("##### Contraintes Spécifiques PER")
        versement_max_initial_per_opt = st.number_input("Plafond versement initial PER (sur capital) (€)", min_value=0, value=10000, step=1000, key="max_init_per_opt")
        versement_max_per_annuel_opt = st.number_input("Plafond versement annuel PER (sur épargne) (€)", min_value=0, value=15000, step=1000, key="max_per_opt")

        st.markdown("---")
        st.markdown("##### Paramètres d'Acquisition Immobilière")
        if "Immo" in investissements_a_optimiser:
            mode_acquisition_immo_opt = st.radio(
                "Mode d'acquisition Immobilier :",
                options=["Fixés par l'utilisateur", "Optimisés par l'algorithme"],
                index=0, 
                key="mode_acq_immo_opt",
                # help="Choisissez si le montant d'acquisition est fixé ou optimisé."
            )
            if mode_acquisition_immo_opt == "Fixés par l'utilisateur":
                montant_acquisition_immo_fixe_opt = st.number_input(
                    "Montant acquisition Immobilier (si fixé) (€)", 
                    min_value=0, value=150000, step=10000, key="acq_immo_fixe_opt", 
                    help="Ce montant sera utilisé si le mode d'acquisition est 'Fixés par l'utilisateur'."
                )
        
        st.markdown("---")
        st.markdown("##### Paramètres d'Acquisition SCPI")
        if "SCPI" in investissements_a_optimiser:
            mode_acquisition_scpi_opt = st.radio(
                "Mode d'acquisition SCPI :",
                options=["Fixés par l'utilisateur", "Optimisés par l'algorithme"],
                index=0, 
                key="mode_acq_scpi_opt",
                # help="Choisissez si le montant d'acquisition est fixé ou optimisé."
            )
            if mode_acquisition_scpi_opt == "Fixés par l'utilisateur":
                montant_acquisition_scpi_fixe_opt = st.number_input(
                    "Montant acquisition SCPI (si fixé) (€)", 
                    min_value=0, value=50000, step=5000, key="acq_scpi_fixe_opt", 
                    help="Ce montant sera utilisé si le mode d'acquisition est 'Fixés par l'utilisateur'."
                )

    st.markdown("---")
    
    # Les durées de crédit pour l'optimisation sont maintenant reprises de la sidebar principale (duree_credit_immo, duree_credit_scpi)
    # st.markdown("###### Paramètres de crédit pour l'optimisation")
    # duree_credit_immo_opt = st.slider("Durée crédit immobilier pour optimisation (années)", 5, 30, 20, key="duree_immo_opt")
    # duree_credit_scpi_opt = st.slider("Durée crédit SCPI pour optimisation (années)", 5, 30, 15, key="duree_scpi_opt")

    # Les hypothèses de marché (rendements, taux, etc.) sont reprises de la sidebar principale pour l'instant.
    # horizon_projection et tmi sont également repris de la sidebar.

    # --- Fonction Objectif pour l'Optimiseur ---
    def objectif_optimisation(x_opt, # Vecteur des variables d'optimisation
                              # Paramètres fixes passés via args
                              horizon_p, tmi_p,
                              glob_rendement_av, glob_frais_entree_av_pct,
                              glob_rendement_per, glob_frais_entree_per_pct,
                              glob_rendement_locatif_immo, glob_revalorisation_immo,
                              glob_taux_credit_immo, glob_taux_prelevements_sociaux_immo,
                              glob_duree_credit_immo_sidebar, 
                              glob_rendement_scpi, glob_taux_credit_scpi,
                              glob_taux_prelevements_sociaux_scpi,
                              glob_duree_credit_scpi_sidebar,
                              glob_montant_acq_immo_fixe_input, glob_montant_acq_scpi_fixe_input, # Inputs utilisateur
                              glob_mode_acq_immo, glob_mode_acq_scpi, # Modes d'optimisation
                              glob_investissements_a_optimiser # Liste des investissements sélectionnés
                             ):
        # x_opt = [cap_av, cap_per, app_immo, app_scpi, ep_av, ep_per, ep_ded_immo, ep_ded_scpi, acq_immo_var, acq_scpi_var]
        cap_av, cap_per, app_immo, app_scpi, ep_av, ep_per, ep_ded_immo, ep_ded_scpi, acq_immo_var, acq_scpi_var = x_opt

        montant_acq_immo_a_utiliser = 0
        if "Immo" in glob_investissements_a_optimiser:
            if glob_mode_acq_immo == "Optimisés par l'algorithme":
                montant_acq_immo_a_utiliser = acq_immo_var
            else: # "Fixés par l'utilisateur"
                montant_acq_immo_a_utiliser = glob_montant_acq_immo_fixe_input

        montant_acq_scpi_a_utiliser = 0
        if "SCPI" in glob_investissements_a_optimiser:
            if glob_mode_acq_scpi == "Optimisés par l'algorithme":
                montant_acq_scpi_a_utiliser = acq_scpi_var
            else: # "Fixés par l'utilisateur"
                montant_acq_scpi_a_utiliser = glob_montant_acq_scpi_fixe_input
        
        # Si l'investissement n'est pas sélectionné, l'acquisition doit être 0, et donc l'emprunt aussi.
        # Les bornes (0,0) pour app_immo/app_scpi et acq_immo_var/acq_scpi_var gèrent cela en amont.
        # Si montant_acq_xxx_a_utiliser est 0, alors l'emprunt sera 0.
        montant_emprunt_immo_calc = max(0, montant_acq_immo_a_utiliser - app_immo)
        montant_emprunt_scpi_calc = max(0, montant_acq_scpi_a_utiliser - app_scpi)

        _, kpis_res = simuler_projection_patrimoniale(
            horizon_projection=horizon_p, tmi=tmi_p,
            capital_initial_av=cap_av, epargne_mensuelle_av=ep_av, rendement_av=glob_rendement_av, frais_entree_av_pct=glob_frais_entree_av_pct,
            capital_initial_per=cap_per, epargne_mensuelle_per=ep_per, rendement_per=glob_rendement_per, frais_entree_per_pct=glob_frais_entree_per_pct,
            # simuler_projection_patrimoniale calcule montant_achat_immo = apport + emprunt.
            # Donc, on passe app_immo et montant_emprunt_immo_calc.
            apport_initial_immo=app_immo, montant_emprunt_immo=montant_emprunt_immo_calc, duree_credit_immo=glob_duree_credit_immo_sidebar,
            rendement_locatif_immo=glob_rendement_locatif_immo, revalorisation_immo=glob_revalorisation_immo,
            taux_credit_immo=glob_taux_credit_immo, taux_prelevements_sociaux_immo=glob_taux_prelevements_sociaux_immo,
            epargne_mensuelle_immo_dediee=ep_ded_immo,
            apport_initial_scpi=app_scpi, montant_emprunt_scpi=montant_emprunt_scpi_calc, duree_credit_scpi=glob_duree_credit_scpi_sidebar,
            rendement_scpi=glob_rendement_scpi, taux_credit_scpi=glob_taux_credit_scpi,
            taux_prelevements_sociaux_scpi=glob_taux_prelevements_sociaux_scpi,
            epargne_mensuelle_scpi_dediee=ep_ded_scpi
        )
        final_net_worth = kpis_res.get('patrimoine_net_final', -float('inf')) # Pénaliser si non trouvé
        if final_net_worth is None: final_net_worth = -float('inf')
        return -final_net_worth # Minimiser l'opposé pour maximiser

    # --- Fonctions de Contrainte ---
    # x_opt = [cap_av, cap_per, app_immo, app_scpi, ep_av, ep_per, ep_ded_immo, ep_ded_scpi, acq_immo_var, acq_scpi_var]
    # Indices:   0       1        2         3         4       5        6            7            8             9
    
    # Rappel de la structure des arguments globaux (args_objectif) passés aux contraintes :
    # (horizon_p, tmi_p, rend_av, frais_av, rend_per, frais_per,
    #  rend_loc_immo, reval_immo, tx_cred_immo, ps_immo, dur_cred_immo_sidebar,
    #  rend_scpi, tx_cred_scpi, ps_scpi, dur_cred_scpi_sidebar,
    #  montant_acq_immo_fixe_input, montant_acq_scpi_fixe_input, (indices 15, 16)
    #  mode_acq_immo_opt_val, mode_acq_scpi_opt_val, investissements_a_optimiser_val) (indices 17, 18, 19)
    # Les arguments spécifiques à la contrainte sont ajoutés à la fin de ce tuple.

    def contrainte_capital_total(x_opt, 
                                 # Global args (unpack from *args_objectif in minimize call)
                                 p_horizon, p_tmi, p_rend_av, p_frais_av, p_rend_per, p_frais_per,
                                 p_rend_loc_immo, p_reval_immo, p_tx_cred_immo, p_ps_immo, p_dur_cred_immo_o,
                                 p_rend_scpi, p_tx_cred_scpi, p_ps_scpi, p_dur_cred_scpi_o,
                                 p_montant_acq_immo_fixe_in, p_montant_acq_scpi_fixe_in, p_mode_acq_immo, p_mode_acq_scpi, p_inv_opt_list,
                                 # Constraint-specific args
                                 capital_alloc_opt_specific):
        cap_av = x_opt[0]
        cap_per_brut = x_opt[1]
        app_immo = x_opt[2]
        app_scpi = x_opt[3]
        
        # Capital PER net de la défiscalisation initiale
        cap_per_net = cap_per_brut * (1 - p_tmi)
        
        total_capital_engage_net = cap_av + cap_per_net + app_immo + app_scpi
        return capital_alloc_opt_specific - total_capital_engage_net

    def contrainte_epargne_totale(x_opt, 
                                  # Global args
                                  p_horizon, p_tmi, p_rend_av, p_frais_av, p_rend_per, p_frais_per,
                                  p_rend_loc_immo, p_reval_immo, p_tx_cred_immo, p_ps_immo, p_dur_cred_immo_o,
                                  p_rend_scpi, p_tx_cred_scpi, p_ps_scpi, p_dur_cred_scpi_o,
                                  p_montant_acq_immo_fixe_in, p_montant_acq_scpi_fixe_in, p_mode_acq_immo, p_mode_acq_scpi, p_inv_opt_list,
                                  # Constraint-specific args
                                  epargne_alloc_opt_specific):
        ep_av_brut = x_opt[4]
        ep_per_brut = x_opt[5]
        ep_ded_immo_brut = x_opt[6]
        ep_ded_scpi_brut = x_opt[7]

        somme_epargnes_programmees_brutes = ep_av_brut + ep_per_brut + ep_ded_immo_brut + ep_ded_scpi_brut
        gain_fiscal_per_mensuel = ep_per_brut * p_tmi

        # Estimation du cash-flow net mensuel Immo (année 1)
        acq_immo_var_from_x = x_opt[8]
        app_immo = x_opt[2]
        cf_net_mensuel_immo = 0
        montant_acq_immo_a_utiliser_contrainte = 0
        if "Immo" in p_inv_opt_list:
            if p_mode_acq_immo == "Optimisés par l'algorithme":
                montant_acq_immo_a_utiliser_contrainte = acq_immo_var_from_x
            else:
                montant_acq_immo_a_utiliser_contrainte = p_montant_acq_immo_fixe_in
        
        if montant_acq_immo_a_utiliser_contrainte > 0:
            montant_emprunt_immo_calc = max(0, montant_acq_immo_a_utiliser_contrainte - app_immo)
            mensualite_immo_opt = calculer_mensualite_credit(montant_emprunt_immo_calc, p_tx_cred_immo, p_dur_cred_immo_o)
            loyers_immo_annuels_opt = montant_acq_immo_a_utiliser_contrainte * p_rend_loc_immo
            interets_immo_annuels_opt_an1 = montant_emprunt_immo_calc * p_tx_cred_immo # Approx an 1
            rev_foncier_imposable_annuel_opt = max(0, loyers_immo_annuels_opt - interets_immo_annuels_opt_an1)
            impot_foncier_annuel_opt = rev_foncier_imposable_annuel_opt * (p_tmi + p_ps_immo)
            cf_net_mensuel_immo = (loyers_immo_annuels_opt / 12) - mensualite_immo_opt - (impot_foncier_annuel_opt / 12)

        # Estimation du cash-flow net mensuel SCPI (année 1)
        acq_scpi_var_from_x = x_opt[9]
        app_scpi = x_opt[3]
        cf_net_mensuel_scpi = 0
        montant_acq_scpi_a_utiliser_contrainte = 0
        if "SCPI" in p_inv_opt_list:
            if p_mode_acq_scpi == "Optimisés par l'algorithme":
                montant_acq_scpi_a_utiliser_contrainte = acq_scpi_var_from_x
            else:
                montant_acq_scpi_a_utiliser_contrainte = p_montant_acq_scpi_fixe_in

        if montant_acq_scpi_a_utiliser_contrainte > 0:
            montant_emprunt_scpi_calc = max(0, montant_acq_scpi_a_utiliser_contrainte - app_scpi)
            mensualite_scpi_opt = calculer_mensualite_credit(montant_emprunt_scpi_calc, p_tx_cred_scpi, p_dur_cred_scpi_o)
            revenus_scpi_annuels_opt = montant_acq_scpi_a_utiliser_contrainte * p_rend_scpi
            interets_scpi_annuels_opt_an1 = montant_emprunt_scpi_calc * p_tx_cred_scpi # Approx an 1
            rev_scpi_imposable_annuel_opt = max(0, revenus_scpi_annuels_opt - interets_scpi_annuels_opt_an1)
            impot_scpi_annuel_opt = rev_scpi_imposable_annuel_opt * (p_tmi + p_ps_scpi)
            cf_net_mensuel_scpi = (revenus_scpi_annuels_opt / 12) - mensualite_scpi_opt - (impot_scpi_annuel_opt / 12)
            
        return epargne_alloc_opt_specific + gain_fiscal_per_mensuel + cf_net_mensuel_immo + cf_net_mensuel_scpi - somme_epargnes_programmees_brutes
    
    def contrainte_plafond_per(x_opt, 
                               p_horizon, p_tmi, p_rend_av, p_frais_av, p_rend_per, p_frais_per,
                               p_rend_loc_immo, p_reval_immo, p_tx_cred_immo, p_ps_immo, p_dur_cred_immo_o,
                               p_rend_scpi, p_tx_cred_scpi, p_ps_scpi, p_dur_cred_scpi_o,
                               p_montant_acq_immo_fixe_in, p_montant_acq_scpi_fixe_in, p_mode_acq_immo, p_mode_acq_scpi, p_inv_opt_list,
                               max_versement_per_annuel):
        return max_versement_per_annuel - (x_opt[5] * 12) # ep_per_brut est à l'index 5

    def contrainte_endettement(x_opt, 
                               # Global args
                               p_horizon, p_tmi, p_rend_av, p_frais_av, p_rend_per, p_frais_per,
                               p_rend_loc_immo, p_reval_immo, p_tx_cred_immo_glob, p_ps_immo, p_dur_cred_immo_glob,
                               p_rend_scpi, p_tx_cred_scpi_glob, p_ps_scpi, p_dur_cred_scpi_glob,
                               p_montant_acq_immo_fixe_in, p_montant_acq_scpi_fixe_in, p_mode_acq_immo, p_mode_acq_scpi, p_inv_opt_list,
                               # Constraint-specific args
                               max_endettement_mensuel):
        
        montant_acq_immo_eff = 0
        if "Immo" in p_inv_opt_list:
            montant_acq_immo_eff = x_opt[8] if p_mode_acq_immo == "Optimisés par l'algorithme" else p_montant_acq_immo_fixe_in
        
        montant_acq_scpi_eff = 0
        if "SCPI" in p_inv_opt_list:
            montant_acq_scpi_eff = x_opt[9] if p_mode_acq_scpi == "Optimisés par l'algorithme" else p_montant_acq_scpi_fixe_in
            
        emp_immo_calc = max(0, montant_acq_immo_eff - x_opt[2])
        emp_scpi_calc = max(0, montant_acq_scpi_eff - x_opt[3])
        
        mens_immo = calculer_mensualite_credit(emp_immo_calc, p_tx_cred_immo_glob, p_dur_cred_immo_glob)
        mens_scpi = calculer_mensualite_credit(emp_scpi_calc, p_tx_cred_scpi_glob, p_dur_cred_scpi_glob)
        return max_endettement_mensuel - (mens_immo + mens_scpi)

    if st.button("🚀 Lancer l'Optimisation"):
        with st.spinner("Optimisation en cours... Veuillez patienter, cela peut prendre plusieurs minutes."):
            # x_opt = [cap_av, cap_per, app_immo, app_scpi, ep_av, ep_per, ep_ded_immo, ep_ded_scpi, acq_immo_var, acq_scpi_var]
            # Indices:   0       1        2         3         4       5        6            7            8             9
            
            max_ep_per_brut_monthly_from_ceiling = versement_max_per_annuel_opt / 12.0 if versement_max_per_annuel_opt > 0 else float('inf')
            
            base_bounds = [
                (0, capital_a_allouer_opt),  # cap_av (0)
                (0, min(capital_a_allouer_opt, versement_max_initial_per_opt)),  # cap_per (1)
                (0, capital_a_allouer_opt),  # app_immo (2) - borne lâche, contrainte acq-app ou montant_fixe fera le travail
                (0, capital_a_allouer_opt),  # app_scpi (3) - borne lâche
                (0, epargne_mensuelle_a_allouer_opt),  # ep_av (4)
                (0, max_ep_per_brut_monthly_from_ceiling),  # ep_per (5)
                (0, epargne_mensuelle_a_allouer_opt),  # ep_ded_immo (6)
                (0, epargne_mensuelle_a_allouer_opt),  # ep_ded_scpi (7)
                (0, 0), # acq_immo_var (8) - sera ajusté dynamiquement
                (0, 0)  # acq_scpi_var (9) - sera ajusté dynamiquement
            ]
            base_x0 = [
                capital_a_allouer_opt * 0.3,
                min(capital_a_allouer_opt * 0.1, versement_max_initial_per_opt),
                capital_a_allouer_opt * 0.1, 
                capital_a_allouer_opt * 0.1, 
                epargne_mensuelle_a_allouer_opt * 0.3,
                min(epargne_mensuelle_a_allouer_opt * 0.1, max_ep_per_brut_monthly_from_ceiling),
                epargne_mensuelle_a_allouer_opt * 0.1, 
                epargne_mensuelle_a_allouer_opt * 0.1, 
                montant_acquisition_immo_fixe_opt * 0.5, # x0 pour acq_immo_var
                montant_acquisition_scpi_fixe_opt * 0.5  # x0 pour acq_scpi_var
            ]

            final_bounds = list(base_bounds) 
            final_x0 = list(base_x0)       

            # Borne max pour les acquisitions optimisées (exemple très lâche)
            max_acq_val_heuristic = max(capital_a_allouer_opt * 7, capacite_endettement_mensuelle_opt * 12 * 25 * 2) 
            # S'assurer que les montants d'acquisition fixes ne sont pas négatifs
            montant_acq_immo_fixe_sane = max(0, montant_acquisition_immo_fixe_opt)
            montant_acq_scpi_fixe_sane = max(0, montant_acquisition_scpi_fixe_opt)

            # Gestion des bornes et x0 pour l'Immobilier
            if "Immo" in investissements_a_optimiser:
                if mode_acquisition_immo_opt == "Optimisés par l'algorithme":
                    final_bounds[8] = (0, max_acq_val_heuristic) # acq_immo_var
                    final_x0[8] = min(montant_acq_immo_fixe_sane if montant_acq_immo_fixe_sane > 0 else max_acq_val_heuristic * 0.1, max_acq_val_heuristic)
                    final_bounds[2] = (0, max_acq_val_heuristic) # app_immo (sera contraint par acq_immo_var - app_immo >= 0)
                    final_x0[2] = min(final_x0[2], final_x0[8] * 0.2) # Apport initial 20% de l'acquisition x0
                else: # Mode "Fixés par l'utilisateur" pour Immo
                    final_bounds[8]=(0,0); final_x0[8]=0 # acq_immo_var non utilisé
                    final_bounds[2] = (0, montant_acq_immo_fixe_sane) # app_immo borné par l'acquisition fixe
                    final_x0[2] = min(base_x0[2], montant_acq_immo_fixe_sane * 0.2)
                    if montant_acq_immo_fixe_sane == 0: # Si acquisition fixe est 0, pas d'apport ni d'épargne dédiée
                        final_bounds[2]=(0,0); final_x0[2]=0; final_bounds[6]=(0,0); final_x0[6]=0
            else: # Immo non sélectionné du tout
                final_bounds[2]=(0,0); final_x0[2]=0; final_bounds[6]=(0,0); final_x0[6]=0; final_bounds[8]=(0,0); final_x0[8]=0

            # Gestion des bornes et x0 pour les SCPI
            if "SCPI" in investissements_a_optimiser:
                if mode_acquisition_scpi_opt == "Optimisés par l'algorithme":
                    final_bounds[9] = (0, max_acq_val_heuristic) # acq_scpi_var
                    final_x0[9] = min(montant_acq_scpi_fixe_sane if montant_acq_scpi_fixe_sane > 0 else max_acq_val_heuristic * 0.1, max_acq_val_heuristic)
                    final_bounds[3] = (0, max_acq_val_heuristic) # app_scpi
                    final_x0[3] = min(final_x0[3], final_x0[9] * 0.2)
                else: # Mode "Fixés par l'utilisateur" pour SCPI
                    final_bounds[9]=(0,0); final_x0[9]=0 # acq_scpi_var non utilisé
                    final_bounds[3] = (0, montant_acq_scpi_fixe_sane) # app_scpi borné par l'acquisition fixe
                    final_x0[3] = min(base_x0[3], montant_acq_scpi_fixe_sane * 0.2)
                    if montant_acq_scpi_fixe_sane == 0:
                        final_bounds[3]=(0,0); final_x0[3]=0; final_bounds[7]=(0,0); final_x0[7]=0
            else: # SCPI non sélectionné du tout
                final_bounds[3]=(0,0); final_x0[3]=0; final_bounds[7]=(0,0); final_x0[7]=0; final_bounds[9]=(0,0); final_x0[9]=0

            # Ajustements généraux pour AV et PER si non sélectionnés
            if "AV" not in investissements_a_optimiser:
                final_bounds[0]=(0,0); final_x0[0]=0; final_bounds[4]=(0,0); final_x0[4]=0
            if "PER" not in investissements_a_optimiser:
                final_bounds[1]=(0,0); final_x0[1]=0; final_bounds[5]=(0,0); final_x0[5]=0

            # S'assurer que x0 respecte les bornes (surtout après les ajustements)
            for i in range(len(final_x0)):
                final_x0[i] = max(final_bounds[i][0], min(final_x0[i], final_bounds[i][1]))

            # Arguments fixes pour la fonction objectif et les contraintes
            args_objectif = (
                horizon_projection, tmi,
                rendement_av, frais_entree_av_pct,
                rendement_per, frais_entree_per_pct,
                rendement_locatif_immo, revalorisation_immo,
                taux_credit_immo, taux_prelevements_sociaux_immo,
                duree_credit_immo, 
                rendement_scpi, taux_credit_scpi,
                taux_prelevements_sociaux_scpi,
                duree_credit_scpi,
                montant_acq_immo_fixe_sane, 
                montant_acq_scpi_fixe_sane,
                mode_acquisition_immo_opt, 
                mode_acquisition_scpi_opt,
                investissements_a_optimiser # La liste des investissements sélectionnés
            )

            constraints = [
                {'type': 'ineq', 'fun': contrainte_capital_total, # Changé de 'eq' à 'ineq'
                 'args': args_objectif + (capital_a_allouer_opt,)},
                {'type': 'ineq', 'fun': contrainte_epargne_totale, # Changé de 'eq' à 'ineq'
                 'args': args_objectif + (epargne_mensuelle_a_allouer_opt,)},
                {'type': 'ineq', 'fun': contrainte_plafond_per, 
                 'args': args_objectif + (versement_max_per_annuel_opt,)},
                {'type': 'ineq', 'fun': contrainte_endettement, 
                 'args': args_objectif + (capacite_endettement_mensuelle_opt,)}
            ]
            
            # Contraintes: apport <= acquisition (si acquisition optimisée)
            def contrainte_apport_le_acquisition_immo(x_opt, *full_args_list):
                # full_args_list est args_objectif (pas d'arg spécifique pour cette contrainte)
                # Indices: mode_acq_immo=17, mode_acq_scpi=18, inv_opt_list=19
                mode_acq_immo_loc = full_args_list[17] 
                inv_opt_list_loc = full_args_list[19]
                if "Immo" in inv_opt_list_loc and mode_acq_immo_loc == "Optimisés par l'algorithme":
                    return x_opt[8] - x_opt[2] # acq_immo_var - app_immo >= 0
                return 0 # Contrainte inactive ou toujours satisfaite

            def contrainte_apport_le_acquisition_scpi(x_opt, *full_args_list):
                mode_acq_scpi_loc = full_args_list[18]
                inv_opt_list_loc = full_args_list[19]
                if "SCPI" in inv_opt_list_loc and mode_acq_scpi_loc == "Optimisés par l'algorithme":
                    return x_opt[9] - x_opt[3] # acq_scpi_var - app_scpi >= 0
                return 0

            if "Immo" in investissements_a_optimiser and mode_acquisition_immo_opt == "Optimisés par l'algorithme":
                constraints.append({'type': 'ineq', 'fun': contrainte_apport_le_acquisition_immo, 'args': args_objectif})
            if "SCPI" in investissements_a_optimiser and mode_acquisition_scpi_opt == "Optimisés par l'algorithme":
                constraints.append({'type': 'ineq', 'fun': contrainte_apport_le_acquisition_scpi, 'args': args_objectif})
            
            solution = minimize(objectif_optimisation, final_x0, args=args_objectif,
                                method='SLSQP', bounds=final_bounds, constraints=constraints,
                                options={'disp': True, 'maxiter': 200}) # maxiter augmenté

            if solution.success:
                st.success("Optimisation terminée avec succès !")
                opt_values = solution.x
                max_patrimoine_net = -solution.fun

                st.subheader("Résultats de l'Optimisation")
                st.metric("Patrimoine Net Final Optimisé", f"{max_patrimoine_net:,.0f} €")

                st.markdown("#### Allocation Optimale Suggérée :")
                opt_cap_av, opt_cap_per, opt_app_immo, opt_app_scpi, \
                opt_ep_av, opt_ep_per, opt_ep_ded_immo, opt_ep_ded_scpi, \
                opt_acq_immo_var, opt_acq_scpi_var = solution.x
                
                montant_acq_immo_sim = 0
                if "Immo" in investissements_a_optimiser:
                    montant_acq_immo_sim = opt_acq_immo_var if mode_acquisition_immo_opt == "Optimisés par l'algorithme" else montant_acq_immo_fixe_sane
                
                montant_acq_scpi_sim = 0
                if "SCPI" in investissements_a_optimiser:
                    montant_acq_scpi_sim = opt_acq_scpi_var if mode_acquisition_scpi_opt == "Optimisés par l'algorithme" else montant_acq_scpi_fixe_sane

                opt_emp_immo = max(0, montant_acq_immo_sim - opt_app_immo)
                opt_emp_scpi = max(0, montant_acq_scpi_sim - opt_app_scpi)

                alloc_details = []
                if "AV" in investissements_a_optimiser:
                    alloc_details.append({"Type d'Investissement": "Assurance-Vie", "Catégorie": "Capital Initial", "Montant Optimisé (€)": opt_cap_av})
                    alloc_details.append({"Type d'Investissement": "Assurance-Vie", "Catégorie": "Épargne Mensuelle", "Montant Optimisé (€)": opt_ep_av})
                if "PER" in investissements_a_optimiser:
                    alloc_details.append({"Type d'Investissement": "PER", "Catégorie": "Capital Initial", "Montant Optimisé (€)": opt_cap_per})
                    alloc_details.append({"Type d'Investissement": "PER", "Catégorie": "Épargne Mensuelle", "Montant Optimisé (€)": opt_ep_per})
                
                if "Immo" in investissements_a_optimiser:
                    acq_type_immo_label = "Optimisée" if mode_acquisition_immo_opt == "Optimisés par l'algorithme" else "Fixée"
                    alloc_details.append({"Type d'Investissement": f"Immobilier (Acquisition {acq_type_immo_label})", "Catégorie": "Objectif Année 1", "Montant Optimisé (€)": montant_acq_immo_sim})
                    alloc_details.append({"Type d'Investissement": "Immobilier (Apport Optimisé)", "Catégorie": "Capital Initial", "Montant Optimisé (€)": opt_app_immo})
                    alloc_details.append({"Type d'Investissement": "Immobilier (Emprunt Calculé)", "Catégorie": "Financement", "Montant Optimisé (€)": opt_emp_immo})
                    alloc_details.append({"Type d'Investissement": "Immobilier (Dédiée)", "Catégorie": "Épargne Mensuelle", "Montant Optimisé (€)": opt_ep_ded_immo})
                
                if "SCPI" in investissements_a_optimiser:
                    acq_type_scpi_label = "Optimisée" if mode_acquisition_scpi_opt == "Optimisés par l'algorithme" else "Fixée"
                    # Afficher SCPI seulement si l'acquisition (fixe ou optimisée) est > 0, ou si l'apport est > 0
                    # Pour être cohérent, on affiche si SCPI est dans investissements_a_optimiser
                    alloc_details.append({"Type d'Investissement": f"SCPI (Acquisition {acq_type_scpi_label})", "Catégorie": "Objectif Année 1", "Montant Optimisé (€)": montant_acq_scpi_sim})
                    alloc_details.append({"Type d'Investissement": "SCPI (Apport Optimisé)", "Catégorie": "Capital Initial", "Montant Optimisé (€)": opt_app_scpi})
                    alloc_details.append({"Type d'Investissement": "SCPI (Emprunt Calculé)", "Catégorie": "Financement", "Montant Optimisé (€)": opt_emp_scpi})
                    alloc_details.append({"Type d'Investissement": "SCPI (Dédiée)", "Catégorie": "Épargne Mensuelle", "Montant Optimisé (€)": opt_ep_ded_scpi})
                
                df_alloc_display = pd.DataFrame(alloc_details)
                df_alloc_display = df_alloc_display[df_alloc_display["Montant Optimisé (€)"].abs() > 1e-1] # Afficher si > 0.1€
                if not df_alloc_display.empty:
                    st.dataframe(df_alloc_display.style.format({"Montant Optimisé (€)": "{:,.0f} €"}))
                else:
                    st.write("Aucune allocation significative trouvée pour les investissements sélectionnés.")

                # Afficher les graphiques avec l'allocation optimale
                st.markdown("---")
                st.markdown("#### Projection avec l'Allocation Optimale :")
                df_proj_opt, kpis_opt = simuler_projection_patrimoniale(
                    horizon_projection, tmi,
                    opt_cap_av, opt_ep_av, rendement_av, frais_entree_av_pct, # AV
                    opt_cap_per, opt_ep_per, rendement_per, frais_entree_per_pct, # PER
                    opt_app_immo, opt_emp_immo, duree_credit_immo, # Immo
                    rendement_locatif_immo, revalorisation_immo, taux_credit_immo, taux_prelevements_sociaux_immo,
                    opt_ep_ded_immo,
                    opt_app_scpi, opt_emp_scpi, duree_credit_scpi, # SCPI
                    rendement_scpi, taux_credit_scpi, taux_prelevements_sociaux_scpi,
                    opt_ep_ded_scpi
                )

                st.header("📉 Évolution du Patrimoine (Optimal)")
                afficher_evolution_patrimoine(df_proj_opt, titre_suffix="(Optimal)")
                
                st.header("🏛️ Composition du Patrimoine Net par Investissement (Optimal)")
                afficher_composition_patrimoine(df_proj_opt, titre_suffix="(Optimal)")
                
                st.header("📊 Évolution des Flux de Trésorerie Annuels (Optimal)")
                afficher_evolution_flux_tresorerie(df_proj_opt, titre_suffix="(Optimal)")
                
                st.header("🔢 Tableau de Projection Détaillé (Optimal)")
                afficher_tableau_detaille(df_proj_opt)
                
                st.header("🌊 Diagramme de Sankey : Composition du Patrimoine Final (Optimal)")
                afficher_sankey_composition_patrimoine(kpis_opt, kpis_opt['patrimoine_net_final'])

            else:
                st.error(f"L'optimisation n'a pas pu aboutir : {solution.message}")


# Le reste du code de l'onglet Simulateur (affichage des graphiques, tableau, info)
# doit être indenté sous `with tab1:`
# ... (code de l'onglet simulateur existant) ...
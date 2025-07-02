# pages/2_🏦_Patrimoine.py
import streamlit as st
import pandas as pd
from utils.state_manager import initialize_session
from utils.patrimoine_ui import (
    display_immobilier_ui,
    display_investissements_financiers_ui,
    display_autres_actifs_ui,
    display_passifs_ui,
    display_summary,
    display_charts
)
from utils.patrimoine_calculs import calculate_patrimoine_summaries, get_patrimoine_df

# Configuration de la page et titre
st.set_page_config(page_title="Bilan Patrimonial", layout="wide")
st.title("🏦 Bilan Patrimonial")

# Initialisation de l'état de la session au début du script
initialize_session()

# Vérification de l'existence de la clé 'patrimoine' pour la robustesse
if 'patrimoine' not in st.session_state:
    st.error("Erreur critique : L'état du patrimoine n'a pas pu être initialisé.")
    st.stop()

patrimoine_state = st.session_state.patrimoine

# --- Section des ACTIFS ---
st.header("ACTIFS")
display_immobilier_ui(patrimoine_state)
display_investissements_financiers_ui(patrimoine_state)
display_autres_actifs_ui(patrimoine_state)

# --- Section des PASSIFS ---
st.header("PASSIFS")
display_passifs_ui(patrimoine_state)

# --- Section de la SYNTHÈSE ---
st.header("Synthèse du Patrimoine")

# Vérification qu'il y a des données avant de faire les calculs et l'affichage
if (patrimoine_state['immobilier'] or 
    patrimoine_state['investissements_financiers'] or 
    patrimoine_state['autres_actifs'] or 
    patrimoine_state['passifs']):
    
    # 1. Calculer les données de synthèse
    summary_data = calculate_patrimoine_summaries(patrimoine_state)

    # 2. Afficher les métriques et les graphiques
    display_summary(summary_data)
    display_charts(summary_data, patrimoine_state)

    # 3. Afficher le tableau récapitulatif
    st.subheader("Tableau Récapitulatif")
    df_recap = get_patrimoine_df(patrimoine_state)
    st.dataframe(
        df_recap.style.format("€ {:,.2f}", na_rep=""),
        use_container_width=True
    )
else:
    st.info("Commencez par ajouter des actifs ou des passifs pour voir la synthèse.")

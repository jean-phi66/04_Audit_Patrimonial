# views/01_bilan_actuel.py
import streamlit as st
import pandas as pd

st.title("🏠 Bilan Patrimonial Actuel")

# Initialisation du session_state si nécessaire
if 'patrimoine_df' not in st.session_state:
    st.session_state.patrimoine_df = pd.DataFrame([
        {'Actif': 'Résidence Principale', 'Valeur': 400000, 'Rendement %': 2.0},
        {'Actif': 'Livret A', 'Valeur': 15000, 'Rendement %': 3.0},
    ])
if 'prets_df' not in st.session_state:
    st.session_state.prets_df = pd.DataFrame([
        {'Nom': 'Prêt RP', 'Montant Initial': 250000, 'CRD': 150000, 'Taux %': 1.5, 'Fin': 2040},
    ])

st.header("Actifs")
st.session_state.patrimoine_df = st.data_editor(
    st.session_state.patrimoine_df,
    num_rows="dynamic",
    key="editor_actifs"
)

st.header("Passifs (Prêts)")
st.session_state.prets_df = st.data_editor(
    st.session_state.prets_df,
    num_rows="dynamic",
    key="editor_passifs"
)

st.success("Les données du bilan sont enregistrées. Passez à l'onglet 'Budget Actuel'.")
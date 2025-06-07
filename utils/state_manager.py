# utils/state_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime
import json

def initialize_session():
    if 'initialized' in st.session_state:
        return

    st.session_state.df_stocks = pd.DataFrame([
        {'Actif': 'Résidence Principale', 'Type': 'Immobilier de jouissance', 'Valeur Brute': 350000, 'Valeur Nette': 200000, 'Rendement %': 2.0, 'Prix Achat Initial': 220000, 'Date Achat': datetime(2015, 6, 15)},
        {'Actif': 'Immo Locatif (meublé)', 'Type': 'Immobilier productif', 'Valeur Brute': 120000, 'Valeur Nette': 80000, 'Rendement %': 4.5, 'Prix Achat Initial': 90000, 'Date Achat': datetime(2018, 9, 1)},
        {'Actif': 'Assurance Vie', 'Type': 'Financier', 'Valeur Brute': 50000, 'Valeur Nette': 50000, 'Rendement %': 3.5, 'Prix Achat Initial': 50000, 'Date Achat': datetime(2019, 1, 1)},
        {'Actif': 'Livret bancaire', 'Type': 'Financier', 'Valeur Brute': 15000, 'Valeur Nette': 15000, 'Rendement %': 3.0, 'Prix Achat Initial': 15000, 'Date Achat': datetime(2019, 1, 1)},
    ])
    st.session_state.df_revenus = pd.DataFrame({'Poste': ['Salaire', 'Revenus locatifs'], 'Montant Annuel': [60000, 8000]})
    st.session_state.df_depenses = pd.DataFrame({'Poste': ['Dépenses courantes', 'Taxe foncière'], 'Montant Annuel': [25000, 1500]})
    st.session_state.df_prets = pd.DataFrame([
        {'Nom': 'Prêt RP', 'Montant Initial': 150000, 'Taux Annuel %': 1.5, 'Durée Initiale (ans)': 25, 'Date Début': datetime(2020, 1, 1), 'Actif Associé': 'Résidence Principale'},
        {'Nom': 'Prêt Locatif', 'Montant Initial': 40000, 'Taux Annuel %': 2.0, 'Durée Initiale (ans)': 20, 'Date Début': datetime(2022, 1, 1), 'Actif Associé': 'Immo Locatif (meublé)'}
    ])
    st.session_state.df_adultes = pd.DataFrame([{'Prénom': 'Jean', 'Âge': 40, 'Année Départ Retraite': 2049}])
    st.session_state.df_enfants = pd.DataFrame([{'Prénom': 'Léo', 'Âge': 12, 'Âge Début Études': 18, 'Durée Études (ans)': 5, 'Coût Annuel Études (€)': 8000}])
    st.session_state.hyp_retraite = {'taux_remplacement': 60.0}
    st.session_state.hyp_economiques = {'inflation': 2.0, 'revalo_salaire': 1.5}
    st.session_state.parent_isole = True
    st.session_state.df_ventes = pd.DataFrame(columns=['Année de Vente', 'Bien à Vendre'])
    st.session_state.initialized = True

def serialize_state():
    state_to_save = {}
    keys_to_save = ['df_stocks', 'df_revenus', 'df_depenses', 'df_prets', 'df_adultes', 'df_enfants', 'hyp_retraite', 'parent_isole', 'df_ventes', 'hyp_economiques']
    for key in keys_to_save:
        if key in st.session_state:
            data = st.session_state[key]
            if isinstance(data, pd.DataFrame):
                df_copy = data.copy()
                for col in df_copy.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns:
                    df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
                state_to_save[key] = df_copy.to_dict('records')
            else:
                state_to_save[key] = data
    return json.dumps(state_to_save, indent=4)

def deserialize_and_update_state(json_data):
    data = json.load(json_data)
    for key, value in data.items():
        if isinstance(value, list) and key.startswith('df_'):
            df = pd.DataFrame(value)
            for col in df.columns:
                if 'Date' in col:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            st.session_state[key] = df
        else:
            st.session_state[key] = value
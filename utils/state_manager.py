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
    # Assurer que df_revenus a un Prénom associé si nécessaire pour la logique de pension
    # Pour l'instant, on suppose que le premier revenu est pour le premier adulte, etc.
    # Ou que la projection gère cela via df_adultes.
    st.session_state.df_depenses = pd.DataFrame({'Poste': ['Dépenses courantes', 'Taxe foncière'], 'Montant Annuel': [25000, 1500]}) # Pas de changement ici
    st.session_state.df_prets = pd.DataFrame([
        {'Nom': 'Prêt RP', 'Montant Initial': 150000, 'Taux Annuel %': 1.5, 'Durée Initiale (ans)': 25, 'Date Début': datetime(2020, 1, 1), 'Actif Associé': 'Résidence Principale'},
        {'Nom': 'Prêt Locatif', 'Montant Initial': 40000, 'Taux Annuel %': 2.0, 'Durée Initiale (ans)': 20, 'Date Début': datetime(2022, 1, 1), 'Actif Associé': 'Immo Locatif (meublé)'}
    ])
    st.session_state.df_adultes = pd.DataFrame([{'Prénom': 'Jean', 'Âge': 40}]) # Suppression de 'Année Départ Retraite'
    st.session_state.df_enfants = pd.DataFrame([{'Prénom': 'Léo', 'Âge': 12, 'Âge Début Études': 18, 'Durée Études (ans)': 5, 'Coût Annuel Études (€)': 8000}])
    # Suppression de hyp_retraite, remplacé par df_pension_hypotheses
    st.session_state.hyp_economiques = {'inflation': 2.0, 'revalo_salaire': 1.5}
    st.session_state.parent_isole = True
    st.session_state.df_ventes = pd.DataFrame(columns=['Année de Vente', 'Bien à Vendre'])
    
    # Initialisation améliorée de df_pension_hypotheses
    st.session_state.df_pension_hypotheses = pd.DataFrame([
        {'Prénom Adulte': 'Jean', 'Âge Départ Retraite': 64, 'Montant Pension Annuelle (€)': 30000, 'Active': True, 'Année Départ Retraite': pd.NA}
    ])
    # S'assurer que les types sont corrects dès l'initialisation
    st.session_state.df_pension_hypotheses['Prénom Adulte'] = st.session_state.df_pension_hypotheses['Prénom Adulte'].astype('object')
    st.session_state.df_pension_hypotheses['Âge Départ Retraite'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Âge Départ Retraite'], errors='coerce').astype('Int64')
    st.session_state.df_pension_hypotheses['Montant Pension Annuelle (€)'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Montant Pension Annuelle (€)'], errors='coerce').astype('float64')
    st.session_state.df_pension_hypotheses['Active'] = st.session_state.df_pension_hypotheses['Active'].astype('boolean') # Utiliser le type nullable boolean
    st.session_state.df_pension_hypotheses['Année Départ Retraite'] = pd.to_numeric(st.session_state.df_pension_hypotheses['Année Départ Retraite'], errors='coerce').astype('Int64')

    st.session_state.initialized = True

def serialize_state():
    state_to_save = {}
    keys_to_save = ['df_stocks', 'df_revenus', 'df_depenses', 'df_prets', 'df_adultes', 'df_enfants', 'parent_isole', 'df_ventes', 'hyp_economiques', 'df_pension_hypotheses']
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
                # Convertir les colonnes de date
                if 'Date' in col or 'Année Départ Retraite' in col: # Année Départ Retraite peut être une date ou un entier
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if col == 'Année Départ Retraite' and df[col].isna().all(): # Si c'est une année, convertir en Int64
                        df[col] = pd.to_numeric(pd.DataFrame(value)[col], errors='coerce').astype('Int64')
            st.session_state[key] = df
        else:
            st.session_state[key] = value
# utils/state_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import json

def initialize_session():
    """
    Initialise toutes les variables de session nécessaires pour l'application si elles n'existent pas.
    """
    if 'initialized' in st.session_state:
        return

    # --- Initialisation du Foyer ---
    st.session_state.df_adultes = pd.DataFrame([
        {'Prénom': 'Jean', 'Âge': 40, 'Date Naissance': datetime(1984, 5, 20)},
        {'Prénom': 'Marie', 'Âge': 38, 'Date Naissance': datetime(1986, 8, 15)}
    ])
    st.session_state.df_enfants = pd.DataFrame([
        {'Prénom': 'Léo', 'Âge': 12, 'Date Naissance': datetime(2012, 3, 10), 'Âge Début Études': 18, 'Durée Études (ans)': 5, 'Coût Annuel Études (€)': 8000}
    ])
    st.session_state.parent_isole = False

    # --- Initialisation du Patrimoine (Stocks) ---
    st.session_state.df_stocks = pd.DataFrame([
        {
            'Actif': 'Résidence Principale', 'Type': 'Immobilier de jouissance', 'Valeur Brute': 350000, 'Valeur Nette': 200000, 
            'Rendement %': 2.0, 'Prix Achat Initial': 280000, 'Date Achat': datetime(2015, 6, 15),
            'Capital Réorientable ?': False, 'Pourcentage Réorientable (%)': 0.0,
            'Loyer Mensuel Brut (€)': 0.0, 'Charges Annuelles (€)': 2000.0, 'Taxe Foncière Annuelle (€)': 1500.0,
            'Type de Propriété': 'Commun', 'Propriétaire Propre': None, 'Part Adulte 1 (%)': 50.0, 'Part Adulte 2 (%)': 50.0,
            'Dispositif Fiscal': None, 'Durée Défiscalisation (ans)': 0
        },
        {
            'Actif': 'Immo Locatif (meublé)', 'Type': 'Immobilier productif', 'Valeur Brute': 120000, 'Valeur Nette': 80000, 
            'Rendement %': 4.5, 'Prix Achat Initial': 90000, 'Date Achat': datetime(2018, 9, 1),
            'Capital Réorientable ?': False, 'Pourcentage Réorientable (%)': 0.0,
            'Loyer Mensuel Brut (€)': 450.0, 'Charges Annuelles (€)': 1000.0, 'Taxe Foncière Annuelle (€)': 800.0,
            'Type de Propriété': 'Propre', 'Propriétaire Propre': 'Jean', 'Part Adulte 1 (%)': 100.0, 'Part Adulte 2 (%)': 0.0,
            'Dispositif Fiscal': None, 'Durée Défiscalisation (ans)': 0
        },
        {
            'Actif': 'Assurance Vie', 'Type': 'Financier', 'Valeur Brute': 50000, 'Valeur Nette': 50000, 
            'Rendement %': 3.5, 'Prix Achat Initial': 40000, 'Date Achat': datetime(2019, 1, 1),
            'Capital Réorientable ?': True, 'Pourcentage Réorientable (%)': 100.0,
            'Loyer Mensuel Brut (€)': 0.0, 'Charges Annuelles (€)': 0.0, 'Taxe Foncière Annuelle (€)': 0.0,
            'Type de Propriété': 'Commun', 'Propriétaire Propre': None, 'Part Adulte 1 (%)': 50.0, 'Part Adulte 2 (%)': 50.0,
            'Dispositif Fiscal': None, 'Durée Défiscalisation (ans)': 0
        },
    ])

    # --- Initialisation des Flux (Revenus & Dépenses) ---
    st.session_state.df_revenus = pd.DataFrame([
        # MODIFIÉ: Ajout de 'Prénom Adulte' et 'Type'
        {'Poste': 'Salaire Jean', 'Montant Annuel': 55000, 'Prénom Adulte': 'Jean', 'Type': 'Salaire'},
        {'Poste': 'Salaire Marie', 'Montant Annuel': 48000, 'Prénom Adulte': 'Marie', 'Type': 'Salaire'},
        {'Poste': 'Revenus indépendants', 'Montant Annuel': 5000, 'Prénom Adulte': None, 'Type': 'Autre'}
    ])
    st.session_state.df_depenses = pd.DataFrame([
        {'Poste': 'Dépenses courantes', 'Montant Annuel': 30000}, 
        {'Poste': 'Loisirs et vacances', 'Montant Annuel': 5000}
    ])

    # --- Initialisation des Passifs (Prêts) ---
    st.session_state.df_prets = pd.DataFrame([
        {'Actif Associé': 'Résidence Principale', 'Montant Initial': 150000, 'Taux Annuel %': 1.5, 'Durée Initiale (ans)': 25, 'Date Début': datetime(2015, 6, 15), 'Assurance Emprunteur %': 0.36},
        {'Actif Associé': 'Immo Locatif (meublé)', 'Montant Initial': 40000, 'Taux Annuel %': 2.0, 'Durée Initiale (ans)': 20, 'Date Début': datetime(2018, 9, 1), 'Assurance Emprunteur %': 0.36}
    ])
    
    # --- Initialisation des Hypothèses de Projection ---
    st.session_state.hyp_economiques = {'inflation': 2.0, 'revalo_salaire': 1.5}
    st.session_state.df_pension_hypotheses = pd.DataFrame([
        {'Prénom Adulte': 'Jean', 'Âge Départ Retraite': 64, 'Montant Pension Annuelle (€)': 30000, 'Active': True, 'Année Départ Retraite': pd.NA},
        {'Prénom Adulte': 'Marie', 'Âge Départ Retraite': 64, 'Montant Pension Annuelle (€)': 28000, 'Active': True, 'Année Départ Retraite': pd.NA}
    ])
    st.session_state.df_ventes = pd.DataFrame(columns=['Bien à Vendre', 'Année de Vente'])

    # --- Marqueur d'initialisation ---
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
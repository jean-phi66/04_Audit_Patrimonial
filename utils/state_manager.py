# utils/state_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import json

# --- DÉFINITION DE L'ÉTAT INITIAL ---
def get_initial_state_config():
    """
    Retourne un dictionnaire de configuration pour l'état initial complet de l'application.
    Ceci est la source de vérité pour toutes les variables de session.
    """
    return {
        # Famille & Événements
        'df_adultes': {'type': 'dataframe', 'cols': ['Prénom', 'Âge', 'Date Naissance']},
        'df_enfants': {'type': 'dataframe', 'cols': ['Prénom', 'Âge', 'Date Naissance', 'Âge Début Études', 'Durée Études (ans)', 'Coût Annuel Études (€)']},
        'parent_isole': {'type': 'value', 'default': False},
        
        # Patrimoine (Bilan)
        'patrimoine': {
            'type': 'value', 'default': {
                'immobilier': [], 'investissements_financiers': [], 'autres_actifs': [], 'passifs': []
            }
        },
        
        # Patrimoine & Dettes (pour Projection)
        'df_stocks': {'type': 'dataframe', 'cols': ['Actif', 'Type', 'Valeur Brute', 'Rendement %', 'Prix Achat Initial', 'Date Achat', 'Dispositif Fiscal', 'Durée Défiscalisation (ans)', 'Charges Annuelles (€)', 'Taxe Foncière Annuelle (€)', 'Loyer Mensuel Brut (€)']},
        'df_prets': {'type': 'dataframe', 'cols': ['Actif Associé', 'Montant Initial', 'Taux Annuel %', 'Durée Initiale (ans)', 'Date Début', 'Assurance Emprunteur %']},
        
        # Flux
        'df_revenus': {'type': 'dataframe', 'cols': ['Poste', 'Montant Annuel', 'Prénom Adulte', 'Type']},
        'df_depenses': {'type': 'dataframe', 'cols': ['Poste', 'Montant Annuel']},
        
        # Projection
        'df_pension_hypotheses': {'type': 'dataframe', 'cols': ['Prénom Adulte', 'Âge Départ Retraite', 'Montant Pension Annuelle (€)', 'Active', 'Année Départ Retraite']},
        'df_ventes': {'type': 'dataframe', 'cols': ['Bien à Vendre', 'Année de Vente']},
        'hyp_economiques': {'type': 'value', 'default': {'inflation': 0.0, 'revalo_salaire': 0.0}},
        
        # Données de sortie de simulation
        'tableau_financier': {'type': 'value', 'default': None},
        'logs_evenements': {'type': 'value', 'default': []},

        # Paramètres et résultats d'optimisation/simulation
        'optim_params': {'type': 'value', 'default': {}},
        'opt_result': {'type': 'value', 'default': None},
        'simulation_args': {'type': 'value', 'default': None},
        'sim_manual_params': {'type': 'value', 'default': {}},
        'manual_sim_results': {'type': 'value', 'default': None},
    }

# --- FONCTIONS DE GESTION DE L'ÉTAT ---
def initialize_session():
    """
    Initialise st.session_state avec la structure de données complète si nécessaire.
    """
    config = get_initial_state_config()
    for key, item_config in config.items():
        if key not in st.session_state:
            if item_config['type'] == 'dataframe':
                st.session_state[key] = pd.DataFrame(columns=item_config['cols'])
            elif item_config['type'] == 'value':
                st.session_state[key] = item_config['default']

def reset_state():
    """
    Réinitialise l'état de la session à sa valeur initiale.
    """
    config = get_initial_state_config()
    # Supprimer toutes les clés gérées pour garantir une réinitialisation propre
    for key in list(st.session_state.keys()):
        if key in config:
            del st.session_state[key]
    initialize_session() # Recrée l'état à partir de la configuration
    st.success("L'état de la session a été réinitialisé.")

# --- FONCTIONS DE SAUVEGARDE ET CHARGEMENT ---
class CustomEncoder(json.JSONEncoder):
    """Encode les objets complexes (DataFrame, datetime) en JSON."""
    def default(self, obj):
        if isinstance(obj, (datetime, date, pd.Timestamp)):
            return {'__complex_object__': 'datetime', 'value': obj.isoformat()}
        if isinstance(obj, pd.DataFrame):
            # Utilise to_json avec l'orientation 'split' qui est efficace et gère bien les types
            return {'__complex_object__': 'dataframe', 'value': obj.to_json(orient='split', date_format='iso')}
        if pd.isna(obj):
            return None  # Convertit pd.NA/np.nan en null JSON
        return super().default(obj)

def custom_decoder(dct):
    """Décode les objets complexes depuis JSON."""
    if '__complex_object__' in dct:
        obj_type = dct['__complex_object__']
        if obj_type == 'datetime':
            return pd.to_datetime(dct['value'])
        if obj_type == 'dataframe':
            # Utilise read_json avec l'orientation 'split'
            return pd.read_json(dct['value'], orient='split')
    return dct

def save_state_to_file(file_path):
    """
    Sauvegarde l'état actuel de la session dans un fichier JSON.
    """
    state_to_save = {}
    config = get_initial_state_config()
    # On ne sauvegarde que les clés qui font partie de notre état défini
    for key in config.keys():
        if key in st.session_state:
            state_to_save[key] = st.session_state[key]
            
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_to_save, f, cls=CustomEncoder, indent=4)
        st.success(f"État sauvegardé avec succès dans {file_path}")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du fichier : {e}")

def load_state_from_file(uploaded_file):
    """
    Charge l'état de la session depuis un fichier JSON, en réinitialisant d'abord.
    """
    try:
        content = uploaded_file.read().decode('utf-8')
        loaded_data = json.loads(content, object_hook=custom_decoder)
        
        # Réinitialiser l'état avant de charger pour éviter les conflits de clés anciennes/nouvelles
        reset_state()
        
        # Mettre à jour la session avec les données chargées
        for key, value in loaded_data.items():
            # S'assurer de ne charger que les clés attendues pour la sécurité et la propreté
            if key in get_initial_state_config():
                st.session_state[key] = value
            else:
                st.warning(f"Clé '{key}' trouvée dans le fichier mais non reconnue par l'application. Elle a été ignorée.")

        st.success("État chargé avec succès !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")

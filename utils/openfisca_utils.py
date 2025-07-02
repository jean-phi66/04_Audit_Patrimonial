# utils/openfisca_utils.py
import streamlit as st
import pandas as pd
try:
    from openfisca_france import FranceTaxBenefitSystem
    from openfisca_core.simulation_builder import SimulationBuilder
    OPENFISCA_READY = True
except ImportError:
    OPENFISCA_READY = False

@st.cache_data
def calculer_impot_openfisca(annee, foyer_details):
    if not OPENFISCA_READY: 
        st.warning(f"Année {annee}: OpenFisca non installé, utilisation d'un calcul simplifié.")
        return foyer_details.get('revenus_imposables', 0) * 0.15 
        
    tax_benefit_system = FranceTaxBenefitSystem()
    simulation_builder = SimulationBuilder()
    
    individus = {}
    for i, adulte in enumerate(foyer_details['adultes_details']):
        annee_naissance_adulte = adulte.get('annee_naissance')
        if pd.isna(annee_naissance_adulte):
            st.error(f"Année de naissance manquante pour parent{i+1} pour l'année {annee}. Calcul d'impôt approximatif utilisé.")
            return foyer_details.get('revenus_imposables', 0) * 0.15 # Fallback
        
        # Assurer que l'année de naissance est un entier pour le formatage correct de la date
        date_naissance_formatee = f"{int(annee_naissance_adulte)}-01-01"
        
        individus[f'parent{i+1}'] = {
            'salaire_imposable': {str(annee): adulte['revenu']},
            'date_naissance': {'ETERNITY': date_naissance_formatee}
        }
    
    personnes_a_charge_valides = []
    for i, enfant in enumerate(foyer_details['enfants_details']):
        annee_naissance_enfant = enfant.get('Année Naissance')
        if pd.isna(annee_naissance_enfant):
            st.warning(f"Année de naissance manquante pour enfant{i+1} pour l'année {annee}. Enfant ignoré pour le calcul d'impôt.")
            continue # Ne pas traiter cet enfant si son année de naissance manque
            
        # Assurer que l'année de naissance est un entier pour le formatage correct de la date
        date_naissance_enfant_formatee = f"{int(annee_naissance_enfant)}-01-01"
        nom_openfisca_enfant = f'enfant{i+1}'
        individus[nom_openfisca_enfant] = {'date_naissance': {'ETERNITY': date_naissance_enfant_formatee}}
        personnes_a_charge_valides.append(nom_openfisca_enfant)
        
    foyer_fiscal = {'foyerfiscal1': {
        'declarants': [f'parent{i+1}' for i in range(len(foyer_details['adultes_details']))],
        'personnes_a_charge': personnes_a_charge_valides
    }}
    
    if foyer_details.get('est_parent_isole', False):
         foyer_fiscal['foyerfiscal1']['caseT'] = {str(annee): True}
         
    CASE = {'individus': individus, 'foyers_fiscaux': foyer_fiscal}
    
    try:
        simulation = simulation_builder.build_from_entities(tax_benefit_system, CASE)
        return float(simulation.calculate('ip_net', str(annee))[0])
    except Exception as e:
        st.error(f"Erreur OpenFisca pour l'année {annee}: {e}")
        return 0
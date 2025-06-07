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
        individus[f'parent{i+1}'] = {
            'salaire_imposable': {str(annee): adulte['revenu']},
            'date_naissance': {'ETERNITY': f"{adulte['annee_naissance']}-01-01"}
        }
    
    personnes_a_charge = [f'enfant{i+1}' for i, _ in enumerate(foyer_details['enfants_details'])]
    for i, enfant in enumerate(foyer_details['enfants_details']):
        individus[f'enfant{i+1}'] = {'date_naissance': {'ETERNITY': f"{enfant['Année Naissance']}-01-01"}}
        
    foyer_fiscal = {'foyerfiscal1': {
        'declarants': [f'parent{i+1}' for i in range(len(foyer_details['adultes_details']))],
        'personnes_a_charge': personnes_a_charge
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
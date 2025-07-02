import streamlit as st
import numpy as np
from types import SimpleNamespace
from ui_components import setup_sidebar, display_results
from simulation import calculate_monthly_payment

# --- Configuration de la page ---
st.set_page_config(page_title="Simulation Manuelle", page_icon="✍️", layout="wide")
st.title("✍️ Simulateur d'Allocation Manuelle")
st.write("Utilisez le panneau de gauche pour définir vos paramètres ET votre allocation manuelle, puis lancez la simulation.")

# --- Interface Utilisateur ---
# On passe "simulation" pour afficher les sliders d'allocation manuelle
user_params = setup_sidebar(page_name="simulation")

# --- Lancement de la Simulation ---
if st.button("Lancer la Simulation Manuelle", type="primary", use_container_width=True):
    active_financial_assets = user_params['df_options_financiers_edited'][user_params['df_options_financiers_edited']['Actif']]
    asset_names = active_financial_assets.index.tolist()

    if not asset_names and not user_params['include_immo']:
        st.warning("Veuillez activer au moins un type d'investissement dans la barre latérale.")
        st.stop()
    
    # Vérifier que l'allocation manuelle somme à 100% pour les actifs financiers
    manual_allocs = user_params.get('manual_allocations', {})
    total_alloc_pct = sum(manual_allocs.values())
    if len(asset_names) > 0 and abs(total_alloc_pct - 100) > 1:
        st.error(f"La somme des allocations manuelles doit être de 100%. Actuellement : {total_alloc_pct}%.")
        st.stop()

    with st.spinner("Simulation manuelle en cours..."):
        # Construire les arguments de la simulation
        simulation_args = (
            asset_names, user_params['initial_capital'], user_params['monthly_investment'], user_params['investment_horizon'],
            active_financial_assets.drop(columns=['Actif']),
            user_params['immo_params'] if user_params['include_immo'] else None,
            user_params['loan_params'] if user_params['include_immo'] else None,
            user_params['marginal_tax_rate'], user_params['per_deduction_limit']
        )

        # Construire le vecteur de variables pour la simulation
        manual_weights = np.array([manual_allocs.get(name, 0) / 100.0 for name in asset_names])
        
        if user_params['include_immo']:
            # Pour la simu manuelle, on utilise le prix fixé s'il est coché, sinon la borne inférieure
            if user_params['fix_immo_price']:
                immo_price = user_params['fixed_immo_price']
            else:
                immo_price = user_params['immo_price_range'][0] 
                st.info(f"Le prix du bien immobilier a été fixé à {immo_price:,.0f} € (borne inférieure de la fourchette).")

            # Vérifier la contrainte de mensualité
            mensualite_calculee = calculate_monthly_payment(immo_price, user_params['loan_params']['rate'], user_params['loan_params']['duration'])
            if mensualite_calculee > user_params['loan_params']['mensualite_max']:
                st.error(f"Le prix du bien ({immo_price:,.0f} €) engendre une mensualité de {mensualite_calculee:,.0f} €, dépassant votre max de {user_params['loan_params']['mensualite_max']:,.0f} €.")
                st.stop()
            
            simulation_vars = np.append(manual_weights, immo_price)
        else:
            simulation_vars = manual_weights

        # Créer un faux objet "resultat" pour le passer à la fonction d'affichage
        manual_result = SimpleNamespace(
            success=True,
            message="Simulation manuelle exécutée avec succès.",
            x=simulation_vars
        )
        
        display_results(manual_result, simulation_args)
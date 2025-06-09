# Fichier: app.py (version mise à jour pour simulation manuelle)
import streamlit as st
import numpy as np
from types import SimpleNamespace # <<< AJOUT : Pour créer un objet simple
from ui_components import setup_sidebar, display_results
from optimization import setup_and_run_optimization, calculate_monthly_payment # <<< AJOUT : Import calculate_monthly_payment

def main():
    """
    Fonction principale de l'application Streamlit.
    """
    st.set_page_config(
        page_title="Optimiseur & Simulateur Patrimonial",
        page_icon="🚀",
        layout="wide"
    )
    st.title("🚀 Optimiseur & Simulateur d'Allocation Patrimoniale")
    st.write("Utilisez le panneau de gauche pour définir vos paramètres. Ensuite, lancez une **optimisation** pour trouver la meilleure stratégie, ou une **simulation manuelle** pour tester votre propre allocation.")

    user_params = setup_sidebar()
    
    col1, col2 = st.columns(2)

    # --- Bouton 1: Lancer l'Optimisation (Logique existante) ---
    with col1:
        if st.button("Lancer l'Optimisation", type="primary", use_container_width=True):
            with st.spinner("Optimisation en cours... Cela peut prendre une minute."):
                opt_result, simulation_args = setup_and_run_optimization(user_params)
                
                if opt_result and simulation_args:
                    if opt_result.success and user_params.get('fix_immo_price'):
                        weights = opt_result.x
                        fixed_price = user_params.get('fixed_immo_price', 0)
                        opt_result.x = np.append(weights, fixed_price)

                    display_results(opt_result, simulation_args)
                elif opt_result is None and simulation_args is None:
                    # Ce cas est géré dans setup_and_run_optimization (pas d'actifs)
                    st.warning("Veuillez activer au moins un type d'investissement dans la barre latérale.")
                else:
                    st.error("Une erreur est survenue durant l'optimisation.")

    # --- Bouton 2: Lancer la Simulation Manuelle (Nouvelle logique) ---
    with col2:
        if st.button("Lancer la Simulation Manuelle", use_container_width=True):
            active_financial_assets = user_params['df_options_financiers_edited'][user_params['df_options_financiers_edited']['Actif']]
            asset_names = active_financial_assets.index.tolist()

            if not asset_names and not user_params['include_immo']:
                st.warning("Veuillez activer au moins un type d'investissement dans la barre latérale.")
                st.stop()
            
            # Vérifier que l'allocation manuelle somme à 100%
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
                    # Pour la simu manuelle, on utilise le prix fixé s'il est coché, sinon la borne inférieure de la fourchette
                    if user_params['fix_immo_price']:
                        immo_price = user_params['fixed_immo_price']
                    else:
                        immo_price = user_params['immo_price_range'][0] # On prend la borne min comme défaut
                        st.info(f"Le prix du bien immobilier pour la simulation manuelle a été fixé à {immo_price:,.0f} € (borne inférieure de la fourchette).")

                    # Vérifier la contrainte de mensualité manuellement
                    mensualite_calculee = calculate_monthly_payment(immo_price, user_params['loan_params']['rate'], user_params['loan_params']['duration'])
                    if mensualite_calculee > user_params['loan_params']['mensualite_max']:
                        st.error(f"Le prix du bien ({immo_price:,.0f} €) engendre une mensualité de {mensualite_calculee:,.0f} €, ce qui dépasse votre maximum de {user_params['loan_params']['mensualite_max']:,.0f} €.")
                        st.stop()
                    
                    simulation_vars = np.append(manual_weights, immo_price)
                else:
                    simulation_vars = manual_weights

                # Créer un faux objet "opt_result" pour le passer à display_results
                manual_result = SimpleNamespace(
                    success=True,
                    message="Simulation manuelle exécutée avec succès.",
                    x=simulation_vars
                )
                
                display_results(manual_result, simulation_args)

if __name__ == "__main__":
    main()
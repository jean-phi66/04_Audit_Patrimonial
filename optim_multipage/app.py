# Fichier: app.py (version mise à jour)
import streamlit as st
import numpy as np
from ui_components import setup_sidebar, display_results
from optimization import setup_and_run_optimization

def main():
    """
    Fonction principale de l'application Streamlit.
    """
    st.set_page_config(
        page_title="Optimiseur d'Allocation Patrimoniale",
        page_icon="🚀",
        layout="wide"
    )
    st.title("🚀 Optimiseur d'Allocation Patrimoniale")

    user_params = setup_sidebar()

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
                pass
            else:
                st.warning("Veuillez activer au moins un type d'investissement dans la barre latérale.")

if __name__ == "__main__":
    main()
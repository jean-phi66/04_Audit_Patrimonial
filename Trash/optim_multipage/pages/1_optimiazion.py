import streamlit as st
import numpy as np
from ui_components import setup_sidebar, display_results
from optimization import setup_and_run_optimization

# --- Configuration de la page ---
st.set_page_config(page_title="Optimisation", page_icon="🚀", layout="wide")
st.title("🚀 Optimiseur d'Allocation Patrimoniale")
st.write("Utilisez le panneau de gauche pour définir vos paramètres, puis lancez l'optimisation pour trouver la stratégie la plus performante.")

# --- Interface Utilisateur ---
# On passe "optimisation" pour n'afficher que les paramètres pertinents
user_params = setup_sidebar(page_name="optimisation") 

# --- Lancement de l'Optimisation ---
if st.button("Lancer l'Optimisation", type="primary", use_container_width=True):
    with st.spinner("Optimisation en cours... Cela peut prendre une minute."):
        opt_result, simulation_args = setup_and_run_optimization(user_params)
        
        if opt_result and simulation_args:
            # Cas spécial où le prix de l'immo est fixé, il faut le rajouter au vecteur de résultat
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
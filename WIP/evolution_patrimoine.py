import streamlit as st
import pandas as pd
import numpy as np # Pour les calculs financiers (pmt)
import copy # Pour la copie profonde des objets (deepcopy)
import plotly.express as px # Pour des graphiques plus interactifs

# Initialisation des variables de l'état de session
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []
if 'scenario_counter' not in st.session_state: # Correction de la coquille ici (était 'not st in')
    st.session_state.scenario_counter = 0

# --- Configuration pour les colonnes de st.data_editor ---
config_immobilier = {
    "Nom": st.column_config.TextColumn("Nom du bien", required=True, help="Ex: Résidence principale"),
    "Valeur Actuelle (€)": st.column_config.NumberColumn("Valeur Actuelle (€)", min_value=0, format="€%.2f", required=True),
    "Rendement Annuel (%)": st.column_config.NumberColumn("Rendement Annuel (%)", min_value=-100.0, max_value=100.0, format="%.2f%%", help="Rendement net ou plus-value estimée"),
    "Capital Restant Dû Emprunt (€)": st.column_config.NumberColumn("Capital Restant Dû Emprunt (€)", min_value=0, format="€%.2f", help="Laissez à 0 si pas d'emprunt"),
    "Taux Annuel Emprunt (%)": st.column_config.NumberColumn("Taux Annuel Emprunt (%)", min_value=0.0, max_value=100.0, format="%.2f%%"),
    "Années Restantes Emprunt": st.column_config.NumberColumn("Années Restantes Emprunt", min_value=0, step=1, format="%d an(s)")
}

config_placements = {
    "Nom": st.column_config.TextColumn("Nom du placement", required=True, help="Ex: Livret A, Assurance Vie"),
    "Valeur Actuelle (€)": st.column_config.NumberColumn("Valeur Actuelle (€)", min_value=0, format="€%.2f", required=True),
    "Rendement Annuel (%)": st.column_config.NumberColumn("Rendement Annuel (%)", min_value=-100.0, max_value=100.0, format="%.2f%%"),
    "Versement Mensuel (€)": st.column_config.NumberColumn("Versement Mensuel (€)", min_value=0, format="€%.2f", help="Montant versé chaque mois sur ce placement")
}

# DataFrames vides par défaut
default_immobilier_df = pd.DataFrame(columns=list(config_immobilier.keys()))
default_placements_df = pd.DataFrame(columns=list(config_placements.keys()))

# --- Fonctions de Calcul pour la Simulation ---

def calculate_annual_loan_payment(principal, annual_rate_percent, years_remaining):
    """Calcule l'annuité d'un prêt."""
    if principal <= 0 or years_remaining <= 0: # Si plus de principal ou plus d'années, pas de paiement
        return 0, 0, 0 # Annuité, Intérêts, Principal remboursé
    
    # Cas d'un taux d'intérêt nul
    if annual_rate_percent == 0:
        annual_payment = principal / years_remaining
        interest_paid = 0
        principal_paid = annual_payment
        return annual_payment, interest_paid, principal_paid

    try:
        monthly_rate = (annual_rate_percent / 100) / 12
        number_of_months = years_remaining * 12
        
        # np.pmt calcule le paiement périodique. Il sera négatif (sortie d'argent).
        # On le veut positif pour nos calculs.
        if monthly_rate > 0: # np.pmt standard
            monthly_payment = -np.pmt(monthly_rate, number_of_months, principal)
        # Le cas monthly_rate == 0 est déjà géré par annual_rate_percent == 0 plus haut.
        # Si on arrive ici avec monthly_rate == 0, c'est une erreur de logique ou un cas non prévu.
        # Cependant, pour la robustesse, si principal > 0 et number_of_months > 0 :
        elif principal > 0 and number_of_months > 0: # Fallback pour taux zéro si non capturé avant
            monthly_payment = principal / number_of_months
        else: # Aucun prêt ou durée nulle non capturé avant
            monthly_payment = 0

        annual_payment = monthly_payment * 12
        
        # Calcul des intérêts pour l'année en cours sur le capital restant dû au début de l'année
        interest_paid_this_year = principal * (annual_rate_percent / 100)
        
        # Le principal remboursé cette année est le paiement annuel moins les intérêts
        principal_paid_this_year = annual_payment - interest_paid_this_year
        
        # Ajustements pour la dernière année ou si le calcul est imprécis
        # S'assurer que le principal remboursé ne dépasse pas le capital restant dû
        if principal_paid_this_year > principal:
            principal_paid_this_year = principal
            # Recalculer l'annuité pour qu'elle corresponde exactement au remboursement final
            annual_payment = interest_paid_this_year + principal_paid_this_year
        
        # S'assurer que le principal remboursé n'est pas négatif (si les intérêts calculés > paiement)
        principal_paid_this_year = max(0, principal_paid_this_year)

    except Exception as e:
        # st.warning(f"Erreur calcul annuité: {e}. Principal: {principal}, Taux: {annual_rate_percent}, Années: {years_remaining}")
        # Fallback simple en cas d'erreur inattendue avec np.pmt
        if years_remaining > 0 and principal > 0 :
             annual_payment = principal / years_remaining # Simple division, moins précis
             interest_paid_this_year = 0 # Simplification
             principal_paid_this_year = annual_payment
        else:
            return 0,0,0 # Annuité, Intérêts, Principal remboursé

    return annual_payment, interest_paid_this_year, principal_paid_this_year


def run_simulation_for_scenario(scenario_data, duration_years):
    """Exécute la simulation pour un scénario donné."""
    
    # S'assurer que les DataFrames ont toutes les colonnes attendues.
    # Cela évite les KeyErrors si les données de session proviennent d'une ancienne structure.
    immo_df_orig = scenario_data["immobilier_df"].copy()
    immo_df = pd.DataFrame(columns=list(config_immobilier.keys())) # Crée un DF avec les bonnes colonnes
    if not immo_df_orig.empty:
        immo_df = pd.concat([immo_df, immo_df_orig], ignore_index=True)
    immo_df = immo_df.reindex(columns=list(config_immobilier.keys())) # Assure l'ordre et colonnes manquantes avec NaN

    plac_df_orig = scenario_data["placements_df"].copy()
    plac_df = pd.DataFrame(columns=list(config_placements.keys())) # Crée un DF avec les bonnes colonnes
    if not plac_df_orig.empty:
        plac_df = pd.concat([plac_df, plac_df_orig], ignore_index=True)
    plac_df = plac_df.reindex(columns=list(config_placements.keys())) # Assure l'ordre et colonnes manquantes avec NaN

    from pandas.api.types import is_any_real_numeric_dtype

    # Nettoyage des données d'entrée (conversion en numérique, gestion des NaN)
    for col in config_immobilier.keys():
        if col in immo_df.columns: # Vérifier si la colonne existe avant la conversion
#            if isinstance(config_immobilier[col], st.column_config.NumberColumn):
            if is_any_real_numeric_dtype(config_immobilier[col]):#, st.column_config.NumberColumn):
                 immo_df[col] = pd.to_numeric(immo_df[col], errors='coerce').fillna(0)
        else: # Si la colonne n'existe toujours pas (ne devrait pas arriver avec reindex), la créer avec 0
            if isinstance(config_immobilier[col], st.column_config.NumberColumn):
                immo_df[col] = 0


    for col in config_placements.keys():
        if col in plac_df.columns: # Vérifier si la colonne existe
            if is_any_real_numeric_dtype(config_placements[col]):#, st.column_config.NumberColumn):
            #if isinstance(config_placements[col], st.column_config.NumberColumn):
                plac_df[col] = pd.to_numeric(plac_df[col], errors='coerce').fillna(0)
        else: # Si la colonne n'existe toujours pas, la créer avec 0
             if isinstance(config_placements[col], st.column_config.NumberColumn):
                plac_df[col] = 0
    
    # Initialisation des listes pour stocker les résultats annuels
    annual_results = []
    
    # Valeurs initiales pour l'année 0
    current_immo_values = immo_df["Valeur Actuelle (€)"].copy()
    current_loan_principals = immo_df["Capital Restant Dû Emprunt (€)"].copy()
    current_loan_years_remaining = immo_df["Années Restantes Emprunt"].copy().astype(int) # S'assurer que c'est un entier
    
    current_plac_values = plac_df["Valeur Actuelle (€)"].copy()
    
    total_versements_cumules = 0

    # Enregistrement de l'état initial (Année 0)
    patrimoine_immo_net_annee_0 = (current_immo_values - current_loan_principals).sum()
    patrimoine_financier_annee_0 = current_plac_values.sum()
    patrimoine_total_net_annee_0 = patrimoine_immo_net_annee_0 + patrimoine_financier_annee_0
    total_dettes_annee_0 = current_loan_principals.sum()

    annual_results.append({
        "Année": 0,
        "Patrimoine Immobilier Brut (€)": current_immo_values.sum(),
        "Total Dettes (€)": total_dettes_annee_0,
        "Patrimoine Immobilier Net (€)": patrimoine_immo_net_annee_0,
        "Patrimoine Financier (€)": patrimoine_financier_annee_0,
        "Patrimoine Total Net (€)": patrimoine_total_net_annee_0,
        "Cumul Versements Placements (€)": total_versements_cumules
    })

    # Boucle de simulation pour chaque année
    for year in range(1, duration_years + 1):
        # --- Évolution Immobilier ---
        # Revalorisation
        current_immo_values *= (1 + immo_df["Rendement Annuel (%)"] / 100)
        
        # Remboursement des emprunts
        total_dettes_annee = 0
        for i in range(len(immo_df)): # itérer sur l'index du DataFrame immo_df
            if current_loan_principals.iloc[i] > 0 and current_loan_years_remaining.iloc[i] > 0:
                _, _, principal_paid = calculate_annual_loan_payment(
                    current_loan_principals.iloc[i],
                    immo_df.loc[i, "Taux Annuel Emprunt (%)"], # Utiliser .loc pour accéder par label d'index et nom de colonne
                    current_loan_years_remaining.iloc[i]
                )
                current_loan_principals.iloc[i] -= principal_paid
                current_loan_principals.iloc[i] = max(0, current_loan_principals.iloc[i]) 
                current_loan_years_remaining.iloc[i] -= 1
                current_loan_years_remaining.iloc[i] = max(0, current_loan_years_remaining.iloc[i])
            total_dettes_annee += current_loan_principals.iloc[i]

        patrimoine_immo_brut = current_immo_values.sum()
        patrimoine_immo_net = (current_immo_values - current_loan_principals).sum()

        # --- Évolution Placements Financiers ---
        # S'assurer que "Versement Mensuel (€)" existe avant de l'utiliser
        versements_annuels_placements = 0
        if "Versement Mensuel (€)" in plac_df.columns:
            versements_annuels_placements = (plac_df["Versement Mensuel (€)"] * 12).sum()
        
        total_versements_cumules += versements_annuels_placements
        
        # Ajout des versements mensuels (annualisés)
        if "Versement Mensuel (€)" in plac_df.columns:
            current_plac_values += (plac_df["Versement Mensuel (€)"] * 12)
        # Revalorisation
        current_plac_values *= (1 + plac_df["Rendement Annuel (%)"] / 100)
        
        patrimoine_financier = current_plac_values.sum()

        # --- Aggrégation des résultats pour l'année ---
        patrimoine_total_net = patrimoine_immo_net + patrimoine_financier
        
        annual_results.append({
            "Année": year,
            "Patrimoine Immobilier Brut (€)": patrimoine_immo_brut,
            "Total Dettes (€)": total_dettes_annee,
            "Patrimoine Immobilier Net (€)": patrimoine_immo_net,
            "Patrimoine Financier (€)": patrimoine_financier,
            "Patrimoine Total Net (€)": patrimoine_total_net,
            "Cumul Versements Placements (€)": total_versements_cumules
        })
        
    return pd.DataFrame(annual_results)


# --- Titre de l'application ---
st.set_page_config(layout="wide", page_title="Simulateur Patrimoine")
st.title("Simulateur d'Évolution de Patrimoine Multi-Scénarios")

# --- Barre latérale ---
st.sidebar.header("Paramètres de Simulation")
simulation_duration = st.sidebar.number_input(
    "Durée de la simulation (années)", 
    min_value=1, max_value=50, value=10, step=1,
    help="Nombre d'années sur lesquelles la simulation sera effectuée."
)

st.sidebar.header("Gestion des Scénarios")

def add_new_scenario():
    st.session_state.scenario_counter += 1
    new_scenario_name = f"Scénario {st.session_state.scenario_counter}"
    
    # S'assurer que les DataFrames par défaut ont bien toutes les colonnes définies dans les configs
    clean_default_immobilier_df = pd.DataFrame(columns=list(config_immobilier.keys()))
    clean_default_placements_df = pd.DataFrame(columns=list(config_placements.keys()))

    if not st.session_state.scenarios:
        new_scenario_data = {
            "name": new_scenario_name,
            "immobilier_df": clean_default_immobilier_df.copy(),
            "placements_df": clean_default_placements_df.copy(),
            "simulation_results": None 
        }
    else:
        initial_scenario_template = st.session_state.scenarios[0]
        
        # S'assurer que le template a aussi les bonnes colonnes avant la copie
        template_immo_df = initial_scenario_template["immobilier_df"].copy().reindex(columns=list(config_immobilier.keys()))
        template_plac_df = initial_scenario_template["placements_df"].copy().reindex(columns=list(config_placements.keys()))

        new_scenario_data = {
            "name": new_scenario_name,
            "immobilier_df": copy.deepcopy(template_immo_df),
            "placements_df": copy.deepcopy(template_plac_df),
            "simulation_results": None
        }
    st.session_state.scenarios.append(new_scenario_data)

if not st.session_state.scenarios:
    add_new_scenario() 

if st.sidebar.button("➕ Ajouter un Scénario", help="Crée un nouveau scénario (copie du Scénario 1 si existant)."):
    add_new_scenario()
    st.rerun() 

# --- Affichage des scénarios et du bilan ---
if st.session_state.scenarios:
    tab_names = [s["name"] for s in st.session_state.scenarios]
    all_tab_titles = tab_names + ["📊 Bilan Comparatif"]
    
    active_tabs = st.tabs(all_tab_titles) # Renommé pour éviter conflit avec variable 'tabs' potentielle

    for i, tab_content in enumerate(active_tabs[:-1]): 
        with tab_content:
            # Vérifier si l'index i est valide pour st.session_state.scenarios
            if i < len(st.session_state.scenarios):
                current_scenario = st.session_state.scenarios[i]
            else:
                st.error("Erreur: Incohérence dans le nombre de scénarios et d'onglets. Veuillez rafraîchir.")
                continue # Passer à l'itération suivante

            st.header(f"Configuration et Résultats du {current_scenario['name']}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🏦 Biens Immobiliers")
                # S'assurer que le DataFrame passé à data_editor a les bonnes colonnes
                df_immo_editor = current_scenario["immobilier_df"].copy().reindex(columns=list(config_immobilier.keys()))
                edited_immobilier_df = st.data_editor(
                    df_immo_editor, # Utiliser le DataFrame réindexé
                    column_config=config_immobilier,
                    num_rows="dynamic",
                    key=f"immobilier_editor_{current_scenario['name']}_{i}",
                    use_container_width=True, hide_index=True
                )
                st.session_state.scenarios[i]["immobilier_df"] = edited_immobilier_df
            
            with col2:
                st.markdown("#### 📈 Placements Financiers")
                df_plac_editor = current_scenario["placements_df"].copy().reindex(columns=list(config_placements.keys()))
                edited_placements_df = st.data_editor(
                    df_plac_editor, # Utiliser le DataFrame réindexé
                    column_config=config_placements,
                    num_rows="dynamic",
                    key=f"placements_editor_{current_scenario['name']}_{i}",
                    use_container_width=True, hide_index=True
                )
                st.session_state.scenarios[i]["placements_df"] = edited_placements_df
            
            st.markdown("---")
            if st.button(f"🚀 Lancer/Relancer la simulation pour {current_scenario['name']}", key=f"simulate_btn_{current_scenario['name']}_{i}"):
                with st.spinner(f"Calcul de la simulation pour {current_scenario['name']}..."):
                    results_df = run_simulation_for_scenario(current_scenario, simulation_duration)
                    st.session_state.scenarios[i]["simulation_results"] = results_df
                st.success(f"Simulation terminée pour {current_scenario['name']}!")

            if st.session_state.scenarios[i]["simulation_results"] is not None:
                results_df = st.session_state.scenarios[i]["simulation_results"]
                st.subheader("Résultats de la Simulation")

                st.markdown("##### Évolution du Patrimoine Net Total")
                fig_patrimoine = px.line(results_df, x="Année", y="Patrimoine Total Net (€)", title="Patrimoine Net Total (€) vs. Année")
                fig_patrimoine.update_layout(yaxis_title="Patrimoine Total Net (€)")
                st.plotly_chart(fig_patrimoine, use_container_width=True)

                st.markdown("##### Cumul des Versements sur Placements")
                fig_versements = px.line(results_df, x="Année", y="Cumul Versements Placements (€)", title="Cumul des Versements (€) vs. Année")
                fig_versements.update_layout(yaxis_title="Cumul Versements Placements (€)")
                st.plotly_chart(fig_versements, use_container_width=True)
                
                st.markdown("##### Détail de l'évolution du patrimoine")
                fig_details_patrimoine = px.line(results_df, x="Année", 
                                                 y=["Patrimoine Immobilier Net (€)", "Patrimoine Financier (€)", "Total Dettes (€)"],
                                                 title="Composition du Patrimoine et Dettes vs. Année")
                fig_details_patrimoine.update_layout(yaxis_title="Montant (€)")
                st.plotly_chart(fig_details_patrimoine, use_container_width=True)

                with st.expander("Voir le tableau détaillé des résultats"):
                    st.dataframe(results_df.style.format({
                        "Patrimoine Immobilier Brut (€)": "€{:,.2f}",
                        "Total Dettes (€)": "€{:,.2f}",
                        "Patrimoine Immobilier Net (€)": "€{:,.2f}",
                        "Patrimoine Financier (€)": "€{:,.2f}",
                        "Patrimoine Total Net (€)": "€{:,.2f}",
                        "Cumul Versements Placements (€)": "€{:,.2f}"
                    }), use_container_width=True)

    # Onglet Bilan Comparatif
    with active_tabs[-1]:
        st.header("📊 Bilan Comparatif des Scénarios")
        
        simulated_scenarios = [s for s in st.session_state.scenarios if s.get("simulation_results") is not None and not s["simulation_results"].empty]

        if not simulated_scenarios:
            st.info("Aucune simulation n'a encore été lancée ou les résultats sont vides. Veuillez lancer une simulation dans un des scénarios pour voir le bilan comparatif.")
        else:
            st.subheader("Comparaison de l'Évolution du Patrimoine Net Total")
            comparison_patrimoine_df = pd.DataFrame()
            for scenario in simulated_scenarios:
                results = scenario["simulation_results"]
                if "Année" in results.columns and "Patrimoine Total Net (€)" in results.columns:
                    temp_df = results[["Année", "Patrimoine Total Net (€)"]].set_index("Année")
                    temp_df = temp_df.rename(columns={"Patrimoine Total Net (€)": scenario["name"]})
                    if comparison_patrimoine_df.empty:
                        comparison_patrimoine_df = temp_df
                    else:
                        comparison_patrimoine_df = comparison_patrimoine_df.join(temp_df, how='outer')
            
            if not comparison_patrimoine_df.empty:
                comparison_patrimoine_df = comparison_patrimoine_df.reset_index()
                df_melted = comparison_patrimoine_df.melt(id_vars=['Année'], var_name='Scénario', value_name='Patrimoine Total Net (€)')
                
                # S'assurer que la colonne 'Patrimoine Total Net (€)' est numérique pour le graphique
                df_melted['Patrimoine Total Net (€)'] = pd.to_numeric(df_melted['Patrimoine Total Net (€)'], errors='coerce')
                df_melted.dropna(subset=['Patrimoine Total Net (€)'], inplace=True)


                fig_comp_evol = px.line(df_melted, x="Année", y="Patrimoine Total Net (€)", color="Scénario",
                                        title="Évolution Comparée du Patrimoine Net Total par Scénario")
                fig_comp_evol.update_layout(yaxis_title="Patrimoine Total Net (€)")
                st.plotly_chart(fig_comp_evol, use_container_width=True)
            else:
                st.warning("Données insuffisantes ou incorrectes pour le graphique d'évolution comparée.")

            st.subheader("Comparaison des Valeurs Finales (Après Simulation)")
            final_values_data = []
            for scenario in simulated_scenarios:
                if not scenario["simulation_results"].empty:
                    final_row = scenario["simulation_results"].iloc[-1]
                    final_values_data.append({
                        "Scénario": scenario["name"],
                        "Patrimoine Total Net Final (€)": final_row.get("Patrimoine Total Net (€)"),
                        "Cumul Versements Placements Final (€)": final_row.get("Cumul Versements Placements (€)"),
                        "Patrimoine Immobilier Net Final (€)": final_row.get("Patrimoine Immobilier Net (€)"),
                        "Patrimoine Financier Final (€)": final_row.get("Patrimoine Financier (€)"),
                    })
            
            if final_values_data:
                final_values_df = pd.DataFrame(final_values_data)
                
                st.markdown("##### Tableau Récapitulatif des Valeurs Finales")
                st.dataframe(final_values_df.style.format({
                    "Patrimoine Total Net Final (€)": "€{:,.2f}",
                    "Cumul Versements Placements Final (€)": "€{:,.2f}",
                    "Patrimoine Immobilier Net Final (€)": "€{:,.2f}",
                    "Patrimoine Financier Final (€)": "€{:,.2f}"
                }), use_container_width=True)

                fig_bar_patrimoine = px.bar(final_values_df, x="Scénario", y="Patrimoine Total Net Final (€)", 
                                            color="Scénario", title="Patrimoine Total Net Final par Scénario")
                fig_bar_patrimoine.update_layout(yaxis_title="Montant (€)")
                st.plotly_chart(fig_bar_patrimoine, use_container_width=True)

                fig_bar_versements = px.bar(final_values_df, x="Scénario", y="Cumul Versements Placements Final (€)", 
                                             color="Scénario", title="Cumul des Versements Final par Scénario")
                fig_bar_versements.update_layout(yaxis_title="Montant (€)")
                st.plotly_chart(fig_bar_versements, use_container_width=True)
            else:
                st.warning("Données insuffisantes pour le tableau et graphiques des valeurs finales.")
else:
    st.info("Cliquez sur '➕ Ajouter un Scénario' dans la barre latérale pour commencer.")

# --- Pour le débogage ---
# with st.sidebar.expander("Afficher l'état de la session (pour débogage)"):
#    st.write(st.session_state)

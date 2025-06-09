# Fichier: ui_components.py (version mise à jour pour simulation manuelle)
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy_financial as npf
from simulation import run_unified_simulation, calculate_monthly_payment

def setup_sidebar():
    """
    Configure et affiche la barre latérale de l'application Streamlit pour recueillir les paramètres de l'utilisateur.
    """
    st.sidebar.title("👨‍💼 Vos Paramètres")
    st.sidebar.header("Situation Initiale")
    initial_capital = st.sidebar.number_input("Capital de départ (€)", 0, value=20000, step=1000)
    monthly_investment = st.sidebar.number_input("Épargne mensuelle (€)", 0, value=500, step=50)
    investment_horizon = st.sidebar.slider("Horizon de temps (années)", 5, 40, 20, 1)

    st.sidebar.header("Fiscalité")
    marginal_tax_rate = st.sidebar.selectbox("Taux Marginal d'Imposition (TMI) (%)", options=[0, 11, 30, 41, 45], index=2)
    per_deduction_limit = st.sidebar.number_input("Plafond Annuel PER (€)", 0, value=4399, step=100)

    st.sidebar.header("Sélection des Investissements")
    df_options_financiers = pd.DataFrame(
        {'Actif': [True, True, True],
         'Rendement Annuel (%)': [3.5, 4.0, 4.5],
         'Frais Entrée (%)': [1.0, 2.0, 5.0],
         'Frais Gestion Annuels (%)': [0.6, 0.8, 0.5]},
        index=["Assurance-Vie", "PER", "SCPI"]
    )
    df_options_financiers_edited = st.sidebar.data_editor(
        df_options_financiers,
        column_config={"Actif": st.column_config.CheckboxColumn("Activer ?", default=True)}
    )

    include_immo = st.sidebar.checkbox("Inclure un projet immobilier (achat en Année 1 sans apport)", value=True)

    st.sidebar.header("Hypothèses Projet Immobilier")
    fix_immo_price = st.checkbox("Fixer le prix du bien immobilier", value=False, disabled=not include_immo)
    fixed_immo_price = st.number_input("Prix fixe du bien (€)", 0, 2000000, 150000, 1000, disabled=not (include_immo and fix_immo_price))
    immo_price_range = st.slider("Fourchette de prix du bien (€)", 0, 1000000, (0, 150000), step=10000, disabled=not include_immo or fix_immo_price)
    loan_params = {'mensualite_max': st.sidebar.number_input("Mensualité max de prêt (€)", 50, 5000, 1000, 50, disabled=not include_immo)}
    immo_params = {
        'rendement_locatif_brut': st.sidebar.slider("Rdt Locatif Brut (%)", 2.0, 8.0, 5.0, 0.1, disabled=not include_immo),
        'charges_pct': st.sidebar.slider("Charges annuelles (% loyer)", 0, 30, 15, 1, disabled=not include_immo),
        'frais_notaire_pct': st.sidebar.slider("Frais d'acquisition (%)", 5.0, 12.0, 8.0, 0.5, disabled=not include_immo),
        'immo_reval_rate': st.sidebar.slider("Reval. annuelle du bien (%)", -2.0, 5.0, 1.5, 0.1, disabled=not include_immo)
    }
    loan_params.update({
        'rate': st.sidebar.slider("Taux crédit immo (%)", 1.0, 6.0, 3.5, 0.1, disabled=not include_immo),
        'duration': st.sidebar.slider("Durée crédit (ans)", 10, 25, 20, 1, disabled=not include_immo)
    })

    # <<< AJOUT : Section pour l'allocation manuelle >>>
    st.sidebar.header("Allocation Manuelle (pour Simulation)")
    st.sidebar.caption("Utilisez ces sliders pour définir une stratégie manuelle, puis cliquez sur 'Lancer la Simulation Manuelle'.")
    
    active_financial_assets = df_options_financiers_edited[df_options_financiers_edited['Actif']].index.tolist()
    manual_allocations = {}
    if active_financial_assets:
        for asset in active_financial_assets:
            manual_allocations[asset] = st.sidebar.slider(f"Allocation {asset} (%)", 0, 100, 100 // len(active_financial_assets), 1)
    else:
        st.sidebar.info("Aucun actif financier sélectionné.")
    # <<< FIN DE L'AJOUT >>>

    return {
        "initial_capital": initial_capital,
        "monthly_investment": monthly_investment,
        "investment_horizon": investment_horizon,
        "marginal_tax_rate": marginal_tax_rate,
        "per_deduction_limit": per_deduction_limit,
        "df_options_financiers_edited": df_options_financiers_edited,
        "include_immo": include_immo,
        "loan_params": loan_params,
        "immo_price_range": immo_price_range,
        "immo_params": immo_params,
        "fix_immo_price": fix_immo_price,
        "fixed_immo_price": fixed_immo_price,
        "manual_allocations": manual_allocations # <<< AJOUT : On retourne les allocations manuelles
    }

# Le reste du fichier (display_results, etc.) ne change pas.
def display_results(opt_result, simulation_args):
    st.subheader("📊 Résultat de la Stratégie")
    with st.expander("Voir le journal de l'optimiseur", expanded=not opt_result.success):
        st.text(f"Message de l'optimiseur : {opt_result.message}")
        st.text(f"Convergence réussie : {opt_result.success}")
    if not opt_result.success:
        st.error("L'optimisation n'a pas pu converger.")
        if simulation_args[5] is not None and 'x' in opt_result and len(opt_result.x) > 0:
             st.subheader("🕵️ Diagnostic de l'Échec")
             last_immo_price = opt_result.x[-1]
             loan_amount = last_immo_price
             loan_params = simulation_args[6]
             calculated_payment = calculate_monthly_payment(loan_amount, loan_params['rate'], loan_params['duration'])
             st.warning(f"La mensualité calculée ({calculated_payment:,.0f} €) pour le dernier bien testé à {last_immo_price:,.0f} € dépasse probablement votre maximum autorisé de {loan_params['mensualite_max']:,.0f} €.")
        return
    optimal_vars = opt_result.x
    _, final_patrimoine, final_crd, historique, event_logs, kpis, _ = run_unified_simulation(optimal_vars, *simulation_args)
    final_net_worth = historique['Total Net'].iloc[-1]
    st.success(f"**Patrimoine Net Final Estimé : {final_net_worth:,.0f} €**")
    display_kpis(historique, final_net_worth, kpis, simulation_args[1], simulation_args[2])
    display_allocations_and_charts(final_patrimoine, final_crd, historique, event_logs, kpis, optimal_vars, simulation_args)

def display_kpis(historique, final_net_worth, kpis, initial_capital, monthly_investment):
    st.subheader("Indicateurs Clés de Performance (KPIs)")
    flow_cols = [col for col in historique.columns if 'Flux' in col]
    total_flux_invested = historique[flow_cols].sum().sum()
    total_invested = initial_capital + total_flux_invested
    if kpis.get('leaked_cash', 0) > 0:
        st.warning(f"**Flux non investi :** {kpis['leaked_cash']:,.0f} € n'ont pas pu être investis.")
    investment_horizon = len(historique) - 1
    cash_flows = [-initial_capital] + [-monthly_investment * 12] * investment_horizon
    cash_flows[-1] += final_net_worth
    irr = npf.irr(cash_flows) if total_invested > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Plus-Value Nette Totale", f"{final_net_worth - total_invested:,.0f} €")
    col2.metric("Total des Versements", f"{total_invested:,.0f} €")
    col3.metric("Rendement Annuel Moyen (TRI)", f"{irr:.2%}")

def display_allocations_and_charts(final_patrimoine, final_crd, historique, event_logs, kpis, optimal_vars, simulation_args):
    """Affiche les détails de l'allocation, les bilans et les graphiques."""
    asset_names, initial_capital, monthly_investment, _, _, _, loan_params, _, _ = simulation_args

    # --- CORRECTION DÉFINITIVE ---
    # Logique simplifiée et robuste pour déterminer si l'immo est inclus
    if len(optimal_vars) > len(asset_names):
        alloc_vars_df = optimal_vars[:-1]
        include_immo = True
    else:
        alloc_vars_df = optimal_vars
        include_immo = False

    st.subheader("Détails de la Stratégie Optimale")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if len(alloc_vars_df) > 0:
            df_alloc = pd.DataFrame(alloc_vars_df, index=asset_names, columns=['Poids'])
            st.write("**Allocation de l'Épargne Mensuelle**")
            df_alloc_monthly = df_alloc.copy()
            df_alloc_monthly['Montant Mensuel'] = df_alloc_monthly['Poids'] * monthly_investment
            st.dataframe(df_alloc_monthly[df_alloc_monthly['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant Mensuel': '{:,.0f} €'}))
            
            st.write("**Répartition du Capital de Départ**")
            df_alloc_capital = df_alloc.copy()
            df_alloc_capital['Montant'] = df_alloc_capital['Poids'] * initial_capital
            st.dataframe(df_alloc_capital[df_alloc_capital['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant': '{:,.0f} €'}))
        else:
            st.write("**Allocation d'actifs financiers**")
            st.info("Aucun actif financier sélectionné.")

    # On ajoute une vérification explicite que loan_params n'est pas None
    if include_immo and loan_params:
        with col2:
            st.write("**Bilan du Projet Immobilier**")
            optimal_immo_price = optimal_vars[-1]
            final_mensualite = calculate_monthly_payment(optimal_immo_price, loan_params['rate'], loan_params['duration'])
            st.metric(label="Prix d'achat du bien visé", value=f"{optimal_immo_price:,.0f} €", help=f"Mensualité de prêt associée : {final_mensualite:,.0f} €/mois")
            st.text(f"Total Loyers Perçus : {kpis.get('total_rent_received', 0):,.0f} €")
            st.text(f"Total Intérêts Payés : {kpis.get('total_interest_paid', 0):,.0f} €")
            st.text(f"Total Impôts Locatifs : {kpis.get('total_rental_tax', 0):,.0f} €")
    
    if kpis.get('total_tax_saving_per', 0) > 0:
        st.info(f"💰 **Gain fiscal total grâce au PER : {kpis['total_tax_saving_per']:,.0f} €** (réinvesti)")
    
    if event_logs:
        st.write("**Journal des Événements Clés**"); 
        for log in event_logs: st.info(f"{log}")

    st.subheader("Analyse Visuelle de la Stratégie")
    net_assets = {k: v for k, v in final_patrimoine.items() if v > 1}
    if 'Immobilier (Bien)' in net_assets and net_assets['Immobilier (Bien)'] > 0:
        net_assets['Immobilier (Patrimoine Net)'] = net_assets.pop('Immobilier (Bien)') - final_crd
    
    df_final_comp = pd.DataFrame(net_assets.values(), index=net_assets.keys(), columns=['Valeur'])
    if not df_final_comp.empty:
        fig_pie = px.pie(df_final_comp, values='Valeur', names=df_final_comp.index, title="Composition du Patrimoine Net Final", hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    df_plot = historique.drop(columns=[col for col in historique.columns if 'Flux' in col or 'Dette' in col or 'Total' in col or 'Soutien' in col])
    df_plot = df_plot.loc[:, (df_plot.abs().sum() > 0)]
    if not df_plot.empty:
        fig_area = px.area(df_plot, x=df_plot.index, y=df_plot.columns, title="Évolution de la Composition du Patrimoine Brut", labels={'index': 'Année', 'value': 'Valeur (€)', 'variable': 'Actif'})
        st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("Tableau de Bord Annuel"); st.dataframe(historique.style.format(formatter="{:,.0f} €", subset=pd.IndexSlice[:, [col for col in historique.columns if 'Flux' not in col and 'Soutien' not in col]]))
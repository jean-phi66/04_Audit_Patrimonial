# optimizer_app.py
import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.optimize import minimize, LinearConstraint, NonlinearConstraint
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Optimiseur d'Allocation Patrimoniale",
    page_icon="🚀",
    layout="wide"
)

# --- FONCTIONS DE SIMULATION ET D'OPTIMISATION ---
def calculate_monthly_payment(loan_amount, rate_pct, duration_years):
    if loan_amount <= 0 or duration_years <= 0 or rate_pct < 0: return 0
    monthly_rate = (rate_pct / 100) / 12
    n_months = duration_years * 12
    if n_months <= 0: return float('inf')
    return -npf.pmt(monthly_rate, n_months, loan_amount)

def run_unified_simulation(optimization_vars, asset_names, initial_capital, monthly_investment, investment_horizon, df_options_financiers, immo_params, loan_params, marginal_tax_rate, per_deduction_limit):
    include_immo = immo_params is not None
    financial_asset_names = [name for name in asset_names if name != 'Projet Immobilier']
    if include_immo:
        allocation_weights = optimization_vars[:-1] if len(financial_asset_names) > 0 else []
        target_immo_price = optimization_vars[-1]
    else:
        allocation_weights, target_immo_price = optimization_vars, 0
    
    allocation = dict(zip(financial_asset_names, allocation_weights))

    patrimoine = {asset: 0.0 for asset in financial_asset_names}
    patrimoine['Immobilier (Bien)'] = 0.0
    
    flow_cols = [f"Flux {name}" for name in financial_asset_names]
    historique_cols = list(patrimoine.keys()) + ['Dette Immobilière', 'Total Net', 'Soutien Épargne Immo'] + flow_cols
    historique = pd.DataFrame(0.0, index=range(investment_horizon + 1), columns=historique_cols)
    kpi_trackers = {'total_tax_saving_per': 0, 'total_rental_tax': 0, 'total_interest_paid': 0, 'total_rent_received': 0, 'leaked_cash': 0}
    event_logs, penalty = [], 0.0
    
    loan_crd, annuite_pret, immo_purchase_done = 0, 0, False

    for asset, weight in allocation.items():
        if asset in patrimoine:
            frais_entree = df_options_financiers.loc[asset, 'Frais Entrée (%)']/100
            capital_flow = initial_capital * weight
            patrimoine[asset] += capital_flow * (1 - frais_entree)
            historique.loc[0, f"Flux {asset}"] = capital_flow

    for year in range(1, investment_horizon + 1):
        if include_immo and not immo_purchase_done and year == 1:
            immo_purchase_done = True
            loan_amount = target_immo_price
            event_logs.append(f"Année 1: Achat d'un bien de {target_immo_price:,.0f} € financé à 100%.")
            patrimoine['Immobilier (Bien)'] = target_immo_price * (1 - immo_params['frais_notaire_pct']/100)
            loan_crd, annuite_pret = loan_amount, calculate_monthly_payment(loan_amount, loan_params['rate'], loan_params['duration']) * 12

        for asset in df_options_financiers.index:
            if asset in patrimoine and patrimoine[asset] > 0:
                patrimoine[asset] *= (1 + df_options_financiers.loc[asset, 'Rendement Annuel (%)']/100 - df_options_financiers.loc[asset, 'Frais Gestion Annuels (%)']/100)
        
        if immo_purchase_done: patrimoine['Immobilier (Bien)'] *= (1 + immo_params['immo_reval_rate']/100)

        annual_savings = monthly_investment * 12
        net_immo_cash_flow = 0
        if immo_purchase_done:
            loyer_annuel = target_immo_price * (immo_params['rendement_locatif_brut'] / 100)
            interets, amortissement = loan_crd * (loan_params['rate']/100), (target_immo_price * 0.85)/30
            revenu_imposable = loyer_annuel - ((loyer_annuel*immo_params['charges_pct']/100) + interets + amortissement)
            impot_locatif = max(0, revenu_imposable) * (marginal_tax_rate/100 + 0.172)
            remb_capital = min(loan_crd, annuite_pret - interets)
            loan_crd = max(0, loan_crd - remb_capital)
            net_immo_cash_flow = loyer_annuel - annuite_pret - (loyer_annuel*immo_params['charges_pct']/100) - impot_locatif
            kpi_trackers.update({'total_rent_received': kpi_trackers['total_rent_received'] + loyer_annuel, 'total_interest_paid': kpi_trackers['total_interest_paid'] + interets, 'total_rental_tax': kpi_trackers['total_rental_tax'] + impot_locatif})
            historique.loc[year, 'Soutien Épargne Immo'] = max(0, -net_immo_cash_flow)
        
        cash_for_investment = annual_savings + net_immo_cash_flow
        if cash_for_investment < 0:
            penalty += abs(cash_for_investment) * 2; cash_for_investment = 0
            event_logs.append(f"⚠️ Année {year}: Épargne mensuelle insuffisante pour couvrir le déficit immobilier.")

        per_weight = allocation.get('PER', 0)
        total_invested_this_year = cash_for_investment
        if per_weight > 0.001 and total_invested_this_year * per_weight > per_deduction_limit:
            total_invested_this_year = per_deduction_limit / per_weight
        
        per_contribution_this_year = total_invested_this_year * per_weight
        
        for asset, weight in allocation.items():
            flow_amount = total_invested_this_year * weight
            patrimoine[asset] += flow_amount * (1 - df_options_financiers.loc[asset, 'Frais Entrée (%)']/100)
            historique.loc[year, f"Flux {asset}"] = flow_amount

        tax_saving = 0
        if per_contribution_this_year > 0:
            tax_saving = per_contribution_this_year * (marginal_tax_rate / 100)
            kpi_trackers['total_tax_saving_per'] += tax_saving
            if tax_saving > 0:
                reinvested_tax_saving = 0
                for asset, weight in allocation.items():
                    reinvestment_amount = tax_saving * weight
                    current_per_total = historique.loc[year, "Flux PER"] if "Flux PER" in historique.columns else 0
                    if asset == 'PER' and current_per_total + reinvestment_amount > per_deduction_limit:
                       reinvestment_amount = max(0, per_deduction_limit - current_per_total)
                    
                    patrimoine[asset] += reinvestment_amount * (1 - (df_options_financiers.loc[asset, 'Frais Entrée (%)']/100))
                    if f"Flux {asset}" in historique.columns:
                        historique.loc[year, f"Flux {asset}"] += reinvestment_amount
                    reinvested_tax_saving += reinvestment_amount
                
                if tax_saving > reinvested_tax_saving:
                    kpi_trackers['leaked_cash'] += (tax_saving - reinvested_tax_saving)

        for col in patrimoine: historique.loc[year, col] = patrimoine.get(col, 0)
        historique.loc[year, 'Dette Immobilière'] = -loan_crd
        historique.loc[year, 'Total Net'] = sum(patrimoine.values()) - loan_crd

    final_net_worth = historique['Total Net'].iloc[-1] - penalty
    return final_net_worth, patrimoine, loan_crd, historique, event_logs, kpi_trackers

def objective_function(optimization_vars, *args):
    final_net_worth, _, _, _, _, _ = run_unified_simulation(optimization_vars, *args)
    return -final_net_worth

# --- INTERFACE UTILISATEUR ---
st.sidebar.title("👨‍💼 Vos Paramètres")
st.sidebar.header("Situation Initiale")
initial_capital = st.sidebar.number_input("Capital de départ (€)", 0, value=20000, step=1000)
monthly_investment = st.sidebar.number_input("Épargne mensuelle (€)", 0, value=500, step=50)
investment_horizon = st.sidebar.slider("Horizon de temps (années)", 5, 40, 20, 1)
st.sidebar.header("Fiscalité")
marginal_tax_rate = st.sidebar.selectbox("Taux Marginal d'Imposition (TMI) (%)", options=[0, 11, 30, 41, 45], index=2)
per_deduction_limit = st.sidebar.number_input("Plafond Annuel PER (€)", 0, value=4399, step=100)
st.sidebar.header("Sélection des Investissements")
df_options_financiers = pd.DataFrame({'Actif': [True, True, True], 'Rendement Annuel (%)': [3.5, 4.0, 4.5], 'Frais Entrée (%)': [1.0, 2.0, 5.0], 'Frais Gestion Annuels (%)': [0.6, 0.8, 0.5]}, index=["Assurance-Vie", "PER", "SCPI"])
df_options_financiers_edited = st.sidebar.data_editor(df_options_financiers, column_config={"Actif": st.column_config.CheckboxColumn("Activer ?", default=True)})
include_immo = st.sidebar.checkbox("Inclure un projet immobilier (achat en Année 1 sans apport)", value=True)
st.sidebar.header("Hypothèses Projet Immobilier")
loan_params = {'mensualite_max': st.sidebar.number_input("Mensualité max de prêt (€)", 50, 5000, 1000, 50, disabled=not include_immo)}
immo_price_range = st.sidebar.slider("Fourchette de prix du bien (€)", 0, 1000000, (0, 150000), step=10000, disabled=not include_immo)
immo_params = {'rendement_locatif_brut': st.sidebar.slider("Rdt Locatif Brut (%)", 2.0, 8.0, 5.0, 0.1, disabled=not include_immo), 'charges_pct': st.sidebar.slider("Charges annuelles (% loyer)", 0, 30, 15, 1, disabled=not include_immo), 'frais_notaire_pct': st.sidebar.slider("Frais d'acquisition (%)", 5.0, 12.0, 8.0, 0.5, disabled=not include_immo), 'immo_reval_rate': st.sidebar.slider("Reval. annuelle du bien (%)", -2.0, 5.0, 1.5, 0.1, disabled=not include_immo)}
loan_params.update({'rate': st.sidebar.slider("Taux crédit immo (%)", 1.0, 6.0, 3.5, 0.1, disabled=not include_immo), 'duration': st.sidebar.slider("Durée crédit (ans)", 10, 25, 20, 1, disabled=not include_immo)})

# --- PAGE PRINCIPALE ---
st.title("🚀 Optimiseur d'Allocation Patrimoniale")

if st.button("Lancer l'Optimisation", type="primary", use_container_width=True):
    with st.spinner("Optimisation en cours..."):
        
        active_financial_assets = df_options_financiers_edited[df_options_financiers_edited['Actif']].drop(columns=['Actif'])
        asset_names = active_financial_assets.index.tolist()
        
        if not asset_names and not include_immo:
            st.warning("Veuillez activer au moins un type d'investissement.")
        else:
            df_options_for_optim = active_financial_assets.copy()
            
            # --- Configuration de l'optimiseur ---
            if include_immo:
                num_alloc_vars = len(asset_names)
                initial_guess = np.array([1.0/num_alloc_vars if num_alloc_vars > 0 else 0.0]*num_alloc_vars + [np.mean(immo_price_range)])
                bounds = ([(0,1)]*num_alloc_vars if num_alloc_vars > 0 else []) + [immo_price_range]
                def check_mensualite(x): return loan_params['mensualite_max'] - calculate_monthly_payment(x[-1], loan_params['rate'], loan_params['duration'])
                constraints = []
                if num_alloc_vars > 0:
                    constraints.append({'type': 'eq', 'fun': lambda x: 1 - np.sum(x[:-1])})
                constraints.append({'type': 'ineq', 'fun': check_mensualite})
                args = (asset_names, initial_capital, monthly_investment, investment_horizon, df_options_for_optim, immo_params, loan_params, marginal_tax_rate, per_deduction_limit)
            else:
                num_alloc_vars = len(asset_names)
                initial_guess, bounds = np.array([1.0/num_alloc_vars]*num_alloc_vars), [(0,1)]*num_alloc_vars
                constraints = [{'type': 'eq', 'fun': lambda x: 1 - np.sum(x)}]
                args = (asset_names, initial_capital, monthly_investment, investment_horizon, df_options_for_optim, None, None, marginal_tax_rate, per_deduction_limit)

            opt_result = minimize(objective_function, initial_guess, args=args, method='SLSQP', bounds=bounds, constraints=constraints, options={'maxiter': 500, 'ftol': 1e-9})
            
            # --- Affichage des résultats ---
            st.subheader("📊 Résultat de la Stratégie")

            with st.expander("Voir le journal de l'optimiseur", expanded=not opt_result.success):
                st.text(f"Message de l'optimiseur : {opt_result.message}")
                st.text(f"Convergence réussie : {opt_result.success}")

            if opt_result.success:
                optimal_vars = opt_result.x
                _, final_patrimoine, final_crd, historique, event_logs, kpis = run_unified_simulation(optimal_vars, *args)
                final_net_worth = historique['Total Net'].iloc[-1]

                st.success(f"**Patrimoine Net Final Estimé : {final_net_worth:,.0f} €**")
                
                st.subheader("Indicateurs Clés de Performance (KPIs)")
                flow_cols = [col for col in historique.columns if 'Flux' in col]
                total_flux_invested = historique[flow_cols].sum().sum()
                total_invested = initial_capital + total_flux_invested
                
                if kpis.get('leaked_cash', 0) > 0:
                    st.warning(f"**Flux non investi :** {kpis['leaked_cash']:,.0f} € n'ont pas pu être investis faute de support disponible et sont considérés comme perdus.")
                
                cash_flows = [-initial_capital] + [-monthly_investment * 12] * investment_horizon
                cash_flows[-1] += final_net_worth
                irr = npf.irr(cash_flows) if total_invested > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Plus-Value Nette Totale", f"{final_net_worth - total_invested:,.0f} €")
                col2.metric("Total des Versements (Capital + Épargne)", f"{total_invested:,.0f} €")
                col3.metric("Rendement Annuel Moyen (TRI)", f"{irr:.2%}")
                
                st.subheader("Détails de la Stratégie Optimale")
                col1, col2 = st.columns([1, 2])
                with col1:
                    alloc_vars_df = optimal_vars[:-1] if include_immo else optimal_vars
                    df_alloc = pd.DataFrame(alloc_vars_df, index=asset_names, columns=['Poids'])
                    
                    st.write("**Allocation de l'Épargne Mensuelle**")
                    df_alloc_monthly = df_alloc.copy()
                    df_alloc_monthly['Montant Mensuel'] = df_alloc_monthly['Poids'] * monthly_investment
                    st.dataframe(df_alloc_monthly[df_alloc_monthly['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant Mensuel': '{:,.0f} €'}))
                    
                    st.write("**Répartition du Capital de Départ**")
                    df_alloc_capital = df_alloc.copy()
                    df_alloc_capital['Montant'] = df_alloc_capital['Poids'] * initial_capital
                    st.dataframe(df_alloc_capital[df_alloc_capital['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant': '{:,.0f} €'}))
                
                if include_immo:
                    with col2:
                        st.write("**Bilan du Projet Immobilier**")
                        optimal_immo_price = optimal_vars[-1]
                        loan_amount = optimal_immo_price
                        final_mensualite = calculate_monthly_payment(loan_amount, loan_params['rate'], loan_params['duration'])
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

            else:
                st.error("L'optimisation n'a pas pu converger.")
                if include_immo and 'x' in opt_result:
                    st.subheader("🕵️ Diagnostic de l'Échec")
                    last_immo_price = opt_result.x[-1]
                    loan_amount = last_immo_price
                    calculated_payment = calculate_monthly_payment(loan_amount, loan_params['rate'], loan_params['duration'])
                    st.warning(f"La mensualité calculée ({calculated_payment:,.0f} €) pour le dernier bien testé à {last_immo_price:,.0f} € dépasse probablement votre maximum autorisé de {loan_params['mensualite_max']:,.0f} €.")
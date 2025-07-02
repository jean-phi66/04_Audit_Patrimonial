# Fichier: optimization.py (version corrigée)
import streamlit as st
import numpy as np
from scipy.optimize import minimize, NonlinearConstraint
from .simulation import run_unified_simulation, calculate_monthly_payment # MODIFIÉ: Import relatif

def objective_function(optimization_vars, *args):
    final_net_worth, _, _, _, _, _, _ = run_unified_simulation(optimization_vars, *args)
    return -final_net_worth

def cash_flow_constraint(optimization_vars, *args):
    _, _, _, _, _, _, cash_flow_history = run_unified_simulation(optimization_vars, *args)
    return np.array(cash_flow_history)

def setup_and_run_optimization(params):
    """
    Configure et lance l'optimisation en tenant compte du prix fixe ou variable de l'immobilier.
    """
    active_financial_assets = params['df_options_financiers_edited'][params['df_options_financiers_edited']['Actif']].drop(columns=['Actif'])
    asset_names = active_financial_assets.index.tolist()

    if not asset_names and not params['include_immo']:
        return None, None
        
    args = (
        asset_names, params['initial_capital'], params['monthly_investment'], params['investment_horizon'],
        active_financial_assets,
        params['immo_params'] if params['include_immo'] else None,
        params['loan_params'] if params['include_immo'] else None,
        params['marginal_tax_rate'], params['per_deduction_limit']
    )
    
    num_alloc_vars = len(asset_names)
    
    # Cas 1: Immobilier inclus ET prix FIXÉ
    if params['include_immo'] and params['fix_immo_price']:
        fixed_price = params['fixed_immo_price']
        
        mensualite_calculee = calculate_monthly_payment(fixed_price, params['loan_params']['rate'], params['loan_params']['duration'])
        if mensualite_calculee > params['loan_params']['mensualite_max']:
            st.error(f"Le prix fixé de {fixed_price:,.0f} € engendre une mensualité de {mensualite_calculee:,.0f} €, ce qui dépasse votre maximum de {params['loan_params']['mensualite_max']:,.0f} €.")
            return None, None
            
        initial_guess = np.array([1.0/num_alloc_vars if num_alloc_vars > 0 else 0.0]*num_alloc_vars)
        bounds = [(0, 1)] * num_alloc_vars if num_alloc_vars > 0 else []
        
        constraints = []
        if num_alloc_vars > 0:
            constraints.append({'type': 'eq', 'fun': lambda x: 1 - np.sum(x)})
        
        # --- LIGNE CORRIGÉE ---
        # La lambda accepte maintenant les arguments supplémentaires (*args_to_ignore) que scipy lui passe,
        # mais elle continue d'utiliser les 'args' du contexte pour l'appel de la fonction.
        wrapped_objective = lambda x, *args_to_ignore: objective_function(np.append(x, fixed_price), *args)
        
        wrapped_cash_constraint = lambda x: cash_flow_constraint(np.append(x, fixed_price), *args)
        
        nlc = NonlinearConstraint(wrapped_cash_constraint, 0, np.inf)
        constraints.append(nlc)
        objective_to_pass = wrapped_objective

    # Cas 2: Immobilier inclus ET prix VARIABLE
    elif params['include_immo']:
        initial_guess = np.array([1.0/num_alloc_vars if num_alloc_vars > 0 else 0.0]*num_alloc_vars + [np.mean(params['immo_price_range'])])
        bounds = ([(0, 1)] * num_alloc_vars if num_alloc_vars > 0 else []) + [params['immo_price_range']]
        constraints = []
        if num_alloc_vars > 0:
            constraints.append({'type': 'eq', 'fun': lambda x: 1 - np.sum(x[:-1])})
        constraints.append({'type': 'ineq', 'fun': lambda x: params['loan_params']['mensualite_max'] - calculate_monthly_payment(x[-1], params['loan_params']['rate'], params['loan_params']['duration'])})
        nlc = NonlinearConstraint(lambda x: cash_flow_constraint(x, *args), 0, np.inf)
        constraints.append(nlc)
        objective_to_pass = objective_function

    # Cas 3: SANS immobilier
    else:
        initial_guess = np.array([1.0/num_alloc_vars] * num_alloc_vars)
        bounds = [(0, 1)] * num_alloc_vars
        constraints = [{'type': 'eq', 'fun': lambda x: 1 - np.sum(x)}]
        objective_to_pass = objective_function

    opt_result = minimize(
        objective_to_pass,
        initial_guess,
        args=args,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )
    
    return opt_result, args
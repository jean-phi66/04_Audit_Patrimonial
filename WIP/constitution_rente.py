import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

def calculate_future_value(initial_capital, annual_rate_of_return, investment_horizon, monthly_investment):
    """
    Calcule la valeur future d'un investissement avec versements mensuels.

    Args:
        initial_capital (float): Capital initial.
        annual_rate_of_return (float): Taux de rendement annuel (en pourcentage).
        investment_horizon (int): Durée de l'investissement en années.
        monthly_investment (float): Montant investi mensuellement.

    Returns:
        float: Valeur future de l'investissement.
    """
    monthly_rate_of_return = annual_rate_of_return / 100 / 12
    n_periods = investment_horizon * 12
    future_value = initial_capital * (1 + monthly_rate_of_return) ** n_periods + \
                   monthly_investment * ((1 + monthly_rate_of_return) ** n_periods - 1) / monthly_rate_of_return
    return future_value

def calculate_required_rate_of_return(investment_horizon, monthly_income_target, initial_capital, monthly_investment, target_future_value):
    """
    Calcule le taux de rendement annuel nécessaire pour atteindre un capital cible
    permettant de générer un revenu mensuel donné.

    Args:
        investment_horizon (int): Durée de la phase de constitution du capital en années.
        monthly_income_target (float): Revenu mensuel cible souhaité en euros.
        initial_capital (float): Capital initial de départ.
        monthly_investment (float): Montant investi mensuellement.
        target_future_value (float): Valeur future cible du capital.

    Returns:
        float: Taux de rendement annuel nécessaire (en pourcentage).
               Retourne None si le calcul échoue.
    """
    if investment_horizon <= 0:
        return None

    n_periods = investment_horizon * 12

    def future_value_equation(rate):
        monthly_rate = rate / 100 / 12
        future_value = initial_capital * (1 + monthly_rate)**n_periods + \
                       monthly_investment * ((1 + monthly_rate)**n_periods - 1) / monthly_rate
        return future_value

    low_rate = -50
    high_rate = 100
    tolerance = 0.0001
    max_iterations = 1000

    rate = 0
    for _ in range(max_iterations):
        mid_rate = (low_rate + high_rate) / 2
        future_value = future_value_equation(mid_rate)
        if abs(future_value - target_future_value) < tolerance:
            rate = mid_rate
            break
        elif future_value < target_future_value:
            low_rate = mid_rate
        else:
            high_rate = mid_rate
    else:
        return None

    return rate

def calculate_income_stream(capital, annual_rate_of_return_retirement):
    """
    Calcule le revenu mensuel que le capital accumulé peut générer pendant la
    retraite, en supposant un taux de rendement annuel constant.

    Args:
        capital (float): Capital disponible au début de la retraite.
        annual_rate_of_return_retirement (float): Taux de rendement annuel pendant la phase de rente (en pourcentage).

    Returns:
        float: Revenu mensuel généré par le capital.
    """
    monthly_rate_of_return = annual_rate_of_return_retirement / 100 / 12
    monthly_income = capital * monthly_rate_of_return
    return monthly_income

def main():
    """
    Fonction principale qui exécute l'application Streamlit.
    """
    st.title("Rendement phase de constitution")

    # Phase de constitution du capital
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Phase de constitution")
        initial_capital = st.number_input("Capital initial (en €)", min_value=0.0, value=0.0)
        investment_horizon = st.number_input("Durée de la phase de constitution (en années)", min_value=1, value=20)
        monthly_investment = st.number_input("Montant investi mensuellement (en €)", min_value=0.0, value=100.0)
        monthly_income_target = st.number_input("Revenu mensuel cible à la retraite (en €)", min_value=0.0, value=1000.0)

    # Phase de rente
    with col2:
        st.subheader("Phase de rente")
        annual_rate_of_return_retirement_min = st.number_input("Taux de rendement annuel MIN pendant la retraite (en %)", min_value=0.0, value=3.0)
        annual_rate_of_return_retirement_max = st.number_input("Taux de rendement annuel MAX pendant la retraite (en %)", min_value=0.0, value=7.0)
        num_points = st.slider("Nombre de points pour l'analyse de sensibilité", min_value=5, max_value=50, value=20)

    # Calcul du capital cible
    target_future_value = monthly_income_target * 12 * 20

    # Générer une plage de taux de rendement pour la retraite
    retirement_rates = np.linspace(annual_rate_of_return_retirement_min/100, annual_rate_of_return_retirement_max/100, num_points)

    # Calculer le taux de rendement requis pour chaque taux de rendement à la retraite
    required_rates = []
    for retirement_rate in retirement_rates:
        target_future_value = monthly_income_target * 12 / retirement_rate
        required_rate = calculate_required_rate_of_return(investment_horizon, monthly_income_target, initial_capital, monthly_investment, target_future_value)
        required_rates.append(required_rate)

    # Affichage des résultats
    st.header("Résultats")
    if required_rates[0] is not None:
        # Créer un DataFrame pour les résultats
        df = pd.DataFrame({'Rendement à la retraite (%)': np.round(retirement_rates * 100, 2), 'Rendement requis (%)': np.round(required_rates, 2)})

        # Créer un graphique de l'évolution du rendement requis en fonction du rendement à la retraite
        fig = go.Figure(data=go.Scatter(x=df['Rendement à la retraite (%)'], y=df['Rendement requis (%)'], mode='lines+markers'))
        fig.update_layout(
            title="Sensibilité du rendement requis au rendement de la retraite",
            xaxis_title="Rendement annuel à la retraite (%)",
            yaxis_title="Rendement annuel requis (%)  - Phase de constitution",
            #hovermode="x unified"
        )
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig, use_container_width=True)
        
        # Afficher le DataFrame
        st.dataframe(df)

    else:
        st.error("Impossible de calculer un taux de rendement réaliste avec les paramètres fournis. Veuillez ajuster les valeurs d'entrée.")
        st.warning("Assurez-vous que le revenu mensuel cible est atteignable avec l'horizon d'investissement et les versements mensuels.")

if __name__ == "__main__":
    main()

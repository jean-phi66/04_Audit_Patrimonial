# utils/patrimoine_calculs.py
import pandas as pd
import plotly.graph_objects as go

def calculate_patrimoine_summaries(patrimoine_data):
    """
    Calcule les totaux pour les actifs, les passifs et le patrimoine net.

    Args:
        patrimoine_data (dict): Le dictionnaire contenant les données du patrimoine 
                                depuis st.session_state.

    Returns:
        dict: Un dictionnaire avec les totaux calculés.
    """
    # Calcul des totaux pour chaque catégorie d'actifs
    total_immobilier = sum(item['valeur'] for item in patrimoine_data['immobilier'])
    total_financier = sum(item['valeur'] for item in patrimoine_data['investissements_financiers'])
    total_autres_actifs = sum(item['valeur'] for item in patrimoine_data['autres_actifs'])

    # Calcul du total des actifs
    total_actifs = total_immobilier + total_financier + total_autres_actifs

    # Calcul du total des passifs
    total_passifs = sum(item['valeur'] for item in patrimoine_data['passifs'])

    # Calcul du patrimoine net
    patrimoine_net = total_actifs - total_passifs

    return {
        "total_immobilier": total_immobilier,
        "total_financier": total_financier,
        "total_autres_actifs": total_autres_actifs,
        "total_actifs": total_actifs,
        "total_passifs": total_passifs,
        "patrimoine_net": patrimoine_net
    }

def get_patrimoine_df(patrimoine_data):
    """
    Crée un DataFrame récapitulatif du patrimoine.

    Args:
        patrimoine_data (dict): Le dictionnaire du patrimoine.

    Returns:
        pd.DataFrame: Un DataFrame formaté pour l'affichage.
    """
    data = {
        'Catégorie': [
            'ACTIFS', 'Immobilier', 'Investissements Financiers', 'Autres Actifs',
            'PASSIFS', 'TOTAL PASSIFS', 'PATRIMOINE NET'
        ],
        'Montant': [
            sum(item['valeur'] for item in patrimoine_data['immobilier']) +
            sum(item['valeur'] for item in patrimoine_data['investissements_financiers']) +
            sum(item['valeur'] for item in patrimoine_data['autres_actifs']),
            sum(item['valeur'] for item in patrimoine_data['immobilier']),
            sum(item['valeur'] for item in patrimoine_data['investissements_financiers']),
            sum(item['valeur'] for item in patrimoine_data['autres_actifs']),
            None, # Ligne vide pour la séparation visuelle
            sum(item['valeur'] for item in patrimoine_data['passifs']),
            (sum(item['valeur'] for item in patrimoine_data['immobilier']) +
             sum(item['valeur'] for item in patrimoine_data['investissements_financiers']) +
             sum(item['valeur'] for item in patrimoine_data['autres_actifs'])) -
            sum(item['valeur'] for item in patrimoine_data['passifs'])
        ]
    }
    df = pd.DataFrame(data).set_index('Catégorie')
    return df

def create_actifs_pie_chart(summary_data):
    """Crée un graphique circulaire pour la répartition des actifs."""
    labels = ['Immobilier', 'Investissements Financiers', 'Autres Actifs']
    values = [
        summary_data['total_immobilier'],
        summary_data['total_financier'],
        summary_data['total_autres_actifs']
    ]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text='Répartition des Actifs')
    return fig

def create_passifs_pie_chart(patrimoine_data):
    """Crée un graphique circulaire pour la répartition des passifs."""
    if not patrimoine_data['passifs']:
        return None
    labels = [p['nom'] for p in patrimoine_data['passifs']]
    values = [p['valeur'] for p in patrimoine_data['passifs']]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text='Répartition des Passifs')
    return fig

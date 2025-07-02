# pages/1_💰_Patrimoine.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go # Added for Sankey plots
import plotly.express as px
from datetime import datetime
import numpy as np
from utils.calculs import generer_tableau_amortissement, calculer_mensualite_pret

st.title("💰 Patrimoine et Dettes")
st.write("Les valeurs sont mises à jour automatiquement après chaque modification.")

# Initialiser un état pour contrôler l'affichage des calculs et graphiques
if 'calculate_and_plot_patrimoine' not in st.session_state:
    st.session_state.calculate_and_plot_patrimoine = True # Afficher par défaut au premier chargement

# --- Sankey Plot Helper Function ---
def _generate_sankey_plot(
    loyers_bruts,
    charges_annuelles,
    mensualites_pret_annuelles,
    surcroit_ir,
    prelevements_sociaux,
    avantage_fiscal,
    title_suffix=""
):
    # Calculate the cash flow before considering any "effort d'épargne"
    # This is the raw result of income minus expenses and taxes
    cash_flow_before_effort = (
        loyers_bruts
        + avantage_fiscal
        - charges_annuelles
        - mensualites_pret_annuelles
        - surcroit_ir
        - prelevements_sociaux
    )
    
    effort_depargne_value = 0
    final_cash_flow_disponible = 0

    if cash_flow_before_effort < 0:
        effort_depargne_value = abs(cash_flow_before_effort)
        final_cash_flow_disponible = 0 # Deficit is covered by effort
    else:
        effort_depargne_value = 0
        final_cash_flow_disponible = cash_flow_before_effort # Positive cash flow remains

    # Define nodes (updated for new logic)
    labels = [
        "Loyers Bruts",                  # 0
        "Avantage Fiscal",               # 1
        "Effort d'Épargne",              # 2 (New source node for inflow)
        "Total Entrées",                 # 3 (New intermediate node for all inflows)
        "Charges Annuelles",             # 4
        "Mensualités de Prêt",           # 5
        "Impôt sur le Revenu (IR)",      # 6
        "Prélèvements Sociaux (PS)",     # 7
        "Cash-flow Disponible",          # 8 (Final sink, always >= 0)
    ]

    # Define links (source, target, value)
    sources = []
    targets = []
    values = []
    
    # Inflows to "Total Entrées"
    if loyers_bruts > 0: sources.append(0); targets.append(3); values.append(loyers_bruts)
    if avantage_fiscal > 0: sources.append(1); targets.append(3); values.append(avantage_fiscal)
    if effort_depargne_value > 0: sources.append(2); targets.append(3); values.append(effort_depargne_value)

    # Outflows from "Total Entrées"
    if charges_annuelles > 0: sources.append(3); targets.append(4); values.append(charges_annuelles)
    if mensualites_pret_annuelles > 0: sources.append(3); targets.append(5); values.append(mensualites_pret_annuelles)
    if surcroit_ir > 0: sources.append(3); targets.append(6); values.append(surcroit_ir)
    if prelevements_sociaux > 0: sources.append(3); targets.append(7); values.append(prelevements_sociaux)
    if final_cash_flow_disponible > 0: sources.append(3); targets.append(8); values.append(final_cash_flow_disponible)

    fig = go.Figure(data=[go.Sankey(node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=labels), link=dict(source=sources, target=targets, value=values))])
    fig.update_layout(title_text=f"Décomposition des Flux Financiers {title_suffix}", font_size=10)
    return fig
# --- NEW Stacked Bar Chart Helper Function ---
def _generate_stacked_bar_chart(
    loyers_bruts,
    avantage_fiscal,
    charges_annuelles,
    mensualites_pret_annuelles,
    surcroit_ir,
    prelevements_sociaux,
    title_suffix=""
):
    # Calculer le cash-flow pour déterminer l'effort d'épargne ou le cash-flow disponible
    cash_flow_before_effort = (
        loyers_bruts
        + avantage_fiscal
        - charges_annuelles
        - mensualites_pret_annuelles
        - surcroit_ir
        - prelevements_sociaux
    )

    effort_depargne_value = 0
    final_cash_flow_disponible = 0

    if cash_flow_before_effort < 0:
        effort_depargne_value = abs(cash_flow_before_effort)
    else:
        final_cash_flow_disponible = cash_flow_before_effort

    # Data for the bar chart
    revenus_sources = {
        'Loyers Bruts': loyers_bruts, 
        'Avantage Fiscal': avantage_fiscal,
        "Effort d'Épargne": effort_depargne_value
    }
    depenses_sources = {
        'Charges Annuelles': charges_annuelles,
        'Mensualités de Prêt': mensualites_pret_annuelles,
        'Impôt sur le Revenu (IR)': surcroit_ir,
        'Prélèvements Sociaux (PS)': prelevements_sociaux,
        'Cash-flow Disponible': final_cash_flow_disponible
    }

    fig = go.Figure()

    # Define colors for consistency
    colors = {
        'Loyers Bruts': 'mediumseagreen',
        'Avantage Fiscal': 'cornflowerblue',
        "Effort d'Épargne": 'lightskyblue',
        'Charges Annuelles': 'lightcoral',
        'Mensualités de Prêt': 'sandybrown',
        'Impôt sur le Revenu (IR)': 'khaki',
        'Prélèvements Sociaux (PS)': 'plum',
        'Cash-flow Disponible': 'mediumaquamarine'
    }

    # Add traces for revenus
    for name, value in revenus_sources.items():
        if value > 0:
            fig.add_trace(go.Bar(name=name, x=['Revenus'], y=[value], text=f"{value:,.0f}€", textposition='inside', marker_color=colors.get(name)))

    # Add traces for dépenses
    for name, value in depenses_sources.items():
        if value > 0:
            fig.add_trace(go.Bar(name=name, x=['Dépenses'], y=[value], text=f"{value:,.0f}€", textposition='inside', marker_color=colors.get(name)))

    fig.update_layout(
        barmode='stack',
        title_text=f"Synthèse des Revenus vs. Dépenses {title_suffix}",
        xaxis_title="",
        yaxis_title="Montant Annuel (€)",
        legend_title="Postes",
        uniformtext_minsize=8, 
        uniformtext_mode='hide'
    )
    return fig

# Récupérer les noms des adultes pour les options de propriété
adult_names = []
if 'df_adultes' in st.session_state and not st.session_state.df_adultes.empty:
    adult_names = st.session_state.df_adultes['Prénom'].tolist()


# Assurer l'existence et le type correct des colonnes pour la réorientation du capital
# et les nouvelles colonnes immobilières
if 'df_stocks' in st.session_state:
    # Colonnes pour la réorientation
    default_reorientable = True
    default_percentage = 100.0
    if 'Capital Réorientable ?' not in st.session_state.df_stocks.columns:
        st.session_state.df_stocks['Capital Réorientable ?'] = default_reorientable
    st.session_state.df_stocks['Capital Réorientable ?'] = st.session_state.df_stocks['Capital Réorientable ?'].fillna(default_reorientable).astype(bool)

    if 'Pourcentage Réorientable (%)' not in st.session_state.df_stocks.columns:
        st.session_state.df_stocks['Pourcentage Réorientable (%)'] = default_percentage
    st.session_state.df_stocks['Pourcentage Réorientable (%)'] = pd.to_numeric(st.session_state.df_stocks['Pourcentage Réorientable (%)'], errors='coerce').fillna(default_percentage)
    st.session_state.df_stocks['Pourcentage Réorientable (%)'] = st.session_state.df_stocks['Pourcentage Réorientable (%)'].clip(0, 100)

    # Nouvelles colonnes immobilières
    new_immo_cols = {
        'Loyer Mensuel Brut (€)': 0.0,
        'Charges Annuelles (€)': 0.0,
        'Taxe Foncière Annuelle (€)': 0.0
        # NOUVELLES COLONNES POUR DEFISCALISATION (added by user)
        ,'Dispositif Fiscal': None
        ,'Durée Défiscalisation (ans)': 0
    }
    for col, default_val in new_immo_cols.items():
        if col not in st.session_state.df_stocks.columns:
            st.session_state.df_stocks[col] = default_val

        # Ensure correct type for columns, handling 'Dispositif Fiscal' specifically
        if col == 'Dispositif Fiscal':
            # Pour les colonnes de type objet, il faut utiliser .replace() pour gérer les None, car .fillna(None) n'est pas autorisé.
            st.session_state.df_stocks[col] = st.session_state.df_stocks[col].astype(object).replace({np.nan: None})
        elif col == 'Durée Défiscalisation (ans)':
            st.session_state.df_stocks[col] = pd.to_numeric(st.session_state.df_stocks[col], errors='coerce').fillna(default_val).astype(int)
        else:
            st.session_state.df_stocks[col] = pd.to_numeric(st.session_state.df_stocks[col], errors='coerce').fillna(default_val)
    new_ownership_cols = {
        'Type de Propriété': 'Commun',
        'Propriétaire Propre': None,
        'Part Adulte 1 (%)': 50.0,
        'Part Adulte 2 (%)': 50.0
    }
    for col, default_val in new_ownership_cols.items():
        if col not in st.session_state.df_stocks.columns:
            st.session_state.df_stocks[col] = default_val
        if col.startswith('Part Adulte'):
            st.session_state.df_stocks[col] = pd.to_numeric(st.session_state.df_stocks[col], errors='coerce').fillna(default_val)
        elif col == 'Propriétaire Propre':
            st.session_state.df_stocks[col] = st.session_state.df_stocks[col].astype(object).replace({np.nan: None})

col_actifs, col_passifs = st.columns(2)

with col_actifs:
    st.header("Actifs")
    # MODIFICATION: Remplacement du data_editor par des widgets individuels
    types_actifs_options = ["Immobilier de jouissance", "Immobilier productif", "Financier"]

    # --- NOUVELLE LOGIQUE DE WIDGETS ---
    updated_stocks_data = []
    indices_to_delete = []

    # Itérer sur une copie pour éviter les problèmes pendant la modification
    df_stocks_copy = st.session_state.df_stocks.copy()

    for i, row in df_stocks_copy.iterrows():
        # Utiliser le nom de l'actif pour le titre de l'expander, ou un placeholder si nouveau
        expander_title = row.get('Actif') if row.get('Actif') else f"Nouvel Actif #{i+1}"
        with st.expander(expander_title, expanded=not row.get('Actif')):
            # Créer des colonnes pour une mise en page propre
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                actif_name = st.text_input("Nom de l'actif", value=row.get('Actif', ''), key=f"actif_name_{i}")
                # Gérer l'index du selectbox
                try:
                    type_index = types_actifs_options.index(row.get('Type'))
                except (ValueError, TypeError):
                    type_index = 0 # Défaut à "Immobilier de jouissance"
                actif_type = st.selectbox("Type d'actif", options=types_actifs_options, index=type_index, key=f"actif_type_{i}")

            # Initialisation des variables pour le scope
            rendement = float(row.get('Rendement %', 0.0))
            loyer_mensuel = float(row.get('Loyer Mensuel Brut (€)', 0.0))
            charges_annuelles = float(row.get('Charges Annuelles (€)', 0.0))
            taxe_fonciere = float(row.get('Taxe Foncière Annuelle (€)', 0.0))
            # Initialisation des nouvelles variables
            dispositif_fiscal = row.get('Dispositif Fiscal')
            duree_defiscalisation = int(row.get('Durée Défiscalisation (ans)', 0))

            with col2:
                valeur_brute = st.number_input("Valeur Brute (€)", value=float(row.get('Valeur Brute', 0.0)), min_value=0.0, step=1000.0, key=f"valeur_brute_{i}", format="%.0f")
                
                if actif_type == 'Immobilier productif':
                    loyer_mensuel = st.number_input("Loyer Mensuel Brut (€)", value=loyer_mensuel, min_value=0.0, step=50.0, key=f"loyer_mensuel_{i}", format="%.0f")
                    # Calcul du rendement pour le backend (compatibilité)
                    if valeur_brute > 0:
                        rendement = (loyer_mensuel * 12 / valeur_brute) * 100
                    else:
                        rendement = 0.0
                else: # Pour 'Immobilier de jouissance' et 'Financier'
                    rendement = st.number_input("Rendement / Revalo. (%)", value=rendement, step=0.1, key=f"rendement_{i}", format="%.2f", help="Pour l'immobilier, il s'agit du taux de revalorisation annuel. Pour le financier, du rendement.")

            with col3:
                prix_achat = st.number_input("Prix Achat Initial (€)", value=float(row.get('Prix Achat Initial', 0.0)), min_value=0.0, step=1000.0, key=f"prix_achat_{i}", format="%.0f")
                date_achat_val = pd.to_datetime(row.get('Date Achat')).date() if pd.notna(row.get('Date Achat')) else None
                date_achat = st.date_input("Date Achat", value=date_achat_val, key=f"date_achat_{i}")

            with col4:
                st.write("") # Espace pour aligner le bouton
                st.write("")
                if st.button("🗑️ Supprimer", key=f"delete_actif_{i}", use_container_width=True):
                    indices_to_delete.append(i)

            # Section pour les détails immobiliers
            if 'Immobilier' in actif_type:
                st.markdown("---")
                immo_cols = st.columns(2)
                with immo_cols[0]:
                    charges_annuelles = st.number_input("Charges Annuelles (€)", value=charges_annuelles, min_value=0.0, step=50.0, key=f"charges_annuelles_{i}", format="%.0f")
                with immo_cols[1]:
                    taxe_fonciere = st.number_input("Taxe Foncière Annuelle (€)", value=taxe_fonciere, min_value=0.0, step=50.0, key=f"taxe_fonciere_{i}", format="%.0f")

                # NOUVEAUX CHAMPS POUR IMMOBILIER PRODUCTIF
                if actif_type == 'Immobilier productif':
                    st.markdown("---")
                    st.subheader("Dispositif Fiscal (Immobilier Productif)")

                    # Déterminer le type de dispositif actuel pour le radio-bouton
                    current_device_type = "Aucun"
                    if dispositif_fiscal:
                        if "Pinel" in str(dispositif_fiscal):
                            current_device_type = "Pinel"
                        else:
                            current_device_type = "Autre"

                    device_type = st.radio(
                        "Type de dispositif",
                        ["Aucun", "Pinel", "Autre"],
                        index=["Aucun", "Pinel", "Autre"].index(current_device_type),
                        key=f"device_type_{i}",
                        horizontal=True
                    )

                    if device_type == "Pinel":
                        pinel_options = ["Pinel Classique (avant 2023)", "Pinel Classique (2023)", "Pinel Classique (2024)", "Pinel + (2023-2024)"]
                        try:
                            pinel_index = pinel_options.index(dispositif_fiscal)
                        except (ValueError, TypeError):
                            pinel_index = 0
                        
                        dispositif_fiscal = st.selectbox(
                            "Variante Pinel",
                            options=pinel_options,
                            index=pinel_index,
                            key=f"pinel_variant_{i}"
                        )

                        duree_options = [6, 9, 12]
                        try:
                            duree_index = duree_options.index(duree_defiscalisation)
                        except (ValueError, TypeError):
                            duree_index = 1 # Défaut à 9 ans
                        duree_defiscalisation = st.selectbox(
                            "Durée d'engagement",
                            options=duree_options,
                            index=duree_index,
                            key=f"duree_defiscalisation_{i}"
                        )

                    elif device_type == "Autre":
                        other_device_name = dispositif_fiscal if current_device_type == "Autre" else ""
                        dispositif_fiscal = st.text_input("Nom du dispositif", value=other_device_name, key=f"dispositif_fiscal_autre_{i}")
                        duree_defiscalisation = st.number_input("Durée de défiscalisation (années)", value=duree_defiscalisation, min_value=0, step=1, key=f"duree_defiscalisation_autre_{i}")
                    else: # "Aucun"
                        dispositif_fiscal = None
                        duree_defiscalisation = 0
            # Affichage de la valeur nette calculée
            valeur_nette_display = row.get('Valeur Nette')
            if pd.notna(valeur_nette_display):
                st.metric("Valeur Nette (calculée)", f"{valeur_nette_display:,.0f} €", help="Mise à jour après avoir cliqué sur 'Mettre à jour les calculs et graphiques'.")
            else:
                st.metric("Valeur Nette (calculée)", "N/A", help="Sera calculée après avoir cliqué sur 'Mettre à jour les calculs et graphiques'.")

            # Widgets conditionnels pour les actifs financiers
            is_reorientable = bool(row.get('Capital Réorientable ?', True))
            percentage_reorientable = float(row.get('Pourcentage Réorientable (%)', 100.0))
            
            if actif_type == 'Financier':
                st.markdown("---")
                reorient_cols = st.columns(2)
                with reorient_cols[0]:
                    is_reorientable = st.checkbox("Capital Réorientable ?", value=is_reorientable, key=f"reorientable_{i}")
                with reorient_cols[1]:
                    if is_reorientable:
                        percentage_reorientable = st.slider("Si oui, part réorientable (%)", min_value=0, max_value=100, value=int(percentage_reorientable), key=f"percentage_reorientable_{i}")
                    else:
                        percentage_reorientable = 0.0
            
            # --- Nouveaux Détails de Propriété ---
            # Récupérer la valeur existante ou la valeur par défaut
            proprio_propre = row.get('Propriétaire Propre')
            part_adulte1 = float(row.get('Part Adulte 1 (%)', 50.0))
            part_adulte2 = float(row.get('Part Adulte 2 (%)', 50.0))

            st.markdown("---")
            st.subheader("Détails de Propriété")
            
            # Récupérer la valeur existante ou la valeur par défaut
            current_ownership_type = row.get('Type de Propriété', 'Commun')
            try:
                ownership_type_index = ['Commun', 'Propre', 'Indivis'].index(current_ownership_type)
            except ValueError:
                ownership_type_index = 0 # Default to 'Commun' if value is invalid

            ownership_type = st.selectbox(
                "Type de Propriété",
                options=['Commun', 'Propre', 'Indivis'],
                index=ownership_type_index,
                key=f"ownership_type_{i}"
            )

            if ownership_type == 'Indivis':
                proprio_propre = None # Not 'Propre'

                if len(adult_names) >= 2:
                    st.markdown("###### Répartition de la part indivise du foyer entre les adultes :")
                    col_split1, col_split2 = st.columns(2)
                    with col_split1:
                        part_adulte1 = st.number_input(f"Part de {adult_names[0]} (%)", min_value=0.0, max_value=100.0, value=part_adulte1, step=1.0, key=f"part_adulte1_{i}", format="%.0f")
                    with col_split2:
                        part_adulte2 = st.number_input(f"Part de {adult_names[1]} (%)", min_value=0.0, max_value=100.0, value=part_adulte2, step=1.0, key=f"part_adulte2_{i}", format="%.0f")
                    
                    if (part_adulte1 + part_adulte2) != 100:
                        st.warning("La somme des parts des adultes doit être égale à 100%.")
                elif len(adult_names) == 1:
                    st.info(f"Le bien est en indivision, et {adult_names[0]} est le seul adulte enregistré. Sa part est de 100% de la part du foyer.")
                    part_adulte1 = 100.0
                    part_adulte2 = 0.0
                else:
                    st.warning("Veuillez ajouter au moins un adulte dans l'onglet 'Famille & Événements' pour définir la répartition en indivision.")
                    part_adulte1 = 50.0 # Default
                    part_adulte2 = 50.0 # Default

            elif ownership_type == 'Propre':
                if not adult_names:
                    st.warning("Veuillez ajouter des adultes dans l'onglet 'Famille & Événements' pour spécifier le propriétaire du bien propre.")
                    proprio_propre = None
                elif len(adult_names) == 1:
                    st.info(f"Le bien est propre à {adult_names[0]}.")
                    proprio_propre = adult_names[0]
                else:
                    try:
                        proprio_propre_index = adult_names.index(proprio_propre) if proprio_propre in adult_names else 0
                    except ValueError:
                        proprio_propre_index = 0
                    proprio_propre = st.selectbox("Propriétaire du bien propre", options=adult_names, index=proprio_propre_index, key=f"proprio_propre_{i}")
                
                if proprio_propre and len(adult_names) >= 1 and proprio_propre == adult_names[0]:
                    part_adulte1, part_adulte2 = 100.0, 0.0
                elif proprio_propre and len(adult_names) >= 2 and proprio_propre == adult_names[1]:
                    part_adulte1, part_adulte2 = 0.0, 100.0
                else:
                    part_adulte1, part_adulte2 = 0.0, 0.0

            else: # Commun
                proprio_propre = None
                part_adulte1 = 50.0
                part_adulte2 = 50.0

            # Ajouter les données mises à jour à la liste
            updated_stocks_data.append({
                'Actif': actif_name,
                'Type': actif_type,
                'Valeur Brute': valeur_brute,
                'Valeur Nette': row.get('Valeur Nette'), # Conserver l'ancienne valeur nette jusqu'au recalcul
                'Rendement %': rendement,
                'Prix Achat Initial': prix_achat,
                'Date Achat': pd.to_datetime(date_achat) if date_achat else pd.NaT,
                'Capital Réorientable ?': is_reorientable,
                'Pourcentage Réorientable (%)': percentage_reorientable,
                'Loyer Mensuel Brut (€)': loyer_mensuel,
                'Charges Annuelles (€)': charges_annuelles, 
                'Taxe Foncière Annuelle (€)': taxe_fonciere,
                'Dispositif Fiscal': dispositif_fiscal, # NOUVEAU
                'Durée Défiscalisation (ans)': duree_defiscalisation, # NOUVEAU
                'Type de Propriété': ownership_type,
                'Propriétaire Propre': proprio_propre,
                'Part Adulte 1 (%)': part_adulte1,
                'Part Adulte 2 (%)': part_adulte2
            })

    # Gérer les suppressions
    if indices_to_delete:
        st.session_state.df_stocks = st.session_state.df_stocks.drop(indices_to_delete).reset_index(drop=True)
        st.rerun()

    # Mettre à jour le DataFrame dans le session_state avec les nouvelles valeurs des widgets
    # Cela se fait à chaque re-run pour que les changements soient "live"
    st.session_state.df_stocks = pd.DataFrame(updated_stocks_data)

    # Bouton pour ajouter un nouvel actif
    if st.button("➕ Ajouter un Actif", use_container_width=True):
        new_row = pd.DataFrame([{
            'Actif': '', 'Type': 'Financier', 'Valeur Brute': 0.0, 'Valeur Nette': np.nan,
            'Rendement %': 0.0, 'Prix Achat Initial': 0.0, 'Date Achat': pd.NaT,
            'Capital Réorientable ?': True, 'Pourcentage Réorientable (%)': 100.0,
            'Loyer Mensuel Brut (€)': 0.0, 'Charges Annuelles (€)': 0.0, 'Taxe Foncière Annuelle (€)': 0.0,
            'Type de Propriété': 'Commun', 'Propriétaire Propre': None,
            'Dispositif Fiscal': None, # NOUVEAU
            'Durée Défiscalisation (ans)': 0, # NOUVEAU
            'Part Adulte 1 (%)': 50.0, 'Part Adulte 2 (%)': 50.0
        }])
        st.session_state.df_stocks = pd.concat([st.session_state.df_stocks, new_row], ignore_index=True)
        st.rerun()

with col_passifs:
    st.header("Passifs (Prêts Immobiliers)")
    # MODIFICATION: Filtrage pour ne lister que les actifs immobiliers
    df_immobilier_only = st.session_state.df_stocks[st.session_state.df_stocks['Type'].str.contains('Immobilier', na=False)]
    actifs_immobiliers_options = df_immobilier_only['Actif'].tolist()

    # S'assurer que la colonne 'Assurance Emprunteur %' existe dans df_prets
    if 'Assurance Emprunteur %' not in st.session_state.df_prets.columns:
        st.session_state.df_prets['Assurance Emprunteur %'] = np.nan

    if not actifs_immobiliers_options:
        st.info("Aucun actif de type 'Immobilier' n'a été saisi. Vous ne pouvez pas encore ajouter de prêt associé.")
    else:
        updated_prets_data = []
        indices_to_delete_prets = []
        df_prets_copy = st.session_state.df_prets.copy()

        for i, row in df_prets_copy.iterrows():
            # Utiliser le nom de l'actif pour le titre de l'expander, ou un placeholder si nouveau
            expander_title_pret = row.get('Actif Associé') if row.get('Actif Associé') and row.get('Actif Associé') in actifs_immobiliers_options else f"Nouveau Prêt #{i+1}"
            with st.expander(f"Prêt pour : {expander_title_pret}", expanded=not row.get('Actif Associé')):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    try:
                        # Gérer le cas où l'actif associé a été supprimé ou n'est pas dans la liste
                        if row.get('Actif Associé') in actifs_immobiliers_options:
                            actif_associe_index = actifs_immobiliers_options.index(row.get('Actif Associé'))
                        else:
                            actif_associe_index = 0 # Défaut à la première option
                    except (ValueError, TypeError):
                        actif_associe_index = 0
                    actif_associe = st.selectbox("Actif Associé", options=actifs_immobiliers_options, index=actif_associe_index, key=f"pret_actif_{i}")
                    montant_initial = st.number_input("Montant Initial (€)", value=float(row.get('Montant Initial', 0.0)), min_value=0.0, step=1000.0, key=f"pret_montant_{i}", format="%.0f")

                with col2:
                    taux_annuel = st.number_input("Taux Annuel Nominal (%)", value=float(row.get('Taux Annuel %', 0.0)), step=0.1, key=f"pret_taux_{i}", format="%.2f")
                    taux_assurance = st.number_input("Assurance Emprunteur Annuel (%)", value=float(row.get('Assurance Emprunteur %', 0.0)), step=0.01, key=f"pret_assurance_{i}", format="%.2f", help="Taux annuel de l'assurance sur le capital initial (ex: 0.36%).")

                with col3:
                    duree_ans = st.number_input("Durée Initiale (ans)", value=int(row.get('Durée Initiale (ans)', 20)), min_value=1, max_value=30, step=1, key=f"pret_duree_{i}")
                    date_debut_val = pd.to_datetime(row.get('Date Début')).date() if pd.notna(row.get('Date Début')) else None
                    date_debut = st.date_input("Date de Début", value=date_debut_val, key=f"pret_date_{i}")
                
                with col4:
                    st.write("") # Espace pour aligner
                    st.write("")
                    if st.button("🗑️ Supprimer", key=f"delete_pret_{i}", use_container_width=True):
                        indices_to_delete_prets.append(i)

                updated_prets_data.append({
                    'Actif Associé': actif_associe,
                    'Montant Initial': montant_initial,
                    'Taux Annuel %': taux_annuel,
                    'Assurance Emprunteur %': taux_assurance,
                    'Durée Initiale (ans)': duree_ans,
                    'Date Début': pd.to_datetime(date_debut) if date_debut else pd.NaT
                })

        # Gérer les suppressions de prêts
        if indices_to_delete_prets:
            st.session_state.df_prets = st.session_state.df_prets.drop(indices_to_delete_prets).reset_index(drop=True)
            st.rerun()

        # Mettre à jour le DataFrame dans le session_state avec les nouvelles valeurs des widgets
        st.session_state.df_prets = pd.DataFrame(updated_prets_data)

        # Bouton pour ajouter un nouveau prêt
        if st.button("➕ Ajouter un Prêt", use_container_width=True):
            new_pret_row = pd.DataFrame([{
                'Actif Associé': actifs_immobiliers_options[0] if actifs_immobiliers_options else None,
                'Montant Initial': 0.0, 'Taux Annuel %': 3.5, 'Assurance Emprunteur %': 0.36,
                'Durée Initiale (ans)': 20, 'Date Début': pd.to_datetime(datetime.now().date())
            }])
            st.session_state.df_prets = pd.concat([st.session_state.df_prets, new_pret_row], ignore_index=True)
            st.rerun()

st.divider()

# Bouton pour déclencher les calculs et l'affichage des graphiques
if st.button("Mettre à jour les calculs et graphiques", type="primary", use_container_width=True):
    st.session_state.calculate_and_plot_patrimoine = True

# Conditionner l'exécution des calculs et l'affichage des graphiques
if st.session_state.calculate_and_plot_patrimoine:
    # Logique de mise à jour des valeurs nettes des actifs
    crd_par_actif = {}
    for _, pret in st.session_state.df_prets.iterrows():
        actif_associe = pret['Actif Associé']
        if actif_associe:
            # S'assurer que la date est bien au format datetime avant de la passer
            echeancier = generer_tableau_amortissement(pret['Montant Initial'], pret['Taux Annuel %'], pret['Durée Initiale (ans)'], pd.to_datetime(pret['Date Début'], errors='coerce'), pret['Assurance Emprunteur %'])
            crd_actuel = pret['Montant Initial']
            if not echeancier.empty:
                echeances_passees = echeancier[echeancier.index < datetime.now().year]
                if not echeances_passees.empty:
                    crd_actuel = echeances_passees.iloc[-1]['CRD']
                elif echeancier.index[0] > datetime.now().year:
                    crd_actuel = pret['Montant Initial']
                else:
                    lignes_annee_en_cours = echeancier[echeancier.index == datetime.now().year]
                    if not lignes_annee_en_cours.empty:
                        crd_actuel = lignes_annee_en_cours.iloc[0]['CRD']
            crd_par_actif[actif_associe] = crd_par_actif.get(actif_associe, 0) + crd_actuel
    
    # Mise à jour de la Valeur Nette dans le DataFrame édité principal
    # Utiliser edited_stocks_main pour la mise à jour, puis l'assigner à session_state
    temp_df_stocks = st.session_state.df_stocks.copy() # Travailler sur une copie pour éviter SettingWithCopyWarning
    for i, row in temp_df_stocks.iterrows():
        crd = crd_par_actif.get(row['Actif'], 0)
        # S'assurer que la valeur brute est numérique avant la soustraction
        valeur_brute_num = pd.to_numeric(row['Valeur Brute'], errors='coerce')
        if pd.notna(valeur_brute_num):
            temp_df_stocks.loc[i, 'Valeur Nette'] = valeur_brute_num - crd
        else:
            temp_df_stocks.loc[i, 'Valeur Nette'] = -crd
    
    st.session_state.df_stocks = temp_df_stocks.copy() # Sauvegarder les modifications du calcul de la valeur nette

    # Définition des taux Pinel (moved here for scope)
    PINEL_RATES = {
        "Pinel Classique (avant 2023)": {6: 0.12, 9: 0.18, 12: 0.21},
        "Pinel Classique (2023)": {6: 0.105, 9: 0.15, 12: 0.175},
        "Pinel Classique (2024)": {6: 0.09, 9: 0.12, 12: 0.14},
        "Pinel + (2023-2024)": {6: 0.12, 9: 0.18, 12: 0.21},
    }

    # --- Tableau de synthèse des investissements immobiliers ---
    immo_summary_data = []
    df_immobilier = st.session_state.df_stocks[st.session_state.df_stocks['Type'].str.contains('Immobilier', na=False)].copy()

    # Dictionnaire pour stocker les mensualités totales par actif
    mensualites_par_actif = {}
    for _, pret in st.session_state.df_prets.iterrows():
        actif_associe = pret['Actif Associé']
        if actif_associe:
            mensualite = calculer_mensualite_pret(
                pret['Montant Initial'],
                pret['Taux Annuel %'],
                pret['Durée Initiale (ans)'],
                pret.get('Assurance Emprunteur %', 0)
            )
            mensualites_par_actif[actif_associe] = mensualites_par_actif.get(actif_associe, 0) + mensualite

    # Itérer sur les biens immobiliers pour construire le tableau
    for _, bien in df_immobilier.iterrows():
        nom_bien = bien['Actif']
        crd_bien = crd_par_actif.get(nom_bien, 0)
        mensualite_bien = mensualites_par_actif.get(nom_bien, 0)
        
        loyer_mensuel = 0
        if bien['Type'] == 'Immobilier productif':
            loyer_mensuel = bien.get('Loyer Mensuel Brut (€)', 0)
            
        effort_epargne = mensualite_bien - loyer_mensuel
        
        # Calculate tax reduction for this property
        reduction_annuelle = 0.0
        dispositif = bien['Dispositif Fiscal']
        duree = bien['Durée Défiscalisation (ans)']
        prix_achat = bien['Prix Achat Initial']

        if bien['Type'] == 'Immobilier productif' and dispositif and dispositif != 'Aucun' and duree > 0:
            if "Pinel" in dispositif:
                if dispositif in PINEL_RATES and duree in PINEL_RATES[dispositif]:
                    taux_total = PINEL_RATES[dispositif][duree]
                    # La réduction d'impôt est plafonnée à un prix d'achat de 300 000 €
                    base_calcul = min(prix_achat, 300000)
                    reduction_annuelle = (base_calcul * taux_total) / duree
            else: # For "Autre" devices
                reduction_annuelle = prix_achat * 0.02 # Heuristic: 2% of initial purchase price

        immo_summary_data.append({
            'Bien Immobilier': nom_bien,
            'Mensualité Totale (€)': mensualite_bien,
            'CRD Actuel (€)': crd_bien,
            "Loyer Mensuel Brut (€)": loyer_mensuel,
            "Effort d'Épargne Mensuel (€)": effort_epargne,
            "Réduction Impôt Annuelle Estimée (€)": reduction_annuelle # NEW COLUMN
        })

    if immo_summary_data:
        st.divider()
        st.header("Synthèse des Investissements Immobiliers")
        df_immo_summary = pd.DataFrame(immo_summary_data)
        
        # Transpose the dataframe so indicators are rows and properties are columns
        df_transposed = df_immo_summary.set_index('Bien Immobilier').T
        
        # Calculate a 'Global' column with the sum if there are multiple properties
        if len(df_transposed.columns) > 1:
            df_transposed['Global'] = df_transposed.sum(axis=1)
        
        # Format the values for display, applying different formats based on the indicator
        float_format_indicators = [
            'Mensualité Totale (€)',
            'Loyer Mensuel Brut (€)',
            "Effort d'Épargne Mensuel (€)"
        ]
        
        df_display = df_transposed.copy()
        for idx in df_display.index:
            # Check if the indicator is for float values
            if idx in float_format_indicators:
                df_display.loc[idx] = df_display.loc[idx].apply(lambda x: f"{x:,.2f} €")
            else: # Otherwise, use integer format
                df_display.loc[idx] = df_display.loc[idx].apply(lambda x: f"{x:,.0f} €")
        
        # Reset index to make 'Indicateur' a column for display
        df_display.reset_index(inplace=True)
        df_display.rename(columns={'index': 'Indicateur'}, inplace=True)
        
        st.dataframe(
            df_display.style.set_properties(**{'text-align': 'right'}),
            use_container_width=True, 
            hide_index=True
        )

    # --- Analyse de rentabilité des biens productifs ---
    df_immo_productif_renta = st.session_state.df_stocks[st.session_state.df_stocks['Type'] == 'Immobilier productif'].copy()
    if not df_immo_productif_renta.empty:
        st.header("🔍 Analyse de Rentabilité des Biens Productifs")

        # TMI Selectbox
        tmi_options = [0, 11, 30, 41, 45]
        # Initialize tmi_selected_patrimoine in session_state if it doesn't exist
        if 'tmi_selected_patrimoine' not in st.session_state:
            st.session_state.tmi_selected_patrimoine = tmi_options[2] # Default to 30%
        
        # Find the index of the stored value
        try:
            default_index = tmi_options.index(st.session_state.tmi_selected_patrimoine)
        except ValueError:
            default_index = 2 # Fallback to 30% if the stored value is not in options

        tmi_selected = st.selectbox(
                "Tranche Marginale d'Imposition (TMI) pour le calcul fiscal",
                options=tmi_options,
                index=default_index, # Use the calculated index
                format_func=lambda x: f"{x}%",
                help="Sélectionnez votre TMI pour estimer l'impôt sur les revenus fonciers.",
                key="tmi_selectbox_patrimoine" # Add a unique key
            )
        st.session_state.tmi_selected_patrimoine = tmi_selected

        # Define all possible metrics for selection
        all_metrics_options = [
                "Rentabilité Brute", 
                "Rentabilité Nette de Charges", 
                "Rentabilité Nette-Nette", 
                "Rentabilité Nette après Avantage Fiscal",
                "Rentabilité Nette (après Fiscalité Complète)",
                "Cash-flow Annuel (avant impôt)",
                "Revenus Fonciers Nets (Imposables)",
                "Surcroît d'IR associé",
                "Prélèvements Sociaux",
                "Impact Fiscal Global"
            ]

        selected_metrics = st.multiselect(
                "Sélectionnez les indicateurs de rentabilité à afficher pour chaque bien :",
                options=all_metrics_options,
                default=all_metrics_options, # Default to all selected
                key="immo_renta_metrics_selector"
            )
        
        PS_RATE = 0.172 # Prélèvements Sociaux rate
        current_year = datetime.now().year

            # --- ANALYSE GLOBALE (si plusieurs biens) ---
        if len(df_immo_productif_renta) > 1:
            with st.expander("Synthèse Globale de la Rentabilité Immobilière", expanded=True):
                st.subheader("Synthèse Globale de la Rentabilité Immobilière") # This line was the start of the incorrect indentation

            # Initialisation des totaux
                total_prix_achat = 0
                total_loyers_annuels_bruts = 0
                total_charges_totales_annuelles = 0
                total_interets_annuels_globaux = 0
                total_reduction_annuelle_globale = 0
                total_cash_flow_annuel_avant_impot_global = 0

            # Boucle pour agréger les données de tous les biens productifs
                for _, bien in df_immo_productif_renta.iterrows():
                    # Récupération des données
                    prix_achat_bien = bien.get('Prix Achat Initial', 0)
                    loyer_mensuel_bien = bien.get('Loyer Mensuel Brut (€)', 0)
                    charges_annuelles_bien = bien.get('Charges Annuelles (€)', 0)
                    taxe_fonciere_bien = bien.get('Taxe Foncière Annuelle (€)', 0)

                # Calculs des prêts pour ce bien
                    prets_associes_bien = st.session_state.df_prets[st.session_state.df_prets['Actif Associé'] == bien['Actif']]
                    mensualite_totale_bien = mensualites_par_actif.get(bien['Actif'], 0)
                    
                    interets_annuels_bien = 0
                    for _, pret in prets_associes_bien.iterrows():
                        echeancier_bien = generer_tableau_amortissement(
                            pret['Montant Initial'], pret['Taux Annuel %'], pret['Durée Initiale (ans)'],
                            pd.to_datetime(pret['Date Début'], errors='coerce'), pret.get('Assurance Emprunteur %', 0)
                        )
                        if not echeancier_bien.empty and current_year in echeancier_bien.index:
                            interets_annuels_bien += echeancier_bien.loc[current_year, 'Intérêts Annuels']

                # Calcul de la réduction fiscale pour ce bien
                    reduction_annuelle_bien = 0
                    dispositif_bien = bien['Dispositif Fiscal']
                    duree_bien = bien['Durée Défiscalisation (ans)']
                    if bien['Type'] == 'Immobilier productif' and dispositif_bien and dispositif_bien != 'Aucun' and duree_bien > 0:
                        if "Pinel" in dispositif_bien:
                            if dispositif_bien in PINEL_RATES and duree_bien in PINEL_RATES[dispositif_bien]:
                                taux_total_bien = PINEL_RATES[dispositif_bien][duree_bien]
                                base_calcul_bien = min(prix_achat_bien, 300000)
                                reduction_annuelle_bien = (base_calcul_bien * taux_total_bien) / duree_bien
                        else:
                            reduction_annuelle_bien = prix_achat_bien * 0.02

                # Calculs financiers pour ce bien
                    loyers_annuels_bruts_bien = loyer_mensuel_bien * 12
                    charges_totales_annuelles_bien = charges_annuelles_bien + taxe_fonciere_bien
                    cash_flow_annuel_avant_impot_bien = loyers_annuels_bruts_bien - charges_totales_annuelles_bien - (mensualite_totale_bien * 12)

                    # Agrégation
                    total_prix_achat += prix_achat_bien
                    total_loyers_annuels_bruts += loyers_annuels_bruts_bien
                    total_charges_totales_annuelles += charges_totales_annuelles_bien
                    total_interets_annuels_globaux += interets_annuels_bien
                    total_reduction_annuelle_globale += reduction_annuelle_bien
                    total_cash_flow_annuel_avant_impot_global += cash_flow_annuel_avant_impot_bien

            # Calculs de rentabilité globale
                rentabilite_brute_globale = (total_loyers_annuels_bruts / total_prix_achat) * 100 if total_prix_achat > 0 else 0
                rentabilite_nette_charges_globale = ((total_loyers_annuels_bruts - total_charges_totales_annuelles) / total_prix_achat) * 100 if total_prix_achat > 0 else 0
                rentabilite_nette_nette_globale = ((total_loyers_annuels_bruts - total_charges_totales_annuelles - total_interets_annuels_globaux) / total_prix_achat) * 100 if total_prix_achat > 0 else 0
                rentabilite_nette_apres_avantage_fiscal_globale = ((total_loyers_annuels_bruts - total_charges_totales_annuelles - total_interets_annuels_globaux + total_reduction_annuelle_globale) / total_prix_achat) * 100 if total_prix_achat > 0 else 0
                # Calculs fiscaux globaux
                revenu_foncier_net_imposable_global = total_loyers_annuels_bruts - total_charges_totales_annuelles - total_interets_annuels_globaux
                surcroit_ir_global = revenu_foncier_net_imposable_global * (tmi_selected / 100)
                prelevements_sociaux_global = revenu_foncier_net_imposable_global * PS_RATE
                impact_fiscal_global_total = (surcroit_ir_global + prelevements_sociaux_global) - total_reduction_annuelle_globale

                rentabilite_nette_apres_fiscalite_complete_globale = ((total_loyers_annuels_bruts - total_charges_totales_annuelles - total_interets_annuels_globaux - impact_fiscal_global_total) / total_prix_achat) * 100 if total_prix_achat > 0 else 0

            # Affichage des métriques globales
            # Create a dictionary of all calculated global metrics and their display properties
                global_metrics_data = {
                    "Rentabilité Brute": {"value": f"{rentabilite_brute_globale:.2f} %", "help": "Total Loyers Annuels Bruts / Total Prix d'Achat"},
                    "Rentabilité Nette de Charges": {"value": f"{rentabilite_nette_charges_globale:.2f} %", "help": "(Total Loyers - Total Charges) / Total Prix d'Achat"},
                    "Rentabilité Nette-Nette": {"value": f"{rentabilite_nette_nette_globale:.2f} %", "help": "(Total Loyers - Total Charges - Total Intérêts) / Total Prix d'Achat"},
                    "Rentabilité Nette après Avantage Fiscal": {"value": f"{rentabilite_nette_apres_avantage_fiscal_globale:.2f} %", "help": "(Total Loyers - Total Charges - Total Intérêts + Total Av. Fiscal) / Total Prix d'Achat"},
                    "Rentabilité Nette (après Fiscalité Complète)": {"value": f"{rentabilite_nette_apres_fiscalite_complete_globale:.2f} %", "help": "(Loyers - Charges - Intérêts - Impact Fiscal Global) / Prix d'Achat"},
                    "Cash-flow Annuel (avant impôt)": {"value": f"{total_cash_flow_annuel_avant_impot_global:,.0f} €", "help": "Total Loyers - Total Charges - Total Mensualités"},
                    "Revenus Fonciers Nets (Imposables)": {"value": f"{revenu_foncier_net_imposable_global:,.0f} €", "help": "Total Loyers - Total Charges - Total Intérêts"},
                    "Surcroît d'IR associé": {"value": f"{surcroit_ir_global:,.0f} €", "help": f"Revenus Fonciers Nets Globaux * TMI ({tmi_selected}%)"},
                    "Prélèvements Sociaux": {"value": f"{prelevements_sociaux_global:,.0f} €", "help": f"Revenus Fonciers Nets Globaux * {PS_RATE*100:.1f}%"},
                    "Impact Fiscal Global": {"value": f"{impact_fiscal_global_total:,.0f} €", "help": "(IR + PS) - Avantage Fiscal"}
                }

            # Display global metrics in columns based on selection
                g_cols = st.columns(3)
                g_col_idx = 0
                for metric_name in all_metrics_options: # Iterate through all possible metrics to maintain consistent order
                    if metric_name in selected_metrics:
                        # Adjust metric name for global display if needed (e.g., add "Globale")
                        display_metric_name = metric_name
                        if not metric_name.endswith("Globale") and not metric_name.endswith("Global"):
                            display_metric_name = metric_name.replace("Rentabilité", "Rentabilité Globale").replace("Revenus", "Revenus Globaux").replace("Surcroît", "Surcroît Global").replace("Prélèvements", "Prélèvements Globaux").replace("Cash-flow", "Cash-flow Global")

                        with g_cols[g_col_idx]:
                            st.metric(display_metric_name, global_metrics_data[metric_name]["value"], help=global_metrics_data[metric_name]["help"])
                        g_col_idx = (g_col_idx + 1) % 3 # Move to next column, wrap around after 3
                
                st.subheader("Décomposition des Flux Financiers Globaux")
                # Need total_mensualites_pret_annuelles_global
                total_mensualites_pret_annuelles_global = 0
                for _, bien_sankey in df_immo_productif_renta.iterrows():
                    mensualite_bien_sankey = mensualites_par_actif.get(bien_sankey['Actif'], 0)
                    total_mensualites_pret_annuelles_global += mensualite_bien_sankey * 12

                # fig_sankey_global = _generate_sankey_plot(
                #     loyers_bruts=total_loyers_annuels_bruts,
                #     charges_annuelles=total_charges_totales_annuelles,
                #     mensualites_pret_annuelles=total_mensualites_pret_annuelles_global,
                #     surcroit_ir=surcroit_ir_global,
                #     prelevements_sociaux=prelevements_sociaux_global,
                #     avantage_fiscal=total_reduction_annuelle_globale,
                #     title_suffix="(Global)"
                # )
                # st.plotly_chart(fig_sankey_global, use_container_width=True)

                # --- NOUVEAU GRAPHIQUE BARRES EMPILEES ---
                fig_stacked_bar_global = _generate_stacked_bar_chart(
                    loyers_bruts=total_loyers_annuels_bruts,
                    avantage_fiscal=total_reduction_annuelle_globale,
                    charges_annuelles=total_charges_totales_annuelles,
                    mensualites_pret_annuelles=total_mensualites_pret_annuelles_global,
                    surcroit_ir=surcroit_ir_global,
                    prelevements_sociaux=prelevements_sociaux_global,
                    title_suffix="(Global)"
                )
                st.plotly_chart(fig_stacked_bar_global, use_container_width=True)
        
        st.divider()
        st.subheader("Analyses Détaillées par Bien")

        all_properties_metrics = {} # To store metrics for each property for the summary table
        # Boucle pour chaque bien immobilier productif
        for _, bien in df_immo_productif_renta.iterrows():
            with st.expander(f"Analyse pour : {bien['Actif']}", expanded=False):
                    # --- Récupération des données ---
                    prix_achat = bien.get('Prix Achat Initial', 0)
                    loyer_mensuel = bien.get('Loyer Mensuel Brut (€)', 0)
                    charges_annuelles = bien.get('Charges Annuelles (€)', 0)
                    taxe_fonciere = bien.get('Taxe Foncière Annuelle (€)', 0)
                    
                    # --- Calculs liés aux prêts ---
                    prets_associes = st.session_state.df_prets[st.session_state.df_prets['Actif Associé'] == bien['Actif']]
                    montant_emprunte_total = prets_associes['Montant Initial'].sum()
                    mensualite_totale = mensualites_par_actif.get(bien['Actif'], 0)
                    
                    interets_annuels_totaux = 0
                    
                    # Calcul de la réduction fiscale pour ce bien
                    reduction_annuelle = 0.0
                    dispositif = bien['Dispositif Fiscal']
                    duree = bien['Durée Défiscalisation (ans)']
                    # prix_achat est déjà défini comme bien.get('Prix Achat Initial', 0)

                    if bien['Type'] == 'Immobilier productif' and dispositif and dispositif != 'Aucun' and duree > 0:
                        if "Pinel" in dispositif:
                            if dispositif in PINEL_RATES and duree in PINEL_RATES[dispositif]:
                                taux_total = PINEL_RATES[dispositif][duree]
                                # La réduction d'impôt est plafonnée à un prix d'achat de 300 000 €
                                base_calcul = min(prix_achat, 300000)
                                reduction_annuelle = (base_calcul * taux_total) / duree
                        else: # For "Autre" devices
                            reduction_annuelle = prix_achat * 0.02 # Heuristic: 2% of initial purchase price
                    for _, pret in prets_associes.iterrows():
                        echeancier = generer_tableau_amortissement(
                            pret['Montant Initial'], 
                            pret['Taux Annuel %'], 
                            pret['Durée Initiale (ans)'], 
                            pd.to_datetime(pret['Date Début'], errors='coerce'), 
                            pret.get('Assurance Emprunteur %', 0)
                        )
                        if not echeancier.empty and current_year in echeancier.index:
                            interets_annuels_totaux += echeancier.loc[current_year, 'Intérêts Annuels']

                    # --- Calculs financiers ---
                    apport_personnel = prix_achat - montant_emprunte_total if prix_achat > 0 else 0
                    loyers_annuels_bruts = loyer_mensuel * 12
                    charges_totales_annuelles = charges_annuelles + taxe_fonciere
                    cash_flow_annuel_avant_impot = loyers_annuels_bruts - charges_totales_annuelles - (mensualite_totale * 12)

                    # --- Nouveaux calculs fiscaux (déplacés avant les calculs de rentabilité qui les utilisent) ---
                    revenu_foncier_net_imposable = loyers_annuels_bruts - charges_totales_annuelles - interets_annuels_totaux
                    surcroit_ir = revenu_foncier_net_imposable * (tmi_selected / 100)
                    prelevements_sociaux = revenu_foncier_net_imposable * PS_RATE
                    impact_fiscal_global = (surcroit_ir + prelevements_sociaux) - reduction_annuelle

                    # --- Calculs de rentabilité ---
                    rentabilite_brute = (loyers_annuels_bruts / prix_achat) * 100 if prix_achat > 0 else 0
                    rentabilite_nette_charges = ((loyers_annuels_bruts - charges_totales_annuelles) / prix_achat) * 100 if prix_achat > 0 else 0
                    rentabilite_nette_nette = ((loyers_annuels_bruts - charges_totales_annuelles - interets_annuels_totaux) / prix_achat) * 100 if prix_achat > 0 else 0
                    rentabilite_nette_apres_avantage_fiscal = ((loyers_annuels_bruts - charges_totales_annuelles - interets_annuels_totaux + reduction_annuelle) / prix_achat) * 100 if prix_achat > 0 else 0
                    cash_on_cash_return = (cash_flow_annuel_avant_impot / apport_personnel) * 100 if apport_personnel > 0 else np.inf if cash_flow_annuel_avant_impot > 0 else 0
                    rentabilite_nette_apres_fiscalite_complete = ((loyers_annuels_bruts - charges_totales_annuelles - interets_annuels_totaux - impact_fiscal_global) / prix_achat) * 100 if prix_achat > 0 else 0

                    # Create a dictionary of all calculated metrics and their display properties
                    metrics_data = {
                        "Rentabilité Brute": {"value": f"{rentabilite_brute:.2f} %", "help": "Loyer Annuel Brut / Prix d'Achat"},
                        "Rentabilité Nette de Charges": {"value": f"{rentabilite_nette_charges:.2f} %", "help": "(Loyer Annuel Brut - Charges Annuelles) / Prix d'Achat"},
                        "Rentabilité Nette-Nette": {"value": f"{rentabilite_nette_nette:.2f} %", "help": "(Loyer Annuel Brut - Charges - Intérêts d'emprunt) / Prix d'Achat"},
                        "Rentabilité Nette après Avantage Fiscal": {"value": f"{rentabilite_nette_apres_avantage_fiscal:.2f} %", "help": "(Loyers - Charges - Intérêts + Réduction Fiscale) / Prix d'Achat"},
                        "Rentabilité Nette (après Fiscalité Complète)": {"value": f"{rentabilite_nette_apres_fiscalite_complete:.2f} %", "help": "(Loyers - Charges - Intérêts - Impact Fiscal Global) / Prix d'Achat"},
                        "Cash-flow Annuel (avant impôt)": {"value": f"{cash_flow_annuel_avant_impot:,.0f} €", "help": "Loyers - Charges - Mensualités de prêt"},
                        "Revenus Fonciers Nets (Imposables)": {"value": f"{revenu_foncier_net_imposable:,.0f} €", "help": "Loyers - Charges - Intérêts d'emprunt"},
                        "Surcroît d'IR associé": {"value": f"{surcroit_ir:,.0f} €", "help": f"Revenus Fonciers Nets * TMI ({tmi_selected}%)"},
                        "Prélèvements Sociaux": {"value": f"{prelevements_sociaux:,.0f} €", "help": f"Revenus Fonciers Nets * {PS_RATE*100:.1f}%"},
                        "Impact Fiscal Global": {"value": f"{impact_fiscal_global:,.0f} €", "help": "(IR + PS) - Avantage Fiscal"}
                    }

                    # Display metrics in columns based on selection
                    cols = st.columns(3)
                    col_idx = 0
                    for metric_name in all_metrics_options: # Iterate through all possible metrics to maintain consistent order
                        if metric_name in selected_metrics:
                            with cols[col_idx]:
                                st.metric(metric_name, metrics_data[metric_name]["value"], help=metrics_data[metric_name]["help"])
                            col_idx = (col_idx + 1) % 3 # Move to next column, wrap around after 3
                    
                    # st.subheader(f"Décomposition des Flux Financiers pour {bien['Actif']}")
                    # fig_sankey_individual = _generate_sankey_plot(
                    #     loyers_bruts=loyers_annuels_bruts,
                    #     charges_annuelles=charges_totales_annuelles,
                    #     mensualites_pret_annuelles=mensualite_totale * 12, # Already annual
                    #     surcroit_ir=surcroit_ir,
                    #     prelevements_sociaux=prelevements_sociaux,
                    #     avantage_fiscal=reduction_annuelle,
                    #     title_suffix=f"({bien['Actif']})"
                    # )
                    # st.plotly_chart(fig_sankey_individual, use_container_width=True)

                    # --- NOUVEAU GRAPHIQUE BARRES EMPILEES ---
                    fig_stacked_bar_individual = _generate_stacked_bar_chart(
                        loyers_bruts=loyers_annuels_bruts,
                        avantage_fiscal=reduction_annuelle,
                        charges_annuelles=charges_totales_annuelles,
                        mensualites_pret_annuelles=mensualite_totale * 12,
                        surcroit_ir=surcroit_ir,
                        prelevements_sociaux=prelevements_sociaux,
                        title_suffix=f"({bien['Actif']})"
                    )
                    all_properties_metrics[bien['Actif']] = metrics_data # Store metrics for this property
                    st.plotly_chart(fig_stacked_bar_individual, use_container_width=True)

    df_graph = st.session_state.df_stocks.copy()
    df_graph.rename(columns={"Type": "Type de Patrimoine"}, inplace=True)
    couleurs_patrimoine = {"Immobilier de jouissance": "#1f77b4", "Immobilier productif": "#636EFA", "Financier": "#ff7f0e"}
    ordre_categories_patrimoine = ["Financier", "Immobilier productif", "Immobilier de jouissance"]

    # --- Nouveau tableau récapitulatif des indicateurs ---
    if selected_metrics and not df_immo_productif_renta.empty:
        st.divider()
        st.subheader("Tableau Récapitulatif des Indicateurs de Rentabilité")
        summary_table_data = []
        
        # Get all unique property names to ensure column order
        property_columns = [bien['Actif'] for _, bien in df_immo_productif_renta.iterrows()]

        for metric_name in all_metrics_options: # Iterate through all possible metrics to maintain consistent order
            if metric_name in selected_metrics: # Only include selected metrics
                row_dict = {'Indicateur': metric_name}
                
                # Add global value
                if metric_name in global_metrics_data: # Ensure the metric exists in global data
                    row_dict['Global'] = global_metrics_data[metric_name]["value"]
                else:
                    row_dict['Global'] = "N/A" # Or some other placeholder

                # Add individual property values
                for prop_name in property_columns:
                    if prop_name in all_properties_metrics and metric_name in all_properties_metrics[prop_name]:
                        row_dict[prop_name] = all_properties_metrics[prop_name][metric_name]["value"]
                    else:
                        row_dict[prop_name] = "N/A" # Or some other placeholder
                summary_table_data.append(row_dict)

        if summary_table_data:
            df_summary_table = pd.DataFrame(summary_table_data)
            st.dataframe(df_summary_table.style.set_properties(**{'text-align': 'right'}), use_container_width=True, hide_index=True)
        else:
            st.info("Aucun indicateur sélectionné à afficher dans le tableau récapitulatif.")
    # --- Expander pour le Patrimoine BRUT ---
    with st.expander("Analyse Visuelle du Patrimoine BRUT", expanded=True):
        st.subheader("Répartition par Type de Patrimoine (BRUT)")
        total_valeur_brute = df_graph["Valeur Brute"].sum()

        if total_valeur_brute > 0:
            repartition_type_brute = df_graph.groupby("Type de Patrimoine")["Valeur Brute"].sum().reset_index()
            
            fig_treemap_detail_brut = px.treemap(df_graph[df_graph['Valeur Brute'] > 0], 
                                            path=['Type de Patrimoine', 'Actif'], 
                                            values='Valeur Brute', 
                                            color='Type de Patrimoine', 
                                            color_discrete_map=couleurs_patrimoine, 
                                            title='Treemap Détaillé du Patrimoine Brut Actuel')
            fig_treemap_detail_brut.update_traces(texttemplate='%{label}<br>%{value:,.0f} €')
            st.plotly_chart(fig_treemap_detail_brut, use_container_width=True)
        
            fig_treemap_agrege_brut = px.treemap(repartition_type_brute[repartition_type_brute['Valeur Brute'] > 0], 
                                            path=['Type de Patrimoine'], 
                                            values='Valeur Brute', 
                                            color='Type de Patrimoine',
                                            color_discrete_map=couleurs_patrimoine, 
                                            title='Treemap Global du Patrimoine Brut Actuel')
            fig_treemap_agrege_brut.update_traces(texttemplate='%{label}<br>%{percentRoot:.0%}<br>%{value:,.0f} €')
            st.plotly_chart(fig_treemap_agrege_brut, use_container_width=True)

            # Nouveau Pie Chart pour le Patrimoine BRUT
            col_pie_brut1, col_pie_brut2 = st.columns(2) # Utiliser deux colonnes pour les pie charts bruts

            with col_pie_brut1:
                if not repartition_type_brute.empty:
                    fig_pie_brut_actuel = px.pie(repartition_type_brute[repartition_type_brute['Valeur Brute'] > 0], 
                                            values='Valeur Brute', 
                                            names='Type de Patrimoine',
                                            title='Répartition Actuelle du Patrimoine Brut',
                                            color='Type de Patrimoine',
                                            color_discrete_map=couleurs_patrimoine,
                                            hole=.3,
                                            category_orders={"Type de Patrimoine": ordre_categories_patrimoine})
                    fig_pie_brut_actuel.update_traces(textposition='inside', textinfo='percent+label+value', texttemplate='%{label}<br>%{value:,.0f}€<br>(%{percent:.0%})')
                    st.plotly_chart(fig_pie_brut_actuel, use_container_width=True)
                else:
                    st.info("Aucune valeur brute positive à afficher pour le graphique camembert.")
            
            with col_pie_brut2:
                # Création des données pour le graphique "Patrimoine Idéal" (BRUT)
                ideal_labels_brut = ordre_categories_patrimoine # Utiliser l'ordre défini
                ideal_values_brut = [total_valeur_brute / 3, total_valeur_brute / 3, total_valeur_brute / 3] # Répartition en tiers égaux
                df_ideal_brut = pd.DataFrame({'Type de Patrimoine': ideal_labels_brut, 'Valeur': ideal_values_brut})
                
                fig_pie_ideal_brut = px.pie(df_ideal_brut[df_ideal_brut['Valeur'] > 0], 
                                       values='Valeur', 
                                       names='Type de Patrimoine', 
                                       title='Patrimoine Idéal Brut (Répartition en Tiers)',
                                       color='Type de Patrimoine', 
                                       color_discrete_map=couleurs_patrimoine, 
                                       hole=.3,
                                       category_orders={"Type de Patrimoine": ordre_categories_patrimoine})
                fig_pie_ideal_brut.update_traces(textposition='inside', textinfo='percent+label', texttemplate='%{label}<br>(%{percent:.0%})')
                st.plotly_chart(fig_pie_ideal_brut, use_container_width=True)
        else:
            st.info("Aucune valeur brute positive à afficher pour le treemap.")

    # --- Expander pour le Patrimoine NET ---
    with st.expander("Analyse Visuelle du Patrimoine NET", expanded=False):
        st.subheader("Répartition par Type de Patrimoine (NET)")
        df_graph['Valeur Nette'] = pd.to_numeric(df_graph['Valeur Nette'], errors='coerce').fillna(0)
        total_valeur_nette_treemap = df_graph["Valeur Nette"].sum()

        if total_valeur_nette_treemap > 0:
            repartition_type_nette_treemap = df_graph.groupby("Type de Patrimoine")["Valeur Nette"].sum().reset_index()
            
            fig_treemap_detail_net = px.treemap(df_graph[df_graph['Valeur Nette'] > 0],
                                                path=['Type de Patrimoine', 'Actif'], 
                                                values='Valeur Nette', 
                                                color='Type de Patrimoine', 
                                                color_discrete_map=couleurs_patrimoine, 
                                                title='Treemap Détaillé du Patrimoine Net')
            fig_treemap_detail_net.update_traces(texttemplate='%{label}<br>%{value:,.0f} €')
            st.plotly_chart(fig_treemap_detail_net, use_container_width=True)
        
            fig_treemap_agrege_net = px.treemap(repartition_type_nette_treemap[repartition_type_nette_treemap['Valeur Nette'] > 0], 
                                                path=['Type de Patrimoine'], 
                                                values='Valeur Nette', 
                                                color='Type de Patrimoine',
                                                color_discrete_map=couleurs_patrimoine, 
                                                title='Treemap Global du Patrimoine Net')
            fig_treemap_agrege_net.update_traces(texttemplate='%{label}<br>%{percentRoot:.0%}<br>%{value:,.0f} €')
            st.plotly_chart(fig_treemap_agrege_net, use_container_width=True)

            # Pie Charts pour le Patrimoine NET (Actuel et Idéal)
            col_pie1, col_pie2 = st.columns(2)

            # Le calcul pour les camemberts reste basé sur la Valeur Nette
            # total_valeur_nette et repartition_type_nette sont déjà calculés
            # dans le scope de cet expander (total_valeur_nette_treemap et repartition_type_nette_treemap)
            # Renommer pour la clarté dans cette section
            total_valeur_nette = total_valeur_nette_treemap
            repartition_type_nette = repartition_type_nette_treemap

            # Graphique de répartition actuelle du patrimoine net
            with col_pie1:
                if not repartition_type_nette.empty and total_valeur_nette > 0:
                    fig_pie_actuel = px.pie(repartition_type_nette[repartition_type_nette['Valeur Nette'] > 0], 
                                            values='Valeur Nette', 
                                            names='Type de Patrimoine',
                                            title='Répartition Actuelle du Patrimoine Net',
                                            color='Type de Patrimoine',
                                            color_discrete_map=couleurs_patrimoine,
                                            hole=.3,
                                            category_orders={"Type de Patrimoine": ordre_categories_patrimoine})
                    fig_pie_actuel.update_traces(textposition='inside', textinfo='percent+label+value', texttemplate='%{label}<br>%{value:,.0f}€<br>(%{percent:.0%})')
                    st.plotly_chart(fig_pie_actuel, use_container_width=True)
                else:
                    st.info("Aucune valeur nette positive à afficher pour le graphique camembert actuel.")
        
            # Graphique de répartition idéale du patrimoine net
            with col_pie2:
                # Création des données pour le graphique "Patrimoine Idéal"
                ideal_labels = ordre_categories_patrimoine # Utiliser l'ordre défini
                ideal_values = [total_valeur_nette / 3, total_valeur_nette / 3, total_valeur_nette / 3] # Répartition en tiers égaux
                df_ideal = pd.DataFrame({'Type de Patrimoine': ideal_labels, 'Valeur': ideal_values})
                
                fig_pie_ideal = px.pie(df_ideal[df_ideal['Valeur'] > 0], 
                                       values='Valeur', 
                                       names='Type de Patrimoine', 
                                       title='Patrimoine Idéal (Répartition en Tiers)',
                                       color='Type de Patrimoine', 
                                       color_discrete_map=couleurs_patrimoine, 
                                       hole=.3,
                                       category_orders={"Type de Patrimoine": ordre_categories_patrimoine})
                fig_pie_ideal.update_traces(textposition='inside', textinfo='percent+label', texttemplate='%{label}<br>(%{percent:.0%})')
                st.plotly_chart(fig_pie_ideal, use_container_width=True)
        else:
            st.info("Aucune valeur nette positive à afficher pour les graphiques.")

    st.divider()
    st.header("💸 Gestion de la Réorientation du Capital Financier")
    
    # Filtrer pour les actifs financiers à partir de st.session_state.df_stocks (qui a été mis à jour)
    df_financier_assets = st.session_state.df_stocks[st.session_state.df_stocks['Type'] == 'Financier'].copy()
    
    if not df_financier_assets.empty:
        # Calcul du KPI du capital disponible pour réorientation
        capital_disponible_reorientation = 0.0
        # Utiliser df_financier_assets déjà filtré
        for _, row_kpi in df_financier_assets.iterrows():
            valeur_nette_kpi = pd.to_numeric(row_kpi.get('Valeur Nette'), errors='coerce')
            if pd.notna(valeur_nette_kpi) and row_kpi.get('Capital Réorientable ?', False):
                pourcentage_kpi = pd.to_numeric(row_kpi.get('Pourcentage Réorientable (%)'), errors='coerce')
                if pd.notna(pourcentage_kpi):
                    capital_disponible_reorientation += valeur_nette_kpi * (pourcentage_kpi / 100.0)
        
        total_patrimoine_financier_net = df_financier_assets['Valeur Nette'].sum()
        capital_non_reorientable = total_patrimoine_financier_net - capital_disponible_reorientation
        
        col_kpi1, col_kpi2 = st.columns(2)
        col_kpi1.metric("🏦 Capital Financier Disponible pour Réorientation", f"{capital_disponible_reorientation:,.0f} €")
        col_kpi2.metric("🔒 Capital Financier Non Réorientable", f"{capital_non_reorientable:,.0f} €", help="Part du patrimoine financier net non marquée comme réorientable ou dont le pourcentage réorientable est à 0%.")
    else:
        st.info("Aucun actif financier n'a été saisi pour gérer la réorientation.")
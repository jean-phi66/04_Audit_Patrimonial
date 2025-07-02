# utils/patrimoine_ui.py
import streamlit as st
import pandas as pd
from .patrimoine_calculs import create_actifs_pie_chart, create_passifs_pie_chart

def _display_asset_section(title, asset_key, state, columns_config):
    """
    Affiche une section pour un type d'actif (formulaire d'ajout et tableau).

    Args:
        title (str): Le titre de la section (ex: "Immobilier").
        asset_key (str): La clé dans le dictionnaire du patrimoine (ex: "immobilier").
        state (dict): L'état du patrimoine (st.session_state.patrimoine).
        columns_config (dict): Configuration des colonnes pour st.data_editor.
    """
    with st.expander(title, expanded=True):
        st.subheader(f"Ajouter un actif : {title}")
        
        # Formulaire pour ajouter un nouvel actif
        with st.form(key=f"add_{asset_key}_form"):
            cols = st.columns(len(columns_config) - 1)
            new_item_data = {}
            form_columns = list(columns_config.keys())
            form_columns.remove("Actions") # Ne pas afficher le champ "Actions" dans le formulaire

            for i, col_name in enumerate(form_columns):
                with cols[i]:
                    if columns_config[col_name]["type"] == "text":
                        new_item_data[col_name] = st.text_input(f"{col_name}")
                    elif columns_config[col_name]["type"] == "number":
                        new_item_data[col_name] = st.number_input(f"{col_name}", value=0, step=1000)

            submitted = st.form_submit_button("Ajouter")
            if submitted:
                # Vérifie que le nom n'est pas vide
                if new_item_data.get("nom"):
                    state[asset_key].append(new_item_data)
                    st.success(f"Actif '{new_item_data['nom']}' ajouté !")
                    st.rerun()
                else:
                    st.warning("Veuillez entrer un nom pour l'actif.")

        st.subheader("Liste des actifs")
        if state[asset_key]:
            df = pd.DataFrame(state[asset_key])
            
            # Ajout de la colonne pour les actions de suppression
            df['Actions'] = "Supprimer"
            
            edited_df = st.data_editor(
                df,
                column_config=columns_config,
                key=f"editor_{asset_key}",
                hide_index=True,
            )
            
            # Logique de suppression
            # On compare l'ancien et le nouveau dataframe pour trouver les lignes supprimées
            if len(edited_df) < len(state[asset_key]):
                original_indices = pd.DataFrame(state[asset_key]).index
                edited_indices = edited_df.index
                deleted_indices = original_indices.difference(edited_indices)
                
                if not deleted_indices.empty:
                    # Pour simplifier, on reconstruit la liste depuis le DF édité
                    state[asset_key] = edited_df.drop(columns=['Actions']).to_dict('records')
                    st.success("Actif supprimé.")
                    st.rerun()

        else:
            st.info(f"Aucun actif de type '{title}' pour le moment.")


def display_immobilier_ui(patrimoine_state):
    """Affiche la section UI pour l'immobilier."""
    config = {
        "nom": st.column_config.TextColumn("Nom", required=True),
        "valeur": st.column_config.NumberColumn("Valeur Vénale (€)", format="€ %d"),
        "Actions": st.column_config.ActionColumn()
    }
    _display_asset_section("Immobilier", "immobilier", patrimoine_state, config)

def display_investissements_financiers_ui(patrimoine_state):
    """Affiche la section UI pour les investissements financiers."""
    config = {
        "nom": st.column_config.TextColumn("Nom du placement", required=True),
        "valeur": st.column_config.NumberColumn("Valeur Actuelle (€)", format="€ %d"),
        "type": st.column_config.SelectboxColumn("Type", options=["Assurance Vie", "PEA", "Compte-titres", "Cryptomonnaies", "Autre"]),
        "Actions": st.column_config.ActionColumn()
    }
    _display_asset_section("Investissements Financiers", "investissements_financiers", patrimoine_state, config)


def display_autres_actifs_ui(patrimoine_state):
    """Affiche la section UI pour les autres actifs."""
    config = {
        "nom": st.column_config.TextColumn("Nom de l'actif", required=True),
        "valeur": st.column_config.NumberColumn("Valeur (€)", format="€ %d"),
        "Actions": st.column_config.ActionColumn()
    }
    _display_asset_section("Autres Actifs", "autres_actifs", patrimoine_state, config)


def display_passifs_ui(patrimoine_state):
    """Affiche la section UI pour les passifs."""
    config = {
        "nom": st.column_config.TextColumn("Nom du passif", required=True),
        "valeur": st.column_config.NumberColumn("Capital Restant Dû (€)", format="€ %d"),
        "Actions": st.column_config.ActionColumn()
    }
    _display_asset_section("Passifs (Dettes)", "passifs", patrimoine_state, config)


def display_summary(summary_data):
    """Affiche les métriques de synthèse du patrimoine."""
    st.subheader("Synthèse")
    col1, col2, col3 = st.columns(3)
    col1.metric("Actif Total", f"€ {summary_data['total_actifs']:,.2f}")
    col2.metric("Passif Total", f"€ {summary_data['total_passifs']:,.2f}")
    col3.metric("Patrimoine Net", f"€ {summary_data['patrimoine_net']:,.2f}")

def display_charts(summary_data, patrimoine_data):
    """Affiche les graphiques de répartition."""
    st.subheader("Répartition Graphique")
    col1, col2 = st.columns(2)
    with col1:
        fig_actifs = create_actifs_pie_chart(summary_data)
        st.plotly_chart(fig_actifs, use_container_width=True)
    with col2:
        fig_passifs = create_passifs_pie_chart(patrimoine_data)
        if fig_passifs:
            st.plotly_chart(fig_passifs, use_container_width=True)
        else:
            st.info("Aucun passif à afficher.")

# pages/3_👨‍👩‍👧‍👦_Famille_&_Événements.py
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("👨‍👩‍👧‍👦 Famille & Événements")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Adultes")
    st.session_state.df_adultes = st.data_editor(st.session_state.df_adultes, num_rows="dynamic", key="editor_adultes", use_container_width=True)
    if len(st.session_state.df_adultes) == 1:
        st.session_state.parent_isole = st.checkbox("Parent isolé (coche la case T de la déclaration)", value=st.session_state.get('parent_isole', False))
    else:
        st.session_state.parent_isole = False
with col2:
    st.subheader("Enfants")
    st.session_state.df_enfants = st.data_editor(st.session_state.df_enfants, num_rows="dynamic", key="editor_enfants", use_container_width=True, column_config={"Coût Annuel Études (€)": st.column_config.NumberColumn(format="%d €")})

st.divider()
st.subheader("Hypothèses de Retraite (Pensions Annuelles par Adulte)")

adult_names = []
if 'df_adultes' in st.session_state and not st.session_state.df_adultes.empty:
    adult_names = st.session_state.df_adultes['Prénom'].tolist()

    # S'assurer que l'âge des adultes est numérique pour les calculs
    if 'Âge' in st.session_state.df_adultes.columns:
        st.session_state.df_adultes['Âge'] = pd.to_numeric(st.session_state.df_adultes['Âge'], errors='coerce')

if not adult_names:
    st.info("Veuillez d'abord ajouter des adultes pour définir leurs hypothèses de pension.")
else:
    # Colonnes de base pour les hypothèses de pension (sans l'année calculée)
    base_pension_cols = ['Prénom Adulte', 'Âge Départ Retraite', 'Montant Pension Annuelle (€)', 'Active']
    # Colonnes pour l'éditeur spécifique à chaque adulte
    editor_cols_per_adult = ['Âge Départ Retraite', 'Montant Pension Annuelle (€)', 'Active']

    # Vérification de df_pension_hypotheses (normalement initialisé par state_manager)
    if 'df_pension_hypotheses' not in st.session_state or not isinstance(st.session_state.df_pension_hypotheses, pd.DataFrame):
        st.session_state.df_pension_hypotheses = pd.DataFrame(columns=base_pension_cols + ['Année Départ Retraite'])
    
    # S'assurer que les colonnes de base et les types sont corrects (redondant si state_manager est bien exécuté, mais sécurisant)
    for col in base_pension_cols:
        if col not in st.session_state.df_pension_hypotheses.columns:
            st.session_state.df_pension_hypotheses[col] = pd.NA
    if not st.session_state.df_pension_hypotheses.empty:
        # Conversion de type pour les colonnes qui seront éditées, si elles existent déjà
        # Cela garantit que les données passées à data_for_editor sont correctement typées.
        # Le type 'boolean' (nullable) est préférable pour 'Active' s'il peut y avoir des NA avant la première édition.
        # Cependant, CheckboxColumn avec default devrait gérer cela.
        # La conversion principale des types est maintenant dans state_manager.
        for col in editor_cols_per_adult:
            if col in st.session_state.df_pension_hypotheses.columns:
                if col == 'Active':
                    # Fill NA values with False before casting to boolean
                    st.session_state.df_pension_hypotheses[col] = st.session_state.df_pension_hypotheses[col].fillna(False).astype(bool)
                else: # For other columns in editor_cols_per_adult, cast to numeric
                    st.session_state.df_pension_hypotheses[col] = pd.to_numeric(st.session_state.df_pension_hypotheses[col], errors='coerce')

    all_adults_edited_hypotheses_list = []

    for adult_name in adult_names:
        st.markdown(f"##### Hypothèses de pension pour {adult_name}")
        
        # Filtrer les hypothèses existantes pour l'adulte courant
        current_adult_hypotheses_df = st.session_state.df_pension_hypotheses[
            st.session_state.df_pension_hypotheses['Prénom Adulte'] == adult_name
        ].copy()

        # Préparer les données pour l'éditeur
        if not current_adult_hypotheses_df.empty:
            data_for_editor = current_adult_hypotheses_df[editor_cols_per_adult].copy()
        else:
            # Créer un DataFrame vide avec les colonnes et types attendus par l'éditeur
            data_for_editor = pd.DataFrame(columns=editor_cols_per_adult)
            # Assurer les types pour que le data_editor vide se comporte correctement
            data_for_editor['Âge Départ Retraite'] = pd.Series(dtype='Int64')
            data_for_editor['Montant Pension Annuelle (€)'] = pd.Series(dtype='float64')
            data_for_editor['Active'] = pd.Series(dtype='boolean')

        edited_adult_specific_data = st.data_editor(
            data_for_editor,
            num_rows="dynamic",
            key=f"pension_editor_{adult_name.replace(' ', '_').lower()}", # Clé unique et valide
            use_container_width=True,
            column_config={
                "Âge Départ Retraite": st.column_config.NumberColumn(
                    "Âge Départ Retraite", min_value=50, max_value=80, step=1, format="%d", required=True
                ),
                "Montant Pension Annuelle (€)": st.column_config.NumberColumn(
                    "Montant Pension Annuelle (€)", min_value=0, step=1000, format="%d €", required=True
                ),
                "Active": st.column_config.CheckboxColumn("Active pour la simulation ?", default=False, required=True)
            }
        )

        # Si des données ont été éditées/ajoutées pour cet adulte, les préparer pour la consolidation
        # Vérifier si le DataFrame retourné n'est pas vide ET s'il contient des données non-NA
        if not edited_adult_specific_data.dropna(how='all').empty:
            df_to_add = edited_adult_specific_data.copy()
            df_to_add['Prénom Adulte'] = adult_name # Rajouter le prénom de l'adulte
            
            # S'assurer qu'une seule hypothèse est active par adulte
            if 'Active' in edited_adult_specific_data.columns:
                active_rows = edited_adult_specific_data[edited_adult_specific_data['Active'] == True]
                if len(active_rows) > 1:
                    st.warning(f"Plusieurs hypothèses de retraite sont marquées comme 'Actives' pour {adult_name}. Seule la première sera considérée dans la projection. Veuillez n'en activer qu'une seule.")
                    # Optionnel: forcer une seule active (par exemple, la dernière cochée ou la première dans la liste)
                    # Pour l'instant, on laisse l'utilisateur gérer avec un avertissement, la projection prendra la première active.
                elif len(active_rows) == 0 and not edited_adult_specific_data.empty:
                     # Si aucune n'est active et qu'il y a des hypothèses, on pourrait activer la première par défaut
                     # ou laisser l'utilisateur le faire explicitement.
                     # Pour l'instant, si aucune n'est active, aucune pension ne sera prise pour cet adulte.
                     pass

            all_adults_edited_hypotheses_list.append(df_to_add)

    # Consolider les hypothèses de tous les adultes
    if all_adults_edited_hypotheses_list:
        consolidated_df = pd.concat(all_adults_edited_hypotheses_list, ignore_index=True)
        # S'assurer que les colonnes de base sont présentes et dans le bon ordre
        consolidated_df = consolidated_df.reindex(columns=base_pension_cols)
    else:
        consolidated_df = pd.DataFrame(columns=base_pension_cols)

    # Calculer 'Année Départ Retraite' sur le DataFrame consolidé
    final_pensions_df = consolidated_df.copy()
    if 'Année Départ Retraite' not in final_pensions_df.columns:
        final_pensions_df['Année Départ Retraite'] = pd.NA

    if not final_pensions_df.empty and not st.session_state.df_adultes.empty:
        current_year = datetime.now().year
        adult_birth_years = {
            adult['Prénom']: current_year - adult['Âge'] 
            for _, adult in st.session_state.df_adultes.iterrows() if pd.notna(adult['Âge'])
        }

        for index, row in final_pensions_df.iterrows():
            adult_name_hyp = row['Prénom Adulte']
            age_depart_hyp = row['Âge Départ Retraite']
            if pd.notna(adult_name_hyp) and adult_name_hyp in adult_birth_years and pd.notna(age_depart_hyp):
                birth_year = adult_birth_years[adult_name_hyp]
                final_pensions_df.loc[index, 'Année Départ Retraite'] = int(birth_year + age_depart_hyp)
            else:
                final_pensions_df.loc[index, 'Année Départ Retraite'] = pd.NA
    
    st.session_state.df_pension_hypotheses = final_pensions_df
    
    # Affichage d'un avertissement si un adulte a plusieurs hypothèses actives
    if 'Active' in st.session_state.df_pension_hypotheses.columns:
        for adult_name_check in adult_names:
            active_count = st.session_state.df_pension_hypotheses[
                (st.session_state.df_pension_hypotheses['Prénom Adulte'] == adult_name_check) &
                (st.session_state.df_pension_hypotheses['Active'] == True)
            ].shape[0]
            if active_count > 1:
                st.warning(f"Attention : {adult_name_check} a {active_count} hypothèses de retraite marquées comme 'Actives'. La projection utilisera la première rencontrée (celle avec l'âge de départ le plus bas parmi les actives). Il est recommandé de n'activer qu'une seule hypothèse par adulte pour une simulation donnée.")

st.divider()
st.subheader("Événements Immobiliers (optionnel)")
st.write("Planifiez ici la revente d'un bien au cours de la projection.")
df_immobilier = st.session_state.df_stocks[st.session_state.df_stocks['Type'].str.contains('Immobilier', na=False)]
liste_biens_immobiliers = df_immobilier['Actif'].tolist()
if not liste_biens_immobiliers:
    st.info("Aucun bien de type 'Immobilier' n'a été saisi dans l'onglet 'Patrimoine & Dettes'.")
else:
    st.session_state.df_ventes = st.data_editor(st.session_state.df_ventes, num_rows="dynamic", key="editor_ventes", use_container_width=True, column_config={'Année de Vente': st.column_config.NumberColumn(min_value=datetime.now().year, format="%d"),'Bien à Vendre': st.column_config.SelectboxColumn("Bien à Vendre", options=liste_biens_immobiliers, required=True)})
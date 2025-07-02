# pages/3_👨‍👩‍👧‍👦_Famille_&_Événements.py
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("👨‍👩‍👧‍👦 Famille & Événements")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Adultes")
    
    updated_adults_data = []
    indices_to_delete_adults = []
    df_adultes_copy = st.session_state.df_adultes.copy()

    for i, row in df_adultes_copy.iterrows():
        expander_title = row.get('Prénom') if pd.notna(row.get('Prénom')) and row.get('Prénom') != '' else f"Nouvel Adulte #{i+1}"
        with st.expander(expander_title, expanded=not (pd.notna(row.get('Prénom')) and row.get('Prénom') != '')):
            col_a1, col_a2, col_a3 = st.columns([3, 2, 1])
            with col_a1:
                prenom_adulte = st.text_input("Prénom", value=row.get('Prénom', ''), key=f"adult_prenom_{i}")
                age_input_method = st.radio(
                    "Saisie de l'âge",
                    options=["Âge", "Date de Naissance"],
                    index=0 if pd.notna(row.get('Âge')) else 1,
                    key=f"adult_age_method_{i}",
                    horizontal=True
                )
            with col_a2:
                # Récupérer la date de naissance existante pour la préserver
                date_naissance = row.get('Date Naissance') if pd.notna(row.get('Date Naissance')) else None

                if age_input_method == "Âge":
                    age_adulte = st.number_input("Âge", value=int(row.get('Âge', 0)) if pd.notna(row.get('Âge')) else 0, min_value=0, step=1, key=f"adult_age_{i}")
                else:
                    date_naissance = st.date_input("Date de Naissance", value=date_naissance, key=f"adult_naissance_{i}")
                    age_adulte = datetime.now().year - date_naissance.year if date_naissance else 0

            with col_a3:
                st.write("") # Spacer for alignment
                st.write("")

                if st.button("🗑️ Supprimer", key=f"delete_adult_{i}", use_container_width=True):
                    indices_to_delete_adults.append(i)
            
            updated_adults_data.append({'Prénom': prenom_adulte, 'Âge': age_adulte, 'Date Naissance': date_naissance})

    if indices_to_delete_adults:
        st.session_state.df_adultes = st.session_state.df_adultes.drop(indices_to_delete_adults).reset_index(drop=True)
        st.rerun()

    st.session_state.df_adultes = pd.DataFrame(updated_adults_data) if updated_adults_data else pd.DataFrame(columns=['Prénom', 'Âge', 'Date Naissance'])

    if len(st.session_state.df_adultes) < 2:
        if st.button("➕ Ajouter un Adulte", key="add_adult", use_container_width=True):
            new_row = pd.DataFrame([{'Prénom': '', 'Âge': 0, 'Date Naissance': None}])
            st.session_state.df_adultes = pd.concat([st.session_state.df_adultes, new_row], ignore_index=True)
    else:
        st.info("Le nombre maximum d'adultes (2) a été atteint.")

    if len(st.session_state.df_adultes) == 1:
        st.session_state.parent_isole = st.checkbox("Parent isolé (coche la case T de la déclaration)", value=st.session_state.get('parent_isole', False))
    else:
        st.session_state.parent_isole = False
with col2:
    st.subheader("Enfants")

    updated_enfants_data = []
    indices_to_delete_enfants = []
    df_enfants_copy = st.session_state.df_enfants.copy()

    for i, row in df_enfants_copy.iterrows():
        expander_title = row.get('Prénom') if pd.notna(row.get('Prénom')) and row.get('Prénom') != '' else f"Nouvel Enfant #{i+1}"
        with st.expander(expander_title, expanded=not (pd.notna(row.get('Prénom')) and row.get('Prénom') != '')):
            col_e1, col_e2, col_e3, col_e4 = st.columns([3, 2, 2, 1])
            with col_e1:
                prenom_enfant = st.text_input("Prénom", value=row.get('Prénom', ''), key=f"enfant_prenom_{i}")
                age_input_method_enfant = st.radio(
                    "Saisie de l'âge",
                    options=["Âge", "Date de Naissance"],
                    index=0 if pd.notna(row.get('Âge')) else 1,
                    key=f"enfant_age_method_{i}",
                    horizontal=True
                )
            with col_e2:
                # Récupérer la date de naissance existante pour la préserver
                date_naissance_enfant = row.get('Date Naissance') if pd.notna(row.get('Date Naissance')) else None

                if age_input_method_enfant == "Âge":
                    age_enfant = st.number_input("Âge", value=int(row.get('Âge', 0)) if pd.notna(row.get('Âge')) else 0, min_value=0, step=1, key=f"enfant_age_{i}")
                else:
                    date_naissance_enfant = st.date_input("Date de Naissance", value=date_naissance_enfant, key=f"enfant_naissance_{i}")
                    age_enfant = datetime.now().year - date_naissance_enfant.year if date_naissance_enfant else 0
            with col_e3:
                age_debut_etudes = st.number_input("Âge Début Études", value=int(row.get('Âge Début Études', 0)) if pd.notna(row.get('Âge Début Études')) else 0, min_value=0, step=1, key=f"enfant_age_debut_etudes_{i}")
                duree_etudes = st.number_input("Durée Études (ans)", value=int(row.get('Durée Études (ans)', 0)) if pd.notna(row.get('Durée Études (ans)')) else 0, min_value=0, step=1, key=f"enfant_duree_etudes_{i}")
            with col_e4:
                cout_annuel_etudes = st.number_input("Coût Annuel Études (€)", value=float(row.get('Coût Annuel Études (€)', 0.0)) if pd.notna(row.get('Coût Annuel Études (€)')) else 0.0, min_value=0.0, step=100.0, format="%.0f", key=f"enfant_cout_etudes_{i}")
                st.write("") # Spacer for alignment
                if st.button("🗑️ Supprimer", key=f"delete_enfant_{i}", use_container_width=True):
                    indices_to_delete_enfants.append(i)
            
            updated_enfants_data.append({
                'Prénom': prenom_enfant,
                'Âge': age_enfant,
                'Date Naissance': date_naissance_enfant,
                'Âge Début Études': age_debut_etudes,
                'Durée Études (ans)': duree_etudes,
                'Coût Annuel Études (€)': cout_annuel_etudes
            })

    if indices_to_delete_enfants:
        st.session_state.df_enfants = st.session_state.df_enfants.drop(indices_to_delete_enfants).reset_index(drop=True)
        st.rerun()

    st.session_state.df_enfants = pd.DataFrame(updated_enfants_data) if updated_enfants_data else pd.DataFrame(columns=['Prénom', 'Âge', 'Date Naissance', 'Âge Début Études', 'Durée Études (ans)', 'Coût Annuel Études (€)'])

    if st.button("➕ Ajouter un Enfant", key="add_enfant", use_container_width=True):
        new_row = pd.DataFrame([{
            'Prénom': '',
            'Âge': 0,
            'Date Naissance': None,
            'Âge Début Études': 0,
            'Durée Études (ans)': 0,
            'Coût Annuel Études (€)': 0.0
        }])
        st.session_state.df_enfants = pd.concat([st.session_state.df_enfants, new_row], ignore_index=True)
        st.rerun()


# The following sections for "Hypothèses de Retraite" and "Événements Immobiliers"
# are not present in the current version of pages/1_👨‍👩‍👧‍👦_Famille_&_Événements.py
# as provided in the context. They are found in pages/5_📶_Projection.py.
# Therefore, they are not modified as part of this request.

# st.divider()
# st.subheader("Hypothèses de Retraite (Pensions Annuelles par Adulte)")
# ... (original code for pension hypotheses if it were in this file) ...

# st.divider()
# st.subheader("Événements Immobiliers (optionnel)")
# ... (original code for real estate events if it were in this file) ...
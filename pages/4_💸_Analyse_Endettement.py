# pages/6_📊_Analyse_Endettement.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from utils.state_manager import initialize_session

# Initialiser la session au début du script
initialize_session()

# Tentative d'importation de la fonction de calcul des mensualités
try:
    from utils.calculs import calculer_mensualite_pret
except ImportError:
    st.error("La fonction `calculer_mensualite_pret` n'a pas pu être importée. Vérifiez le chemin `utils.calculs`.")
    # Définition d'une fonction factice pour éviter que l'application ne plante (les calculs seront incorrects)
    def calculer_mensualite_pret(montant_initial, taux_annuel_nominal_pourcent, duree_annees, taux_assurance_annuel_pourcent_capital_initial=0):
        st.warning("ATTENTION : Utilisation d'une fonction `calculer_mensualite_pret` factice car l'originale est introuvable.")
        if duree_annees == 0 or montant_initial is None or taux_annuel_nominal_pourcent is None or pd.isna(montant_initial) or pd.isna(taux_annuel_nominal_pourcent) or pd.isna(duree_annees):
            return np.nan
        
        # Calcul simplifié et incorrect pour démonstration
        mensualite_base = (montant_initial / (duree_annees * 12)) 
        interet_simule = mensualite_base * (taux_annuel_nominal_pourcent / 100.0) / 12.0
        assurance_simulee = 0
        if taux_assurance_annuel_pourcent_capital_initial > 0 and montant_initial > 0 and pd.notna(taux_assurance_annuel_pourcent_capital_initial):
             assurance_simulee = (montant_initial * (taux_assurance_annuel_pourcent_capital_initial / 100.0)) / 12.0
        return mensualite_base + interet_simule + assurance_simulee

st.title("📊 Analyse du Taux d'Endettement")
st.write("""
Cette page analyse le taux d'endettement actuel du foyer. 
Le calcul prend en compte l'ensemble des revenus (avec une pondération de 70% pour les revenus locatifs bruts issus de l'immobilier productif) 
et les mensualités de tous les prêts en cours.
""")

# Entrée utilisateur pour le taux d'endettement cible
taux_endettement_max_cible = st.slider(
    "Taux d'endettement maximum cible (%)", 
    min_value=30.0, 
    max_value=40.0, 
    value=35.0, 
    step=0.5,
    help="Définissez le taux d'endettement que vous considérez comme acceptable ou comme objectif. Généralement entre 35% et 40%."
)
st.markdown("---")

# --- Chargement et Préparation des Données ---
if st.session_state.df_revenus.empty:
    st.info("ℹ️ Aucun revenu n'a été saisi dans l'onglet '💸 Flux'. Le calcul du taux d'endettement ne peut être effectué sans revenus.")

# Conditions d'arrêt ou d'avertissement si les données sont insuffisantes
if st.session_state.df_revenus.empty and st.session_state.df_prets.empty: 
    st.warning("Veuillez saisir des revenus et/ou des prêts pour effectuer une analyse.")
    st.stop()
elif st.session_state.df_revenus.empty and not st.session_state.df_prets.empty: 
     st.warning("⚠️ Aucun revenu n'a été saisi, mais des prêts existent. Le taux d'endettement sera infini ou non calculable.")
     # On continue pour afficher au moins les charges de prêts

df_revenus = st.session_state.df_revenus.copy()
df_prets = st.session_state.df_prets.copy()
df_stocks = st.session_state.df_stocks.copy()

# Assurer les types de données corrects et gérer les NaN
df_revenus['Montant Annuel'] = pd.to_numeric(df_revenus['Montant Annuel'], errors='coerce').fillna(0)

colonnes_prets_requises = {'Montant Initial':0.0, 'Taux Annuel %':0.0, 'Durée Initiale (ans)':0.0, 'Date Début':pd.NaT, 'Assurance Emprunteur %':0.0, 'Actif Associé': 'N/A'}
for col, valeur_defaut in colonnes_prets_requises.items():
    if col not in df_prets.columns:
        df_prets[col] = valeur_defaut
df_prets['Montant Initial'] = pd.to_numeric(df_prets['Montant Initial'], errors='coerce').fillna(0)
df_prets['Taux Annuel %'] = pd.to_numeric(df_prets['Taux Annuel %'], errors='coerce').fillna(0)
df_prets['Durée Initiale (ans)'] = pd.to_numeric(df_prets['Durée Initiale (ans)'], errors='coerce').fillna(0)
df_prets['Assurance Emprunteur %'] = pd.to_numeric(df_prets['Assurance Emprunteur %'], errors='coerce').fillna(0)
df_prets['Date Début'] = pd.to_datetime(df_prets['Date Début'], errors='coerce')

colonnes_stocks_requises = {'Type': None, 'Valeur Brute': 0.0, 'Rendement %': 0.0, 'Actif': 'Actif Inconnu'}
for col, valeur_defaut in colonnes_stocks_requises.items():
    if col not in df_stocks.columns:
        df_stocks[col] = valeur_defaut
df_stocks['Valeur Brute'] = pd.to_numeric(df_stocks['Valeur Brute'], errors='coerce').fillna(0)
df_stocks['Rendement %'] = pd.to_numeric(df_stocks['Rendement %'], errors='coerce').fillna(0)


# --- 1. Calcul des Charges de Prêts Mensuelles ---
charges_details_list = []

for _, pret in df_prets.iterrows():
    is_active = False
    status_reason = ""
    
    # Vérifier les conditions pour qu'un prêt soit actif
    if not (pd.notna(pret['Date Début']) and pret['Date Début'] < datetime.now()):
        status_reason = f"Prêt futur (début le {pret['Date Début'].strftime('%d/%m/%Y')})" if pd.notna(pret['Date Début']) else "Date de début manquante"
    elif not (pret['Montant Initial'] > 0):
        status_reason = "Montant initial nul ou manquant"
    elif not (pret['Durée Initiale (ans)'] > 0):
        status_reason = "Durée nulle ou manquante"
    elif not (pd.notna(pret['Taux Annuel %'])):
        status_reason = "Taux manquant"
    else:
        is_active = True
        status_reason = "Actif et inclus dans le calcul"

    # Calculer la mensualité si possible, quel que soit le statut
    mensualite = np.nan
    if pret['Montant Initial'] > 0 and pret['Durée Initiale (ans)'] > 0 and pd.notna(pret['Taux Annuel %']):
        mensualite = calculer_mensualite_pret(
            pret['Montant Initial'],
            pret['Taux Annuel %'],
            pret['Durée Initiale (ans)'],
            pret.get('Assurance Emprunteur %', 0)
        )

    charges_details_list.append({
        "Description": f"Prêt ({pret.get('Actif Associé', 'N/A')})",
        "Mensualité (€)": mensualite if pd.notna(mensualite) else 0,
        "Statut": "Actif" if is_active else "Inactif",
        "Raison / Statut": status_reason
    })

df_charges_details = pd.DataFrame(charges_details_list)

# Calculer le total basé uniquement sur les prêts actifs
total_charges_prets_mensuelles = df_charges_details[df_charges_details['Statut'] == 'Actif']['Mensualité (€)'].sum()

# --- 2. Calcul des Revenus Mensuels Pondérés ---
revenus_details_list = []

# Revenus autres que locatifs
revenus_autres_annuels = df_revenus['Montant Annuel'].sum()
revenus_autres_mensuels = revenus_autres_annuels / 12.0
if revenus_autres_mensuels > 0:
    revenus_details_list.append({
        "Source": "Autres revenus (salaires, pensions, etc.)", 
        "Montant Mensuel Brut (€)": revenus_autres_mensuels, 
        "Pondération (%)": 100, 
        "Montant Mensuel Pondéré (€)": revenus_autres_mensuels
    })

# Revenus locatifs (Immobilier productif)
revenus_locatifs_bruts_annuels_total = 0.0
revenus_locatifs_pondérés_mensuels_total = 0.0

df_immobilier_productif = df_stocks[df_stocks['Type'] == "Immobilier productif"]

for _, actif in df_immobilier_productif.iterrows():
    if actif['Valeur Brute'] > 0 and pd.notna(actif['Rendement %']) and actif['Rendement %'] != 0:
        revenu_locatif_actif_annuel_brut = actif['Valeur Brute'] * (actif['Rendement %'] / 100.0)
        revenu_locatif_actif_mensuel_brut = revenu_locatif_actif_annuel_brut / 12.0
        revenu_locatif_actif_mensuel_pondere = revenu_locatif_actif_mensuel_brut * 0.70
        
        revenus_locatifs_bruts_annuels_total += revenu_locatif_actif_annuel_brut
        revenus_locatifs_pondérés_mensuels_total += revenu_locatif_actif_mensuel_pondere
        
        revenus_details_list.append({
            "Source": f"Locatif Brut - {actif['Actif']}",
            "Montant Mensuel Brut (€)": revenu_locatif_actif_mensuel_brut,
            "Pondération (%)": 70,
            "Montant Mensuel Pondéré (€)": revenu_locatif_actif_mensuel_pondere
        })

total_revenus_mensuels_pondérés = revenus_autres_mensuels + revenus_locatifs_pondérés_mensuels_total
df_revenus_details = pd.DataFrame(revenus_details_list)

# --- 3. Calcul du Taux d'Endettement ---
taux_endettement_actuel = 0.0
if total_revenus_mensuels_pondérés > 0:
    taux_endettement_actuel = (total_charges_prets_mensuelles / total_revenus_mensuels_pondérés) * 100.0
elif total_charges_prets_mensuelles > 0: # Dettes mais pas de revenus pris en compte
    taux_endettement_actuel = float('inf') 

# --- 4. Affichage des Résultats ---
st.subheader("📈 Synthèse du Taux d'Endettement")

# Calcul de la mensualité résiduelle avant d'atteindre le taux cible
mensualite_residuelle = 0.0
if total_revenus_mensuels_pondérés > 0:
    charges_max_autorisees_cible = total_revenus_mensuels_pondérés * (taux_endettement_max_cible / 100.0)
    mensualite_residuelle = charges_max_autorisees_cible - total_charges_prets_mensuelles
else:
    # Si les revenus sont nuls ou négatifs, la capacité maximale d'emprunt est nulle (ou négative).
    # La mensualité résiduelle est donc 0 (capacité max pour la cible) - charges_actuelles.
    mensualite_residuelle = -total_charges_prets_mensuelles

# Affichage des métriques en 2x2
kpi_col1, kpi_col2 = st.columns(2)
kpi_col3, kpi_col4 = st.columns(2)

kpi_col1.metric("Revenus Mensuels Pondérés", f"{total_revenus_mensuels_pondérés:,.2f} €")
kpi_col2.metric("Charges Prêts Mensuelles", f"{total_charges_prets_mensuelles:,.2f} €")

if taux_endettement_actuel == float('inf'):
    kpi_col3.metric("Taux d'Endettement Actuel", "Infini", delta_color="off")
    st.error("🚨 Les revenus totaux pondérés sont nuls ou négatifs alors que des charges existent. Le taux d'endettement est infini.")
elif total_revenus_mensuels_pondérés <= 0 and total_charges_prets_mensuelles == 0:
    kpi_col3.metric("Taux d'Endettement Actuel", "0.00 %", delta_color="off")
    st.success("✅ Aucun revenu ni charge de prêt n'est actuellement pris en compte. Taux d'endettement nul.")
else:
    kpi_col3.metric("Taux d'Endettement Actuel", f"{taux_endettement_actuel:.2f} %")
    # Appréciation du taux
    seuil_vigilance = taux_endettement_max_cible + 5.0 # ex: 35% cible -> 40% vigilance
    if taux_endettement_actuel <= taux_endettement_max_cible:
        st.success(f"✅ Votre taux d'endettement ({taux_endettement_actuel:.2f}%) est inférieur ou égal à votre cible de {taux_endettement_max_cible:.1f}%.")
    elif taux_endettement_actuel <= seuil_vigilance:
         st.warning(f"⚠️ Votre taux d'endettement ({taux_endettement_actuel:.2f}%) est supérieur à votre cible de {taux_endettement_max_cible:.1f}%, mais reste dans une zone de vigilance (jusqu'à {seuil_vigilance:.1f}%).")
    else: 
        st.error(f"🚨 Votre taux d'endettement ({taux_endettement_actuel:.2f}%) dépasse significativement votre cible de {taux_endettement_max_cible:.1f}% (et la zone de vigilance de {seuil_vigilance:.1f}%).")

kpi_col4.metric(
    label=f"Capacité Mens. Résiduelle (cible {taux_endettement_max_cible:.1f}%)",
    value=f"{mensualite_residuelle:,.2f} €",
    help="Montant de mensualité supplémentaire que le foyer peut supporter avant d'atteindre le taux d'endettement cible. Une valeur négative indique un dépassement de la cible."
)

st.markdown("---")
st.info("ℹ️ Le calcul du taux d'endettement utilise 100% des revenus 'Autres' et 70% des revenus locatifs bruts estimés à partir des actifs de type 'Immobilier productif' et de leur rendement indiqué.")

with st.expander("🔍 Détail des Revenus Pris en Compte pour le Calcul"):
    if not df_revenus_details.empty:
        st.dataframe(
            df_revenus_details.style.format({
                "Montant Mensuel Brut (€)": "{:,.2f} €",
                "Pondération (%)": "{:.0f}%",
                "Montant Mensuel Pondéré (€)": "{:,.2f} €"
            }), 
            use_container_width=True, 
            hide_index=True
        )
        st.markdown(f"**Total Revenus Mensuels Pondérés Pris en Compte : {total_revenus_mensuels_pondérés:,.2f} €**")
    else:
        st.write("Aucun revenu pris en compte pour le calcul.")

with st.expander("🔍 Détail des Charges de Prêts Mensuelles"):
    if not df_charges_details.empty:
        # Appliquer un style pour mettre en évidence les prêts inactifs
        def highlight_inactive(s):
            return ['background-color: #f0f2f6' if s.Statut == 'Inactif' else '' for _ in s]

        st.dataframe(
            df_charges_details.style.apply(highlight_inactive, axis=1).format({
                "Mensualité (€)": "{:,.2f} €"
            }), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Description": st.column_config.TextColumn("Description", width="large"),
                "Mensualité (€)": st.column_config.NumberColumn("Mensualité (€)"),
                "Statut": st.column_config.TextColumn("Statut"),
                "Raison / Statut": st.column_config.TextColumn("Raison / Statut", width="large"),
            }
        )
        st.markdown(f"**Total des Charges de Prêts Actives (incluses dans le calcul) : {total_charges_prets_mensuelles:,.2f} €**")
    else:
        st.write("Aucun prêt n'a été saisi.")

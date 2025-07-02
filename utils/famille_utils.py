# utils/famille_utils.py
from datetime import datetime
import pandas as pd

def calculate_age(birth_date):
    """
    Calcule l'âge à partir d'une date de naissance.
    Retourne 0 si la date de naissance n'est pas valide.
    """
    if not birth_date or pd.isna(birth_date):
        return 0
    today = datetime.now()
    # Calcule l'âge en se basant sur la différence d'années, puis ajuste si l'anniversaire n'est pas encore passé.
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def add_new_adult():
    """
    Retourne un DataFrame contenant une nouvelle ligne pour un adulte par défaut.
    """
    return pd.DataFrame([{'Prénom': '', 'Âge': 0, 'Date Naissance': None}])

def add_new_child():
    """
    Retourne un DataFrame contenant une nouvelle ligne pour un enfant par défaut.
    """
    return pd.DataFrame([{
        'Prénom': '',
        'Âge': 0,
        'Date Naissance': None,
        'Âge Début Études': 18,
        'Durée Études (ans)': 5,
        'Coût Annuel Études (€)': 0.0
    }])

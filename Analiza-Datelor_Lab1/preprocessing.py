# preprocessing.py
# ============================================
# Modul pentru preprocesarea datelor:
# - identificarea coloanelor energetice
# - conversia coloanei 'date'
# - extragerea componentelor temporale
# - conversia coloanelor numerice
# - standardizarea variabilelor categorice
# ============================================

import pandas as pd


def get_energy_columns():
    """
    Returnează lista coloanelor care reprezintă tipurile de energie
    și agregatele principale din setul de date.

    Această listă o folosim peste tot în proiect pentru:
    - statistici descriptive
    - corelații
    - vizualizări
    """
    return [
        "carbune", "hidro", "hidrocarburi", "nuclear",
        "eolian", "fotovolt", "biomasa", "productie", "consum"
    ]


def convert_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertește coloana 'date' la tip datetime.

    - errors='coerce' => dacă există valori invalide, sunt transformate în NaT.
    """
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def add_time_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adaugă componente temporale derivate din coloana 'date':
    - year, month, day, hour, minute, weekday

    Acestea sunt utile pentru:
    - grupări pe an/lună/oră
    - vizualizări avansate (heatmap ore, luni)
    - analize sezoniere.
    """
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    df["weekday"] = df["date"].dt.weekday  # 0 = Luni, 6 = Duminică
    return df


def convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertește toate coloanele (în afară de 'date') la tip numeric,
    acolo unde este posibil.

    - Dacă o valoare nu poate fi convertită => devine NaN.
    - Ne asigurăm că valorile pentru energie, producție, consum etc.
      pot fi folosite în calcule și grafice.
    """
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def standardize_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creează și standardizează variabile categorice:

    - year_str: anul ca string (pentru filtrări sau legendă)
    - month_name: numele lunii în limba română
    - weekday_name: numele zilei săptămânii în limba română
    """
    # Transformăm anul în string (categorial)
    df["year_str"] = df["year"].astype(str)

    # Dicționar cu denumirile lunilor
    month_map = {
        1: "Ianuarie", 2: "Februarie", 3: "Martie", 4: "Aprilie",
        5: "Mai", 6: "Iunie", 7: "Iulie", 8: "August",
        9: "Septembrie", 10: "Octombrie", 11: "Noiembrie", 12: "Decembrie"
    }
    df["month_name"] = df["month"].map(month_map)

    # Dicționar cu denumirile zilelor săptămânii
    weekday_map = {
        0: "Luni", 1: "Marți", 2: "Miercuri", 3: "Joi",
        4: "Vineri", 5: "Sâmbătă", 6: "Duminică"
    }
    df["weekday_name"] = df["weekday"].map(weekday_map)

    return df


def preprocess(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline complet de preprocesare, folosit de aplicația principală:

    1. Luăm o copie a DataFrame-ului brut
    2. Convertim 'date' la datetime
    3. Adăugăm componente temporale
    4. Convertim coloanele numerice
    5. Standardizăm variabilele categorice

    Returnează DataFrame-ul preprocesat.
    """
    df = df_raw.copy()
    df = convert_datetime(df)
    df = add_time_components(df)
    df = convert_numeric(df)
    df = standardize_categorical(df)
    return df

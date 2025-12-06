# visualizations.py
# ============================================
# Modul pentru vizualizări avansate:
# - histograme
# - heatmap-uri (energie–ore, energie–luni)
# - producție medie lunară pe tipuri
# - sold zilnic
# - seria temporală a soldului
# - producție medie pe ore
# - consum mediu pe zile
# - comparații între ani
# ============================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from preprocessing import get_energy_columns


def plot_histograms(df: pd.DataFrame):
    """
    Afișează un selector pentru coloanele de energie
    și generează histogramă pentru coloana selectată.
    """
    st.subheader("Histograme – tipuri de energie")

    energy_cols = [c for c in get_energy_columns() if c in df.columns]
    col = st.selectbox("Alege coloana", energy_cols)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df[col].dropna(), bins=30)
    ax.set_title(f"Histogramă - {col}")
    ax.set_xlabel("Valori (MW)")
    ax.set_ylabel("Frecvență")
    st.pyplot(fig)


def plot_heatmap_hour_energy(df: pd.DataFrame):
    """
    Generează un heatmap al producției medii pe ore (0–23),
    pentru toate tipurile de energie.
    """
    st.subheader("Heatmap: Producția medie de energie pe ore")

    df_local = df.copy()
    df_local["hour"] = df_local["date"].dt.hour

    energy_cols = [c for c in get_energy_columns() if c in df.columns]
    for col in energy_cols:
        df_local[col] = pd.to_numeric(df_local[col], errors="coerce")

    # Matrice: rânduri = ore, coloane = tipuri de energie
    hourly_matrix = df_local.groupby("hour")[energy_cols].mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(hourly_matrix, aspect="auto")
    ax.set_title("Producția medie de energie pe ore")
    ax.set_xlabel("Tip energie")
    ax.set_ylabel("Ora")
    ax.set_xticks(range(len(energy_cols)))
    ax.set_xticklabels(energy_cols, rotation=45)
    ax.set_yticks(range(24))
    ax.set_yticklabels(range(24))
    fig.colorbar(cax)
    st.pyplot(fig)


def plot_heatmap_month_energy(df: pd.DataFrame):
    """
    Generează un heatmap al producției medii pe luni (1–12),
    pentru toate tipurile de energie.
    """
    st.subheader("Heatmap: Producția medie de energie pe luni")

    df_local = df.copy()
    df_local["month"] = df_local["date"].dt.month

    energy_cols = [c for c in get_energy_columns() if c in df.columns]
    for col in energy_cols:
        df_local[col] = pd.to_numeric(df_local[col], errors="coerce")

    # Matrice: rânduri = luni, coloane = tipuri de energie
    monthly_matrix = df_local.groupby("month")[energy_cols].mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(monthly_matrix, aspect="auto")
    ax.set_title("Producția medie de energie pe luni")
    ax.set_xlabel("Tip energie")
    ax.set_ylabel("Lună")
    ax.set_xticks(range(len(energy_cols)))
    ax.set_xticklabels(energy_cols, rotation=45)
    ax.set_yticks(range(1, 13))
    ax.set_yticklabels(range(1, 13))
    fig.colorbar(cax)
    st.pyplot(fig)


def plot_monthly_production_by_type(df: pd.DataFrame):
    """
    Generează un grafic cu bare stivuite (stacked bar) care arată
    contribuția fiecărui tip de energie la producția medie lunară.
    """
    st.subheader("Producția medie lunară pe tipuri de energie (stacked bar)")

    df_local = df.copy()
    df_local["month"] = df_local["date"].dt.month

    energy_cols = ["carbune", "hidro", "hidrocarburi",
                   "nuclear", "eolian", "fotovolt", "biomasa"]
    energy_cols = [c for c in energy_cols if c in df_local.columns]

    for col in energy_cols:
        df_local[col] = pd.to_numeric(df_local[col], errors="coerce")

    # Grupare pe lună și medie pentru fiecare tip de energie
    monthly_prod = df_local.groupby("month")[energy_cols].mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom_vals = None
    for col in energy_cols:
        if bottom_vals is None:
            ax.bar(monthly_prod.index, monthly_prod[col], label=col)
            bottom_vals = monthly_prod[col].copy()
        else:
            ax.bar(monthly_prod.index, monthly_prod[col], bottom=bottom_vals, label=col)
            bottom_vals += monthly_prod[col]

    ax.set_title("Producția medie lunară pe tipuri de energie")
    ax.set_xlabel("Lună")
    ax.set_ylabel("Producție medie (MW)")
    ax.set_xticks(range(1, 13))
    ax.legend()
    st.pyplot(fig)


def plot_daily_sold_2024_2025(df: pd.DataFrame):
    """
    Calculează și afișează soldul zilnic (producție - consum) pentru anii 2024 și 2025.
    """
    st.subheader("Soldul zilnic (Producție - Consum) – 2024 vs 2025")

    df_local = df.copy()
    df_local["year"] = df_local["date"].dt.year
    df_local["day"] = df_local["date"].dt.date

    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")
    df_local["consum"] = pd.to_numeric(df_local["consum"], errors="coerce")
    df_local["sold"] = df_local["productie"] - df_local["consum"]

    # Calculăm soldul mediu pe fiecare zi
    daily_sold = df_local.groupby(["year", "day"])["sold"].mean().reset_index()
    sold_2024 = daily_sold[daily_sold["year"] == 2024]
    sold_2025 = daily_sold[daily_sold["year"] == 2025]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(sold_2024["day"], sold_2024["sold"], label="2024")
    ax.plot(sold_2025["day"], sold_2025["sold"], label="2025")
    ax.axhline(0, color="black")
    ax.set_title("Sold zilnic (Producție - Consum) 2024 vs 2025")
    ax.set_xlabel("Ziua")
    ax.set_ylabel("Sold (MW)")
    ax.legend()
    st.pyplot(fig)


def plot_sold_timeseries(df: pd.DataFrame):
    """
    Afișează seria temporală completă a soldului energetic (producție - consum).
    """
    st.subheader("Seria temporală a soldului energetic")

    df_local = df.copy().sort_values("date")
    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")
    df_local["consum"] = pd.to_numeric(df_local["consum"], errors="coerce")
    df_local["sold"] = df_local["productie"] - df_local["consum"]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_local["date"], df_local["sold"])
    ax.axhline(0, color="black")
    ax.set_title("Seria temporală a soldului (Producție - Consum)")
    ax.set_xlabel("Data")
    ax.set_ylabel("Sold (MW)")
    st.pyplot(fig)


def plot_hourly_mean_production(df: pd.DataFrame):
    """
    Afișează producția medie pe ore (0–23) pentru întreaga perioadă,
    pentru a identifica peak-ul orar al producției.
    """
    st.subheader("Producția medie pe ore (peak orar)")

    df_local = df.copy()
    df_local["hour"] = df_local["date"].dt.hour
    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")

    hourly_mean_prod = df_local.groupby("hour")["productie"].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(hourly_mean_prod.index, hourly_mean_prod.values)
    ax.set_title("Producția medie pe ore")
    ax.set_xlabel("Ora")
    ax.set_ylabel("Producție medie (MW)")
    ax.set_xticks(range(24))
    ax.grid(True)
    st.pyplot(fig)


def plot_weekday_mean_consumption(df: pd.DataFrame):
    """
    Afișează consumul mediu de energie pentru fiecare zi a săptămânii.
    """
    st.subheader("Consumul mediu pe zilele săptămânii")

    df_local = df.copy()
    df_local["weekday"] = df_local["date"].dt.weekday
    df_local["consum"] = pd.to_numeric(df_local["consum"], errors="coerce")

    weekday_mean = df_local.groupby("weekday")["consum"].mean()
    weekday_names = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(weekday_mean.index, weekday_mean.values)
    ax.set_xticks(range(7))
    ax.set_xticklabels(weekday_names, rotation=45)
    ax.set_title("Consumul mediu pe zilele săptămânii")
    ax.set_xlabel("Ziua săptămânii")
    ax.set_ylabel("Consum mediu (MW)")
    ax.grid(True)
    st.pyplot(fig)


def plot_monthly_mean_production_2024_2025(df: pd.DataFrame):
    """
    Afișează producția medie lunară pentru anii 2024 și 2025,
    pentru a compara sezonalitatea între ani.
    """
    st.subheader("Producția medie lunară – 2024 vs 2025")

    df_local = df.copy()
    df_local["year"] = df_local["date"].dt.year
    df_local["month"] = df_local["date"].dt.month
    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")

    monthly_prod = df_local.groupby(["year", "month"])["productie"].mean().reset_index()
    prod_2024 = monthly_prod[monthly_prod["year"] == 2024]
    prod_2025 = monthly_prod[monthly_prod["year"] == 2025]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(prod_2024["month"], prod_2024["productie"], marker="o", label="2024")
    ax.plot(prod_2025["month"], prod_2025["productie"], marker="o", label="2025")
    ax.set_title("Producția medie lunară – 2024 vs 2025")
    ax.set_xlabel("Lună")
    ax.set_ylabel("Producție medie (MW)")
    ax.set_xticks(range(1, 13))
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)


def plot_production_vs_consumption(df: pd.DataFrame):
    """
    Afișează într-o singură figură evoluția în timp a producției și consumului.
    """
    st.subheader("Comparație producție vs consum (toată perioada)")

    df_local = df.copy().sort_values("date")
    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")
    df_local["consum"] = pd.to_numeric(df_local["consum"], errors="coerce")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_local["date"], df_local["productie"], label="Producție")
    ax.plot(df_local["date"], df_local["consum"], label="Consum")
    ax.set_title("Comparație producție vs consum")
    ax.set_xlabel("Data")
    ax.set_ylabel("MW")
    ax.legend()
    st.pyplot(fig)


def plot_production_vs_consumption_by_year(df: pd.DataFrame):
    """
    Afișează comparația între producție și consum pentru anii 2024 și 2025,
    pe același grafic, cu stiluri diferite.
    """
    st.subheader("Comparație producție/consum – 2024 vs 2025")

    df_local = df.copy()
    df_local["year"] = df_local["date"].dt.year
    df_local["productie"] = pd.to_numeric(df_local["productie"], errors="coerce")
    df_local["consum"] = pd.to_numeric(df_local["consum"], errors="coerce")

    df_2024 = df_local[df_local["year"] == 2024].sort_values("date")
    df_2025 = df_local[df_local["year"] == 2025].sort_values("date")

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df_2024["date"], df_2024["productie"], label="Producție 2024")
    ax.plot(df_2024["date"], df_2024["consum"], label="Consum 2024")
    ax.plot(df_2025["date"], df_2025["productie"], label="Producție 2025", linestyle="--")
    ax.plot(df_2025["date"], df_2025["consum"], label="Consum 2025", linestyle="--")
    ax.set_title("Comparație producție/consum – 2024 vs 2025")
    ax.set_xlabel("Data")
    ax.set_ylabel("MW")
    ax.legend()
    st.pyplot(fig)

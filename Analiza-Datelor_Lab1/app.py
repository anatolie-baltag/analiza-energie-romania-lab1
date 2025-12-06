# app.py
# ============================================
# Aplicația Streamlit:
# - încarcă fișierul CSV
# - rulează preprocesarea
# - permite navigarea între:
#     * Preprocesare & overview
#     * Statistici & corelații
#     * Vizualizări avansate
#     * Filtrare + raport PDF
# ============================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Importăm funcțiile proprii din modulele proiectului
from preprocessing import preprocess, get_energy_columns
from analysis import (
    show_missing_and_duplicates,
    show_descriptive_stats,
    show_correlation_matrix,
    show_hour_fotovolt_correlations,
    create_pdf_report,
)
from visualizations import (
    plot_histograms,
    plot_heatmap_hour_energy,
    plot_heatmap_month_energy,
    plot_monthly_production_by_type,
    plot_daily_sold_2024_2025,
    plot_sold_timeseries,
    plot_hourly_mean_production,
    plot_weekday_mean_consumption,
    plot_monthly_mean_production_2024_2025,
    plot_production_vs_consumption,
    plot_production_vs_consumption_by_year,
)

# Configurăm pagina Streamlit (titlu, layout etc.)
st.set_page_config(
    page_title="Analiza energiei electrice România",
    layout="wide"
)


@st.cache_data
def load_data(uploaded_file=None, default_path=None):
    """
    Încărcarea datelor într-un DataFrame Pandas.

    - uploaded_file: fișier urcat prin interfața Streamlit
    - default_path: alternativ, o cale fixă pe disc (dacă vrem să o folosim)

    Funcția este memorată (cache_data) pentru a evita reîncărcări inutile.
    """
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif default_path is not None:
        df = pd.read_csv(default_path)
    else:
        raise ValueError("Nu există fișier de intrare.")
    return df


def main():
    """
    Funcția principală a aplicației Streamlit.
    Ordonează fluxul:
    - încărcare date
    - preprocesare
    - selectare secțiune
    - afișarea conținutului pentru secțiunea aleasă
    """
    st.title("Analiza energiei electrice în România – 2024–2025")
    st.markdown(
        """
        Aplicație completă pentru:
        - preprocesarea datelor
        - analiza statistică și a corelațiilor
        - vizualizări avansate
        - filtrare pe interval de timp + tipuri de energie
        - generare de rapoarte PDF
        """
    )

    # ----------------------------------------
    # 1. ÎNCĂRCARE DATE
    # ----------------------------------------
    st.sidebar.header("1. Încărcare date")

    # Uploader pentru fișierul CSV
    uploaded_file = st.sidebar.file_uploader("Încarcă fișierul data.csv", type=["csv"])

    default_path = None

    # Dacă nu avem nici fișier încărcat, nici path fix, oprim aplicația aici
    if uploaded_file is None and default_path is None:
        st.info("Încarcă un fișier CSV din sidebar pentru a începe.")
        return

    # Încărcăm DataFrame-ul brut din fișier
    df_raw = load_data(uploaded_file, default_path)

    # Verificăm că există coloana 'date' (necesară pentru preprocesare și grafice)
    if "date" not in df_raw.columns:
        st.error("Setul de date trebuie să conțină o coloană 'date'.")
        return

    # Rulăm pipeline-ul de preprocesare (din preprocessing.py)
    df = preprocess(df_raw)

    # Identificăm coloanele energetice care chiar există în DataFrame
    energy_cols = [c for c in get_energy_columns() if c in df.columns]

    # ----------------------------------------
    # 2. SECȚIUNI ALE APLICAȚIEI
    # ----------------------------------------
    st.sidebar.header("2. Secțiuni")
    section = st.sidebar.radio(
        "Alege secțiunea:",
        [
            "Preprocesare & overview",
            "Statistici & corelații",
            "Vizualizări avansate",
            "Filtrare + raport PDF",
        ]
    )

    # ========================================
    # SECȚIUNEA: Preprocesare & overview
    # ========================================
    if section == "Preprocesare & overview":
        st.subheader("Primele rânduri din setul de date (preprocesat)")
        st.dataframe(df.head(), use_container_width=True)

        # Afișăm informații despre valori lipsă și duplicate
        show_missing_and_duplicates(df)

    # ========================================
    # SECȚIUNEA: Statistici & corelații
    # ========================================
    elif section == "Statistici & corelații":
        # Statistici descriptive pentru tipurile de energie
        show_descriptive_stats(df)
        st.markdown("---")

        # Matrice de corelație + heatmap
        show_correlation_matrix(df)
        st.markdown("---")

        # Corelații hour–fotovolt
        show_hour_fotovolt_correlations(df)

    # ========================================
    # SECȚIUNEA: Vizualizări avansate
    # ========================================
    elif section == "Vizualizări avansate":
        # Selector pentru tipul de vizualizare pe care dorim să o afișăm
        viz_choice = st.selectbox(
            "Alege vizualizarea",
            [
                "Histograme pe tipuri de energie",
                "Heatmap energie–ore",
                "Heatmap energie–luni",
                "Producția medie lunară pe tipuri",
                "Sold zilnic 2024 vs 2025",
                "Seria temporală a soldului",
                "Producția medie pe ore",
                "Consumul mediu pe zilele săptămânii",
                "Producția medie lunară 2024 vs 2025",
                "Producție vs consum (tot intervalul)",
                "Producție vs consum 2024 vs 2025",
            ]
        )

        # În funcție de opțiune, apelăm funcția de vizualizare corespunzătoare
        if viz_choice == "Histograme pe tipuri de energie":
            plot_histograms(df)
        elif viz_choice == "Heatmap energie–ore":
            plot_heatmap_hour_energy(df)
        elif viz_choice == "Heatmap energie–luni":
            plot_heatmap_month_energy(df)
        elif viz_choice == "Producția medie lunară pe tipuri":
            plot_monthly_production_by_type(df)
        elif viz_choice == "Sold zilnic 2024 vs 2025":
            plot_daily_sold_2024_2025(df)
        elif viz_choice == "Seria temporală a soldului":
            plot_sold_timeseries(df)
        elif viz_choice == "Producția medie pe ore":
            plot_hourly_mean_production(df)
        elif viz_choice == "Consumul mediu pe zilele săptămânii":
            plot_weekday_mean_consumption(df)
        elif viz_choice == "Producția medie lunară 2024 vs 2025":
            plot_monthly_mean_production_2024_2025(df)
        elif viz_choice == "Producție vs consum (tot intervalul)":
            plot_production_vs_consumption(df)
        elif viz_choice == "Producție vs consum 2024 vs 2025":
            plot_production_vs_consumption_by_year(df)

    # ========================================
    # SECȚIUNEA: Filtrare + raport PDF
    # ========================================
    elif section == "Filtrare + raport PDF":
        st.subheader("Filtrare de date și vizualizare")

        # Calculăm data minimă și maximă din setul de date
        min_date = df["date"].min()
        max_date = df["date"].max()

        # Filtre în sidebar: interval de date și tipuri de energie
        st.sidebar.header("3. Filtre")
        st.sidebar.markdown("Interval de date")
        date_range = st.sidebar.date_input(
            "Alege intervalul de analiză",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )

        # Extragem capetele intervalului (start, end)
        if isinstance(date_range, tuple):
            start_date, end_date = date_range
        else:
            start_date = date_range
            end_date = date_range

        # Creăm un mask pentru a păstra doar înregistrările din intervalul selectat
        mask_date = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
        df_filtered = df.loc[mask_date].copy()

        st.sidebar.markdown("Tipuri de energie")
        selected_energy = st.sidebar.multiselect(
            "Selectează tipurile de energie",
            options=energy_cols,
            default=energy_cols  # implicit le selectăm pe toate
        )

        st.markdown(
            f"Interval selectat: **{start_date}** → **{end_date}**, "
            f"tipuri de energie: {', '.join(selected_energy) if selected_energy else '-'}"
        )

        # Gestionăm cazurile în care nu există date sau nu e selectată nicio coloană
        if df_filtered.empty:
            st.warning("Nu există date în intervalul selectat.")
            return

        if not selected_energy:
            st.warning("Selectează cel puțin un tip de energie din sidebar.")
            return

        # Afișăm primele 50 de rânduri din datele filtrate
        st.subheader("Date filtrate (primele 50 de rânduri)")
        st.dataframe(
            df_filtered[["date"] + selected_energy].head(50),
            use_container_width=True
        )

        # Serie temporală pentru coloanele selectate
        st.subheader("Serie temporală – tipuri de energie selectate")
        fig, ax = plt.subplots(figsize=(12, 5))
        for col in selected_energy:
            ax.plot(df_filtered["date"], df_filtered[col], label=col)
        ax.set_title("Evoluția în timp pentru tipurile de energie selectate")
        ax.set_xlabel("Data")
        ax.set_ylabel("MW")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # Statistici descriptive pentru subsetul filtrat
        st.subheader("Statistici descriptive pentru datele filtrate")
        stats = df_filtered[selected_energy].describe().T
        st.dataframe(stats)

        # Histogramă pentru o coloană de energie aleasă
        st.subheader("Histogramă pentru un tip de energie selectat")
        col_hist = st.selectbox("Alege coloana pentru histogramă", selected_energy)
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.hist(df_filtered[col_hist].dropna(), bins=30)
        ax2.set_title(f"Histogramă - {col_hist} (filtrat pe intervalul selectat)")
        ax2.set_xlabel("Valori (MW)")
        ax2.set_ylabel("Frecvență")
        st.pyplot(fig2)

        # Generare raport PDF pentru filtrarea curentă
        st.subheader("Raport PDF pentru filtrarea curentă")
        pdf_bytes = create_pdf_report(
            df_filtered,
            selected_energy,
            start_date,
            end_date,
            col_hist,
        )
        st.download_button(
            label="Descarcă raport PDF",
            data=pdf_bytes,
            file_name="raport_energie_filtrat.pdf",
            mime="application/pdf"
        )


# Punct de intrare în aplicație
if __name__ == "__main__":
    main()

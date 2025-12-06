# analysis.py
# ============================================
# Modul pentru analiză și raportare:
# - afișarea valorilor lipsă și a duplicatelor
# - statistici descriptive
# - corelații (inclusiv hour–fotovolt)
# - generarea unui raport PDF pentru filtrarea curentă:
#      1. date filtrate (primele 50 rânduri)
#      2. statistici descriptive
#      3. histogramă pentru tipul de energie selectat
# ============================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader  # pentru a insera imagini (histograma) în PDF

from preprocessing import get_energy_columns


# -----------------------------
# Valori lipsă & duplicate
# -----------------------------
def show_missing_and_duplicates(df: pd.DataFrame):
    """
    Afișează în interfața Streamlit:
    - numărul de valori lipsă (NaN) pe fiecare coloană
    - numărul de rânduri duplicate complet
    - numărul de timestamp-uri duplicate în coloana 'date'
    """
    st.subheader("Valori lipsă (NaN) pe coloane")
    st.write(df.isna().sum())  # afișăm un Series cu numărul de NaN / coloană

    st.subheader("Rânduri duplicate complet")
    dup_rows = df.duplicated().sum()  # rânduri identice pe toate coloanele
    st.write(f"Număr rânduri duplicate: {dup_rows}")

    # Verificăm și duplicatele pe coloana 'date' (aceeași dată/oră înregistrată de mai multe ori)
    if "date" in df.columns:
        st.subheader("Timestamp-uri duplicate (coloana 'date')")
        dup_ts = df["date"].duplicated().sum()
        st.write(f"Număr timestamp-uri duplicate: {dup_ts}")


# -----------------------------
# Statistici descriptive
# -----------------------------
def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculează statisticile descriptive (count, mean, std, min, quartile, max)
    pentru toate coloanele de energie.

    Returnează un DataFrame cu rezultatele (un rând per coloană).
    """
    energy_cols = [c for c in get_energy_columns() if c in df.columns]
    stats = df[energy_cols].describe().T  # transpunem pentru lizibilitate: rânduri = coloane
    return stats


def show_descriptive_stats(df: pd.DataFrame):
    """
    Afișează în Streamlit tabelul cu statisticile descriptive.
    """
    st.subheader("Statistici descriptive pentru tipurile de energie")
    stats = compute_descriptive_stats(df)
    st.dataframe(stats)


# -----------------------------
# Corelații
# -----------------------------
def show_correlation_matrix(df: pd.DataFrame):
    """
    Calculează și afișează:
    - matricea de corelație (Pearson) între tipurile de energie
    - un heatmap pentru această matrice
    """
    st.subheader("Matricea de corelație (Pearson) între tipurile de energie")

    # Alegem doar coloanele care există în DataFrame
    energy_cols = [c for c in get_energy_columns() if c in df.columns]

    # Matricea de corelație
    corr = df[energy_cols].corr()
    st.dataframe(corr)

    # Reprezentare heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(corr, aspect="auto")
    ax.set_xticks(range(len(energy_cols)))
    ax.set_xticklabels(energy_cols, rotation=45)
    ax.set_yticks(range(len(energy_cols)))
    ax.set_yticklabels(energy_cols)
    ax.set_title("Heatmap corelații (Pearson)")
    fig.colorbar(cax)
    st.pyplot(fig)


def show_hour_fotovolt_correlations(df: pd.DataFrame):
    """
    Calculează și afișează corelația dintre:
    - hour (ora zilei)
    - fotovolt (energia fotovoltaică)

    Se calculează atât coeficientul Pearson cât și Spearman.
    """
    st.subheader("Corelații între oră și energia fotovoltaică")

    df_local = df.copy()
    # Ne asigurăm că avem coloana 'hour' (dacă preprocesarea a fost completă, ea există deja)
    if "hour" not in df_local.columns:
        df_local["hour"] = df_local["date"].dt.hour

    # Convertim 'fotovolt' la numeric (dacă nu este deja)
    df_local["fotovolt"] = pd.to_numeric(df_local["fotovolt"], errors="coerce")

    # Coeficientul Pearson
    pearson = df_local[["hour", "fotovolt"]].corr(method="pearson").iloc[0, 1]
    # Coeficientul Spearman
    spearman = df_local[["hour", "fotovolt"]].corr(method="spearman").iloc[0, 1]

    # Afișăm rezultatele în interfață
    st.write(f"Pearson: {pearson:.4f}")
    st.write(f"Spearman: {spearman:.4f}")


# -----------------------------
# Raport PDF pe baza filtrării
# -----------------------------
def create_pdf_report(
    df_filtered: pd.DataFrame,
    selected_energy: list,
    start_date,
    end_date,
    col_hist: str,
) -> bytes:
    """
    Generează un raport PDF cu următoarea structură:

    1. Date filtrate (primele 50 de rânduri)
       - coloanele: 'date' + tipurile de energie selectate
    2. Statistici descriptive pentru datele filtrate
       - count, mean, std, min, max
    3. Histogramă pentru coloana de energie selectată (col_hist)

    Returnează:
        pdf_bytes: conținutul PDF-ului, gata pentru download în Streamlit.
    """
    # Buffer în memorie (nu scriem direct pe disc)
    buffer = BytesIO()

    # Inițializăm un canvas ReportLab, format A4
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4  # lățime și înălțime pagină

    # Stabilim marginea stângă și poziția inițială pe verticală
    x_margin = 40
    y = height - 40

    # -------------------------
    # Titlu și informații generale
    # -------------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_margin, y, "Raport analiză energie electrică")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(x_margin, y, f"Interval de date: {start_date}  –  {end_date}")
    y -= 20

    c.drawString(x_margin, y, "Tipuri de energie selectate:")
    y -= 15
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(x_margin + 15, y, ", ".join(selected_energy))
    y -= 25

    # ======================================================
    # 1. Date filtrate (primele 50 de rânduri)
    # ======================================================
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Date filtrate (primele 50 de rânduri)")
    y -= 20

    # Extragem un eșantion din datele filtrate: 'date' + coloanele energetice selectate
    sample_cols = ["date"] + selected_energy
    sample = df_filtered[sample_cols].head(50).copy()

    # Convertim coloana 'date' la string pentru afișare
    sample["date"] = sample["date"].astype(str)

    # Header-ul tabelului
    headers = list(sample.columns)
    c.setFont("Helvetica-Bold", 8)

    # Calculăm lățimea fiecărei coloane în funcție de lățimea paginii
    usable_width = width - 2 * x_margin
    col_width = usable_width / len(headers)

    # Pozițiile X ale coloanelor
    x_positions = [x_margin + i * col_width for i in range(len(headers))]

    # Funcție internă pentru a (re)desena header-ul tabelului când schimbăm pagina
    def draw_sample_header(title_if_new_page=None):
        nonlocal y
        if title_if_new_page:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, title_if_new_page)
            y -= 20
        c.setFont("Helvetica-Bold", 8)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i], y, str(h))
        y -= 12
        c.setFont("Helvetica", 7)

    # Desenăm header-ul inițial
    draw_sample_header()

    # Desenăm rândurile eșantionului
    c.setFont("Helvetica", 7)
    for _, row in sample.iterrows():
        # Dacă nu mai e spațiu pe pagină, trecem la o nouă pagină
        if y < 60:
            c.showPage()
            y = height - 40
            draw_sample_header("Date filtrate (continuare)")

        for i, h in enumerate(headers):
            val = str(row[h])
            # Tăiem textul dacă e foarte lung
            if len(val) > 20:
                val = val[:17] + "..."
            c.drawString(x_positions[i], y, val)
        y -= 10

    y -= 15  # spațiu înainte de secțiunea următoare

    # ======================================================
    # 2. Statistici descriptive pentru datele filtrate
    # ======================================================
    stats = df_filtered[selected_energy].describe().T
    stats = stats[["count", "mean", "std", "min", "max"]]

    if y < 100:
        # Dacă nu mai e spațiu, trecem la o nouă pagină
        c.showPage()
        y = height - 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Statistici descriptive (date filtrate)")
    y -= 20

    # Header pentru tabelul de statistici
    c.setFont("Helvetica-Bold", 9)
    header_stats = ["Coloană", "count", "mean", "std", "min", "max"]
    col_widths_stats = [90, 60, 60, 60, 60, 60]

    x_positions_stats = [x_margin]
    for w in col_widths_stats[:-1]:
        x_positions_stats.append(x_positions_stats[-1] + w)

    for i, h in enumerate(header_stats):
        c.drawString(x_positions_stats[i], y, h)
    y -= 15
    c.setFont("Helvetica", 9)

    for idx, row in stats.iterrows():
        if y < 60:
            # Pagină nouă și header de continuare
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, "Statistici descriptive (continuare)")
            y -= 20
            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(header_stats):
                c.drawString(x_positions_stats[i], y, h)
            y -= 15
            c.setFont("Helvetica", 9)

        values = [
            idx,
            f"{row['count']:.0f}",
            f"{row['mean']:.2f}",
            f"{row['std']:.2f}",
            f"{row['min']:.2f}",
            f"{row['max']:.2f}",
        ]
        for i, v in enumerate(values):
            c.drawString(x_positions_stats[i], y, str(v))
        y -= 15

    y -= 20  # spațiu înainte de histogramă

    # ======================================================
    # 3. Histogramă pentru coloana de energie selectată
    # ======================================================
    # Construim histograma cu Matplotlib
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(df_filtered[col_hist].dropna(), bins=30)
    ax.set_title(f"Histogramă - {col_hist}")
    ax.set_xlabel("Valori (MW)")
    ax.set_ylabel("Frecvență")

    # Salvăm figura în memorie (buffer PNG)
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="PNG", bbox_inches="tight")
    plt.close(fig)
    img_buffer.seek(0)

    # Creăm un obiect ImageReader pentru ReportLab
    image = ImageReader(img_buffer)

    # Dacă nu mai este suficient spațiu pentru histogramă, trecem pe o pagină nouă
    img_height = 200
    img_width = width - 2 * x_margin
    if y < img_height + 60:
        c.showPage()
        y = height - 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, f"Histogramă pentru {col_hist}")
    y -= 10

    # Desenăm imaginea histogramei în PDF
    c.drawImage(
        image,
        x_margin,
        y - img_height,
        width=img_width,
        height=img_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    y -= img_height + 20

    # Finalizăm pagina curentă și închidem documentul
    c.showPage()
    c.save()

    # Extragem conținutul PDF din buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

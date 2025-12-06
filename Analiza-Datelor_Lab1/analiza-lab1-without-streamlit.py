# =======================================================
# Analiza producției de energie electrică în România
# Preprocesare completă + corelații + vizualizări avansate
# =======================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# -------------------------------
# 1. Încărcare date
# -------------------------------
def load_data(path: str) -> pd.DataFrame:
    """Încarcă fișierul CSV într-un DataFrame."""
    df = pd.read_csv(path)
    print(f"[INFO] Date încărcate din {path}. Forma: {df.shape}")
    return df


# -------------------------------
# 2. Verificare valori lipsă
# -------------------------------
def check_missing(df: pd.DataFrame) -> pd.Series:
    """Calculează și afișează numărul de valori lipsă pe fiecare coloană."""
    missing = df.isna().sum()
    print("\n=== Verificare valori lipsă (NaN) ===")
    print(missing)
    return missing


# -------------------------------
# 3. Verificare duplicate
# -------------------------------
def check_duplicates(df: pd.DataFrame) -> None:
    """Verifică diferite tipuri de duplicate în setul de date."""
    print("\n=== Verificare duplicate ===")

    # 3.1 Rânduri duplicate complet
    dup_rows = df[df.duplicated()]
    print(f"- Rânduri duplicate complet: {dup_rows.shape[0]}")

    # 3.2 Pregătim coloana de timp pentru verificări
    if "date" in df.columns:
        date_dt = pd.to_datetime(df["date"], errors="coerce")
    else:
        date_dt = None

    # 3.3 Timestamp-uri duplicate
    if date_dt is not None:
        dup_ts = df[date_dt.duplicated()]
        print(f"- Timestamp-uri duplicate (coloana 'date'): {dup_ts.shape[0]}")
    else:
        print("- Nu s-a putut verifica timestamp-urile (coloana 'date' lipsește).")

    # 3.4 Duplicate pe subset (date + consum)
    if date_dt is not None and "consum" in df.columns:
        df_temp = df.copy()
        df_temp["date_dt"] = date_dt
        subset_dup = df_temp[df_temp.duplicated(subset=["date_dt", "consum"], keep=False)]
        print(f"- Duplicate pe subset (date + consum): {subset_dup.shape[0]}")
    else:
        print("- Nu s-a putut verifica duplicatele pe subset (date + consum).")

    # 3.5 Near-duplicates (0–60 sec între înregistrări consecutive)
    if date_dt is not None:
        df_sorted = df.copy()
        df_sorted["date_dt"] = date_dt
        df_sorted = df_sorted.sort_values("date_dt")
        df_sorted["diff_sec"] = df_sorted["date_dt"].diff().dt.total_seconds()
        near_dups = df_sorted[(df_sorted["diff_sec"] >= 0) & (df_sorted["diff_sec"] <= 60)]
        print(f"- Near-duplicates (0–60 sec): {near_dups.shape[0]}")
    else:
        print("- Nu s-a putut verifica near-duplicates.")

    # 3.6 Approximate duplicates (după rotunjire)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        rounded = df.copy()
        rounded[numeric_cols] = rounded[numeric_cols].round(0)
        approx_dups = rounded[rounded.duplicated(subset=numeric_cols, keep=False)]
        print(f"- Approximate duplicates (numerice egale după rotunjire): {approx_dups.shape[0]}")
    else:
        print("- Nu există coloane numerice pentru verificarea approximate duplicates.")


# -------------------------------
# 4. Conversie 'date' în datetime
# -------------------------------
def convert_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Convertește coloana 'date' în datetime."""
    if "date" not in df.columns:
        raise KeyError("Coloana 'date' nu există în DataFrame.")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    print("\n[INFO] Coloana 'date' a fost convertită la datetime.")
    return df


# -------------------------------
# 5. Componente de timp
# -------------------------------
def add_time_components(df: pd.DataFrame) -> pd.DataFrame:
    """Adaugă coloanele year, month, day, hour, minute, weekday."""
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["hour"] = df["date"].dt.hour
    df["minute"] = df["date"].dt.minute
    df["weekday"] = df["date"].dt.weekday  # 0 = Luni
    print("[INFO] Componentele de timp au fost adăugate.")
    return df


# -------------------------------
# 6. Conversie numerică
# -------------------------------
def convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convertește toate coloanele (în afară de 'date') la numeric acolo unde este posibil."""
    numeric_cols = df.columns.drop("date")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print("[INFO] Conversia coloanelor numerice a fost realizată.")
    return df


# -------------------------------
# 7. Standardizare categorice
# -------------------------------
def standardize_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """Adaugă year_str, month_name, weekday_name."""
    df["year_str"] = df["year"].astype(str)

    month_map = {
        1: "Ianuarie", 2: "Februarie", 3: "Martie", 4: "Aprilie",
        5: "Mai", 6: "Iunie", 7: "Iulie", 8: "August",
        9: "Septembrie", 10: "Octombrie", 11: "Noiembrie", 12: "Decembrie"
    }
    df["month_name"] = df["month"].map(month_map)

    weekday_map = {
        0: "Luni", 1: "Marți", 2: "Miercuri", 3: "Joi",
        4: "Vineri", 5: "Sâmbătă", 6: "Duminică"
    }
    df["weekday_name"] = df["weekday"].map(weekday_map)

    print("[INFO] Variabilele categorice au fost standardizate.")
    return df


# -------------------------------
# 8. Salvare versiuni CSV
# -------------------------------
def save_versions(df: pd.DataFrame, base_dir: str = "."):
    """Salvează versiunile procesate ale datelor."""
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(base_dir / "data_converted.csv", index=False)
    df.to_csv(base_dir / "data_categorical_standardized.csv", index=False)

    print("\n[INFO] Fișiere salvate:")
    print(f" - {base_dir / 'data_converted.csv'}")
    print(f" - {base_dir / 'data_categorical_standardized.csv'}")


# -------------------------------
# 9. Statistici descriptive
# -------------------------------
def get_energy_columns():
    return [
        "carbune", "hidro", "hidrocarburi", "nuclear",
        "eolian", "fotovolt", "biomasa", "productie", "consum"
    ]


def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculează statisticile descriptive pentru tipurile de energie."""
    energy_cols = get_energy_columns()
    stats = df[energy_cols].describe().T
    print("\n=== Statistici descriptive (energie) ===")
    print(stats)
    return stats


# -------------------------------
# 10. Histograme pe tipuri de energie
# -------------------------------
def plot_histograms(df: pd.DataFrame, out_dir: str = "plots"):
    """Generează și salvează histograme pentru fiecare tip de energie."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    energy_cols = get_energy_columns()

    for col in energy_cols:
        plt.figure(figsize=(6, 4))
        plt.hist(df[col].dropna(), bins=30)
        plt.title(f"Histogramă - {col}")
        plt.xlabel("Valori (MW)")
        plt.ylabel("Frecvență")
        plt.tight_layout()
        plt.savefig(Path(out_dir) / f"hist_{col}.png", dpi=150)
        plt.close()

    print(f"[INFO] Histograme salvate în folderul '{out_dir}/'.")


# -------------------------------
# 11. Corelații oră – fotovoltaic
# -------------------------------
def compute_hour_fotovolt_correlations(df: pd.DataFrame):
    """Calculează corelațiile Pearson și Spearman între oră și fotovoltaic."""
    if "hour" not in df.columns:
        df["hour"] = df["date"].dt.hour

    df["fotovolt"] = pd.to_numeric(df["fotovolt"], errors="coerce")

    pearson = df[["hour", "fotovolt"]].corr(method="pearson").iloc[0, 1]
    spearman = df[["hour", "fotovolt"]].corr(method="spearman").iloc[0, 1]

    print("\n=== Corelații între oră și energia fotovoltaică ===")
    print(f"Pearson : {pearson:.4f}")
    print(f"Spearman: {spearman:.4f}")

    return pearson, spearman


# -------------------------------
# 12. Heatmap energie – ore
# -------------------------------
def plot_heatmap_hour_energy(df: pd.DataFrame, out_dir: str = "plots"):
    """Heatmap pentru producția medie pe ore pentru fiecare tip de energie."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if "hour" not in df.columns:
        df["hour"] = df["date"].dt.hour

    energy_cols = get_energy_columns()
    for col in energy_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    hourly_matrix = df.groupby("hour")[energy_cols].mean()

    plt.figure(figsize=(10, 6))
    plt.imshow(hourly_matrix, aspect="auto")
    plt.title("Heatmap: Producția medie de energie pe ore")
    plt.xlabel("Tip energie")
    plt.ylabel("Ora zilei")
    plt.xticks(range(len(energy_cols)), energy_cols, rotation=45)
    plt.yticks(range(24), range(24))
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "heatmap_energie_ore.png", dpi=150)
    plt.close()

    print(f"[INFO] Heatmap energie–ore salvat în '{out_dir}/heatmap_energie_ore.png'.")


# -------------------------------
# 13. Heatmap energie – luni
# -------------------------------
def plot_heatmap_month_energy(df: pd.DataFrame, out_dir: str = "plots"):
    """Heatmap pentru producția medie pe luni pentru fiecare tip de energie."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if "month" not in df.columns:
        df["month"] = df["date"].dt.month

    energy_cols = get_energy_columns()
    for col in energy_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    monthly_matrix = df.groupby("month")[energy_cols].mean()

    plt.figure(figsize=(10, 6))
    plt.imshow(monthly_matrix, aspect="auto")
    plt.title("Heatmap: Producția medie de energie pe luni")
    plt.xlabel("Tip energie")
    plt.ylabel("Lună")
    plt.xticks(range(len(energy_cols)), energy_cols, rotation=45)
    plt.yticks(range(1, 13), range(1, 13))
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "heatmap_energie_luni.png", dpi=150)
    plt.close()

    print(f"[INFO] Heatmap energie–luni salvat în '{out_dir}/heatmap_energie_luni.png'.")


# -------------------------------
# 14. Producția medie lunară pe tipuri (stacked bar)
# -------------------------------
def plot_monthly_production_by_type(df: pd.DataFrame, out_dir: str = "plots"):
    """Stacked bar cu producția medie lunară pe tipuri de energie."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["month"] = df["date"].dt.month
    energy_cols = ["carbune", "hidro", "hidrocarburi", "nuclear",
                   "eolian", "fotovolt", "biomasa"]

    for col in energy_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    monthly_prod = df.groupby("month")[energy_cols].mean()

    plt.figure(figsize=(10, 6))
    bottom_vals = None
    for col in energy_cols:
        if bottom_vals is None:
            plt.bar(monthly_prod.index, monthly_prod[col])
            bottom_vals = monthly_prod[col].copy()
        else:
            plt.bar(monthly_prod.index, monthly_prod[col], bottom=bottom_vals)
            bottom_vals += monthly_prod[col]

    plt.title("Producția medie lunară pe tipuri de energie")
    plt.xlabel("Lună")
    plt.ylabel("Producție medie (MW)")
    plt.xticks(range(1, 13))
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "stacked_prod_lunar_tipuri.png", dpi=150)
    plt.close()

    print(f"[INFO] Stacked bar producție lunară pe tipuri salvat în '{out_dir}/stacked_prod_lunar_tipuri.png'.")


# -------------------------------
# 15. Sold zilnic pentru 2024 și 2025
# -------------------------------
def plot_daily_sold_2024_2025(df: pd.DataFrame, out_dir: str = "plots"):
    """Graficul soldului zilnic pentru 2024 și 2025."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["year"] = df["date"].dt.year
    df["day"] = df["date"].dt.date
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")
    df["consum"] = pd.to_numeric(df["consum"], errors="coerce")
    df["sold"] = df["productie"] - df["consum"]

    daily_sold = df.groupby(["year", "day"])["sold"].mean().reset_index()
    sold_2024 = daily_sold[daily_sold["year"] == 2024]
    sold_2025 = daily_sold[daily_sold["year"] == 2025]

    plt.figure(figsize=(12, 6))
    plt.plot(sold_2024["day"], sold_2024["sold"], label="2024")
    plt.plot(sold_2025["day"], sold_2025["sold"], label="2025")
    plt.axhline(0)
    plt.title("Soldul zilnic (Producție - Consum) pentru anii 2024 și 2025")
    plt.xlabel("Ziua")
    plt.ylabel("Sold zilnic (MW)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "sold_zilnic_2024_2025.png", dpi=150)
    plt.close()

    print(f"[INFO] Grafic sold zilnic 2024/2025 salvat în '{out_dir}/sold_zilnic_2024_2025.png'.")


# -------------------------------
# 16. Seria temporală a soldului
# -------------------------------
def plot_sold_timeseries(df: pd.DataFrame, out_dir: str = "plots"):
    """Seria temporală completă a soldului (producție - consum)."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df = df.sort_values("date")
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")
    df["consum"] = pd.to_numeric(df["consum"], errors="coerce")
    df["sold"] = df["productie"] - df["consum"]

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["sold"])
    plt.axhline(0)
    plt.title("Seria temporală a soldului energetic (Producție - Consum)")
    plt.xlabel("Data")
    plt.ylabel("Sold (MW)")
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "sold_serie_temporala.png", dpi=150)
    plt.close()

    print(f"[INFO] Seria temporală a soldului salvată în '{out_dir}/sold_serie_temporala.png'.")


# -------------------------------
# 17. Peak-ul producției medii pe ore
# -------------------------------
def plot_hourly_mean_production(df: pd.DataFrame, out_dir: str = "plots"):
    """Producția medie pe ore (peak orar)."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["hour"] = df["date"].dt.hour
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")

    hourly_mean_prod = df.groupby("hour")["productie"].mean()

    plt.figure(figsize=(8, 5))
    plt.plot(hourly_mean_prod.index, hourly_mean_prod.values)
    plt.title("Producția medie pe ore")
    plt.xlabel("Ora zilei")
    plt.ylabel("Producție medie (MW)")
    plt.xticks(range(24))
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "prod_medie_pe_ore.png", dpi=150)
    plt.close()

    print(f"[INFO] Producția medie pe ore salvată în '{out_dir}/prod_medie_pe_ore.png'.")


# -------------------------------
# 18. Consum mediu pe zilele săptămânii
# -------------------------------
def plot_weekday_mean_consumption(df: pd.DataFrame, out_dir: str = "plots"):
    """Consumul mediu pe zilele săptămânii."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["weekday"] = df["date"].dt.weekday
    df["consum"] = pd.to_numeric(df["consum"], errors="coerce")

    weekday_mean = df.groupby("weekday")["consum"].mean()
    weekday_names = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]

    plt.figure(figsize=(8, 5))
    plt.plot(weekday_mean.index, weekday_mean.values)
    plt.xticks(range(7), weekday_names, rotation=45)
    plt.title("Consumul mediu pe zilele săptămânii")
    plt.xlabel("Ziua săptămânii")
    plt.ylabel("Consum mediu (MW)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "consum_med_pe_zile_sapt.png", dpi=150)
    plt.close()

    print(f"[INFO] Consum mediu pe zilele săptămânii salvat în '{out_dir}/consum_med_pe_zile_sapt.png'.")


# -------------------------------
# 19. Producția medie lunară 2024 vs 2025
# -------------------------------
def plot_monthly_mean_production_2024_2025(df: pd.DataFrame, out_dir: str = "plots"):
    """Producția medie lunară pentru anii 2024 și 2025."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")

    monthly_prod = df.groupby(["year", "month"])["productie"].mean().reset_index()
    prod_2024 = monthly_prod[monthly_prod["year"] == 2024]
    prod_2025 = monthly_prod[monthly_prod["year"] == 2025]

    plt.figure(figsize=(10, 6))
    plt.plot(prod_2024["month"], prod_2024["productie"], marker="o", label="2024")
    plt.plot(prod_2025["month"], prod_2025["productie"], marker="o", label="2025")
    plt.title("Producția medie lunară pentru anii 2024 și 2025")
    plt.xlabel("Lună")
    plt.ylabel("Producție medie (MW)")
    plt.xticks(range(1, 13))
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "prod_med_lunar_2024_2025.png", dpi=150)
    plt.close()

    print(f"[INFO] Producția medie lunară 2024/2025 salvată în '{out_dir}/prod_med_lunar_2024_2025.png'.")


# -------------------------------
# 20. Comparație producție vs consum (toată perioada)
# -------------------------------
def plot_production_vs_consumption(df: pd.DataFrame, out_dir: str = "plots"):
    """Comparația grafică între producție și consum pe toată perioada."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df = df.sort_values("date")
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")
    df["consum"] = pd.to_numeric(df["consum"], errors="coerce")

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["productie"], label="Producție")
    plt.plot(df["date"], df["consum"], label="Consum")
    plt.title("Comparație grafică între producție și consum")
    plt.xlabel("Data")
    plt.ylabel("MW")
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "prod_vs_consum.png", dpi=150)
    plt.close()

    print(f"[INFO] Comparația producție vs consum salvată în '{out_dir}/prod_vs_consum.png'.")


# -------------------------------
# 21. Comparație producție & consum: 2024 vs 2025
# -------------------------------
def plot_production_vs_consumption_by_year(df: pd.DataFrame, out_dir: str = "plots"):
    """Comparație grafică între producție și consum pentru anii 2024 și 2025."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    df["year"] = df["date"].dt.year
    df["productie"] = pd.to_numeric(df["productie"], errors="coerce")
    df["consum"] = pd.to_numeric(df["consum"], errors="coerce")

    df_2024 = df[df["year"] == 2024].sort_values("date")
    df_2025 = df[df["year"] == 2025].sort_values("date")

    plt.figure(figsize=(14, 6))
    plt.plot(df_2024["date"], df_2024["productie"], label="Producție 2024")
    plt.plot(df_2024["date"], df_2024["consum"], label="Consum 2024")
    plt.plot(df_2025["date"], df_2025["productie"], label="Producție 2025", linestyle="--")
    plt.plot(df_2025["date"], df_2025["consum"], label="Consum 2025", linestyle="--")
    plt.title("Comparație grafică între producție și consum pentru anii 2024 și 2025")
    plt.xlabel("Data")
    plt.ylabel("MW")
    plt.legend()
    plt.tight_layout()
    plt.savefig(Path(out_dir) / "prod_vs_consum_2024_2025.png", dpi=150)
    plt.close()

    print(f"[INFO] Comparația producție/consum 2024/2025 salvată în '{out_dir}/prod_vs_consum_2024_2025.png'.")


# -------------------------------
# MAIN
# -------------------------------
def main():
    # Path real al fișierului inițial
    input_path = r"E:\documents\master\year_I\sem_I\analiza-și-vizualizarea-datelor\lab1\data.csv"

    # 1. Load
    df = load_data(input_path)

    # 2. Missing values
    check_missing(df)

    # 3. Duplicates
    check_duplicates(df)

    # 4. Convert 'date'
    df = convert_datetime(df)

    # 5. Time components
    df = add_time_components(df)

    # 6. Numeric conversion
    df = convert_numeric(df)

    # 7. Categorical standardization
    df = standardize_categorical(df)

    # 8. Save processed CSVs
    save_versions(df, base_dir=".")

    # 9. Descriptive stats
    compute_descriptive_stats(df)

    # 10. Visualizations
    out_dir = "plots"
    plot_histograms(df, out_dir=out_dir)
    compute_hour_fotovolt_correlations(df)
    plot_heatmap_hour_energy(df, out_dir=out_dir)
    plot_heatmap_month_energy(df, out_dir=out_dir)
    plot_monthly_production_by_type(df, out_dir=out_dir)
    plot_daily_sold_2024_2025(df, out_dir=out_dir)
    plot_sold_timeseries(df, out_dir=out_dir)
    plot_hourly_mean_production(df, out_dir=out_dir)
    plot_weekday_mean_consumption(df, out_dir=out_dir)
    plot_monthly_mean_production_2024_2025(df, out_dir=out_dir)
    plot_production_vs_consumption(df, out_dir=out_dir)
    plot_production_vs_consumption_by_year(df, out_dir=out_dir)

    print("\n[INFO] Procesarea completă și toate vizualizările s-au încheiat.")


if __name__ == "__main__":
    main()

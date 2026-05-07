from pathlib import Path
import pandas as pd

PRODUCCION = Path("runtime_lab/recoleccion/outputs/resumen_global.csv")
COSTES = Path("runtime_lab/recoleccion/data/22-04-2026_coste.csv")

OUTPUT = Path("runtime_lab/recoleccion/outputs/coste_por_kg.csv")


def main() -> None:
    df_prod = pd.read_csv(PRODUCCION)
    df_cost = pd.read_csv(COSTES)

    # Normalización defensiva
    df_prod["trabajador"] = df_prod["trabajador"].str.strip().str.upper()
    df_cost["trabajador"] = df_cost["trabajador"].str.strip().str.upper()

    # Cruce
    df = df_prod.merge(
        df_cost,
        on=["fecha", "trabajador"],
        how="inner",
    )

    # Validación
    if (df["kg_totales"] <= 0).any():
        raise ValueError("Hay trabajadores con kg_totales <= 0")

    # Métrica
    df["coste_por_kg"] = (
        df["coste"] / df["kg_totales"]
    ).round(3)

    # Orden
    df = df.sort_values(
        by=["fecha", "coste_por_kg"]
    )

    # Output
    columnas = [
        "fecha",
        "trabajador",
        "kg_totales",
        "coste",
        "coste_por_kg",
        "num_cajas",
    ]

    df[columnas].to_csv(
        OUTPUT,
        index=False
    )

    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    main()
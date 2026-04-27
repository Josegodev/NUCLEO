from pathlib import Path
import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT = BASE_DIR / "outputs" / "resumen_global.csv"

VALID_WEIGHTS = {4, 5, 6, 7, 8, 10}


def procesar_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    caja_cols = [f"caja_{i}" for i in range(1, 21)]
    expected = ["fecha", "trabajador"] + caja_cols

    if list(df.columns) != expected:
        raise ValueError(f"Cabecera inválida en {path}")

    if df["fecha"].nunique() != 1:
        raise ValueError(f"El CSV debe tener una única fecha: {path}")

    for col in caja_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valores = df[caja_cols].stack().dropna().astype(int)
    invalidos = sorted(set(valores) - VALID_WEIGHTS- {0})
    if invalidos:
        raise ValueError(f"Pesos inválidos en {path}: {invalidos}")

    resumen = df[["fecha", "trabajador"]].copy()
    resumen["kg_totales"] = df[caja_cols].sum(axis=1, skipna=True).round().astype(int)
    resumen["num_cajas"] = df[caja_cols].gt(0).sum(axis=1)
    resumen["archivo_origen"] = path.name

    return resumen


def main() -> None:
    archivos = sorted(DATA_DIR.glob("*_recoleccion.csv"))

    if not archivos:
        raise FileNotFoundError(f"No hay CSV en {DATA_DIR}")

    resultados = [procesar_csv(path) for path in archivos]

    resumen_global = pd.concat(resultados, ignore_index=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    resumen_global.to_csv(OUTPUT, index=False)

    print(resumen_global)
    print(f"OK -> {OUTPUT}")


if __name__ == "__main__":
    main()
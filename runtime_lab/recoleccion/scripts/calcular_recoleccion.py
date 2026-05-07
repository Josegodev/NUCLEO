from pathlib import Path
import csv
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT = BASE_DIR / "outputs" / "resumen_global.csv"

VALID_WEIGHTS = {4, 5, 6, 7, 8, 10, 16,32 }

CAJA_COLS = [f"caja_{i}" for i in range(1, 21)]
EXPECTED_COLUMNS = ["fecha", "trabajador"] + CAJA_COLS
EXPECTED_LEN = len(EXPECTED_COLUMNS)


def leer_csv_recoleccion(path: Path) -> pd.DataFrame:
    rows = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"CSV vacío: {path}")

        if header != EXPECTED_COLUMNS:
            raise ValueError(f"Cabecera inválida en {path}: {header}")

        for line_no, row in enumerate(reader, start=2):
            while len(row) > EXPECTED_LEN and row[-1] == "":
                row.pop()

            if len(row) > EXPECTED_LEN:
                raise ValueError(
                    f"{path}: línea {line_no} tiene columnas extra con datos: {row}"
                )

            if len(row) < EXPECTED_LEN:
                row += [""] * (EXPECTED_LEN - len(row))

            rows.append(row)

    return pd.DataFrame(rows, columns=EXPECTED_COLUMNS)


def procesar_csv(path: Path) -> pd.DataFrame:
    df = leer_csv_recoleccion(path)

    if df["fecha"].nunique() != 1:
        raise ValueError(f"El CSV debe tener una única fecha: {path}")

    for col in CAJA_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valores = df[CAJA_COLS].stack().dropna().astype(int)
    invalidos = sorted(set(valores) - VALID_WEIGHTS - {0})
    if invalidos:
        raise ValueError(f"Pesos inválidos en {path}: {invalidos}")

    resumen = df[["fecha", "trabajador"]].copy()
    resumen["kg_totales"] = df[CAJA_COLS].sum(axis=1, skipna=True).round().astype(int)
    resumen["num_cajas"] = df[CAJA_COLS].gt(0).sum(axis=1)
    

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

from __future__ import annotations


from pathlib import Path

import pandas as pd


def caged_ts_load(caminho_parquet: str | Path) -> pd.DataFrame:
    """
    Lê um arquivo Parquet do CAGED, converte a coluna 'competencia'
    no formato YYYYMM para datetime e a define como índice temporal.

    Parameters
    ----------
    caminho_parquet : str | pathlib.Path
        Caminho para o arquivo Parquet.

    Returns
    -------
    pd.DataFrame
        DataFrame ordenado cronologicamente e indexado por competencia.
    """
    df = pd.read_parquet(caminho_parquet)

    if "competencia" not in df.columns:
        raise KeyError(
            "A coluna 'competencia' não foi encontrada. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    df["competencia"] = pd.to_datetime(
        df["competencia"].astype("string"),
        format="%Y%m",
        errors="raise"
    )

    if df["competencia"].duplicated().any():
        competencias_duplicadas = (
            df.loc[
                df["competencia"].duplicated(keep=False),
                "competencia"
            ]
            .dt.strftime("%Y-%m")
            .unique()
            .tolist()
        )

        raise ValueError(
            "Há mais de uma linha para pelo menos uma competência. "
            f"Competências duplicadas: {competencias_duplicadas}"
        )

    return (
        df
        .sort_values("competencia")
        .set_index("competencia")
    )
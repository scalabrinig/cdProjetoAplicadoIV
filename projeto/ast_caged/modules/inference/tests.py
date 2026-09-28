from statsmodels.tsa.stattools import adfuller, kpss
import pandas as pd
import numpy as np
import warnings

def adf_test(
        serie: pd.Series,
        autolag: str = "AIC",
        result_object = False,
    ):

    # Executa o teste ADF sobre o saldo mensal
    resultado_adf = adfuller(
        serie,
        autolag = autolag,
    )

    return {
        "adf_statistic": resultado_adf[0],
        "adf_pvalor": resultado_adf[1],
        "adf_lags": resultado_adf[2],
        "adf_observacoes": resultado_adf[3],
        "adf_valores_criticos": resultado_adf[5],
    }



def kpss_test(serie: pd.Series, regression: str = "c") -> dict:
    
    valores = serie.dropna().to_numpy(dtype=float)

    if not np.isfinite(valores).all():
        raise ValueError("A série contém valores infinitos.")
    if regression not in ("c", "ct"):
        raise ValueError("regression deve ser 'c' ou 'ct'.")

    resultado = kpss(
        valores,
        regression=regression,
        nlags="auto",
        result_object=True,
    )

    return {
        "kpss_statistic": float(resultado.statistic),
        "kpss_pvalor": float(resultado.pvalue),
        "kpss_lags": int(resultado.lags),
        "kpss_valores_criticos": dict(resultado.critical_values),
    }
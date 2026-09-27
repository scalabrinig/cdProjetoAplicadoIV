import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import boxcox


def lambda_guerrero(
    serie: pd.Series,
    periodo: int = 12,
    limites: tuple[float, float] = (-0.9, 2.0),
) -> float:
    """Estima o lambda de Box-Cox pelo método de Guerrero."""
    valores = serie.to_numpy(dtype=float)

    if periodo < 2:
        raise ValueError("O período deve ser pelo menos 2.")
    if not np.isfinite(valores).all():
        raise ValueError("A série não pode conter valores ausentes ou infinitos.")
    if (valores <= 0).any():
        raise ValueError("Box-Cox requer valores estritamente positivos.")

    n_blocos = len(valores) // periodo
    if n_blocos < 2:
        raise ValueError("São necessários pelo menos dois períodos completos.")

    if np.all(valores == valores[0]):
        return 1.0

    # Mantém os períodos completos mais recentes, como em feasts.
    blocos = valores[-n_blocos * periodo:].reshape(n_blocos, periodo)

    medias = blocos.mean(axis=1)
    desvios = blocos.std(axis=1, ddof=1)

    if np.all(desvios == 0):
        return 1.0

    def criterio(lmbda: float) -> float:
        razoes = desvios / medias ** (1 - lmbda)
        if razoes.mean() == 0:
            return np.inf
        return razoes.std(ddof=1) / razoes.mean()

    resultado = minimize_scalar(
        criterio,
        bounds=limites,
        method="bounded",
    )

    if not resultado.success:
        raise RuntimeError("Não foi possível estimar o lambda.")

    return float(resultado.x)


def box_cox(
        serie: pd.Series,
        lmbda: float,
    ) -> pd.Series:
    
    valores = serie.to_numpy(dtype=float)

    if not np.isfinite(lmbda):
        raise ValueError("Lambda deve ser finito.")
    if not np.isfinite(valores).all():
        raise ValueError("Box-Cox exige que não haja valores ausentes ou infinitos.")
    if (valores <= 0).any():
        raise ValueError("Box-Cox exige quetodos os valores sejam estritamente positivos.")

    boxcox_serie = boxcox(valores, lmbda = lmbda)

    return pd.Series(
        boxcox_serie,
        index = serie.index,
        name = serie.name + "_boxcox"
    )


def max_min(serie: pd.Series):
    amplitude = serie.max() - serie.min()
    if amplitude == 0:
        raise ValueError("Não é possível transformar uma série constante.")
    return (serie-serie.min()) / amplitude
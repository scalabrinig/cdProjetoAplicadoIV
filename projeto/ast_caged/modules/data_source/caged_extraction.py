from __future__ import annotations


from ast_caged.modules.utils.utils import exception_trackers
import itertools
import json
from datetime import datetime
from ftplib import FTP
from pathlib import Path
from typing import Any

import pandas as pd
import py7zr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # ast_caged/
PATHS_CONFIG_FILE = PACKAGE_ROOT / "config" / "paths.json"

FTP_HOST = "ftp.mtps.gov.br"
FTP_BASE_DIRECTORY = "/pdet/microdados/NOVO CAGED"

COMPETENCIA_COLUMN = "competênciamov"

class CagedFileNotFoundError(FileNotFoundError):
    pass



def load_json(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)



def resolve_project_path(relative_path: str) -> Path:
    return (PROJECT_ROOT / relative_path).resolve()


# def load_settings() -> tuple[dict[str, Path], dict[str, Any]]:
#     paths_config = load_json(PATHS_CONFIG_FILE)

#     required_path_keys = [
#         "raw_caged",
#         "extracted_caged",
#         "processed_caged",
#     ]

#     data_paths = paths_config.get("data", {})

#     missing_keys = [key for key in required_path_keys if key not in data_paths]

#     if missing_keys:
#         raise KeyError(
#             "Chaves ausentes em paths.json, dentro de 'data': "
#             f"{', '.join(missing_keys)}"
#         )

#     etl_filter_relative_path = paths_config.get("config", {}).get("etl_filter")

#     if not etl_filter_relative_path:
#         raise KeyError(
#             "A chave 'config.etl_filter' não foi encontrada em paths.json."
#         )

#     paths = {
#         "raw_caged": resolve_project_path(data_paths["raw_caged"]),
#         "extracted_caged": resolve_project_path(data_paths["extracted_caged"]),
#         "processed_caged": resolve_project_path(data_paths["processed_caged"]),
#         "etl_filter": resolve_project_path(etl_filter_relative_path),
#     }

#     etl_filters = load_json(paths["etl_filter"])

#     return paths, etl_filters



def create_directories(paths: dict[str, Path]) -> None:
    for key in (
        "raw_caged",
        "extracted_caged",
        "processed_caged",
        "ready_caged",
    ):
        paths[key].mkdir(parents=True, exist_ok=True)


def normalize_competencia(competencia: str | int) -> str:
    competencia = str(competencia)

    if len(competencia) != 6 or not competencia.isdigit():
        raise ValueError(
            f"Competência inválida: {competencia}. Use o formato AAAAMM."
        )

    mes = int(competencia[-2:])

    if not 1 <= mes <= 12:
        raise ValueError(
            f"Competência inválida: {competencia}. O mês deve estar entre 01 e 12."
        )

    return competencia


# def resolve_competencias(competencias_config: dict[str, Any]) -> list[str]:
#     modo = competencias_config.get("modo", "lista")

#     if modo == "lista":
#         valores = competencias_config.get("valores", [])

#         if not valores:
#             raise ValueError(
#                 "O campo 'competencias.valores' está vazio. "
#                 "Informe pelo menos uma competência."
#             )

#         return [normalize_competencia(c) for c in valores]

#     elif modo == "desde":
#         inicio = competencias_config.get("inicio")

#         if not inicio:
#             raise ValueError(
#                 "O campo 'competencias.inicio' é obrigatório no modo 'desde'."
#             )

#         inicio = normalize_competencia(inicio)
#         hoje = datetime.now()
#         competencias = []

#         ano_inicio = int(inicio[:4])
#         mes_inicio = int(inicio[4:])

#         ano_atual = hoje.year
#         mes_atual = hoje.month

#         for ano in range(ano_inicio, ano_atual + 1):
#             for mes in range(1, 13):
#                 if ano == ano_inicio and mes < mes_inicio:
#                     continue
#                 if ano == ano_atual and mes > mes_atual:
#                     break

#                 competencias.append(f"{ano}{mes:02d}")

#         return competencias

#     elif modo == "intervalo":
#         inicio = competencias_config.get("inicio")
#         fim = competencias_config.get("fim")

#         if not inicio or not fim:
#             raise ValueError(
#                 "Os campos 'competencias.inicio' e 'competencias.fim' "
#                 "são obrigatórios no modo 'intervalo'."
#             )

#         inicio = normalize_competencia(inicio)
#         fim = normalize_competencia(fim)

#         ano_inicio = int(inicio[:4])
#         mes_inicio = int(inicio[4:])
#         ano_fim = int(fim[:4])
#         mes_fim = int(fim[4:])

#         competencias = []

#         for ano in range(ano_inicio, ano_fim + 1):
#             for mes in range(1, 13):
#                 if ano == ano_inicio and mes < mes_inicio:
#                     continue
#                 if ano == ano_fim and mes > mes_fim:
#                     break

#                 competencias.append(f"{ano}{mes:02d}")

#         return competencias

#     else:
#         raise ValueError(
#             f"Modo de competências inválido: {modo}. "
#             "Use 'lista', 'desde' ou 'intervalo'."
#         )


def normalizar_competencia(competencia: str | int) -> str:
    competencia = str(competencia)

    if len(competencia) != 6 or not competencia.isdigit():
        raise ValueError(
            f"Competência inválida: {competencia}. Use o formato AAAAMM."
        )

    mes = int(competencia[-2:])

    if not 1 <= mes <= 12:
        raise ValueError(
            f"Competência inválida: {competencia}. O mês deve estar entre 01 e 12."
        )

    return competencia



def proximo_mes(competencia: str) -> str:
    ano = int(competencia[:4])
    mes = int(competencia[-2:])

    mes += 1

    if mes > 12:
        mes = 1
        ano += 1

    return f"{ano:04d}{mes:02d}"



def resolve_competencias(config: dict) -> list[str]:
    competencias_config = config.get("competencias", {})

    modo = competencias_config.get("modo", "lista")

    if modo == "lista":
        valores = competencias_config.get("valores", [])

        if not valores:
            raise ValueError(
                "O campo 'competencias.valores' está vazio. "
                "Informe pelo menos uma competência no formato AAAAMM."
            )

        return [normalizar_competencia(c) for c in valores]

    elif modo == "desde":
        inicio = competencias_config.get("inicio")

        if not inicio:
            raise ValueError(
                "No modo 'desde', o campo 'competencias.inicio' é obrigatório."
            )

        inicio = normalizar_competencia(inicio)

        fim = competencias_config.get("fim")

        if fim is not None:
            fim = normalizar_competencia(fim)
        else:
            agora = datetime.now()
            fim = f"{agora.year:04d}{agora.month:02d}"

        if inicio > fim:
            raise ValueError(
                f"'inicio' ({inicio}) não pode ser maior que 'fim' ({fim})."
            )

        competencias = []
        competencia_atual = inicio

        while competencia_atual <= fim:
            competencias.append(competencia_atual)
            competencia_atual = proximo_mes(competencia_atual)

        return competencias

    else:
        raise ValueError(
            f"Modo de competências inválido: {modo}. Use 'lista' ou 'desde'."
        )



def load_settings() -> tuple[dict[str, Path], dict[str, Any]]:
    paths_config = load_json(PATHS_CONFIG_FILE)

    data_paths = paths_config.get("data", {})

    paths = {
        "raw_caged": resolve_project_path(data_paths["raw_caged"]),
        "extracted_caged": resolve_project_path(data_paths["extracted_caged"]),
        "processed_caged": resolve_project_path(data_paths["processed_caged"]),
        "ready_caged": resolve_project_path(data_paths["ready_caged"]),
        "etl_filter": resolve_project_path(
            paths_config["config"]["etl_filter"]
        ),
    }

    etl_filters = load_json(paths["etl_filter"])

    competencias = resolve_competencias(etl_filters)

    etl_filters["_competencias_resolvidas"] = competencias

    return paths, etl_filters



def validate_category_config(category_config: dict[str, Any]) -> None:
    if "incluir" not in category_config:
        raise KeyError("A chave 'incluir' é obrigatória em cada categoria.")

    if "fragmentar" not in category_config:
        raise KeyError("A chave 'fragmentar' é obrigatória em cada categoria.")

    if not isinstance(category_config["incluir"], list):
        raise TypeError("O campo 'incluir' deve ser uma lista.")

    if not isinstance(category_config["fragmentar"], bool):
        raise TypeError("O campo 'fragmentar' deve ser um booleano.")


def load_catalog_values(
    category_key: str,
    catalog_directory: Path,
) -> list[str]:
    catalog_path = catalog_directory / f"{category_key}.csv"

    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Catálogo não encontrado para a categoria '{category_key}': "
            f"{catalog_path}"
        )

    catalog = pd.read_csv(
        catalog_path,
        sep=";",
        encoding="utf-8",
        dtype="string",
        usecols=[0],
    )
    values = catalog.iloc[:, 0].dropna().str.strip()
    values = values[values != ""]

    if values.empty:
        raise ValueError(
            f"O catálogo da categoria '{category_key}' não possui códigos."
        )

    return values.drop_duplicates().tolist()


def build_fragments(
    categories_config: dict[str, dict[str, Any]],
    catalog_directory: Path | None = None,
    max_arquivos: int | None = None,
) -> list[dict[str, Any]]:
    validated_categories = {}

    for category_key, category_config in categories_config.items():
        validate_category_config(category_config)

        incluir = category_config["incluir"]
        fragmentar = category_config["fragmentar"]

        if len(incluir) == 1:
            fragmentar = False

        validated_categories[category_key] = {
            "incluir": incluir,
            "fragmentar": fragmentar,
        }

    fixed_filters = {}
    for key, category in validated_categories.items():
        if category["incluir"] and not category["fragmentar"]:
            values = category["incluir"]
            fixed_filters[key] = (
                values[0] if len(values) == 1 else values
            )

    fragment_dimensions = {}
    for key, category in validated_categories.items():
        if not category["fragmentar"]:
            continue

        values = category["incluir"]
        if not values:
            if catalog_directory is None:
                raise ValueError(
                    f"A categoria '{key}' precisa do diretório do catálogo "
                    "para fragmentar todos os valores."
                )

            catalog_path = catalog_directory / f"{key}.csv"
            if not catalog_path.exists():
                print(
                    f"[warning] Catálogo não encontrado para '{key}': "
                    "fragmentação desativada."
                )
                continue

            values = load_catalog_values(key, catalog_directory)

        fragment_dimensions[key] = values

    if not fragment_dimensions:
        return [
            {
                "id": "total",
                "filters": fixed_filters,
            }
        ]

    dimension_keys = list(fragment_dimensions.keys())
    dimension_values = [fragment_dimensions[k] for k in dimension_keys]

    combination_count = 1
    for values in dimension_values:
        combination_count *= len(values)

    if max_arquivos is not None and combination_count > max_arquivos:
        raise ValueError(
            f"O número de combinações calculadas ({combination_count}) "
            f"excede o limite configurado em 'max_arquivos' ({max_arquivos}). "
            "Reduza o número de categorias fragmentadas ou aumente o limite."
        )

    combinations = list(itertools.product(*dimension_values))

    fragments = []

    for combo in combinations:
        filters = dict(fixed_filters)

        for key, value in zip(dimension_keys, combo):
            filters[key] = value

        fragment_id_parts = []

        for key, value in zip(dimension_keys, combo):
            fragment_id_parts.append(f"{key}_{value}")

        fragment_id = "__".join(fragment_id_parts)

        fragments.append(
            {
                "id": fragment_id,
                "filters": filters,
            }
        )

    return fragments


def validate_max_arquivos(
    fragments: list[dict[str, Any]],
    max_arquivos: int,
) -> None:
    num_combinations = len(fragments)

    if num_combinations > max_arquivos:
        raise ValueError(
            f"O número de combinações calculadas ({num_combinations}) "
            f"excede o limite configurado em 'max_arquivos' ({max_arquivos}). "
            "Reduza o número de categorias fragmentadas ou aumente o limite."
        )


def download_ftp_file(
    host: str,
    remote_directory: str,
    remote_file_name: str,
    local_file_path: Path,
) -> None:
    temporary_file_path = local_file_path.with_suffix(
        f"{local_file_path.suffix}.part"
    )

    if temporary_file_path.exists():
        temporary_file_path.unlink()

    try:
        with FTP(host, timeout=300) as ftp:
            ftp.login()
            ftp.cwd(remote_directory)

            with temporary_file_path.open("wb") as local_file:
                ftp.retrbinary(
                    f"RETR {remote_file_name}",
                    local_file.write,
                    blocksize=1024 * 1024,
                )

        temporary_file_path.replace(local_file_path)

    except Exception as exc:
        if temporary_file_path.exists():
            temporary_file_path.unlink()

        exception_trackers(exc)
        raise


def download_caged_archive(
    competencia: str,
    raw_directory: Path,
) -> Path:
    ano = competencia[:4]
    archive_name = f"CAGEDMOV{competencia}.7z"

    local_directory = raw_directory / competencia
    local_directory.mkdir(parents=True, exist_ok=True)

    local_archive_path = local_directory / archive_name

    if local_archive_path.exists() and local_archive_path.stat().st_size > 0:
        print(f"[download] Arquivo já disponível: {local_archive_path.name}")
        return local_archive_path

    remote_directory = f"{FTP_BASE_DIRECTORY}/{ano}/{competencia}"

    print(f"[download] Baixando competência {competencia}...")
    download_ftp_file(
        host=FTP_HOST,
        remote_directory=remote_directory,
        remote_file_name=archive_name,
        local_file_path=local_archive_path,
    )

    print(f"[download] Concluído: {local_archive_path}")
    return local_archive_path


def extract_archive(
    archive_path: Path,
    extracted_directory: Path,
    competencia: str,
) -> Path:
    target_directory = extracted_directory / competencia
    target_directory.mkdir(parents=True, exist_ok=True)

    txt_files = list(target_directory.glob("*.txt"))

    if txt_files:
        print(f"[extract] TXT já disponível: {txt_files[0].name}")
        return txt_files[0]

    print(f"[extract] Descompactando: {archive_path.name}")

    with py7zr.SevenZipFile(archive_path, mode="r") as archive:
        archive.extractall(path=target_directory)

    txt_files = list(target_directory.rglob("*.txt"))

    if not txt_files:
        raise FileNotFoundError(
            f"Nenhum TXT foi encontrado após extrair {archive_path.name}."
        )

    txt_file = txt_files[0]
    print(f"[extract] Concluído: {txt_file}")

    return txt_file


def get_available_columns(txt_path: Path) -> list[str]:
    sample = pd.read_csv(
        txt_path,
        sep=";",
        encoding="utf-8",
        nrows=1,
        low_memory=False,
    )

    return sample.columns.tolist()


def select_existing_columns(
    requested_columns: list[str],
    available_columns: list[str],
) -> list[str]:
    selected_columns = [
        column for column in requested_columns if column in available_columns
    ]

    missing_columns = sorted(set(requested_columns) - set(selected_columns))

    if missing_columns:
        print(
            "[warning] Colunas não encontradas no arquivo e ignoradas: "
            f"{missing_columns}"
        )

    if not selected_columns:
        raise ValueError(
            "Nenhuma coluna solicitada foi encontrada no TXT."
        )

    return selected_columns


def apply_filters(
    dataframe: pd.DataFrame,
    fragment_filters: dict[str, Any],
) -> pd.DataFrame:
    if not fragment_filters:
        return dataframe

    filtered_dataframe = dataframe

    for column_name, accepted_value in fragment_filters.items():
        if column_name not in filtered_dataframe.columns:
            raise KeyError(
                f"A coluna '{column_name}' não existe no arquivo, "
                "mas foi solicitada como filtro."
            )

        values = accepted_value if isinstance(accepted_value, list) else [accepted_value]
        filtered_dataframe = filtered_dataframe[
            filtered_dataframe[column_name].astype("string").isin(
                str(value) for value in values
            )
        ]

    return filtered_dataframe


def aggregate_time_series(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(columns=["competencia", "admissoes", "desligamentos", "saldo"])

    if "saldomovimentação" not in dataframe.columns:
        raise KeyError(
            "A coluna 'saldomovimentação' é obrigatória para agregar a série temporal."
        )

    admissoes = (dataframe["saldomovimentação"] == "1").sum()
    desligamentos = (dataframe["saldomovimentação"] == "-1").sum()
    saldo = admissoes - desligamentos

    resultado = pd.DataFrame(
        {
            "admissoes": [admissoes],
            "desligamentos": [desligamentos],
            "saldo": [saldo],
        }
    )
    if COMPETENCIA_COLUMN in dataframe.columns:
        resultado.insert(0, "competencia", dataframe[COMPETENCIA_COLUMN].iloc[0])

    return resultado


def process_caged_competencia(
    competencia: str,
    paths: dict[str, Path],
    fragmentos: list[dict],
    categorias: dict[str, Any],
    formato_saida: str = "parquet",
    chunksize: int = 500_000,
    manter_txt_extraido: bool = True,
    sobrescrever_processado: bool = False,
) -> list[Path]:
    """
    Baixa e extrai o arquivo de uma competência e processa os dados
    para cada fragmento definido em etl_filter.json.

    Retorna a lista de caminhos dos arquivos processados.
    """
    archive_path = download_caged_archive(
        competencia=competencia,
        raw_directory=paths["raw_caged"],
    )

    txt_path = extract_archive(
        archive_path=archive_path,
        extracted_directory=paths["extracted_caged"],
        competencia=competencia,
    )

    output_directory = paths["processed_caged"] / competencia
    output_directory.mkdir(parents=True, exist_ok=True)

    output_paths = []

    for fragmento in fragmentos:
        fragmento_id = fragmento["id"]
        filtros = fragmento["filters"]

        output_path = output_directory / f"caged_mov_{competencia}_{fragmento_id}.{formato_saida}"

        if output_path.exists() and not sobrescrever_processado:
            print(f"[process] Arquivo já disponível: {output_path.name}")
            output_paths.append(output_path)
            continue

        colunas_necessarias = [COMPETENCIA_COLUMN, "saldomovimentação"] + list(filtros.keys())

        partes = []

        for chunk in pd.read_csv(
            txt_path,
            sep=";",
            encoding="utf-8",
            usecols=colunas_necessarias,
            dtype="string",
            chunksize=chunksize,
            low_memory=False,
        ):
            chunk_filtrado = apply_filters(chunk, filtros)

            if chunk_filtrado.empty:
                continue

            agregado = (
                chunk_filtrado.groupby(COMPETENCIA_COLUMN, as_index=False)["saldomovimentação"]
                .agg(
                    admissoes=lambda s: (s == "1").sum(),
                    desligamentos=lambda s: (s == "-1").sum(),
                )
            )

            agregado["saldo"] = agregado["admissoes"] - agregado["desligamentos"]
            agregado = agregado.rename(columns={COMPETENCIA_COLUMN: "competencia"})

            partes.append(agregado)

        if not partes:
            resultado = pd.DataFrame(columns=["competencia", "admissoes", "desligamentos", "saldo"])
        else:
            resultado = pd.concat(partes, ignore_index=True)
            resultado = (
                resultado.groupby("competencia", as_index=False)[
                    ["admissoes", "desligamentos"]
                ]
                .sum()
            )
            resultado["saldo"] = (
                resultado["admissoes"] - resultado["desligamentos"]
            )
            resultado = resultado.sort_values("competencia").reset_index(drop=True)

        if formato_saida == "parquet":
            resultado.to_parquet(output_path, index=False)
        else:
            resultado.to_csv(output_path, sep=";", encoding="utf-8", index=False)

        print(
            f"[process] Concluído: {len(resultado):,} registros "
            f"gravados em {output_path}"
        )

        output_paths.append(output_path)

    if not manter_txt_extraido:
        txt_path.unlink(missing_ok=True)
        print(f"[cleanup] TXT removido: {txt_path.name}")

    return output_paths


def merge_time_series(
    paths: dict[str, Path],
    fragments: list[dict[str, Any]],
    competencias: list[str],
    output_format: str,
) -> dict[str, Path]:
    final_paths = {}

    for fragment in fragments:
        fragment_id = fragment["id"]

        dataframes = []

        for competencia in competencias:
            output_directory = paths["processed_caged"] / competencia
            output_filename = f"caged_mov_{competencia}_{fragment_id}.{output_format}"
            output_path = output_directory / output_filename

            if output_path.exists():
                if output_format == "parquet":
                    df = pd.read_parquet(output_path)
                else:
                    df = pd.read_csv(output_path, sep=";", encoding="utf-8")

                dataframes.append(df)

        if dataframes:
            merged_dataframe = pd.concat(dataframes, ignore_index=True)
            merged_dataframe = merged_dataframe.sort_values("competencia").reset_index(
                drop=True
            )

            merged_output_path = paths["ready_caged"] / f"caged_mov_{fragment_id}.{output_format}"
            merged_output_path.parent.mkdir(parents=True, exist_ok=True)

            if output_format == "parquet":
                merged_dataframe.to_parquet(merged_output_path, index=False)
            else:
                merged_dataframe.to_csv(
                    merged_output_path,
                    sep=";",
                    encoding="utf-8",
                    index=False,
                )

            print(
                f"[merge] Série temporal consolidada para {fragment_id}: "
                f"{len(merged_dataframe):,} meses em {merged_output_path}"
            )

            final_paths[fragment_id] = merged_output_path

    return final_paths


# def main() -> None:
#     paths, etl_filters = load_settings()
#     create_directories(paths)

#     # competencias_config = etl_filters.get("competencias", {})

#     competencias = etl_filters.get("_competencias_resolvidas", [])

#     if not competencias:
#         raise ValueError(
#             "Nenhuma competência foi resolvida. Verifique a configuração em 'tempo'."
#         )

#     categorias_config = etl_filters.get("categorias", {})

#     if not categorias_config:
#         raise ValueError(
#             "O campo 'categorias' é obrigatório no arquivo de configuração."
#         )

#     competencias = resolve_competencias(competencias_config)

#     print(f"[config] Competências a processar: {competencias}")

#     fragments = build_fragments(categorias_config)

#     print(f"[config] Fragmentos calculados: {len(fragments)}")

#     for fragment in fragments:
#         print(f"  - {fragment['id']}: {fragment['filters']}")

#     max_arquivos = etl_filters.get("max_arquivos", 20)

#     validate_max_arquivos(fragments, max_arquivos)

#     output_format = etl_filters.get("formato_saida", "parquet")
#     chunksize = int(etl_filters.get("chunksize", 500_000))
#     overwrite = etl_filters.get("sobrescrever_processado", False)
#     manter_txt = etl_filters.get("manter_txt_extraido", True)

#     if output_format not in {"parquet", "csv"}:
#         raise ValueError(
#             "O campo 'formato_saida' deve ser 'parquet' ou 'csv'."
#         )

#     all_output_paths = {}

#     for competencia in competencias:
#         competencia = normalize_competencia(competencia)

#         output_paths = process_caged_competencia(
#             competencia=competencia,
#             paths=paths,
#             fragments=fragments,
#             output_format=output_format,
#             chunksize=chunksize,
#             overwrite=overwrite,
#             manter_txt=manter_txt,
#         )

#         all_output_paths[competencia] = output_paths

#     merged_paths = merge_time_series(
#         paths=paths,
#         fragments=fragments,
#         competencias=competencias,
#         output_format=output_format,
#     )

#     print("[done] Processamento concluído.")
#     print("[done] Séries temporais consolidadas:")

#     for fragment_id, output_path in merged_paths.items():
#         print(f"  - {fragment_id}: {output_path}")


def main() -> None:
    # Carregar configuração geral (paths + etl_filter)
    paths_config = load_json(PATHS_CONFIG_FILE)

    # Resolver caminhos usados
    raw_caged = resolve_project_path(paths_config["data"]["raw_caged"])
    extracted_caged = resolve_project_path(paths_config["data"]["extracted_caged"])
    processed_caged = resolve_project_path(paths_config["data"]["processed_caged"])
    ready_caged = resolve_project_path(paths_config["data"]["ready_caged"])
    etl_filter_path = resolve_project_path(paths_config["config"]["etl_filter"])

    paths = {
        "raw_caged": raw_caged,
        "extracted_caged": extracted_caged,
        "processed_caged": processed_caged,
        "ready_caged": ready_caged,
        "etl_filter": etl_filter_path,
    }

    # Carregar filtros e parâmetros de processamento
    config = load_json(paths["etl_filter"])

    competencias = resolve_competencias(config)

    # === Resolver categorias e fragmentos ===
    categorias = config.get("categorias", {})
    max_arquivos = config.get("max_arquivos", 20)
    catalog_directory = resolve_project_path(
        paths_config["data"]["catalog_caged"]
    )

    fragmentos = build_fragments(
        categorias,
        catalog_directory=catalog_directory,
        max_arquivos=max_arquivos,
    )

    if len(fragmentos) > max_arquivos:
        raise RuntimeError(
            f"Número de combinações ({len(fragmentos)}) excede o limite "
            f"configurado (max_arquivos={max_arquivos}). Ajuste os filtros "
            "ou aumente o limite em etl_filter.json."
        )

    # === Criar diretórios ===
    create_directories(paths)

    # === Parâmetros de processamento ===
    formato_saida = config.get("formato_saida", "parquet")
    if formato_saida not in {"parquet", "csv"}:
        raise ValueError("O campo 'formato_saida' deve ser 'parquet' ou 'csv'.")

    chunksize = config.get("chunksize", 500_000)
    manter_txt_extraido = config.get("manter_txt_extraido", True)
    sobrescrever_processado = config.get("sobrescrever_processado", False)

    # === Processar cada competência ===
    for competencia in competencias:
        try:
            output_paths = process_caged_competencia(
                competencia=competencia,
                paths=paths,
                fragmentos=fragmentos,
                categorias=categorias,
                formato_saida=formato_saida,
                chunksize=chunksize,
                manter_txt_extraido=manter_txt_extraido,
                sobrescrever_processado=sobrescrever_processado,
            )

            for path in output_paths:
                print(f"[done] Resultado disponível em: {path}")

        except CagedFileNotFoundError as exc:
            print(f"[skip] Competência {competencia} indisponível: {exc}")
            continue

    merged_paths = merge_time_series(
        paths=paths,
        fragments=fragmentos,
        competencias=competencias,
        output_format=formato_saida,
    )

    for fragment_id, output_path in merged_paths.items():
        print(f"[done] Série temporal consolidada ({fragment_id}): {output_path}")


if __name__ == "__main__":
    main()
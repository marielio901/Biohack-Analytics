from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

import pandas as pd


VIEW_FREQUENCIES = {
    "Dia": "D",
    "Semana": "W-MON",
    "Mês": "M",
}

GOAL_STATUS_ORDER = ["Programado", "Iniciado", "Em Andamento", "Concluído"]
SLEEP_TARGET_CHANGE_DATE = date(2026, 3, 1)
SLEEP_TARGET_FEBRUARY_HOURS = 8.0
SLEEP_TARGET_CURRENT_HOURS = 6.0
SLEEP_TARGET_TOLERANCE_MINUTES = 15


def ensure_datetime(df: pd.DataFrame, date_col: str = "data") -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df.copy()
    prepared = df.copy()
    prepared[date_col] = pd.to_datetime(prepared[date_col], errors="coerce")
    prepared = prepared.dropna(subset=[date_col])
    return prepared


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: date | None = None,
    end_date: date | None = None,
    date_col: str = "data",
) -> pd.DataFrame:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty:
        return prepared

    if start_date:
        prepared = prepared[prepared[date_col].dt.date >= start_date]
    if end_date:
        prepared = prepared[prepared[date_col].dt.date <= end_date]
    return prepared.sort_values(date_col).reset_index(drop=True)


def get_global_date_bounds(datasets: dict[str, pd.DataFrame]) -> tuple[date, date]:
    dates: list[pd.Timestamp] = []
    mapping = {
        "dados_corporais": "data",
        "registros_cardiacos": "data",
        "atividades_fisicas": "data",
        "alimentacao": "data",
        "registros_sono": "data",
        "metas": "data_inicio",
        "metas_finalizadas": "data_finalizacao",
    }

    for key, column in mapping.items():
        df = ensure_datetime(datasets.get(key, pd.DataFrame()), column)
        if not df.empty:
            dates.extend(df[column].tolist())

    if not dates:
        today = date.today()
        return today - timedelta(days=30), today

    minimum = min(dates).date()
    maximum = max(dates).date()
    return minimum, maximum


def latest_record(df: pd.DataFrame, date_col: str = "data") -> pd.Series | None:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty:
        return None
    return prepared.sort_values(date_col).iloc[-1]


def latest_value_with_delta(
    df: pd.DataFrame,
    value_col: str,
    date_col: str = "data",
) -> tuple[float | None, float | None]:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty or value_col not in prepared.columns:
        return None, None
    prepared = prepared.sort_values(date_col)
    latest_value = float(prepared.iloc[-1][value_col])
    previous_value = (
        float(prepared.iloc[-2][value_col]) if len(prepared) > 1 else None
    )
    delta = latest_value - previous_value if previous_value is not None else None
    return latest_value, delta


def compare_recent_windows(
    df: pd.DataFrame,
    value_col: str,
    date_col: str = "data",
    window_days: int = 7,
    agg: str = "sum",
) -> tuple[float | None, float | None]:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty or value_col not in prepared.columns:
        return None, None

    prepared = prepared.sort_values(date_col)
    end_date = prepared[date_col].max().date()
    recent_start = end_date - timedelta(days=window_days - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)

    recent = prepared[prepared[date_col].dt.date >= recent_start]
    recent = recent[recent[date_col].dt.date <= end_date]

    previous = prepared[prepared[date_col].dt.date >= previous_start]
    previous = previous[previous[date_col].dt.date <= previous_end]

    if agg == "mean":
        recent_value = float(recent[value_col].mean()) if not recent.empty else None
        previous_value = (
            float(previous[value_col].mean()) if not previous.empty else None
        )
    else:
        recent_value = float(recent[value_col].sum()) if not recent.empty else None
        previous_value = (
            float(previous[value_col].sum()) if not previous.empty else None
        )
    return recent_value, previous_value


def aggregate_timeseries(
    df: pd.DataFrame,
    value_col: str,
    date_col: str = "data",
    view_mode: str = "Dia",
    agg: str = "sum",
) -> pd.DataFrame:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty:
        return pd.DataFrame(columns=[date_col, "periodo", "valor"])

    working = prepared.copy()
    target_col = value_col
    if value_col == "__count__":
        target_col = "_count"
        working[target_col] = 1

    grouped = (
        working.groupby(pd.Grouper(key=date_col, freq=VIEW_FREQUENCIES[view_mode]))[
            target_col
        ]
        .agg(agg)
        .reset_index()
        .rename(columns={target_col: "valor"})
    )
    grouped["periodo"] = format_period_labels(grouped[date_col], view_mode)
    return grouped


def aggregate_multi_series(
    df: pd.DataFrame,
    value_cols: Iterable[str],
    date_col: str = "data",
    view_mode: str = "Dia",
    agg: str = "sum",
) -> pd.DataFrame:
    prepared = ensure_datetime(df, date_col)
    if prepared.empty:
        return pd.DataFrame(columns=[date_col, "periodo", *list(value_cols)])

    grouped = (
        prepared.groupby(pd.Grouper(key=date_col, freq=VIEW_FREQUENCIES[view_mode]))[
            list(value_cols)
        ]
        .agg(agg)
        .reset_index()
    )
    grouped["periodo"] = format_period_labels(grouped[date_col], view_mode)
    return grouped


def format_period_labels(series: pd.Series, view_mode: str) -> pd.Series:
    if view_mode == "Mês":
        return series.dt.strftime("%m/%Y")
    return series.dt.strftime("%d/%m/%Y")


def format_display_date(
    value: object,
    fmt: str = "%Y-%m-%d",
    fallback: str = "Sem data",
) -> str:
    if value is None or pd.isna(value):
        return fallback
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return fallback
    return parsed.strftime(fmt)


def _time_to_decimal(value: str) -> float:
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour + parsed.minute / 60


def prepare_sleep_analysis_df(sleep_df: pd.DataFrame) -> pd.DataFrame:
    prepared = ensure_datetime(sleep_df, "data")
    if prepared.empty:
        return prepared

    working = prepared.copy()
    working["duracao_horas"] = pd.to_numeric(working["duracao_horas"], errors="coerce")
    working["hora_dormir_decimal"] = working["hora_dormir"].map(_time_to_decimal)
    working["hora_acordar_decimal"] = working["hora_acordar"].map(_time_to_decimal)
    working["hora_dormir_plot"] = working["hora_dormir_decimal"].apply(
        lambda value: value if value >= 12 else value + 24
    )
    working["hora_acordar_plot"] = working["hora_acordar_decimal"].apply(
        lambda value: value + 24 if value < 12 else value
    )
    return working.dropna(
        subset=[
            "duracao_horas",
            "hora_dormir_decimal",
            "hora_acordar_decimal",
            "hora_dormir_plot",
            "hora_acordar_plot",
        ]
    )


def get_sleep_target_hours(target_date: date) -> float:
    if target_date < SLEEP_TARGET_CHANGE_DATE:
        return SLEEP_TARGET_FEBRUARY_HOURS
    return SLEEP_TARGET_CURRENT_HOURS


def summarize_goal_statuses(
    active_goals: pd.DataFrame,
    archived_goals: pd.DataFrame,
) -> pd.DataFrame:
    counts = {status: 0 for status in GOAL_STATUS_ORDER}

    if not active_goals.empty and "status" in active_goals.columns:
        for status, total in active_goals["status"].value_counts().items():
            counts[status] = counts.get(status, 0) + int(total)

    if not archived_goals.empty:
        counts["Concluído"] += len(archived_goals)

    return pd.DataFrame(
        {"status": list(counts.keys()), "total": list(counts.values())}
    )


def prepare_goal_table(
    active_goals: pd.DataFrame,
    archived_goals: pd.DataFrame,
) -> pd.DataFrame:
    active = active_goals.copy()
    archived = archived_goals.copy()

    if not active.empty:
        active["situacao_final"] = "Em aberto"

    if not archived.empty:
        if "meta_origem_id" in archived.columns:
            archived["id"] = archived["meta_origem_id"]
            archived = archived.rename(columns={"meta_origem_id": "id_origem"})
        elif "id" not in archived.columns:
            archived["id"] = range(1, len(archived) + 1)

    columns = [
        "id",
        "titulo",
        "descricao",
        "categoria",
        "data_criacao",
        "prazo",
        "status",
        "progresso",
        "situacao_final",
    ]
    frames = []
    if not active.empty:
        frames.append(active[columns])
    if not archived.empty:
        frames.append(archived[columns])
    if not frames:
        return pd.DataFrame(columns=columns)
    combined = pd.concat(frames, ignore_index=True)
    for column in ("data_criacao", "prazo", "data_inicio"):
        if column in combined.columns:
            combined[column] = pd.to_datetime(combined[column], errors="coerce")
    return combined.sort_values("data_criacao", ascending=False).reset_index(drop=True)


def prepare_goal_pace_table(
    active_goals: pd.DataFrame,
    reference_date: date | None = None,
) -> pd.DataFrame:
    if active_goals.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "titulo",
                "status",
                "progresso",
                "progresso_esperado",
                "desvio_ritmo",
                "dias_restantes",
                "tendencia",
                "prazo_label",
            ]
        )

    reference_ts = pd.Timestamp(reference_date or date.today()).normalize()
    working = active_goals.copy()
    working["data_inicio"] = pd.to_datetime(working["data_inicio"], errors="coerce")
    working["prazo"] = pd.to_datetime(working["prazo"], errors="coerce")
    working["progresso"] = pd.to_numeric(working["progresso"], errors="coerce")
    working = working.dropna(subset=["data_inicio", "prazo", "progresso"])
    if working.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "titulo",
                "status",
                "progresso",
                "progresso_esperado",
                "desvio_ritmo",
                "dias_restantes",
                "tendencia",
                "prazo_label",
            ]
        )

    total_days = (
        (working["prazo"].dt.normalize() - working["data_inicio"].dt.normalize())
        .dt.days.clip(lower=1)
    )
    elapsed_days = (
        (reference_ts - working["data_inicio"].dt.normalize())
        .dt.days.clip(lower=0)
        .clip(upper=total_days)
    )

    working["progresso"] = working["progresso"].clip(lower=0, upper=100)
    working["progresso_esperado"] = (elapsed_days / total_days * 100).round(1)
    working["desvio_ritmo"] = (
        working["progresso"] - working["progresso_esperado"]
    ).round(1)
    working["dias_restantes"] = (
        working["prazo"].dt.normalize() - reference_ts
    ).dt.days.astype(int)
    working["tendencia"] = working.apply(
        lambda row: (
            "Concluída"
            if row["status"] == "Concluído" or row["progresso"] >= 100
            else "Adiantada"
            if row["desvio_ritmo"] >= 10
            else "No ritmo"
            if row["desvio_ritmo"] >= -10
            else "Em risco"
        ),
        axis=1,
    )
    working["prazo_label"] = working["prazo"].dt.strftime("%d/%m/%Y")
    return working.sort_values(
        ["dias_restantes", "desvio_ritmo"],
        ascending=[True, False],
    ).reset_index(drop=True)


def build_consolidated_history(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    body = datasets.get("dados_corporais", pd.DataFrame()).copy()
    if not body.empty:
        body["tipo"] = "Dados Corporais"
        body["referencia"] = body["data"]
        body["descricao"] = body.apply(
            lambda row: (
                f"Peso {row['peso']:.1f} kg | Altura {row['altura']:.2f} m | "
                f"IMC {row['imc']:.2f}"
            ),
            axis=1,
        )
        frames.append(body[["tipo", "referencia", "descricao", "id"]])

    heart = datasets.get("registros_cardiacos", pd.DataFrame()).copy()
    if not heart.empty:
        heart["tipo"] = "Cardíaco"
        heart["referencia"] = heart["data"]
        heart["descricao"] = heart.apply(
            lambda row: (
                f"Média {row['frequencia_media']} bpm | Repouso "
                f"{row['frequencia_repouso']} bpm | Máx {row['frequencia_maxima']} bpm"
            ),
            axis=1,
        )
        frames.append(heart[["tipo", "referencia", "descricao", "id"]])

    activity = datasets.get("atividades_fisicas", pd.DataFrame()).copy()
    if not activity.empty:
        activity["tipo"] = "Atividades"
        activity["referencia"] = activity["data"]
        activity["descricao"] = activity.apply(
            lambda row: (
                f"{row['tipo_atividade']} | {row['duracao_minutos']} min | "
                f"{row['calorias_gastas']:.0f} kcal"
            ),
            axis=1,
        )
        frames.append(activity[["tipo", "referencia", "descricao", "id"]])

    food = datasets.get("alimentacao", pd.DataFrame()).copy()
    if not food.empty:
        food["tipo"] = "Alimentação"
        food["referencia"] = food["data"]
        food["descricao"] = food.apply(
            lambda row: (
                f"{row['refeicao']} | {row['alimento']} | "
                f"{row['calorias']:.0f} kcal"
            ),
            axis=1,
        )
        frames.append(food[["tipo", "referencia", "descricao", "id"]])

    sleep = datasets.get("registros_sono", pd.DataFrame()).copy()
    if not sleep.empty:
        sleep["tipo"] = "Sono"
        sleep["referencia"] = sleep["data"]
        sleep["descricao"] = sleep.apply(
            lambda row: (
                f"Dormiu {row['hora_dormir']} | Acordou {row['hora_acordar']} | "
                f"{row['duracao_horas']:.1f} h"
            ),
            axis=1,
        )
        frames.append(sleep[["tipo", "referencia", "descricao", "id"]])

    goals = datasets.get("metas", pd.DataFrame()).copy()
    if not goals.empty:
        goals["tipo"] = "Metas Ativas"
        goals["referencia"] = goals["data_criacao"]
        goals["descricao"] = goals.apply(
            lambda row: (
                f"{row['titulo']} | {row['status']} | "
                f"{row['progresso']}% concluído"
            ),
            axis=1,
        )
        frames.append(goals[["tipo", "referencia", "descricao", "id"]])

    archived = datasets.get("metas_finalizadas", pd.DataFrame()).copy()
    if not archived.empty:
        archived["tipo"] = "Metas Finalizadas"
        archived["referencia"] = archived["data_finalizacao"]
        archived["descricao"] = archived.apply(
            lambda row: (
                f"{row['titulo']} | {row['situacao_final']} | "
                f"finalizada em {format_display_date(row['data_finalizacao'])}"
            ),
            axis=1,
        )
        frames.append(archived[["tipo", "referencia", "descricao", "id"]])

    if not frames:
        return pd.DataFrame(columns=["tipo", "referencia", "descricao", "id"])

    history = pd.concat(frames, ignore_index=True)
    history["referencia"] = pd.to_datetime(history["referencia"], errors="coerce")
    history = history.dropna(subset=["referencia"])
    history = history.sort_values("referencia", ascending=False).reset_index(drop=True)
    history["referencia"] = history["referencia"].dt.strftime("%Y-%m-%d")
    return history


def build_health_snapshot(
    profile: dict,
    body_df: pd.DataFrame,
    heart_df: pd.DataFrame,
    activity_df: pd.DataFrame,
    food_df: pd.DataFrame,
    sleep_df: pd.DataFrame,
    goals_df: pd.DataFrame,
    archived_goals_df: pd.DataFrame,
) -> dict[str, object]:
    today = date.today()
    last_30_days = today - timedelta(days=29)
    last_60_days = today - timedelta(days=59)

    body_all = ensure_datetime(body_df, "data")
    heart_all = ensure_datetime(heart_df, "data")
    activity_all = ensure_datetime(activity_df, "data")
    food_all = ensure_datetime(food_df, "data")
    sleep_all = prepare_sleep_analysis_df(sleep_df)
    goals_all = ensure_datetime(goals_df, "data_inicio")
    archived_all = ensure_datetime(archived_goals_df, "data_finalizacao")

    body_recent = filter_by_date_range(body_all, last_60_days, today, "data")
    heart_recent = filter_by_date_range(heart_all, last_30_days, today, "data")
    activity_recent = filter_by_date_range(activity_all, last_30_days, today, "data")
    food_recent = filter_by_date_range(food_all, last_30_days, today, "data")
    sleep_recent = filter_by_date_range(sleep_all, last_30_days, today, "data")

    weight, weight_delta = latest_value_with_delta(body_all, "peso")
    bmi, bmi_delta = latest_value_with_delta(body_all, "imc")
    body_latest = latest_record(body_all, "data")

    heart_mean = float(heart_recent["frequencia_media"].mean()) if not heart_recent.empty else None
    heart_rest = (
        float(heart_recent["frequencia_repouso"].mean())
        if not heart_recent.empty
        else None
    )
    heart_max = (
        int(heart_all["frequencia_maxima"].max())
        if not heart_all.empty
        else None
    )
    heart_min = (
        int(heart_all["frequencia_minima"].min())
        if not heart_all.empty
        else None
    )
    heart_recent_avg, heart_previous_avg = compare_recent_windows(
        heart_all,
        "frequencia_media",
        date_col="data",
        window_days=7,
        agg="mean",
    )

    sessions_30d = len(activity_recent)
    duration_30d = float(activity_recent["duracao_minutos"].sum()) if not activity_recent.empty else 0.0
    calories_burned_30d = (
        float(activity_recent["calorias_gastas"].sum()) if not activity_recent.empty else 0.0
    )
    distance_30d = float(activity_recent["distancia_km"].sum()) if not activity_recent.empty else 0.0
    consistency = "Baixa"
    if not activity_recent.empty:
        weekly_sessions = (
            activity_recent.assign(
                semana=activity_recent["data"].dt.to_period("W").astype(str)
            )
            .groupby("semana")
            .size()
        )
        active_weeks = int((weekly_sessions > 0).sum())
        if active_weeks >= 4:
            consistency = "Alta"
        elif active_weeks >= 2:
            consistency = "Moderada"

    calories_30d = float(food_recent["calorias"].sum()) if not food_recent.empty else 0.0
    proteins_30d = float(food_recent["proteinas"].sum()) if not food_recent.empty else 0.0
    carbs_30d = float(food_recent["carboidratos"].sum()) if not food_recent.empty else 0.0
    fats_30d = float(food_recent["gorduras"].sum()) if not food_recent.empty else 0.0
    daily_food = (
        food_recent.groupby(food_recent["data"].dt.date)["calorias"].sum()
        if not food_recent.empty
        else pd.Series(dtype=float)
    )
    avg_daily_calories = float(daily_food.mean()) if not daily_food.empty else None

    sleep_recent_avg, sleep_previous_avg = compare_recent_windows(
        sleep_all,
        "duracao_horas",
        date_col="data",
        window_days=7,
        agg="mean",
    )
    sleep_latest = latest_record(sleep_all, "data")
    sleep_avg_30d = float(sleep_recent["duracao_horas"].mean()) if not sleep_recent.empty else None
    avg_bedtime_30d = (
        float(sleep_recent["hora_dormir_plot"].mean()) if not sleep_recent.empty else None
    )
    avg_waketime_30d = (
        float(sleep_recent["hora_acordar_plot"].mean()) if not sleep_recent.empty else None
    )
    sleep_sessions_30d = len(sleep_recent)
    sleep_target_hit_rate = None
    sleep_nights_on_target_30d = 0
    if not sleep_recent.empty:
        target_hours = sleep_recent["data"].dt.date.map(get_sleep_target_hours)
        target_margin_minutes = (sleep_recent["duracao_horas"] - target_hours) * 60
        target_hits = target_margin_minutes >= -SLEEP_TARGET_TOLERANCE_MINUTES
        sleep_nights_on_target_30d = int(target_hits.sum())
        sleep_target_hit_rate = float(target_hits.mean() * 100)

    total_goals = len(goals_all) + len(archived_all)
    completed_goals = len(archived_all)
    completion_rate = (completed_goals / total_goals * 100) if total_goals else 0.0

    best_period = "Dados insuficientes"
    if not activity_all.empty:
        monthly = aggregate_timeseries(
            activity_all,
            "duracao_minutos",
            date_col="data",
            view_mode="Mês",
            agg="sum",
        )
        if not monthly.empty:
            best_row = monthly.sort_values("valor", ascending=False).iloc[0]
            best_period = str(best_row["periodo"])

    weight_goal = profile.get("peso_meta")
    goal_gap = None
    if weight_goal and weight is not None:
        goal_gap = float(weight - float(weight_goal))

    return {
        "weight": weight,
        "weight_delta": weight_delta,
        "bmi": bmi,
        "bmi_delta": bmi_delta,
        "latest_height": float(body_latest["altura"]) if body_latest is not None else None,
        "latest_age": int(body_latest["idade"]) if body_latest is not None else None,
        "goal_weight": float(weight_goal) if weight_goal is not None else None,
        "goal_gap": goal_gap,
        "heart_mean": heart_mean,
        "heart_rest": heart_rest,
        "heart_max": heart_max,
        "heart_min": heart_min,
        "heart_recent_avg": heart_recent_avg,
        "heart_previous_avg": heart_previous_avg,
        "sessions_30d": sessions_30d,
        "duration_30d": duration_30d,
        "calories_burned_30d": calories_burned_30d,
        "distance_30d": distance_30d,
        "activity_consistency": consistency,
        "calories_30d": calories_30d,
        "proteins_30d": proteins_30d,
        "carbs_30d": carbs_30d,
        "fats_30d": fats_30d,
        "avg_daily_calories": avg_daily_calories,
        "sleep_sessions_30d": sleep_sessions_30d,
        "sleep_avg_30d": sleep_avg_30d,
        "sleep_recent_avg": sleep_recent_avg,
        "sleep_previous_avg": sleep_previous_avg,
        "sleep_last_duration": float(sleep_latest["duracao_horas"]) if sleep_latest is not None else None,
        "sleep_last_date": sleep_latest["data"].date().isoformat() if sleep_latest is not None else None,
        "sleep_avg_bedtime_30d": avg_bedtime_30d,
        "sleep_avg_waketime_30d": avg_waketime_30d,
        "sleep_nights_on_target_30d": sleep_nights_on_target_30d,
        "sleep_target_hit_rate": sleep_target_hit_rate,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completion_rate": completion_rate,
        "best_period": best_period,
    }

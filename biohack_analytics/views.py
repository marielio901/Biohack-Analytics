from __future__ import annotations

import html
from datetime import date, time, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from biohack_analytics.analytics import (
    GOAL_STATUS_ORDER,
    aggregate_multi_series,
    aggregate_timeseries,
    build_consolidated_history,
    build_health_snapshot,
    compare_recent_windows,
    filter_by_date_range,
    format_display_date,
    get_global_date_bounds,
    latest_value_with_delta,
    prepare_goal_pace_table,
    prepare_sleep_analysis_df,
    prepare_goal_table,
    summarize_goal_statuses,
)
from biohack_analytics.axiel_audio import (
    AXIEL_TTS_VOICES,
    DEFAULT_AXIEL_VOICE,
    synthesize_axiel_audio,
)
from biohack_analytics.axiel_ai import (
    DEFAULT_SUGGESTIONS,
    generate_axiel_response,
)
from biohack_analytics.database import (
    calculate_imc,
    calculate_sleep_duration_hours,
    clear_axiel_history,
    finalize_goal,
    get_user_profile,
    insert_activity_record,
    insert_body_record,
    insert_cardiac_record,
    insert_food_record,
    insert_goal,
    insert_sleep_record,
    load_all_data,
    save_axiel_message,
    update_goal,
)


COLOR_SEQUENCE = ["#00f995", "#0bd184", "#00d7ff", "#ffd166", "#ff6b6b"]
SLEEP_TARGET_CHANGE_DATE = date(2026, 3, 1)
SLEEP_TARGET_FEBRUARY_HOURS = 8.0
SLEEP_TARGET_CURRENT_HOURS = 6.0
SLEEP_TARGET_TOLERANCE_MINUTES = 15
ACTIVITY_INTENSITIES = ["Leve", "Moderada", "Alta", "Muito Alta"]
MEAL_OPTIONS = [
    "Café da manhã",
    "Lanche da manhã",
    "Almoço",
    "Lanche da tarde",
    "Jantar",
    "Ceia",
]
GOAL_CATEGORIES = ["Peso", "Performance", "Cardíaco", "Nutrição", "Hábitos", "Bem-estar"]
SIDEBAR_MENU_OPTIONS = ["Dashboard", "Registros", "Metas", "Axiel AI"]
SIDEBAR_MENU_LABELS = {
    "Dashboard": ":material/space_dashboard: Dashboard",
    "Registros": ":material/edit_note: Registros",
    "Metas": ":material/track_changes: Metas",
    "Axiel AI": ":material/neurology: Axiel AI",
}
METRIC_CARD_ICONS = {
    "Peso atual": "monitor_weight",
    "IMC atual": "health_and_safety",
    "Meta de peso": "flag",
    "Atividades registradas": "directions_run",
    "Calorias consumidas": "restaurant",
    "Calorias totais": "restaurant",
    "Calorias gastas": "local_fire_department",
    "Evolução semanal": "timeline",
    "Tendência calórica": "show_chart",
    "Freq. média": "favorite",
    "Repouso médio": "hotel",
    "Máxima registrada": "north",
    "Mínima registrada": "south",
    "Tipo dominante": "fitness_center",
    "Tempo total": "schedule",
    "Distância total": "route",
    "Refeições cadastradas": "restaurant_menu",
    "Proteínas": "egg_alt",
    "Carboidratos": "grain",
    "Treinos em 30 dias": "calendar_month",
    "Metas concluídas": "task_alt",
    "Sono médio": "bedtime",
    "Última noite": "night_shelter",
    "Hora média de dormir": "bed",
    "Hora média de acordar": "alarm",
    "Noites na meta": "event_repeat",
    "Total de metas": "track_changes",
    "Programadas": "event_upcoming",
    "Iniciadas": "play_circle",
    "Em andamento": "pending_actions",
    "Taxa de conclusão": "checklist",
}


def render_sidebar_menu() -> str:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <span class="sidebar-brand-label">Sistema</span>
            <h1>BIOHACK ANALYTICS</h1>
            <p>Menu principal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.sidebar.radio(
        "Menu principal",
        SIDEBAR_MENU_OPTIONS,
        format_func=lambda option: SIDEBAR_MENU_LABELS[option],
        label_visibility="collapsed",
        key="main_sidebar_menu",
    )


def _render_page_title(title: str) -> None:
    st.markdown(f'<h2 class="page-title">{title}</h2>', unsafe_allow_html=True)


def _metric_columns(spec: int | list[int]) -> list[Any]:
    return st.columns(spec, gap="large")


def _format_decimal_hour(value: float | None) -> str:
    if value is None:
        return "Sem dados"
    normalized = value % 24
    hours = int(normalized)
    minutes = int(round((normalized - hours) * 60))
    if minutes == 60:
        hours = (hours + 1) % 24
        minutes = 0
    return f"{hours:02d}:{minutes:02d}"


def _get_data_revision() -> int:
    if "data_revision" not in st.session_state:
        st.session_state["data_revision"] = 0
    return int(st.session_state["data_revision"])


@st.cache_data(show_spinner=False)
def _load_cached_datasets(_revision: int) -> dict[str, pd.DataFrame]:
    return load_all_data()


@st.cache_data(show_spinner=False)
def _load_cached_profile(_revision: int) -> dict[str, Any]:
    return get_user_profile()


def _load_ui_data() -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    revision = _get_data_revision()
    return _load_cached_datasets(revision), _load_cached_profile(revision)


def _invalidate_data_cache() -> None:
    st.session_state["data_revision"] = _get_data_revision() + 1
    _load_cached_datasets.clear()
    _load_cached_profile.clear()


def _render_section_switcher(label: str, options: list[str], key: str) -> str:
    default_value = st.session_state.get(key, options[0])
    if default_value not in options:
        default_value = options[0]
    return st.segmented_control(
        label,
        options,
        default=default_value,
        key=key,
        label_visibility="collapsed",
    )


def _get_sleep_target_hours(value: pd.Timestamp) -> float:
    if value.date() < SLEEP_TARGET_CHANGE_DATE:
        return SLEEP_TARGET_FEBRUARY_HOURS
    return SLEEP_TARGET_CURRENT_HOURS


def _get_sleep_target_caption(sleep: pd.DataFrame) -> str:
    start_date = sleep["data"].min().date()
    end_date = sleep["data"].max().date()
    if end_date < SLEEP_TARGET_CHANGE_DATE:
        return "Meta aplicada neste recorte: pelo menos 8h por noite."
    if start_date >= SLEEP_TARGET_CHANGE_DATE:
        return "Meta aplicada neste recorte: pelo menos 6h por noite."
    return "Meta aplicada: fevereiro com pelo menos 8h; março em diante com pelo menos 6h."


def _format_duration_hours(value: float | None) -> str:
    if value is None:
        return "Sem dados"
    total_minutes = int(round(value * 60))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h{minutes:02d}"


def _format_duration_delta(value: float | None) -> str | None:
    if value is None:
        return None
    total_minutes = int(round(value * 60))
    sign = "+" if total_minutes > 0 else ""
    return f"{sign}{total_minutes} min"


def _sleep_tick_values(start: int = 22, end: int = 33) -> tuple[list[int], list[str]]:
    tickvals = list(range(start, end + 1))
    ticktext = [f"{value % 24:02d}:00" for value in tickvals]
    return tickvals, ticktext


def _bmi_status(bmi: float | None) -> tuple[str | None, str, str | None]:
    if bmi is None:
        return None, "muted", None
    if bmi < 18.5:
        return "Ruim", "warning", "Abaixo do peso"
    if bmi < 25:
        return "Bom", "good", "Faixa saudável"
    if bmi < 30:
        return "Ruim", "warning", "Sobrepeso"
    if bmi < 35:
        return "Ruim", "danger", "Obesidade I"
    if bmi < 40:
        return "Ruim", "danger", "Obesidade II"
    return "Ruim", "danger", "Obesidade III"


def _metric_delta_class(delta: str | None, delta_color: str) -> str:
    if not delta:
        return "metric-card-meta-text"
    if delta_color == "off":
        return "metric-card-meta-text"
    if delta.startswith("+"):
        return "metric-card-delta-positive" if delta_color == "normal" else "metric-card-delta-negative"
    if delta.startswith("-"):
        return "metric-card-delta-negative" if delta_color == "normal" else "metric-card-delta-positive"
    return "metric-card-meta-text"


def _render_metric_card(
    container: Any,
    label: str,
    value: str,
    delta: str | None = None,
    *,
    icon: str | None = None,
    delta_color: str = "normal",
    badge: str | None = None,
    badge_tone: str = "muted",
    supporting_text: str | None = None,
) -> None:
    card_icon = icon or METRIC_CARD_ICONS.get(label, "insights")
    meta_parts: list[str] = []
    if badge:
        meta_parts.append(
            f'<span class="metric-card-badge metric-card-badge--{badge_tone}">{html.escape(badge)}</span>'
        )
    if supporting_text:
        meta_parts.append(
            f'<span class="metric-card-meta-text">{html.escape(supporting_text)}</span>'
        )
    if delta:
        meta_parts.append(
            f'<span class="{_metric_delta_class(delta, delta_color)}">{html.escape(delta)}</span>'
        )
    meta_html = ""
    if meta_parts:
        meta_html = '<div class="metric-card-meta">' + "".join(meta_parts) + "</div>"

    container.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-head">
                <span class="metric-card-label">{html.escape(label)}</span>
                <span class="material-symbols-rounded metric-card-icon">{html.escape(card_icon)}</span>
            </div>
            <div class="metric-card-value">{html.escape(value)}</div>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _reset_axiel_audio_player() -> None:
    st.session_state.pop("axiel_audio_target", None)
    st.session_state.pop("axiel_audio_autoplay", None)


def _render_axiel_audio_toolbar() -> None:
    if st.session_state.get("axiel_tts_voice") not in AXIEL_TTS_VOICES:
        st.session_state["axiel_tts_voice"] = DEFAULT_AXIEL_VOICE

    audio_col, hint_col = st.columns([1.2, 1.8])
    audio_col.selectbox(
        "Voz masculina da Axiel",
        list(AXIEL_TTS_VOICES.keys()),
        index=list(AXIEL_TTS_VOICES.keys()).index(
            st.session_state.get("axiel_tts_voice", DEFAULT_AXIEL_VOICE)
        ),
        key="axiel_tts_voice",
        on_change=_reset_axiel_audio_player,
    )
    hint_col.caption("Clique em `Ouvir` em qualquer resposta da Axiel para gerar o audio.")


def render_dashboard_page() -> None:
    datasets, profile = _load_ui_data()
    snapshot = build_health_snapshot(
        profile,
        datasets["dados_corporais"],
        datasets["registros_cardiacos"],
        datasets["atividades_fisicas"],
        datasets["alimentacao"],
        datasets["registros_sono"],
        datasets["metas"],
        datasets["metas_finalizadas"],
    )

    start_bound, end_bound = get_global_date_bounds(datasets)
    selected_range, view_mode, start_date, end_date = _render_date_controls(
        start_bound,
        end_bound,
        key_prefix="dashboard",
        use_sidebar=True,
    )

    filtered = {
        "dados_corporais": filter_by_date_range(
            datasets["dados_corporais"], start_date, end_date, "data"
        ),
        "registros_cardiacos": filter_by_date_range(
            datasets["registros_cardiacos"], start_date, end_date, "data"
        ),
        "atividades_fisicas": filter_by_date_range(
            datasets["atividades_fisicas"], start_date, end_date, "data"
        ),
        "alimentacao": filter_by_date_range(
            datasets["alimentacao"], start_date, end_date, "data"
        ),
        "registros_sono": filter_by_date_range(
            datasets["registros_sono"], start_date, end_date, "data"
        ),
        "metas": filter_by_date_range(
            datasets["metas"], start_date, end_date, "data_inicio"
        ),
        "metas_finalizadas": filter_by_date_range(
            datasets["metas_finalizadas"], start_date, end_date, "data_finalizacao"
        ),
    }

    _render_page_title("Centro analítico")

    hint = (
        f"Período aplicado: {selected_range.lower()} entre {start_date.isoformat()} e "
        f"{end_date.isoformat()}."
    )
    st.caption(hint)

    section = _render_section_switcher(
        "Seção do dashboard",
        [
            "Geral",
            "Controle do Sono",
            "Cardíaco",
            "Atividades Físicas",
            "Alimentação",
            "Controle de Metas",
        ],
        key="dashboard_section",
    )
    if section == "Geral":
        _render_general_dashboard(filtered, profile, snapshot, view_mode)
    elif section == "Controle do Sono":
        _render_sleep_dashboard(filtered, view_mode)
    elif section == "Cardíaco":
        _render_cardiac_dashboard(filtered, view_mode)
    elif section == "Atividades Físicas":
        _render_activity_dashboard(filtered, view_mode)
    elif section == "Alimentação":
        _render_food_dashboard(filtered, view_mode)
    else:
        _render_goals_dashboard(filtered, view_mode, end_date)


def render_records_page() -> None:
    datasets, _ = _load_ui_data()

    _render_page_title("Entrada de dados estruturada")

    section = _render_section_switcher(
        "Seção de registros",
        ["Dados Corporais", "Cardíaco", "Atividades", "Alimentação", "Sono", "Histórico"],
        key="records_section",
    )
    if section == "Dados Corporais":
        _render_body_register(datasets["dados_corporais"])
    elif section == "Cardíaco":
        _render_cardiac_register(datasets["registros_cardiacos"])
    elif section == "Atividades":
        _render_activity_register(datasets["atividades_fisicas"])
    elif section == "Alimentação":
        _render_food_register(datasets["alimentacao"])
    elif section == "Sono":
        _render_sleep_register(datasets["registros_sono"])
    else:
        _render_history_tab(datasets)


def render_goals_page() -> None:
    datasets, _ = _load_ui_data()

    _render_page_title("Gestão visual de objetivos")

    section = _render_section_switcher(
        "Seção de metas",
        ["Kanban", "Tabela", "Registrar Meta"],
        key="goals_section",
    )

    if section == "Kanban":
        _render_kanban(datasets["metas"])
    elif section == "Tabela":
        _render_goals_table(datasets["metas"], datasets["metas_finalizadas"])
    else:
        _render_goal_form()


def render_axiel_page() -> None:
    datasets, profile = _load_ui_data()
    snapshot = build_health_snapshot(
        profile,
        datasets["dados_corporais"],
        datasets["registros_cardiacos"],
        datasets["atividades_fisicas"],
        datasets["alimentacao"],
        datasets["registros_sono"],
        datasets["metas"],
        datasets["metas_finalizadas"],
    )

    _render_page_title("Assistente de acompanhamento inteligente")

    insight_cols = _metric_columns(3)
    _render_metric_card(
        insight_cols[0],
        "Peso atual",
        _fmt_metric(snapshot["weight"], "kg"),
    )
    _render_metric_card(
        insight_cols[1],
        "Treinos em 30 dias",
        str(snapshot["sessions_30d"]),
    )
    _render_metric_card(
        insight_cols[2],
        "Metas concluídas",
        f"{snapshot['completed_goals']}/{snapshot['total_goals']}",
    )
    _render_axiel_audio_toolbar()

    with st.expander("Perguntas sugeridas", expanded=False):
        for suggestion in DEFAULT_SUGGESTIONS:
            if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                _process_axiel_message(suggestion)

    history = datasets["historico_axiel"]
    if history.empty:
        st.info(
            "O histórico do chat ainda está vazio. Faça uma pergunta para iniciar a análise."
        )
    else:
        for _, row in history.iterrows():
            with st.chat_message("assistant" if row["role"] == "assistant" else "user"):
                st.markdown(row["mensagem"])
                if row["role"] == "assistant":
                    if st.button("Ouvir", key=f"axiel_listen_{int(row['id'])}"):
                        st.session_state["axiel_audio_target"] = int(row["id"])
                        st.session_state["axiel_audio_autoplay"] = int(row["id"])
                    if st.session_state.get("axiel_audio_target") == int(row["id"]):
                        voice_label = st.session_state.get(
                            "axiel_tts_voice",
                            DEFAULT_AXIEL_VOICE,
                        )
                        try:
                            with st.spinner("Gerando audio da Axiel..."):
                                audio_bytes = synthesize_axiel_audio(
                                    str(row["mensagem"]),
                                    voice_label,
                                )
                        except Exception:
                            audio_bytes = b""

                        if audio_bytes:
                            st.audio(
                                audio_bytes,
                                format="audio/mp3",
                                autoplay=st.session_state.get("axiel_audio_autoplay")
                                == int(row["id"]),
                            )
                            if st.button(
                                "Fechar audio",
                                key=f"axiel_hide_audio_{int(row['id'])}",
                            ):
                                st.session_state.pop("axiel_audio_target", None)
                                st.session_state.pop("axiel_audio_autoplay", None)
                                st.rerun()
                        else:
                            st.error("Nao foi possivel gerar o audio desta resposta.")

    prompt = st.chat_input("Pergunte à Axiel AI sobre sua rotina de saúde e performance")
    if prompt:
        _process_axiel_message(prompt)

    col_left, _ = st.columns([1, 5])
    if col_left.button("Limpar histórico", use_container_width=True):
        clear_axiel_history()
        _reset_axiel_audio_player()
        _invalidate_data_cache()
        st.rerun()
    st.session_state.pop("axiel_audio_autoplay", None)


def _process_axiel_message(prompt: str) -> None:
    save_axiel_message("user", prompt)
    _invalidate_data_cache()
    datasets, profile = _load_ui_data()
    response = generate_axiel_response(prompt, profile, datasets)
    save_axiel_message("assistant", response)
    _invalidate_data_cache()
    st.rerun()


def _render_date_controls(
    start_bound: date,
    end_bound: date,
    key_prefix: str,
    use_sidebar: bool = False,
) -> tuple[str, str, date, date]:
    options = ["7 dias", "30 dias", "90 dias", "Todo o histórico", "Personalizado"]
    target = st.sidebar if use_sidebar else st
    period_key = f"{key_prefix}_period"
    view_key = f"{key_prefix}_view"
    interval_key = f"{key_prefix}_applied_dates"
    last_period_key = f"{key_prefix}_last_period"
    default_period = "30 dias"

    if st.session_state.get(period_key) not in options:
        st.session_state[period_key] = default_period

    if use_sidebar:
        target.markdown(
            """
            <div class="sidebar-filter-card">
                <div class="sidebar-filter-label">Filtros do dashboard</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_range = target.selectbox("Período", options, key=period_key)
        view_mode = target.selectbox("Visão", ["Dia", "Semana", "Mês"], key=view_key)
    else:
        col1, col2, col3 = st.columns([1.2, 1, 1.2])
        selected_range = col1.selectbox("Período", options, key=period_key)
        view_mode = col2.selectbox("Visão", ["Dia", "Semana", "Mês"], key=view_key)

    preset_start, preset_end = _resolve_date_preset(selected_range, start_bound, end_bound)
    period_changed = st.session_state.get(last_period_key) != selected_range

    if interval_key not in st.session_state or (period_changed and selected_range != "Personalizado"):
        st.session_state[interval_key] = (preset_start, preset_end)

    st.session_state[last_period_key] = selected_range

    interval_value = target.date_input(
        "Intervalo aplicado",
        min_value=start_bound,
        max_value=end_bound,
        key=interval_key,
    )
    start_date, end_date = _normalize_date_interval(
        interval_value,
        start_bound=start_bound,
        end_bound=end_bound,
        fallback_start=preset_start,
        fallback_end=preset_end,
    )

    if selected_range != "Personalizado" and (start_date, end_date) != (preset_start, preset_end):
        st.session_state[period_key] = "Personalizado"
        st.session_state[last_period_key] = "Personalizado"
        st.rerun()

    return st.session_state.get(period_key, selected_range), view_mode, start_date, end_date


def _resolve_date_preset(
    selected_range: str,
    start_bound: date,
    end_bound: date,
) -> tuple[date, date]:
    if selected_range == "7 dias":
        return max(start_bound, end_bound - timedelta(days=6)), end_bound
    if selected_range == "30 dias":
        return max(start_bound, end_bound - timedelta(days=29)), end_bound
    if selected_range == "90 dias":
        return max(start_bound, end_bound - timedelta(days=89)), end_bound
    return start_bound, end_bound


def _normalize_date_interval(
    value: Any,
    *,
    start_bound: date,
    end_bound: date,
    fallback_start: date,
    fallback_end: date,
) -> tuple[date, date]:
    if isinstance(value, tuple | list) and len(value) == 2:
        raw_start, raw_end = value
    elif isinstance(value, date):
        raw_start = raw_end = value
    else:
        raw_start, raw_end = fallback_start, fallback_end

    start_date = min(max(raw_start, start_bound), end_bound)
    end_date = min(max(raw_end, start_date), end_bound)
    return start_date, end_date


def _render_general_dashboard(
    datasets: dict[str, pd.DataFrame],
    profile: dict[str, Any],
    snapshot: dict[str, Any],
    view_mode: str,
) -> None:
    body = datasets["dados_corporais"]
    activities = datasets["atividades_fisicas"]
    food = datasets["alimentacao"]
    sleep = prepare_sleep_analysis_df(datasets["registros_sono"])
    active_goals = datasets["metas"]
    archived_goals = datasets["metas_finalizadas"]

    weight, weight_delta = latest_value_with_delta(body, "peso")
    bmi, bmi_delta = latest_value_with_delta(body, "imc")
    calories_consumed = float(food["calorias"].sum()) if not food.empty else 0.0
    calories_burned = (
        float(activities["calorias_gastas"].sum()) if not activities.empty else 0.0
    )
    weight_goal = float(profile.get("peso_meta") or 0)
    bmi_badge, bmi_badge_tone, bmi_supporting = _bmi_status(bmi)

    first_row = _metric_columns(4)
    _render_metric_card(
        first_row[0],
        "Peso atual",
        _fmt_metric(weight, "kg"),
        _fmt_delta(weight_delta, "kg"),
    )
    _render_metric_card(
        first_row[1],
        "IMC atual",
        _fmt_metric(bmi, digits=2),
        _fmt_delta(bmi_delta, digits=2),
        badge=bmi_badge,
        badge_tone=bmi_badge_tone,
        supporting_text=bmi_supporting,
    )
    _render_metric_card(
        first_row[2],
        "Meta de peso",
        _fmt_metric(weight_goal, "kg"),
        _fmt_delta(weight - weight_goal if weight is not None else None, "kg"),
        delta_color="inverse",
    )
    _render_metric_card(first_row[3], "Atividades registradas", str(len(activities)))

    weekly_activity, previous_week_activity = compare_recent_windows(
        activities,
        "duracao_minutos",
        date_col="data",
        window_days=7,
        agg="sum",
    )
    monthly_food, previous_month_food = compare_recent_windows(
        food,
        "calorias",
        date_col="data",
        window_days=30,
        agg="sum",
    )

    second_row = _metric_columns(4)
    _render_metric_card(
        second_row[0],
        "Calorias consumidas",
        _fmt_metric(calories_consumed, "kcal", 0),
    )
    _render_metric_card(
        second_row[1],
        "Calorias gastas",
        _fmt_metric(calories_burned, "kcal", 0),
    )
    _render_metric_card(
        second_row[2],
        "Evolução semanal",
        _fmt_metric(weekly_activity, " min", 0),
        _fmt_delta(
            (weekly_activity - previous_week_activity)
            if weekly_activity is not None and previous_week_activity is not None
            else None,
            " min",
            0,
        ),
    )
    _render_metric_card(
        second_row[3],
        "Tendência calórica",
        _fmt_metric(monthly_food, " kcal", 0),
        _fmt_delta(
            (monthly_food - previous_month_food)
            if monthly_food is not None and previous_month_food is not None
            else None,
            " kcal",
            0,
        ),
    )

    insight_cols = st.columns([2, 1])
    with insight_cols[0]:
        _render_weight_and_bmi_charts(body, key_prefix="dashboard_general_body")
    with insight_cols[1]:
        sleep_summary = ""
        if not sleep.empty:
            sleep_summary = (
                f" Sono médio em {_format_duration_hours(float(sleep['duracao_horas'].mean()))}, "
                f"dormindo em média às {_format_decimal_hour(float(sleep['hora_dormir_plot'].mean()))} "
                f"e acordando às {_format_decimal_hour(float(sleep['hora_acordar_plot'].mean()))}."
            )
        st.markdown(
            f"""
            <div class="note-card">
                <strong>Resumo do período</strong>
                Peso atual em {_fmt_metric(snapshot["weight"], "kg")} com IMC em
                {_fmt_metric(snapshot["bmi"], digits=2)}. Consistência de treino classificada
                como {snapshot["activity_consistency"].lower()} e taxa de metas concluídas em
                {_fmt_metric(snapshot["completion_rate"], "%", 1)}.{sleep_summary}
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_goal_status_chart(
            active_goals,
            archived_goals,
            chart_key="dashboard_general_goal_status",
            height=260,
        )

    st.markdown("##### Comparativos energéticos e frequência de treino")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        _render_calorie_balance_chart(
            food,
            activities,
            view_mode,
            chart_key="dashboard_general_calorie_balance",
        )
    with chart_cols[1]:
        _render_activity_frequency_chart(
            activities,
            chart_key="dashboard_general_activity_frequency",
        )


def _render_sleep_dashboard(datasets: dict[str, pd.DataFrame], view_mode: str) -> None:
    sleep = prepare_sleep_analysis_df(datasets["registros_sono"])
    if sleep.empty:
        st.info("Cadastre horários de dormir e acordar para visualizar os indicadores de sono.")
        return

    sleep = sleep.copy()
    sleep["target_sleep_hours"] = sleep["data"].apply(_get_sleep_target_hours)
    sleep["sleep_margin_minutes"] = (
        sleep["duracao_horas"] - sleep["target_sleep_hours"]
    ) * 60
    sleep["duration_gap_minutes"] = (
        sleep["target_sleep_hours"] - sleep["duracao_horas"]
    ).clip(lower=0) * 60
    sleep["stable_routine"] = sleep["sleep_margin_minutes"] >= -SLEEP_TARGET_TOLERANCE_MINUTES
    sleep["routine_status"] = sleep["sleep_margin_minutes"].apply(
        lambda margin: "Na meta"
        if margin >= -SLEEP_TARGET_TOLERANCE_MINUTES
        else "Leve abaixo"
        if margin >= -45
        else "Fora da meta"
    )

    recent_sleep, previous_sleep = compare_recent_windows(
        sleep,
        "duracao_horas",
        date_col="data",
        window_days=7,
        agg="mean",
    )
    latest_sleep = sleep.sort_values("data").iloc[-1]
    avg_sleep = float(sleep["duracao_horas"].mean())
    avg_bedtime = float(sleep["hora_dormir_plot"].mean())
    avg_waketime = float(sleep["hora_acordar_plot"].mean())
    stable_nights = int(sleep["stable_routine"].sum())
    stable_share = stable_nights / len(sleep) * 100
    duration_trend_caption = (
        f"{_get_sleep_target_caption(sleep)} "
        f"{stable_nights} de {len(sleep)} noites ficaram dentro da meta."
    )

    row = _metric_columns(5)
    _render_metric_card(
        row[0],
        "Sono médio",
        _format_duration_hours(avg_sleep),
        _format_duration_delta(
            (recent_sleep - previous_sleep)
            if recent_sleep is not None and previous_sleep is not None
            else None
        ),
    )
    _render_metric_card(
        row[1],
        "Última noite",
        _format_duration_hours(float(latest_sleep["duracao_horas"])),
        supporting_text=latest_sleep["data"].strftime("%d/%m/%Y"),
    )
    _render_metric_card(
        row[2],
        "Hora média de dormir",
        _format_decimal_hour(avg_bedtime),
    )
    _render_metric_card(
        row[3],
        "Hora média de acordar",
        _format_decimal_hour(avg_waketime),
    )
    _render_metric_card(
        row[4],
        "Noites na meta",
        str(stable_nights),
        supporting_text=f"{stable_share:.0f}% dentro da meta de sono",
    )

    charts = st.columns(2)
    with charts[0]:
        st.markdown("##### Sono real vs meta de sono")
        st.caption(duration_trend_caption)
        duration = aggregate_multi_series(
            sleep,
            ["duracao_horas", "target_sleep_hours"],
            date_col="data",
            view_mode=view_mode,
            agg="mean",
        )
        duration["status"] = (
            (duration["duracao_horas"] - duration["target_sleep_hours"]) * 60
        ).apply(
            lambda margin: "Na meta"
            if margin >= -SLEEP_TARGET_TOLERANCE_MINUTES
            else "Leve abaixo"
            if margin >= -45
            else "Fora da meta"
        )
        duration["actual_label"] = duration["duracao_horas"].map(_format_duration_hours)
        duration["target_label"] = duration["target_sleep_hours"].map(_format_duration_hours)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=duration["data"],
                y=duration["duracao_horas"],
                name="Sono real",
                marker=dict(
                    color=duration["status"].map(
                        {
                            "Na meta": COLOR_SEQUENCE[0],
                            "Leve abaixo": COLOR_SEQUENCE[3],
                            "Fora da meta": COLOR_SEQUENCE[4],
                        }
                    ).tolist()
                ),
                customdata=duration[["actual_label", "target_label", "status"]],
                hovertemplate=(
                    "Periodo: %{x|%d/%m}<br>"
                    "Sono real: %{customdata[0]}<br>"
                    "Meta: %{customdata[1]}<br>"
                    "Status: %{customdata[2]}<extra></extra>"
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=duration["data"],
                y=duration["target_sleep_hours"],
                mode="lines+markers",
                name="Meta do período",
                line=dict(color="#f4fff9", width=2.4, dash="dash", shape="spline"),
                marker=dict(size=6),
                customdata=duration[["target_label"]],
                hovertemplate=(
                    "Periodo: %{x|%d/%m}<br>"
                    "Meta do período: %{customdata[0]}<extra></extra>"
                ),
            )
        )
        _style_plot(fig)
        fig.update_layout(
            hovermode="closest",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(
            tickformat="%d/%m" if view_mode != "Mês" else "%m/%y",
            title=None,
        )
        fig.update_yaxes(title="Horas", rangemode="tozero")
        _plot_chart(fig, "dashboard_sleep_duration")

    with charts[1]:
        st.markdown("##### Janela média do sono por período")
        schedule = aggregate_multi_series(
            sleep,
            ["hora_dormir_plot", "hora_acordar_plot"],
            date_col="data",
            view_mode=view_mode,
            agg="mean",
        ).rename(
            columns={
                "hora_dormir_plot": "Dormir",
                "hora_acordar_plot": "Acordar",
            }
        )
        schedule["Dormir_label"] = schedule["Dormir"].map(_format_decimal_hour)
        schedule["Acordar_label"] = schedule["Acordar"].map(_format_decimal_hour)
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=schedule["data"],
                y=schedule["Dormir"],
                mode="lines",
                name="Dormir",
                line=dict(color="rgba(255, 209, 102, 0.95)", width=2.2, shape="spline"),
                customdata=schedule[["Dormir_label"]],
                hovertemplate="Periodo: %{x|%d/%m}<br>Dormir: %{customdata[0]}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=schedule["data"],
                y=schedule["Acordar"],
                mode="lines",
                name="Acordar",
                line=dict(color=COLOR_SEQUENCE[0], width=2.6, shape="spline"),
                fill="tonexty",
                fillcolor="rgba(0, 249, 149, 0.14)",
                customdata=schedule[["Acordar_label"]],
                hovertemplate="Periodo: %{x|%d/%m}<br>Acordar: %{customdata[0]}<extra></extra>",
            )
        )
        _style_plot(fig)
        tickvals, ticktext = _sleep_tick_values()
        fig.update_layout(
            hovermode="closest",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(
            tickformat="%d/%m" if view_mode != "Mês" else "%m/%y",
            title=None,
            nticks=10,
            tickangle=0,
        )
        fig.update_yaxes(
            title="Horário",
            tickvals=tickvals,
            ticktext=ticktext,
            range=[22, 33],
        )
        _plot_chart(fig, "dashboard_sleep_schedule")

    st.markdown("##### Aderência à meta de sono")
    routine_freq = {"Dia": "W-MON", "Semana": "W-MON", "Mês": "M"}[view_mode]
    routine_summary = (
        sleep.groupby([pd.Grouper(key="data", freq=routine_freq), "routine_status"])
        .size()
        .reset_index(name="total")
    )
    fig = px.bar(
        routine_summary,
        x="data",
        y="total",
        color="routine_status",
        color_discrete_map={
            "Na meta": COLOR_SEQUENCE[0],
            "Leve abaixo": COLOR_SEQUENCE[3],
            "Fora da meta": COLOR_SEQUENCE[4],
        },
        category_orders={
            "routine_status": ["Na meta", "Leve abaixo", "Fora da meta"]
        },
    )
    _style_plot(fig)
    fig.update_layout(
        barmode="stack",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.for_each_trace(
        lambda trace: trace.update(
            hovertemplate=(
                "Periodo: %{x|%d/%m}<br>"
                "Noites: %{y}<br>"
                f"Status: {trace.name}<extra></extra>"
            )
        )
    )
    fig.update_xaxes(
        tickformat="%d/%m" if view_mode != "Mês" else "%m/%y",
        title=None,
    )
    fig.update_yaxes(
        title="Noites",
        rangemode="tozero",
    )
    _plot_chart(fig, "dashboard_sleep_routine_adherence")


def _render_cardiac_dashboard(datasets: dict[str, pd.DataFrame], view_mode: str) -> None:
    heart = datasets["registros_cardiacos"]
    if heart.empty:
        st.info("Cadastre registros cardíacos para visualizar este dashboard.")
        return

    recent_avg, previous_avg = compare_recent_windows(
        heart,
        "frequencia_media",
        date_col="data",
        window_days=7,
        agg="mean",
    )
    recent_rest, previous_rest = compare_recent_windows(
        heart,
        "frequencia_repouso",
        date_col="data",
        window_days=7,
        agg="mean",
    )

    row = _metric_columns(4)
    _render_metric_card(
        row[0],
        "Freq. média",
        _fmt_metric(float(heart["frequencia_media"].mean()), " bpm", 0),
        _fmt_delta(
            (recent_avg - previous_avg)
            if recent_avg is not None and previous_avg is not None
            else None,
            " bpm",
            0,
        ),
    )
    _render_metric_card(
        row[1],
        "Repouso médio",
        _fmt_metric(float(heart["frequencia_repouso"].mean()), " bpm", 0),
        _fmt_delta(
            (recent_rest - previous_rest)
            if recent_rest is not None and previous_rest is not None
            else None,
            " bpm",
            0,
        ),
    )
    _render_metric_card(
        row[2],
        "Máxima registrada",
        f"{int(heart['frequencia_maxima'].max())} bpm",
    )
    _render_metric_card(
        row[3],
        "Mínima registrada",
        f"{int(heart['frequencia_minima'].min())} bpm",
    )

    charts = st.columns(2)
    with charts[0]:
        heart_df = heart.copy()
        heart_df["data"] = pd.to_datetime(heart_df["data"])
        fig = px.line(
            heart_df,
            x="data",
            y="frequencia_media",
            markers=True,
            title="Frequência cardíaca por data",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_cardiac_frequency_line")

    with charts[1]:
        weekly = aggregate_timeseries(
            heart,
            "frequencia_media",
            date_col="data",
            view_mode="Semana",
            agg="mean",
        )
        if weekly.empty:
            st.info("Sem dados suficientes para a média semanal.")
        else:
            fig = px.bar(
                weekly,
                x="periodo",
                y="valor",
                title="Média cardíaca por semana",
                color_discrete_sequence=[COLOR_SEQUENCE[1]],
            )
            _style_plot(fig)
            _plot_chart(fig, "dashboard_cardiac_weekly_average")

    secondary = st.columns(2)
    with secondary[0]:
        distribution = (
            heart.groupby("frequencia_media")
            .size()
            .reset_index(name="total")
            .sort_values("frequencia_media")
        )
        mean_bpm = float(heart["frequencia_media"].mean())
        fig = px.bar(
            distribution,
            x="frequencia_media",
            y="total",
            text="total",
            title="Distribuição dos batimentos médios",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        _style_plot(fig)
        fig.add_vline(
            x=mean_bpm,
            line_dash="dash",
            line_color="rgba(255, 209, 102, 0.92)",
            line_width=2,
        )
        fig.add_annotation(
            x=mean_bpm,
            y=1.12,
            yref="paper",
            text=f"Média {mean_bpm:.0f} bpm",
            showarrow=False,
            font=dict(color="#ffd166", size=12),
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="BPM médio %{x}<br>Dias %{y}<extra></extra>",
        )
        fig.update_xaxes(dtick=1, title="BPM médio")
        fig.update_yaxes(title="Dias registrados")
        _plot_chart(fig, "dashboard_cardiac_distribution")

    with secondary[1]:
        st.markdown("##### Comparação entre repouso e atividade")
        comparison = aggregate_multi_series(
            heart,
            ["frequencia_media", "frequencia_repouso"],
            date_col="data",
            view_mode=view_mode,
            agg="mean",
        )
        comparison = comparison.rename(
            columns={
                "frequencia_media": "Atividade",
                "frequencia_repouso": "Repouso",
            }
        )
        melted = comparison.melt(
            id_vars=["data", "periodo"],
            value_vars=["Atividade", "Repouso"],
            var_name="Categoria",
            value_name="BPM",
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=comparison["data"],
                y=comparison["Repouso"],
                mode="lines+markers",
                name="Repouso",
                line=dict(color="rgba(11, 209, 132, 0.72)"),
                marker=dict(size=5),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=comparison["data"],
                y=comparison["Atividade"],
                mode="lines+markers",
                name="Atividade",
                fill="tonexty",
                fillcolor="rgba(0, 249, 149, 0.10)",
                line=dict(color=COLOR_SEQUENCE[0]),
                marker=dict(size=5),
            )
        )
        _style_plot(fig)
        bpm_min = float(melted["BPM"].min()) if not melted.empty else 0.0
        bpm_max = float(melted["BPM"].max()) if not melted.empty else 0.0
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(
            tickformat="%d/%m" if view_mode != "Mês" else "%m/%y",
            title=None,
            nticks=10,
            tickangle=0,
        )
        fig.update_yaxes(
            title="BPM",
            range=[max(0, bpm_min - 4), bpm_max + 4],
        )
        _plot_chart(fig, "dashboard_cardiac_rest_vs_activity")


def _render_activity_dashboard(datasets: dict[str, pd.DataFrame], view_mode: str) -> None:
    activities = datasets["atividades_fisicas"]
    if activities.empty:
        st.info("Cadastre atividades para visualizar métricas de treino.")
        return

    row = _metric_columns(4)
    _render_metric_card(
        row[0],
        "Tipo dominante",
        activities["tipo_atividade"].mode().iloc[0],
    )
    _render_metric_card(
        row[1],
        "Tempo total",
        _fmt_metric(float(activities["duracao_minutos"].sum()), " min", 0),
    )
    _render_metric_card(
        row[2],
        "Calorias gastas",
        _fmt_metric(float(activities["calorias_gastas"].sum()), " kcal", 0),
    )
    _render_metric_card(
        row[3],
        "Distância total",
        _fmt_metric(float(activities["distancia_km"].sum()), " km", 1),
    )

    second = st.columns(2)
    with second[0]:
        by_type = (
            activities.groupby("tipo_atividade")["duracao_minutos"]
            .sum()
            .reset_index()
            .sort_values("duracao_minutos", ascending=False)
        )
        fig = px.bar(
            by_type,
            x="tipo_atividade",
            y="duracao_minutos",
            title="Tempo por tipo de atividade",
            color="tipo_atividade",
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_activity_time_by_type")

    with second[1]:
        evolution = aggregate_timeseries(
            activities,
            "__count__",
            date_col="data",
            view_mode=view_mode,
            agg="sum",
        )
        fig = px.line(
            evolution,
            x="periodo",
            y="valor",
            markers=True,
            title="Evolução de treinos",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_activity_evolution")

    third = st.columns(2)
    with third[0]:
        distribution = (
            activities.groupby("tipo_atividade")["calorias_gastas"]
            .sum()
            .reset_index()
        )
        fig = px.pie(
            distribution,
            names="tipo_atividade",
            values="calorias_gastas",
            title="Distribuição por modalidade",
            hole=0.56,
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_activity_distribution")

    with third[1]:
        calories = aggregate_timeseries(
            activities,
            "calorias_gastas",
            date_col="data",
            view_mode=view_mode,
            agg="sum",
        )
        fig = px.bar(
            calories,
            x="periodo",
            y="valor",
            title="Calorias gastas por período",
            color_discrete_sequence=[COLOR_SEQUENCE[2]],
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_activity_calories")

    trained = aggregate_timeseries(
        activities,
        "duracao_minutos",
        date_col="data",
        view_mode="Semana" if view_mode == "Dia" else view_mode,
        agg="sum",
    )
    fig = px.area(
        trained,
        x="periodo",
        y="valor",
        title="Tempo total treinado por período",
        color_discrete_sequence=[COLOR_SEQUENCE[1]],
    )
    _style_plot(fig)
    _plot_chart(fig, "dashboard_activity_total_trained")


def _render_food_dashboard(datasets: dict[str, pd.DataFrame], view_mode: str) -> None:
    food = datasets["alimentacao"]
    activities = datasets["atividades_fisicas"]
    if food.empty:
        st.info("Cadastre refeições para visualizar o dashboard alimentar.")
        return

    row = _metric_columns(4)
    _render_metric_card(row[0], "Refeições cadastradas", str(len(food)))
    _render_metric_card(
        row[1],
        "Calorias totais",
        _fmt_metric(float(food["calorias"].sum()), " kcal", 0),
    )
    _render_metric_card(
        row[2],
        "Proteínas",
        _fmt_metric(float(food["proteinas"].sum()), " g", 0),
    )
    _render_metric_card(
        row[3],
        "Carboidratos",
        _fmt_metric(float(food["carboidratos"].sum()), " g", 0),
    )

    charts = st.columns(2)
    with charts[0]:
        by_meal = food.groupby("refeicao")["calorias"].sum().reset_index()
        fig = px.bar(
            by_meal,
            x="refeicao",
            y="calorias",
            title="Calorias por refeição",
            color="refeicao",
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_food_calories_by_meal")

    with charts[1]:
        macros = pd.DataFrame(
            {
                "macro": ["Proteínas", "Carboidratos", "Gorduras"],
                "valor": [
                    float(food["proteinas"].sum()),
                    float(food["carboidratos"].sum()),
                    float(food["gorduras"].sum()),
                ],
            }
        )
        fig = px.pie(
            macros,
            names="macro",
            values="valor",
            title="Distribuição de macronutrientes",
            hole=0.58,
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_food_macro_distribution")

    line_cols = st.columns(2)
    with line_cols[0]:
        daily = aggregate_timeseries(
            food,
            "calorias",
            date_col="data",
            view_mode=view_mode,
            agg="sum",
        )
        fig = px.line(
            daily,
            x="periodo",
            y="valor",
            markers=True,
            title="Consumo calórico por período",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_food_calorie_consumption")

    with line_cols[1]:
        _render_calorie_balance_chart(
            food,
            activities,
            view_mode,
            chart_key="dashboard_food_calorie_balance",
        )


def _render_goals_dashboard(
    datasets: dict[str, pd.DataFrame],
    view_mode: str,
    reference_date: date,
) -> None:
    active_goals = datasets["metas"]
    archived_goals = datasets["metas_finalizadas"]
    status_df = summarize_goal_statuses(active_goals, archived_goals)

    total_goals = len(active_goals) + len(archived_goals)
    concluded = len(archived_goals) + int(
        (active_goals["status"] == "Concluído").sum() if not active_goals.empty else 0
    )
    completion_rate = concluded / total_goals * 100 if total_goals else 0

    row = _metric_columns(5)
    _render_metric_card(row[0], "Total de metas", str(total_goals))
    _render_metric_card(
        row[1],
        "Programadas",
        str(int(status_df.loc[status_df["status"] == "Programado", "total"].sum())),
    )
    _render_metric_card(
        row[2],
        "Iniciadas",
        str(int(status_df.loc[status_df["status"] == "Iniciado", "total"].sum())),
    )
    _render_metric_card(
        row[3],
        "Em andamento",
        str(int(status_df.loc[status_df["status"] == "Em Andamento", "total"].sum())),
    )
    _render_metric_card(
        row[4],
        "Taxa de conclusão",
        _fmt_metric(completion_rate, "%", 1),
    )

    charts = st.columns(2)
    with charts[0]:
        _render_goal_status_chart(
            active_goals,
            archived_goals,
            chart_key="dashboard_goals_status",
            height=320,
        )

    with charts[1]:
        pace = prepare_goal_pace_table(active_goals, reference_date=reference_date)
        if pace.empty:
            if not archived_goals.empty:
                st.info("Sem metas ativas neste recorte. As metas visíveis já foram finalizadas.")
            else:
                st.info("Nenhuma meta cadastrada.")
        else:
            st.markdown("##### Tendência de cumprimento das metas")
            trend_counts = pace["tendencia"].value_counts()
            caption_parts = [
                f"{int(trend_counts.get('Adiantada', 0))} adiantadas",
                f"{int(trend_counts.get('No ritmo', 0))} no ritmo",
                f"{int(trend_counts.get('Em risco', 0))} em risco",
            ]
            if int(trend_counts.get("Concluída", 0)):
                caption_parts.append(f"{int(trend_counts.get('Concluída', 0))} concluídas")
            st.caption(
                "Referência até "
                f"{reference_date.strftime('%d/%m/%Y')}: "
                + ", ".join(caption_parts)
                + "."
            )
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=pace["progresso"],
                    y=pace["titulo"],
                    orientation="h",
                    name="Progresso atual",
                    marker=dict(
                        color=pace["tendencia"].map(
                            {
                                "Adiantada": COLOR_SEQUENCE[0],
                                "No ritmo": COLOR_SEQUENCE[3],
                                "Em risco": COLOR_SEQUENCE[4],
                                "Concluída": COLOR_SEQUENCE[2],
                            }
                        ).tolist()
                    ),
                    customdata=pace[
                        [
                            "progresso_esperado",
                            "desvio_ritmo",
                            "prazo_label",
                            "dias_restantes",
                            "tendencia",
                        ]
                    ],
                    hovertemplate=(
                        "Meta: %{y}<br>"
                        "Progresso atual: %{x:.0f}%<br>"
                        "Ritmo esperado: %{customdata[0]:.0f}%<br>"
                        "Desvio: %{customdata[1]:+.0f} pp<br>"
                        "Prazo: %{customdata[2]}<br>"
                        "Dias restantes: %{customdata[3]}<br>"
                        "Tendência: %{customdata[4]}<extra></extra>"
                    ),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pace["progresso_esperado"],
                    y=pace["titulo"],
                    mode="markers",
                    name="Ritmo esperado",
                    marker=dict(
                        symbol="line-ns-open",
                        size=22,
                        color="#f4fff9",
                        line=dict(width=2, color="#f4fff9"),
                    ),
                    hovertemplate=(
                        "Meta: %{y}<br>"
                        "Ritmo esperado nesta data: %{x:.0f}%<extra></extra>"
                    ),
                )
            )
            _style_plot(fig)
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            fig.update_xaxes(title="Progresso (%)", range=[0, 105])
            fig.update_yaxes(
                title=None,
                categoryorder="array",
                categoryarray=pace["titulo"].tolist()[::-1],
                automargin=True,
            )
            _plot_chart(fig, "dashboard_goals_progress_timeline")

    combined = prepare_goal_table(active_goals, archived_goals)
    if not combined.empty:
        open_vs_done = pd.DataFrame(
            {
                "grupo": ["Abertas", "Finalizadas"],
                "total": [
                    int((combined["situacao_final"] == "Em aberto").sum()),
                    int((combined["situacao_final"] != "Em aberto").sum()),
                ],
            }
        )
        fig = px.bar(
            open_vs_done,
            x="grupo",
            y="total",
            title="Comparativo entre metas abertas e finalizadas",
            color="grupo",
            color_discrete_sequence=[COLOR_SEQUENCE[0], COLOR_SEQUENCE[2]],
        )
        _style_plot(fig)
        _plot_chart(fig, "dashboard_goals_open_vs_done")


def _render_body_register(body_df: pd.DataFrame) -> None:
    col_form, col_table = st.columns([1, 1.35])

    with col_form:
        with st.form("body_register_form", clear_on_submit=True):
            data_ref = st.date_input("Data", value=date.today())
            idade = st.number_input("Idade", min_value=0, max_value=120, value=30, step=1)
            peso = st.number_input("Peso (kg)", min_value=0.0, max_value=400.0, value=70.0, step=0.1)
            altura = st.number_input(
                "Altura (m)",
                min_value=0.5,
                max_value=2.5,
                value=1.70,
                step=0.01,
                format="%.2f",
            )
            st.caption(f"IMC calculado automaticamente: {calculate_imc(peso, altura):.2f}")
            submitted = st.form_submit_button("Salvar dado corporal", use_container_width=True)

        if submitted:
            insert_body_record(
                data=data_ref.isoformat(),
                idade=int(idade),
                peso=float(peso),
                altura=float(altura),
            )
            _invalidate_data_cache()
            st.success("Dado corporal registrado.")
            st.rerun()

    with col_table:
        table = body_df.sort_values("data", ascending=False) if not body_df.empty else body_df
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_cardiac_register(heart_df: pd.DataFrame) -> None:
    col_form, col_table = st.columns([1, 1.35])

    with col_form:
        with st.form("cardiac_register_form", clear_on_submit=True):
            data_ref = st.date_input("Data do registro", value=date.today())
            cols = st.columns(2)
            frequencia_media = cols[0].number_input("Freq. média", min_value=20, max_value=240, value=78)
            frequencia_repouso = cols[1].number_input("Freq. repouso", min_value=20, max_value=220, value=62)
            frequencia_maxima = cols[0].number_input("Freq. máxima", min_value=20, max_value=250, value=148)
            frequencia_minima = cols[1].number_input("Freq. mínima", min_value=20, max_value=220, value=54)
            observacoes = st.text_area("Observações", placeholder="Ex.: treino intenso, noite mal dormida...")
            submitted = st.form_submit_button("Salvar registro cardíaco", use_container_width=True)

        if submitted:
            insert_cardiac_record(
                data=data_ref.isoformat(),
                frequencia_media=int(frequencia_media),
                frequencia_repouso=int(frequencia_repouso),
                frequencia_maxima=int(frequencia_maxima),
                frequencia_minima=int(frequencia_minima),
                observacoes=observacoes,
            )
            _invalidate_data_cache()
            st.success("Registro cardíaco salvo.")
            st.rerun()

    with col_table:
        table = heart_df.sort_values("data", ascending=False) if not heart_df.empty else heart_df
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_activity_register(activity_df: pd.DataFrame) -> None:
    col_form, col_table = st.columns([1, 1.35])

    with col_form:
        with st.form("activity_register_form", clear_on_submit=True):
            data_ref = st.date_input("Data da atividade", value=date.today())
            tipo = st.text_input("Tipo de atividade", value="Corrida")
            cols = st.columns(2)
            duracao = cols[0].number_input("Duração (min)", min_value=0, max_value=1440, value=45)
            intensidade = cols[1].selectbox("Intensidade", ACTIVITY_INTENSITIES)
            calorias = cols[0].number_input("Calorias gastas", min_value=0.0, max_value=10000.0, value=350.0, step=10.0)
            distancia = cols[1].number_input("Distância (km)", min_value=0.0, max_value=500.0, value=5.0, step=0.1)
            observacoes = st.text_area("Observações", placeholder="Ex.: treino intervalado, musculação de pernas...")
            submitted = st.form_submit_button("Salvar atividade", use_container_width=True)

        if submitted:
            insert_activity_record(
                data=data_ref.isoformat(),
                tipo_atividade=tipo,
                duracao_minutos=int(duracao),
                intensidade=intensidade,
                calorias_gastas=float(calorias),
                distancia_km=float(distancia),
                observacoes=observacoes,
            )
            _invalidate_data_cache()
            st.success("Atividade registrada.")
            st.rerun()

    with col_table:
        table = (
            activity_df.sort_values("data", ascending=False)
            if not activity_df.empty
            else activity_df
        )
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_food_register(food_df: pd.DataFrame) -> None:
    col_form, col_table = st.columns([1, 1.35])

    with col_form:
        with st.form("food_register_form", clear_on_submit=True):
            data_ref = st.date_input("Data da refeição", value=date.today())
            cols = st.columns(2)
            refeicao = cols[0].selectbox("Refeição", MEAL_OPTIONS)
            alimento = cols[1].text_input("Alimento", value="Peito de frango")
            quantidade = cols[0].number_input("Quantidade", min_value=0.0, max_value=10000.0, value=150.0, step=10.0)
            calorias = cols[1].number_input("Calorias", min_value=0.0, max_value=10000.0, value=280.0, step=10.0)
            proteinas = cols[0].number_input("Proteínas (g)", min_value=0.0, max_value=2000.0, value=30.0, step=1.0)
            carboidratos = cols[1].number_input("Carboidratos (g)", min_value=0.0, max_value=2000.0, value=12.0, step=1.0)
            gorduras = cols[0].number_input("Gorduras (g)", min_value=0.0, max_value=2000.0, value=8.0, step=1.0)
            observacoes = st.text_area("Observações", placeholder="Ex.: refeição pós-treino, preparo assado...")
            submitted = st.form_submit_button("Salvar alimentação", use_container_width=True)

        if submitted:
            insert_food_record(
                data=data_ref.isoformat(),
                refeicao=refeicao,
                alimento=alimento,
                quantidade=float(quantidade),
                calorias=float(calorias),
                proteinas=float(proteinas),
                carboidratos=float(carboidratos),
                gorduras=float(gorduras),
                observacoes=observacoes,
            )
            _invalidate_data_cache()
            st.success("Registro alimentar salvo.")
            st.rerun()

    with col_table:
        table = food_df.sort_values("data", ascending=False) if not food_df.empty else food_df
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_sleep_register(sleep_df: pd.DataFrame) -> None:
    col_form, col_table = st.columns([1, 1.35])

    with col_form:
        with st.form("sleep_register_form", clear_on_submit=True):
            data_ref = st.date_input("Data da noite", value=date.today() - timedelta(days=1))
            cols = st.columns(2)
            hora_dormir = cols[0].time_input("Hora de dormir", value=time(23, 40))
            hora_acordar = cols[1].time_input("Hora de acordar", value=time(8, 0))
            observacoes = st.text_area(
                "Observações",
                placeholder="Ex.: dormi bem, acordei no meio da noite, sono leve...",
            )
            duration_hours = calculate_sleep_duration_hours(
                hora_dormir.strftime("%H:%M"),
                hora_acordar.strftime("%H:%M"),
            )
            st.caption(f"Duração estimada automaticamente: {_format_duration_hours(duration_hours)}")
            submitted = st.form_submit_button("Salvar registro de sono", use_container_width=True)

        if submitted:
            insert_sleep_record(
                data=data_ref.isoformat(),
                hora_dormir=hora_dormir.strftime("%H:%M"),
                hora_acordar=hora_acordar.strftime("%H:%M"),
                observacoes=observacoes,
            )
            _invalidate_data_cache()
            st.success("Registro de sono salvo.")
            st.rerun()

    with col_table:
        if sleep_df.empty:
            table = sleep_df
        else:
            table = sleep_df.sort_values("data", ascending=False).copy()
            table["duracao_horas"] = table["duracao_horas"].map(_format_duration_hours)
            table = table.rename(
                columns={
                    "data": "Data",
                    "hora_dormir": "Dormir",
                    "hora_acordar": "Acordar",
                    "duracao_horas": "Duração",
                    "observacoes": "Observações",
                }
            )
        st.dataframe(table, use_container_width=True, hide_index=True)


def _render_history_tab(datasets: dict[str, pd.DataFrame]) -> None:
    history = build_consolidated_history(datasets)
    if history.empty:
        st.info("Nenhum registro consolidado disponível ainda.")
        return

    history["referencia"] = pd.to_datetime(history["referencia"])
    min_date = history["referencia"].min().date()
    max_date = history["referencia"].max().date()

    range_option, _, start_date, end_date = _render_date_controls(
        min_date, max_date, key_prefix="history"
    )
    record_type = st.selectbox(
        "Tipo de registro",
        ["Todos"] + sorted(history["tipo"].unique().tolist()),
    )
    st.caption(f"Filtro aplicado: {range_option.lower()} para {record_type.lower()}.")

    filtered = history[
        (history["referencia"].dt.date >= start_date)
        & (history["referencia"].dt.date <= end_date)
    ]
    if record_type != "Todos":
        filtered = filtered[filtered["tipo"] == record_type]

    filtered = filtered.copy()
    filtered["referencia"] = filtered["referencia"].dt.strftime("%Y-%m-%d")
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def _render_kanban(active_goals: pd.DataFrame) -> None:
    if active_goals.empty:
        st.info("Nenhuma meta ativa cadastrada no momento.")
        return

    columns = st.columns(len(GOAL_STATUS_ORDER))
    for column, status in zip(columns, GOAL_STATUS_ORDER):
        with column:
            st.markdown(f"##### {status}")
            subset = active_goals[active_goals["status"] == status]
            if subset.empty:
                st.caption("Sem metas nesta coluna.")
                continue

            for _, goal in subset.iterrows():
                _render_goal_card(goal)


def _render_goal_card(goal: pd.Series) -> None:
    goal_id = int(goal["id"])
    progress_key = f"goal_progress_{goal_id}"
    progress_value = int(goal["progresso"])
    status_index = GOAL_STATUS_ORDER.index(goal["status"])

    if progress_key not in st.session_state:
        st.session_state[progress_key] = progress_value

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="goal-card">
                <div class="goal-card-head">
                    <h4>{goal['titulo']}</h4>
                    <p>{goal['descricao']}</p>
                    <div class="goal-meta">
                        <span class="goal-chip">{goal['categoria']}</span>
                        <span class="goal-chip">Prazo {goal['prazo']}</span>
                    </div>
                    <div class="small-note">Criada em {format_display_date(goal['data_criacao'])}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(progress_value / 100)

        st.markdown('<div class="goal-status-label">Status</div>', unsafe_allow_html=True)
        prev_col, status_col, next_col = st.columns([0.24, 1, 0.24], vertical_alignment="center")

        with prev_col:
            move_prev = st.button(
                "‹",
                key=f"goal_prev_status_{goal_id}",
                disabled=status_index == 0,
                help="Mover para o status anterior",
                type="secondary",
                use_container_width=True,
            )

        with status_col:
            st.markdown(
                f"""
                <div class="goal-status-readout">
                    <span class="goal-chip">{goal['status']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with next_col:
            move_next = st.button(
                "›",
                key=f"goal_next_status_{goal_id}",
                disabled=status_index == len(GOAL_STATUS_ORDER) - 1,
                help="Mover para o próximo status",
                type="secondary",
                use_container_width=True,
            )

        if move_prev:
            _shift_goal_status(goal, direction=-1, progress_key=progress_key)
        if move_next:
            _shift_goal_status(goal, direction=1, progress_key=progress_key)

        current_progress = int(st.session_state.get(progress_key, progress_value))
        st.markdown(
            f"""
            <div class="goal-progress-row">
                <span>Progresso</span>
                <strong>{current_progress}%</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.slider(
            "Progresso (%)",
            min_value=0,
            max_value=100,
            value=current_progress,
            key=progress_key,
            label_visibility="collapsed",
            on_change=_save_goal_progress,
            args=(goal_id, goal["status"], progress_key),
        )

        if goal["status"] == "Concluído":
            if st.button("Finalizar", key=f"finalize_{goal_id}", use_container_width=True):
                finalize_goal(goal_id)
                _invalidate_data_cache()
                st.rerun()


def _shift_goal_status(goal: pd.Series, direction: int, progress_key: str) -> None:
    current_index = GOAL_STATUS_ORDER.index(goal["status"])
    new_index = max(0, min(len(GOAL_STATUS_ORDER) - 1, current_index + direction))
    if new_index == current_index:
        return

    progress_value = int(st.session_state.get(progress_key, int(goal["progresso"])))
    update_goal(int(goal["id"]), GOAL_STATUS_ORDER[new_index], progress_value)
    st.session_state[progress_key] = progress_value
    _invalidate_data_cache()
    st.rerun()


def _save_goal_progress(goal_id: int, status: str, progress_key: str) -> None:
    update_goal(goal_id, status, int(st.session_state[progress_key]))
    _invalidate_data_cache()


def _render_goals_table(
    active_goals: pd.DataFrame,
    archived_goals: pd.DataFrame,
) -> None:
    table = prepare_goal_table(active_goals, archived_goals)
    if table.empty:
        st.info("Nenhuma meta registrada.")
        return

    table["data_criacao"] = pd.to_datetime(table["data_criacao"], errors="coerce")
    table["prazo"] = pd.to_datetime(table["prazo"], errors="coerce")
    min_date = table["data_criacao"].min().date()
    max_date = table["data_criacao"].max().date()
    min_deadline = table["prazo"].min().date()
    max_deadline = table["prazo"].max().date()

    filter_cols = st.columns(4)
    status_filter = filter_cols[0].multiselect(
        "Status",
        sorted(table["status"].dropna().unique().tolist()),
    )
    category_filter = filter_cols[1].multiselect(
        "Categoria",
        sorted(table["categoria"].dropna().unique().tolist()),
    )
    creation_range = filter_cols[2].date_input(
        "Data de criação",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    deadline_limit = filter_cols[3].date_input(
        "Prazo até",
        value=max_deadline,
        min_value=min(min_date, min_deadline),
        max_value=max(max_date, max_deadline),
    )

    filtered = table[
        (table["data_criacao"].dt.date >= creation_range[0])
        & (table["data_criacao"].dt.date <= creation_range[1])
    ]
    filtered = filtered[filtered["prazo"].dt.date <= deadline_limit]

    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if category_filter:
        filtered = filtered[filtered["categoria"].isin(category_filter)]

    display = filtered.copy()
    display["data_criacao"] = display["data_criacao"].dt.strftime("%Y-%m-%d")
    display["prazo"] = display["prazo"].dt.strftime("%Y-%m-%d")
    display = display.rename(
        columns={
            "id": "ID",
            "titulo": "Título",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "data_criacao": "Data de criação",
            "prazo": "Prazo",
            "status": "Status",
            "progresso": "Progresso",
            "situacao_final": "Situação final",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def _render_goal_form() -> None:
    with st.form("goal_register_form", clear_on_submit=True):
        titulo = st.text_input("Título", value="Baixar 2 kg com consistência")
        descricao = st.text_area("Descrição", placeholder="Defina contexto, critério e objetivo final...")
        cols = st.columns(2)
        categoria = cols[0].selectbox("Categoria", GOAL_CATEGORIES)
        data_inicio = cols[1].date_input("Data de início", value=date.today())
        prazo = cols[0].date_input("Prazo", value=date.today() + timedelta(days=30))
        status = cols[1].selectbox("Status inicial", GOAL_STATUS_ORDER)
        progresso = st.slider("Percentual de progresso", min_value=0, max_value=100, value=0)
        observacoes = st.text_area("Observações", placeholder="Ex.: checkpoints semanais, métricas de validação...")
        submitted = st.form_submit_button("Registrar meta", use_container_width=True)

    if submitted:
        insert_goal(
            titulo=titulo,
            descricao=descricao,
            categoria=categoria,
            data_inicio=data_inicio.isoformat(),
            prazo=prazo.isoformat(),
            status=status,
            progresso=progresso,
            observacoes=observacoes,
        )
        _invalidate_data_cache()
        st.success("Meta criada com sucesso.")
        st.rerun()


def _render_weight_and_bmi_charts(body_df: pd.DataFrame, key_prefix: str) -> None:
    if body_df.empty:
        st.info("Sem registros corporais para gerar a evolução de peso e IMC.")
        return

    body = body_df.copy()
    body["data"] = pd.to_datetime(body["data"])

    tabs = st.tabs(["Peso", "IMC"])
    with tabs[0]:
        fig = px.line(
            body,
            x="data",
            y="peso",
            markers=True,
            title="Evolução do peso",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        _style_plot(fig)
        _plot_chart(fig, f"{key_prefix}_weight")

    with tabs[1]:
        fig = px.line(
            body,
            x="data",
            y="imc",
            markers=True,
            title="Evolução do IMC",
            color_discrete_sequence=[COLOR_SEQUENCE[1]],
        )
        _style_plot(fig)
        _plot_chart(fig, f"{key_prefix}_bmi")


def _render_calorie_balance_chart(
    food_df: pd.DataFrame,
    activities_df: pd.DataFrame,
    view_mode: str,
    chart_key: str,
) -> None:
    consumed = aggregate_timeseries(
        food_df,
        "calorias",
        date_col="data",
        view_mode=view_mode,
        agg="sum",
    ).rename(columns={"valor": "Consumidas"})
    burned = aggregate_timeseries(
        activities_df,
        "calorias_gastas",
        date_col="data",
        view_mode=view_mode,
        agg="sum",
    ).rename(columns={"valor": "Gastas"})

    merged = pd.merge(
        consumed[["data", "Consumidas"]],
        burned[["data", "Gastas"]],
        on="data",
        how="outer",
    ).fillna(0).sort_values("data")

    if merged.empty:
        st.info("Sem dados suficientes para o comparativo calórico.")
        return

    melted = merged.melt(
        id_vars=["data"],
        value_vars=["Consumidas", "Gastas"],
        var_name="Categoria",
        value_name="Calorias",
    )
    fig = px.bar(
        melted,
        x="data",
        y="Calorias",
        color="Categoria",
        barmode="stack",
        title="Calorias consumidas vs gastas",
        color_discrete_sequence=[COLOR_SEQUENCE[2], COLOR_SEQUENCE[0]],
    )
    _style_plot(fig)
    fig.update_layout(bargap=0.2)
    fig.update_xaxes(
        tickformat="%d/%m" if view_mode != "Mês" else "%m/%y",
        title=None,
    )
    _plot_chart(fig, chart_key)


def _render_activity_frequency_chart(
    activities_df: pd.DataFrame,
    chart_key: str,
) -> None:
    weekly = aggregate_timeseries(
        activities_df,
        "__count__",
        date_col="data",
        view_mode="Semana",
        agg="sum",
    )
    if weekly.empty:
        st.info("Sem treinos suficientes para medir frequência semanal.")
        return

    fig = px.line(
        weekly,
        x="periodo",
        y="valor",
        markers=True,
        title="Frequência de atividades por semana",
        color_discrete_sequence=[COLOR_SEQUENCE[1]],
    )
    _style_plot(fig)
    _plot_chart(fig, chart_key)


def _render_goal_status_chart(
    active_goals: pd.DataFrame,
    archived_goals: pd.DataFrame,
    chart_key: str,
    height: int = 280,
) -> None:
    status_df = summarize_goal_statuses(active_goals, archived_goals)
    if status_df["total"].sum() == 0:
        st.info("Sem metas suficientes para gerar indicadores.")
        return

    fig = px.bar(
        status_df,
        x="status",
        y="total",
        color="status",
        title="Resumo de metas concluídas e em progresso",
        color_discrete_sequence=COLOR_SEQUENCE,
        height=height,
    )
    _style_plot(fig)
    _plot_chart(fig, chart_key)


def _plot_chart(fig: go.Figure, key: str) -> None:
    for trace in fig.data:
        trace_name = getattr(trace, "name", None)
        if trace_name is None or str(trace_name).strip().lower() == "undefined":
            trace.name = ""
    st.plotly_chart(fig, use_container_width=True, key=key, theme=None)


def _style_plot(fig: go.Figure) -> None:
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=12, r=12, t=48, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        legend_title_text="",
        hovermode="closest",
        font=dict(color="#f4fff9"),
        title_font=dict(color="#f4fff9"),
    )
    fig.update_traces(
        line_shape="spline",
        line_smoothing=1.0,
        line_width=3,
        marker_size=7,
        selector=dict(type="scatter"),
    )
    fig.update_xaxes(showgrid=False, color="#95aca4")
    fig.update_yaxes(gridcolor="rgba(0,249,149,0.10)", color="#95aca4")


def _fmt_metric(
    value: float | int | None,
    suffix: str = "",
    digits: int = 1,
) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Sem dados"
    return f"{value:.{digits}f}{suffix}"


def _fmt_delta(
    value: float | None,
    suffix: str = "",
    digits: int = 1,
) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}{suffix}"

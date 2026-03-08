from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

import pandas as pd
import streamlit as st

from biohack_analytics.analytics import build_health_snapshot


def _secret_candidate_keys(key: str) -> list[str]:
    keys = [key]
    if key.startswith("AXIEL_"):
        keys.append(key.removeprefix("AXIEL_"))
    if key.startswith("STOCKPILOT_"):
        keys.append(key.removeprefix("STOCKPILOT_"))
    return keys


def _read_secret_value(*keys: str) -> str | None:
    try:
        secrets = st.secrets
    except Exception:
        return None

    containers: list[Any] = [secrets]
    for section_name in ("axiel", "stockpilot"):
        try:
            section = secrets.get(section_name)
        except Exception:
            section = None
        if section:
            containers.append(section)

    for container in containers:
        for key in keys:
            for candidate in _secret_candidate_keys(key):
                try:
                    value = container.get(candidate)
                except Exception:
                    value = None
                if value not in (None, ""):
                    return str(value).strip()
    return None


def _read_text_setting(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.environ.get(key)
        if value not in (None, ""):
            return str(value).strip()

    secret_value = _read_secret_value(*keys)
    if secret_value not in (None, ""):
        return secret_value
    return default


def _read_int_setting(*keys: str, default: int) -> int:
    value = _read_text_setting(*keys, default=str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_axiel_runtime_config() -> dict[str, Any]:
    api_key = _read_text_setting(
        "AXIEL_TOGETHER_API_KEY",
        "TOGETHER_API_KEY",
        "STOCKPILOT_TOGETHER_API_KEY",
        default="",
    )
    chat_model = _read_text_setting(
        "AXIEL_CHAT_MODEL",
        "STOCKPILOT_CHAT_MODEL",
        default="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    )
    transcribe_model = _read_text_setting(
        "AXIEL_TRANSCRIBE_MODEL",
        "STOCKPILOT_TRANSCRIBE_MODEL",
        default="openai/whisper-large-v3",
    )
    transcribe_language = _read_text_setting(
        "AXIEL_TRANSCRIBE_LANGUAGE",
        "STOCKPILOT_TRANSCRIBE_LANGUAGE",
        default="pt",
    )
    chat_timeout_seconds = _read_int_setting(
        "AXIEL_CHAT_TIMEOUT_SECONDS",
        "STOCKPILOT_CHAT_TIMEOUT_SECONDS",
        default=90,
    )
    transcribe_timeout_seconds = _read_int_setting(
        "AXIEL_TRANSCRIBE_TIMEOUT_SECONDS",
        "STOCKPILOT_TRANSCRIBE_TIMEOUT_SECONDS",
        default=120,
    )
    chat_api_url = _read_text_setting(
        "AXIEL_CHAT_API_URL",
        default="https://api.together.xyz/v1/chat/completions",
    )
    return {
        "provider": "Together",
        "api_key": api_key,
        "api_key_configured": bool(api_key),
        "chat_model": chat_model,
        "transcribe_model": transcribe_model,
        "transcribe_language": transcribe_language,
        "chat_timeout_seconds": chat_timeout_seconds,
        "transcribe_timeout_seconds": transcribe_timeout_seconds,
        "chat_api_url": chat_api_url,
        "mode": "remote" if api_key else "local",
    }

DEFAULT_SUGGESTIONS = [
    "Axiel, como está minha evolução de peso?",
    "Axiel, meu IMC melhorou neste período?",
    "Axiel, estou treinando com consistência?",
    "Axiel, como está meu sono e minha recuperação?",
    "Axiel, que treino faz sentido para esta semana?",
    "Axiel, qual meta eu deveria cadastrar agora?",
    "Axiel, minha frequência cardíaca está estável?",
    "Axiel, como está meu consumo calórico?",
]


def _fmt(value: float | int | None, suffix: str = "", digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "sem dados"
    return f"{value:.{digits}f}{suffix}"


def _direction(delta: float | None, preferred: str = "up") -> str:
    if delta is None:
        return "sem base comparativa"
    if abs(delta) < 0.01:
        return "estável"
    if preferred == "down":
        return "melhorando" if delta < 0 else "subindo"
    return "melhorando" if delta > 0 else "caindo"


def _resolve_user_name(profile: dict[str, Any]) -> str:
    raw_name = str(profile.get("nome") or "").strip()
    if not raw_name or raw_name == "Usuário BIOHACK":
        return "Mariélio"
    return raw_name


def _heart_assessment(snapshot: dict[str, Any]) -> str:
    recent = snapshot["heart_recent_avg"]
    previous = snapshot["heart_previous_avg"]
    if recent is None:
        return "Ainda não há registros cardíacos suficientes para avaliar estabilidade."
    if previous is None:
        return (
            f"Sua frequência média recente está em {_fmt(recent, ' bpm', 0)}. "
            "Ainda falta uma janela anterior para comparar tendência."
        )
    delta = recent - previous
    status = "estável" if abs(delta) <= 5 else "em variação"
    return (
        f"Sua frequência média recente está em {_fmt(recent, ' bpm', 0)} contra "
        f"{_fmt(previous, ' bpm', 0)} na janela anterior. O ritmo está {status}."
    )


def _goal_assessment(snapshot: dict[str, Any]) -> str:
    if snapshot["total_goals"] == 0:
        return "Nenhuma meta foi cadastrada ainda."
    return (
        f"Você concluiu {snapshot['completed_goals']} de {snapshot['total_goals']} metas, "
        f"com taxa de conclusão de {_fmt(snapshot['completion_rate'], '%', 1)}."
    )


def _sleep_assessment(snapshot: dict[str, Any]) -> str:
    if int(snapshot.get("sleep_sessions_30d") or 0) == 0:
        return "Ainda não há registros de sono suficientes para avaliar recuperação e rotina."

    average = snapshot.get("sleep_avg_30d")
    recent = snapshot.get("sleep_recent_avg")
    previous = snapshot.get("sleep_previous_avg")
    adherence = snapshot.get("sleep_target_hit_rate")
    last_night = snapshot.get("sleep_last_duration")
    last_date = snapshot.get("sleep_last_date")

    trend_text = ""
    if recent is not None and previous is not None:
        delta = recent - previous
        if delta > 0.15:
            trend_text = (
                f" A média recente subiu para {_fmt(recent, ' h', 2)} "
                f"contra {_fmt(previous, ' h', 2)} na janela anterior."
            )
        elif delta < -0.15:
            trend_text = (
                f" A média recente caiu para {_fmt(recent, ' h', 2)} "
                f"contra {_fmt(previous, ' h', 2)} na janela anterior."
            )
        else:
            trend_text = (
                f" A média recente está estável em {_fmt(recent, ' h', 2)}."
            )

    last_text = ""
    if last_night is not None and last_date:
        last_text = f" Última noite registrada: {_fmt(last_night, ' h', 2)} em {last_date}."

    return (
        f"Nos últimos 30 dias seu sono médio ficou em {_fmt(average, ' h', 2)} "
        f"e a aderência à meta bateu {_fmt(adherence, '%', 1)}."
        f"{trend_text}{last_text}"
    )


def _activity_assessment(snapshot: dict[str, Any]) -> str:
    if snapshot["sessions_30d"] == 0:
        return "Não encontrei treinos nos últimos 30 dias, então a consistência está baixa."
    return (
        f"Nos últimos 30 dias você registrou {snapshot['sessions_30d']} treinos, "
        f"{_fmt(snapshot['duration_30d'], ' min', 0)} de exercício e "
        f"{_fmt(snapshot['calories_burned_30d'], ' kcal', 0)} gastas. "
        f"A consistência atual está classificada como {snapshot['activity_consistency'].lower()}."
    )


def _nutrition_assessment(snapshot: dict[str, Any]) -> str:
    if snapshot["calories_30d"] == 0:
        return "Ainda não há consumo alimentar suficiente registrado para avaliar sua nutrição."
    average = snapshot["avg_daily_calories"]
    average_text = (
        f"A média diária ficou em {_fmt(average, ' kcal', 0)}. " if average else ""
    )
    return (
        f"Nos últimos 30 dias foram registrados {_fmt(snapshot['calories_30d'], ' kcal', 0)} "
        f"de consumo, com {_fmt(snapshot['proteins_30d'], ' g', 0)} de proteínas, "
        f"{_fmt(snapshot['carbs_30d'], ' g', 0)} de carboidratos e "
        f"{_fmt(snapshot['fats_30d'], ' g', 0)} de gorduras. "
        f"{average_text}Compare esse volume com o gasto calórico para ajustar sua estratégia."
    )


def _body_assessment(snapshot: dict[str, Any]) -> str:
    if snapshot["weight"] is None:
        return "Ainda não há registros corporais suficientes para avaliar peso e IMC."
    weight_trend = _direction(snapshot["weight_delta"], preferred="down")
    bmi_trend = _direction(snapshot["bmi_delta"], preferred="down")
    goal_text = ""
    if snapshot["goal_gap"] is not None and snapshot["goal_weight"] is not None:
        goal_text = (
            f" Sua meta atual é {_fmt(snapshot['goal_weight'], ' kg', 1)} e a distância "
            f"para ela está em {_fmt(abs(snapshot['goal_gap']), ' kg', 1)}."
        )
    return (
        f"Seu último peso registrado é {_fmt(snapshot['weight'], ' kg', 1)} e o IMC atual "
        f"está em {_fmt(snapshot['bmi'], '', 2)}. O peso vem {weight_trend} e o IMC está "
        f"{bmi_trend}.{goal_text}"
    )


def _overall_assessment(snapshot: dict[str, Any]) -> str:
    parts = [
        _body_assessment(snapshot),
        _sleep_assessment(snapshot),
        _heart_assessment(snapshot),
        _activity_assessment(snapshot),
        _nutrition_assessment(snapshot),
        _goal_assessment(snapshot),
    ]
    return " ".join(parts)


def _training_recommendation(snapshot: dict[str, Any]) -> str:
    sessions = int(snapshot["sessions_30d"] or 0)
    duration = float(snapshot["duration_30d"] or 0)
    goal_gap = snapshot["goal_gap"]

    if sessions == 0:
        return (
            "Sugestão de treino: recomece com 3 sessões leves a moderadas por semana, "
            "alternando caminhada acelerada, bicicleta ou treino de força básico."
        )

    if sessions < 8:
        return (
            "Sugestão de treino: suba para 3 ou 4 sessões por semana, com 2 treinos de força "
            "e 1 ou 2 sessões cardiovasculares de 30 a 45 minutos."
        )

    if goal_gap is not None and goal_gap > 0:
        return (
            "Sugestão de treino: mantenha o volume atual e priorize uma combinação de força "
            "com cardio intervalado leve a moderado para melhorar gasto calórico sem perder consistência."
        )

    if duration >= 600:
        return (
            "Sugestão de treino: preserve a frequência atual e organize microciclos com 2 dias de força, "
            "2 dias de cardio e 1 sessão regenerativa."
        )

    return (
        "Sugestão de treino: mantenha consistência semanal e ajuste intensidade conforme recuperação, "
        "alternando força, mobilidade e cardio."
    )


def _goal_suggestion(snapshot: dict[str, Any]) -> str:
    if snapshot["sessions_30d"] < 8:
        return (
            "Meta sugerida: completar pelo menos 3 treinos por semana durante as próximas 4 semanas."
        )

    if snapshot["weight"] is not None and snapshot["goal_gap"] is not None and snapshot["goal_gap"] > 0:
        return (
            f"Meta sugerida: reduzir {_fmt(min(snapshot['goal_gap'], 2.0), ' kg', 1)} "
            "com consistência de treino e monitoramento alimentar nas próximas 6 semanas."
        )

    if snapshot["calories_30d"] == 0:
        return "Meta sugerida: registrar a alimentação diariamente por 14 dias para gerar base analítica melhor."

    return "Meta sugerida: elevar sua taxa de metas concluídas com um objetivo mensurável de performance nas próximas 4 semanas."


def _sleep_recommendation(snapshot: dict[str, Any]) -> str:
    if int(snapshot.get("sleep_sessions_30d") or 0) == 0:
        return "Sugestão de sono: registrar horário de dormir e acordar todos os dias nas próximas 2 semanas."

    adherence = float(snapshot.get("sleep_target_hit_rate") or 0.0)
    average = float(snapshot.get("sleep_avg_30d") or 0.0)
    if adherence < 70:
        return (
            "Sugestão de sono: estabilize a rotina noturna e proteja um bloco fixo de descanso para "
            "elevar a aderência da meta antes de subir intensidade de treino."
        )
    if average < 6.0:
        return (
            "Sugestão de sono: tente colocar pelo menos 20 a 30 minutos a mais por noite antes de aumentar carga de treino."
        )
    return (
        "Sugestão de sono: sua base de recuperação está utilizável; mantenha regularidade e ajuste treino pesado "
        "nos dias após noites mais curtas."
    )


def _recent_records_block(
    title: str,
    df: pd.DataFrame,
    columns: list[str],
    limit: int = 5,
) -> str:
    if df.empty:
        return f"{title}:\n- sem registros"

    prepared = df.copy().tail(limit)
    rows: list[str] = []
    for _, row in prepared.iterrows():
        parts = []
        for column in columns:
            if column not in prepared.columns:
                continue
            value = row[column]
            if pd.isna(value):
                continue
            parts.append(f"{column}={value}")
        if parts:
            rows.append("- " + " | ".join(parts))

    if not rows:
        return f"{title}:\n- sem registros"
    return f"{title}:\n" + "\n".join(rows)


def _build_profile_context(profile: dict[str, Any], profile_name: str) -> str:
    return (
        f"Nome do usuário: {profile_name}\n"
        f"Peso meta: {_fmt(profile.get('peso_meta'), ' kg', 1)}\n"
        f"Email: {profile.get('email') or 'não informado'}\n"
        f"Data de nascimento: {profile.get('data_nascimento') or 'não informada'}"
    )


def _build_snapshot_context(snapshot: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Peso atual: {_fmt(snapshot['weight'], ' kg', 1)}",
            f"Delta de peso: {_fmt(snapshot['weight_delta'], ' kg', 1)}",
            f"IMC atual: {_fmt(snapshot['bmi'], '', 2)}",
            f"Delta de IMC: {_fmt(snapshot['bmi_delta'], '', 2)}",
            f"Treinos 30d: {snapshot['sessions_30d']}",
            f"Duração 30d: {_fmt(snapshot['duration_30d'], ' min', 0)}",
            f"Calorias gastas 30d: {_fmt(snapshot['calories_burned_30d'], ' kcal', 0)}",
            f"Calorias consumidas 30d: {_fmt(snapshot['calories_30d'], ' kcal', 0)}",
            f"Média diária de calorias: {_fmt(snapshot['avg_daily_calories'], ' kcal', 0)}",
            f"Proteínas 30d: {_fmt(snapshot['proteins_30d'], ' g', 0)}",
            f"Carboidratos 30d: {_fmt(snapshot['carbs_30d'], ' g', 0)}",
            f"Gorduras 30d: {_fmt(snapshot['fats_30d'], ' g', 0)}",
            f"Noites registradas 30d: {snapshot['sleep_sessions_30d']}",
            f"Sono médio 30d: {_fmt(snapshot['sleep_avg_30d'], ' h', 2)}",
            f"Sono recente: {_fmt(snapshot['sleep_recent_avg'], ' h', 2)}",
            f"Sono anterior: {_fmt(snapshot['sleep_previous_avg'], ' h', 2)}",
            f"Aderência da meta de sono: {_fmt(snapshot['sleep_target_hit_rate'], '%', 1)}",
            f"Noites na meta 30d: {snapshot['sleep_nights_on_target_30d']}",
            f"Última noite: {_fmt(snapshot['sleep_last_duration'], ' h', 2)}",
            f"Data da última noite: {snapshot['sleep_last_date'] or 'sem dados'}",
            f"Frequência cardíaca média recente: {_fmt(snapshot['heart_recent_avg'], ' bpm', 0)}",
            f"Frequência cardíaca média anterior: {_fmt(snapshot['heart_previous_avg'], ' bpm', 0)}",
            f"Metas concluídas: {snapshot['completed_goals']}",
            f"Metas totais: {snapshot['total_goals']}",
            f"Taxa de conclusão: {_fmt(snapshot['completion_rate'], '%', 1)}",
            f"Melhor período: {snapshot['best_period']}",
            f"Gap para meta de peso: {_fmt(snapshot['goal_gap'], ' kg', 1)}",
        ]
    )


def _build_context_payload(
    profile: dict[str, Any],
    profile_name: str,
    snapshot: dict[str, Any],
    datasets: dict[str, pd.DataFrame],
) -> str:
    sections = [
        "PERFIL\n" + _build_profile_context(profile, profile_name),
        "RESUMO ANALÍTICO\n" + _build_snapshot_context(snapshot),
        _recent_records_block(
            "METAS ATIVAS",
            datasets.get("metas", pd.DataFrame()),
            ["titulo", "categoria", "status", "progresso", "prazo"],
            limit=5,
        ),
        _recent_records_block(
            "ATIVIDADES RECENTES",
            datasets.get("atividades_fisicas", pd.DataFrame()),
            ["data", "tipo_atividade", "duracao_minutos", "intensidade", "calorias_gastas", "distancia_km"],
            limit=5,
        ),
        _recent_records_block(
            "ALIMENTAÇÃO RECENTE",
            datasets.get("alimentacao", pd.DataFrame()),
            ["data", "refeicao", "alimento", "calorias", "proteinas", "carboidratos", "gorduras"],
            limit=5,
        ),
        _recent_records_block(
            "SONO RECENTE",
            datasets.get("registros_sono", pd.DataFrame()),
            ["data", "hora_dormir", "hora_acordar", "duracao_horas", "observacoes"],
            limit=7,
        ),
        _recent_records_block(
            "REGISTROS CORPORAIS RECENTES",
            datasets.get("dados_corporais", pd.DataFrame()),
            ["data", "peso", "imc", "altura"],
            limit=5,
        ),
        _recent_records_block(
            "REGISTROS CARDÍACOS RECENTES",
            datasets.get("registros_cardiacos", pd.DataFrame()),
            ["data", "frequencia_media", "frequencia_repouso", "frequencia_maxima", "frequencia_minima"],
            limit=5,
        ),
        _recent_records_block(
            "METAS FINALIZADAS",
            datasets.get("metas_finalizadas", pd.DataFrame()),
            ["titulo", "categoria", "status", "progresso", "situacao_final", "data_finalizacao"],
            limit=5,
        ),
    ]
    return "\n\n".join(section for section in sections if section)


def _build_axiel_system_prompt(profile_name: str) -> str:
    return f"""
Você é Axiel, a inteligência pessoal de saúde e performance do usuário {profile_name}.

Sua função:
- agir como assistente pessoal e analista de performance;
- interpretar os dados corporais, cardíacos, nutricionais, de treino e metas;
- sugerir treinos, metas e próximos passos realistas;
- responder sempre em português do Brasil;
- falar com objetividade, clareza e postura profissional;
- tratar o usuário pelo nome {profile_name} quando fizer sentido;
- usar apenas os dados fornecidos no contexto;
- dizer explicitamente quando faltarem dados;
- evitar inventar números, diagnósticos ou certezas médicas.
- antes de afirmar ausência de dados, verifique com rigor as seções RESUMO ANALÍTICO, SONO RECENTE,
  REGISTROS CARDÍACOS RECENTES, ATIVIDADES RECENTES, ALIMENTAÇÃO RECENTE, METAS ATIVAS e METAS FINALIZADAS;
- ao recomendar treino, cruzar recuperação do sono, carga recente, alimentação, coração e metas;
- ao falar de metas, considerar metas ativas e finalizadas para entender ritmo e histórico.

Estilo esperado:
- primeiro faça uma leitura curta do cenário;
- depois entregue recomendações práticas;
- quando útil, proponha uma meta clara e mensurável;
- seja direto, útil e personalizado.
""".strip()


def _history_to_messages(history_df: pd.DataFrame, limit: int = 8) -> list[dict[str, str]]:
    if history_df.empty:
        return []

    messages: list[dict[str, str]] = []
    for _, row in history_df.tail(limit).iterrows():
        role = "assistant" if row.get("role") == "assistant" else "user"
        content = str(row.get("mensagem") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    return messages


def _call_together_chat(messages: list[dict[str, str]], config: dict[str, Any]) -> str:
    payload = {
        "model": config["chat_model"],
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 900,
    }
    http_request = request.Request(
        config["chat_api_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BIOHACK-ANALYTICS/1.0",
        },
        method="POST",
    )
    with request.urlopen(http_request, timeout=config["chat_timeout_seconds"]) as response:
        body = json.loads(response.read().decode("utf-8"))

    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError("Resposta vazia da API de chat.")

    message = choices[0].get("message", {})
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("Conteúdo vazio retornado pela API de chat.")
    return content


def _generate_remote_response(
    question: str,
    profile: dict[str, Any],
    profile_name: str,
    snapshot: dict[str, Any],
    datasets: dict[str, pd.DataFrame],
) -> str | None:
    config = get_axiel_runtime_config()
    if not config["api_key_configured"]:
        return None

    history_messages = _history_to_messages(datasets.get("historico_axiel", pd.DataFrame()))
    context_payload = _build_context_payload(profile, profile_name, snapshot, datasets)
    messages = [
        {"role": "system", "content": _build_axiel_system_prompt(profile_name)},
        {
            "role": "system",
            "content": "Contexto analítico atual do usuário:\n\n" + context_payload,
        },
        *history_messages,
        {"role": "user", "content": question.strip()},
    ]

    try:
        return _call_together_chat(messages, config)
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError):
        return None


def _response_contradicts_context(
    question: str,
    response: str,
    snapshot: dict[str, Any],
) -> bool:
    normalized_question = question.lower()
    normalized_response = response.lower()
    no_data_markers = (
        "não há informa",
        "nao ha informa",
        "não é possível avaliar",
        "nao e possivel avaliar",
        "sem informações",
        "sem dados",
    )
    if not any(marker in normalized_response for marker in no_data_markers):
        return False

    checks = [
        (("sono", "dorm", "acord"), int(snapshot.get("sleep_sessions_30d") or 0) > 0),
        (("card", "cora", "bpm", "frequ"), snapshot.get("heart_recent_avg") is not None),
        (("treino", "atividade", "exerc"), int(snapshot.get("sessions_30d") or 0) > 0),
        (("alimenta", "caloria", "prote", "carbo", "gord"), float(snapshot.get("calories_30d") or 0) > 0),
        (("meta", "objetivo"), int(snapshot.get("total_goals") or 0) > 0),
    ]
    return any(
        any(keyword in normalized_question for keyword in keywords) and has_data
        for keywords, has_data in checks
    )


def _generate_local_response(
    question: str,
    profile_name: str,
    snapshot: dict[str, Any],
) -> str:
    normalized = question.lower().strip()
    if not normalized:
        return (
            f"{profile_name}, envie uma pergunta sobre peso, sono, treinos, alimentação, coração ou metas."
        )

    if any(keyword in normalized for keyword in ["peso", "imc", "corporal"]):
        response = _body_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["sono", "dorm", "acord", "recuper"]):
        response = _sleep_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["treino", "atividade", "consist", "exerc"]):
        response = _activity_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["caloria", "aliment", "refei", "prote", "carbo", "gord"]):
        response = _nutrition_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["meta", "objetivo", "kanban"]):
        response = _goal_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["card", "cora", "frequ", "bpm"]):
        response = _heart_assessment(snapshot)
    elif any(keyword in normalized for keyword in ["melhor período", "desempenho", "performance"]):
        response = (
            f"Seu melhor período registrado até aqui foi {snapshot['best_period']}, "
            "considerando o maior volume mensal de treino."
        )
    else:
        response = _overall_assessment(snapshot)

    recommendation = _training_recommendation(snapshot)
    sleep_recommendation = _sleep_recommendation(snapshot)
    goal_suggestion = _goal_suggestion(snapshot)
    return (
        f"{profile_name}, {response}\n\n"
        f"Recomendação prática: {recommendation}\n\n"
        f"{sleep_recommendation}\n\n"
        f"{goal_suggestion}"
    )


def generate_axiel_response(
    question: str,
    profile: dict[str, Any],
    datasets: dict[str, pd.DataFrame],
) -> str:
    snapshot = build_health_snapshot(
        profile,
        datasets.get("dados_corporais", pd.DataFrame()),
        datasets.get("registros_cardiacos", pd.DataFrame()),
        datasets.get("atividades_fisicas", pd.DataFrame()),
        datasets.get("alimentacao", pd.DataFrame()),
        datasets.get("registros_sono", pd.DataFrame()),
        datasets.get("metas", pd.DataFrame()),
        datasets.get("metas_finalizadas", pd.DataFrame()),
    )
    profile_name = _resolve_user_name(profile)

    remote_response = _generate_remote_response(
        question=question,
        profile=profile,
        profile_name=profile_name,
        snapshot=snapshot,
        datasets=datasets,
    )
    if remote_response and not _response_contradicts_context(question, remote_response, snapshot):
        return remote_response.strip()

    local_response = _generate_local_response(question, profile_name, snapshot)
    return local_response

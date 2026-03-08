from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from biohack_analytics.database import (
    calculate_imc,
    calculate_sleep_duration_hours,
    get_connection,
    init_db,
    update_user_profile,
)


USER_NAME = "Mariélio"
USER_EMAIL = ""
USER_BIRTH_DATE = "1995-08-15"
USER_GOAL_WEIGHT = 75.0
START_DATE = date(2026, 2, 1)

BREAKFASTS = [
    ("Ovos com aveia", 285.0, 425.0, 29.0, 34.0, 18.0, "Cafe proteico"),
    ("Iogurte com granola", 260.0, 355.0, 20.0, 39.0, 11.0, "Inicio do dia"),
    ("Vitamina de banana com whey", 340.0, 395.0, 32.0, 41.0, 8.0, "Pre-treino"),
    ("Tapioca com queijo e ovos", 295.0, 435.0, 27.0, 39.0, 15.0, "Energia moderada"),
    ("Pao integral com ovos", 265.0, 410.0, 24.0, 36.0, 14.0, "Rotina padrao"),
    ("Aveia com frutas", 275.0, 365.0, 17.0, 49.0, 8.0, "Manha leve"),
    ("Panqueca proteica", 260.0, 405.0, 31.0, 32.0, 11.0, "Cafe reforcado"),
]

LUNCHES = [
    ("Frango com arroz e legumes", 420.0, 610.0, 44.0, 56.0, 16.0, "Refeicao principal"),
    ("Carne magra com arroz integral", 430.0, 640.0, 42.0, 58.0, 18.0, "Boa saciedade"),
    ("Peixe com quinoa", 410.0, 560.0, 39.0, 48.0, 17.0, "Almoco limpo"),
    ("Macarrao integral com frango", 470.0, 690.0, 43.0, 74.0, 14.0, "Reposicao de glicogenio"),
    ("Patinho moido com feijao", 450.0, 650.0, 46.0, 52.0, 19.0, "Boa distribuicao"),
    ("Frango com batata e brocolis", 440.0, 620.0, 45.0, 50.0, 17.0, "Almoco equilibrado"),
    ("Peito de peru com arroz", 430.0, 610.0, 41.0, 57.0, 13.0, "Boa digestao"),
]

DINNERS = [
    ("Salmao com batata doce", 360.0, 540.0, 38.0, 42.0, 20.0, "Jantar leve"),
    ("Omelete com salada", 300.0, 410.0, 31.0, 15.0, 24.0, "Baixo carbo"),
    ("Frango grelhado com pure", 340.0, 500.0, 41.0, 36.0, 15.0, "Pos-treino"),
    ("Tilapia com legumes", 320.0, 470.0, 36.0, 22.0, 18.0, "Jantar leve"),
    ("Sopa de legumes com frango", 330.0, 390.0, 30.0, 26.0, 12.0, "Jantar seco"),
    ("Wrap proteico", 290.0, 430.0, 29.0, 34.0, 14.0, "Jantar rapido"),
    ("Carne com salada e mandioca", 350.0, 520.0, 34.0, 35.0, 21.0, "Fechamento do dia"),
]

ACTIVITY_TEMPLATES = {
    0: ("Musculação", 56, "Alta", 335.0, 0.0, "Treino de forca"),
    1: ("Corrida", 43, "Moderada", 405.0, 6.1, "Ritmo constante"),
    2: ("Bike", 54, "Moderada", 395.0, 15.4, "Cardio progressivo"),
    3: ("Caminhada", 48, "Leve", 225.0, 5.0, "Recuperacao ativa"),
    4: ("Musculação", 52, "Alta", 320.0, 0.0, "Treino misto"),
    5: ("Corrida", 45, "Alta", 430.0, 6.6, "Ritmo forte"),
    6: ("Mobilidade", 30, "Leve", 95.0, 0.0, "Alongamento e core"),
}

ACTIVITY_OVERRIDES = {
    "2026-02-23": ("Corrida", 47, "Alta", 438.0, 6.9, "Ritmo forte"),
    "2026-03-06": ("Corrida", 46, "Alta", 432.0, 6.7, "Ritmo forte"),
}

CARDIAC_NOTES = [
    "Treino de corrida",
    "Musculação com cardio no fim",
    "Bike moderada",
    "Caminhada de recuperacao",
    "Treino misto",
    "Corrida com ritmo forte",
    "Recuperacao ativa",
]

SLEEP_TEMPLATES_FEBRUARY = [
    ("23:35", "07:45", "Meta de ferias atingida"),
    ("23:40", "08:00", "Sono completo"),
    ("23:50", "08:05", "Boa recuperacao"),
    ("23:30", "07:50", "Rotina descansada"),
    ("23:45", "08:10", "Noite bem aproveitada"),
]

SLEEP_TEMPLATES_MARCH = [
    ("00:00", "06:05", "Meta atual cumprida"),
    ("23:55", "06:05", "Sono ajustado"),
    ("00:10", "06:20", "Duracao dentro da meta"),
    ("00:05", "06:10", "Rotina atual consistente"),
    ("23:50", "06:00", "Meta minima atendida"),
]


def iter_dates(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    return [start_date + timedelta(days=offset) for offset in range(days + 1)]


def build_body_records(dates: list[date]) -> list[tuple[str, int, float, float, float]]:
    start_weight = 99.6
    end_weight = 97.0
    offsets = [0.18, 0.10, 0.06, 0.02, 0.05, -0.04, -0.07]
    total_steps = max(len(dates) - 1, 1)
    records: list[tuple[str, int, float, float, float]] = []

    for index, current_date in enumerate(dates):
        progress = index / total_steps
        base_weight = start_weight + (end_weight - start_weight) * progress
        weight = round(base_weight + offsets[index % len(offsets)], 1)
        if index == len(dates) - 1:
            weight = 97.0
        imc = calculate_imc(weight, 1.72)
        records.append((current_date.isoformat(), 30, weight, 1.72, imc))
    return records


def build_cardiac_records(
    dates: list[date],
) -> list[tuple[str, int, int, int, int, str]]:
    means = [value for value in (92, 94, 91, 95, 93, 90, 96) for _ in (0,)]
    means = [means[index % len(means)] for index in range(len(dates))]
    target_total = len(dates) * 93
    difference = target_total - sum(means)
    cursor = 0
    while difference != 0:
        step = 1 if difference > 0 else -1
        if 88 <= means[cursor] + step <= 99:
            means[cursor] += step
            difference -= step
        cursor = (cursor + 1) % len(means)

    rest_pattern = [63, 62, 61, 64, 62, 60, 61]
    max_pattern = [57, 60, 54, 62, 58, 55, 59]
    min_pattern = [7, 7, 6, 8, 7, 7, 6]
    records: list[tuple[str, int, int, int, int, str]] = []

    for index, current_date in enumerate(dates):
        avg = means[index]
        rest = rest_pattern[index % len(rest_pattern)]
        max_bpm = avg + max_pattern[index % len(max_pattern)]
        min_bpm = rest - min_pattern[index % len(min_pattern)]
        note = CARDIAC_NOTES[index % len(CARDIAC_NOTES)]
        records.append((current_date.isoformat(), avg, rest, max_bpm, min_bpm, note))
    return records


def build_activity_records(
    dates: list[date],
) -> list[tuple[str, str, int, str, float, float, str]]:
    records: list[tuple[str, str, int, str, float, float, str]] = []
    for current_date in dates:
        override = ACTIVITY_OVERRIDES.get(current_date.isoformat())
        if override is not None:
            tipo, duracao, intensidade, calorias, distancia, observacoes = override
        else:
            tipo, duracao, intensidade, calorias, distancia, observacoes = ACTIVITY_TEMPLATES[
                current_date.weekday()
            ]
        records.append(
            (
                current_date.isoformat(),
                tipo,
                duracao,
                intensidade,
                calorias,
                distancia,
                observacoes,
            )
        )
    return records


def build_food_records(
    dates: list[date],
) -> list[tuple[str, str, str, float, float, float, float, float, str]]:
    records: list[tuple[str, str, str, float, float, float, float, float, str]] = []
    for index, current_date in enumerate(dates):
        breakfast = BREAKFASTS[index % len(BREAKFASTS)]
        lunch = LUNCHES[(index + 2) % len(LUNCHES)]
        dinner = DINNERS[(index + 4) % len(DINNERS)]
        for refeicao, template in (
            ("Café da manhã", breakfast),
            ("Almoço", lunch),
            ("Jantar", dinner),
        ):
            alimento, quantidade, calorias, proteinas, carbs, gorduras, observacoes = template
            records.append(
                (
                    current_date.isoformat(),
                    refeicao,
                    alimento,
                    quantidade,
                    calorias,
                    proteinas,
                    carbs,
                    gorduras,
                    observacoes,
                )
            )
    return records


def build_sleep_records(
    dates: list[date],
) -> list[tuple[str, str, str, float, str]]:
    records: list[tuple[str, str, str, float, str]] = []
    for index, current_date in enumerate(dates):
        if current_date < date(2026, 3, 1):
            templates = SLEEP_TEMPLATES_FEBRUARY
        else:
            templates = SLEEP_TEMPLATES_MARCH
        hora_dormir, hora_acordar, observacoes = templates[index % len(templates)]
        duration_hours = calculate_sleep_duration_hours(hora_dormir, hora_acordar)
        records.append(
            (
                current_date.isoformat(),
                hora_dormir,
                hora_acordar,
                duration_hours,
                observacoes,
            )
        )
    return records


def reseed_daily_data(end_date: date) -> dict[str, int]:
    dates = iter_dates(START_DATE, end_date)
    body_records = build_body_records(dates)
    cardiac_records = build_cardiac_records(dates)
    activity_records = build_activity_records(dates)
    food_records = build_food_records(dates)
    sleep_records = build_sleep_records(dates)

    with get_connection() as connection:
        for table in (
            "dados_corporais",
            "registros_cardiacos",
            "atividades_fisicas",
            "alimentacao",
            "registros_sono",
        ):
            connection.execute(
                f"DELETE FROM {table} WHERE user_id = 1 AND data >= ?",
                (START_DATE.isoformat(),),
            )

        connection.executemany(
            """
            INSERT INTO dados_corporais (user_id, data, idade, peso, altura, imc)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            body_records,
        )
        connection.executemany(
            """
            INSERT INTO registros_cardiacos (
                user_id,
                data,
                frequencia_media,
                frequencia_repouso,
                frequencia_maxima,
                frequencia_minima,
                observacoes
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            """,
            cardiac_records,
        )
        connection.executemany(
            """
            INSERT INTO atividades_fisicas (
                user_id,
                data,
                tipo_atividade,
                duracao_minutos,
                intensidade,
                calorias_gastas,
                distancia_km,
                observacoes
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            activity_records,
        )
        connection.executemany(
            """
            INSERT INTO alimentacao (
                user_id,
                data,
                refeicao,
                alimento,
                quantidade,
                calorias,
                proteinas,
                carboidratos,
                gorduras,
                observacoes
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            food_records,
        )
        connection.executemany(
            """
            INSERT INTO registros_sono (
                user_id,
                data,
                hora_dormir,
                hora_acordar,
                duracao_horas,
                observacoes
            )
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            sleep_records,
        )

    return {
        "dados_corporais": len(body_records),
        "registros_cardiacos": len(cardiac_records),
        "atividades_fisicas": len(activity_records),
        "alimentacao": len(food_records),
        "registros_sono": len(sleep_records),
    }


def main() -> None:
    init_db()
    update_user_profile(
        nome=USER_NAME,
        email=USER_EMAIL,
        data_nascimento=USER_BIRTH_DATE,
        peso_meta=USER_GOAL_WEIGHT,
    )
    end_date = date.today() - timedelta(days=1)
    if end_date < START_DATE:
        raise SystemExit("Periodo invalido para seed diario.")

    counts = reseed_daily_data(end_date)
    print("Seed diario concluido.")
    print(f"Periodo: {START_DATE.isoformat()} ate {end_date.isoformat()}")
    print(counts)


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from biohack_analytics.database import get_connection, init_db, update_user_profile


USER_NAME = "Usuário BIOHACK"
USER_EMAIL = ""
USER_BIRTH_DATE = "1995-08-15"
USER_GOAL_WEIGHT = 75.0
START_DATE = "2026-02-01"
END_DATE = "2026-02-28"


BODY_RECORDS = [
    ("2026-02-01", 30, 78.0, 1.72, 26.37),
    ("2026-02-08", 30, 77.8, 1.72, 26.30),
    ("2026-02-15", 30, 77.6, 1.72, 26.23),
    ("2026-02-22", 30, 77.4, 1.72, 26.16),
    ("2026-02-28", 30, 77.2, 1.72, 26.10),
]


CARDIAC_RECORDS = [
    ("2026-02-02", 79, 63, 146, 56, "Treino leve de corrida"),
    ("2026-02-05", 82, 62, 154, 55, "Musculação com cardio no fim"),
    ("2026-02-08", 77, 61, 143, 54, "Caminhada longa"),
    ("2026-02-11", 84, 64, 159, 57, "Treino intervalado"),
    ("2026-02-14", 80, 62, 151, 55, "Bike moderada"),
    ("2026-02-18", 78, 60, 147, 53, "Recuperação ativa"),
    ("2026-02-22", 83, 63, 161, 56, "Corrida com ritmo forte"),
    ("2026-02-26", 76, 60, 142, 52, "Semana de menor carga"),
]


ACTIVITY_RECORDS = [
    ("2026-02-02", "Corrida", 42, "Moderada", 390, 6.2, "Ritmo constante"),
    ("2026-02-04", "Musculação", 55, "Alta", 310, 0.0, "Treino de membros superiores"),
    ("2026-02-06", "Caminhada", 48, "Leve", 210, 4.4, "Recuperação ativa"),
    ("2026-02-08", "Bike", 50, "Moderada", 360, 14.0, "Pedal urbano"),
    ("2026-02-10", "Corrida", 38, "Alta", 405, 5.8, "Tiros curtos"),
    ("2026-02-12", "Musculação", 60, "Alta", 335, 0.0, "Treino de pernas"),
    ("2026-02-15", "Corrida", 44, "Moderada", 398, 6.4, "Treino contínuo"),
    ("2026-02-17", "Mobilidade", 30, "Leve", 95, 0.0, "Alongamento e core"),
    ("2026-02-19", "Bike", 58, "Moderada", 415, 16.2, "Cardio progressivo"),
    ("2026-02-21", "Musculação", 52, "Alta", 320, 0.0, "Treino misto"),
    ("2026-02-23", "Corrida", 46, "Alta", 430, 6.8, "Ritmo forte"),
    ("2026-02-26", "Caminhada", 54, "Leve", 225, 5.2, "Fechamento da semana"),
]


FOOD_RECORDS = [
    ("2026-02-01", "Café da manhã", "Ovos com aveia", 280, 420, 28, 34, 18, "Café proteico"),
    ("2026-02-01", "Almoço", "Frango com arroz e legumes", 420, 610, 44, 56, 16, "Refeição principal"),
    ("2026-02-01", "Jantar", "Salmão com batata doce", 360, 540, 38, 42, 20, "Jantar leve"),
    ("2026-02-04", "Café da manhã", "Iogurte com granola", 260, 350, 20, 38, 11, "Início do dia"),
    ("2026-02-04", "Almoço", "Carne magra com arroz integral", 430, 640, 42, 58, 18, "Boa saciedade"),
    ("2026-02-04", "Jantar", "Omelete com salada", 300, 410, 31, 15, 24, "Baixo carbo"),
    ("2026-02-08", "Café da manhã", "Vitamina de banana com whey", 350, 390, 32, 40, 8, "Pré-treino"),
    ("2026-02-08", "Almoço", "Peixe com quinoa", 410, 560, 39, 48, 17, "Almoço limpo"),
    ("2026-02-08", "Jantar", "Frango grelhado com purê", 340, 500, 41, 36, 15, "Pós-treino"),
    ("2026-02-12", "Café da manhã", "Tapioca com queijo e ovos", 290, 430, 27, 39, 15, "Energia moderada"),
    ("2026-02-12", "Almoço", "Macarrão integral com frango", 470, 690, 43, 74, 14, "Reposição de glicogênio"),
    ("2026-02-12", "Jantar", "Tilápia com legumes", 320, 470, 36, 22, 18, "Jantar leve"),
    ("2026-02-16", "Café da manhã", "Pão integral com ovos", 260, 410, 24, 36, 14, "Rotina padrão"),
    ("2026-02-16", "Almoço", "Patinho moído com feijão", 450, 650, 46, 52, 19, "Boa distribuição"),
    ("2026-02-16", "Jantar", "Sopa de legumes com frango", 330, 390, 30, 26, 12, "Jantar seco"),
    ("2026-02-20", "Café da manhã", "Aveia com frutas", 270, 360, 17, 49, 8, "Manhã leve"),
    ("2026-02-20", "Almoço", "Frango com batata e brócolis", 440, 620, 45, 50, 17, "Almoço equilibrado"),
    ("2026-02-20", "Jantar", "Wrap proteico", 290, 430, 29, 34, 14, "Jantar rápido"),
    ("2026-02-24", "Café da manhã", "Omelete com frutas", 250, 340, 23, 24, 13, "Café leve"),
    ("2026-02-24", "Almoço", "Peito de peru com arroz", 430, 610, 41, 57, 13, "Boa digestão"),
    ("2026-02-24", "Jantar", "Carne com salada e mandioca", 350, 520, 34, 35, 21, "Fechamento do dia"),
    ("2026-02-28", "Café da manhã", "Panqueca proteica", 260, 400, 31, 32, 11, "Café reforçado"),
    ("2026-02-28", "Almoço", "Frango ao forno com arroz", 450, 630, 44, 59, 15, "Almoço de fim de semana"),
    ("2026-02-28", "Jantar", "Sopa cremosa com carne", 320, 450, 28, 28, 17, "Jantar confortável"),
]


ACTIVE_GOALS = [
    (
        "Melhorar consistência de treino",
        "Manter pelo menos 3 treinos por semana durante fevereiro.",
        "Performance",
        "2026-02-01",
        "2026-03-15",
        "Em Andamento",
        72,
        "Rotina evoluindo bem, com boa distribuição semanal.",
        "2026-02-01 08:00:00",
    ),
    (
        "Reduzir peso corporal",
        "Atingir 76.5 kg mantendo rotina alimentar mais consistente.",
        "Peso",
        "2026-02-03",
        "2026-03-31",
        "Iniciado",
        48,
        "Queda gradual ao longo de fevereiro.",
        "2026-02-03 09:30:00",
    ),
]


ARCHIVED_GOALS = [
    (
        1001,
        "Registrar alimentação por 21 dias",
        "Criar o hábito de registrar refeições e macros com regularidade.",
        "Nutrição",
        "2026-02-01",
        "2026-02-28",
        "Concluído",
        100,
        "Concluída com sucesso",
        "Hábito consolidado no fim do mês.",
        "2026-02-01 07:15:00",
        "2026-02-28 21:10:00",
    ),
]


TEXT_NORMALIZATION = {
    "usuarios": {
        "nome": {
            "Usuario BIOHACK": "Usuário BIOHACK",
        }
    },
    "registros_cardiacos": {
        "observacoes": {
            "Musculacao com cardio no fim": "Musculação com cardio no fim",
            "Recuperacao ativa": "Recuperação ativa",
        }
    },
    "atividades_fisicas": {
        "tipo_atividade": {
            "Musculacao": "Musculação",
        },
        "observacoes": {
            "Recuperacao ativa": "Recuperação ativa",
            "Treino continuo": "Treino contínuo",
        },
    },
    "alimentacao": {
        "refeicao": {
            "Cafe da manha": "Café da manhã",
            "Almoco": "Almoço",
        },
        "alimento": {
            "Frango grelhado com pure": "Frango grelhado com purê",
            "Macarrao integral com frango": "Macarrão integral com frango",
            "Tilapia com legumes": "Tilápia com legumes",
            "Pao integral com ovos": "Pão integral com ovos",
            "Patinho moido com feijao": "Patinho moído com feijão",
            "Frango com batata e brocolis": "Frango com batata e brócolis",
        },
        "observacoes": {
            "Cafe proteico": "Café proteico",
            "Refeicao principal": "Refeição principal",
            "Inicio do dia": "Início do dia",
            "Pre treino": "Pré-treino",
            "Almoco limpo": "Almoço limpo",
            "Pos treino": "Pós-treino",
            "Reposicao de glicogenio": "Reposição de glicogênio",
            "Rotina padrao": "Rotina padrão",
            "Boa distribuicao": "Boa distribuição",
            "Manha leve": "Manhã leve",
            "Almoco equilibrado": "Almoço equilibrado",
            "Jantar rapido": "Jantar rápido",
            "Cafe leve": "Café leve",
            "Boa digestao": "Boa digestão",
            "Cafe reforcado": "Café reforçado",
            "Almoco de fim de semana": "Almoço de fim de semana",
            "Jantar confortavel": "Jantar confortável",
        },
    },
    "metas": {
        "titulo": {
            "Melhorar consistencia de treino": "Melhorar consistência de treino",
        },
        "observacoes": {
            "Rotina evoluindo bem, com boa distribuicao semanal.": "Rotina evoluindo bem, com boa distribuição semanal.",
        },
    },
    "metas_finalizadas": {
        "titulo": {
            "Registrar alimentacao por 21 dias": "Registrar alimentação por 21 dias",
        },
        "descricao": {
            "Criar o habito de registrar refeicoes e macros com regularidade.": "Criar o hábito de registrar refeições e macros com regularidade.",
        },
        "categoria": {
            "Nutricao": "Nutrição",
        },
        "status": {
            "Concluido": "Concluído",
        },
        "situacao_final": {
            "Concluida com sucesso": "Concluída com sucesso",
        },
        "observacoes": {
            "Habito consolidado no fim do mes.": "Hábito consolidado no fim do mês.",
        },
    },
}


def row_exists(connection, table: str, where_clause: str, params: tuple) -> bool:
    row = connection.execute(
        f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1",
        params,
    ).fetchone()
    return row is not None


def ensure_user_profile() -> None:
    update_user_profile(
        nome=USER_NAME,
        email=USER_EMAIL,
        data_nascimento=USER_BIRTH_DATE,
        peso_meta=USER_GOAL_WEIGHT,
    )


def normalize_existing_seed_texts(connection) -> None:
    for table, columns in TEXT_NORMALIZATION.items():
        for column, mapping in columns.items():
            for old_value, new_value in mapping.items():
                connection.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                    (new_value, old_value),
                )


def seed_body_records(connection) -> int:
    inserted = 0
    for data_ref, idade, peso, altura, imc in BODY_RECORDS:
        if row_exists(
            connection,
            "dados_corporais",
            "user_id = 1 AND data = ?",
            (data_ref,),
        ):
            continue
        connection.execute(
            """
            INSERT INTO dados_corporais (user_id, data, idade, peso, altura, imc)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (data_ref, idade, peso, altura, imc),
        )
        inserted += 1
    return inserted


def seed_cardiac_records(connection) -> int:
    inserted = 0
    for record in CARDIAC_RECORDS:
        data_ref = record[0]
        if row_exists(
            connection,
            "registros_cardiacos",
            "user_id = 1 AND data = ? AND observacoes = ?",
            (data_ref, record[5]),
        ):
            continue
        connection.execute(
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
            record,
        )
        inserted += 1
    return inserted


def seed_activity_records(connection) -> int:
    inserted = 0
    for record in ACTIVITY_RECORDS:
        data_ref, tipo, duracao, intensidade, calorias, distancia, observacoes = record
        if row_exists(
            connection,
            "atividades_fisicas",
            "user_id = 1 AND data = ? AND tipo_atividade = ? AND duracao_minutos = ?",
            (data_ref, tipo, duracao),
        ):
            continue
        connection.execute(
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
            (data_ref, tipo, duracao, intensidade, calorias, distancia, observacoes),
        )
        inserted += 1
    return inserted


def seed_food_records(connection) -> int:
    inserted = 0
    for record in FOOD_RECORDS:
        data_ref, refeicao, alimento, quantidade, calorias, proteinas, carbs, gorduras, observacoes = record
        if row_exists(
            connection,
            "alimentacao",
            "user_id = 1 AND data = ? AND refeicao = ? AND alimento = ?",
            (data_ref, refeicao, alimento),
        ):
            continue
        connection.execute(
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
            (data_ref, refeicao, alimento, quantidade, calorias, proteinas, carbs, gorduras, observacoes),
        )
        inserted += 1
    return inserted


def seed_active_goals(connection) -> int:
    inserted = 0
    for goal in ACTIVE_GOALS:
        title = goal[0]
        if row_exists(
            connection,
            "metas",
            "user_id = 1 AND titulo = ? AND data_inicio = ?",
            (title, goal[3]),
        ):
            continue
        connection.execute(
            """
            INSERT INTO metas (
                user_id,
                titulo,
                descricao,
                categoria,
                data_inicio,
                prazo,
                status,
                progresso,
                observacoes,
                data_criacao
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            goal,
        )
        inserted += 1
    return inserted


def seed_archived_goals(connection) -> int:
    inserted = 0
    for goal in ARCHIVED_GOALS:
        meta_origem_id, title, descricao, categoria, data_inicio, prazo, status, progresso, situacao, observacoes, data_criacao, data_finalizacao = goal
        if row_exists(
            connection,
            "metas_finalizadas",
            "user_id = 1 AND titulo = ? AND data_inicio = ?",
            (title, data_inicio),
        ):
            continue
        connection.execute(
            """
            INSERT INTO metas_finalizadas (
                meta_origem_id,
                user_id,
                titulo,
                descricao,
                categoria,
                data_inicio,
                prazo,
                status,
                progresso,
                situacao_final,
                observacoes,
                data_criacao,
                data_finalizacao
            )
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meta_origem_id,
                title,
                descricao,
                categoria,
                data_inicio,
                prazo,
                status,
                progresso,
                situacao,
                observacoes,
                data_criacao,
                data_finalizacao,
            ),
        )
        inserted += 1
    return inserted


def main() -> None:
    init_db()
    ensure_user_profile()

    with get_connection() as connection:
        normalize_existing_seed_texts(connection)
        counts = {
            "dados_corporais": seed_body_records(connection),
            "registros_cardiacos": seed_cardiac_records(connection),
            "atividades_fisicas": seed_activity_records(connection),
            "alimentacao": seed_food_records(connection),
            "metas": seed_active_goals(connection),
            "metas_finalizadas": seed_archived_goals(connection),
        }

    print("Seed concluido para fevereiro de 2026.")
    print(f"Periodo: {START_DATE} ate {END_DATE}")
    print(f"Perfil base: 78.0 kg | 1.72 m | 30 anos | nascimento {USER_BIRTH_DATE}")
    print(counts)


if __name__ == "__main__":
    main()

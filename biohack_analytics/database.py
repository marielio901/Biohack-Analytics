from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote
import os
import time
import tomllib

import pandas as pd
import psycopg
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"
DEFAULT_USER_ID = 1
SUPABASE_BACKEND = "supabase"

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    data_nascimento TEXT,
    peso_meta REAL DEFAULT 75.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dados_corporais (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    data TEXT NOT NULL,
    idade INTEGER NOT NULL,
    peso REAL NOT NULL,
    altura REAL NOT NULL,
    imc REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registros_cardiacos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    data TEXT NOT NULL,
    frequencia_media INTEGER NOT NULL,
    frequencia_repouso INTEGER NOT NULL,
    frequencia_maxima INTEGER NOT NULL,
    frequencia_minima INTEGER NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atividades_fisicas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    data TEXT NOT NULL,
    tipo_atividade TEXT NOT NULL,
    duracao_minutos INTEGER NOT NULL,
    intensidade TEXT NOT NULL,
    calorias_gastas REAL NOT NULL,
    distancia_km REAL NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alimentacao (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    data TEXT NOT NULL,
    refeicao TEXT NOT NULL,
    alimento TEXT NOT NULL,
    quantidade REAL NOT NULL,
    calorias REAL NOT NULL,
    proteinas REAL NOT NULL,
    carboidratos REAL NOT NULL,
    gorduras REAL NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registros_sono (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    data TEXT NOT NULL,
    hora_dormir TEXT NOT NULL,
    hora_acordar TEXT NOT NULL,
    duracao_horas REAL NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    categoria TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    prazo TEXT NOT NULL,
    status TEXT NOT NULL,
    progresso INTEGER NOT NULL,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metas_finalizadas (
    id SERIAL PRIMARY KEY,
    meta_origem_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    categoria TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    prazo TEXT NOT NULL,
    status TEXT NOT NULL,
    progresso INTEGER NOT NULL,
    situacao_final TEXT NOT NULL,
    observacoes TEXT,
    data_criacao TEXT,
    data_finalizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historico_axiel (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usuarios(id),
    role TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class DBConnection:
    def __init__(self, raw_connection: Any) -> None:
        self.raw = raw_connection
        self.backend = SUPABASE_BACKEND

    def _adapt_query(self, query: str) -> str:
        return query.replace("?", "%s")

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> Any:
        return self.raw.execute(self._adapt_query(query), params)

    def executemany(
        self,
        query: str,
        seq_of_params: list[tuple[Any, ...]] | tuple[tuple[Any, ...], ...],
    ) -> Any:
        with self.raw.cursor() as cursor:
            cursor.executemany(self._adapt_query(query), seq_of_params)
            return cursor

    def executescript(self, script: str) -> None:
        statements = [statement.strip() for statement in script.split(";") if statement.strip()]
        for statement in statements:
            self.execute(statement)

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()

    def close(self) -> None:
        self.raw.close()

    def __enter__(self) -> "DBConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


@lru_cache(maxsize=1)
def _load_local_secrets() -> dict[str, Any]:
    if not SECRETS_PATH.exists():
        return {}
    with SECRETS_PATH.open("rb") as handle:
        return tomllib.load(handle)


def _get_setting(name: str, default: Any = None) -> Any:
    env_value = os.environ.get(name)
    if env_value not in (None, ""):
        return env_value
    return _load_local_secrets().get(name, default)


def _normalize_postgres_dsn(raw_dsn: str | None) -> str | None:
    if not raw_dsn:
        return None
    raw_dsn = raw_dsn.strip()
    if "://" not in raw_dsn:
        return raw_dsn
    scheme, rest = raw_dsn.split("://", 1)
    if "@" not in rest:
        return raw_dsn
    credentials, host = rest.rsplit("@", 1)
    if ":" not in credentials:
        return raw_dsn
    user, password = credentials.split(":", 1)
    return f"{scheme}://{user}:{quote(password, safe='')}@{host}"


def _get_supabase_dsn() -> str:
    raw_dsn = _get_setting("SUPABASE_DB_URL")
    dsn = _normalize_postgres_dsn(str(raw_dsn)) if raw_dsn else None
    if not dsn:
        raise RuntimeError("SUPABASE_DB_URL não configurado")
    return dsn


def _get_connect_timeout_seconds() -> int:
    value = _get_setting("SUPABASE_CONNECT_TIMEOUT_SECONDS", 15)
    try:
        return max(5, int(value))
    except (TypeError, ValueError):
        return 15


def _get_connect_retries() -> int:
    value = _get_setting("SUPABASE_CONNECT_RETRIES", 3)
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 3


def calculate_imc(peso: float, altura: float) -> float:
    if altura <= 0:
        return 0.0
    return round(peso / (altura**2), 2)


def calculate_sleep_duration_hours(hora_dormir: str, hora_acordar: str) -> float:
    sleep_time = datetime.strptime(hora_dormir.strip(), "%H:%M")
    wake_time = datetime.strptime(hora_acordar.strip(), "%H:%M")
    if wake_time <= sleep_time:
        wake_time += timedelta(days=1)
    duration = wake_time - sleep_time
    return round(duration.total_seconds() / 3600, 2)


def get_connection(backend: str | None = None) -> DBConnection:
    del backend
    last_error: Exception | None = None
    for attempt in range(1, _get_connect_retries() + 1):
        try:
            raw_connection = psycopg.connect(
                _get_supabase_dsn(),
                row_factory=dict_row,
                connect_timeout=_get_connect_timeout_seconds(),
            )
            return DBConnection(raw_connection)
        except psycopg.OperationalError as exc:
            last_error = exc
            if attempt == _get_connect_retries():
                break
            time.sleep(min(1.5 * attempt, 4))
    raise RuntimeError(
        "Não foi possível conectar ao Supabase após múltiplas tentativas. "
        "Se persistir, troque a conexão para o pooler do Supabase."
    ) from last_error


def init_db(backend: str | None = None) -> Path:
    del backend
    with get_connection() as connection:
        connection.executescript(POSTGRES_SCHEMA)
        current = connection.execute(
            "SELECT id FROM usuarios WHERE id = ?",
            (DEFAULT_USER_ID,),
        ).fetchone()
        if current is None:
            connection.execute(
                """
                INSERT INTO usuarios (id, nome, email, data_nascimento, peso_meta)
                VALUES (?, ?, ?, ?, ?)
                """,
                (DEFAULT_USER_ID, "Mariélio", "", None, 75.0),
            )
        else:
            row = connection.execute(
                "SELECT nome FROM usuarios WHERE id = ?",
                (DEFAULT_USER_ID,),
            ).fetchone()
            if row and str(row["nome"] or "").strip() == "Usuário BIOHACK":
                connection.execute(
                    "UPDATE usuarios SET nome = ? WHERE id = ?",
                    ("Mariélio", DEFAULT_USER_ID),
                )
    return PROJECT_ROOT


def _query_dataframe(
    query: str,
    params: tuple[Any, ...] = (),
    *,
    backend: str | None = None,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    del backend
    if connection is not None:
        cursor = connection.execute(query, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in (cursor.description or [])]
    else:
        with get_connection() as db_connection:
            cursor = db_connection.execute(query, params)
            rows = cursor.fetchall()
            columns = [description[0] for description in (cursor.description or [])]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([dict(row) for row in rows], columns=columns)


def get_user_profile(user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else {}


def update_user_profile(
    nome: str,
    email: str,
    data_nascimento: str | None,
    peso_meta: float,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE usuarios
            SET nome = ?, email = ?, data_nascimento = ?, peso_meta = ?
            WHERE id = ?
            """,
            (nome.strip(), email.strip(), data_nascimento, peso_meta, user_id),
        )


def insert_body_record(
    data: str,
    idade: int,
    peso: float,
    altura: float,
    user_id: int = DEFAULT_USER_ID,
) -> float:
    imc = calculate_imc(peso, altura)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dados_corporais (user_id, data, idade, peso, altura, imc)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, data, idade, peso, altura, imc),
        )
    return imc


def insert_cardiac_record(
    data: str,
    frequencia_media: int,
    frequencia_repouso: int,
    frequencia_maxima: int,
    frequencia_minima: int,
    observacoes: str,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
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
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data,
                frequencia_media,
                frequencia_repouso,
                frequencia_maxima,
                frequencia_minima,
                observacoes.strip(),
            ),
        )


def insert_activity_record(
    data: str,
    tipo_atividade: str,
    duracao_minutos: int,
    intensidade: str,
    calorias_gastas: float,
    distancia_km: float,
    observacoes: str,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data,
                tipo_atividade.strip(),
                duracao_minutos,
                intensidade.strip(),
                calorias_gastas,
                distancia_km,
                observacoes.strip(),
            ),
        )


def insert_food_record(
    data: str,
    refeicao: str,
    alimento: str,
    quantidade: float,
    calorias: float,
    proteinas: float,
    carboidratos: float,
    gorduras: float,
    observacoes: str,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data,
                refeicao.strip(),
                alimento.strip(),
                quantidade,
                calorias,
                proteinas,
                carboidratos,
                gorduras,
                observacoes.strip(),
            ),
        )


def insert_sleep_record(
    data: str,
    hora_dormir: str,
    hora_acordar: str,
    observacoes: str,
    user_id: int = DEFAULT_USER_ID,
) -> float:
    duration_hours = calculate_sleep_duration_hours(hora_dormir, hora_acordar)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO registros_sono (
                user_id,
                data,
                hora_dormir,
                hora_acordar,
                duracao_horas,
                observacoes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                data,
                hora_dormir.strip(),
                hora_acordar.strip(),
                duration_hours,
                observacoes.strip(),
            ),
        )
    return duration_hours


def insert_goal(
    titulo: str,
    descricao: str,
    categoria: str,
    data_inicio: str,
    prazo: str,
    status: str,
    progresso: int,
    observacoes: str,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
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
                observacoes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                titulo.strip(),
                descricao.strip(),
                categoria.strip(),
                data_inicio,
                prazo,
                status.strip(),
                progresso,
                observacoes.strip(),
            ),
        )


def update_goal(meta_id: int, status: str, progresso: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE metas
            SET status = ?, progresso = ?
            WHERE id = ?
            """,
            (status.strip(), progresso, meta_id),
        )


def finalize_goal(meta_id: int, situacao_final: str = "Concluída com sucesso") -> bool:
    with get_connection() as connection:
        goal = connection.execute(
            "SELECT * FROM metas WHERE id = ?",
            (meta_id,),
        ).fetchone()

        if goal is None:
            return False

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
                data_criacao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                goal["id"],
                goal["user_id"],
                goal["titulo"],
                goal["descricao"],
                goal["categoria"],
                goal["data_inicio"],
                goal["prazo"],
                goal["status"],
                goal["progresso"],
                situacao_final,
                goal["observacoes"],
                goal["data_criacao"],
            ),
        )
        connection.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
    return True


def save_axiel_message(
    role: str,
    mensagem: str,
    user_id: int = DEFAULT_USER_ID,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO historico_axiel (user_id, role, mensagem)
            VALUES (?, ?, ?)
            """,
            (user_id, role.strip(), mensagem.strip()),
        )


def clear_axiel_history(user_id: int = DEFAULT_USER_ID) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM historico_axiel WHERE user_id = ?",
            (user_id,),
        )


def get_body_history_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT id, data, idade, peso, altura, imc
        FROM dados_corporais
        WHERE user_id = ?
        ORDER BY data, id
        """,
        (user_id,),
        connection=connection,
    )


def get_cardiac_history_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            data,
            frequencia_media,
            frequencia_repouso,
            frequencia_maxima,
            frequencia_minima,
            observacoes
        FROM registros_cardiacos
        WHERE user_id = ?
        ORDER BY data, id
        """,
        (user_id,),
        connection=connection,
    )


def get_activity_history_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            data,
            tipo_atividade,
            duracao_minutos,
            intensidade,
            calorias_gastas,
            distancia_km,
            observacoes
        FROM atividades_fisicas
        WHERE user_id = ?
        ORDER BY data, id
        """,
        (user_id,),
        connection=connection,
    )


def get_food_history_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            data,
            refeicao,
            alimento,
            quantidade,
            calorias,
            proteinas,
            carboidratos,
            gorduras,
            observacoes
        FROM alimentacao
        WHERE user_id = ?
        ORDER BY data, id
        """,
        (user_id,),
        connection=connection,
    )


def get_sleep_history_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            data,
            hora_dormir,
            hora_acordar,
            duracao_horas,
            observacoes
        FROM registros_sono
        WHERE user_id = ?
        ORDER BY data, id
        """,
        (user_id,),
        connection=connection,
    )


def get_goals_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            titulo,
            descricao,
            categoria,
            data_inicio,
            prazo,
            status,
            progresso,
            observacoes,
            data_criacao
        FROM metas
        WHERE user_id = ?
        ORDER BY data_criacao DESC, id DESC
        """,
        (user_id,),
        connection=connection,
    )


def get_goal_archive_df(
    user_id: int = DEFAULT_USER_ID,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    return _query_dataframe(
        """
        SELECT
            id,
            meta_origem_id,
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
        FROM metas_finalizadas
        WHERE user_id = ?
        ORDER BY data_finalizacao DESC, id DESC
        """,
        (user_id,),
        connection=connection,
    )


def load_axiel_history_df(
    user_id: int = DEFAULT_USER_ID,
    limit: int = 40,
    connection: DBConnection | None = None,
) -> pd.DataFrame:
    history = _query_dataframe(
        """
        SELECT id, role, mensagem, created_at
        FROM historico_axiel
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
        connection=connection,
    )
    if history.empty:
        return history
    return history.sort_values("id").reset_index(drop=True)


def load_all_data(user_id: int = DEFAULT_USER_ID) -> dict[str, pd.DataFrame]:
    with get_connection() as connection:
        return {
            "dados_corporais": get_body_history_df(user_id, connection=connection),
            "registros_cardiacos": get_cardiac_history_df(user_id, connection=connection),
            "atividades_fisicas": get_activity_history_df(user_id, connection=connection),
            "alimentacao": get_food_history_df(user_id, connection=connection),
            "registros_sono": get_sleep_history_df(user_id, connection=connection),
            "metas": get_goals_df(user_id, connection=connection),
            "metas_finalizadas": get_goal_archive_df(user_id, connection=connection),
            "historico_axiel": load_axiel_history_df(user_id, connection=connection),
        }

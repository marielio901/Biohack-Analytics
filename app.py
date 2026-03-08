from biohack_analytics.database import init_db
from biohack_analytics.styles import APP_STYLE
from biohack_analytics.views import (
    render_axiel_page,
    render_dashboard_page,
    render_records_page,
    render_sidebar_menu,
    render_goals_page,
)

import streamlit as st


@st.cache_resource(show_spinner=False)
def _ensure_app_initialized() -> None:
    init_db()


def _render_startup_error(message: str) -> None:
    st.error(message)
    st.caption(
        "No deploy da Streamlit Community Cloud, configure `SUPABASE_DB_URL` em "
        "`App settings > Secrets` com a URL do pooler do Supabase."
    )
    st.stop()


def main() -> None:
    st.set_page_config(
        page_title="BIOHACK ANALYTICS",
        page_icon="B",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(APP_STYLE, unsafe_allow_html=True)
    try:
        _ensure_app_initialized()
    except RuntimeError as exc:
        _render_startup_error(str(exc))

    menu = render_sidebar_menu()

    if menu == "Dashboard":
        render_dashboard_page()
    elif menu == "Registros":
        render_records_page()
    elif menu == "Metas":
        render_goals_page()
    else:
        render_axiel_page()


if __name__ == "__main__":
    main()

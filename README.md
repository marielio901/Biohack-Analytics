# BIOHACK ANALYTICS

Sistema web local para monitoramento de saúde, performance, alimentação, atividades físicas, metas e acompanhamento inteligente com Axiel AI.

## Stack

- Python
- Streamlit
- Supabase Postgres
- Plotly
- Pandas
- Edge TTS

## Como executar

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuração da Axiel

A Axiel usa seus dados do Supabase como contexto e pode responder em dois modos:

- `Together configurada`: usa um modelo externo da Together API e cai para o modo local se a chamada falhar.
- `Modo local`: gera análise e recomendações diretamente pelas regras locais do app.

Para ambiente local, copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml` e preencha os valores reais.

Para deploy na Streamlit Community Cloud, cole os mesmos campos no painel `App settings > Secrets`.

Exemplo:

```toml
SUPABASE_DB_URL = "postgresql://postgres:SUA_SENHA@SEU_HOST/postgres"
AXIEL_TOGETHER_API_KEY = "sua-chave-aqui"
AXIEL_CHAT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
AXIEL_TRANSCRIBE_MODEL = "openai/whisper-large-v3"
AXIEL_TRANSCRIBE_LANGUAGE = "pt"
AXIEL_CHAT_TIMEOUT_SECONDS = 90
AXIEL_TRANSCRIBE_TIMEOUT_SECONDS = 120
SUPABASE_CONNECT_TIMEOUT_SECONDS = 15
SUPABASE_CONNECT_RETRIES = 3
```

Também são aceitas variáveis de ambiente equivalentes, incluindo `TOGETHER_API_KEY` e os nomes legados `STOCKPILOT_*`.

## Deploy na Streamlit Community Cloud

Arquivos usados no deploy:

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `.streamlit/secrets.example.toml`

Passos:

1. Suba o projeto para um repositório no GitHub.
2. Na Streamlit Community Cloud, crie uma nova app apontando para `app.py`.
3. Em `App settings > Secrets`, cole os campos do arquivo `.streamlit/secrets.example.toml` com os valores reais.
4. Faça o primeiro deploy.

Secrets realmente usados pelo app hoje:

- `SUPABASE_DB_URL`
- `AXIEL_TOGETHER_API_KEY`

Secrets opcionais:

- `AXIEL_CHAT_MODEL`
- `AXIEL_TRANSCRIBE_MODEL`
- `AXIEL_TRANSCRIBE_LANGUAGE`
- `AXIEL_CHAT_TIMEOUT_SECONDS`
- `AXIEL_TRANSCRIBE_TIMEOUT_SECONDS`
- `SUPABASE_CONNECT_TIMEOUT_SECONDS`
- `SUPABASE_CONNECT_RETRIES`

Checklist antes de publicar:

- `SUPABASE_DB_URL` usando a credencial real do banco
- `AXIEL_TOGETHER_API_KEY` real
- rotação das chaves que já foram expostas durante a configuração

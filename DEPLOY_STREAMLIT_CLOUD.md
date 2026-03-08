# Deploy na Streamlit Community Cloud

## Entry point

- `app.py`

## Dependencias

- `requirements.txt`

## Configuracao visual

- `.streamlit/config.toml`

## Secrets

Cole no painel `App settings > Secrets`:

```toml
SUPABASE_DB_URL = "postgresql://postgres.PROJECT_REF:SUA_SENHA_NOVA@aws-0-REGIAO.pooler.supabase.com:5432/postgres?sslmode=require"
AXIEL_TOGETHER_API_KEY = "SUA_CHAVE_NOVA"
AXIEL_CHAT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
AXIEL_TRANSCRIBE_MODEL = "openai/whisper-large-v3"
AXIEL_TRANSCRIBE_LANGUAGE = "pt"
AXIEL_CHAT_TIMEOUT_SECONDS = 90
AXIEL_TRANSCRIBE_TIMEOUT_SECONDS = 120
SUPABASE_CONNECT_TIMEOUT_SECONDS = 15
SUPABASE_CONNECT_RETRIES = 3
```

## Fluxo

1. Subir o codigo no GitHub
2. Criar a app na Streamlit Community Cloud
3. Selecionar o repositorio e o arquivo `app.py`
4. Colar os secrets
5. Fazer deploy

## Observacoes

- Nao subir `.streamlit/secrets.toml` para o GitHub
- O projeto ja ignora esse arquivo em `.gitignore`
- O arquivo `.streamlit/secrets.example.toml` e apenas template
- `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` nao sao necessarios no codigo atual
- Na Streamlit Community Cloud, nao use a conexao direta `db.<project>.supabase.co:5432`
- Para producao, prefira a conexao `pooler` do Supabase
- Se usar `Transaction pooler` na porta `6543`, o app ja desabilita prepared statements

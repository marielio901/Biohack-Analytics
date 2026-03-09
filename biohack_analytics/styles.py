APP_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&family=Space+Grotesk:wght@500;700&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    --bg: #171717;
    --bg-soft: #111111;
    --panel: rgba(28, 28, 28, 0.96);
    --panel-strong: #202020;
    --panel-alt: #262626;
    --ink: #f4fff9;
    --muted: #95aca4;
    --primary: #00f995;
    --secondary: #0bd184;
    --accent: #00f995;
    --danger: #ff6b6b;
    --success: #00f995;
    --line: rgba(0, 249, 149, 0.16);
    --line-strong: rgba(0, 249, 149, 0.42);
    --shadow: 0 18px 44px rgba(0, 0, 0, 0.36);
}

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif;
    color: var(--ink);
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(0, 249, 149, 0.11), transparent 24%),
        radial-gradient(circle at top right, rgba(0, 249, 149, 0.07), transparent 18%),
        linear-gradient(180deg, #171717 0%, #111111 100%);
}

header[data-testid="stHeader"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

div[data-testid="stDecoration"] {
    display: none;
}

div[data-testid="stToolbar"] {
    background: transparent !important;
    border: 0 !important;
}

[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stToolbarActions"],
[data-testid="stHeaderActionElements"] {
    display: none !important;
    visibility: hidden !important;
}

button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] button {
    position: fixed !important;
    top: 0.7rem !important;
    left: 0.7rem !important;
    width: 2.5rem !important;
    height: 2.5rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    z-index: 1000000 !important;
    background: rgba(18, 18, 18, 0.96) !important;
    color: var(--primary) !important;
    border: 1px solid rgba(0, 249, 149, 0.22) !important;
    border-radius: 14px !important;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22) !important;
}

button[data-testid="stExpandSidebarButton"] span,
[data-testid="stSidebarCollapseButton"] button span {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
}

[data-testid="stSidebarCollapseButton"] {
    margin-left: auto !important;
}

button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    border-color: rgba(0, 249, 149, 0.65) !important;
    background: rgba(0, 249, 149, 0.12) !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0;
}

[data-testid="stAppViewContainer"] > .main .block-container {
    max-width: none !important;
    width: 100%;
    padding: 0.75rem 1.1rem 2rem 1.1rem;
}

@media (min-width: 1440px) {
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-left: 1.4rem;
        padding-right: 1.4rem;
    }
}

@media (max-width: 900px) {
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-left: 0.75rem;
        padding-right: 0.75rem;
        padding-bottom: 1.4rem;
    }
}

[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at top left, rgba(0, 249, 149, 0.12), transparent 26%),
        linear-gradient(180deg, #101010 0%, #141414 100%);
    border-right: 1px solid rgba(0, 249, 149, 0.14);
}

[data-testid="stSidebar"] * {
    color: var(--ink);
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0.45rem;
}

.page-title {
    margin: 0.15rem 0 0.8rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    line-height: 1.05;
    color: var(--ink);
}

.section-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.section-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12rem;
    color: var(--primary);
    font-size: 0.76rem;
    font-weight: 700;
}

.section-card h3 {
    margin: 0.15rem 0 0.35rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
}

.section-card p {
    margin: 0;
    color: var(--muted);
    line-height: 1.55;
}

div[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(35, 35, 35, 0.96), rgba(26, 26, 26, 0.96));
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 0.9rem 1rem;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.24);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--ink);
}

.metric-card {
    min-height: 138px;
    background: linear-gradient(180deg, rgba(35, 35, 35, 0.96), rgba(26, 26, 26, 0.96));
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 1rem 1rem 0.95rem;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.24);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.metric-card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
    min-height: 2.9rem;
}

.metric-card-label {
    display: block;
    flex: 1;
    color: var(--muted);
    font-weight: 600;
    font-size: 0.96rem;
    line-height: 1.35;
}

.metric-card-icon {
    flex-shrink: 0;
    margin-top: 0.05rem;
    color: var(--primary);
    font-size: 1.15rem;
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.metric-card-value {
    margin-top: 0.35rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    line-height: 1.02;
    color: var(--ink);
    letter-spacing: -0.03rem;
}

.metric-card-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.45rem;
    margin-top: 0.8rem;
}

.metric-card-badge {
    display: inline-flex;
    align-items: center;
    min-height: 1.7rem;
    padding: 0.18rem 0.62rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
}

.metric-card-badge--good {
    background: rgba(0, 249, 149, 0.14);
    color: var(--primary);
}

.metric-card-badge--warning {
    background: rgba(255, 209, 102, 0.14);
    color: #ffd166;
}

.metric-card-badge--danger {
    background: rgba(255, 107, 107, 0.14);
    color: #ff8f8f;
}

.metric-card-badge--muted {
    background: rgba(255, 255, 255, 0.06);
    color: rgba(244, 255, 249, 0.72);
}

.metric-card-meta-text,
.metric-card-delta-positive,
.metric-card-delta-negative {
    font-size: 0.82rem;
    font-weight: 600;
}

.metric-card-meta-text {
    color: rgba(244, 255, 249, 0.62);
}

.metric-card-delta-positive {
    color: var(--primary);
}

.metric-card-delta-negative {
    color: #ff8f8f;
}

.sidebar-brand {
    padding: 0.35rem 0 1rem;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid rgba(0, 249, 149, 0.14);
}

.sidebar-brand-label {
    display: inline-block;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16rem;
    opacity: 0.72;
    margin-bottom: 0.5rem;
}

.sidebar-brand h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    line-height: 1.02;
    margin: 0;
    color: var(--ink);
}

.sidebar-brand p {
    margin: 0.45rem 0 0;
    color: rgba(244, 255, 249, 0.68);
    font-size: 0.88rem;
}

.sidebar-filter-card {
    margin: 0.65rem 0 0.3rem;
    padding-top: 0.9rem;
    border-top: 1px solid rgba(0, 249, 149, 0.14);
}

.sidebar-filter-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.14rem;
    color: rgba(244, 255, 249, 0.7);
    font-weight: 700;
}

.stTextInput label,
.stNumberInput label,
.stDateInput label,
.stTimeInput label,
.stSelectbox label,
.stMultiSelect label,
.stTextArea label,
.stSlider label,
.stRadio label,
.stCheckbox label {
    color: var(--muted) !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: rgba(20, 20, 20, 0.96) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
}

.stTextArea textarea {
    min-height: 120px;
}

.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stDateInput > div > div,
.stDateInput [data-baseweb="input"] > div,
.stTimeInput [data-baseweb="input"] > div {
    background: rgba(20, 20, 20, 0.96) !important;
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    box-shadow: none !important;
}

.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span,
.stDateInput input,
.stTimeInput input {
    color: var(--ink) !important;
}

.stSelectbox [data-baseweb="select"] > div:hover,
.stMultiSelect [data-baseweb="select"] > div:hover,
.stDateInput > div > div:hover,
.stTimeInput [data-baseweb="input"] > div:hover {
    border-color: var(--line-strong) !important;
}

[data-baseweb="button-group"] {
    background: rgba(18, 18, 18, 0.94) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    width: fit-content !important;
    box-shadow: none !important;
}

[data-baseweb="button-group"] > div {
    gap: 0 !important;
}

[data-baseweb="button-group"] button {
    background: transparent !important;
    color: var(--muted) !important;
    border: 0 !important;
    border-right: 1px solid rgba(0, 249, 149, 0.14) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition:
        background-color 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease !important;
}

[data-baseweb="button-group"] button:last-child {
    border-right: 0 !important;
}

[data-baseweb="button-group"] button *,
[data-baseweb="button-group"] button span,
[data-baseweb="button-group"] button p {
    color: inherit !important;
}

[data-baseweb="button-group"] button:hover {
    background: rgba(0, 249, 149, 0.07) !important;
    color: var(--ink) !important;
}

[data-baseweb="button-group"] button[aria-pressed="true"],
[data-baseweb="button-group"] button[aria-selected="true"],
[data-baseweb="button-group"] button[aria-checked="true"],
[data-baseweb="button-group"] button[data-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 249, 149, 0.16), rgba(0, 249, 149, 0.06)) !important;
    color: var(--primary) !important;
    box-shadow: inset 0 0 0 1px rgba(0, 249, 149, 0.5) !important;
}

[data-baseweb="button-group"] button:focus,
[data-baseweb="button-group"] button:focus-visible {
    outline: none !important;
    box-shadow:
        inset 0 0 0 1px rgba(0, 249, 149, 0.68) !important,
        0 0 0 3px rgba(0, 249, 149, 0.12) !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] {
    background: linear-gradient(180deg, rgba(11, 16, 27, 0.98), rgba(7, 11, 20, 0.98)) !important;
    border: 1px solid var(--line) !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 44px rgba(0, 0, 0, 0.42) !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] *,
div[data-baseweb="popover"] div[data-baseweb="calendar"] span,
div[data-baseweb="popover"] div[data-baseweb="calendar"] p {
    color: var(--ink) !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] [data-baseweb="select"] > div,
div[data-baseweb="popover"] div[data-baseweb="calendar"] [data-baseweb="input"] > div {
    background: rgba(22, 27, 40, 0.98) !important;
    border: 1px solid rgba(0, 249, 149, 0.18) !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] button {
    color: var(--ink) !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    transition:
        background-color 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] button:hover {
    background: rgba(0, 249, 149, 0.1) !important;
    color: var(--primary) !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] button[aria-selected="true"],
div[data-baseweb="popover"] div[data-baseweb="calendar"] button[aria-pressed="true"],
div[data-baseweb="popover"] div[data-baseweb="calendar"] [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 249, 149, 0.95), rgba(11, 209, 132, 0.82)) !important;
    color: #08150f !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] button:focus,
div[data-baseweb="popover"] div[data-baseweb="calendar"] button:focus-visible {
    outline: none !important;
    box-shadow:
        inset 0 0 0 1px rgba(0, 249, 149, 0.72) !important,
        0 0 0 3px rgba(0, 249, 149, 0.12) !important;
}

div[data-baseweb="popover"] div[data-baseweb="calendar"] svg {
    color: var(--primary) !important;
    fill: currentColor !important;
}

.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 6px rgba(0, 249, 149, 0.14) !important;
}

.stSlider [data-baseweb="slider"] > div > div:first-child {
    background: rgba(0, 249, 149, 0.18) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
    gap: 0.55rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type {
    margin-bottom: 0.75rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type div[role="radiogroup"] {
    gap: 0.22rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label {
    background: transparent;
    border: 1px solid transparent;
    border-left: 2px solid transparent;
    border-radius: 12px;
    padding: 0.72rem 0.78rem;
    box-shadow: none;
    transition:
        background-color 160ms ease,
        border-color 160ms ease,
        color 160ms ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label:hover {
    background: rgba(255, 255, 255, 0.025);
    border-color: rgba(255, 255, 255, 0.04);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label:has(input:checked) {
    background: linear-gradient(90deg, rgba(0, 249, 149, 0.11), rgba(0, 249, 149, 0.03) 62%, transparent);
    border-color: rgba(0, 249, 149, 0.08);
    border-left-color: rgba(0, 249, 149, 0.84);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label p {
    display: flex;
    align-items: center;
    gap: 0.58rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: rgba(244, 255, 249, 0.74);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label:has(input:checked) p {
    color: rgba(244, 255, 249, 0.98);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label p .material-symbols-rounded {
    font-size: 1.02rem;
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
    color: rgba(244, 255, 249, 0.62);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label:has(input:checked) p .material-symbols-rounded {
    color: var(--primary);
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type label > div:first-child {
    display: none;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:first-of-type input[type="radio"] {
    display: none;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-wrap: nowrap;
    gap: 0.35rem;
    width: 100%;
    white-space: nowrap;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) div[role="radiogroup"] > * {
    display: inline-flex !important;
    align-items: center;
    width: auto !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
    min-height: auto;
    box-shadow: none;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    width: auto !important;
    white-space: nowrap;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label:has(input:checked) {
    background: transparent;
    border: none;
    box-shadow: none;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label p {
    font-weight: 600;
    color: rgba(244, 255, 249, 0.68);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label:hover p {
    color: rgba(244, 255, 249, 0.88);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label:has(input:checked) p {
    color: var(--primary);
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label > div:first-child,
[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) input[type="radio"] {
    display: none;
}

[data-testid="stSidebar"] [data-testid="stRadio"]:not(:first-of-type) label:not(:last-child)::after {
    content: "|";
    color: rgba(244, 255, 249, 0.34);
    font-weight: 500;
    margin-left: 0.05rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.55rem;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(28, 28, 28, 0.95);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.6rem 1rem;
    color: var(--muted);
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(0, 249, 149, 0.07);
    color: var(--ink);
}

.stTabs [aria-selected="true"] {
    background: rgba(0, 249, 149, 0.12);
    color: var(--primary);
    border-color: rgba(0, 249, 149, 0.62);
    box-shadow: 0 0 0 1px rgba(0, 249, 149, 0.12);
}

.stTabs [aria-selected="true"] * {
    color: inherit !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(31, 31, 31, 0.98), rgba(23, 23, 23, 0.98));
    border: 1px solid var(--line);
    border-radius: 20px;
    box-shadow: var(--shadow);
    margin-bottom: 0.7rem;
}

.goal-card {
    margin-bottom: 0.1rem;
}

.goal-card-head {
    margin-bottom: 0.65rem;
}

.goal-card h4 {
    font-family: 'Space Grotesk', sans-serif;
    margin: 0;
    font-size: 1.02rem;
}

.goal-card p {
    color: var(--muted);
    margin: 0.45rem 0 0.75rem;
    line-height: 1.45;
    font-size: 0.92rem;
}

.goal-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 0.55rem;
}

.goal-chip {
    background: rgba(0, 249, 149, 0.1);
    color: var(--primary);
    border-radius: 999px;
    padding: 0.25rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 700;
}

.goal-status-label {
    margin-top: 0.8rem;
    margin-bottom: 0.35rem;
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08rem;
}

.goal-status-readout {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 2.4rem;
}

.goal-progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0.7rem 0 0.2rem;
    color: var(--muted);
    font-size: 0.88rem;
}

.goal-progress-row strong {
    color: var(--primary);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
    min-height: 2.35rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([disabled]) {
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color: rgba(244, 255, 249, 0.82) !important;
    box-shadow: none !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"]:hover {
    background: rgba(0, 249, 149, 0.08) !important;
    border-color: rgba(0, 249, 149, 0.42) !important;
    color: var(--primary) !important;
}

.note-card {
    background: rgba(27, 27, 27, 0.96);
    border-left: 4px solid var(--accent);
    border-radius: 16px;
    padding: 0.95rem 1rem;
    margin-bottom: 0.9rem;
}

.note-card strong {
    display: block;
    margin-bottom: 0.2rem;
}

.small-note {
    color: var(--muted);
    font-size: 0.86rem;
}

[data-testid="stAlert"] {
    background: rgba(29, 29, 29, 0.98) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    color: var(--ink) !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid var(--line);
    border-radius: 18px;
    overflow: hidden;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00f995, #00c97a) !important;
}

button[kind="primary"],
.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, rgba(0, 249, 149, 0.18), rgba(0, 249, 149, 0.08)) !important;
    color: var(--primary) !important;
    border: 1px solid rgba(0, 249, 149, 0.42) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
}

button[kind="primary"]:hover,
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: rgba(0, 249, 149, 0.82) !important;
    color: #091b14 !important;
    background: linear-gradient(135deg, rgba(0, 249, 149, 0.92), rgba(0, 249, 149, 0.7)) !important;
}

.caption-pill {
    display: inline-block;
    background: rgba(16, 35, 27, 0.06);
    border-radius: 999px;
    padding: 0.25rem 0.65rem;
    font-size: 0.78rem;
    color: var(--muted);
    margin-right: 0.35rem;
}

[data-testid="stChatMessage"] .stButton > button {
    min-height: 2rem;
    padding: 0.35rem 0.8rem !important;
    border-radius: 12px !important;
}

[data-testid="stChatMessage"] .stButton > button:not(:hover) {
    background: rgba(255, 255, 255, 0.02) !important;
    color: rgba(244, 255, 249, 0.82) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
}

[data-testid="stChatMessage"] audio {
    margin-top: 0.35rem;
    width: 100%;
}
</style>
"""

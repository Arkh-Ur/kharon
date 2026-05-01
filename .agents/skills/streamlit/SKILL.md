---
name: streamlit
description: >
  Streamlit web framework patterns for Python — caching, session state, fragments,
  widget state management, layout, forms, and performance optimization.
  Trigger: When working with Streamlit apps, st.* APIs, st.cache_data, st.cache_resource,
  st.session_state, st.fragment, st.form, st.rerun, or any Streamlit webapp code.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Building or modifying Streamlit web apps (`app.py`, `streamlit run`)
- Using `st.cache_data`, `st.cache_resource`, or any caching
- Managing `st.session_state` for widget state persistence
- Using `@st.fragment` for independent reruns or auto-refresh
- Creating forms, dialogs, or multi-page navigation
- Debugging Streamlit rerun behavior or widget state issues
- Optimizing Streamlit performance (N+1 queries, redundant I/O)

## Critical Patterns

### Caching Decision Tree

| Use Case | Decorator | Why |
|----------|-----------|-----|
| API calls, DataFrame transforms, computations | `@st.cache_data(ttl=N)` | Returns a **copy** — safe against mutations |
| Database connections, ML models, HTTP sessions | `@st.cache_resource` | Returns the **same object** — singleton pattern |
| Data that changes frequently | `@st.cache_data(ttl=5)` | Auto-expires after N seconds |
| Large immutable datasets (>100M rows) | `@st.cache_resource` | Avoids serialization overhead |

**Rules:**
- `st.cache_data` creates a **copy** on each call — prevents mutation bugs across sessions
- `st.cache_resource` returns the **same object** — mutations affect ALL sessions (thread-safety required)
- Always set `ttl` for data from APIs/databases to prevent stale data
- Never mutate the return value of a `@st.cache_resource` function without thread-safety guards
- Use `st.cache_data.clear()` / `st.cache_resource.clear()` to force refresh

```python
@st.cache_data(ttl=300)
def fetch_api_data(url):
    return requests.get(url).json()

@st.cache_resource
def get_db_connection():
    return psycopg2.connect(...)

@st.cache_resource
def get_http_client():
    return requests.Session()
```

### Session State Widget Pattern (Pending Value Pattern)

Streamlit widgets (`st.selectbox`, `st.text_input`, etc.) cannot have their value
set programmatically AFTER instantiation. Use the **pending value pattern**:

```python
# 1. Process pending values BEFORE widget instantiation
if "pending_color" in st.session_state:
    st.session_state.color = st.session_state.pop("pending_color")

# 2. Create widget (reads from session_state.color)
color = st.selectbox("Color", ["red", "blue", "green"], key="color")

# 3. Set pending value in callbacks/buttons (triggers rerun, widget picks it up)
if st.button("Reset"):
    st.session_state.pending_color = "red"
    st.rerun()
```

**Rules:**
- `pop()` the pending key BEFORE widget creation — never after
- The widget's `key` parameter is what binds it to `st.session_state`
- If you don't pop before creation, you get `StreamlitAPIException`
- Use separate pending keys for each widget that needs programmatic updates

### Fragments for Auto-Refresh and Independent Reruns

```python
# Auto-refreshing fragment (e.g., live data chart)
@st.fragment(run_every="5s")
def live_chart():
    data = fetch_latest_data()
    st.line_chart(data)

# Click-to-refresh fragment (no auto-refresh)
@st.fragment
def metrics_panel():
    st.metric("CPU", f"{random.randint(20, 80)}%")
    if st.button("Refresh"):
        st.rerun(scope="fragment")  # Only reruns THIS fragment
```

**Rules:**
- `run_every` accepts `"10s"`, `"1m"`, `"1h"`, or `timedelta`
- `st.rerun(scope="fragment")` only reruns the fragment, not the whole app
- Fragments share `st.session_state` with the main app
- Use fragments for: live charts, status panels, auto-refreshing metrics
- Do NOT put navigation or page-level state changes inside fragments

### Layout Patterns

```python
# Sidebar for config/settings
with st.sidebar:
    st.title("Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])

# Columns with weighted widths
col1, col2, col3 = st.columns([2, 1, 1])

# Tabs for page sections
tab1, tab2 = st.tabs(["Overview", "Details"])

# Expander for optional content
with st.expander("Advanced Options"):
    st.checkbox("Enable debug mode")

# Forms batch widget interactions (no rerun until submit)
with st.form("search_form"):
    query = st.text_input("Query")
    st.form_submit_button("Search")

# Modal dialog (separate from main flow)
@st.dialog("Confirm Action")
def confirm_dialog():
    st.write("Are you sure?")
    if st.button("Yes"):
        st.rerun()
```

### HTML in Streamlit (Security Pattern)

```python
# ALWAYS escape user-controlled data in unsafe_allow_html
from html import escape as safe_html

name = user_input  # untrusted
st.markdown(f'<div>{safe_html(name)}</div>', unsafe_allow_html=True)

# NEVER do this:
st.markdown(f'<div>{name}</div>', unsafe_allow_html=True)  # XSS risk!
```

**Rules:**
- Use `html.escape()` (aliased as `safe_html`) for ALL user/API data in HTML
- This applies to `st.markdown(..., unsafe_allow_html=True)` and `st.write(..., unsafe_allow_html=True)`
- API responses from external services are NOT trusted — escape them too
- Streamlit's built-in widgets (`st.text`, `st.write`, `st.dataframe`) auto-escape

### File I/O Patterns

```python
# Always specify encoding for text files
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Atomic writes to prevent corruption on crash
import tempfile, os
def atomic_write(path, content):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise

# Path traversal prevention
from pathlib import Path
def safe_path(user_path, allowed_root):
    resolved = Path(user_path).resolve()
    if not resolved.is_relative_to(Path(allowed_root).resolve()):
        raise ValueError("Path outside allowed directory")
    return resolved
```

### Multi-Page Navigation

```python
# Dictionary-based page routing (single-file pattern)
_PAGE_HANDLERS = {
    "dashboard": _page_dashboard,
    "settings": _page_settings,
}

page = st.sidebar.radio("Navigate", list(_PAGE_HANDLERS.keys()))
_PAGE_HANDLERS[page]()
```

### Performance Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `AirflowClient()` inside `@st.cache_data` function | Re-creates HTTP session on every cache miss | Use `@st.cache_resource` for the client factory |
| Reading YAML/JSON files in a loop | N+1 file I/O per loop iteration | Load once before the loop |
| `datetime.now()` naive mixed with tz-aware | `TypeError: can't subtract offset-naive and offset-aware` | Use `datetime.now(ZoneInfo("Region/City"))` consistently |
| Mutating `@st.cache_data` return values | Mutations persist across reruns for same user | Copy first or use immutable patterns |
| `st_autorefresh` from `streamlit_autorefresh` | External dependency, limited control | Use `@st.fragment(run_every="Ns")` instead |

## Commands

```bash
# Run Streamlit app
streamlit run app.py --server.port 8501 --server.address "0.0.0.0" --server.headless true

# Run with auto-reload on file changes
streamlit run app.py --server.runOnSave true

# Clear all caches programmatically
st.cache_data.clear()
st.cache_resource.clear()

# Check Streamlit version
streamlit --version
```

## Resources

- **Official Docs**: https://docs.streamlit.io/develop/api-reference
- **Caching Guide**: https://docs.streamlit.io/develop/concepts/architecture/caching
- **Session State**: https://docs.streamlit.io/develop/concepts/architecture/session-state
- **Fragments**: https://docs.streamlit.io/develop/concepts/architecture/fragments
- **Context7**: `/streamlit/docs` — 1800+ code snippets

# Changelog

All notable changes to Kharōn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.0-pre] — 2026-04-28

### Added

- **Platform core**: Full Kharōn script orchestration platform with Airflow 3.x + Streamlit
- **7 pages**: Tablero (dashboard), Procesos, Ver Logs, Monitoreo Global, Salud por Cliente, Nuevo Script, Configuración
- **Airflow 3.x integration**: JWT cookie-based auth, `/api/v2` REST client, health checks, DAG CRUD, log retrieval
- **Script management**: 5-step wizard form to create scripts with validation, preview, and auto-DAG generation
- **3 execution modes**: On-demand (`schedule=None`), Continuous (`@continuous`), Scheduled (cron)
- **Cron scheduling**: Human-readable descriptions in Spanish + quick reference guide
- **Client management**: CRUD with optional logo upload (PNG/JPG/SVG/BMP), automatic color extraction, color picker
- **Client filtering**: Per-page filter in Procesos and Monitoreo
- **KharonOperator**: Custom Airflow operator with ScriptRunner + ScriptMonitor
- **Script health monitoring**: Per-script success rate, consecutive failure tracking, health bars
- **Corporate dark theme**: Custom CSS with Kharōn brand palette, SVG logos in sidebar header/footer
- **Typography system**: Google Fonts (Space Grotesk for headings, DM Sans for body, JetBrains Mono for code)
- **Accent color system**: `#3b82f6` blue as primary action color across all CTAs and active states
- **Design audit**: 25 improvements identified and implemented across CRITICAL/HIGH/MEDIUM priorities
- **Metric cards**: Top accent border per-status color, icons, hover lift animation
- **Sidebar navigation**: Active state with blue border-left accent, full-width buttons
- **Status indicators**: CSS circles replacing emoji (cross-platform consistent), pulse animation for running state
- **Step progress indicator**: Connected circles with checkmarks for completed steps
- **Summary bar**: Scannable status overview in Procesos page
- **Mobile responsive design**: Media queries for `< 768px` and `< 480px`, touch targets, collapsible sidebar
- **Page subtitles**: Contextual description under each page title
- **Review step**: Card-styled summary with row-by-row layout
- **Registry info**: Formatted key-value table replacing raw JSON dump
- **E2E tests**: Playwright test suite for client tags and webapp flows
- **Design audit document**: `DESIGN_AUDIT.md` with 25 prioritized improvements

### Changed

- Metric cards: flat rectangles → accent-bordered cards with icons and hover animation
- Sidebar buttons: generic gray → active state with blue border-left
- Status dots: emoji (🟢🔴🟡) → CSS circles with `pulse-dot` animation
- Step progress: invisible gray boxes → connected circles with ✓ checkmarks
- Primary buttons: barely visible → high-contrast `#3b82f6` blue
- Background: flat `#0A0F18` → radial gradient (desktop), flat (mobile)
- Donut chart: no segment labels → inside labels at 14px with radial orientation
- Expander charts: 250px → 300px height
- `st.balloons()` → professional `st.toast()` on script creation
- Badge sizing: `2px 10px` / `0.78em` → `4px 14px` / `0.82em`
- Dividers in Configuración and Tablero → subtle spacing

### Removed

- Dead sidebar client filter selectbox (no functionality, `client_filter` session state)
- Unused `_filter_by_client()` and `_get_client_filter_options()` functions
- Duplicate `.metric-card` CSS block
- Conflicting `baseButton-primary` sidebar override

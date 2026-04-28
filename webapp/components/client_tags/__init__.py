import json
import streamlit.components.v1 as components

_HTML = """<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; padding: 4px 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .tag {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 10px; border-radius: 14px;
    font-size: 0.82em; font-weight: 600; white-space: nowrap;
    transition: opacity 0.15s;
  }}
  .tag:hover {{ opacity: 0.85; }}
  .tag-x {{
    cursor: pointer; font-size: 0.8em; opacity: 0.45;
    background: none; border: none; padding: 0 2px;
    line-height: 1; font-weight: 700; color: inherit;
  }}
  .tag-x:hover {{ opacity: 1; color: #ef4444; }}
</style>
</head>
<body>
<div class="tags" id="tags"></div>
<script>
  const clients = {data_json};
  const el = document.getElementById('tags');
  clients.forEach(c => {{
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.style.backgroundColor = c.bg;
    tag.style.color = c.color;
    tag.textContent = c.icon + ' ' + c.name;
    const x = document.createElement('button');
    x.className = 'tag-x';
    x.textContent = '\\u2715';
    x.onclick = () => {{
      tag.style.opacity = '0.3';
      x.textContent = '...';
      const url = new URL(window.parent.location.href);
      url.searchParams.set('delete_client', c.id);
      window.parent.location.href = url.toString();
    }};
    tag.appendChild(x);
    el.appendChild(tag);
  }});
</script>
</body>
</html>"""


def render_client_tags(clients: list) -> None:
    data = []
    for c in clients:
        color = c.get("color", "#374151")
        try:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            bg = f"rgba({r},{g},{b},0.18)"
        except Exception:
            bg = "rgba(55,65,81,0.18)"
        data.append({
            "id": c.get("id", ""),
            "name": c.get("name", ""),
            "color": color,
            "bg": bg,
            "icon": c.get("icon", "🏢"),
        })

    html = _HTML.replace("{data_json}", json.dumps(data))
    components.html(html, height=50)

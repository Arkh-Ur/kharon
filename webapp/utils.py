"""Shared utilities for Kharōn webapp."""

import io
import re
from typing import Any, List, Optional

_WEEKDAYS = {
    "0": "domingo", "1": "lunes", "2": "martes", "3": "miércoles",
    "4": "jueves", "5": "viernes", "6": "sábado", "7": "domingo",
}


def describe_cron(expr: str) -> str:
    """Human-readable Spanish description of a cron expression."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return expr
    minute, hour, dom, month, dow = parts
    try:
        if dow != "*" and dom == "*" and month == "*" and hour != "*" and minute != "*":
            day_name = _WEEKDAYS.get(dow, f"día {dow}")
            return f"Cada {day_name} a las {int(hour):02d}:{int(minute):02d}"
        if dom == "*" and month == "*" and dow == "*":
            if hour.startswith("*/"):
                return f"Cada {hour[2:]} horas"
            if minute.startswith("*/"):
                return f"Cada {minute[2:]} minutos"
            if hour != "*" and minute != "*":
                return f"Todos los días a las {int(hour):02d}:{int(minute):02d}"
        if dom != "*" and month == "*" and hour != "*" and minute != "*":
            return f"El día {int(dom)} de cada mes a las {int(hour):02d}:{int(minute):02d}"
    except (ValueError, TypeError):
        pass
    return expr


def extract_primary_color(img_bytes: bytes, filename: str) -> Optional[str]:
    """Extract the dominant non-background color from an image file.

    Handles PNG/JPG/BMP via numpy binning and SVG via regex parsing.
    Returns a hex color string or None if extraction fails.
    """
    if filename.lower().endswith(".svg"):
        return _extract_svg_color(img_bytes)
    return _extract_raster_color(img_bytes)


def _extract_raster_color(img_bytes: bytes) -> Optional[str]:
    try:
        from PIL import Image
        import numpy as np

        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        img = img.resize((64, 64), Image.LANCZOS)
        pixels = np.array(img)  # (64, 64, 4)

        alpha = pixels[:, :, 3].flatten()
        rgb = pixels[:, :, :3].reshape(-1, 3).astype(float)

        # Keep only sufficiently opaque pixels
        visible = rgb[alpha > 128]
        if len(visible) == 0:
            visible = rgb

        r, g, b = visible[:, 0], visible[:, 1], visible[:, 2]

        # Exclude near-black and near-white
        is_dark = (r < 30) & (g < 30) & (b < 30)
        is_light = (r > 225) & (g > 225) & (b > 225)

        # Compute HSV saturation to prefer vivid colors
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        saturation = np.where(max_c > 0, (max_c - min_c) / max_c, 0.0)

        colorful = visible[~is_dark & ~is_light & (saturation > 0.15)]
        if len(colorful) == 0:
            colorful = visible[~is_dark & ~is_light]
        if len(colorful) == 0:
            colorful = visible

        # Find dominant color by 3-bit binning (32-unit buckets per channel)
        cf = colorful.astype(int)
        bin_keys = (cf[:, 0] // 32) * 64 + (cf[:, 1] // 32) * 8 + (cf[:, 2] // 32)
        unique, counts = np.unique(bin_keys, return_counts=True)
        dominant_bin = unique[np.argmax(counts)]
        dominant_pixels = colorful[bin_keys == dominant_bin]
        avg = dominant_pixels.mean(axis=0).astype(int)

        return f"#{avg[0]:02x}{avg[1]:02x}{avg[2]:02x}"
    except Exception:
        return None


def _extract_svg_color(svg_bytes: bytes) -> Optional[str]:
    try:
        text = svg_bytes.decode("utf-8", errors="ignore")
        hex_colors = re.findall(
            r'(?:fill|stroke|color)\s*[=:]\s*["\']?\s*(#[0-9a-fA-F]{3,6})',
            text,
        )
        for color in hex_colors:
            hex_c = color.lstrip("#")
            if len(hex_c) == 3:
                hex_c = "".join(c * 2 for c in hex_c)
            if len(hex_c) != 6:
                continue
            rv, gv, bv = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
            if rv < 30 and gv < 30 and bv < 30:
                continue
            if rv > 225 and gv > 225 and bv > 225:
                continue
            return f"#{hex_c}"
    except Exception:
        pass
    return None


def format_airflow_log(content: Any) -> str:
    """Convierte el campo 'content' de Airflow 3.x a texto legible.

    Airflow 3.x devuelve los logs como lista de event-dicts:
      [{"timestamp": "...", "event": "msg", "level": "info", ...}, ...]
    Esta función los formatea como líneas de log clásicas.
    Si 'content' ya es string, lo devuelve tal cual.
    """
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return str(content) if content else ""

    lines: List[str] = []
    for entry in content:
        if not isinstance(entry, dict):
            lines.append(str(entry))
            continue

        event = entry.get("event", "")

        # Marcadores de grupo — convertir a separador visual
        if event == "::endgroup::":
            continue
        if event.startswith("::group::"):
            title = event[len("::group::"):]
            lines.append(f"{'─' * 4} {title} {'─' * 4}")
            # Mostrar rutas de log si vienen en sources
            for src in entry.get("sources", []):
                lines.append(f"  {src}")
            continue

        ts = entry.get("timestamp", "")
        level = (entry.get("level") or "").upper().ljust(5)

        if ts:
            # "2026-04-27T13:41:55.577468Z" → "2026-04-27 13:41:55"
            ts_short = ts[:19].replace("T", " ")
            lines.append(f"{ts_short} [{level}] {event}")
        else:
            lines.append(event)

        # Formatear traceback si está presente
        error_detail = entry.get("error_detail")
        if isinstance(error_detail, list):
            for err in error_detail:
                if not isinstance(err, dict):
                    continue
                exc_type = err.get("exc_type", "")
                exc_value = err.get("exc_value", "")
                if exc_type or exc_value:
                    lines.append(f"  {exc_type}: {exc_value}")
                for frame in err.get("frames", []):
                    if isinstance(frame, dict):
                        lines.append(
                            f"    File {frame.get('filename','?')}, "
                            f"line {frame.get('lineno','?')}, "
                            f"in {frame.get('name','?')}"
                        )

    return "\n".join(lines)

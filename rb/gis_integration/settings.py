import json
import os
from copy import deepcopy
from typing import Any, Dict, Optional, List

import frappe


_CACHED: Optional[Dict[str, Any]] = None
_SOURCE_PATHS: List[str] = []


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_gis_config() -> Dict[str, Any]:
    """Load app config and merge with site-level overrides under gis_integration.
    Site values override app values, but missing keys fall back to app defaults.
    """
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    app_cfg: Dict[str, Any] = {}
    global _SOURCE_PATHS
    _SOURCE_PATHS = []
    # enumerate candidate paths robustly
    candidates = []
    try:
        candidates.append(frappe.get_app_path("rb", "rb", "gis_integration", "config.json"))
    except Exception:
        pass
    # Fallbacks for legacy/alternate paths
    try:
        candidates.append(os.path.join(frappe.get_app_path("rb"), "rb", "gis_integration", "config.json"))
    except Exception:
        pass
    # local to this file
    candidates.append(os.path.join(os.path.dirname(__file__), "config.json"))

    for path in candidates:
        if path and os.path.exists(path):
            _SOURCE_PATHS.append(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    app_cfg = json.load(f)
                    break
            except Exception:
                continue

    conf = frappe.get_conf() or {}
    site_override = conf.get("gis_integration") or {}

    _CACHED = _deep_merge(app_cfg, site_override)
    # attach meta for debugging
    _CACHED.setdefault("_meta", {})["source_paths"] = _SOURCE_PATHS
    return _CACHED


def get_doctype_config(doctype: str) -> Optional[Dict[str, Any]]:
    cfg = load_gis_config()
    collections = cfg.get("collections") or {}
    return collections.get(doctype)


def clear_gis_config_cache():
    global _CACHED
    _CACHED = None

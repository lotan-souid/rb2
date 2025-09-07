import logging
import frappe
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from .settings import load_gis_config


class PGFeatureServConnector:
    """Connector to pg_featureserv for fetching GIS features as GeoJSON."""

    def __init__(self):
        # Prefer site-level conf, then integration-config file, then default
        conf = frappe.get_conf() or {}
        integration_conf = conf.get("gis_integration") or {}
        config_file = load_gis_config() or {}
        self.base_url = (
            integration_conf.get("pg_featureserv_url")
            or conf.get("pg_featureserv_url")
            or config_file.get("pg_featureserv_url")
            or "http://localhost:9000"
        ).rstrip("/")
        self.timeout = int(
            integration_conf.get("pg_featureserv_timeout")
            or conf.get("pg_featureserv_timeout", 30)
        )
        self.headers = {"Accept": "application/geo+json", "Content-Type": "application/json"}
        api_key = integration_conf.get("pg_featureserv_api_key") or conf.get("pg_featureserv_api_key")
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        # Compatible logger across Frappe versions
        try:
            get_logger = getattr(frappe, "get_logger", None)
            if callable(get_logger):
                self.log = get_logger("gis")
            else:
                self.log = frappe.logger("gis")  # older API
        except Exception:
            self.log = logging.getLogger("frappe.gis")

    def check_connectivity(self) -> Dict[str, Any]:
        """Check basic connectivity to pg_featureserv and list collections."""
        url = f"{self.base_url}/collections"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            return {
                "ok": resp.status_code == 200,
                "status": resp.status_code,
                "url": url,
                "error": None if resp.status_code == 200 else resp.text[:500],
            }
        except requests.RequestException as e:
            return {"ok": False, "status": None, "url": url, "error": str(e)}

    def _cache_key(self, *parts: str) -> str:
        return "gis:" + ":".join([p.replace(":", "_") for p in parts])

    def get_feature_by_id(self, collection: str, feature_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single Feature by ID with optional cache."""
        cache_key = self._cache_key("f", collection, str(feature_id))
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return frappe.parse_json(cached)

        url = f"{self.base_url}/collections/{collection}/items/{feature_id}.json"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                frappe.cache().set_value(cache_key, frappe.as_json(data), expires_in_sec=300)
                return data
            if resp.status_code == 404:
                self.log.warning(f"Feature not found: {collection}/{feature_id}")
                return None
            self.log.error(f"Error fetching feature: {resp.status_code} - {resp.text}")
            return None
        except requests.RequestException as e:
            self.log.error(f"Request error: {e}")
            frappe.throw("Failed to connect to GIS server")

    def get_features_by_property(self, collection: str, prop: str, value: Any, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Fetch Features by property filter (CQL), sanitized and limited."""
        safe_value = str(value).replace("'", "''")
        params = {"filter": f"{prop}='{safe_value}'", "limit": min(max(int(limit), 1), 500)}
        url = f"{self.base_url}/collections/{collection}/items.json?{urlencode(params)}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            self.log.error(f"Error fetching features: {resp.status_code} - {resp.text}")
            return None
        except requests.RequestException as e:
            self.log.error(f"Request error: {e}")
            return None

    @staticmethod
    def validate_geojson(obj: Dict[str, Any]) -> bool:
        if not isinstance(obj, dict) or "type" not in obj:
            return False
        valid = {
            "Feature",
            "FeatureCollection",
            "Point",
            "LineString",
            "Polygon",
            "MultiPoint",
            "MultiLineString",
            "MultiPolygon",
        }
        return obj.get("type") in valid

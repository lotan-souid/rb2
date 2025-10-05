import json
from typing import Optional, Dict, Any, List

import frappe
from frappe import _

from .gis_connector import PGFeatureServConnector
from .settings import get_doctype_config, load_gis_config, clear_gis_config_cache


MAX_GEOJSON_BYTES = int(frappe.conf.get("gis_geojson_max_bytes", 1_000_000))  # default 1MB


@frappe.whitelist()
def fetch_lot_geometry(lot_name: str) -> Optional[str]:
    doc = frappe.get_doc("Lot", lot_name)
    cfg = get_doctype_config("Lot") or {}
    collection = cfg.get("collection", "lots")
    id_field = cfg.get("id_field", "lot_id")
    # Save simplified geometry-only FC into Geolocation field `location` by default
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")  # "by_id" or "by_property"
    property_name = cfg.get("property_name")
    fallback_props = cfg.get("fallback_properties") or []

    feature_id = doc.get(id_field)
    if not feature_id:
        frappe.msgprint(_(f"No {id_field} found on this Lot"))
        return None

    conn = PGFeatureServConnector()
    feature = None
    if fetch_mode == "by_property" or property_name:
        property_name = property_name or id_field
        fc = conn.get_features_by_property(collection, property_name, feature_id, limit=1)
        if fc and fc.get("features"):
            feature = fc["features"][0]
    else:
        feature = conn.get_feature_by_id(collection, feature_id)

    # Try configured fallbacks by property if primary attempt failed
    if not feature and fallback_props:
        for fp in fallback_props:
            val = doc.get(fp)
            if not val:
                continue
            fc = conn.get_features_by_property(collection, fp, val, limit=1)
            if fc and fc.get("features"):
                feature = fc["features"][0]
                break

    if not feature:
        msg = _(
            "No geometry found in GIS for {0} using {1}{2}"
        ).format(
            feature_id,
            f"id_field={id_field}",
            f", fallbacks={','.join(fallback_props)}" if fallback_props else "",
        )
        frappe.msgprint(msg, indicator="orange")
        return None

    geojson_full = convert_to_fc(feature)
    if not conn.validate_geojson(geojson_full):
        frappe.throw(_("Invalid GeoJSON data received from GIS"))

    # Simplify to geometry-only (strip id/properties) for the Geolocation field
    geojson_simple = geometry_only_fc(geojson_full)

    data = json.dumps(geojson_simple, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(
            _("Geometry too large; consider simplifying or reducing precision"),
            indicator="orange",
        )

    # Persist simplified FC into the target field (usually `location` Geolocation)
    try:
        doc.db_set(target_field, data)
    except Exception:
        pass

    # Optionally persist full FC into a separate field if you add one in future

    return data


@frappe.whitelist()
def fetch_cluster_geometry(cluster_name: str) -> Optional[str]:
    """Fetch geometry from GIS for a Cluster document based on config and persist it.
    cluster_name is the DocType name (doc.name), not the cluster_name field value.
    """
    doc = frappe.get_doc("Cluster", cluster_name)
    cfg = get_doctype_config("Cluster") or {}
    collection = cfg.get("collection", "rb_layers.clusters")
    id_field = cfg.get("id_field", "cluster_name")
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")  # "by_id" or "by_property"
    property_name = cfg.get("property_name")
    fallback_props = cfg.get("fallback_properties") or []

    feature_id = doc.get(id_field)
    if not feature_id:
        frappe.msgprint(_(f"No {id_field} found on this Cluster"))
        return None

    conn = PGFeatureServConnector()
    feature = None
    if fetch_mode == "by_property" or property_name:
        property_name = property_name or id_field
        fc = conn.get_features_by_property(collection, property_name, feature_id, limit=1)
        if fc and fc.get("features"):
            feature = fc["features"][0]
    else:
        feature = conn.get_feature_by_id(collection, feature_id)

    if not feature and fallback_props:
        for fp in fallback_props:
            val = doc.get(fp)
            if not val:
                continue
            fc = conn.get_features_by_property(collection, fp, val, limit=1)
            if fc and fc.get("features"):
                feature = fc["features"][0]
                break

    if not feature:
        msg = _(
            "No geometry found in GIS for {0} using {1}{2}"
        ).format(
            feature_id,
            f"id_field={id_field}",
            f", fallbacks={','.join(fallback_props)}" if fallback_props else "",
        )
        frappe.msgprint(msg, indicator="orange")
        return None

    geojson_full = convert_to_fc(feature)
    if not conn.validate_geojson(geojson_full):
        frappe.throw(_("Invalid GeoJSON data received from GIS"))

    geojson_simple = geometry_only_fc(geojson_full)
    data = json.dumps(geojson_simple, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(
            _("Geometry too large; consider simplifying or reducing precision"),
            indicator="orange",
        )

    try:
        doc.db_set(target_field, data)
    except Exception:
        pass

    return data


@frappe.whitelist()
def fetch_fixture_compensation_geometry(fixture_name: str) -> Optional[str]:
    """Fetch geometry for Fixture Compensation based on GIS config and persist it."""
    doc = frappe.get_doc("Fixture Compensation", fixture_name)
    cfg = get_doctype_config("Fixture Compensation") or {}
    collection = cfg.get("collection", "rb_layers.fixture_compensation")
    id_field = cfg.get("id_field", "name")
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")
    property_name = cfg.get("property_name")
    fallback_props = cfg.get("fallback_properties") or []

    feature_id = doc.get(id_field) if id_field != "name" else doc.name
    if not feature_id:
        # As a last resort, use the document name which carries the FXC-* autoname
        feature_id = doc.name

    if not feature_id:
        frappe.msgprint(_(f"No {id_field} found on this Fixture Compensation"))
        return None

    conn = PGFeatureServConnector()
    feature = None
    if fetch_mode == "by_property" or property_name:
        property_name = property_name or id_field
        fc = conn.get_features_by_property(collection, property_name, feature_id, limit=1)
        if fc and fc.get("features"):
            feature = fc["features"][0]
    else:
        feature = conn.get_feature_by_id(collection, feature_id)

    if not feature and fallback_props:
        for fp in fallback_props:
            val = doc.get(fp)
            if not val:
                continue
            fc = conn.get_features_by_property(collection, fp, val, limit=1)
            if fc and fc.get("features"):
                feature = fc["features"][0]
                break

    if not feature:
        msg = _(
            "No geometry found in GIS for {0} using {1}{2}"
        ).format(
            feature_id,
            f"id_field={id_field}",
            f", fallbacks={','.join(fallback_props)}" if fallback_props else "",
        )
        frappe.msgprint(msg, indicator="orange")
        return None

    geojson_full = convert_to_fc(feature)
    if not conn.validate_geojson(geojson_full):
        frappe.throw(_("Invalid GeoJSON data received from GIS"))

    geojson_simple = geometry_only_fc(geojson_full)
    data = json.dumps(geojson_simple, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(
            _("Geometry too large; consider simplifying or reducing precision"),
            indicator="orange",
        )

    try:
        doc.db_set(target_field, data)
    except Exception:
        pass

    return data

@frappe.whitelist()
def fetch_geometry_by_property(
    doctype: str,
    docname: str,
    field_name: str,
    collection: str,
    property_name: str,
    property_value: str,
    limit: int = 100,
) -> Optional[str]:
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("You don't have permission to update this document"))

    conn = PGFeatureServConnector()
    fc = conn.get_features_by_property(collection, property_name, property_value, limit)
    if not fc or not fc.get("features"):
        frappe.msgprint(_("No geometry found for {0}={1}").format(property_name, property_value))
        return None

    data = json.dumps(fc, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(
            _("Geometry too large; consider narrowing the filter or simplifying"),
            indicator="orange",
        )

    frappe.db.set_value(doctype, docname, field_name, data)
    return data


@frappe.whitelist()
def sync_all_lot_geometries(collection: Optional[str] = None) -> Dict[str, Any]:
    lots = frappe.get_all(
        "Lot",
        filters={"lot_id": ["!=", ""]},
        fields=["name", "lot_id"],
    )
    cfg = get_doctype_config("Lot") or {}
    collection = cfg.get("collection", "lots")
    id_field = cfg.get("id_field", "lot_id")
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")
    property_name = cfg.get("property_name")

    conn = PGFeatureServConnector()
    ok, errs, details = 0, 0, []

    for lot in lots:
        coll = collection
        try:
            feature = None
            feature_id = lot.get(id_field) or lot.get("lot_id")
            if fetch_mode == "by_property" or property_name:
                pn = property_name or id_field
                fc = conn.get_features_by_property(coll, pn, feature_id, limit=1)
                if fc and fc.get("features"):
                    feature = fc["features"][0]
            else:
                feature = conn.get_feature_by_id(coll, feature_id)
            if feature:
                fc_full = convert_to_fc(feature)
                fc_simple = geometry_only_fc(fc_full)
                try:
                    frappe.db.set_value("Lot", lot.name, target_field, json.dumps(fc_simple, ensure_ascii=False))
                except Exception:
                    pass
                ok += 1
            else:
                errs += 1
                details.append(f"No geometry for Lot {lot['name']}")
        except Exception as e:
            errs += 1
            details.append(f"Error updating {lot['name']}: {e}")

    return {"success": ok, "errors": errs, "error_details": details[:10]}


@frappe.whitelist()
def sync_all_cluster_geometries(collection: Optional[str] = None) -> Dict[str, Any]:
    """Bulk sync for Clusters that have an id_field value configured (default cluster_name)."""
    clusters = frappe.get_all(
        "Cluster",
        filters={"cluster_name": ["!=", ""]},
        fields=["name", "cluster_name"],
    )
    cfg = get_doctype_config("Cluster") or {}
    collection = cfg.get("collection", "rb_layers.clusters")
    id_field = cfg.get("id_field", "cluster_name")
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")
    property_name = cfg.get("property_name")

    conn = PGFeatureServConnector()
    ok, errs, details = 0, 0, []

    for cl in clusters:
        coll = collection
        try:
            feature = None
            feature_id = cl.get(id_field) or cl.get("cluster_name")
            if fetch_mode == "by_property" or property_name:
                pn = property_name or id_field
                fc = conn.get_features_by_property(coll, pn, feature_id, limit=1)
                if fc and fc.get("features"):
                    feature = fc["features"][0]
            else:
                feature = conn.get_feature_by_id(coll, feature_id)
            if feature:
                fc_full = convert_to_fc(feature)
                fc_simple = geometry_only_fc(fc_full)
                try:
                    frappe.db.set_value("Cluster", cl.name, target_field, json.dumps(fc_simple, ensure_ascii=False))
                except Exception:
                    pass
                ok += 1
            else:
                errs += 1
                details.append(f"No geometry for Cluster {cl['name']}")
        except Exception as e:
            errs += 1
            details.append(f"Error updating {cl['name']}: {e}")

    return {"success": ok, "errors": errs, "error_details": details[:10]}


@frappe.whitelist()
def sync_all_fixture_compensation_geometries() -> Dict[str, Any]:
    """Bulk sync for Fixture Compensation records based on configured GIS mapping."""
    fixtures = frappe.get_all("Fixture Compensation", pluck="name")
    ok, errs, details = 0, 0, []

    for fx_name in fixtures:
        try:
            data = fetch_fixture_compensation_geometry(fx_name)
            if data:
                ok += 1
            else:
                errs += 1
                details.append(f"No geometry for Fixture Compensation {fx_name}")
        except Exception as e:
            errs += 1
            details.append(f"Error updating {fx_name}: {e}")

    return {"success": ok, "errors": errs, "error_details": details[:10]}


@frappe.whitelist()
def get_fixture_compensation_coords(
    doctype: str,
    filters: Optional[List[Dict[str, Any]]] = None,
    type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return GeoJSON features for Fixture Compensation Map View."""
    from frappe.geo import utils as geo_utils

    filters_sql = geo_utils.get_coords_conditions(doctype, filters)[4:]

    if filters_sql:
        rows = frappe.db.sql(
            f"""SELECT name, location FROM `tab{doctype}` WHERE {filters_sql}""",
            as_dict=True,
        )
    else:
        rows = frappe.get_all(doctype, fields=["name", "location"])

    coords = []
    for row in rows:
        location = row.get("location")
        if not location:
            continue
        coords.append({"name": row["name"], "location": location})

    return geo_utils.convert_to_geojson("location_field", coords)


def convert_to_fc(data: Dict[str, Any]) -> Dict[str, Any]:
    t = data.get("type")
    if t == "FeatureCollection":
        return data
    if t == "Feature":
        return {"type": "FeatureCollection", "features": [data]}
    # Geometry only
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": data, "properties": {}}],
    }

def geometry_only_fc(fc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip id and properties from each feature, keep geometry only."""
    fc = convert_to_fc(fc)
    simple = {"type": "FeatureCollection", "features": []}
    for feat in fc.get("features", []):
        simple["features"].append({
            "type": "Feature",
            "properties": {},
            "geometry": feat.get("geometry"),
        })
    return simple


@frappe.whitelist()
def gis_healthcheck(doctype: str = "Lot") -> Dict[str, Any]:
    """Simple healthcheck to debug connectivity and config used by the server."""
    cfg = get_doctype_config(doctype) or {}
    collection = cfg.get("collection") or ""
    conf = frappe.get_conf() or {}
    integ_conf = conf.get("gis_integration") or {}
    conn = PGFeatureServConnector()
    probe = conn.check_connectivity()

    # Example URLs the server will try
    examples = []
    if collection:
        examples.append(f"{conn.base_url}/collections/{collection}")
        examples.append(f"{conn.base_url}/collections/{collection}/items?limit=1")

    return {
        "ok": bool(probe.get("ok")),
        "base_url": conn.base_url,
        "timeout": conn.timeout,
        "collection": collection,
        "status": probe.get("status"),
        "error": probe.get("error"),
        "config_sources": {
            "site_conf_has_gis_integration": bool(integ_conf),
            "has_app_config_file": bool(load_gis_config()),
        },
        "config_meta": (load_gis_config() or {}).get("_meta"),
        "examples": examples,
    }


@frappe.whitelist()
def gis_reload_config() -> Dict[str, Any]:
    clear_gis_config_cache()
    cfg = load_gis_config()
    return {"reloaded": True, "config": cfg}

@frappe.whitelist()
def gis_get_client_config(doctype: str) -> Dict[str, Any]:
    cfg = load_gis_config() or {}
    dt_cfg = get_doctype_config(doctype) or {}
    return {
        "basemaps": cfg.get("basemaps") or {},
        "map": (dt_cfg.get("map") if isinstance(dt_cfg, dict) else None) or {},
    }

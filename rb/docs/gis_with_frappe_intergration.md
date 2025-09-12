# מדריך אינטגרציית GIS עם Frappe — גרסת עבודה 1.2 (ספטמבר 2025)

> מסמך זה מרחיב ומשפר את הטיוטה שהעברת. הוספתי בדיקות תקינות, שיקולי אבטחה וביצועים, קוד קשיח יותר (עם cache, לוגרים ושמירה בטוחה), והפרדות ברורות בין DEV/PROD. אפשר להטמיע חלקים בהדרגה.

---

## TL;DR / Quick Start

1. **PostGIS**: ודאו שקיימת שכבה/טבלה `rb_layers.lots` (או אחרת) עם שדה מזהה תואם (`lotId`) ואינדקסים מתאימים.
2. **pg_featureserv**: זמינות של `collections/rb_layers.lots` ושורת דוגמה עובדת: `/collections/rb_layers.lots/items.json?filter=lotId='...'&limit=1`.
3. **Frappe (Lot)**: משתמשים בשדות קיימים `lot_id` (מזהה) ו־`location` (Geolocation) בלבד. אין צורך בשדות נוספים.
3.1 **Frappe (Cluster)**: משתמשים בשדות קיימים `cluster_name` (מזהה) ו־`location` (Geolocation).
4. **קובץ קונפיג**: `rb/rb/gis_integration/config.json` או `site_config.json`→`gis_integration` להגדרת `pg_featureserv_url`, ה־collection, ושמות השדות.
5. **כפתור Fetch** ימשוך GeoJSON, יפשט אותו ל־FeatureCollection עם geometry בלבד, וישמור אותו בשדה `location`. הצגה בטופס מתבצעת עם Leaflet.
6. **בריאות/דיבוג**: השתמשו ב־API `rb.gis_integration.api.gis_healthcheck` ובלוג `logs/gis.log`.

---

## מה חדש לעומת הטיוטה המקורית (v1.2)

- ✅ שימוש ב־`lot_id` כמזהה יחיד; בוטלו `gis_feature_id`, `gis_collection`, `lot_location`.
- ✅ שדה היעד הוא `location` (Geolocation) שמקבל FeatureCollection “נקי” (רק geometry, ללא id/‏properties).
- ✅ שמירת פוליגון בצד הלקוח והצגה עם Leaflet, ללא תלות ב־Geolocation לרינדור.
- ✅ קובץ קונפיג מרכזי עם Merge לסביבת `site_config.json` ו־healthcheck שרת.
- ✅ המרות ל־`.json` ב־pg_featureserv (`items.json`, `items/{id}.json`).
- ✅ Logger תואם גרסאות, ולוג ייעודי `gis.log`.

---

## ארכיטקטורה בתמצית

- **Frappe**: מציג ושומר FeatureCollection “נקי” בשדה `location` (Geolocation). הצגה אינטראקטיבית עם Leaflet.
- **PostGIS**: מקור האמת הגיאומטרי (SRID 4326 לתאימות GeoJSON).
- **pg_featureserv**: REST ל־Features (GeoJSON).
- **pg_tileserv**: Tiles向 (矢向矢; MVT) לתצוגה אינטראקטיבית בעתיד (Leaflet/MapLibre).
- **(אופציונלי)** MapStore/GeoServer לשימושים מתקדמים/ארגוניים.

---

## קוד — גרסאות משופרות (קטעים מרכזיים)

### `rb/gis_integration/gis_connector.py`

```python
import frappe
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlencode

class PGFeatureServConnector:
    """חיבור ל-pg_featureserv ומשיכת נתונים גיאוגרפיים."""

    def __init__(self):
        # קריאה מקונפיג אתר/אפליקציה ומיזוג
        conf = frappe.get_conf() or {}
        integration_conf = conf.get("gis_integration") or {}
        config_file = load_gis_config() or {}
        self.base_url = (
            integration_conf.get("pg_featureserv_url")
            or conf.get("pg_featureserv_url")
            or config_file.get("pg_featureserv_url")
            or "http://localhost:9000"
        ).rstrip("/")
        self.timeout = int(integration_conf.get("pg_featureserv_timeout") or conf.get("pg_featureserv_timeout", 30))
        self.headers = {"Accept": "application/geo+json", "Content-Type": "application/json"}
        api_key = integration_conf.get("pg_featureserv_api_key") or conf.get("pg_featureserv_api_key")
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        # Logger תואם גרסאות
        try:
            self.log = (getattr(frappe, "get_logger", None) or frappe.logger)("gis")
        except Exception:
            import logging
            self.log = logging.getLogger("frappe.gis")

    def _cache_key(self, *parts: str) -> str:
        return "gis:" + ":".join([p.replace(":", "_") for p in parts])

    def get_feature_by_id(self, collection: str, feature_id: str) -> Optional[Dict[str, Any]]:
        """משיכת Feature בודד לפי ID, עם Cache אופציונלי."""
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
        """משיכת Features לפי תכונה עם סניטיזציה בסיסית לגרשיים והגבלת תוצאות."""
        safe_value = str(value).replace("'", "''")  # CQL-safe
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
        valid = {"Feature", "FeatureCollection", "Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}
        return obj.get("type") in valid
```

### `rb/gis_integration/api.py`

```python
import frappe, json
from typing import Optional, Dict, Any
from frappe import _
from .gis_connector import PGFeatureServConnector

MAX_GEOJSON_BYTES = int(frappe.conf.get("gis_geojson_max_bytes", 1_000_000))  # 1MB ברירת מחדל

@frappe.whitelist()
def fetch_lot_geometry(lot_name: str) -> Optional[str]:
    """טעינת גיאומטריה לפי lot_id → שמירה כ-FeatureCollection נקי בשדה `location`."""
    doc = frappe.get_doc("Lot", lot_name)
    cfg = get_doctype_config("Lot") or {}
    collection = cfg.get("collection", "rb_layers.lots")
    id_field = cfg.get("id_field", "lot_id")
    target_field = cfg.get("geometry_target_field", "location")
    fetch_mode = cfg.get("fetch_mode")
    property_name = cfg.get("property_name")

    feature_id = doc.get(id_field)
    if not feature_id:
        frappe.msgprint(_(f"No {id_field} found on this Lot"))
        return None

    conn = PGFeatureServConnector()
    feature = None
    if fetch_mode == "by_property" or property_name:
        pn = property_name or id_field
        fc = conn.get_features_by_property(collection, pn, feature_id, limit=1)
        if fc and fc.get("features"):
            feature = fc["features"][0]
    else:
        feature = conn.get_feature_by_id(collection, feature_id)

    if not feature:
        frappe.msgprint(_("No geometry found in GIS for ID: {0}").format(feature_id))
        return None

    full_fc = convert_to_fc(feature)
    if not conn.validate_geojson(full_fc):
        frappe.throw(_("Invalid GeoJSON data received from GIS"))

    simple_fc = geometry_only_fc(full_fc)  # הסרה של id ו-properties, השארת geometry בלבד
    data = json.dumps(simple_fc, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(_("Geometry too large; consider simplifying or reducing precision"), indicator="orange")

    doc.db_set(target_field, data)
    return data

@frappe.whitelist()
def fetch_geometry_by_property(doctype: str, docname: str, field_name: str, collection: str, property_name: str, property_value: str, limit: int = 100) -> Optional[str]:
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("You don't have permission to update this document"))

    conn = PGFeatureServConnector()
    fc = conn.get_features_by_property(collection, property_name, property_value, limit)
    if not fc or not fc.get("features"):
        frappe.msgprint(_("No geometry found for {0}={1}").format(property_name, property_value))
        return None

    data = json.dumps(fc, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_GEOJSON_BYTES:
        frappe.msgprint(_("Geometry too large; consider narrowing the filter or simplifying"), indicator="orange")

    frappe.db.set_value(doctype, docname, field_name, data)
    return data

@frappe.whitelist()
def sync_all_lot_geometries(collection: Optional[str] = None) -> Dict[str, Any]:
    lots = frappe.get_all("Lot", filters={"gis_feature_id": ["!=", ""]}, fields=["name", "gis_feature_id", "gis_collection"])
    conn = PGFeatureServConnector()
    ok, errs, details = 0, 0, []

    for lot in lots:
        coll = collection or lot.get("gis_collection") or "lots"
        try:
            feature = conn.get_feature_by_id(coll, lot.gis_feature_id)
            if feature:
                fc = convert_to_fc(feature)
                frappe.db.set_value("Lot", lot.name, "lot_location", json.dumps(fc, ensure_ascii=False))
                ok += 1
            else:
                errs += 1
                details.append(f"No geometry for Lot {lot['name']}")
        except Exception as e:
            errs += 1
            details.append(f"Error updating {lot['name']}: {e}")

    return {"success": ok, "errors": errs, "error_details": details[:10]}

def convert_to_fc(data: Dict[str, Any]) -> Dict[str, Any]:
    t = data.get("type")
    if t == "FeatureCollection":
        return data
    if t == "Feature":
        return {"type": "FeatureCollection", "features": [data]}
    # Geometry
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": data, "properties": {}}]}


def geometry_only_fc(fc: Dict[str, Any]) -> Dict[str, Any]:
    """פישוט ל-FC בסיסי: הסרת id ו-properties מכל Feature, שמירת geometry בלבד."""
    fc = convert_to_fc(fc)
    out = {"type": "FeatureCollection", "features": []}
    for feat in fc.get("features", []):
        out["features"].append({"type": "Feature", "properties": {}, "geometry": feat.get("geometry")})
    return out
```

---

## דוגמת מיפוי נוספת — Cluster

- Collection: `rb_layers.clusters`
- DocType: `Cluster`
- שדה מזהה ב־Frappe: `cluster_name`
- שדה מזהה ב־GIS: `clusterName`
- שדה יעד לגיאומטריה: `location` (Geolocation)

קונפיג ב־`rb/rb/gis_integration/config.json` תחת `collections.Cluster`:

```json
{
  "collection": "rb_layers.clusters",
  "id_field": "cluster_name",
  "geometry_target_field": "location",
  "fetch_mode": "by_property",
  "property_name": "clusterName"
}
```

התנהגות בטופס:
- בשמירה: אם יש `cluster_name` ואין `location`, המערכת תנסה למשוך ולשמור את הגיאומטריה.
- בעדכון: שינוי של `cluster_name` יוצר תור למשיכת גיאומטריה מחדש.

### Hooks — חיווט Lot

```python
import frappe
from .api import fetch_lot_geometry

def on_lot_update(doc, method):
    if doc.has_value_changed("gis_feature_id") and doc.gis_feature_id:
        frappe.enqueue("custom_app.gis_integration.api.fetch_lot_geometry", lot_name=doc.name, queue="short", timeout=30)

def validate(doc, method):
    # רץ בשמירה; אם יש Feature ID ואין גיאומטריה – ננסה לטעון
    if doc.gis_feature_id and not doc.lot_location:
        try:
            fetch_lot_geometry(doc.name)
        except Exception as e:
            frappe.msgprint(f"Could not fetch geometry automatically: {e}", indicator="orange")
```

### לקוח — `custom_app/public/js/lot_form.js`

```javascript
frappe.ui.form.on('Lot', {
  refresh(frm) {
    if (frm.doc.gis_feature_id) {
      frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_geometry_from_gis(frm), __('GIS Actions'));
      if (!frm.doc.lot_location) {
        frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
      }
      frm.add_custom_button(__('Open Map (tileserv)'), () => open_tiles_map(frm), __('GIS Actions'));
    }
    if (frappe.user.has_role('System Manager')) {
      frm.add_custom_button(__('Sync All Geometries'), () => sync_all_geometries(frm), __('GIS Actions'));
    }
  },
  gis_feature_id(frm) {
    if (frm.doc.gis_feature_id) {
      frappe.confirm(__('GIS Feature ID changed. Fetch the new geometry?'), () => fetch_geometry_from_gis(frm));
    }
  },
  before_save(frm) {
    if (frm.doc.gis_feature_id && !frm.doc.lot_location) {
      frappe.msgprint({ title: __('Missing Geometry'), message: __('This lot has a GIS Feature ID but no geometry.'), indicator: 'orange' });
    }
  }
});

function fetch_geometry_from_gis(frm) {
  frappe.show_alert({ message: __('Fetching geometry from GIS...'), indicator: 'blue' });
  frappe.call({
    method: 'custom_app.gis_integration.api.fetch_lot_geometry',
    args: { lot_name: frm.doc.name, collection: frm.doc.gis_collection || 'lots' },
    callback: () => frm.reload_doc(),
    error: (e) => { frappe.msgprint({ title: __('Error'), message: __('Failed to fetch geometry from GIS'), indicator: 'red' }); console.error(e); }
  });
}

function sync_all_geometries(frm) {
  frappe.confirm(__('This will sync geometries for all lots with GIS Feature IDs. Continue?'), () => {
    frappe.call({
      method: 'custom_app.gis_integration.api.sync_all_lot_geometries',
      args: { collection: frm.doc.gis_collection || 'lots' },
      freeze: true,
      freeze_message: __('Syncing geometries...'),
      callback: (r) => {
        const m = r.message || {}; const indicator = m.errors > 0 ? 'orange' : 'green';
        let msg = __('Sync completed. Success: {0}, Errors: {1}', [m.success || 0, m.errors || 0]);
        if (m.error_details && m.error_details.length) { msg += '<br><br>' + __('Errors:') + '<br>' + m.error_details.join('<br>'); }
        frappe.msgprint({ title: __('Sync Results'), message: msg, indicator });
      }
    });
  });
}

function open_tiles_map(frm) {
  // דוגמה לפתיחה ל־pg_tileserv (להחליף ל-URL הארגוני/MapStore)
  const layer = (frm.doc.gis_collection || 'public.lots');
  const url = `http://your-tileserv:7800/${layer}/{z}/{x}/{y}.pbf`;
  window.open(url, '_blank');
}
```

---

## הגדרות `hooks.py`

```python
# hooks.py

doc_events = {
    "Lot": {
        "on_update": "rb.planning.doctype.lot.lot.on_update"
    }
}
doctype_js = { "Lot": "public/js/lot_form.js" }
```

### לקוח — `rb/public/js/cluster_form.js`

```javascript
frappe.ui.form.on('Cluster', {
  refresh(frm) {
    if (frm.doc.cluster_name) {
      frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_geometry_from_gis(frm), __('GIS Actions'));
      frm.add_custom_button(__('Test GIS Connection'), () => test_gis_connection(frm), __('GIS Actions'));
      if (!frm.doc.location) {
        frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
      }
    }
    if (frappe.user.has_role('System Manager')) {
      frm.add_custom_button(__('Sync All Geometries'), () => sync_all_geometries(frm), __('GIS Actions'));
    }
  },
  cluster_name(frm) {
    if (frm.doc.cluster_name) {
      frappe.confirm(__('Cluster Name changed. Fetch the new geometry?'), () => fetch_geometry_from_gis(frm));
    }
  }
});

function fetch_geometry_from_gis(frm) {
  frappe.call({
    method: 'rb.gis_integration.api.fetch_cluster_geometry',
    args: { cluster_name: frm.doc.name },
    callback: (r) => { if (r && r.message) { frm.doc.location = JSON.stringify(r.message); frm.refresh_field('location'); } }
  });
}

function sync_all_geometries(frm) {
  frappe.call({ method: 'rb.gis_integration.api.sync_all_cluster_geometries', freeze: true });
}

function test_gis_connection(frm) {
  frappe.call({ method: 'rb.gis_integration.api.gis_healthcheck', args: { doctype: 'Cluster' } });
}
```

---

## PostGIS — טבלאות/שכבות והיתרים

```sql
-- טבלת מגרשים בסיסית
CREATE TABLE rb_layers.lots (
  id SERIAL PRIMARY KEY,
  parcel_number VARCHAR(50) UNIQUE,
  area NUMERIC(10,2),
  land_use VARCHAR(100),
  status VARCHAR(50),
  geom GEOMETRY(Polygon, 2039) -- לדוגמה ישראל TM; התאימו לפי מקור הנתונים
);

-- אינדקס מרחבי
CREATE INDEX idx_lots_geom ON rb_layers.lots USING GIST (geom);

-- View ל-GeoJSON ב-WGS84 (4326) לתאימות GeoJSON/Frappe
-- אופציונלי: View ל-4326
CREATE OR REPLACE VIEW rb_layers.lots_view AS
SELECT
  id,
  parcel_number,
  area,
  land_use,
  status,
  ST_AsGeoJSON(ST_Transform(geom, 4326), 6)::json AS geometry
FROM rb_layers.lots;

GRANT SELECT ON rb_layers.lots TO pg_featureserv;
```

> **הערה**: אם המקור כבר ב־4326, השמיטו `ST_Transform`. הפרמטר `6` ב־`ST_AsGeoJSON` מגביל דיוק למניעת קבצים כבדים.

---

## Docker/Network — נקודות חשובות

```yml
- אם Frappe ו־pg_featureserv רצים בקונטיינרים שונים—חברו לאותה רשת Docker והשתמשו בשם השירות (service name) במקום IP.
- אל תשתמשו ב־`localhost` מתוך קונטיינר כדי לגשת לשירות ברמת המארח.
- ודאו שהפורט 9000 פתוח ונגיש מהיכן ש־Frappe רץ.

```

## אבטחה — צ׳קליסט קצר

- הגבל גישה ל־pg_featureserv/pg_tileserv ברשת פנימית (או מאחורי reverse-proxy עם OAuth2/OpenID Connect).
- השתמשו ב־API key/Token בין Frappe ↔ GIS; אל תשמרו סודות בקוד.
- אפשרו CORS רק מכתובות ה־Frappe.
- שקלו **Row-Level Security**/Views עם שדות מסוננים.
- לוגים נפרדים ל־GIS (`frappe.get_logger("gis")`) וניטור תקלות.

---

## ביצועים — צ׳קליסט קצר

- גבילו **דיוק**/כמות קואורדינטות לפי צורך (ב־DB או בצד שרת).
- גבילו **גודל GeoJSON** (קונפיג `gis_geojson_max_bytes`).
- השתמשו ב־Cache קריאות ו־enqueue לפעולות המוניות.
- הציגו ב־UI את ה־FeatureCollection מתוך `location`; עבור רקעים כבדים שקלו tiles.

---

## בדיקות יחידה — Mocking

```python
# tests/test_gis_integration.py
import json, frappe, unittest
from unittest.mock import patch
from custom_app.gis_integration.gis_connector import PGFeatureServConnector

class TestGIS(unittest.TestCase):
    @patch('requests.get')
    def test_get_feature_by_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {"type":"Feature","geometry":{"type":"Point","coordinates":[34.85,31.04]}}
        conn = PGFeatureServConnector()
        f = conn.get_feature_by_id('lots', '123')
        self.assertEqual(f.get('type'), 'Feature')
```

---

## שימוש — זרימות עיקריות

- **יצירת Lot** → הזנת `lot_id` → לחיצה על **Fetch Geometry from GIS** → FeatureCollection נקי נשמר בשדה `location` ומצויר במפה.
- **עדכון מזהה** (`lot_id`) → `on_update` יזניק משיכה מחדש.
- **סנכרון המוני** → כפתור למנהלי מערכת.

---

## מילון מונחים (תמצית)

- **GeoJSON / Feature / FeatureCollection** — פורמט JSON למידע גיאוגרפי.
- **SRID 4326** — קואורדינטות `lon,lat` (WGS84) — נדרש ל־GeoJSON.
- **MVT** — Mapbox Vector Tiles, לתצוגה מהירה ע"י tileserv.

---

## המשך דרך

1. הפעלה בסביבת DEV עם בסיס נתונים קטן.
2. בדיקת זרימות ושמירת GeoJSON.
3. הוספת MapLibre/Leaflet למסך מפה אינטראקטיבי (שלב 2).
4. הוספת **עריכה** ושמירה חזרה ל־PostGIS (שלב 3, עם ולידציה והיסטוריית שינויים).

---

**גרסה**: 1.2  
**תאריך**: ספטמבר 2025  
**מחבר**: צוות אינטגרציית GIS–Frappe  
**רישיון**: MIT

const ENFORCEMENT_BASEMAP_FALLBACK = {
  default: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }
  }
};

let __enforcement_basemaps = null;
let __enforcement_map_cfg = null;
let __enforcement_bg_key = 'default';
let __enforcement_map;
let __enforcement_geo_layer;
let __enforcement_leaflet_loading;
let __enforcement_base_layer;

frappe.ui.form.on('Enforcement Order', {
  refresh(frm) {
    frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_geometry_from_gis(frm), __('GIS Actions'));
    frm.add_custom_button(__('Open Map (tileserv)'), () => open_tiles_map(frm), __('GIS Actions'));
    frm.add_custom_button(__('Test GIS Connection'), () => test_gis_connection(frm), __('GIS Actions'));
    frm.add_custom_button(__('Change To Background A'), () => toggle_enforcement_background(frm, 'A'), __('GIS Actions'));
    frm.add_custom_button(__('Change To Background B'), () => set_enforcement_background(frm, 'B'), __('GIS Actions'));

    if (frappe.user.has_role('System Manager')) {
      frm.add_custom_button(__('Sync All Geometries'), () => sync_all_geometries(frm), __('GIS Actions'));
    }

    if (frm.is_new()) {
      frm.dashboard.set_headline(__('Save the document to enable GIS actions.'));
    } else if (!frm.doc.location) {
      frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
      setTimeout(() => fetch_geometry_from_gis(frm), 250);
    } else {
      try {
        const fc = (typeof frm.doc.location === 'string') ? JSON.parse(frm.doc.location) : frm.doc.location;
        render_geometry_on_form(frm, fc);
      } catch (e) {
        console.error('Failed to render saved geometry', e);
      }
    }

    ensure_enforcement_client_cfg(() => setTimeout(() => set_geolocation_basemap(frm, 'location', __enforcement_bg_key), 300));
  }
});

function fetch_geometry_from_gis(frm) {
  if (frm.is_new()) {
    frappe.msgprint({ message: __('Save the document before fetching geometry.'), indicator: 'orange' });
    return;
  }
  if (!frm.doc.order_id) {
    frappe.msgprint({ message: __('Enter Order ID before fetching geometry.'), indicator: 'orange' });
    return;
  }
  frappe.show_alert({ message: __('Fetching geometry from GIS...'), indicator: 'blue' });
  frappe.call({
    method: 'rb.gis_integration.api.fetch_enforcement_order_geometry',
    args: { order_name: frm.doc.name },
    callback: (r) => {
      try {
        if (r && r.message) {
          const fc = (typeof r.message === 'string') ? JSON.parse(r.message) : r.message;
          frm.doc.location = JSON.stringify(fc);
          frm.refresh_field('location');
          render_geometry_on_form(frm, fc);
        }
      } catch (e) {
        console.error('Failed to process geometry', e);
      }
    },
    error: (e) => {
      frappe.msgprint({ title: __('Error'), message: __('Failed to fetch geometry from GIS'), indicator: 'red' });
      console.error(e);
    }
  });
}

function sync_all_geometries(frm) {
  frappe.confirm(__('This will sync geometries for all Enforcement Order records. Continue?'), () => {
    frappe.call({
      method: 'rb.gis_integration.api.sync_all_enforcement_order_geometries',
      args: {},
      freeze: true,
      freeze_message: __('Syncing geometries...'),
      callback: (r) => {
        const m = r.message || {};
        const indicator = m.errors > 0 ? 'orange' : 'green';
        let msg = __('Sync completed. Success: {0}, Errors: {1}', [m.success || 0, m.errors || 0]);
        if (m.error_details && m.error_details.length) {
          msg += '<br><br>' + __('Errors:') + '<br>' + m.error_details.join('<br>');
        }
        frappe.msgprint({ title: __('Sync Results'), message: msg, indicator });
      }
    });
  });
}

function ensure_enforcement_client_cfg(cb) {
  if (__enforcement_basemaps) {
    cb && cb();
    return;
  }
  frappe.call({ method: 'rb.gis_integration.api.gis_reload_config' })
    .always(() => {
      frappe.call({
        method: 'rb.gis_integration.api.gis_get_client_config',
        args: { doctype: 'Enforcement Order' },
        callback: (r) => {
          const msg = r.message || {};
          __enforcement_basemaps = msg.basemaps || null;
          __enforcement_map_cfg = msg.map || {};
          __enforcement_bg_key = normalize_bg_key((__enforcement_map_cfg && __enforcement_map_cfg.default_basemap) || 'default');
          cb && cb();
        },
        error: () => {
          __enforcement_basemaps = null;
          __enforcement_map_cfg = null;
          __enforcement_bg_key = 'default';
          cb && cb();
        }
      });
    });
}

function normalize_bg_key(which) {
  if (!which) return 'default';
  const val = String(which).trim();
  if (val === 'alt') return 'A';
  if (val.toLowerCase() === 'b') return 'B';
  return val;
}

function get_enforcement_basemap(which) {
  const key = normalize_bg_key(which);
  if (__enforcement_basemaps && __enforcement_basemaps[key]) return __enforcement_basemaps[key];
  if (__enforcement_basemaps && __enforcement_basemaps.default) return __enforcement_basemaps.default;
  return ENFORCEMENT_BASEMAP_FALLBACK[key] || ENFORCEMENT_BASEMAP_FALLBACK.default;
}

function ensure_map(frm) {
  ensure_leaflet(() => {});
  const id = 'enforcement-geo-map';
  if (!frm.$wrapper.find(`#${id}`).length) {
    const $c = $(`
      <div class="form-section" style="margin-top:8px;">
        <div class="section-body">
          <div id="${id}" style="height: 340px; border: 1px solid #e5e5e5; border-radius: 6px;"></div>
        </div>
      </div>`);
    frm.$wrapper.find('.form-layout').append($c);
  }

  if (!__enforcement_map) {
    const el = document.getElementById(id);
    if (el && window.L) {
      __enforcement_map = L.map(id);
      ensure_enforcement_client_cfg(() => { set_map_basemap(__enforcement_map, __enforcement_bg_key); apply_default_view(__enforcement_map); });
    }
  }
  return __enforcement_map;
}

function render_geometry_on_form(frm, featureCollection) {
  const map = ensure_map(frm);
  if (!map || !window.L) return;
  if (__enforcement_geo_layer) {
    __enforcement_geo_layer.remove();
    __enforcement_geo_layer = null;
  }
  __enforcement_geo_layer = L.geoJSON(featureCollection, { style: { color: '#117864', weight: 2, fillOpacity: 0.2 } }).addTo(map);
  try {
    if (should_fit_geometry()) {
      map.fitBounds(__enforcement_geo_layer.getBounds(), { padding: [10, 10] });
    } else {
      apply_default_view(map);
    }
  } catch (e) {}
}

function ensure_leaflet(cb) {
  if (window.L) return cb && cb();
  if (__enforcement_leaflet_loading) return;
  __enforcement_leaflet_loading = true;
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = '/assets/frappe/js/lib/leaflet/leaflet.css';
  document.head.appendChild(css);

  const script = document.createElement('script');
  script.src = '/assets/frappe/js/lib/leaflet/leaflet.js';
  script.onload = () => { __enforcement_leaflet_loading = false; cb && cb(); };
  script.onerror = () => { __enforcement_leaflet_loading = false; console.warn('Leaflet load failed'); };
  document.head.appendChild(script);
}

function set_geolocation_basemap(frm, fieldname, which) {
  const field = frm.get_field(fieldname);
  if (!field) return;
  const bm = get_enforcement_basemap(which);
  const swap = () => {
    const map = field.map || field.leaflet_map || field._map;
    const old = field.tile_layer || field._tile_layer;
    if (!map || !window.L) return setTimeout(swap, 200);
    try {
      if (old && map.hasLayer && map.hasLayer(old)) {
        map.removeLayer(old);
      }
      const tile = L.tileLayer(bm.url, bm.options || { maxZoom: 19 }).addTo(map);
      field.tile_layer = tile;
      field._tile_layer = tile;
    } catch (e) {
      setTimeout(swap, 300);
    }
  };
  swap();
}

function set_map_basemap(map, which) {
  const bm = get_enforcement_basemap(which);
  try {
    if (__enforcement_base_layer && map.hasLayer && map.hasLayer(__enforcement_base_layer)) {
      map.removeLayer(__enforcement_base_layer);
    }
  } catch (e) {}
  __enforcement_base_layer = L.tileLayer(bm.url, bm.options || { maxZoom: 19 }).addTo(map);
}

function toggle_enforcement_background(frm, key) {
  const target = normalize_bg_key(key || 'A');
  __enforcement_bg_key = (__enforcement_bg_key === target) ? 'default' : target;
  const map = ensure_map(frm);
  if (map && window.L) set_map_basemap(map, __enforcement_bg_key);
  set_geolocation_basemap(frm, 'location', __enforcement_bg_key);
}

function set_enforcement_background(frm, key) {
  const norm = normalize_bg_key(key || 'B');
  __enforcement_bg_key = norm;
  const map = ensure_map(frm);
  if (map && window.L) set_map_basemap(map, __enforcement_bg_key);
  set_geolocation_basemap(frm, 'location', __enforcement_bg_key);
}

function apply_default_view(map) {
  try {
    const cfg = __enforcement_map_cfg || {};
    const z = parseInt(cfg.default_zoom);
    if (!isNaN(z)) {
      let latlng = null;
      if (Array.isArray(cfg.default_center) && cfg.default_center.length === 2) {
        const lon = Number(cfg.default_center[0]);
        const lat = Number(cfg.default_center[1]);
        if (isFinite(lat) && isFinite(lon)) latlng = [lat, lon];
      }
      if (latlng) {
        map.setView(latlng, z);
      } else {
        map.setZoom(z);
      }
    }
  } catch (e) {}
}

function should_fit_geometry() {
  try {
    if (__enforcement_map_cfg && typeof __enforcement_map_cfg.fit_to_geometry === 'boolean') {
      return __enforcement_map_cfg.fit_to_geometry;
    }
  } catch (e) {}
  return true;
}

function open_tiles_map(frm) {
  const layer = (__enforcement_map_cfg && __enforcement_map_cfg.tileserv_layer) || 'Enforcement Order';
  const url = `http://your-tileserv:7800/${layer}/{z}/{x}/{y}.pbf`;
  window.open(url, '_blank');
}

function test_gis_connection(frm) {
  frappe.call({
    method: 'rb.gis_integration.api.gis_healthcheck',
    args: { doctype: 'Enforcement Order' },
    callback: (r) => {
      const m = r.message || {};
      const ok = m.ok ? 'OK' : 'FAIL';
      const err = m.error ? `<br><b>Error:</b> ${frappe.utils.escape_html(m.error)}` : '';
      const ex = (m.examples || []).map(x => `<div style="font-size:11px;color:#666;">${frappe.utils.escape_html(x)}</div>`).join('');
      const meta = m.config_meta && m.config_meta.source_paths ? `<div style="margin-top:6px;">Sources:<br>${m.config_meta.source_paths.map(s=>`<div style='font-size:11px;color:#888;'>${frappe.utils.escape_html(s)}</div>`).join('')}</div>` : '';
      frappe.msgprint({
        title: __('GIS Healthcheck'),
        indicator: m.ok ? 'green' : 'red',
        message: `
          <b>Base URL:</b> ${frappe.utils.escape_html(m.base_url || '')}<br>
          <b>Collection:</b> ${frappe.utils.escape_html(m.collection || '')}<br>
          <b>Status:</b> ${ok} ${m.status || ''}
          ${err}
          <div style="margin-top:6px;"><b>Examples:</b>${ex || ' (none)'}</div>
          ${meta}
        `
      });
    },
    error: (e) => {
      frappe.msgprint({ title: __('GIS Healthcheck'), message: __('Call failed'), indicator: 'red' });
      console.error(e);
    }
  });
}

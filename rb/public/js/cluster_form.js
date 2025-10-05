// Centralized basemaps/config for Cluster (loaded from server); minimal fallback
const CLUSTER_BASEMAPS_FALLBACK = { default: { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', options: { maxZoom: 19 } } };
let __cluster_basemaps = null;
let __cluster_map_cfg = null;
let __cluster_bg_key = 'default';
let __cluster_base_layer;

frappe.ui.form.on('Cluster', {
  refresh(frm) {
    if (frm.doc.cluster_name) {
      frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_geometry_from_gis(frm), __('GIS Actions'));
      frm.add_custom_button(__('Open Map (tileserv)'), () => open_tiles_map(frm), __('GIS Actions'));
      if (!frm.doc.location) {
        frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
      } else {
        try { const fc = (typeof frm.doc.location === 'string') ? JSON.parse(frm.doc.location) : frm.doc.location; render_geometry_on_form(frm, fc); } catch(e) {}
      }
      frm.add_custom_button(__('Test GIS Connection'), () => test_gis_connection(frm), __('GIS Actions'));
      frm.add_custom_button(__('Cahnge To Background A'), () => toggle_cluster_background(frm, 'A'), __('GIS Actions'));
      frm.add_custom_button(__('Cahnge To Background B'), () => set_cluster_background(frm, 'B'), __('GIS Actions'));
      if (!__cluster_geo_layer && !frm.doc.location) { setTimeout(() => fetch_geometry_from_gis(frm), 200); }
      ensure_cluster_client_cfg(() => setTimeout(() => set_geolocation_basemap(frm, 'location', __cluster_bg_key), 300));
    }
    if (frappe.user.has_role('System Manager')) {
      frm.add_custom_button(__('Sync All Geometries'), () => sync_all_geometries(frm), __('GIS Actions'));
    }
  },
  cluster_name(frm) {
    if (frm.doc.cluster_name) {
      frappe.confirm(__('Cluster Name changed. Fetch the new geometry?'), () => fetch_geometry_from_gis(frm));
    }
  },
  before_save(frm) {}
});

function fetch_geometry_from_gis(frm) {
  frappe.show_alert({ message: __('Fetching geometry from GIS...'), indicator: 'blue' });
  frappe.call({
    method: 'rb.gis_integration.api.fetch_cluster_geometry',
    args: { cluster_name: frm.doc.name },
    callback: (r) => {
      try {
        if (r && r.message) {
          const fc = (typeof r.message === 'string') ? JSON.parse(r.message) : r.message;
          render_geometry_on_form(frm, fc);
          frm.doc.location = JSON.stringify(fc);
        }
      } catch (e) {
        console.error('Failed to render geometry', e);
      }
    },
    error: (e) => { frappe.msgprint({ title: __('Error'), message: __('Failed to fetch geometry from GIS'), indicator: 'red' }); console.error(e); }
  });
}

function sync_all_geometries(frm) {
  frappe.confirm(__('This will sync geometries for all clusters with identifiers. Continue?'), () => {
    frappe.call({
      method: 'rb.gis_integration.api.sync_all_cluster_geometries',
      args: { },
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

// --- Minimal Leaflet rendering (separate namespace to avoid clashes with Lot) ---
let __cluster_map;
let __cluster_geo_layer;
let __leaflet_loading_cluster;

function ensure_map(frm) {
  ensure_leaflet(() => {});
  const id = 'cluster-geo-map';
  if (!frm.$wrapper.find(`#${id}`).length) {
    const $c = $(`
      <div class="form-section" style="margin-top:8px;">
        <div class="section-body">
          <div id="${id}" style="height: 340px; border: 1px solid #e5e5e5; border-radius: 6px;"></div>
        </div>
      </div>`);
    frm.$wrapper.find('.form-layout').append($c);
  }

  if (!__cluster_map) {
    const el = document.getElementById(id);
    if (el && window.L) {
      __cluster_map = L.map(id);
      ensure_cluster_client_cfg(() => { set_map_basemap(__cluster_map, __cluster_bg_key); apply_default_view(__cluster_map); });
    }
  }
  return __cluster_map;
}

function render_geometry_on_form(frm, featureCollection) {
  const map = ensure_map(frm);
  if (!map || !window.L) return;
  if (__cluster_geo_layer) {
    __cluster_geo_layer.remove();
    __cluster_geo_layer = null;
  }
  __cluster_geo_layer = L.geoJSON(featureCollection, { style: { color: '#1F618D', weight: 2, fillOpacity: 0.15 } }).addTo(map);
  try {
    if (should_fit_geometry()) { map.fitBounds(__cluster_geo_layer.getBounds(), { padding: [10, 10] }); }
    else { apply_default_view(map); }
  } catch(e) {}
}

function ensure_leaflet(cb) {
  if (window.L) return cb && cb();
  if (__leaflet_loading_cluster) return;
  __leaflet_loading_cluster = true;
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = '/assets/frappe/js/lib/leaflet/leaflet.css';
  document.head.appendChild(css);

  const script = document.createElement('script');
  script.src = '/assets/frappe/js/lib/leaflet/leaflet.js';
  script.onload = () => { __leaflet_loading_cluster = false; cb && cb(); };
  script.onerror = () => { __leaflet_loading_cluster = false; console.warn('Leaflet load failed'); };
  document.head.appendChild(script);
}

function open_tiles_map(frm) {
  const layer = (__cluster_map_cfg && __cluster_map_cfg.tileserv_layer) || 'rb_layers.clusters';
  const url = `http://your-tileserv:7800/${layer}/{z}/{x}/{y}.pbf`;
  window.open(url, '_blank');
}

// --- Helpers: config/basemaps/default view ---
function ensure_cluster_client_cfg(cb) {
  if (__cluster_basemaps) return cb && cb();
  frappe.call({ method: 'rb.gis_integration.api.gis_reload_config' })
    .always(() => {
      frappe.call({
        method: 'rb.gis_integration.api.gis_get_client_config',
        args: { doctype: 'Cluster' },
        callback: (r) => {
          const msg = r.message || {};
          __cluster_basemaps = msg.basemaps || null;
          __cluster_map_cfg = msg.map || {};
          __cluster_bg_key = normalize_bg_key((__cluster_map_cfg && __cluster_map_cfg.default_basemap) || 'default');
          cb && cb();
        },
        error: () => { __cluster_basemaps = null; __cluster_map_cfg = null; __cluster_bg_key = 'default'; cb && cb(); }
      });
    });
}

function normalize_bg_key(which) { if (!which) return 'default'; const w = String(which).trim(); if (w==='alt') return 'A'; if (w.toLowerCase()==='b') return 'B'; return w; }

function get_basemap(which) {
  const key = normalize_bg_key(which);
  if (__cluster_basemaps && __cluster_basemaps[key]) return __cluster_basemaps[key];
  if (__cluster_basemaps && __cluster_basemaps.default) return __cluster_basemaps.default;
  return CLUSTER_BASEMAPS_FALLBACK[key] || CLUSTER_BASEMAPS_FALLBACK.default;
}

function set_map_basemap(map, which) {
  const bm = get_basemap(which);
  try { if (__cluster_base_layer && map.hasLayer && map.hasLayer(__cluster_base_layer)) map.removeLayer(__cluster_base_layer); } catch(e) {}
  __cluster_base_layer = L.tileLayer(bm.url, bm.options || { maxZoom: 19 }).addTo(map);
}

function toggle_cluster_background(frm, key) {
  const target = normalize_bg_key(key || 'A');
  __cluster_bg_key = (__cluster_bg_key === target) ? 'default' : target;
  const map = ensure_map(frm);
  if (map && window.L) set_map_basemap(map, __cluster_bg_key);
  set_geolocation_basemap(frm, 'location', __cluster_bg_key);
}

function set_cluster_background(frm, key) {
  const norm = normalize_bg_key(key || 'B');
  __cluster_bg_key = norm;
  const map = ensure_map(frm);
  if (map && window.L) set_map_basemap(map, __cluster_bg_key);
  set_geolocation_basemap(frm, 'location', __cluster_bg_key);
}

function set_geolocation_basemap(frm, fieldname, which) {
  const field = frm.get_field(fieldname); if (!field) return;
  const swap = () => {
    const bm = get_basemap(which);
    const map = field.map || field.leaflet_map || field._map;
    const old = field.tile_layer || field._tile_layer;
    if (!map || !window.L) return setTimeout(swap, 200);
    try {
      if (old && map.hasLayer && map.hasLayer(old)) map.removeLayer(old);
      const tile = L.tileLayer(bm.url, bm.options || { maxZoom: 19 }).addTo(map);
      field.tile_layer = tile; field._tile_layer = tile;
      const v = frm.doc[fieldname]; if (!v) apply_default_view(map);
    } catch(e) { setTimeout(swap, 300); }
  };
  swap();
}

function apply_default_view(map) {
  try {
    const cfg = __cluster_map_cfg || {};
    const z = parseInt(cfg.default_zoom);
    if (!isNaN(z)) {
      let latlng = null;
      if (Array.isArray(cfg.default_center) && cfg.default_center.length === 2) {
        const lon = Number(cfg.default_center[0]); const lat = Number(cfg.default_center[1]);
        if (isFinite(lat) && isFinite(lon)) latlng = [lat, lon];
      }
      if (latlng) map.setView(latlng, z); else map.setZoom(z);
    }
  } catch(e) {}
}

function should_fit_geometry() { try { if (__cluster_map_cfg && typeof __cluster_map_cfg.fit_to_geometry === 'boolean') return __cluster_map_cfg.fit_to_geometry; } catch(e) {} return false; }

function test_gis_connection(frm) {
  frappe.call({
    method: 'rb.gis_integration.api.gis_healthcheck',
    args: { doctype: 'Cluster' },
    callback: (r) => {
      const m = r.message || {};
      const ok = m.ok ? 'OK' : 'FAIL';
      const err = m.error ? `<br><b>Error:</b> ${frappe.utils.escape_html(m.error)}` : '';
      const ex = (m.examples || []).map(x => `<div style=\"font-size:11px;color:#666;\">${frappe.utils.escape_html(x)}</div>`).join('');
      const meta = m.config_meta && m.config_meta.source_paths ? `<div style=\"margin-top:6px;\">Sources:<br>${m.config_meta.source_paths.map(s=>`<div style='font-size:11px;color:#888;'>${frappe.utils.escape_html(s)}</div>`).join('')}</div>` : '';
      frappe.msgprint({
        title: __('GIS Healthcheck'),
        indicator: m.ok ? 'green' : 'red',
        message: `
          <b>Base URL:</b> ${frappe.utils.escape_html(m.base_url || '')}<br>
          <b>Collection:</b> ${frappe.utils.escape_html(m.collection || '')}<br>
          <b>Status:</b> ${ok} ${m.status || ''}
          ${err}
          <div style=\"margin-top:6px;\"><b>Examples:</b>${ex || ' (none)'}</div>
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

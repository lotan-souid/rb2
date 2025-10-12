// Basemap definitions — fallback only (real basemaps are loaded from server config)
const PLAN_BASEMAPS = {
  default: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }
  }
};

let __plan_basemaps = null; // populated from gis_get_client_config
let __plan_map_cfg = null;
let __plan_bg_key = 'default';
let __plan_map;
let __plan_geo_layer;
let __plan_leaflet_loading;
let __plan_base_layer;

frappe.ui.form.on('Plan', {
  refresh(frm) {
    const group = __('GIS Actions');
    if (frm.doc.plan_number) {
      frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_plan_geometry(frm), group);
      frm.add_custom_button(__('Open Map (tileserv)'), () => open_plan_tiles_map(frm), group);
      frm.add_custom_button(__('Test GIS Connection'), () => test_plan_gis_connection(frm), group);
      frm.add_custom_button(__('Cahnge To Background A'), () => toggle_plan_background(frm, 'A'), group);
      frm.add_custom_button(__('Cahnge To Background B'), () => set_plan_background(frm, 'B'), group);

      if (!frm.doc.location) {
        frm.dashboard && frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
        if (!__plan_geo_layer) {
          setTimeout(() => fetch_plan_geometry(frm), 200);
        }
      } else {
        frm.dashboard && frm.dashboard.clear_headline();
        try {
          const fc = typeof frm.doc.location === 'string' ? JSON.parse(frm.doc.location) : frm.doc.location;
          render_plan_geometry(frm, fc);
        } catch (e) {
          console.warn('Failed to parse Plan geometry', e);
        }
      }

      ensure_plan_client_cfg(() => setTimeout(() => set_plan_geolocation_basemap(frm, 'location', __plan_bg_key), 300));
    } else if (frm.dashboard) {
      frm.dashboard.set_headline(__('Set Plan Number to enable GIS lookup.'));
    }

    if (frappe.user.has_role('System Manager')) {
      frm.add_custom_button(__('Sync All Geometries'), () => sync_all_plan_geometries(frm), group);
    }
  },

  plan_number(frm) {
    if (!frm.is_new() && frm.doc.plan_number) {
      frappe.confirm(__('Plan Number changed. Fetch the new geometry from GIS?'), () => fetch_plan_geometry(frm));
    }
  }
});

function fetch_plan_geometry(frm) {
  if (!frm.doc.plan_number) {
    frappe.msgprint({ message: __('Plan Number is required before fetching geometry.'), indicator: 'orange' });
    return;
  }
  if (frm.is_new()) {
    frappe.msgprint({ message: __('Save the Plan before fetching geometry from GIS.'), indicator: 'orange' });
    return;
  }
  if (frm.is_dirty()) {
    frappe.msgprint({ message: __('Please save your changes before fetching geometry.'), indicator: 'orange' });
    return;
  }

  frappe.show_alert({ message: __('Fetching geometry from GIS...'), indicator: 'blue' });
  frappe.call({
    method: 'rb.gis_integration.api.fetch_plan_geometry',
    args: { plan_name: frm.doc.name },
    freeze: true,
    freeze_message: __('Fetching geometry from GIS...'),
    callback: (r) => {
      try {
        if (r && r.message) {
          const fc = typeof r.message === 'string' ? JSON.parse(r.message) : r.message;
          render_plan_geometry(frm, fc);
          frm.set_value('location', JSON.stringify(fc));
          frm.dashboard && frm.dashboard.clear_headline();
          frappe.show_alert({ message: __('Geometry updated.'), indicator: 'green' });
        }
      } catch (e) {
        console.error('Failed to render Plan geometry', e);
        frappe.msgprint({ message: __('Fetched geometry could not be rendered.'), indicator: 'orange' });
      }
    },
    error: (err) => {
      console.error(err);
      frappe.msgprint({ message: __('Failed to fetch geometry from GIS.'), indicator: 'red' });
    }
  });
}

function sync_all_plan_geometries(frm) {
  frappe.confirm(__('Sync geometries for all Plans that have a Plan Number?'), () => {
    frappe.call({
      method: 'rb.gis_integration.api.sync_all_plan_geometries',
      freeze: true,
      freeze_message: __('Syncing Plan geometries...'),
      callback: (r) => {
        const m = r.message || {};
        const indicator = (m.errors || 0) > 0 ? 'orange' : 'green';
        let msg = __('Sync completed. Success: {0}, Errors: {1}', [m.success || 0, m.errors || 0]);
        if (m.error_details && m.error_details.length) {
          msg += '<br><br>' + __('Errors:') + '<br>' + m.error_details.join('<br>');
        }
        frappe.msgprint({ title: __('Sync Results'), message: msg, indicator });
      }
    });
  });
}

function open_plan_tiles_map(frm) {
  const layer = frm.doc.gis_collection || 'rb_layers.plans';
  const url = `http://your-tileserv:7800/${layer}/{z}/{x}/{y}.pbf`;
  window.open(url, '_blank');
}

function test_plan_gis_connection(frm) {
  frappe.call({
    method: 'rb.gis_integration.api.gis_healthcheck',
    args: { doctype: 'Plan' },
    callback: (r) => {
      const m = r.message || {};
      const ok = m.ok ? 'OK' : 'FAIL';
      const err = m.error ? `<br><b>Error:</b> ${frappe.utils.escape_html(m.error)}` : '';
      const ex = (m.examples || []).map(x => `<div style="font-size:11px;color:#666;">${frappe.utils.escape_html(x)}</div>`).join('');
      const meta = m.config_meta && m.config_meta.source_paths
        ? `<div style="margin-top:6px;">Sources:<br>${m.config_meta.source_paths.map(s => `<div style='font-size:11px;color:#888;'>${frappe.utils.escape_html(s)}</div>`).join('')}</div>`
        : '';
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

function ensure_plan_map(frm) {
  ensure_plan_leaflet(() => {});
  const id = 'plan-geo-map';
  if (!frm.$wrapper.find(`#${id}`).length) {
    const $c = $(`
      <div class="form-section" style="margin-top:8px;">
        <div class="section-body">
          <div id="${id}" style="height: 340px; border: 1px solid #e5e5e5; border-radius: 6px;"></div>
        </div>
      </div>`);
    frm.$wrapper.find('.form-layout').append($c);
  }

  if (!__plan_map) {
    const el = document.getElementById(id);
    if (el && window.L) {
      __plan_map = L.map(id);
      ensure_plan_client_cfg(() => { set_plan_map_basemap(__plan_map, __plan_bg_key); apply_plan_default_view(__plan_map); });
    }
  }
  return __plan_map;
}

function render_plan_geometry(frm, featureCollection) {
  const map = ensure_plan_map(frm);
  if (!map || !window.L) return;
  if (__plan_geo_layer) {
    __plan_geo_layer.remove();
    __plan_geo_layer = null;
  }
  __plan_geo_layer = L.geoJSON(featureCollection, { style: { color: '#3366cc', weight: 2, fillOpacity: 0.18 } }).addTo(map);
  try {
    if (plan_should_fit_geometry()) {
      map.fitBounds(__plan_geo_layer.getBounds(), { padding: [10, 10] });
    } else {
      apply_plan_default_view(map);
    }
  } catch (e) {}
}

function ensure_plan_leaflet(cb) {
  if (window.L) return cb && cb();
  if (__plan_leaflet_loading) return;
  __plan_leaflet_loading = true;

  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = '/assets/frappe/js/lib/leaflet/leaflet.css';
  document.head.appendChild(css);

  const script = document.createElement('script');
  script.src = '/assets/frappe/js/lib/leaflet/leaflet.js';
  script.onload = () => { __plan_leaflet_loading = false; cb && cb(); };
  script.onerror = () => { __plan_leaflet_loading = false; console.warn('Leaflet load failed'); };
  document.head.appendChild(script);
}

function set_plan_geolocation_basemap(frm, fieldname, which) {
  const field = frm.get_field(fieldname);
  if (!field) return;
  const bm = get_plan_basemap(which);
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
      try {
        if (!frm.doc[fieldname]) {
          apply_plan_default_view(map);
        }
      } catch (e) {}
    } catch (e) {
      setTimeout(swap, 300);
    }
  };
  swap();
}

function set_plan_map_basemap(map, which) {
  const bm = get_plan_basemap(which);
  try {
    if (__plan_base_layer && map.hasLayer && map.hasLayer(__plan_base_layer)) {
      map.removeLayer(__plan_base_layer);
    }
  } catch (e) {}
  __plan_base_layer = L.tileLayer(bm.url, bm.options || { maxZoom: 19 }).addTo(map);
}

function toggle_plan_background(frm, key) {
  const target = normalize_plan_bg_key(key || 'A');
  __plan_bg_key = (__plan_bg_key === target) ? 'default' : target;
  const map = ensure_plan_map(frm);
  if (map && window.L) {
    set_plan_map_basemap(map, __plan_bg_key);
  }
  set_plan_geolocation_basemap(frm, 'location', __plan_bg_key);
}

function set_plan_background(frm, which) {
  const norm = normalize_plan_bg_key(which);
  __plan_bg_key = norm;
  const map = ensure_plan_map(frm);
  if (map && window.L) {
    set_plan_map_basemap(map, norm);
  }
  set_plan_geolocation_basemap(frm, 'location', norm);
}

function ensure_plan_client_cfg(cb) {
  if (__plan_basemaps) return cb && cb();
  frappe.call({ method: 'rb.gis_integration.api.gis_reload_config' })
    .always(() => {
      frappe.call({
        method: 'rb.gis_integration.api.gis_get_client_config',
        args: { doctype: 'Plan' },
        callback: (r) => {
          const msg = r.message || {};
          __plan_basemaps = msg.basemaps || null;
          __plan_map_cfg = msg.map || {};
          __plan_bg_key = normalize_plan_bg_key((__plan_map_cfg && __plan_map_cfg.default_basemap) || 'default');
          cb && cb();
        },
        error: () => { __plan_basemaps = null; __plan_bg_key = 'default'; cb && cb(); }
      });
    });
}

function normalize_plan_bg_key(which) {
  if (!which) return 'default';
  const w = String(which).trim();
  if (w === 'alt') return 'A';
  if (w.toLowerCase() === 'b') return 'B';
  return w;
}

function get_plan_basemap(which) {
  const key = normalize_plan_bg_key(which);
  if (__plan_basemaps && __plan_basemaps[key]) return __plan_basemaps[key];
  if (__plan_basemaps && __plan_basemaps.default) return __plan_basemaps.default;
  return PLAN_BASEMAPS[key] || PLAN_BASEMAPS.default;
}

function apply_plan_default_view(map) {
  try {
    const cfg = __plan_map_cfg || {};
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

function plan_should_fit_geometry() {
  try {
    if (__plan_map_cfg && typeof __plan_map_cfg.fit_to_geometry === 'boolean') {
      return __plan_map_cfg.fit_to_geometry;
    }
  } catch (e) {}
  return true;
}

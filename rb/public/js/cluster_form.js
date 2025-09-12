frappe.ui.form.on('Cluster', {
  refresh(frm) {
    if (frm.doc.cluster_name) {
      frm.add_custom_button(__('Fetch Geometry from GIS'), () => fetch_geometry_from_gis(frm), __('GIS Actions'));
      if (!frm.doc.location) {
        frm.dashboard.set_headline(__('No geometry loaded. Click "Fetch Geometry from GIS" to load.'));
      } else {
        try { const fc = (typeof frm.doc.location === 'string') ? JSON.parse(frm.doc.location) : frm.doc.location; render_geometry_on_form(frm, fc); } catch(e) {}
      }
      frm.add_custom_button(__('Test GIS Connection'), () => test_gis_connection(frm), __('GIS Actions'));
      if (!__cluster_geo_layer && !frm.doc.location) { setTimeout(() => fetch_geometry_from_gis(frm), 200); }
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
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(__cluster_map);
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
  try { map.fitBounds(__cluster_geo_layer.getBounds(), { padding: [10, 10] }); } catch(e) {}
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


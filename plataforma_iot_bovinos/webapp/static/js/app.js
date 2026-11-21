// app.js - Plataforma IoT Bovinos Valle del Mezquital

let map;
let markers = {};
let potreroCircles = [];
let historicalPolyline = null;
let currentSelectedAnimalId = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  recargarDatosCompletos();

  // Refresco automático periódico cada 20 segundos
  setInterval(() => {
    recargarDatosCompletos(true);
  }, 20000);
});

// 1. Inicialización de Leaflet
function initMap() {
  // Centro por defecto: Huichapan, Valle del Mezquital
  map = L.map('map').setView([20.37542, -99.65431], 13);

  // Capa base OpenStreetMap
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors | Bovinos IoT'
  }).addTo(map);

  cargarPotreros();
}

function centrarMapaHuichapan() {
  map.flyTo([20.37542, -99.65431], 14);
}

function centrarMapaTecozautla() {
  map.flyTo([20.52118, -99.63005], 14);
}

function centrarMapaIxmiquilpan() {
  map.flyTo([20.48620, -99.21780], 14);
}

// 2. Cargar Potreros / Geocercas
async function cargarPotreros() {
  try {
    const res = await fetch('/api/potreros');
    const data = await res.json();
    potreroCircles.forEach(c => map.removeLayer(c));
    potreroCircles = [];

    data.forEach(p => {
      const circle = L.circle([p.lat_centro, p.lon_centro], {
        color: '#2d6a4f',
        fillColor: '#52b788',
        fillOpacity: 0.15,
        radius: p.radio_m || 400
      }).addTo(map);

      circle.bindTooltip(`<b>Potrero: ${p.nombre}</b><br>${p.rancho} (${p.superficie_ha} ha)`, {
        permanent: false,
        direction: 'top'
      });
      potreroCircles.push(circle);
    });
  } catch (err) {
    console.error('Error cargando potreros:', err);
  }
}

// 3. Recarga integral de datos
async function recargarDatosCompletos(isSilent = false) {
  try {
    await Promise.all([
      cargarDashboard(),
      cargarBovinos(),
      cargarAlertas(true),
      cargarDispositivos()
    ]);
    const now = new Date();
    document.getElementById('lbl-ultima-act').innerText = now.toLocaleTimeString();
  } catch (err) {
    console.error('Error refrescando datos:', err);
  }
}

// 4. KPI Dashboard
async function cargarDashboard() {
  const res = await fetch('/api/dashboard');
  const d = await res.json();

  document.getElementById('kpi-total-animales').innerText = d.total_animales;
  document.getElementById('kpi-vigencia-verde').innerText = d.vigencia.verde;
  document.getElementById('kpi-vigencia-amarillo').innerText = d.vigencia.amarillo;
  document.getElementById('kpi-vigencia-rojo').innerText = d.vigencia.rojo;
  document.getElementById('kpi-total-dispositivos').innerText = (d.total_collares + d.total_gateways);
  document.getElementById('kpi-collares').innerText = d.total_collares;
  document.getElementById('kpi-gateways').innerText = d.total_gateways;
  document.getElementById('badge-total-alertas').innerText = d.alertas_activas;
}

// 5. Bovinos y Marcadores
async function cargarBovinos() {
  const res = await fetch('/api/bovinos');
  const bovinos = await res.json();

  const tbody = document.getElementById('tabla-bovinos-body');
  tbody.innerHTML = '';

  bovinos.forEach(b => {
    // Marcadores Mapa
    const colorMarker = b.vigencia_color === 'verde' ? '#2e7d32' : (b.vigencia_color === 'amarillo' ? '#f57f17' : '#c62828');
    
    if (b.lat && b.lon) {
      if (markers[b.id]) {
        markers[b.id].setLatLng([b.lat, b.lon]);
      } else {
        const marker = L.circleMarker([b.lat, b.lon], {
          radius: 9,
          fillColor: colorMarker,
          color: '#ffffff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9
        }).addTo(map);

        marker.bindPopup(`
          <div class="p-1">
            <h6 class="mb-1 text-success fw-bold">${b.nombre} (${b.arete})</h6>
            <div class="small">
              <b>Raza:</b> ${b.raza} (${b.sexo})<br>
              <b>Rancho:</b> ${b.rancho} - ${b.potrero}<br>
              <b>Batería:</b> ${b.bateria_pct}% | <b>RSSI:</b> ${b.rssi} dBm<br>
              <b>Vigencia:</b> <span class="badge ${getBadgeClass(b.vigencia_color)}">${b.vigencia_etiqueta}</span>
            </div>
          </div>
        `);

        marker.on('click', () => {
          seleccionarBovino(b);
        });

        markers[b.id] = marker;
      }
    }

    // Fila en tabla
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="badge bg-secondary-subtle text-dark border">${b.arete}</span></td>
      <td><strong>${b.nombre}</strong></td>
      <td>${b.raza} <span class="text-muted small">(${b.sexo})</span></td>
      <td>${b.rancho} <br><small class="text-muted">${b.potrero || 'Sin asignar'}</small></td>
      <td><code>${b.lat ? b.lat.toFixed(5) : '0.0'}, ${b.lon ? b.lon.toFixed(5) : '0.0'}</code></td>
      <td>
        <div class="d-flex align-items-center gap-1">
          <i class="bi bi-battery-charging text-muted"></i>
          <span>${b.bateria_pct}%</span>
        </div>
      </td>
      <td>${b.rssi || '-'} dBm</td>
      <td><span class="badge ${getBadgeClass(b.vigencia_color)}">${b.vigencia_etiqueta}</span></td>
      <td>
        <button class="btn btn-sm btn-outline-success" onclick='seleccionarBovinoPorId(${b.id})'>
          <i class="bi bi-geo"></i> Ver
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function getBadgeClass(color) {
  if (color === 'verde') return 'bg-success';
  if (color === 'amarillo') return 'bg-warning text-dark';
  return 'bg-danger';
}

// 6. Selección y Detalle de Bovino + Trazado Histórico
async function seleccionarBovinoPorId(id) {
  const res = await fetch('/api/bovinos');
  const bovinos = await res.json();
  const bovino = bovinos.find(x => x.id === id);
  if (bovino) seleccionarBovino(bovino);
}

async function seleccionarBovino(bovino) {
  currentSelectedAnimalId = bovino.id;
  
  if (bovino.lat && bovino.lon) {
    map.flyTo([bovino.lat, bovino.lon], 16);
    if (markers[bovino.id]) {
      markers[bovino.id].openPopup();
    }
  }

  // Actualizar Panel Lateral
  const panel = document.getElementById('panel-detalle-bovino');
  panel.innerHTML = `
    <div class="d-flex justify-content-between align-items-center border-bottom pb-2 mb-3">
      <h5 class="mb-0 text-success fw-bold">${bovino.nombre}</h5>
      <span class="badge ${getBadgeClass(bovino.vigencia_color)}">${bovino.vigencia_etiqueta}</span>
    </div>
    <ul class="list-group list-group-flush small mb-3">
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Arete SAGARPA:</span>
        <strong>${bovino.arete}</strong>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Raza y Sexo:</span>
        <span>${bovino.raza} (${bovino.sexo})</span>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Rancho Asignado:</span>
        <span>${bovino.rancho}</span>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Potrero Actual:</span>
        <span>${bovino.potrero || 'Sin asignar'}</span>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Collar LoRa:</span>
        <span>${bovino.collar_nombre || 'No asignado'}</span>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Batería Collar:</span>
        <strong class="${bovino.bateria_pct < 25 ? 'text-danger' : 'text-success'}">${bovino.bateria_pct}%</strong>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Altitud / Velocidad:</span>
        <span>${bovino.altitud || 0} m / ${bovino.velocidad || 0} km/h</span>
      </li>
      <li class="list-group-item d-flex justify-content-between px-0">
        <span class="text-muted">Potencia Señal LoRa:</span>
        <span>${bovino.rssi || '-'} dBm</span>
      </li>
    </ul>

    <button class="btn btn-outline-primary btn-sm w-100" onclick="cargarRutaHistorica(${bovino.id})">
      <i class="bi bi-clock-history"></i> Trazar Ruta Histórica (24h)
    </button>
  `;

  // Cargar ruta histórica automáticamente
  cargarRutaHistorica(bovino.id);
}

// 7. Ruta Histórica (Polyline)
async function cargarRutaHistorica(animalId) {
  try {
    const res = await fetch(`/api/historial/${animalId}?horas=24`);
    const history = await res.json();

    if (historicalPolyline) {
      map.removeLayer(historicalPolyline);
      historicalPolyline = null;
    }

    if (!history || history.length === 0) return;

    const latlngs = history.map(h => [h.lat, h.lon]);
    historicalPolyline = L.polyline(latlngs, {
      color: '#0077b6',
      weight: 4,
      opacity: 0.8,
      dashArray: '6, 6'
    }).addTo(map);

  } catch (err) {
    console.error('Error al cargar historial:', err);
  }
}

// 8. Carga de Alertas
async function cargarAlertas(soloActivas = true) {
  try {
    const res = await fetch(`/api/alertas?activas=${soloActivas}`);
    const alertas = await res.json();
    const tbody = document.getElementById('tabla-alertas-body');
    tbody.innerHTML = '';

    if (alertas.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">No hay alertas registradas.</td></tr>';
      return;
    }

    alertas.forEach(a => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>#${a.id}</td>
        <td><span class="badge ${a.tipo === 'sin_comunicacion' ? 'bg-danger' : 'bg-warning text-dark'}">${a.tipo}</span></td>
        <td><strong>${a.animal_nombre || 'N/A'}</strong> <small class="text-muted">(${a.arete || ''})</small></td>
        <td>${a.mensaje}</td>
        <td><small>${a.creada_en}</small></td>
        <td>
          ${a.atendida ? '<span class="badge bg-success">Atendida</span>' : '<span class="badge bg-danger">Pendiente</span>'}
        </td>
        <td>
          ${!a.atendida ? `<button class="btn btn-sm btn-outline-success" onclick="atenderAlerta(${a.id})"><i class="bi bi-check2"></i> Atender</button>` : '<span class="text-muted small">Cerrada</span>'}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error cargando alertas:', err);
  }
}

async function atenderAlerta(id) {
  try {
    const res = await fetch(`/api/alertas/atender/${id}`, { method: 'POST' });
    if (res.ok) {
      cargarAlertas(true);
      cargarDashboard();
    }
  } catch (err) {
    console.error('Error al atender alerta:', err);
  }
}

// 9. Cargar Dispositivos Hardware
async function cargarDispositivos() {
  try {
    const res = await fetch('/api/dispositivos');
    const dispositivos = await res.json();
    const tbody = document.getElementById('tabla-dispositivos-body');
    tbody.innerHTML = '';

    dispositivos.forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${d.mac_id}</code></td>
        <td><span class="badge bg-dark">${d.tipo.toUpperCase()}</span></td>
        <td>${d.nombre}</td>
        <td>v${d.firmware_ver}</td>
        <td>${d.bateria_pct ? d.bateria_pct + '%' : 'Corriente / GW'}</td>
        <td><span class="status-pill ${d.estado_color === 'verde' ? 'online' : (d.estado_color === 'amarillo' ? 'warning' : 'offline')}"></span>${d.estado_etiqueta}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error al cargar dispositivos:', err);
  }
}

// 10. Inyección Simulada de Telemetría
async function enviarTelemetriaSimulada(e) {
  e.preventDefault();
  const feedback = document.getElementById('sim-feedback');
  feedback.innerHTML = '<span class="text-muted">Enviando...</span>';

  const payload = {
    animal_id: parseInt(document.getElementById('sim-animal-id').value),
    lat: parseFloat(document.getElementById('sim-lat').value),
    lon: parseFloat(document.getElementById('sim-lon').value),
    bateria: parseInt(document.getElementById('sim-bat').value),
    rssi: parseInt(document.getElementById('sim-rssi').value),
    velocidad: 1.2,
    satelites: 8,
    altitud: 1810
  };

  try {
    const res = await fetch('/api/lectura', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok && data.ok) {
      feedback.innerHTML = '<span class="text-success"><i class="bi bi-check-circle"></i> Lectura inyectada correctamente. Actualizando mapa...</span>';
      await recargarDatosCompletos(true);
      if (currentSelectedAnimalId === payload.animal_id) {
        seleccionarBovinoPorId(payload.animal_id);
      }
    } else {
      feedback.innerHTML = `<span class="text-danger">Error: ${data.error || 'No se pudo procesar'}</span>`;
    }
  } catch (err) {
    feedback.innerHTML = `<span class="text-danger">Error de red: ${err.message}</span>`;
  }
}

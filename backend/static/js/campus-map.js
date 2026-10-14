(() => {
  const root = document.getElementById('unimap-map-app');
  if (!root) return;

  const apiUrl = root.dataset.apiUrl;
  const routeUrl = root.dataset.routeUrl;
  const activityUrl = root.dataset.activityUrl || '';
  const shortName = root.dataset.university || '';

  let boundary = [];
  try {
    boundary = JSON.parse(root.dataset.boundary || '[]');
  } catch {
    boundary = [];
  }

  const map = L.map('map', {
    zoomControl: false,
    attributionControl: false,
    minZoom: 15,
    maxZoom: 20,
    zoomSnap: .5,
    bounceAtZoomLimits: false,
    maxBoundsViscosity: 1.0
  });

  map.createPane('campusMask');
  map.getPane('campusMask').style.zIndex = 350;
  map.getPane('campusMask').classList.add('campus-mask-pane');

  const satellite = L.tileLayer(
    'https://mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',
    {
      maxZoom: 20,
      minZoom: 15,
      subdomains: ['mt1'],
      detectRetina: false,
      keepBuffer: 8,
      updateWhenIdle: true,
      updateWhenZooming: false
    }
  );

  const darkTiles = L.tileLayer(
    'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {
      maxZoom: 20,
      minZoom: 1,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }
  );

  satellite.addTo(map);

  let baseMode = 'satellite';
  let boundaryLayer = null;
  let boundaryMask = null;

  const cluster = L.markerClusterGroup({
    showCoverageOnHover: false,
    maxClusterRadius: 42,
    disableClusteringAtZoom: 19
  });

  const visibleLayer = L.layerGroup();

  let buildings = [];
  let userMarker = null;
  let accuracyCircle = null;
  let lastHeading = 0;

  // NEW: Track GPS movement to determine walking direction.
  let previousLocation = null;
  let lastMovementHeading = null;

  let routeStart = null;
  let routeEnd = null;
  let routeLine = null;
  let selectedBuilding = null;

  const $ = id => document.getElementById(id);

  const safe = v =>
    String(v ?? '').replace(/[&<>"']/g, m => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[m]));

  const toast = msg => {
    const el = $('mapToast');
    el.textContent = msg;
    el.style.display = 'block';
    clearTimeout(el._t);
    el._t = setTimeout(() => {
      el.style.display = 'none';
    }, 1900);
  };

  const categoryInfo = category => {
    const c = (category || '').toLowerCase();

    if (c.includes('lab')) {
      return {
        key: 'labs',
        color: 'yellow',
        icon: 'lab',
        label: 'Lab'
      };
    }

    if (c.includes('hostel') || c.includes('dorm')) {
      return {
        key: 'hostels',
        color: 'red',
        icon: 'hostel',
        label: 'Hostel'
      };
    }

    if (
      c.includes('hall') ||
      c.includes('lecture') ||
      c.includes('theatre')
    ) {
      return {
        key: 'halls',
        color: 'purple',
        icon: 'book',
        label: 'Hall'
      };
    }

    if (c.includes('sport')) {
      return {
        key: 'sports',
        color: 'green',
        icon: 'trophy',
        label: 'Sports'
      };
    }

    return {
      key: 'buildings',
      color: 'blue',
      icon: 'building',
      label: 'Building'
    };
  };

  const iconSvg = type => {
    const paths = {
      building:
        '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M4 21h16M8 7h4M8 11h4M8 15h4"/>',

      lab:
        '<path d="M9 3h6M10 3v6l-5.5 9.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3"/><path d="M8 15h8"/>',

      hostel:
        '<path d="M4 21V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16M4 10h16M8 7h.01M12 7h.01M16 7h.01M8 14h3v3H8zM14 14h3v3h-3z"/>',

      book:
        '<path d="M4 5a3 3 0 0 1 3-2h12v17H7a3 3 0 0 0-3 3V5Z"/><path d="M4 20a3 3 0 0 1 3-3h12"/>',

      trophy:
        '<path d="M8 4h8v5a4 4 0 0 1-8 0V4Z"/><path d="M8 6H5a3 3 0 0 0 3 3M16 6h3a3 3 0 0 1-3 3M12 13v4M8 20h8"/>'
    };

    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${paths[type] || paths.building}</svg>`;
  };

  const markerIcon = b => {
    const c = categoryInfo(b.category);

    return L.divIcon({
      className: '',
      html: `<div class="marker-pin marker-${c.color}">${iconSvg(c.icon)}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 30]
    });
  };

  if (boundary.length) {
    boundaryLayer = L.polygon(boundary, {
      className: 'campus-boundary-line',
      color: '#1677ff',
      weight: 2,
      opacity: .72,
      fillColor: '#1677ff',
      fillOpacity: .045,
      dashArray: '7 7'
    }).addTo(map);

    const campusBounds = boundaryLayer.getBounds();

    map.setMinZoom(
      Math.max(15, Math.min(18, map.getBoundsZoom(campusBounds, false)))
    );

    map.fitBounds(campusBounds, {
      padding: [42, 110]
    });

    const outer = [
      [89.9, -179.9],
      [89.9, 179.9],
      [-89.9, 179.9],
      [-89.9, -179.9]
    ];

    boundaryMask = L.polygon(
      [outer, boundary.slice().reverse()],
      {
        pane: 'campusMask',
        stroke: false,
        fillColor: '#02070c',
        fillOpacity: .58,
        fillRule: 'evenodd',
        interactive: false
      }
    ).addTo(map);

    boundaryMask.bringToBack();
    boundaryLayer.bringToFront();
  } else {
    map.setView([5.96, 10.16], 17);
  }

  function openPlace(b) {
    selectedBuilding = b;

    const info = categoryInfo(b.category);

    $('placeName').textContent = b.name || 'Campus place';

    $('placeCategory').textContent =
      info.label + (b.description ? ` · ${b.description}` : '');

    const badges = [];

    if (b.floor) badges.push(`Floor ${safe(b.floor)}`);
    if (b.capacity) badges.push(`Capacity ${safe(b.capacity)}`);
    if (b.opening_hours) badges.push(safe(b.opening_hours));

    if (!badges.length) badges.push(info.label);

    $('placeBadges').innerHTML = badges
      .map(x => `<span class="place-badge">${x}</span>`)
      .join('');

    const statusMap = {
      available: ['Available', 'green'],
      in_use: ['In Use', 'red'],
      limited: ['Limited', 'yellow'],
      closed: ['Closed', 'red']
    };

    const st = statusMap[b.status] || statusMap.available;

    $('placeStatus').innerHTML =
      `<span class="status-dot ${st[1]}"></span> ${st[0]}`;

    $('placeClass').innerHTML =
      '<strong>—</strong><small>No current activity</small>';

    const photo = b.photo_url || b.photo || '';
    const photoEl = $('placePhoto');

    photoEl.style.backgroundImage =
      photo ? `url("${safe(photo)}")` : '';

    photoEl.classList.toggle('has-photo', !!photo);

    $('placeSheet').classList.add('open');
    $('placeSheet').setAttribute('aria-hidden', 'false');
    $('placeSheet').scrollTop = 0;
  }

  function closePlace() {
    $('placeSheet').classList.remove('open');
    $('placeSheet').setAttribute('aria-hidden', 'true');
    selectedBuilding = null;
  }

  $('placeClose').onclick = closePlace;

  $('placeViewMap').onclick = () => {
    if (selectedBuilding) {
      map.flyTo(
        [selectedBuilding.latitude, selectedBuilding.longitude],
        19,
        { duration: .65 }
      );

      closePlace();
    }
  };

  $('placeDirections').onclick = () => {
    if (selectedBuilding) {
      window.unimapNavigate(
        selectedBuilding.latitude,
        selectedBuilding.longitude
      );
    }
  };

  $('placeShare').onclick = () => {
    if (!selectedBuilding) return;

    const text = `${selectedBuilding.name} — UNIMAP`;

    if (navigator.share) {
      navigator.share({
        title: selectedBuilding.name,
        text
      }).catch(() => {});
    } else {
      navigator.clipboard?.writeText(text);
      toast('Place copied to clipboard');
    }
  };

  $('placeSave').onclick = () =>
    toast('Save will be connected to your profile');

  function renderVisibleMarkers(filter) {
    const wanted = buildings.filter(
      b => filter === 'all' || b._category.key === filter
    );

    if (map.hasLayer(cluster)) map.removeLayer(cluster);
    if (map.hasLayer(visibleLayer)) map.removeLayer(visibleLayer);

    cluster.clearLayers();
    visibleLayer.clearLayers();

    if (filter === 'all') {
      wanted.forEach(b => cluster.addLayer(b.marker));
      map.addLayer(cluster);
    } else {
      wanted.forEach(b => visibleLayer.addLayer(b.marker));
      map.addLayer(visibleLayer);
    }
  }

  fetch(`${apiUrl}?university=${encodeURIComponent(shortName)}`)
    .then(r => {
      if (!r.ok) throw new Error();
      return r.json();
    })
    .then(data => {
      buildings = data.map(b => ({
        ...b,
        _category: categoryInfo(b.category)
      }));

      buildings.forEach(b => {
        const m = L.marker(
          [b.latitude, b.longitude],
          { icon: markerIcon(b) }
        );

        m.on('click', () => openPlace(b));

        b.marker = m;
        cluster.addLayer(m);
      });

      renderVisibleMarkers('all');
      updateActivity();
      loadRealActivities();
    })
    .catch(() => toast('Could not load campus places'));

  function showActivityItems(items) {
    const target = $('activityList');
    target.innerHTML = '';

    if (!items.length) {
      target.innerHTML =
        '<div class="activity-card"><div class="activity-main"><div class="activity-title">Nothing happening right now</div><div class="activity-sub">Campus activity will appear here.</div></div></div>';

      return;
    }

    items.slice(0, 2).forEach((item, index) => {
      const b = item.building_id
        ? buildings.find(x => String(x.id) === String(item.building_id))
        : null;

      const title = item.title || `Explore ${b?.name || 'campus'}`;

      const sub =
        item.description ||
        [b?.name, item.activity_type].filter(Boolean).join(' · ') ||
        'Campus activity';

      target.insertAdjacentHTML(
        'beforeend',
        `<button class="activity-card activity-${index + 1}" data-building="${b ? b.id : ''}" style="width:100%;text-align:left;color:inherit"><div class="activity-icon ${index === 0 ? 'green' : ''}">${iconSvg(index === 0 ? 'book' : 'building')}</div><div class="activity-main"><div class="activity-title">${safe(title)}</div><div class="activity-sub">${safe(sub)}</div></div><span class="activity-status">● Active</span><span class="activity-chevron">›</span></button>`
      );
    });

    target.querySelectorAll('[data-building]').forEach(el => {
      el.onclick = () => {
        const b = buildings.find(
          x => String(x.id) === el.dataset.building
        );

        if (b) {
          map.flyTo(
            [b.latitude, b.longitude],
            19,
            { duration: .6 }
          );

          openPlace(b);
        }
      };
    });
  }

  function updateActivity() {
    showActivityItems(
      buildings.slice(0, 2).map((b, i) => ({
        title: i === 0 ? `Explore ${b.name}` : `Discover ${b.name}`,
        description: `${b.category || 'Campus place'} · Tap to view`,
        building_id: b.id,
        activity_type: 'place'
      }))
    );
  }

  async function loadRealActivities() {
    if (!activityUrl) return;

    try {
      const r = await fetch(
        `${activityUrl}?university=${encodeURIComponent(shortName)}`
      );

      if (!r.ok) throw new Error();

      const data = await r.json();

      if (Array.isArray(data) && data.length) {
        showActivityItems(data);
      }
    } catch {
      // Keep the fallback activity list visible.
    }
  }

  const input = $('buildingSearch');
  const results = $('searchResults');

  function focusBuilding(b) {
    results.style.display = 'none';
    input.value = b.name;

    document.querySelectorAll('.category-chip').forEach(x =>
      x.classList.remove('active')
    );

    document
      .querySelector('.category-chip[data-category="all"]')
      .classList.add('active');

    renderVisibleMarkers('all');

    map.flyTo(
      [b.latitude, b.longitude],
      19,
      { duration: .65 }
    );

    setTimeout(() => {
      if (cluster.hasLayer(b.marker)) {
        cluster.zoomToShowLayer(b.marker, () => openPlace(b));
      } else {
        openPlace(b);
      }
    }, 180);
  }

  function renderResults(q) {
    if (!q) {
      results.style.display = 'none';
      return;
    }

    const found = buildings.filter(
      b =>
        (b.name || '').toLowerCase().includes(q) ||
        (b.category || '').toLowerCase().includes(q)
    ).slice(0, 7);

    results.innerHTML = found.map(b =>
      `<div class="search-result" data-id="${b.id}"><div class="result-icon">${iconSvg(b._category.icon)}</div><div><div>${safe(b.name)}</div><div class="result-meta">${safe(b.category || 'Building')}</div></div></div>`
    ).join('');

    results.style.display = found.length ? 'block' : 'none';

    results.querySelectorAll('.search-result').forEach(el => {
      el.onclick = () => {
        const b = buildings.find(
          x => String(x.id) === el.dataset.id
        );

        if (b) focusBuilding(b);
      };
    });
  }

  input.addEventListener('input', () =>
    renderResults(input.value.trim().toLowerCase())
  );

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = input.value.trim().toLowerCase();

      const b =
        buildings.find(x => (x.name || '').toLowerCase() === q) ||
        buildings.find(x => (x.name || '').toLowerCase().includes(q));

      if (b) {
        focusBuilding(b);
      } else {
        toast('Place not found');
      }
    }
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.map-search-row')) {
      results.style.display = 'none';
    }
  });

  document.querySelectorAll('.category-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.category-chip').forEach(x =>
        x.classList.remove('active')
      );

      btn.classList.add('active');
      renderVisibleMarkers(btn.dataset.category);
    });
  });

  let compassStarted = false;

  function orientation(e) {
    let h = null;

    if (typeof e.webkitCompassHeading === 'number') {
      h = e.webkitCompassHeading;
    } else if (e.absolute && e.alpha !== null) {
      h = 360 - e.alpha;
    } else if (e.alpha !== null && e.alpha !== undefined) {
      h = 360 - e.alpha;
    }

    if (h === null || !Number.isFinite(h)) return;

    h = (h + 360) % 360;

    const d = ((h - lastHeading + 540) % 360) - 180;

    lastHeading = (lastHeading + d * .25 + 360) % 360;

    const needle = document.querySelector('.compass-orb .needle');

    if (needle) {
      needle.style.transform =
        `translateX(-50%) rotate(${lastHeading}deg)`;
    }

    const btn = $('compassBtn');

    if (btn) {
      btn.classList.add('compass-active');
      btn.setAttribute('aria-pressed', 'true');
    }
  }

  async function startCompass() {
    if (compassStarted) return true;

    if (!('DeviceOrientationEvent' in window)) {
      toast('Compass sensors are not supported by this browser.');
      return false;
    }

    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        if (
          await DeviceOrientationEvent.requestPermission() !== 'granted'
        ) {
          toast('Allow motion/orientation access to use the compass.');
          return false;
        }
      } catch (error) {
        toast('Could not access compass sensors. Check browser permissions.');
        return false;
      }
    }

    window.addEventListener('deviceorientation', orientation, true);
    window.addEventListener('deviceorientationabsolute', orientation, true);

    compassStarted = true;
    return true;
  }

  map.getContainer().addEventListener(
    'pointerdown',
    () => {
      startCompass();
    },
    { once: true, passive: true }
  );

  function locate() {
    startCompass();

    map.locate({
      setView: false,
      watch: true,
      enableHighAccuracy: true,
      maximumAge: 3000,
      timeout: 15000
    });
  }

  // NEW: Calculate the direction between two GPS positions.
  // This is a bearing measured clockwise from north.
  function calculateBearing(from, to) {
    const lat1 = from.lat * Math.PI / 180;
    const lat2 = to.lat * Math.PI / 180;
    const deltaLng = (to.lng - from.lng) * Math.PI / 180;

    const y = Math.sin(deltaLng) * Math.cos(lat2);

    const x =
      Math.cos(lat1) * Math.sin(lat2) -
      Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLng);

    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }

  // NEW: Rotate the small arrow on the blue location dot.
  function updateWalkingArrow(currentLocation, accuracy) {
    if (!previousLocation) {
      previousLocation = currentLocation;
      return;
    }

    // Avoid trusting GPS readings with poor accuracy.
    if (accuracy > 35) {
      return;
    }

    const distance = map.distance(previousLocation, currentLocation);

    // Tiny movements may just be GPS noise, not actual walking.
    if (distance < 3) {
      return;
    }

    const heading = calculateBearing(
      previousLocation,
      currentLocation
    );

    // Smooth the arrow's rotation to reduce sudden jumps.
    if (lastMovementHeading === null) {
      lastMovementHeading = heading;
    } else {
      const difference =
        ((heading - lastMovementHeading + 540) % 360) - 180;

      lastMovementHeading =
        (lastMovementHeading + difference * 0.35 + 360) % 360;
    }

    const arrow = document.querySelector('.user-heading');

    if (arrow) {
      arrow.style.transform =
        `translateX(-50%) rotate(${lastMovementHeading}deg)`;
    }

    previousLocation = currentLocation;
  }

  // Existing location marker, with the walking-direction update added.
  map.on('locationfound', e => {
    if (!userMarker) {
      userMarker = L.marker(e.latlng, {
        interactive: false,
        icon: L.divIcon({
          className: '',
          html: '<div class="user-location"><div class="user-heading"></div></div>',
          iconSize: [18, 18],
          iconAnchor: [9, 9]
        })
      }).addTo(map);

      accuracyCircle = L.circle(e.latlng, {
        radius: Math.max(e.accuracy, 25),
        color: '#4d9aff',
        fillColor: '#4d9aff',
        fillOpacity: .12,
        weight: 1,
        interactive: false
      }).addTo(map);
    } else {
      userMarker.setLatLng(e.latlng);
      accuracyCircle.setLatLng(e.latlng);
      accuracyCircle.setRadius(Math.max(e.accuracy, 25));
    }

    // NEW: Update the small arrow when GPS movement is reliable.
    updateWalkingArrow(e.latlng, e.accuracy);
  });

  map.on('locationerror', () =>
    toast('Location unavailable. Check GPS permissions.')
  );

  $('locateBtn').onclick = () => {
    locate();

    if (userMarker) {
      map.flyTo(
        userMarker.getLatLng(),
        18,
        { duration: .8 }
      );
    } else {
      toast('Finding your location…');
    }
  };

  $('compassBtn').onclick = async () => {
    const ok = await startCompass();

    if (ok) toast('Compass activated');
  };

  $('layersBtn').onclick = () => {
    if (baseMode === 'satellite') {
      map.removeLayer(satellite);
      darkTiles.addTo(map);
      baseMode = 'dark';
      toast('Dark map enabled');
    } else {
      map.removeLayer(darkTiles);
      satellite.addTo(map);
      baseMode = 'satellite';
      toast('Satellite map enabled');
    }
  };

  window.unimapSetStart = (lat, lng) => {
    routeStart = L.latLng(lat, lng);
    toast('Start location set');
  };

  window.unimapSetEnd = (lat, lng) => {
    routeEnd = L.latLng(lat, lng);
    toast('Destination set');

    if (!routeStart && userMarker) {
      routeStart = userMarker.getLatLng();
    }

    if (routeStart) buildRoute();
  };

  window.unimapNavigate = (lat, lng) => {
    routeEnd = L.latLng(lat, lng);
    closePlace();

    if (!routeStart && userMarker) {
      routeStart = userMarker.getLatLng();
    }

    if (!routeStart) {
      locate();
      toast('Getting your location…');

      setTimeout(() => {
        if (userMarker) {
          routeStart = userMarker.getLatLng();
          buildRoute();
        }
      }, 1800);

      return;
    }

    buildRoute();
  };

  async function buildRoute() {
    if (!routeStart || !routeEnd) return;

    navigationActive = true;

    try {
      const r = await fetch(
        `${routeUrl}?start=${routeStart.lat},${routeStart.lng}&end=${routeEnd.lat},${routeEnd.lng}`
      );

      if (!r.ok) throw new Error();

      const d = await r.json();
      const coords = d.coordinates.map(c => [c[1], c[0]]);

      if (routeLine) map.removeLayer(routeLine);

      routeLine = L.polyline(coords, {
        color: '#1677ff',
        weight: 6,
        opacity: .9
      }).addTo(map);

      map.fitBounds(routeLine.getBounds(), {
        padding: [80, 80]
      });

      $('routeCard').style.display = 'block';

      if ($('stopNavigation')) {
        $('stopNavigation').style.display = 'block';
      }

      $('routeDistance').textContent = Math.round(d.distance) + ' m';
      $('routeDuration').textContent = d.duration;
    } catch {
      toast('Route could not be created');
    }
  }

  $('routeClose').onclick = () => {
    if (routeLine) map.removeLayer(routeLine);

    routeLine = null;
    routeStart = null;
    routeEnd = null;
    navigationActive = false;

    map.stopLocate();

    $('routeCard').style.display = 'none';
  };

  let navigationActive = false;

  function stopNavigation() {
    navigationActive = false;
    map.stopLocate();

    routeStart = null;
    routeEnd = null;

    if (routeLine) {
      map.removeLayer(routeLine);
      routeLine = null;
    }

    $('routeCard').style.display = 'none';

    toast('Navigation stopped');
  }

  if ($('stopNavigation')) {
    $('stopNavigation').onclick = stopNavigation;
  }

  // Bottom dock: default = one item, collapsed = grabber + nav only, expanded = two items.
  const dock = $('bottomDock');
  const grab = $('sheetGrabber');
  const sheet = $('campusSheet');

  let dragging = false;
  let startY = 0;
  let lastY = 0;
  let dragMoved = false;

  const setDockState = state => {
    dock.classList.remove('collapsed', 'expanded');

    if (state === 'collapsed') dock.classList.add('collapsed');
    if (state === 'expanded') dock.classList.add('expanded');

    dock.dataset.state = state;
  };

  setDockState('default');

  const beginDrag = e => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (e.target.closest('.unimap-bottom-nav, .sheet-link')) return;

    dragging = true;
    dragMoved = false;
    startY = e.clientY;
    lastY = startY;

    dock.classList.add('dragging');

    if (e.currentTarget.setPointerCapture) {
      try {
        e.currentTarget.setPointerCapture(e.pointerId);
      } catch {}
    }
  };

  const moveDrag = e => {
    if (!dragging) return;

    lastY = e.clientY;

    if (Math.abs(lastY - startY) > 8) {
      dragMoved = true;
    }

    if (dragMoved) e.preventDefault();
  };

  const endDrag = () => {
    if (!dragging) return;

    dragging = false;
    dock.classList.remove('dragging');

    const dy = lastY - startY;

    if (dy < -35) {
      setDockState('expanded');
    } else if (dy > 35) {
      setDockState('collapsed');
    }
  };

  sheet.addEventListener('pointerdown', beginDrag);
  grab.addEventListener('pointerdown', beginDrag);

  window.addEventListener('pointermove', moveDrag, {
    passive: false
  });

  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);

  grab.addEventListener('click', () => {
    if (dock.classList.contains('collapsed')) {
      setDockState('default');
    } else if (dock.classList.contains('expanded')) {
      setDockState('default');
    } else {
      setDockState('expanded');
    }
  });

  let deferredInstall = null;

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    deferredInstall = e;
  });

  window.addEventListener('appinstalled', () => {
    deferredInstall = null;
    toast('UNIMAP installed successfully');
  });

  const downloadBtn = $('downloadBtn');

  if (downloadBtn) {
    downloadBtn.onclick = async () => {
      if (window.matchMedia('(display-mode: standalone)').matches) {
        toast('UNIMAP is already installed');
        return;
      }

      if (deferredInstall) {
        deferredInstall.prompt();

        try {
          await deferredInstall.userChoice;
        } catch {}

        deferredInstall = null;
        return;
      }

      toast(
        'UNIMAP install is not available yet — use your browser install option'
      );
    };
  }

  const splash = $('unimapSplash');

  if (splash) {
    setTimeout(() => splash.classList.add('hide'), 1550);
    setTimeout(() => splash.remove(), 2050);
  }

  setTimeout(locate, 700);

  window.addEventListener('resize', () =>
    map.invalidateSize({ animate: false })
  );
})();

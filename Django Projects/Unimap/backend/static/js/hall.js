(() => {
  const list = document.getElementById("hallList");
  if (!list) return;

  const icon = window.UNIMAP_HALL_ICON || "";
  const refreshButton = document.getElementById("hallRefresh");
  const filterButton = document.getElementById("hallFilterButton");
  const filterPanel = document.getElementById("hallFilterPanel");
  const statusFilter = document.getElementById("hallStatusFilter");
  const buildingFilter = document.getElementById("hallBuildingFilter");
  const countNode = document.getElementById("hallCount");
  const viewLabel = document.getElementById("hallViewLabel");
  const tabs = [...document.querySelectorAll(".halls-tab")];

  let halls = [];
  let currentView = "near";
  let userLocation = null;

  const labels = {
    available: "Available",
    in_use: "In Use",
    limited: "Limited",
    closed: "Closed"
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function distanceKm(lat1, lon1, lat2, lon2) {
    const toRad = value => value * Math.PI / 180;
    const R = 6371;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function formatDistance(km) {
    if (!Number.isFinite(km)) return "";
    if (km < 1) return `${Math.round(km * 1000)} m away`;
    return `${km.toFixed(1)} km away`;
  }

  function getUniversity() {
    const profileUniversity = document.body.dataset.university || "";
    return profileUniversity;
  }

  function setLoading() {
    list.innerHTML = `
      <div class="hall-loading">
        <span class="hall-loading-spinner"></span>
        <span>Loading halls…</span>
      </div>
    `;
  }

  function setError() {
    list.innerHTML = `
      <div class="hall-error">
        <strong>Could not load halls</strong>
        <p>Check the academic halls API and refresh this page.</p>
      </div>
    `;
  }

  function populateBuildingFilter() {
    const names = [...new Set(
      halls
        .map(h => h.building || h.name)
        .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b));

    buildingFilter.innerHTML =
      `<option value="all">All buildings</option>` +
      names.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
  }

  function filteredHalls() {
    let rows = halls.slice();

    const status = statusFilter.value;
    const building = buildingFilter.value;

    if (status !== "all") {
      rows = rows.filter(h => h.status === status);
    }

    if (building !== "all") {
      rows = rows.filter(h => (h.building || h.name) === building);
    }

    if (currentView === "near") {
      if (userLocation) {
        rows.forEach(h => {
          h._distance = distanceKm(
            userLocation.lat,
            userLocation.lng,
            Number(h.latitude),
            Number(h.longitude)
          );
        });
        rows.sort((a, b) => (a._distance ?? Infinity) - (b._distance ?? Infinity));
      }
    }

    if (currentView === "all") {
      rows.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
    }

    if (currentView === "building") {
      rows.sort((a, b) => {
        const aa = String(a.building || a.name || "");
        const bb = String(b.building || b.name || "");
        return aa.localeCompare(bb) || String(a.name || "").localeCompare(String(b.name || ""));
      });
    }

    return rows;
  }

  function card(h) {
    const status = labels[h.status] ? h.status : "available";
    const category = h.category || "Hall";
    const floor = h.floor ? `Floor ${h.floor}` : "";
    const meta = [category, floor].filter(Boolean).join(" · ");

    const distance = userLocation && Number.isFinite(h._distance)
      ? `<span class="hall-distance">${escapeHtml(formatDistance(h._distance))}</span>`
      : "";

    const capacity = h.capacity
      ? `<div class="hall-capacity">Capacity ${escapeHtml(h.capacity)}</div>`
      : "";

    const currentClass = h.current_class
      ? `<div class="hall-capacity">${escapeHtml(h.current_class)} in progress</div>`
      : "";

    return `
      <article class="hall-card">
        <div class="hall-icon" aria-hidden="true">${icon}</div>

        <div class="hall-main">
          <div class="hall-name">${escapeHtml(h.name || "Unnamed hall")}</div>
          <div class="hall-meta">
            <span>${escapeHtml(meta || "Campus hall")}</span>
            ${distance}
          </div>
        </div>

        <div class="hall-side">
          <span class="hall-status ${status}">
            <span class="hall-status-dot"></span>
            ${escapeHtml(labels[status] || status)}
          </span>
          ${capacity}
          ${currentClass}
        </div>
      </article>
    `;
  }

  function render() {
    const rows = filteredHalls();

    countNode.textContent = `${rows.length} ${rows.length === 1 ? "hall" : "halls"}`;

    const labelsByView = {
      near: userLocation ? "Nearest to your location" : "Near you · location not available",
      all: "All halls",
      building: "Grouped by building"
    };
    viewLabel.textContent = labelsByView[currentView];

    if (!rows.length) {
      list.innerHTML = `
        <div class="hall-empty">
          <div class="hall-empty-icon">${icon}</div>
          <h3>No halls match this view</h3>
          <p>Try another tab or change the filters.</p>
        </div>
      `;
      return;
    }

    if (currentView !== "building") {
      list.innerHTML = rows.map(card).join("");
      return;
    }

    const groups = new Map();

    rows.forEach(h => {
      const key = h.building || h.name || "Other";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(h);
    });

    list.innerHTML = [...groups.entries()].map(([name, group]) => `
      <section class="hall-group">
        <div class="hall-group-title">
          <strong>${escapeHtml(name)}</strong>
          <span>${group.length} ${group.length === 1 ? "hall" : "halls"}</span>
        </div>
        ${group.map(card).join("")}
      </section>
    `).join("");
  }

  function requestLocation() {
    if (!navigator.geolocation) {
      render();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        render();
      },
      () => render(),
      {
        enableHighAccuracy: true,
        timeout: 7000,
        maximumAge: 300000
      }
    );
  }

  async function loadHalls() {
    setLoading();
    refreshButton.classList.add("loading");

    try {
      const university = getUniversity();
      const query = university
        ? `?university=${encodeURIComponent(university)}`
        : "";

      const response = await fetch(`/api/academic/halls/${query}`, {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      halls = Array.isArray(data) ? data : [];

      populateBuildingFilter();
      render();

      if (currentView === "near" && !userLocation) {
        requestLocation();
      }
    } catch (error) {
      console.error("UNIMAP halls:", error);
      setError();
      countNode.textContent = "—";
      viewLabel.textContent = "Unable to load";
    } finally {
      refreshButton.classList.remove("loading");
    }
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      currentView = tab.dataset.view || "all";

      tabs.forEach(item => {
        const active = item === tab;
        item.classList.toggle("active", active);
        item.setAttribute("aria-selected", active ? "true" : "false");
      });

      if (currentView === "near" && !userLocation) {
        requestLocation();
      }

      render();
    });
  });

  filterButton.addEventListener("click", () => {
    const open = filterPanel.hidden;
    filterPanel.hidden = !open;
    filterButton.classList.toggle("active", open);
    filterButton.setAttribute("aria-expanded", open ? "true" : "false");
  });

  statusFilter.addEventListener("change", render);
  buildingFilter.addEventListener("change", render);
  refreshButton.addEventListener("click", loadHalls);

  loadHalls();
})();

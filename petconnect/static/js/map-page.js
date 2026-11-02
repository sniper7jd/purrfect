// Playdate map: clustered pet markers, loaded for the visible area only.
(() => {
  const element = document.getElementById("map");
  if (!element) return;

  const config = JSON.parse(document.getElementById("map-config").textContent);
  const countLabel = document.querySelector("[data-pet-count]");
  const map = PetMaps.createMap(element, {
    lat: config.center.lat,
    lng: config.center.lng,
    zoom: config.zoom,
  });
  const cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 50 });
  map.addLayer(cluster);

  const markers = new Map();
  let controller = null;
  let debounceTimer = null;
  let userMarker = null;
  let fitted = Boolean(config.focusPet);

  function addPet(pet) {
    if (markers.has(pet.id)) return markers.get(pet.id);
    const isFocus = pet.id === config.focusPetId;
    const marker = L.marker([pet.latitude, pet.longitude], {
      icon: PetMaps.petIcon({ name: pet.name, imageUrl: pet.image_url, focus: isFocus }),
      title: pet.name,
      zIndexOffset: isFocus ? 1000 : 0,
    }).bindPopup(() => PetMaps.petPopup(pet));
    markers.set(pet.id, marker);
    cluster.addLayer(marker);
    return marker;
  }

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  async function loadVisiblePets() {
    const bounds = map.getBounds();
    const url = new URL(config.endpoint, window.location.origin);
    url.searchParams.set("south", clamp(bounds.getSouth(), -90, 90).toFixed(5));
    url.searchParams.set("north", clamp(bounds.getNorth(), -90, 90).toFixed(5));
    url.searchParams.set("west", clamp(bounds.getWest(), -180, 180).toFixed(5));
    url.searchParams.set("east", clamp(bounds.getEast(), -180, 180).toFixed(5));

    controller?.abort();
    controller = new AbortController();
    try {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) return;
      const data = await response.json();
      data.pets.forEach(addPet);
      if (!fitted && data.pets.length > 1) {
        fitted = true;
        map.fitBounds(cluster.getBounds(), { padding: [60, 60], maxZoom: 15 });
      }
      if (countLabel) {
        const count = `${data.pets.length}${data.truncated ? "+" : ""}`;
        countLabel.textContent = `${count} pet${data.pets.length === 1 ? "" : "s"} in this area`;
      }
    } catch (error) {
      if (error.name !== "AbortError") throw error;
    }
  }

  map.on("moveend", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadVisiblePets, 250);
  });
  loadVisiblePets();

  if (config.focusPet) {
    const marker = addPet(config.focusPet);
    cluster.zoomToShowLayer(marker, () => marker.openPopup());
  }

  document.getElementById("locate-me-btn")?.addEventListener("click", () => {
    map.locate({ setView: true, maxZoom: 14 });
  });
  map.on("locationfound", ({ latlng }) => {
    userMarker?.remove();
    userMarker = L.circleMarker(latlng, {
      radius: 9,
      color: "#fff",
      weight: 3,
      fillColor: "#2563eb",
      fillOpacity: 1,
    })
      .bindTooltip("You are here")
      .addTo(map);
  });
  map.on("locationerror", () => alert("Unable to get your location."));
})();

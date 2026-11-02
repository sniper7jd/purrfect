// Address search + "use my location" for the pet form.
// Autocomplete: Photon (built for search-as-you-type). Reverse geocoding: Nominatim
// (its usage policy forbids autocomplete, so it is only called once per button press).
(() => {
  const root = document.querySelector("[data-location-picker]");
  if (!root) return;

  const PHOTON_URL = "https://photon.komoot.io/api/";
  const NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse";

  const input = root.querySelector("#location-input");
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const list = root.querySelector("[data-suggestions]");
  const previewElement = root.querySelector("[data-preview-map]");
  const detectButton = root.querySelector("[data-detect-location]");
  const detectLabel = root.querySelector("[data-detect-label]");

  let results = [];
  let activeIndex = -1;
  let debounceTimer = null;
  let controller = null;
  let map = null;
  let marker = null;

  const unique = (parts) => parts.filter((part, i) => part && parts.indexOf(part) === i);

  function photonLabel({ properties: p }) {
    return unique([p.name, p.district, p.city || p.county, p.state, p.country]).join(", ");
  }

  function nominatimLabel({ address: a = {}, display_name: fallback }) {
    const label = unique([
      a.suburb || a.neighbourhood,
      a.city || a.town || a.village || a.county,
      a.state,
    ]).join(", ");
    return label || fallback;
  }

  function hideSuggestions() {
    list.classList.add("hidden");
    activeIndex = -1;
  }

  function renderSuggestions() {
    list.replaceChildren(
      ...results.map((result, index) => {
        const item = document.createElement("li");
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", String(index === activeIndex));
        item.className = `px-4 py-2 text-sm cursor-pointer hover:bg-orange-50 ${
          index === activeIndex ? "bg-orange-50" : ""
        }`;
        item.textContent = result.label;
        item.addEventListener("mousedown", (event) => {
          event.preventDefault();
          choose(result);
        });
        return item;
      }),
    );
    list.classList.toggle("hidden", results.length === 0);
  }

  async function search(query) {
    controller?.abort();
    controller = new AbortController();
    const url = new URL(PHOTON_URL);
    url.searchParams.set("q", query);
    url.searchParams.set("limit", "6");
    url.searchParams.set("lang", "en");
    if (map) {
      const center = map.getCenter();
      url.searchParams.set("lat", center.lat.toFixed(4));
      url.searchParams.set("lon", center.lng.toFixed(4));
    }
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) return;
    const data = await response.json();
    results = data.features.map((feature) => ({
      label: photonLabel(feature),
      lat: feature.geometry.coordinates[1],
      lng: feature.geometry.coordinates[0],
    }));
    activeIndex = -1;
    renderSuggestions();
  }

  function showPreview(lat, lng) {
    previewElement.classList.remove("hidden");
    if (!map) {
      map = PetMaps.createMap(previewElement, { lat, lng, zoom: 13 });
      marker = L.marker([lat, lng]).addTo(map);
    } else {
      map.setView([lat, lng], 13);
      marker.setLatLng([lat, lng]);
    }
    map.invalidateSize();
  }

  function setCoordinates(lat, lng) {
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    showPreview(lat, lng);
  }

  function choose(result) {
    input.value = result.label;
    setCoordinates(result.lat, result.lng);
    hideSuggestions();
  }

  input.addEventListener("input", () => {
    latInput.value = "";
    lngInput.value = "";
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length < 3) {
      hideSuggestions();
      return;
    }
    debounceTimer = setTimeout(() => search(query).catch(() => {}), 300);
  });

  input.addEventListener("keydown", (event) => {
    if (list.classList.contains("hidden") || results.length === 0) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      activeIndex = (activeIndex + step + results.length) % results.length;
      renderSuggestions();
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(results[activeIndex]);
    } else if (event.key === "Escape") {
      hideSuggestions();
    }
  });

  input.addEventListener("blur", () => setTimeout(hideSuggestions, 150));

  detectButton?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    detectButton.disabled = true;
    detectLabel.textContent = "Locating\u2026";

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        setCoordinates(coords.latitude, coords.longitude);
        try {
          const url = new URL(NOMINATIM_REVERSE_URL);
          url.searchParams.set("format", "jsonv2");
          url.searchParams.set("lat", coords.latitude);
          url.searchParams.set("lon", coords.longitude);
          url.searchParams.set("zoom", "14");
          url.searchParams.set("addressdetails", "1");
          const response = await fetch(url, { headers: { "Accept-Language": "en" } });
          input.value = nominatimLabel(await response.json());
        } catch {
          input.value = `${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`;
        } finally {
          detectButton.disabled = false;
          detectLabel.textContent = "Use my location";
        }
      },
      (error) => {
        const reasons = {
          [error.PERMISSION_DENIED]: "Location access was denied. Allow it in your browser settings.",
          [error.POSITION_UNAVAILABLE]: "Your location is unavailable right now.",
          [error.TIMEOUT]: "Finding your location timed out.",
        };
        alert(reasons[error.code] || "Unable to detect your location.");
        detectButton.disabled = false;
        detectLabel.textContent = "Use my location";
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  });

  const initialLat = parseFloat(latInput.value);
  const initialLng = parseFloat(lngInput.value);
  if (!Number.isNaN(initialLat) && !Number.isNaN(initialLng)) {
    showPreview(initialLat, initialLng);
  }
})();

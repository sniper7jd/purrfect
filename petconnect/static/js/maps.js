// Shared Leaflet helpers. Tiles: OpenStreetMap (attribution required by the tile usage policy).
window.PetMaps = (() => {
  const TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  const ATTRIBUTION =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  function createMap(element, { lat, lng, zoom = 13, interactive = true }) {
    const map = L.map(element, {
      zoomControl: interactive,
      dragging: interactive,
      scrollWheelZoom: interactive,
      doubleClickZoom: interactive,
      touchZoom: interactive,
      keyboard: interactive,
    }).setView([lat, lng], zoom);
    L.tileLayer(TILE_URL, { maxZoom: 19, attribution: ATTRIBUTION }).addTo(map);
    return map;
  }

  function petIcon({ name, imageUrl, focus = false }) {
    const marker = document.createElement("div");
    marker.className = focus ? "pet-marker is-focus" : "pet-marker";
    if (imageUrl) {
      const img = document.createElement("img");
      img.src = imageUrl;
      img.alt = name;
      marker.appendChild(img);
    } else {
      marker.textContent = (name || "?").charAt(0).toUpperCase();
    }
    const size = focus ? 56 : 40;
    return L.divIcon({
      html: marker,
      className: "",
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -size / 2],
    });
  }

  // Leaflet's default marker images can't be located once static files are hashed,
  // so the location picker uses a CSS pin instead.
  function pinIcon() {
    return L.divIcon({
      html: '<span class="location-pin"></span>',
      className: "",
      iconSize: [32, 32],
      iconAnchor: [16, 39],
    });
  }

  function petPopup(pet) {
    const wrapper = document.createElement("div");
    wrapper.className = "min-w-[180px]";
    if (pet.image_url) {
      const img = document.createElement("img");
      img.src = pet.image_url;
      img.alt = pet.name;
      img.className = "w-full h-28 object-cover rounded-lg mb-2";
      wrapper.appendChild(img);
    }
    const title = document.createElement("p");
    title.className = "font-bold text-base m-0!";
    title.textContent = pet.name;
    const subtitle = document.createElement("p");
    subtitle.className = "text-gray-500 text-sm m-0!";
    subtitle.textContent = pet.breed || pet.species;
    const link = document.createElement("a");
    link.href = pet.profile_url;
    link.className = "inline-block mt-2 text-sm font-semibold text-brand! hover:underline";
    link.textContent = "View profile \u2192";
    wrapper.append(title, subtitle, link);
    return wrapper;
  }

  function initMiniMaps() {
    document.querySelectorAll("[data-mini-map]").forEach((element) => {
      const lat = parseFloat(element.dataset.lat);
      const lng = parseFloat(element.dataset.lng);
      if (Number.isNaN(lat) || Number.isNaN(lng)) return;
      const map = createMap(element, { lat, lng, zoom: 13, interactive: false });
      L.marker([lat, lng], {
        icon: petIcon({ name: element.dataset.name, imageUrl: element.dataset.image }),
        keyboard: false,
      }).addTo(map);
    });
  }

  document.addEventListener("DOMContentLoaded", initMiniMaps);

  return { createMap, petIcon, pinIcon, petPopup };
})();

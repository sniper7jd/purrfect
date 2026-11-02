// Shared Alpine components. Loaded before Alpine itself so `alpine:init` fires after registration.
document.addEventListener("alpine:init", () => {
  Alpine.data("searchSuggest", (url, initial = "") => ({
    query: initial,
    items: [],
    open: false,
    async fetchSuggestions() {
      if (this.query.trim().length < 2) {
        this.items = [];
        this.open = false;
        return;
      }
      const response = await fetch(`${url}?query=${encodeURIComponent(this.query)}`);
      if (!response.ok) return;
      this.items = await response.json();
      this.open = this.items.length > 0;
    },
    choose(item) {
      this.query = item.text;
      this.open = false;
      this.$nextTick(() => this.$root.closest("form")?.requestSubmit());
    },
  }));

  Alpine.data("imagePreview", () => ({
    preview: null,
    pick(event) {
      const [file] = event.target.files;
      if (!file) return;
      if (this.preview) URL.revokeObjectURL(this.preview);
      this.preview = URL.createObjectURL(file);
    },
  }));

  Alpine.data("shareLink", (url) => ({
    copied: false,
    async share() {
      const absolute = new URL(url, window.location.origin).href;
      if (navigator.share) {
        try {
          await navigator.share({ url: absolute });
          return;
        } catch {
          // Fall back to copying when the share sheet is dismissed or unavailable.
        }
      }
      await navigator.clipboard.writeText(absolute);
      this.copied = true;
      setTimeout(() => (this.copied = false), 1500);
    },
  }));
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}

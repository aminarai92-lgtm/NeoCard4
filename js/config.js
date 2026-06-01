const NeoConfig = {
  get apiBase() {
    if (window.NEO_API_BASE) return window.NEO_API_BASE;
    const origin = window.location.origin;
    if (origin.includes("localhost") || origin.includes("127.0.0.1")) {
      return origin.includes(":8000") ? origin : "http://localhost:8000";
    }
    return origin;
  },

  /** Base URL for links you send to other people (set PUBLIC_BASE_URL when deployed). */
  get shareBase() {
    const custom = localStorage.getItem("neocard_share_base");
    if (custom) return custom.replace(/\/$/, "");
    return window.location.origin;
  },

  isLocalOnly() {
    const host = window.location.hostname;
    return host === "localhost" || host === "127.0.0.1";
  },

  cardPublicUrl(slug) {
    return `${this.shareBase}/pages/card.html?slug=${encodeURIComponent(slug)}`;
  },

  storageKeys: {
    accessToken: "neocard_access_token",
    refreshToken: "neocard_refresh_token",
    user: "neocard_user",
  },
};

window.NeoConfig = NeoConfig;

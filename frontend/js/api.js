class NeoAPI {
  constructor() {
    this.base = NeoConfig.apiBase;
  }

  getAccessToken() {
    return localStorage.getItem(NeoConfig.storageKeys.accessToken);
  }

  getRefreshToken() {
    return localStorage.getItem(NeoConfig.storageKeys.refreshToken);
  }

  setTokens(access, refresh, user) {
    localStorage.setItem(NeoConfig.storageKeys.accessToken, access);
    localStorage.setItem(NeoConfig.storageKeys.refreshToken, refresh);
    if (user) localStorage.setItem(NeoConfig.storageKeys.user, JSON.stringify(user));
  }

  clearTokens() {
    Object.values(NeoConfig.storageKeys).forEach((k) => localStorage.removeItem(k));
  }

  getUser() {
    try {
      return JSON.parse(localStorage.getItem(NeoConfig.storageKeys.user) || "null");
    } catch {
      return null;
    }
  }

  async refreshAccessToken() {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;
    try {
      const res = await fetch(`${this.base}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setTokens(data.access_token, data.refresh_token, data.user);
      return true;
    } catch {
      return false;
    }
  }

  async request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = this.getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    let res = await fetch(`${this.base}${path}`, { ...options, headers });

    if (res.status === 401 && token) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers.Authorization = `Bearer ${this.getAccessToken()}`;
        res = await fetch(`${this.base}${path}`, { ...options, headers });
      }
    }

    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { detail: text || "Unknown error" };
    }

    if (!res.ok) {
      const detail = data.detail;
      const message = typeof detail === "string" ? detail : Array.isArray(detail)
        ? detail.map((d) => d.msg || d).join(", ")
        : data.message || `HTTP ${res.status}`;
      const err = new Error(message);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  get(path) {
    return this.request(path);
  }

  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body) });
  }

  put(path, body) {
    return this.request(path, { method: "PUT", body: JSON.stringify(body) });
  }

  patch(path, body) {
    return this.request(path, { method: "PATCH", body: JSON.stringify(body) });
  }

  delete(path) {
    return this.request(path, { method: "DELETE" });
  }
}

window.api = new NeoAPI();

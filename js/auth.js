const NeoAuth = {
  isLoggedIn() {
    return !!api.getAccessToken();
  },

  _readAuthParams() {
    const hash = window.location.hash.startsWith("#")
      ? window.location.hash.slice(1)
      : "";
    if (hash) return new URLSearchParams(hash);
    return new URLSearchParams(window.location.search);
  },

  async requireAuth(redirectTo = "/index.html") {
    if (!this.isLoggedIn()) {
      window.location.href = redirectTo.startsWith("/") ? redirectTo : `/${redirectTo}`;
      return false;
    }
    try {
      const user = await api.get("/api/auth/me");
      localStorage.setItem(NeoConfig.storageKeys.user, JSON.stringify(user));
      if (user.is_blocked) {
        this.logout();
        NeoUI.toast("Аккаунт заблокирован", "error");
        return false;
      }
      return user;
    } catch {
      api.clearTokens();
      window.location.href = "/index.html";
      return false;
    }
  },

  async loginWithGoogle() {
    const data = await api.get("/api/auth/google/url");
    window.location.href = data.auth_url;
  },

  handleCallback() {
    const params = this._readAuthParams();
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    if (access && refresh) {
      api.setTokens(access, refresh);
      history.replaceState(null, "", window.location.pathname);
      window.location.replace("/pages/dashboard.html");
      return true;
    }
    return false;
  },

  async logout() {
    const refresh = api.getRefreshToken();
    try {
      if (refresh) await api.post("/api/auth/logout", { refresh_token: refresh });
    } catch {
      /* ignore */
    }
    api.clearTokens();
    window.location.href = "/index.html";
  },

  isAdmin() {
    const user = api.getUser();
    return user?.role === "admin";
  },
};

window.NeoAuth = NeoAuth;

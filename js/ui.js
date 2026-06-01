const NeoUI = {
  toast(message, type = "success") {
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 300);
    }, 3500);
  },

  showLoading() {
    let el = document.querySelector(".loading-screen");
    if (!el) {
      el = document.createElement("div");
      el.className = "loading-screen";
      el.innerHTML = '<div class="spinner"></div>';
      document.body.appendChild(el);
    }
    el.classList.remove("hidden");
  },

  hideLoading() {
    const el = document.querySelector(".loading-screen");
    if (el) el.classList.add("hidden");
  },

  initials(first, last) {
    return `${(first || "?")[0]}${(last || "")[0] || ""}`.toUpperCase();
  },

  formatDate(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  },

  escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  },

  renderBottomNav(active) {
    const nav = document.getElementById("bottom-nav");
    if (!nav) return;
    nav.classList.add("visible");
    nav.querySelectorAll("a").forEach((a) => {
      a.classList.toggle("active", a.dataset.nav === active);
    });
  },

  renderHeader(title, showBack = false) {
    const header = document.getElementById("app-header");
    if (!header) return;
    const backBtn = header.querySelector(".btn-back");
    if (backBtn) backBtn.style.display = showBack ? "inline-flex" : "none";
    const titleEl = header.querySelector(".page-title");
    if (titleEl) titleEl.textContent = title || "";
  },

  confirm(message) {
    return window.confirm(message);
  },

  shareCard(slug, name, options = {}) {
    const url = NeoConfig.cardPublicUrl(slug);
    if (NeoConfig.isLocalOnly() && !options.silent) {
      const lanHint = "Для друга в интернете нужен публичный адрес сервера (не localhost).\n\n" +
        "Сейчас ссылка работает только на этом компьютере или в вашей Wi‑Fi сети (замените localhost на IP компьютера, например http://192.168.1.5:8000).\n\n" +
        "Скопировать ссылку всё равно?";
      if (!this.confirm(lanHint)) return;
    }
    if (navigator.share) {
      navigator.share({ title: name, url }).catch(() => this.copyText(url));
    } else {
      this.copyText(url);
    }
  },

  copyText(text) {
    navigator.clipboard.writeText(text).then(
      () => NeoUI.toast("Ссылка скопирована"),
      () => NeoUI.toast("Не удалось скопировать", "error")
    );
  },

  cardListItemHTML(card, actions = "") {
    const name = `${card.first_name} ${card.last_name}`;
    const avatar = card.photo_url
      ? `<img class="avatar" src="${this.escapeHtml(card.photo_url)}" alt="">`
      : `<div class="avatar">${this.initials(card.first_name, card.last_name)}</div>`;
    return `
      <article class="glass-card card-preview" data-id="${card.id}" data-slug="${card.slug}">
        <div class="card-preview-header">
          ${avatar}
          <div>
            <strong>${this.escapeHtml(name)}</strong>
            <p class="text-muted" style="font-size:0.85rem;color:var(--text-muted)">${this.escapeHtml(card.position || "")}</p>
          </div>
        </div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem">
          <span class="badge ${card.is_published ? "badge-published" : "badge-draft"}">${card.is_published ? "Опубликована" : "Черновик"}</span>
          <span class="badge">👁 ${card.view_count || 0}</span>
        </div>
        ${actions}
      </article>`;
  },
};

window.NeoUI = NeoUI;

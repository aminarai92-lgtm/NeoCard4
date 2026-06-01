async function initAppShell(activeNav, pageTitle, showBack = false) {
  const user = await NeoAuth.requireAuth();
  if (!user) return null;

  NeoUI.renderBottomNav(activeNav);
  NeoUI.renderHeader(pageTitle, showBack);

  const avatarBtn = document.getElementById("user-menu-btn");
  if (avatarBtn && user.avatar_url) {
    avatarBtn.innerHTML = `<img src="${NeoUI.escapeHtml(user.avatar_url)}" alt="" style="width:36px;height:36px;border-radius:50%">`;
  }

  if (NeoAuth.isAdmin()) {
    const adminLink = document.getElementById("admin-link");
    if (adminLink) adminLink.style.display = "inline-flex";
  }

  document.getElementById("btn-logout")?.addEventListener("click", () => NeoAuth.logout());

  NeoUI.hideLoading();
  return user;
}

function loadNav() {
  fetch("/pages/_nav.html")
    .then((r) => r.text())
    .then((html) => {
      const wrap = document.createElement("div");
      wrap.innerHTML = html;
      document.body.appendChild(wrap.firstElementChild);
    })
    .catch(() => {});
}

window.initAppShell = initAppShell;

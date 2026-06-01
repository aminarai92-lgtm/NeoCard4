const NeoCards = {
  templates: [
    { id: "modern_blue", name: "Modern Blue" },
    { id: "business_dark", name: "Business Dark" },
    { id: "minimal_white", name: "Minimal White" },
    { id: "gradient_purple", name: "Gradient Purple" },
  ],

  formToPayload(form) {
    const fd = new FormData(form);
    const skillsRaw = fd.get("skills") || "";
    const skills = skillsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const extraLinks = [];
    form.querySelectorAll(".extra-link-row").forEach((row) => {
      const label = row.querySelector('[name="link_label"]')?.value?.trim();
      const url = row.querySelector('[name="link_url"]')?.value?.trim();
      if (label && url) extraLinks.push({ label, url });
    });
    return {
      first_name: fd.get("first_name"),
      last_name: fd.get("last_name"),
      birth_date: fd.get("birth_date") || null,
      position: fd.get("position") || null,
      phone: fd.get("phone") || null,
      telegram: fd.get("telegram") || null,
      instagram: fd.get("instagram") || null,
      skills,
      experience: fd.get("experience") || null,
      school: fd.get("school") || null,
      college: fd.get("college") || null,
      university: fd.get("university") || null,
      masters: fd.get("masters") || null,
      description: fd.get("description") || null,
      website: fd.get("website") || null,
      extra_links: extraLinks,
      photo_url: fd.get("photo_url") || null,
      template: form.dataset.template || "modern_blue",
    };
  },

  renderPublicCard(card, container) {
    const tpl = card.template || "modern_blue";
    const name = `${card.first_name} ${card.last_name}`;
    const skills = (card.skills || [])
      .map((s) => `<span class="skill-tag">${NeoUI.escapeHtml(s)}</span>`)
      .join("");
    const edu = [card.school, card.college, card.university, card.masters]
      .filter(Boolean)
      .map((e) => `<li>${NeoUI.escapeHtml(e)}</li>`)
      .join("");
    const extra = (card.extra_links || [])
      .map((l) => `<a href="${NeoUI.escapeHtml(l.url)}" target="_blank" rel="noopener">${NeoUI.escapeHtml(l.label)}</a>`)
      .join("");
    const avatar = card.photo_url
      ? `<img class="avatar avatar-lg" src="${NeoUI.escapeHtml(card.photo_url)}" alt="">`
      : `<div class="avatar avatar-lg">${NeoUI.initials(card.first_name, card.last_name)}</div>`;

    container.innerHTML = `
      <div class="public-card template-${tpl} glass-card">
        <div class="public-card-inner">
          <div class="profile-top">${avatar}
            <h1 class="full-name">${NeoUI.escapeHtml(name)}</h1>
            <p class="position">${NeoUI.escapeHtml(card.position || "")}</p>
          </div>
          ${card.description ? `<div class="description-block">${NeoUI.escapeHtml(card.description)}</div>` : ""}
          ${skills ? `<div class="section-block"><h4>Навыки</h4><div class="skills-wrap">${skills}</div></div>` : ""}
          ${edu ? `<div class="section-block"><h4>Образование</h4><ul class="education-list">${edu}</ul></div>` : ""}
          ${card.experience ? `<div class="section-block"><h4>Опыт</h4><p class="experience-text">${NeoUI.escapeHtml(card.experience)}</p></div>` : ""}
          ${extra ? `<div class="section-block extra-links"><h4>Ссылки</h4>${extra}</div>` : ""}
          <div class="contact-actions">
            ${card.phone ? `<a class="btn btn-secondary" href="tel:${NeoUI.escapeHtml(card.phone)}">📞 Позвонить</a>` : ""}
            ${card.telegram ? `<a class="btn btn-secondary" href="${this.tgLink(card.telegram)}" target="_blank">Telegram</a>` : ""}
            ${card.instagram ? `<a class="btn btn-secondary" href="${this.igLink(card.instagram)}" target="_blank">Instagram</a>` : ""}
            ${card.website ? `<a class="btn btn-secondary" href="${NeoUI.escapeHtml(card.website)}" target="_blank">Сайт</a>` : ""}
          </div>
          <div class="qr-block" id="qr-container"></div>
          <div class="share-actions">
            <button type="button" class="btn btn-primary btn-sm" id="btn-share">Поделиться</button>
            <button type="button" class="btn btn-secondary btn-sm" id="btn-copy">Копировать ссылку</button>
            <button type="button" class="btn btn-secondary btn-sm" id="btn-vcard">В контакты</button>
            <button type="button" class="btn btn-secondary btn-sm" id="btn-save">${card.is_saved ? "✓ Сохранено" : "Сохранить"}</button>
          </div>
        </div>
      </div>`;
  },

  tgLink(v) {
    const clean = v.replace(/^@/, "");
    return v.startsWith("http") ? v : `https://t.me/${clean}`;
  },

  igLink(v) {
    const clean = v.replace(/^@/, "");
    return v.startsWith("http") ? v : `https://instagram.com/${clean}`;
  },

  generateVCard(card) {
    const name = `${card.first_name} ${card.last_name}`;
    let vcf = "BEGIN:VCARD\nVERSION:3.0\n";
    vcf += `FN:${name}\n`;
    vcf += `N:${card.last_name};${card.first_name};;;\n`;
    if (card.position) vcf += `TITLE:${card.position}\n`;
    if (card.phone) vcf += `TEL;TYPE=CELL:${card.phone}\n`;
    if (card.email) vcf += `EMAIL:${card.email}\n`;
    if (card.website) vcf += `URL:${card.website}\n`;
    if (card.description) vcf += `NOTE:${card.description.replace(/\n/g, "\\n")}\n`;
    vcf += "END:VCARD";
    const blob = new Blob([vcf], { type: "text/vcard" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${card.first_name}_${card.last_name}.vcf`;
    a.click();
  },
};

window.NeoCards = NeoCards;

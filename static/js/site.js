document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector(".menu-toggle");
  const mainNavigation = document.querySelector("#main-navigation");
  if (menuToggle && mainNavigation) {
    const closeMenu = () => {
      mainNavigation.classList.remove("is-open");
      menuToggle.setAttribute("aria-expanded", "false");
    };
    menuToggle.addEventListener("click", () => {
      const open = !mainNavigation.classList.contains("is-open");
      mainNavigation.classList.toggle("is-open", open);
      menuToggle.setAttribute("aria-expanded", String(open));
    });
    mainNavigation.addEventListener("click", event => {
      if (event.target.closest("a")) closeMenu();
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") { closeMenu(); menuToggle.focus(); }
    });
    document.addEventListener("click", event => {
      if (!mainNavigation.contains(event.target) && !menuToggle.contains(event.target)) closeMenu();
    });
  }
  document.querySelectorAll("[data-card-editor]").forEach(editor => {
    const scope = editor.closest("[data-certificate-maker], [data-project-tools]");
    const preview = scope?.querySelector("[data-card-preview]");
    if (!preview) return;
    const layout = editor.querySelector("[data-card-layout]");
    const background = editor.querySelector("[data-card-background]");
    const accent = editor.querySelector("[data-card-accent]");
    const applyCardStyle = () => {
      preview.classList.remove("card-layout-standard", "card-layout-horizontal", "card-layout-minimal", "card-bg-light", "card-bg-dark", "card-bg-transparent");
      preview.classList.add(`card-layout-${layout.value}`, `card-bg-${background.value}`);
      preview.style.setProperty("--card-accent", accent.value);
      preview.dataset.cardLayout = layout.value;
      preview.dataset.cardBackground = background.value;
      preview.dataset.cardAccent = accent.value;
      preview.dispatchEvent(new CustomEvent("cardstylechange", {bubbles: true}));
    };
    [layout, background, accent].forEach(input => input.addEventListener("input", applyCardStyle));
    applyCardStyle();
  });
  const adhesionForm = document.querySelector(".adhesion-form");
  if (adhesionForm) {
    const organizationField = adhesionForm.querySelector(".organization-field");
    const supporterTypes = [...adhesionForm.querySelectorAll('[name="supporter_type"]')];
    const updateSupporterType = () => {
      const isOrganization = supporterTypes.find(input => input.checked)?.value === "organization";
      organizationField.hidden = !isOrganization;
      organizationField.querySelector("input").required = isOrganization;
    };
    supporterTypes.forEach(input => input.addEventListener("change", updateSupporterType));
    updateSupporterType();
  }
  const projectTools = document.querySelector("[data-project-tools]");
  if (projectTools) {
    const title = projectTools.dataset.projectTitle;
    const projectUrl = projectTools.dataset.projectUrl;
    const badgeElements = [...projectTools.querySelectorAll("[data-certificate-badge]")];
    const officialLogoElement = projectTools.querySelector(".official-certificate-logo img");
    const escapeMarkup = value => value.replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
    const slug = (title || "ai-use-declared-certificate").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "ai-use-declared-certificate";
    const loadImage = src => new Promise((resolve, reject) => {
      const image = new Image(); image.onload = () => resolve(image); image.onerror = reject; image.src = src;
    });
    async function renderCertificateCanvas() {
      const [officialLogo, ...images] = await Promise.all([
        loadImage(officialLogoElement.currentSrc || officialLogoElement.src),
        ...badgeElements.map(element => loadImage(element.currentSrc || element.src)),
      ]);
      const width = 1200, pad = 80, gap = 22, primaryWidth = width - pad * 2, qualifierWidth = (primaryWidth - gap) / 2;
      const primaryHeight = primaryWidth * images[0].naturalHeight / images[0].naturalWidth;
      const qualifierHeights = images.slice(1).map(image => qualifierWidth * image.naturalHeight / image.naturalWidth);
      const rows = Math.ceil(qualifierHeights.length / 2);
      let badgesHeight = primaryHeight + (rows ? gap : 0);
      for (let row = 0; row < rows; row++) badgesHeight += Math.max(...qualifierHeights.slice(row * 2, row * 2 + 2)) + (row < rows - 1 ? gap : 0);
      const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = Math.ceil(410 + badgesHeight + 145);
      const context = canvas.getContext("2d");
      const certificate = projectTools.querySelector("[data-project-certificate]");
      const cardBackground = certificate.dataset.cardBackground || "light";
      const cardAccent = certificate.dataset.cardAccent || "#f7836a";
      const foreground = cardBackground === "dark" ? "#ffffff" : "#0d0e37";
      const mutedForeground = cardBackground === "dark" ? "#c4c4d2" : "#66677d";
      if (cardBackground !== "transparent") { context.fillStyle = cardBackground === "dark" ? "#0d0e37" : "#ffffff"; context.fillRect(0, 0, canvas.width, canvas.height); }
      context.strokeStyle = "#d6d6dc"; context.lineWidth = 2; context.strokeRect(18, 18, width - 36, canvas.height - 36);
      context.save(); context.beginPath(); context.arc(pad + 18, 75, 18, 0, Math.PI * 2); context.clip();
      context.drawImage(officialLogo, 70, 70, 1115, 1115, pad, 57, 36, 36); context.restore();
      context.textAlign = "left"; context.fillStyle = foreground; context.font = "bold 15px Arial"; context.fillText("AI USE: DECLARED · BY SELECTORA", pad + 52, 81);
      context.fillStyle = cardAccent; context.beginPath(); context.arc(width - pad - 18, 75, 18, 0, Math.PI * 2); context.fill();
      context.fillStyle = "#0d0e37"; context.font = "bold 18px Arial"; context.textAlign = "center"; context.fillText("✓", width - pad - 18, 82);
      context.strokeStyle = "#d6d6dc"; context.beginPath(); context.moveTo(pad, 115); context.lineTo(width - pad, 115); context.stroke();
      context.textAlign = "left"; context.fillStyle = foreground; context.font = "bold 48px Arial"; context.fillText(title.slice(0, 42), pad, 180);
      context.fillStyle = mutedForeground; context.font = "22px Arial"; context.fillText(projectUrl.slice(0, 78), pad, 220);
      context.fillStyle = foreground; context.font = "bold 30px Arial"; context.fillText("This project discloses its use of AI as:", pad, 285);
      let y = 325; context.drawImage(images[0], pad, y, primaryWidth, primaryHeight); y += primaryHeight + gap;
      images.slice(1).forEach((image, index) => {
        const col = index % 2, x = pad + col * (qualifierWidth + gap), height = qualifierHeights[index];
        context.drawImage(image, x, y, qualifierWidth, height);
        if (col === 1 || index === images.length - 2) y += Math.max(...qualifierHeights.slice(Math.floor(index / 2) * 2, Math.floor(index / 2) * 2 + 2)) + gap;
      });
      const footerY = canvas.height - 58; context.strokeStyle = "#d6d6dc"; context.beginPath(); context.moveTo(pad, footerY - 26); context.lineTo(width - pad, footerY - 26); context.stroke();
      context.fillStyle = mutedForeground; context.font = "14px Arial"; context.fillText("AI USE: DECLARED · BY SELECTORA", pad, footerY);
      context.textAlign = "right"; context.fillText(window.location.href, width - pad, footerY);
      context.textAlign = "left"; context.fillStyle = cardBackground === "dark" ? "#ffffff" : "#0d0e37"; context.font = "bold 16px Arial"; context.fillText("What does this mean? Explore AI USE: DECLARED → ai.selectora.cc/badges/", pad, footerY + 35);
      return canvas;
    }
    const download = (href, filename) => { const link = document.createElement("a"); link.href = href; link.download = filename; link.click(); };
    projectTools.querySelector("[data-download-png]").addEventListener("click", async () => download((await renderCertificateCanvas()).toDataURL("image/png"), `${slug}-ai-use-declared.png`));
    projectTools.querySelector("[data-download-svg]").addEventListener("click", async () => {
      const canvas = await renderCertificateCanvas();
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${canvas.width} ${canvas.height}" role="img" aria-label="AI use disclosure certificate for ${escapeMarkup(title)}"><image width="${canvas.width}" height="${canvas.height}" href="${canvas.toDataURL("image/png")}"/></svg>`;
      download(URL.createObjectURL(new Blob([svg], {type: "image/svg+xml"})), `${slug}-ai-use-declared.svg`);
    });
    projectTools.querySelector("[data-download-pdf]").addEventListener("click", () => { document.body.classList.add("printing-registered-certificate"); window.print(); });
    window.addEventListener("afterprint", () => document.body.classList.remove("printing-registered-certificate"));
    const embed = projectTools.querySelector("[data-project-embed]");
    const disclosurePath = projectTools.dataset.disclosureUrl;
    const disclosureUrl = `https://ai.selectora.cc${disclosurePath}`;
    const imageHtml = badgeElements.map(element => {
      const path = new URL(element.src, window.location.origin).pathname.replace(/\.(png|svg)$/i, ".svg");
      return `      <img src="https://ai.selectora.cc${path}" alt="${escapeMarkup(element.dataset.label)} disclosure badge" loading="lazy">`;
    }).join("\n");
    embed.value = `<div class="aiud-widget">
  <style>
    .aiud-widget{position:relative;display:inline-block;font:14px/1.4 system-ui,sans-serif;color:#0d0e37}
    .aiud-trigger{display:flex;align-items:center;gap:9px;width:max-content;max-width:100%;padding:7px 10px 7px 7px;border:1px solid #d5d5dc;border-radius:8px;background:#fff;color:#0d0e37;text-decoration:none;box-shadow:0 4px 12px #0d0e3712}
    .aiud-logo{position:relative;width:42px;height:42px;flex:0 0 42px;overflow:hidden;border-radius:50%}.aiud-logo img{position:absolute;width:112.6%;height:112.6%;left:-6.3%;top:-6.3%;max-width:none}
    .aiud-label{font-weight:800;letter-spacing:.03em}.aiud-label small{display:block;color:#66677d;font-size:10px;font-weight:600;letter-spacing:0}
    .aiud-details{position:absolute;z-index:2147483647;left:0;bottom:calc(100% + 9px);visibility:hidden;opacity:0;transform:translateY(5px);width:min(370px,90vw);padding:15px;border:1px solid #d5d5dc;border-radius:11px;background:#fff;box-shadow:0 18px 45px #0d0e3728;transition:.18s ease;pointer-events:none}
    .aiud-widget:hover .aiud-details,.aiud-widget:focus-within .aiud-details{visibility:visible;opacity:1;transform:none;pointer-events:auto}
    .aiud-details p{margin:0 0 10px}.aiud-badges{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}.aiud-badges img{display:block;width:100%;height:auto;border-radius:5px}.aiud-badges img:first-child{grid-column:1/-1}.aiud-details>a{display:inline-block;margin-top:10px;color:#0d0e37;font-weight:750;text-underline-offset:3px}.aiud-details .aiud-meaning{display:block;padding-top:9px;border-top:1px solid #ddd;font-size:11px}
  </style>
  <a class="aiud-trigger" href="${disclosureUrl}" target="aiud_disclosure" aria-describedby="aiud-details-${slug}" onclick="window.open(this.href,'aiud_disclosure','popup=yes,width=680,height=760,resizable=yes,scrollbars=yes');return false;">
    <span class="aiud-logo"><img src="https://ai.selectora.cc/static/images/ai-use-declared-logo.png" alt=""></span>
    <span class="aiud-label">AI USE: DECLARED<small>Hover to see how AI was used</small></span>
  </a>
  <div class="aiud-details" id="aiud-details-${slug}" role="tooltip">
    <p><strong>${escapeMarkup(title)}</strong><br>This project discloses its use of AI as:</p>
    <div class="aiud-badges">
${imageHtml}
    </div>
    <a href="${disclosureUrl}" target="aiud_disclosure">View registered disclosure →</a>
    <a class="aiud-meaning" href="https://ai.selectora.cc/badges/" target="_blank">What does this mean? Explore AI USE: DECLARED →</a>
  </div>
</div>`;
    const demoDialog = projectTools.querySelector("[data-embed-demo]");
    const demoFrame = projectTools.querySelector("[data-embed-demo-frame]");
    projectTools.querySelector("[data-preview-project-embed]").addEventListener("click", () => {
      demoFrame.srcdoc = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{min-height:100%;margin:0}body{display:flex;align-items:flex-end;justify-content:center;padding:230px 24px 45px;box-sizing:border-box;background:#f7f5ef}</style></head><body>${embed.value}</body></html>`;
      demoDialog.showModal();
    });
    projectTools.querySelector("[data-close-embed-demo]").addEventListener("click", () => demoDialog.close());
    demoDialog.addEventListener("click", event => {
      if (event.target === demoDialog) demoDialog.close();
    });
    projectTools.querySelector("[data-copy-project-embed]").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(embed.value); } catch (_) { embed.select(); document.execCommand("copy"); }
      projectTools.querySelector("[data-project-copy-status]").textContent = "Copied.";
    });
  }
  const story = document.querySelector(".badge-story");
  if (story) {
    const images = [...story.querySelectorAll("img")];
    const ready = images.map(image => {
      if (image.complete) return image.decode?.().catch(() => {}) || Promise.resolve();
      return new Promise(resolve => {
        image.addEventListener("load", resolve, {once: true});
        image.addEventListener("error", resolve, {once: true});
      });
    });
    Promise.all(ready).then(() => requestAnimationFrame(() => story.classList.add("is-ready")));
  }
  const maker = document.querySelector("[data-certificate-maker]");
  if (maker) {
    const primaryInputs = [...maker.querySelectorAll('input[name="maker_primary"]')];
    const qualifierInputs = [...maker.querySelectorAll('input[name="maker_qualifier"]')];
    const badgeArea = maker.querySelector("[data-maker-badges]");
    const note = maker.querySelector("[data-maker-note]");
    const titleInput = maker.querySelector("[data-maker-title]");
    const urlInput = maker.querySelector("[data-maker-url]");
    const certificateTitle = maker.querySelector("[data-certificate-title]");
    const certificateUrl = maker.querySelector("[data-certificate-url]");
    const embedFormat = maker.querySelector("[data-embed-format]");
    const embedCode = maker.querySelector("[data-embed-code]");
    const copyButton = maker.querySelector("[data-copy-embed]");
    const copyStatus = maker.querySelector("[data-copy-status]");
    const makerPreview = maker.querySelector("[data-maker-preview]");
    const escapeHtml = value => value.replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
    function updateMaker() {
      const primary = primaryInputs.find(input => input.checked);
      const restricted = ["NO AI USED", "NO GENERATIVE AI"].includes(primary?.value);
      qualifierInputs.forEach(input => {
        if (input.value === "HUMAN-REVIEWED") return;
        input.disabled = restricted;
        if (restricted) input.checked = false;
        input.closest("label")?.classList.toggle("is-disabled", restricted);
      });
      note.hidden = !restricted;
      badgeArea.replaceChildren();
      const selected = [primary, ...qualifierInputs.filter(input => input.checked)].filter(Boolean);
      selected.forEach((input, index) => {
        const image = new Image();
        image.src = input.dataset.src;
        image.alt = `${input.value} disclosure badge`;
        image.className = index === 0 ? "maker-primary" : "maker-qualifier";
        badgeArea.append(image);
      });
      const title = titleInput.value.trim() || "This project";
      const projectUrl = urlInput.value.trim();
      certificateTitle.textContent = title;
      certificateUrl.textContent = projectUrl;
      certificateUrl.href = projectUrl || "#";
      certificateUrl.hidden = !projectUrl;
      const format = embedFormat.value;
      const layout = makerPreview.dataset.cardLayout || "standard";
      const background = makerPreview.dataset.cardBackground || "light";
      const accent = makerPreview.dataset.cardAccent || "#f7836a";
      const backgroundColor = background === "transparent" ? "transparent" : background === "dark" ? "#0d0e37" : "#ffffff";
      const textColor = background === "dark" ? "#ffffff" : "#0d0e37";
      const imageHtml = selected.map(input => {
        const localPath = new URL(input.dataset.src, window.location.origin).pathname.replace(/\.(png|svg)$/i, `.${format}`);
        const remoteSrc = `https://ai.selectora.cc${localPath}`;
        return `  <img src="${remoteSrc}" alt="${escapeHtml(input.value)}: AI use disclosure badge" loading="lazy">`;
      }).join("\n");
      const wrapperTag = projectUrl ? `a href="${escapeHtml(projectUrl)}"` : "div";
      const closingTag = projectUrl ? "a" : "div";
      const layoutCss = layout === "horizontal" ? "display:grid;grid-template-columns:minmax(150px,.7fr) minmax(260px,1.3fr);gap:8px 14px;align-items:start" : layout === "minimal" ? "max-width:420px;padding:10px" : "max-width:680px;padding:18px";
      embedCode.value = `<div class="ai-use-declared" style="${layoutCss};box-sizing:border-box;border:1px solid ${accent};border-radius:10px;background:${backgroundColor};color:${textColor};font:14px/1.4 system-ui,sans-serif" aria-label="AI use disclosure for ${escapeHtml(title)}">\n  <p style="margin:0 0 8px"><strong>${escapeHtml(title)}</strong> discloses its use of AI as:</p>\n  <${wrapperTag} style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;color:inherit;text-decoration:none">\n${imageHtml}\n  </${closingTag}>\n  <a href="https://ai.selectora.cc/badges/" style="grid-column:1/-1;margin-top:8px;padding-top:8px;border-top:1px solid ${accent};color:inherit;font-size:11px;font-weight:700">What does this mean? Explore AI USE: DECLARED →</a>\n</div>`;
    }
    [...primaryInputs, ...qualifierInputs, embedFormat].forEach(input => input.addEventListener("change", updateMaker));
    [titleInput, urlInput].forEach(input => input.addEventListener("input", updateMaker));
    makerPreview.addEventListener("cardstylechange", updateMaker);
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(embedCode.value);
        copyStatus.textContent = "Copied.";
      } catch (_) {
        embedCode.select();
        document.execCommand("copy");
        copyStatus.textContent = "Copied.";
      }
      setTimeout(() => copyStatus.textContent = "", 1800);
    });
    updateMaker();
  }
  const form = document.querySelector("[data-badge-form]");
  if (!form) return;
  const primaryInputs = [...form.querySelectorAll('input[name="primary_badge"]')];
  const qualifierInputs = [...form.querySelectorAll('input[name="qualifiers"]')];
  const note = form.querySelector("[data-compatibility]");
  function updateCompatibility() {
    const primary = primaryInputs.find(input => input.checked)?.value;
    const restrict = primary === "no-ai-used" || primary === "no-generative-ai";
    qualifierInputs.forEach(input => {
      if (input.value === "human-reviewed") return;
      input.disabled = restrict;
      if (restrict) input.checked = false;
      input.closest(".badge-option")?.classList.toggle("is-disabled", restrict);
    });
    if (note) note.hidden = !restrict;
  }
  primaryInputs.forEach(input => input.addEventListener("change", updateCompatibility));
  updateCompatibility();
});

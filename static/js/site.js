document.addEventListener("DOMContentLoaded", () => {
  const projectTools = document.querySelector("[data-project-tools]");
  if (projectTools) {
    const title = projectTools.dataset.projectTitle;
    const projectUrl = projectTools.dataset.projectUrl;
    const badgeElements = [...projectTools.querySelectorAll("[data-certificate-badge]")];
    const escapeMarkup = value => value.replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
    const slug = (title || "ai-use-declared-certificate").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "ai-use-declared-certificate";
    const loadImage = src => new Promise((resolve, reject) => {
      const image = new Image(); image.onload = () => resolve(image); image.onerror = reject; image.src = src;
    });
    async function renderCertificateCanvas() {
      const images = await Promise.all(badgeElements.map(element => loadImage(element.currentSrc || element.src)));
      const width = 1200, pad = 80, gap = 22, primaryWidth = width - pad * 2, qualifierWidth = (primaryWidth - gap) / 2;
      const primaryHeight = primaryWidth * images[0].naturalHeight / images[0].naturalWidth;
      const qualifierHeights = images.slice(1).map(image => qualifierWidth * image.naturalHeight / image.naturalWidth);
      const rows = Math.ceil(qualifierHeights.length / 2);
      let badgesHeight = primaryHeight + (rows ? gap : 0);
      for (let row = 0; row < rows; row++) badgesHeight += Math.max(...qualifierHeights.slice(row * 2, row * 2 + 2)) + (row < rows - 1 ? gap : 0);
      const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = Math.ceil(410 + badgesHeight + 105);
      const context = canvas.getContext("2d");
      context.fillStyle = "#ffffff"; context.fillRect(0, 0, canvas.width, canvas.height);
      context.strokeStyle = "#d6d6dc"; context.lineWidth = 2; context.strokeRect(18, 18, width - 36, canvas.height - 36);
      context.fillStyle = "#0d0e37"; context.beginPath(); context.arc(pad + 18, 75, 18, 0, Math.PI * 2); context.fill();
      context.fillStyle = "#ffffff"; context.font = "bold 14px Arial"; context.textAlign = "center"; context.fillText("ai", pad + 18, 80);
      context.textAlign = "left"; context.fillStyle = "#0d0e37"; context.font = "bold 15px Arial"; context.fillText("AI USE: DECLARED · BY SELECTORA", pad + 52, 81);
      context.fillStyle = "#f7836a"; context.beginPath(); context.arc(width - pad - 18, 75, 18, 0, Math.PI * 2); context.fill();
      context.fillStyle = "#0d0e37"; context.font = "bold 18px Arial"; context.textAlign = "center"; context.fillText("✓", width - pad - 18, 82);
      context.strokeStyle = "#d6d6dc"; context.beginPath(); context.moveTo(pad, 115); context.lineTo(width - pad, 115); context.stroke();
      context.textAlign = "left"; context.fillStyle = "#0d0e37"; context.font = "bold 48px Arial"; context.fillText(title.slice(0, 42), pad, 180);
      context.fillStyle = "#66677d"; context.font = "22px Arial"; context.fillText(projectUrl.slice(0, 78), pad, 220);
      context.fillStyle = "#0d0e37"; context.font = "bold 30px Arial"; context.fillText("This project discloses its use of AI as:", pad, 285);
      let y = 325; context.drawImage(images[0], pad, y, primaryWidth, primaryHeight); y += primaryHeight + gap;
      images.slice(1).forEach((image, index) => {
        const col = index % 2, x = pad + col * (qualifierWidth + gap), height = qualifierHeights[index];
        context.drawImage(image, x, y, qualifierWidth, height);
        if (col === 1 || index === images.length - 2) y += Math.max(...qualifierHeights.slice(Math.floor(index / 2) * 2, Math.floor(index / 2) * 2 + 2)) + gap;
      });
      const footerY = canvas.height - 58; context.strokeStyle = "#d6d6dc"; context.beginPath(); context.moveTo(pad, footerY - 26); context.lineTo(width - pad, footerY - 26); context.stroke();
      context.fillStyle = "#66677d"; context.font = "14px Arial"; context.fillText("AI USE: DECLARED · BY SELECTORA", pad, footerY);
      context.textAlign = "right"; context.fillText(window.location.href, width - pad, footerY);
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
    const imageHtml = badgeElements.map(element => {
      const path = new URL(element.src, window.location.origin).pathname.replace(/\.(png|svg)$/i, ".svg");
      return `  <img src="https://ai.selectora.cc${path}" alt="${element.dataset.label} disclosure badge" loading="lazy">`;
    }).join("\n");
    embed.value = `<a class="ai-use-declared-registered" href="${window.location.href}">\n  <p><strong>${escapeMarkup(title)}</strong> discloses its use of AI as:</p>\n${imageHtml}\n</a>`;
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
      const imageHtml = selected.map(input => {
        const localPath = new URL(input.dataset.src, window.location.origin).pathname.replace(/\.(png|svg)$/i, `.${format}`);
        const remoteSrc = `https://ai.selectora.cc${localPath}`;
        return `  <img src="${remoteSrc}" alt="${escapeHtml(input.value)}: AI use disclosure badge" loading="lazy">`;
      }).join("\n");
      const wrapperTag = projectUrl ? `a href="${escapeHtml(projectUrl)}"` : "div";
      const closingTag = projectUrl ? "a" : "div";
      embedCode.value = `<${wrapperTag} class="ai-use-declared" aria-label="AI use disclosure for ${escapeHtml(title)}">\n  <p><strong>${escapeHtml(title)}</strong> discloses its use of AI as:</p>\n${imageHtml}\n</${closingTag}>`;
    }
    [...primaryInputs, ...qualifierInputs, embedFormat].forEach(input => input.addEventListener("change", updateMaker));
    [titleInput, urlInput].forEach(input => input.addEventListener("input", updateMaker));
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

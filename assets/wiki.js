(() => {
  const figures = document.querySelectorAll("figure");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("play");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.2 });
    figures.forEach((figure) => observer.observe(figure));
  } else {
    figures.forEach((figure) => figure.classList.add("play"));
  }

  const recentItems = document.querySelectorAll(".recent-item");
  recentItems.forEach((item) => {
    item.addEventListener("toggle", () => {
      if (!item.open) return;
      recentItems.forEach((other) => {
        if (other !== item) other.open = false;
      });
    });
  });

  const cards = [...document.querySelectorAll(".note-card")];
  const mapLinks = [...document.querySelectorAll(".reading-map a[href^='#']")];
  const focusButton = document.querySelector("[data-reading-action='focus']");
  let activeCard = cards[0] || null;
  const stateKey = `reading-view:${window.location.pathname}`;
  let savedState = {};
  try {
    savedState = JSON.parse(window.sessionStorage.getItem(stateKey) || "{}");
  } catch {
    savedState = {};
  }

  const saveState = () => {
    try {
      window.sessionStorage.setItem(stateKey, JSON.stringify({
        collapsed: cards.filter((card) => card.classList.contains("is-collapsed")).map((card) => card.id),
        focus: document.body.classList.contains("focus-reading"),
      }));
    } catch {
      // Reading controls remain functional when storage is unavailable.
    }
  };

  const setCollapsed = (card, collapsed) => {
    const toggle = card.querySelector(".section-toggle");
    card.classList.toggle("is-collapsed", collapsed);
    if (!toggle) return;
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.textContent = collapsed ? "展开" : "收起";
    toggle.setAttribute("aria-label", collapsed ? "展开本节" : "折叠本节");
    saveState();
  };

  cards.forEach((card) => {
    if (savedState.collapsed?.includes(card.id)) setCollapsed(card, true);
    card.querySelector(".section-toggle")?.addEventListener("click", () => {
      setCollapsed(card, !card.classList.contains("is-collapsed"));
    });
    card.querySelector(".section-copy")?.addEventListener("click", async (event) => {
      const button = event.currentTarget;
      const target = button.dataset.copySection;
      const url = new URL(window.location.href);
      url.hash = target;
      try {
        await navigator.clipboard.writeText(url.toString());
        button.textContent = "已复制";
        window.setTimeout(() => { button.textContent = "复制链接"; }, 1200);
      } catch {
        window.location.hash = target;
      }
    });
    [...card.querySelectorAll("h3")].forEach((heading) => {
      heading.dataset.headingTitle = heading.textContent;
      const isTranscriptGroup = document.body.classList.contains("session-page") && ["用户", "Codex"].includes(heading.dataset.headingTitle);
      const toggle = document.createElement("button"); toggle.type = "button"; toggle.className = "detail-toggle"; toggle.textContent = isTranscriptGroup ? "展开内容" : "收起细节"; toggle.setAttribute("aria-expanded", String(!isTranscriptGroup));
      const setDetailCollapsed = (collapsed) => {
        toggle.setAttribute("aria-expanded", String(!collapsed));
        toggle.textContent = collapsed ? (isTranscriptGroup ? "展开内容" : "展开细节") : (isTranscriptGroup ? "收起内容" : "收起细节");
        let sibling = heading.nextElementSibling; while (sibling && sibling.tagName !== "H3") { sibling.hidden = collapsed; sibling = sibling.nextElementSibling; }
      };
      toggle.addEventListener("click", () => {
        const collapsed = toggle.getAttribute("aria-expanded") === "true";
        setDetailCollapsed(collapsed);
      });
      heading.append(toggle);
      if (isTranscriptGroup) setDetailCollapsed(true);
    });
  });

  const setActiveCard = (card) => {
    if (!card) return;
    activeCard = card;
    cards.forEach((item) => item.classList.toggle("is-focused", item === card));
    mapLinks.forEach((link) => link.classList.toggle("is-active", link.hash === `#${card.id}`));
    const activeLink = mapLinks.find((link) => link.hash === `#${card.id}`);
    activeLink?.scrollIntoView({ block: "nearest" });
  };

  if (cards.length && "IntersectionObserver" in window) {
    const cardObserver = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) setActiveCard(visible.target);
    }, { rootMargin: "-18% 0px -58%", threshold: [0.05, 0.25, 0.5] });
    cards.forEach((card) => cardObserver.observe(card));
    const headingTargets = mapLinks.map((link) => document.querySelector(link.hash)).filter(Boolean);
    const headingObserver = new IntersectionObserver((entries) => {
      const active = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!active) return;
      mapLinks.forEach((link) => link.classList.toggle("is-active", link.hash === `#${active.target.id}`));
      active.target.closest(".note-card") && (activeCard = active.target.closest(".note-card"));
      document.dispatchEvent(new CustomEvent("reading:active", { detail: { blockId: active.target.id } }));
    }, { rootMargin: "-12% 0px -76%", threshold: 0 });
    headingTargets.forEach((heading) => headingObserver.observe(heading));
  }

  mapLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const target = document.querySelector(link.hash);
      const card = target?.closest(".note-card");
      if (card?.classList.contains("note-card")) {
        setCollapsed(card, false);
        setActiveCard(card);
      }
    });
  });

  document.querySelector("[data-reading-action='expand']")?.addEventListener("click", () => {
    cards.forEach((card) => setCollapsed(card, false));
  });
  document.querySelector("[data-reading-action='collapse']")?.addEventListener("click", () => {
    cards.forEach((card) => setCollapsed(card, true));
  });
  focusButton?.addEventListener("click", () => {
    const enabled = !document.body.classList.contains("focus-reading");
    document.body.classList.toggle("focus-reading", enabled);
    focusButton.setAttribute("aria-pressed", String(enabled));
    focusButton.textContent = enabled ? "退出聚焦" : "聚焦当前";
    setActiveCard(activeCard);
    saveState();
  });

  if (savedState.focus && focusButton) {
    document.body.classList.add("focus-reading");
    focusButton.setAttribute("aria-pressed", "true");
    focusButton.textContent = "退出聚焦";
  }

  const panels = {
    sessions: document.querySelector("#session-list-panel"),
    map: document.querySelector("#reading-map"),
    research: document.querySelector("#research-panel"),
  };
  const scrim = document.querySelector("[data-panel-scrim]");
  let panelTrigger = null;
  const closePanels = () => {
    Object.entries(panels).forEach(([name, panel]) => {
      panel?.classList.remove("is-open");
      panel?.setAttribute("aria-modal", "false");
      document.querySelector(`[data-panel-toggle='${name}']`)?.setAttribute("aria-expanded", "false");
    });
    if (scrim) scrim.hidden = true;
    panelTrigger?.focus(); panelTrigger = null;
  };
  const openPanel = (name) => {
    const panel = panels[name];
    if (!panel) return;
    const opening = !panel.classList.contains("is-open");
    closePanels();
    if (!opening) return;
    panelTrigger = document.activeElement;
    panel.classList.add("is-open");
    panel.setAttribute("aria-modal", "true");
    document.querySelector(`[data-panel-toggle='${name}']`)?.setAttribute("aria-expanded", "true");
    if (scrim) scrim.hidden = false;
    panel.querySelector(".panel-close")?.focus();
  };
  document.querySelectorAll("[data-panel-toggle]").forEach((button) => {
    button.addEventListener("click", () => openPanel(button.dataset.panelToggle));
  });
  document.querySelectorAll("[data-panel-close]").forEach((button) => {
    button.addEventListener("click", closePanels);
  });
  scrim?.addEventListener("click", closePanels);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closePanels();
    if (event.key === "Tab") {
      const panel = Object.values(panels).find((item) => item?.classList.contains("is-open"));
      if (!panel) return;
      const focusable = [...panel.querySelectorAll("button,a,input,select,textarea,[tabindex]:not([tabindex='-1'])")].filter((item) => !item.hidden);
      if (!focusable.length) return;
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  mapLinks.forEach((link) => link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 1099px)").matches) closePanels();
  }));

  const pageSlug = document.body.dataset.pageSlug;
  const toast = document.querySelector(".toast");
  const showToast = (message, error = false) => {
    if (!toast) return;
    toast.textContent = message; toast.hidden = false; toast.classList.toggle("is-error", error);
    window.clearTimeout(showToast.timer); showToast.timer = window.setTimeout(() => { toast.hidden = true; }, 2600);
  };
  if (pageSlug && cards.length) {
    let evidence = { claims: [] };
    try { evidence = JSON.parse(document.body.dataset.evidence || '{"claims":[]}'); } catch { evidence = { claims: [] }; }
    const evidenceList = document.querySelector(".evidence-list");
    const statusLabels = { verified: "已核验", located: "候选位置", unverified: "尚未核对", unavailable: "来源不可用", conflict: "存在冲突" };
    const claimLabels = { author: "作者陈述", experiment: "实验结果", analysis: "分析推断", user: "用户判断" };
    const renderEvidence = (blockId) => {
      if (!evidenceList) return;
      evidenceList.replaceChildren();
      let claims = evidence.claims.filter((claim) => claim.block_id === blockId);
      if (!claims.length) { const parentId = document.getElementById(blockId)?.closest(".note-card")?.id; claims = evidence.claims.filter((claim) => claim.block_id === parentId); }
      if (!claims.length) { const empty = document.createElement("p"); empty.textContent = "本节还没有结构化 claim。"; evidenceList.append(empty); return; }
      claims.forEach((claim) => {
        const item = document.createElement("article"); item.className = "evidence-item";
        const badge = document.createElement("span"); badge.className = `evidence-status status-${claim.verification_status}`; badge.textContent = statusLabels[claim.verification_status] || claim.verification_status;
        const kind = document.createElement("span"); kind.className = "claim-type"; kind.textContent = claimLabels[claim.claim_type] || claim.claim_type;
        const summary = document.createElement("p"); summary.textContent = claim.summary;
        item.append(badge, kind, summary);
        claim.anchors.forEach((anchor) => { const link = document.createElement("a"); link.href = anchor.source_url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = `${anchor.kind} · ${anchor.label}`; item.append(link); });
        evidenceList.append(item);
      });
    };
    renderEvidence(activeCard?.id);
    document.addEventListener("reading:active", (event) => renderEvidence(event.detail.blockId));
  }

  document.querySelectorAll("[data-panel-tab]").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("[data-panel-tab]").forEach((item) => item.setAttribute("aria-selected", String(item === tab)));
      document.querySelectorAll("[data-panel-view]").forEach((view) => { view.hidden = view.dataset.panelView !== tab.dataset.panelTab; });
    });
  });

  const modeButton = document.querySelector("[data-reading-mode]");
  const setReadingMode = (overview) => {
    document.body.classList.toggle("overview-mode", overview);
    modeButton?.setAttribute("aria-pressed", String(overview));
    if (modeButton) modeButton.textContent = overview ? "进入精读" : "概览";
    try { window.localStorage.setItem(`reading-mode:${pageSlug}`, overview ? "overview" : "deep"); } catch {}
  };
  if (modeButton) {
    setReadingMode(window.localStorage.getItem(`reading-mode:${pageSlug}`) === "overview");
    modeButton.addEventListener("click", () => setReadingMode(!document.body.classList.contains("overview-mode")));
  }

  const openDialog = (dialog) => { if (dialog?.showModal) dialog.showModal(); else dialog?.setAttribute("open", ""); };
  const searchDialog = document.querySelector("[data-search-dialog]");
  const searchInput = document.querySelector("[data-page-search]");
  const searchResults = document.querySelector(".search-results");
  const searchStatus = document.querySelector(".search-status");
  document.querySelector("[data-search-open]")?.addEventListener("click", () => { openDialog(searchDialog); searchInput?.focus(); });
  const runSearch = () => {
    if (!searchResults || !searchStatus) return;
    searchResults.replaceChildren();
    const query = searchInput.value.trim().toLocaleLowerCase();
    if (!query) { searchStatus.textContent = ""; return; }
    const matches = [];
    document.querySelectorAll(".note-card h2,.note-card h3,.note-card p,.note-card li").forEach((node) => {
      const text = node.textContent.trim(); const index = text.toLocaleLowerCase().indexOf(query);
      if (index >= 0) matches.push({ node, text, index });
    });
    searchStatus.textContent = `找到 ${matches.length} 处结果`;
    matches.slice(0, 80).forEach((match) => {
      const button = document.createElement("button"); button.type = "button"; button.className = "search-result";
      const heading = document.createElement("strong"); heading.textContent = match.node.closest(".note-card")?.querySelector("h2")?.textContent || "正文";
      const excerpt = document.createElement("span"); excerpt.textContent = match.text.slice(Math.max(0, match.index - 36), match.index + query.length + 72); button.append(heading, excerpt);
      button.addEventListener("click", () => { searchDialog.close(); match.node.closest(".note-card")?.classList.remove("is-collapsed"); match.node.scrollIntoView({ block: "center" }); match.node.classList.add("search-hit"); window.setTimeout(() => match.node.classList.remove("search-hit"), 1800); });
      searchResults.append(button);
    });
  };
  searchInput?.addEventListener("input", runSearch);

  const preferencesDialog = document.querySelector("[data-preferences-dialog]");
  const prefControls = { size: document.querySelector("[data-pref-size]"), leading: document.querySelector("[data-pref-leading]"), width: document.querySelector("[data-pref-width]"), sans: document.querySelector("[data-pref-sans]") };
  const applyPreferences = (prefs) => {
    document.documentElement.style.setProperty("--reader-size", `${prefs.size}px`);
    document.documentElement.style.setProperty("--reader-leading", String(prefs.leading / 100));
    document.documentElement.style.setProperty("--reader-width", `${prefs.width}px`);
    document.body.classList.toggle("sans-reading", prefs.sans);
    Object.entries(prefControls).forEach(([key, control]) => { if (control) key === "sans" ? control.checked = prefs[key] : control.value = prefs[key]; });
  };
  const defaultPrefs = { size: 18, leading: 182, width: 760, sans: false };
  let prefs = defaultPrefs;
  try { prefs = { ...defaultPrefs, ...JSON.parse(window.localStorage.getItem("reader-preferences:v1") || "{}") }; } catch {}
  applyPreferences(prefs);
  document.querySelector("[data-preferences-open]")?.addEventListener("click", () => openDialog(preferencesDialog));
  Object.entries(prefControls).forEach(([key, control]) => control?.addEventListener("input", () => {
    prefs = { size: Number(prefControls.size.value), leading: Number(prefControls.leading.value), width: Number(prefControls.width.value), sans: prefControls.sans.checked };
    applyPreferences(prefs); try { window.localStorage.setItem("reader-preferences:v1", JSON.stringify(prefs)); } catch { showToast("阅读偏好无法保存。", true); }
  }));
  document.querySelector("[data-pref-reset]")?.addEventListener("click", () => { prefs = { ...defaultPrefs }; applyPreferences(prefs); try { window.localStorage.removeItem("reader-preferences:v1"); } catch {} });

  const termPopover = document.querySelector("[data-term-popover]");
  const termsList = document.querySelector(".terms-list");
  document.querySelectorAll(".term-link").forEach((link) => {
    if (termsList && !termsList.querySelector(`[href='${link.getAttribute("href")}']`)) { const item = link.cloneNode(true); item.textContent = `${link.dataset.termTitle} — ${link.dataset.termSummary}`; termsList.append(item); }
    link.addEventListener("click", (event) => {
      if (!termPopover) return;
      event.preventDefault(); termPopover.replaceChildren();
      const title = document.createElement("strong"); title.textContent = link.dataset.termTitle;
      const summary = document.createElement("p"); summary.textContent = link.dataset.termSummary;
      const full = document.createElement("a"); full.href = link.href; full.textContent = "打开完整概念页 →";
      termPopover.append(title, summary, full); termPopover.hidden = false;
      const rect = link.getBoundingClientRect(); termPopover.style.left = `${Math.min(rect.left, window.innerWidth - 340)}px`; termPopover.style.top = `${rect.bottom + 8}px`;
    });
  });
  document.addEventListener("pointerdown", (event) => { if (termPopover && !termPopover.hidden && !termPopover.contains(event.target) && !event.target.closest?.(".term-link")) termPopover.hidden = true; });

  const selectionTools = document.querySelector("[data-selection-tools]");
  let selectedText = "";
  document.addEventListener("selectionchange", () => {
    const selection = window.getSelection(); const text = selection?.toString().trim(); const node = selection?.anchorNode?.parentElement?.closest?.(".note-card");
    if (!selectionTools || !text || !node || text.length > 1000) { if (selectionTools) selectionTools.hidden = true; return; }
    selectedText = text; const rect = selection.getRangeAt(0).getBoundingClientRect(); selectionTools.hidden = false; selectionTools.style.left = `${Math.max(8, rect.left)}px`; selectionTools.style.top = `${Math.max(64, rect.top - 46)}px`;
  });
  document.querySelector("[data-selection-copy]")?.addEventListener("click", async () => { try { await navigator.clipboard.writeText(selectedText); showToast("选文已复制"); } catch { showToast("复制失败", true); } selectionTools.hidden = true; });
  const decorateFormulas = () => document.querySelectorAll("mjx-container[display='true']").forEach((formula, index) => {
    if (formula.parentElement?.classList.contains("formula-block")) return;
    const wrapper = document.createElement("div"); wrapper.className = "formula-block"; wrapper.dataset.formula = String(index + 1); formula.before(wrapper); wrapper.append(formula);
    const button = document.createElement("button"); button.type = "button"; button.textContent = "复制公式"; button.addEventListener("click", async () => { try { await navigator.clipboard.writeText(formula.textContent.trim()); button.textContent = "已复制"; window.setTimeout(() => button.textContent = "复制公式", 1200); } catch { showToast("公式复制失败", true); } }); wrapper.prepend(button);
  });
  if (window.MathJax?.startup?.promise) window.MathJax.startup.promise.then(decorateFormulas); else window.addEventListener("load", decorateFormulas);

  const updateOnlineState = () => { const badge = document.querySelector(".offline-badge"); if (badge) badge.hidden = navigator.onLine; };
  updateOnlineState(); window.addEventListener("online", updateOnlineState); window.addEventListener("offline", updateOnlineState);
  document.addEventListener("keydown", (event) => { if (event.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName || "")) { event.preventDefault(); openDialog(searchDialog); searchInput?.focus(); } });

  if (pageSlug) {
    const positionKey = `reading-position:${pageSlug}`;
    const savedPosition = Number(window.localStorage.getItem(positionKey) || 0);
    if (!window.location.hash && savedPosition > 0) window.requestAnimationFrame(() => window.scrollTo({ top: savedPosition }));
    let positionTimer; window.addEventListener("scroll", () => { window.clearTimeout(positionTimer); positionTimer = window.setTimeout(() => { try { window.localStorage.setItem(positionKey, String(window.scrollY)); } catch {} }, 180); }, { passive: true });
  }

  const progress = document.querySelector(".reading-progress span");
  const article = document.querySelector(".block-article");
  if (progress && article) {
    const updateProgress = () => {
      const start = article.offsetTop;
      const distance = Math.max(article.offsetHeight - window.innerHeight * 0.55, 1);
      const value = Math.min(1, Math.max(0, (window.scrollY - start + window.innerHeight * 0.3) / distance));
      progress.style.transform = `scaleX(${value})`;
    };
    updateProgress();
    document.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
  }
})();

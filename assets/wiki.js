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
  const stateKey = `reading-state:${window.location.pathname}`;
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
    map: document.querySelector("#reading-map"),
    research: document.querySelector("#research-panel"),
  };
  const scrim = document.querySelector("[data-panel-scrim]");
  const closePanels = () => {
    Object.entries(panels).forEach(([name, panel]) => {
      panel?.classList.remove("is-open");
      document.querySelector(`[data-panel-toggle='${name}']`)?.setAttribute("aria-expanded", "false");
    });
    if (scrim) scrim.hidden = true;
  };
  const openPanel = (name) => {
    const panel = panels[name];
    if (!panel) return;
    const opening = !panel.classList.contains("is-open");
    closePanels();
    if (!opening) return;
    panel.classList.add("is-open");
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
  });
  mapLinks.forEach((link) => link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 1099px)").matches) closePanels();
  }));

  const pageSlug = document.body.dataset.pageSlug;
  const workspaceStore = {
    key: "research-workspace:v1",
    read() {
      try { return JSON.parse(window.localStorage.getItem(this.key) || '{"version":1,"pages":{}}'); }
      catch { return { version: 1, pages: {} }; }
    },
    write(data) {
      try { window.localStorage.setItem(this.key, JSON.stringify(data)); return true; }
      catch { return false; }
    },
    page(slug) {
      const data = this.read();
      return data.pages[slug] || { readingState: "unread", notes: [] };
    },
    updatePage(slug, value) {
      const data = this.read();
      data.pages[slug] = value;
      return this.write(data);
    },
  };

  if (pageSlug && cards.length) {
    const form = document.querySelector(".note-form");
    const blockSelect = form?.elements.block;
    const notesList = document.querySelector(".notes-list");
    const readingState = document.querySelector("[data-reading-state]");
    let pageData = workspaceStore.page(pageSlug);
    let editingId = null;
    const categoryLabels = { understanding: "个人理解", question: "研究问题", critique: "批判性分析", reproduction: "复现记录" };

    cards.forEach((card) => {
      const option = document.createElement("option");
      option.value = card.id;
      option.textContent = card.querySelector("h2")?.textContent || card.id;
      blockSelect?.append(option);
    });
    if (readingState) {
      readingState.value = pageData.readingState || "unread";
      readingState.addEventListener("change", () => {
        pageData.readingState = readingState.value;
        workspaceStore.updatePage(pageSlug, pageData);
      });
    }

    const renderNotes = () => {
      if (!notesList) return;
      notesList.replaceChildren();
      if (!pageData.notes?.length) {
        const empty = document.createElement("p"); empty.className = "notes-empty"; empty.textContent = "还没有笔记。"; notesList.append(empty); return;
      }
      pageData.notes.forEach((note) => {
        const item = document.createElement("article"); item.className = "saved-note";
        const meta = document.createElement("div"); meta.className = "saved-note-meta";
        const target = document.getElementById(note.blockId);
        meta.textContent = `${categoryLabels[note.category] || note.category} · ${target?.querySelector("h2")?.textContent || note.blockId}`;
        const content = document.createElement("p"); content.textContent = note.content;
        const actions = document.createElement("div"); actions.className = "saved-note-actions";
        const edit = document.createElement("button"); edit.type = "button"; edit.textContent = "编辑";
        edit.addEventListener("click", () => { editingId = note.id; form.elements.category.value = note.category; form.elements.block.value = note.blockId; form.elements.content.value = note.content; form.elements.content.focus(); });
        const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "删除";
        remove.addEventListener("click", () => { pageData.notes = pageData.notes.filter((value) => value.id !== note.id); workspaceStore.updatePage(pageSlug, pageData); renderNotes(); });
        actions.append(edit, remove); item.append(meta, content, actions); notesList.append(item);
      });
    };

    form?.addEventListener("submit", (event) => {
      event.preventDefault();
      const content = form.elements.content.value.trim();
      if (!content) return;
      const note = { id: editingId || (crypto.randomUUID?.() || `note-${Date.now()}`), category: form.elements.category.value, blockId: form.elements.block.value, content, updatedAt: new Date().toISOString() };
      const index = pageData.notes.findIndex((value) => value.id === note.id);
      if (index >= 0) pageData.notes[index] = note; else pageData.notes.push(note);
      workspaceStore.updatePage(pageSlug, pageData); editingId = null; form.reset(); renderNotes();
    });
    document.querySelector("[data-notes-export]")?.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify({ version: 1, pageSlug, ...pageData }, null, 2)], { type: "application/json" });
      const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `${pageSlug}-notes.json`; link.click(); URL.revokeObjectURL(link.href);
    });
    document.querySelector("[data-notes-import]")?.addEventListener("change", async (event) => {
      const file = event.target.files?.[0]; if (!file) return;
      try {
        const imported = JSON.parse(await file.text());
        if (imported.version !== 1 || imported.pageSlug !== pageSlug || !Array.isArray(imported.notes)) throw new Error("invalid notes file");
        pageData = { readingState: imported.readingState || "unread", notes: imported.notes };
        workspaceStore.updatePage(pageSlug, pageData); if (readingState) readingState.value = pageData.readingState; renderNotes();
      } catch { window.alert("笔记文件格式或页面标识不匹配。"); }
      event.target.value = "";
    });
    renderNotes();

    let evidence = { claims: [] };
    try { evidence = JSON.parse(document.body.dataset.evidence || '{"claims":[]}'); } catch { evidence = { claims: [] }; }
    const evidenceList = document.querySelector(".evidence-list");
    const renderEvidence = (blockId) => {
      if (!evidenceList) return;
      evidenceList.replaceChildren();
      const claims = evidence.claims.filter((claim) => claim.block_id === blockId);
      if (!claims.length) { const empty = document.createElement("p"); empty.textContent = "本节还没有结构化 claim。"; evidenceList.append(empty); return; }
      claims.forEach((claim) => {
        const item = document.createElement("article"); item.className = "evidence-item";
        const badge = document.createElement("span"); badge.className = `evidence-status status-${claim.verification_status}`; badge.textContent = claim.verification_status;
        const kind = document.createElement("span"); kind.className = "claim-type"; kind.textContent = claim.claim_type;
        const summary = document.createElement("p"); summary.textContent = claim.summary;
        item.append(badge, kind, summary);
        claim.anchors.forEach((anchor) => { const link = document.createElement("a"); link.href = anchor.source_url; link.target = "_blank"; link.rel = "noreferrer"; link.textContent = `${anchor.kind} · ${anchor.label}`; item.append(link); });
        evidenceList.append(item);
      });
    };
    renderEvidence(activeCard?.id);
    cards.forEach((card) => new IntersectionObserver((entries) => { if (entries.some((entry) => entry.isIntersecting)) { if (blockSelect) blockSelect.value = card.id; renderEvidence(card.id); } }, { rootMargin: "-20% 0px -65%" }).observe(card));
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

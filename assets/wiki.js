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
  const mapLinks = [...document.querySelectorAll(".reading-map a[href^='#block-']")];
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
      const parentBlock = link.hash.match(/^#block-\d+/);
      const card = parentBlock ? document.querySelector(parentBlock[0]) : null;
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

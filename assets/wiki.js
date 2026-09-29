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
})();

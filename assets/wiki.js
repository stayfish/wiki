(() => {
  const figures = document.querySelectorAll("figure");
  if (!("IntersectionObserver" in window)) {
    figures.forEach((figure) => figure.classList.add("play"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("play");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.2 });
  figures.forEach((figure) => observer.observe(figure));
})();

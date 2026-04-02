document.querySelectorAll(".site-nav a, .button, .header-cta").forEach((link) => {
  link.addEventListener("click", () => {
    document.body.dataset.lastAction = link.getAttribute("href") || "";
  });
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.18,
  },
);

document.querySelectorAll(".panel, .timeline-step, .principle, .maturity-step").forEach((node) => {
  node.classList.add("reveal");
  observer.observe(node);
});

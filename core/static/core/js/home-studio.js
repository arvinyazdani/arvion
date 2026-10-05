(function () {
  "use strict";
  document.querySelectorAll("[data-home-showcase]").forEach((showcase) => {
    const choices = showcase.querySelector(".website-showcase-choices");
    if (!choices) return;
    choices.hidden = false;
    choices.querySelectorAll("[data-home-choice]").forEach((button) => {
      button.addEventListener("click", () => {
        showcase.querySelectorAll("[data-home-scene]").forEach((scene) => {
          scene.hidden = scene.dataset.homeScene !== button.dataset.homeChoice;
        });
        choices.querySelectorAll("[data-home-choice]").forEach((choice) => {
          choice.setAttribute("aria-pressed", String(choice === button));
        });
      });
    });
  });
  // Progressive enhancement: text and navigation never depend on animation.
  document.querySelectorAll("[data-home-journey]").forEach((journey) => {
    if (!("IntersectionObserver" in window)) return;
    const chapters = Array.from(journey.querySelectorAll("[data-home-chapter]"));
    const stage = journey.querySelector(".home-journey-stage");
    if (!stage) return;
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting);
      if (!visible.length) return;
      const current = visible.sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0].target;
      stage.querySelectorAll("[data-journey-art]").forEach((art) => {
        art.classList.toggle("is-active", art.dataset.journeyArt === current.dataset.homeChapter);
      });
      stage.querySelectorAll(".home-journey-dots i").forEach((dot, index) => {
        dot.classList.toggle("is-active", chapters[index] === current);
      });
    }, {rootMargin: "-15% 0px -25% 0px", threshold: [0, 0.25, 0.5]});
    chapters.forEach((chapter) => observer.observe(chapter));
  });
})();

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
})();

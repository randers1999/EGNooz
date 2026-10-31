(function () {
  const form = document.getElementById("review-form");
  if (!form) return;

  const publishBtn = document.getElementById("publish-btn");
  const note = document.getElementById("editor_note");

  function includedCount() {
    return form.querySelectorAll('input[name="included"]:checked').length;
  }

  function refreshState() {
    form.querySelectorAll(".item").forEach(function (item) {
      const box = item.querySelector('input[name="included"]');
      if (box) item.classList.toggle("item-off", !box.checked);
    });
    if (publishBtn) {
      const n = includedCount();
      publishBtn.textContent = "Publish " + n + " item" + (n === 1 ? "" : "s");
    }
  }

  async function saveDraft() {
    const data = new FormData(form);
    try {
      await fetch(form.getAttribute("data-save") || "/save", {
        method: "POST",
        body: data,
        headers: { "X-Requested-With": "fetch" },
        credentials: "same-origin",
      });
    } catch (err) {
      // Publish still submits the full form if autosave fails.
    }
  }

  form.setAttribute("data-save", form.querySelector("#save-btn").getAttribute("formaction") || "/save");
  form.addEventListener("change", function (event) {
    if (event.target && event.target.name === "included") {
      refreshState();
      saveDraft();
    }
  });
  if (note) {
    let timer;
    note.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(saveDraft, 400);
    });
  }
  if (publishBtn) {
    publishBtn.addEventListener("click", function (event) {
      const n = includedCount();
      const ok = window.confirm(
        "Publish " + n + " item" + (n === 1 ? "" : "s") +
          " to latest.json and email the prototype list (Tom only unless you added testers)? " +
          "This does not auto-send on a schedule — only this tap."
      );
      if (!ok) event.preventDefault();
    });
  }
  refreshState();
})();

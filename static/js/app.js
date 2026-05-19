(function () {
  const scrapeBtn = document.getElementById("scrape-btn");
  const modal = document.getElementById("scrape-modal");
  const scrapeConfirm = document.getElementById("scrape-confirm");
  const keywordInput = document.getElementById("scrape-keyword");
  const regionInput = document.getElementById("scrape-region");

  if (scrapeBtn && modal) {
    scrapeBtn.addEventListener("click", () => modal.classList.remove("hidden"));
    modal.querySelectorAll(".modal-cancel, .modal-backdrop").forEach((el) => {
      el.addEventListener("click", () => modal.classList.add("hidden"));
    });
  }

  if (scrapeConfirm) {
    scrapeConfirm.addEventListener("click", runScrape);
  }

  async function runScrape() {
    const keyword = keywordInput?.value || "AI startup";
    const region = regionInput?.value || "";
    scrapeConfirm.disabled = true;
    scrapeConfirm.textContent = "Scraping…";
    if (scrapeBtn) scrapeBtn.classList.add("loading");

    try {
      const resp = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, region }),
      });
      const data = await resp.json();
      modal?.classList.add("hidden");
      showToast(
        `Done in ${data.duration_ms}ms — ${data.unique_new} new, ${data.scraped} scraped`
      );
      setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
      showToast("Scrape failed. Check terminal logs.");
    } finally {
      scrapeConfirm.disabled = false;
      scrapeConfirm.textContent = "Start scraping";
      if (scrapeBtn) scrapeBtn.classList.remove("loading");
    }
  }

  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const view = btn.dataset.view;
      document.querySelectorAll(".view-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("grid-view")?.classList.toggle("hidden", view === "table");
      document.getElementById("table-view")?.classList.toggle("hidden", view !== "table");
    });
  });

  const alertForm = document.getElementById("alert-form");
  if (alertForm) {
    alertForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(alertForm);
      const resp = await fetch("/api/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: fd.get("email"),
          keyword: fd.get("keyword"),
        }),
      });
      const data = await resp.json();
      showToast(data.ok ? data.message : data.error || "Failed");
      if (data.ok) alertForm.reset();
    });
  }

  function showToast(message) {
    document.querySelector(".toast")?.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 5000);
  }
})();

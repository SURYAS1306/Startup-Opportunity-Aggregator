(function () {
  const scrapeBtn = document.getElementById("scrape-btn");
  const modal = document.getElementById("scrape-modal");
  const scrapeConfirm = document.getElementById("scrape-confirm");
  const keywordInput = document.getElementById("scrape-keyword");
  const regionInput = document.getElementById("scrape-region");
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menu-toggle");
  const toastRoot = document.getElementById("toast-root");

  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("is-open"));
  }

  if (scrapeBtn && modal) {
    scrapeBtn.addEventListener("click", () => {
      modal.classList.remove("hidden");
      sidebar?.classList.remove("is-open");
    });
    modal.querySelectorAll(".modal-cancel, .modal-backdrop").forEach((el) => {
      el.addEventListener("click", () => modal.classList.add("hidden"));
    });
  }

  if (scrapeConfirm) scrapeConfirm.addEventListener("click", runScrape);

  async function runScrape() {
    const keyword = keywordInput?.value || "AI startup";
    const region = regionInput?.value || "";
    scrapeConfirm.disabled = true;
    scrapeConfirm.textContent = "Running…";
    scrapeBtn?.classList.add("loading");

    try {
      const resp = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, region }),
      });
      const data = await resp.json();
      modal?.classList.add("hidden");
      toast(`Synced in ${(data.duration_ms / 1000).toFixed(1)}s — ${data.unique_new} new`);
      setTimeout(() => location.reload(), 1100);
    } catch {
      toast("Sync failed — check server logs");
    } finally {
      scrapeConfirm.disabled = false;
      scrapeConfirm.textContent = "Run pipeline";
      scrapeBtn?.classList.remove("loading");
    }
  }

  document.querySelectorAll(".view-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const view = tab.dataset.view;
      document.querySelectorAll(".view-tab").forEach((t) => t.classList.remove("is-on"));
      tab.classList.add("is-on");
      document.getElementById("feed-view")?.classList.toggle("hidden", view !== "feed");
      document.getElementById("compact-view")?.classList.toggle("hidden", view !== "compact");
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
        body: JSON.stringify({ email: fd.get("email"), keyword: fd.get("keyword") }),
      });
      const data = await resp.json();
      toast(data.ok ? data.message : data.error || "Failed");
      if (data.ok) alertForm.reset();
    });
  }

  function toast(msg) {
    if (!toastRoot) return;
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    toastRoot.appendChild(el);
    setTimeout(() => el.remove(), 4500);
  }
})();

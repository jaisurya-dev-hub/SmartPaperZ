document.querySelectorAll("[data-share]").forEach(b => b.addEventListener("click", async () => {
  const url = b.dataset.share;
  try {
    if (navigator.share) { await navigator.share({ title: document.title, url }); return; }
    await navigator.clipboard.writeText(url); b.textContent = "Link copied";
  } catch (e) { window.prompt("Copy this link:", url); }
}));

(function () {
  let selected = 0;

  function rows() {
    return Array.from(document.querySelectorAll("[data-ticket-row]"));
  }

  function highlight() {
    const all = rows();
    all.forEach((row, i) => row.classList.toggle("bg-surface-2", i === selected));
    const current = all[selected];
    if (current) current.scrollIntoView({ block: "nearest" });
  }

  function isTyping(target) {
    const tag = target.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "/" && !isTyping(event.target)) {
      event.preventDefault();
      const search = document.getElementById("queue-search");
      if (search) search.focus();
      return;
    }

    if (isTyping(event.target)) return;

    const all = rows();
    if (!all.length) return;

    if (event.key === "j" || event.key === "J") {
      selected = Math.min(selected + 1, all.length - 1);
      highlight();
    } else if (event.key === "k" || event.key === "K") {
      selected = Math.max(selected - 1, 0);
      highlight();
    } else if (event.key === "a" || event.key === "A") {
      const current = all[selected];
      const assumeUrl = current && current.dataset.assumeUrl;
      if (assumeUrl) {
        htmx.ajax("POST", assumeUrl, { source: current });
      }
    }
  });

  document.body.addEventListener("htmx:afterSwap", function () {
    selected = 0;
    highlight();
  });
})();

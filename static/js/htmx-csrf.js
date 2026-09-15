function getCookie(name) {
  const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return match ? match.pop() : "";
}

document.body.addEventListener("htmx:configRequest", function (event) {
  event.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
});

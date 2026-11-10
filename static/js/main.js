// Menu em telas pequenas
(function () {
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("menu");
  if (!btn || !nav) return;
  btn.addEventListener("click", function () {
    var open = nav.classList.toggle("aberto");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();

// 往事 · 阅读小工具：目录、字号、夜读、阅读进度、上次读到哪里
(function () {
  var root = document.documentElement;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // 夜读
  var theme = get("ws-theme");
  if (theme) root.setAttribute("data-theme", theme);
  var tBtn = document.getElementById("theme");
  if (tBtn) tBtn.addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") === "dark" ||
      (!root.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next); set("ws-theme", next);
  });

  // 字号：17–28px，两个按钮一大一小
  var SIZES = [17, 20, 23, 26, 28];
  var fs = parseInt(get("ws-fs") || "", 10);
  if (fs) root.style.setProperty("--fs", fs + "px");
  function step(d) {
    var cur = parseInt(getComputedStyle(root).getPropertyValue("--fs"), 10) || 20;
    var i = SIZES.indexOf(cur); if (i < 0) i = 1;
    var next = SIZES[Math.max(0, Math.min(SIZES.length - 1, i + d))];
    root.style.setProperty("--fs", next + "px"); set("ws-fs", String(next));
    var up = document.getElementById("fs-up"), dn = document.getElementById("fs-down");
    if (up) up.disabled = next === SIZES[SIZES.length - 1];
    if (dn) dn.disabled = next === SIZES[0];
  }
  var upB = document.getElementById("fs-up"), dnB = document.getElementById("fs-down");
  if (upB) upB.addEventListener("click", function () { step(1); });
  if (dnB) dnB.addEventListener("click", function () { step(-1); });

  // 目录抽屉
  var drawer = document.getElementById("drawer");
  function toggle(open) { if (drawer) { drawer.classList.toggle("open", open); document.body.style.overflow = open ? "hidden" : ""; } }
  document.querySelectorAll("[data-open-toc]").forEach(function (b) { b.addEventListener("click", function () { toggle(true); }); });
  document.querySelectorAll("[data-close-toc]").forEach(function (b) { b.addEventListener("click", function () { toggle(false); }); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") toggle(false);
    if (e.target.closest && e.target.closest("input,textarea")) return;
    var a = e.key === "ArrowLeft" ? document.querySelector(".pager .prev") : e.key === "ArrowRight" ? document.querySelector(".pager .next") : null;
    if (a && !e.metaKey && !e.ctrlKey && !e.altKey) location.href = a.href;
  });

  // 阅读进度
  var bar = document.querySelector(".progress");
  var art = document.querySelector(".chapter");
  if (bar && art) {
    var tick = function () {
      var r = art.getBoundingClientRect();
      var total = r.height - innerHeight;
      var p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 1;
      bar.style.width = (p * 100).toFixed(1) + "%";
    };
    addEventListener("scroll", tick, { passive: true }); tick();
  }

  // 记住读到哪一章；首页显示“接着读”
  var here = document.body.getAttribute("data-slug");
  var title = document.body.getAttribute("data-title");
  if (here && title) set("ws-last", JSON.stringify({ slug: here, title: title }));
  var cont = document.getElementById("continue");
  if (cont) {
    try {
      var last = JSON.parse(get("ws-last") || "null");
      if (last && last.slug) {
        var a = cont.querySelector("a"); a.href = last.slug + ".html"; a.textContent = last.title;
        cont.style.display = "block";
      }
    } catch (e) {}
  }
})();

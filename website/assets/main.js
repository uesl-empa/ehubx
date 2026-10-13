(function () {
  "use strict";

  var content = window.EHUBX_CONTENT || { projects: [], publications: [], team: [] };

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function draftBadge(item) {
    return item.todo ? el("span", { class: "draft", text: "draft", title: "Placeholder: to be verified" }) : null;
  }

  // Projects
  var projectList = document.getElementById("project-list");
  content.projects.forEach(function (p) {
    var where = [p.place, p.years].filter(Boolean).join(" · ");
    projectList.appendChild(el("article", { class: "project" }, [
      el("div", { class: "project-head" }, [
        p.status ? el("span", { class: "project-status" + (p.status === "Ongoing" ? " is-ongoing" : ""), text: p.status }) : null,
        where ? el("span", { class: "project-where", text: where }) : null,
      ]),
      el("h3", { text: p.title }, [draftBadge(p)]),
      el("p", { class: "project-summary", text: p.summary }),
      p.partners ? el("p", { class: "partners" }, [el("strong", { text: "Partners: " }), document.createTextNode(p.partners)]) : null,
      p.tags && p.tags.length
        ? el("ul", { class: "tags" }, p.tags.map(function (t) { return el("li", { text: t }); }))
        : null,
      p.links && p.links.length
        ? el("div", { class: "links" }, p.links.map(function (l) {
            return el("a", { href: l.url, text: l.label + " →", rel: "noopener" });
          }))
        : null,
    ]));
  });

  // Publications (newest first)
  var pubList = document.getElementById("pub-list");
  content.publications
    .slice()
    .sort(function (a, b) { return (b.year || 0) - (a.year || 0); })
    .forEach(function (pub) {
      var titleNode = pub.url
        ? el("a", { href: pub.url, text: pub.title, rel: "noopener" })
        : document.createTextNode(pub.title);
      pubList.appendChild(el("li", {}, [
        el("div", {}, [
          el("span", { class: "pub-year", text: String(pub.year || "") }),
          el("span", { class: "pub-type", text: pub.type || "" }),
        ]),
        el("div", {}, [
          el("span", { class: "pub-title" }, [titleNode, draftBadge(pub)]),
          el("span", { class: "pub-authors", text: pub.authors || "" }),
          el("span", { class: "pub-venue", text: pub.venue || "" }),
        ]),
      ]));
    });

  // Theses (PhD first, then MSc and others; newest first within each level)
  var thesisList = document.getElementById("thesis-list");
  var levelRank = { PhD: 0, MSc: 1, BSc: 2 };
  var theses = (content.theses || []).slice().sort(function (a, b) {
    var ra = a.level in levelRank ? levelRank[a.level] : 3;
    var rb = b.level in levelRank ? levelRank[b.level] : 3;
    return ra - rb || String(b.year || "").localeCompare(String(a.year || ""));
  });
  theses.forEach(function (t) {
    var titleNode = t.url
      ? el("a", { href: t.url, text: t.title, rel: "noopener" })
      : document.createTextNode(t.title);
    var details = [t.institution, t.supervisors ? "Supervised by " + t.supervisors : ""]
      .filter(Boolean).join(" · ");
    thesisList.appendChild(el("li", { class: "thesis", "data-level": t.level || "" }, [
      el("div", { class: "thesis-head" }, [
        el("span", { class: "thesis-level", text: t.level || "" }),
        t.status ? el("span", { class: "thesis-status" + (t.status === "Ongoing" ? " is-ongoing" : ""), text: t.status }) : null,
        el("span", { class: "thesis-year", text: String(t.year || "") }),
      ]),
      el("h3", {}, [titleNode, draftBadge(t)]),
      el("p", { class: "thesis-student", text: t.student || "" }),
      details ? el("p", { class: "thesis-details", text: details }) : null,
    ]));
  });

  // Filter chips: "All" plus one per level present in the data (hidden if only one level)
  var filter = document.querySelector(".thesis-filter");
  var levels = [];
  theses.forEach(function (t) { if (t.level && levels.indexOf(t.level) < 0) levels.push(t.level); });
  if (levels.length < 2) filter.hidden = true;
  ["all"].concat(levels).forEach(function (level, i) {
    filter.appendChild(el("button", {
      type: "button", class: "chip" + (i === 0 ? " is-active" : ""),
      "data-level": level, "aria-pressed": i === 0 ? "true" : "false",
      text: level === "all" ? "All" : level,
    }));
  });
  var chips = filter.querySelectorAll(".chip");
  Array.prototype.forEach.call(chips, function (chip) {
    chip.addEventListener("click", function () {
      var level = chip.getAttribute("data-level");
      Array.prototype.forEach.call(chips, function (c) {
        var on = c === chip;
        c.classList.toggle("is-active", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      Array.prototype.forEach.call(thesisList.children, function (item) {
        item.hidden = level !== "all" && item.getAttribute("data-level") !== level;
      });
    });
  });

  // Team
  var teamList = document.getElementById("team-list");
  content.team.forEach(function (name) { teamList.appendChild(el("li", { text: name })); });

  // Mobile nav
  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("nav-links");
  toggle.addEventListener("click", function () {
    var open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
  links.addEventListener("click", function (e) {
    if (e.target.tagName === "A") {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
})();

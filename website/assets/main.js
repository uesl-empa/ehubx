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
    var meta = el("div", { class: "project-meta" }, [
      el("div", { class: "place", text: p.place || "" }),
      p.years ? el("div", { class: "years", text: p.years }) : null,
      p.tags && p.tags.length
        ? el("ul", { class: "tags" }, p.tags.map(function (t) { return el("li", { text: t }); }))
        : null,
    ]);
    var title = el("h3", { text: p.title }, [draftBadge(p)]);
    var body = el("div", {}, [
      title,
      el("p", { text: p.summary }),
      p.partners ? el("p", { class: "partners" }, [el("strong", { text: "Partners: " }), document.createTextNode(p.partners)]) : null,
      p.links && p.links.length
        ? el("div", { class: "links" }, p.links.map(function (l) {
            return el("a", { href: l.url, text: l.label + " →", rel: "noopener" });
          }))
        : null,
    ]);
    projectList.appendChild(el("article", { class: "project" }, [meta, body]));
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

/* Document index: folder tree, search, filters, sorting and pagination. */
(function () {
  "use strict";
  var V = window.VDR;
  if (!V.requireTerms()) {
    return;
  }
  V.wireExit();

  var PAGE_SIZE = 15;
  var status = document.getElementById("status");
  var room = document.getElementById("room");
  var tree = document.getElementById("tree");
  var rows = document.getElementById("rows");
  var count = document.getElementById("count");
  var pager = document.getElementById("pager");
  var inputs = {
    q: document.getElementById("q"),
    folder: document.getElementById("f-folder"),
    type: document.getElementById("f-type"),
    from: document.getElementById("f-from"),
    to: document.getElementById("f-to"),
    sort: document.getElementById("f-sort"),
    superseded: document.getElementById("f-superseded")
  };
  var data = null;
  var state = { q: "", folder: "", type: "", from: "", to: "", superseded: false, sort: "index", dir: "asc", page: 1 };

  function loadState() {
    var p = V.readParams();
    state.q = p.get("q") || "";
    state.folder = p.get("folder") || "";
    state.type = p.get("type") || "";
    state.from = parseDate(p.get("from") || "") || "";
    state.to = parseDate(p.get("to") || "") || "";
    state.superseded = p.get("superseded") === "1";
    state.sort = p.get("sort") === "date" ? "date" : "index";
    state.dir = p.get("dir") === "desc" ? "desc" : "asc";
    state.page = Math.max(1, parseInt(p.get("page") || "1", 10) || 1);
  }

  function saveState() {
    var p = new URLSearchParams();
    if (state.q) { p.set("q", state.q); }
    if (state.folder) { p.set("folder", state.folder); }
    if (state.type) { p.set("type", state.type); }
    if (state.from) { p.set("from", state.from); }
    if (state.to) { p.set("to", state.to); }
    if (state.superseded) { p.set("superseded", "1"); }
    if (state.sort !== "index" || state.dir !== "asc") {
      p.set("sort", state.sort);
      p.set("dir", state.dir);
    }
    if (state.page > 1) { p.set("page", String(state.page)); }
    V.writeParams(p);
  }

  function syncInputs() {
    inputs.q.value = state.q;
    inputs.folder.value = state.folder;
    inputs.type.value = state.type;
    if (parseDate(inputs.from.value) !== (state.from || null)) { inputs.from.value = displayDate(state.from); }
    if (parseDate(inputs.to.value) !== (state.to || null)) { inputs.to.value = displayDate(state.to); }
    inputs.superseded.checked = state.superseded;
    inputs.sort.value = state.sort + "-" + state.dir;
    if (!inputs.sort.value) {
      inputs.sort.value = "index-asc";
    }
    tree.querySelectorAll(".tree-folder").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-folder") === state.folder ? "true" : "false");
    });
    document.querySelectorAll("th[data-col]").forEach(function (th) {
      var col = th.getAttribute("data-col");
      if (col === state.sort) {
        th.setAttribute("aria-sort", state.dir === "asc" ? "ascending" : "descending");
      } else {
        th.removeAttribute("aria-sort");
      }
    });
  }

  function matches(doc) {
    if (!state.superseded && doc.status !== "current") { return false; }
    if (state.folder && String(doc.folder) !== state.folder) { return false; }
    if (state.type && doc.type !== state.type) { return false; }
    if (state.from && doc.date < state.from) { return false; }
    if (state.to && doc.date > state.to) { return false; }
    if (state.q) {
      var hay = (doc.index + " " + doc.title + " " + doc.type).toLowerCase();
      var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < terms.length; i++) {
        if (hay.indexOf(terms[i]) === -1) { return false; }
      }
    }
    return true;
  }

  function sorted(list) {
    var dir = state.dir === "desc" ? -1 : 1;
    return list.slice().sort(function (a, b) {
      var d;
      if (state.sort === "date") {
        d = a.date < b.date ? -1 : a.date > b.date ? 1 : 0;
        if (d === 0) { d = V.compareIndex(a.index, b.index) || a.version - b.version; }
        return d * dir;
      }
      d = V.compareIndex(a.index, b.index) || a.version - b.version;
      return d * dir;
    });
  }

  function cell(label, className, content) {
    var td = V.el("td", { "data-label": label, className: className });
    if (typeof content === "string") {
      td.textContent = content;
    } else {
      td.appendChild(content);
    }
    return td;
  }

  function nameCell(doc) {
    var wrap = V.el("span", null, V.el("a", { href: V.docUrl(doc), text: doc.title }));
    if (doc.status !== "current") {
      wrap.appendChild(V.el("span", { className: "badge superseded", text: "Superseded" }));
    }
    if (doc.view_only) {
      wrap.appendChild(V.el("span", { className: "badge viewonly", text: "View only" }));
    }
    return wrap;
  }

  function render() {
    var list = sorted(data.documents.filter(matches));
    var pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (state.page > pageCount) { state.page = pageCount; }
    var start = (state.page - 1) * PAGE_SIZE;
    var shown = list.slice(start, start + PAGE_SIZE);

    rows.textContent = "";
    if (!shown.length) {
      var td = V.el("td", { colspan: "6", className: "empty", text: "No documents match these filters." });
      rows.appendChild(V.el("tr", null, td));
    }
    shown.forEach(function (doc) {
      var time = V.el("time", { datetime: doc.date, text: V.formatDate(doc.date) });
      rows.appendChild(V.el("tr", null,
        cell("Index", "c-index", doc.index),
        cell("Name", "c-name", nameCell(doc)),
        cell("Type", "c-type", doc.type),
        cell("Date", "c-date", time),
        cell("Version", "c-version", "v" + doc.version),
        cell("Pages", "c-pages", V.pagesLabel(doc))
      ));
    });
    count.textContent = list.length
      ? "Showing " + (start + 1) + " to " + (start + shown.length) + " of " + list.length +
        (list.length === 1 ? " document" : " documents")
      : "0 documents";
    V.renderPager(pager, state.page, pageCount, function (n) {
      state.page = n;
      update();
      count.focus();
    });
    syncInputs();
    saveState();
  }

  function update() {
    render();
  }

  function setFilter(key, value) {
    state[key] = value;
    state.page = 1;
    update();
  }

  function buildTree() {
    var all = V.el("button", { type: "button", className: "tree-folder", "data-folder": "", "aria-pressed": "false" },
      "All documents ", V.el("span", { className: "n", text: "(" + data.documents.filter(function (d) { return d.status === "current"; }).length + ")" }));
    all.addEventListener("click", function () { setFilter("folder", ""); });
    tree.appendChild(V.el("li", null, V.el("div", { className: "tree-row tree-all" }, all)));

    data.folders.forEach(function (folder) {
      var docs = data.documents.filter(function (d) { return d.folder === folder.id && d.status === "current"; });
      var listId = "tree-f" + folder.id;
      var toggle = V.el("button", {
        type: "button", className: "tree-toggle", "aria-expanded": "false", "aria-controls": listId,
        "aria-label": "Show documents in folder " + folder.id + " " + folder.name
      });
      var select = V.el("button", { type: "button", className: "tree-folder", "data-folder": String(folder.id), "aria-pressed": "false" },
        folder.id + " " + folder.name + " ", V.el("span", { className: "n", text: "(" + docs.length + ")" }));
      var sub = V.el("ul", { id: listId, hidden: true });
      docs.forEach(function (d) {
        sub.appendChild(V.el("li", null, V.el("a", { href: V.docUrl(d), text: d.index + " " + d.title })));
      });
      toggle.addEventListener("click", function () {
        var open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", open ? "false" : "true");
        toggle.setAttribute("aria-label", (open ? "Show" : "Hide") + " documents in folder " + folder.id + " " + folder.name);
        sub.hidden = open;
      });
      select.addEventListener("click", function () { setFilter("folder", String(folder.id)); });
      tree.appendChild(V.el("li", null, V.el("div", { className: "tree-row" }, toggle, select), sub));

      inputs.folder.appendChild(V.el("option", { value: String(folder.id), text: folder.id + " " + folder.name }));
    });
  }

  function parseDate(text) {
    var t = text.trim();
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(t);
    var iso = null;
    if (m) {
      iso = m[1] + "-" + m[2] + "-" + m[3];
    } else {
      m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(t);
      if (m) {
        iso = m[3] + "-" + ("0" + m[2]).slice(-2) + "-" + ("0" + m[1]).slice(-2);
      }
    }
    if (!iso) {
      return null;
    }
    var d = new Date(iso + "T00:00:00Z");
    return !isNaN(d) && d.toISOString().slice(0, 10) === iso ? iso : null;
  }

  function dateChanged(key) {
    var input = inputs[key];
    var errorNode = document.getElementById("date-error");
    var text = input.value.trim();
    var iso = text ? parseDate(text) : "";
    if (iso === null) {
      input.setAttribute("aria-invalid", "true");
      errorNode.textContent = "Enter the " + (key === "from" ? "start" : "end") + " date as DD/MM/YYYY or YYYY-MM-DD.";
      errorNode.hidden = !(text.length >= 8);
      return;
    }
    input.removeAttribute("aria-invalid");
    errorNode.hidden = true;
    if (iso !== state[key]) {
      setFilter(key, iso);
    }
  }

  function displayDate(iso) {
    if (!iso) { return ""; }
    var p = iso.split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  function wireFilters() {
    inputs.q.addEventListener("input", function () { setFilter("q", inputs.q.value.trim()); });
    inputs.folder.addEventListener("change", function () { setFilter("folder", inputs.folder.value); });
    inputs.type.addEventListener("change", function () { setFilter("type", inputs.type.value); });
    ["input", "change"].forEach(function (type) {
      inputs.from.addEventListener(type, function () { dateChanged("from"); });
      inputs.to.addEventListener(type, function () { dateChanged("to"); });
    });
    inputs.superseded.addEventListener("change", function () { setFilter("superseded", inputs.superseded.checked); });
    inputs.sort.addEventListener("change", function () {
      var parts = inputs.sort.value.split("-");
      state.sort = parts[0];
      state.dir = parts[1];
      state.page = 1;
      update();
    });
    document.getElementById("filters").addEventListener("submit", function (e) { e.preventDefault(); });
    document.getElementById("f-reset").addEventListener("click", function () {
      state = { q: "", folder: "", type: "", from: "", to: "", superseded: false, sort: "index", dir: "asc", page: 1 };
      inputs.from.value = "";
      inputs.to.value = "";
      inputs.from.removeAttribute("aria-invalid");
      inputs.to.removeAttribute("aria-invalid");
      document.getElementById("date-error").hidden = true;
      update();
    });
    document.querySelectorAll("button.sort").forEach(function (b) {
      b.addEventListener("click", function () {
        var key = b.getAttribute("data-sort");
        if (state.sort === key) {
          state.dir = state.dir === "asc" ? "desc" : "asc";
        } else {
          state.sort = key;
          state.dir = key === "date" ? "desc" : "asc";
        }
        state.page = 1;
        update();
      });
    });
  }

  count.setAttribute("tabindex", "-1");
  loadState();
  V.getJSON("data/index.json").then(function (json) {
    data = json;
    buildTree();
    wireFilters();
    status.textContent = data.documents.filter(function (d) { return d.status === "current"; }).length +
      " current documents in " + data.folders.length + " folders.";
    room.hidden = false;
    update();
  }).catch(function (err) {
    V.showError(status, err);
  });
})();

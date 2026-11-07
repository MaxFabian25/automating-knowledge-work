/* Document viewer: header with index number and version, body or download. */
(function () {
  "use strict";
  var V = window.VDR;
  if (!V.requireTerms()) {
    return;
  }
  V.wireExit();

  var status = document.getElementById("status");
  var article = document.getElementById("doc");
  var body = document.getElementById("d-body");
  var notices = document.getElementById("d-notices");
  var actions = document.getElementById("d-actions");

  function findDoc(documents, id) {
    var exact = documents.filter(function (d) { return d.id === id; })[0];
    return exact || V.currentVersion(documents, id);
  }

  function metaItem(term, value) {
    return V.el("div", null, V.el("dt", { text: term }), V.el("dd", { text: value }));
  }

  function wrapTables(root) {
    root.querySelectorAll("table").forEach(function (table) {
      var wrap = V.el("div", { className: "table-scroll", tabindex: "0", role: "region",
        "aria-label": (table.caption ? table.caption.textContent : "Table") + " (scrolls sideways)" });
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
  }

  function downloadLink(doc) {
    return V.el("a", { className: "btn primary", href: "files/" + doc.file, download: doc.file,
      text: "Download " + doc.type });
  }

  function render(data, doc) {
    var folder = data.folders.filter(function (f) { return f.id === doc.folder; })[0];
    document.title = doc.index + " " + doc.title + " (v" + doc.version + ") | " + data.room_title;
    var crumbFolder = document.getElementById("crumb-folder");
    crumbFolder.appendChild(V.el("a", { href: "room.html?folder=" + doc.folder, text: folder.id + " " + folder.name }));
    document.getElementById("crumb-doc").textContent = doc.index + " v" + doc.version;
    document.getElementById("d-index").textContent = doc.index;
    document.getElementById("d-version").textContent = "Version " + doc.version +
      (doc.status === "current" ? " (current)" : " (superseded)");
    document.getElementById("d-title").textContent = doc.title;

    var meta = document.getElementById("d-meta");
    meta.appendChild(metaItem("Type", doc.type));
    meta.appendChild(metaItem("Uploaded", V.formatDate(doc.date)));
    meta.appendChild(metaItem(doc.type === "XLSX" ? "Sheets" : "Pages", doc.type === "XLSX" ? String(doc.sheets.length) : String(doc.pages)));
    meta.appendChild(metaItem("Folder", folder.id + " " + folder.name));

    var versions = data.documents.filter(function (d) { return d.index === doc.index; })
      .sort(function (a, b) { return a.version - b.version; });
    if (doc.status !== "current") {
      var current = V.currentVersion(data.documents, doc.index);
      notices.appendChild(V.el("div", { className: "notice warn", role: "note" },
        V.el("strong", { text: "Superseded. " }),
        "This is version " + doc.version + ". It was replaced by version " + current.version +
        " on " + V.formatDate(current.date) + ". ",
        V.el("a", { href: V.docUrl(current), text: "Open the current version" })));
    }
    if (doc.view_only) {
      notices.appendChild(V.el("div", { className: "notice", role: "note" },
        V.el("strong", { text: "View only. " }), "This document cannot be downloaded or printed."));
    } else {
      actions.appendChild(downloadLink(doc));
      actions.appendChild(V.el("span", { className: "file-name", text: doc.file }));
    }

    if (versions.length > 1) {
      var history = document.getElementById("d-history");
      var list = document.getElementById("d-history-list");
      versions.forEach(function (v) {
        var label = "Version " + v.version + ", " + V.formatDate(v.date) + (v.status === "current" ? " (current)" : " (superseded)");
        list.appendChild(V.el("li", null, v.id === doc.id
          ? V.el("span", { text: label + ", shown above" })
          : V.el("a", { href: V.docUrl(v), text: label })));
      });
      history.hidden = false;
    }

    if (doc.type === "HTML") {
      return V.getText(doc.content).then(function (fragment) {
        body.innerHTML = fragment;
        wrapTables(body);
      });
    }
    if (doc.type === "PDF") {
      body.appendChild(V.el("p", { text: "Preview of the PDF. If it does not appear, use the Download button." }));
      var frame = V.el("object", { data: "files/" + doc.file, type: "application/pdf", className: "pdf-frame",
        "aria-label": "PDF preview of " + doc.title },
        V.el("p", { text: "Your browser cannot show this PDF here. Use the Download button above." }));
      body.appendChild(frame);
      return Promise.resolve();
    }
    body.appendChild(V.el("p", { text: "Spreadsheets cannot be previewed in the data room. Download the file to open it." }));
    var sheets = V.el("ul");
    doc.sheets.forEach(function (name) { sheets.appendChild(V.el("li", { text: name })); });
    body.appendChild(V.el("h2", { text: "Sheets in this workbook" }));
    body.appendChild(sheets);
    return Promise.resolve();
  }

  var id = V.readParams().get("id") || "";
  V.getJSON("data/index.json").then(function (data) {
    var doc = findDoc(data.documents, id);
    if (!doc) {
      throw new Error("there is no document with the reference " + JSON.stringify(id));
    }
    return render(data, doc).then(function () {
      status.textContent = "";
      status.hidden = true;
      article.hidden = false;
    });
  }).catch(function (err) {
    V.showError(status, err);
  });
})();

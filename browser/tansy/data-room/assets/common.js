/* Shared helpers for the made-up data room. Plain JavaScript, no dependencies. */
(function () {
  "use strict";

  var TERMS_KEY = document.body.dataset.termsKey;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var SAFE_NEXT = /^(room|doc|qa)(\.html)?(\?[A-Za-z0-9=&%._~+-]*)?$/;

  function termsAccepted() {
    try {
      return window.sessionStorage.getItem(TERMS_KEY) === "accepted";
    } catch (e) {
      return false;
    }
  }

  function acceptTerms() {
    window.sessionStorage.setItem(TERMS_KEY, "accepted");
  }

  function requireTerms() {
    if (termsAccepted()) {
      return true;
    }
    var page = window.location.pathname.split("/").pop() || "room.html";
    var next = page + window.location.search;
    window.location.replace("index.html?next=" + encodeURIComponent(next));
    return false;
  }

  function safeNext(value) {
    return value && SAFE_NEXT.test(value) ? value : "room.html";
  }

  function getJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (res) {
      if (!res.ok) {
        throw new Error("Could not load " + url + " (" + res.status + ")");
      }
      return res.json();
    });
  }

  function getText(url) {
    return fetch(url, { cache: "no-cache" }).then(function (res) {
      if (!res.ok) {
        throw new Error("Could not load " + url + " (" + res.status + ")");
      }
      return res.text();
    });
  }

  function el(tag, attrs) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === null || value === undefined || value === false) {
          return;
        }
        if (key === "text") {
          node.textContent = value;
        } else if (key === "className") {
          node.className = value;
        } else {
          node.setAttribute(key, value === true ? "" : value);
        }
      });
    }
    for (var i = 2; i < arguments.length; i++) {
      var child = arguments[i];
      if (child === null || child === undefined) {
        continue;
      }
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
  }

  function formatDate(iso) {
    if (!iso) {
      return "";
    }
    var parts = iso.split("-");
    return Number(parts[2]) + " " + MONTHS[Number(parts[1]) - 1] + " " + parts[0];
  }

  function compareIndex(a, b) {
    var pa = a.split(".").map(Number);
    var pb = b.split(".").map(Number);
    for (var i = 0; i < Math.max(pa.length, pb.length); i++) {
      var d = (pa[i] || 0) - (pb[i] || 0);
      if (d !== 0) {
        return d;
      }
    }
    return 0;
  }

  function docUrl(doc) {
    return "doc.html?id=" + encodeURIComponent(doc.id);
  }

  function currentVersion(documents, index) {
    var matches = documents.filter(function (d) {
      return d.index === index && d.status === "current";
    });
    return matches.length ? matches[0] : null;
  }

  function pagesLabel(doc) {
    if (doc.type === "XLSX") {
      var n = doc.sheets ? doc.sheets.length : 0;
      return n + (n === 1 ? " sheet" : " sheets");
    }
    return doc.pages === null || doc.pages === undefined ? "" : String(doc.pages);
  }

  function renderPager(nav, page, pageCount, onPage) {
    nav.textContent = "";
    if (pageCount <= 1) {
      nav.hidden = true;
      return;
    }
    nav.hidden = false;
    var prev = el("button", { type: "button", className: "btn", text: "Previous", disabled: page <= 1 });
    prev.addEventListener("click", function () { onPage(page - 1); });
    nav.appendChild(prev);
    for (var p = 1; p <= pageCount; p++) {
      (function (n) {
        var b = el("button", {
          type: "button",
          className: "btn",
          text: String(n),
          "aria-label": "Page " + n,
          "aria-current": n === page ? "page" : null
        });
        b.addEventListener("click", function () { onPage(n); });
        nav.appendChild(b);
      })(p);
    }
    var next = el("button", { type: "button", className: "btn", text: "Next", disabled: page >= pageCount });
    next.addEventListener("click", function () { onPage(page + 1); });
    nav.appendChild(next);
  }

  function readParams() {
    return new URLSearchParams(window.location.search);
  }

  function writeParams(params) {
    var query = params.toString();
    var url = window.location.pathname + (query ? "?" + query : "");
    window.history.replaceState(null, "", url);
  }

  function wireExit() {
    document.querySelectorAll("[data-exit]").forEach(function (button) {
      button.addEventListener("click", function () {
        try {
          window.sessionStorage.removeItem(TERMS_KEY);
        } catch (e) {
          /* storage unavailable: nothing to clear */
        }
        window.location.href = "index.html";
      });
    });
  }

  function showError(statusNode, err) {
    statusNode.textContent = "Something went wrong: " + err.message;
    statusNode.classList.add("error");
  }

  window.VDR = {
    termsAccepted: termsAccepted,
    acceptTerms: acceptTerms,
    requireTerms: requireTerms,
    safeNext: safeNext,
    getJSON: getJSON,
    getText: getText,
    el: el,
    formatDate: formatDate,
    compareIndex: compareIndex,
    docUrl: docUrl,
    currentVersion: currentVersion,
    pagesLabel: pagesLabel,
    renderPager: renderPager,
    readParams: readParams,
    writeParams: writeParams,
    wireExit: wireExit,
    showError: showError
  };
})();

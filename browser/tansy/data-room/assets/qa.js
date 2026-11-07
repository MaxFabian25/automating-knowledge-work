/* Q&A module: filter by status and topic, ten entries a page. */
(function () {
  "use strict";
  var V = window.VDR;
  if (!V.requireTerms()) {
    return;
  }
  V.wireExit();

  var PAGE_SIZE = 10;
  var status = document.getElementById("status");
  var wrap = document.getElementById("qa");
  var list = document.getElementById("qa-list");
  var count = document.getElementById("count");
  var pager = document.getElementById("pager");
  var fStatus = document.getElementById("f-status");
  var fTopic = document.getElementById("f-topic");
  var qa = null;
  var index = null;
  var state = { status: "", topic: "", page: 1 };

  function slug(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  }

  function loadState() {
    var p = V.readParams();
    state.status = p.get("status") || "";
    state.topic = p.get("topic") || "";
    state.page = Math.max(1, parseInt(p.get("page") || "1", 10) || 1);
  }

  function saveState() {
    var p = new URLSearchParams();
    if (state.status) { p.set("status", state.status); }
    if (state.topic) { p.set("topic", state.topic); }
    if (state.page > 1) { p.set("page", String(state.page)); }
    V.writeParams(p);
  }

  function refLink(ref) {
    var doc = V.currentVersion(index.documents, ref);
    if (!doc) {
      return V.el("span", { text: ref + " (not found)" });
    }
    return V.el("a", { href: V.docUrl(doc), text: doc.index + " " + doc.title });
  }

  function entry(e) {
    var headingId = "q-" + e.id;
    var meta = V.el("p", { className: "qa-meta" },
      V.el("span", { className: "tag", text: e.topic }),
      V.el("span", { className: "state " + slug(e.status), text: e.status }),
      V.el("span", null, "Asked ", V.el("time", { datetime: e.asked, text: V.formatDate(e.asked) })),
      e.answered ? V.el("span", null, "Answered ", V.el("time", { datetime: e.answered, text: V.formatDate(e.answered) })) : null);
    var answer = V.el("div", { className: "qa-answer" },
      V.el("h3", { className: "visually-hidden", text: "Answer" }),
      V.el("p", { text: e.answer ? e.answer : "No answer yet." }));
    var refs = V.el("p", { className: "qa-refs" }, "Referenced documents: ");
    e.refs.forEach(function (r, i) {
      if (i) { refs.appendChild(document.createTextNode("; ")); }
      refs.appendChild(refLink(r));
    });
    return V.el("li", null, V.el("article", { className: "qa-item", "aria-labelledby": headingId },
      V.el("h2", { id: headingId }, V.el("span", { className: "qid", text: e.id }), e.question),
      meta, answer, refs));
  }

  function render() {
    var items = qa.entries.filter(function (e) {
      return (!state.status || e.status === state.status) && (!state.topic || e.topic === state.topic);
    });
    var pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
    if (state.page > pageCount) { state.page = pageCount; }
    var start = (state.page - 1) * PAGE_SIZE;
    var shown = items.slice(start, start + PAGE_SIZE);
    list.textContent = "";
    shown.forEach(function (e) { list.appendChild(entry(e)); });
    if (!shown.length) {
      list.appendChild(V.el("li", { className: "empty", text: "No questions match these filters." }));
    }
    count.textContent = items.length
      ? "Showing " + (start + 1) + " to " + (start + shown.length) + " of " + items.length +
        (items.length === 1 ? " question" : " questions")
      : "0 questions";
    fStatus.value = state.status;
    fTopic.value = state.topic;
    V.renderPager(pager, state.page, pageCount, function (n) {
      state.page = n;
      render();
      count.focus();
    });
    saveState();
  }

  count.setAttribute("tabindex", "-1");
  loadState();
  Promise.all([V.getJSON("data/qa.json"), V.getJSON("data/index.json")]).then(function (res) {
    qa = res[0];
    index = res[1];
    qa.statuses.forEach(function (s) { fStatus.appendChild(V.el("option", { value: s, text: s })); });
    qa.topics.forEach(function (t) { fTopic.appendChild(V.el("option", { value: t, text: t })); });
    fStatus.addEventListener("change", function () { state.status = fStatus.value; state.page = 1; render(); });
    fTopic.addEventListener("change", function () { state.topic = fTopic.value; state.page = 1; render(); });
    document.getElementById("qa-filters").addEventListener("submit", function (e) { e.preventDefault(); });
    document.getElementById("f-reset").addEventListener("click", function () {
      state = { status: "", topic: "", page: 1 };
      render();
    });
    status.textContent = qa.entries.length + " questions.";
    wrap.hidden = false;
    render();
  }).catch(function (err) {
    V.showError(status, err);
  });
})();

(function () {
  "use strict";
  var form = document.getElementById("gate-form");
  var box = document.getElementById("accept");
  var error = document.getElementById("gate-error");
  var next = window.VDR.safeNext(window.VDR.readParams().get("next"));

  if (window.VDR.termsAccepted()) {
    box.checked = true;
  }

  box.addEventListener("change", function () {
    if (box.checked) {
      error.hidden = true;
      box.removeAttribute("aria-invalid");
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!box.checked) {
      error.hidden = false;
      box.setAttribute("aria-invalid", "true");
      box.focus();
      return;
    }
    window.VDR.acceptTerms();
    window.location.href = next;
  });
})();

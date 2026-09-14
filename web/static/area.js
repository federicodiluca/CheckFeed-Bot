// "Dove insegni?": mostra solo le province della regione scelta (senza JS restano tutte visibili).
(function () {
  var select = document.getElementById("region");
  if (!select) return;
  function update() {
    var r = select.value;
    document.querySelectorAll("fieldset.provinces").forEach(function (fs) {
      var mine = fs.getAttribute("data-region") === r;
      fs.hidden = !mine;
      if (!mine) fs.querySelectorAll("input[type=checkbox]").forEach(function (c) { c.checked = false; });
    });
    document.querySelectorAll(".region-note").forEach(function (n) { n.hidden = n.getAttribute("data-note") !== r; });
  }
  select.addEventListener("change", update);
  update();
})();

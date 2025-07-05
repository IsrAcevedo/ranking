function manejarNuevoTema() {
  let btnNuevoTema = document.getElementById("nuevo-tema");
  let elemento = document.getElementById("form-nuevo-tema");

  elemento.classList.remove("hidden");
  elemento.classList.add("block");
  btnNuevoTema.classList.add("hidden");
}


function ocultarFormularioTema() {
  let btnNuevoTema = document.getElementById("nuevo-tema");
  let elemento = document.getElementById("form-nuevo-tema");

  elemento.classList.remove("block");
  elemento.classList.add("hidden");
  btnNuevoTema.classList.remove("hidden");
  btnNuevoTema.classList.add("block");
}

document.getElementById("nuevo-tema").addEventListener("click", manejarNuevoTema);

document.getElementById("form-nuevo-tema").addEventListener("submit", function (event) {
  ocultarFormularioTema();
});

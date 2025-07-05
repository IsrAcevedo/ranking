
function mostrarDetalle(elemento) {
    const titulo = elemento.getAttribute('data-titulo');
    const fecha = elemento.getAttribute('data-fecha');
    const descripcion = elemento.getAttribute('data-descripcion');

    document.getElementById('titulo-clase').textContent = titulo;
    document.getElementById('fecha-clase').textContent = fecha;
    document.getElementById('descripcion-clase').innerHTML = descripcion;
}

window.addEventListener('DOMContentLoaded', function () {
    const ultimaClase = document.getElementById('ultima-clase');
    if (ultimaClase) {
        mostrarDetalle(ultimaClase);
    }
});
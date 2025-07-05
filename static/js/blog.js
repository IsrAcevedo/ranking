
function mostrarBlog(elemento) {
    const titulo = elemento.getAttribute('data-titulo');
    const fecha = elemento.getAttribute('data-fecha');
    const contenido = elemento.getAttribute('data-contenido');
    const autor = elemento.getAttribute('data-autor');

    document.getElementById('titulo-blog').textContent = titulo;
    document.getElementById('contenido-blog').innerHTML = contenido;
    document.getElementById('autor-blog').textContent = autor
    document.getElementById('fecha-blog').textContent = fecha;

}

window.addEventListener('DOMContentLoaded', function () {
    const ultimaEntrada = document.getElementById('ultima-entrada');
    if (ultimaEntrada) {
        mostrarBlog(ultimaEntrada);
    }
});
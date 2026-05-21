document.addEventListener('DOMContentLoaded', () => {
    const btnHamburguesa = document.getElementById('btn-hamburguesa');
    const menuNavegacion = document.getElementById('menu-navegacion');

    if (btnHamburguesa && menuNavegacion) {
        btnHamburguesa.addEventListener('click', () => {
            // Alterna la clase 'hidden' para mostrar/ocultar el menú en móviles
            menuNavegacion.classList.toggle('hidden');
            menuNavegacion.classList.toggle('flex');
        });
    }
});

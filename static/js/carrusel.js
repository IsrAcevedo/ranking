document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('carrusel-container');
    const prevBtn = document.getElementById('carrusel-prev');
    const nextBtn = document.getElementById('carrusel-next');

    if (!container) return;

    const getCards = () => container.querySelectorAll('.carousel-card');

    // Navegación con botones
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', () => {
            const cards = getCards();
            if (cards.length === 0) return;
            const cardWidth = cards[0].offsetWidth + parseInt(window.getComputedStyle(container).gap || 24);
            container.scrollBy({ left: -cardWidth, behavior: 'smooth' });
        });

        nextBtn.addEventListener('click', () => {
            const cards = getCards();
            if (cards.length === 0) return;
            const cardWidth = cards[0].offsetWidth + parseInt(window.getComputedStyle(container).gap || 24);
            container.scrollBy({ left: cardWidth, behavior: 'smooth' });
        });
    }

    // Efecto de enfoque (Focus) en la tarjeta central
    const updateFocus = () => {
        const cards = getCards();
        if (cards.length === 0) return;

        const containerRect = container.getBoundingClientRect();
        const containerCenter = containerRect.left + containerRect.width / 2;

        let closestCard = null;
        let minDistance = Infinity;

        cards.forEach(card => {
            const cardRect = card.getBoundingClientRect();
            const cardCenter = cardRect.left + cardRect.width / 2;
            const distance = Math.abs(containerCenter - cardCenter);

            if (distance < minDistance) {
                minDistance = distance;
                closestCard = card;
            }
        });

        cards.forEach(card => {
            if (card === closestCard) {
                card.classList.add('scale-105', 'z-10');
                card.classList.remove('scale-95', 'opacity-60');
                card.querySelector('.fondo_secundario').classList.add('shadow-2xl', 'border-green-300');
            } else {
                card.classList.remove('scale-105', 'z-10');
                card.classList.add('scale-95', 'opacity-60');
                card.querySelector('.fondo_secundario').classList.remove('shadow-2xl', 'border-green-300');
            }
        });
    };

    // Escuchar eventos para actualizar el foco
    container.addEventListener('scroll', updateFocus);
    window.addEventListener('resize', updateFocus);

    // Llamada inicial
    setTimeout(updateFocus, 100);
});

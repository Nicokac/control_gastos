document.addEventListener('DOMContentLoaded', function () {
    const tourData = document.getElementById('tour-data');
    if (!tourData || typeof Shepherd === 'undefined') return;

    const tourDoneUrl = tourData.dataset.tourDoneUrl;
    const csrfToken = tourData.dataset.csrfToken;

    function markTourDone() {
        fetch(tourDoneUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
        });
    }

    const isMobile = window.innerWidth < 768;

    function sidebarAttach(elementId) {
        return isMobile ? null : { element: elementId, on: 'right' };
    }

    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: { behavior: 'smooth', block: 'center' },
            classes: 'shepherd-theme-arrows',
            buttons: [
                {
                    text: 'Anterior',
                    action: function () { this.back(); },
                    secondary: true,
                },
                {
                    text: 'Siguiente',
                    action: function () { this.next(); },
                },
            ],
        },
    });

    tour.addStep({
        id: 'dashboard',
        attachTo: sidebarAttach('#tour-nav-dashboard'),
        title: 'Dashboard',
        text: 'Acá vas a ver un resumen de tus finanzas del mes: balance, gastos por categoría y evolución histórica.',
        buttons: [
            { text: 'Saltar tour', action: function () { tour.cancel(); }, secondary: true },
            { text: 'Siguiente', action: function () { this.next(); } },
        ],
    });

    tour.addStep({
        id: 'expenses',
        attachTo: sidebarAttach('#tour-nav-expenses'),
        title: 'Gastos',
        text: 'Registrá y filtrá todos tus gastos. Podés organizarlos por categoría, método de pago o tipo (fijo/variable).',
    });

    tour.addStep({
        id: 'fab',
        attachTo: { element: '#tour-fab', on: 'left' },
        title: 'Nuevo Gasto rápido',
        text: 'Este botón rojo siempre está visible. También podés usar <kbd>Ctrl+N</kbd> desde cualquier pantalla.',
    });

    tour.addStep({
        id: 'savings',
        attachTo: sidebarAttach('#tour-nav-savings'),
        title: 'Ahorro',
        text: 'Creá metas de ahorro con un objetivo y fecha límite. Cada depósito te acerca más a la meta.',
    });

    tour.addStep({
        id: 'categories',
        attachTo: sidebarAttach('#tour-nav-categories'),
        title: 'Categorías',
        text: 'Personalizá tus categorías con íconos y colores. Las podés organizar en grupos para ver subtotales en el dashboard.',
        buttons: [
            {
                text: 'Anterior',
                action: function () { this.back(); },
                secondary: true,
            },
            {
                text: 'Finalizar',
                action: function () { this.complete(); },
            },
        ],
    });

    tour.on('cancel', markTourDone);
    tour.on('complete', markTourDone);

    tour.start();
});

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
        attachTo: { element: '#tour-nav-dashboard', on: 'right' },
        title: 'Dashboard',
        text: 'Acá vas a ver un resumen de tus finanzas del mes: balance, gastos por categoría y evolución histórica.',
        buttons: [
            { text: 'Saltar tour', action: function () { tour.cancel(); }, secondary: true },
            { text: 'Siguiente', action: function () { this.next(); } },
        ],
    });

    tour.addStep({
        id: 'expenses',
        attachTo: { element: '#tour-nav-expenses', on: 'right' },
        title: 'Gastos',
        text: 'Registrá y filtrá todos tus gastos. Podés organizarlos por categoría, método de pago o tipo (fijo/variable).',
    });

    tour.addStep({
        id: 'fab',
        attachTo: { element: '#tour-fab', on: 'left' },
        title: 'Nuevo Gasto rápido',
        text: 'Este botón está siempre visible. También podés usar <kbd>Ctrl+N</kbd> desde cualquier pantalla.',
    });

    tour.addStep({
        id: 'savings',
        attachTo: { element: '#tour-nav-savings', on: 'right' },
        title: 'Ahorro',
        text: 'Creá metas de ahorro con un objetivo y fecha límite. Cada depósito te acerca más a la meta.',
    });

    tour.addStep({
        id: 'categories',
        attachTo: { element: '#tour-nav-categories', on: 'right' },
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

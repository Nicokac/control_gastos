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

    function sidebarAttach(elementId) {
        return window.innerWidth < 768 ? null : { element: elementId, on: 'right' };
    }

    const btnAnterior = { text: 'Anterior', action: function () { this.back(); }, secondary: true };
    const btnSiguiente = { text: 'Siguiente', action: function () { this.next(); } };

    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: { behavior: 'smooth', block: 'center' },
            classes: 'shepherd-theme-arrows',
            buttons: [btnAnterior, btnSiguiente],
        },
    });

    // 1 — Dashboard
    tour.addStep({
        id: 'dashboard',
        attachTo: sidebarAttach('#tour-nav-dashboard'),
        title: 'Dashboard',
        text: 'Tu panorama financiero del mes: balance, distribución de gastos por categoría y evolución mensual. También podés ver el Reporte Anual para comparar todos los meses del año.',
        buttons: [
            { text: 'Saltar tour', action: function () { tour.cancel(); }, secondary: true },
            btnSiguiente,
        ],
    });

    // 2 — Gastos
    tour.addStep({
        id: 'expenses',
        attachTo: sidebarAttach('#tour-nav-expenses'),
        title: 'Gastos',
        text: 'Registrá cada gasto con categoría, método de pago y tipo (fijo/variable). Filtrá por mes, buscá por descripción y exportá a Excel.',
    });

    // 3 — Ingresos
    tour.addStep({
        id: 'income',
        attachTo: sidebarAttach('#tour-nav-income'),
        title: 'Ingresos',
        text: 'Llevá el registro de tus fuentes de ingreso — sueldo, freelance, alquileres. Soporte para pesos y dólares.',
    });

    // 4 — FAB
    tour.addStep({
        id: 'fab',
        attachTo: { element: '#tour-fab', on: 'left' },
        title: 'Nuevo Gasto rápido',
        text: 'Este botón rojo siempre está visible. También podés usar <kbd>Ctrl+N</kbd> desde cualquier pantalla.',
    });

    // 5 — Ahorro
    tour.addStep({
        id: 'savings',
        attachTo: sidebarAttach('#tour-nav-savings'),
        title: 'Metas de Ahorro',
        text: 'Creá metas con un objetivo y fecha límite. Podés depositar directamente desde un gasto para ir acumulando sin esfuerzo.',
    });

    // 6 — Gastos Fijos
    tour.addStep({
        id: 'recurring',
        attachTo: sidebarAttach('#tour-nav-recurring'),
        title: 'Gastos Fijos',
        text: 'Registrá servicios, impuestos y cuotas. La app te muestra cuáles pagaste este mes y cuáles están vencidos. Soporta gastos en cuotas con conteo automático.',
    });

    // 7 — Categorías
    tour.addStep({
        id: 'categories',
        attachTo: sidebarAttach('#tour-nav-categories'),
        title: 'Categorías',
        text: 'Personalizá tus categorías con íconos y colores. Organizalas en grupos para ver subtotales en el dashboard y en los reportes.',
        buttons: [
            btnAnterior,
            { text: 'Finalizar', action: function () { this.complete(); } },
        ],
    });

    tour.on('cancel', markTourDone);
    tour.on('complete', markTourDone);

    tour.start();
});

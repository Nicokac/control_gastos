// El <input type="date"> nativo se dibuja con el idioma del navegador, no de la página (DT-109):
// flatpickr muestra día/mes/año en español y sigue enviando AAAA-MM-DD al servidor.
document.addEventListener('DOMContentLoaded', function () {
    if (typeof flatpickr === 'undefined') return;

    document.querySelectorAll('input[type="date"]').forEach(function (input) {
        flatpickr(input, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            altInput: true,
            altFormat: 'd/m/Y',
            altInputClass: input.className,
            allowInput: window.matchMedia('(pointer: fine)').matches,
            disableMobile: true,
        });
    });
});

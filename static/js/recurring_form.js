document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('id_category');
    if (el && typeof TomSelect !== 'undefined') {
        new TomSelect(el, {
            placeholder: 'Buscar categoría...',
            allowEmptyOption: true,
            maxOptions: null,
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const typeSelect = document.getElementById('id_type');
    const parentSelect = document.getElementById('id_parent');
    if (!typeSelect || !parentSelect) return;

    const allOptions = Array.from(parentSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        type: opt.dataset.type || null,
    }));

    function filterParentOptions() {
        const selected = typeSelect.value;
        const currentValue = parentSelect.value;
        parentSelect.innerHTML = '';
        allOptions.forEach(({ value, text, type }) => {
            if (!type || !selected || type === selected) {
                const opt = new Option(text, value);
                parentSelect.appendChild(opt);
            }
        });
        parentSelect.value = currentValue;
        if (!parentSelect.value) parentSelect.selectedIndex = 0;
    }

    typeSelect.addEventListener('change', filterParentOptions);
    if (typeSelect.value) filterParentOptions();
});

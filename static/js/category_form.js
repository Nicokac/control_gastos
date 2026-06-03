document.addEventListener('DOMContentLoaded', function () {
    // --- Filtro de grupo padre por tipo ---
    const typeSelect = document.getElementById('id_type');
    const parentSelect = document.getElementById('id_parent');

    if (typeSelect && parentSelect) {
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
    }

    // --- Selector de color + preview ---
    const colorInput = document.getElementById('id_color');
    const nativePicker = document.getElementById('color-picker-native');
    const pickerBtn = document.getElementById('color-picker-btn');
    const hexLabel = document.getElementById('color-hex-label');
    const swatches = document.querySelectorAll('.color-swatch[data-color]');

    const previewContainer = document.getElementById('icon-color-preview');
    const previewIcon = document.getElementById('preview-icon');
    const previewName = document.getElementById('preview-name');
    const nameInput = document.getElementById('id_name');
    const iconRadios = document.querySelectorAll('input[name="icon"]');

    if (!colorInput) return;

    function updatePreview(hex) {
        if (!previewContainer || !previewIcon) return;
        previewContainer.style.backgroundColor = hex + '20';
        previewContainer.style.borderColor = hex;
        previewIcon.style.color = hex;
    }

    function applyColor(hex) {
        colorInput.value = hex;
        if (nativePicker) nativePicker.value = hex;
        if (hexLabel) hexLabel.textContent = hex;
        swatches.forEach(s => {
            s.classList.toggle('color-swatch--active', s.dataset.color === hex);
        });
        updatePreview(hex);
    }

    swatches.forEach(swatch => {
        swatch.addEventListener('click', () => applyColor(swatch.dataset.color));
    });

    if (nativePicker) {
        nativePicker.addEventListener('input', () => applyColor(nativePicker.value));
    }

    if (pickerBtn && nativePicker) {
        pickerBtn.addEventListener('click', () => nativePicker.click());
    }

    // Sincronizar ícono seleccionado con el preview
    iconRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (previewIcon && radio.value) {
                previewIcon.className = radio.value;
                previewIcon.style.color = colorInput.value || '#6c757d';
                previewIcon.style.fontSize = '1.25rem';
            }
        });
    });

    // Sincronizar nombre con el preview
    if (nameInput && previewName) {
        nameInput.addEventListener('input', () => {
            previewName.textContent = nameInput.value || 'Nombre de la categoría';
        });
    }

    // Marcar el color activo inicial
    const initial = colorInput.value || '#6c757d';
    applyColor(initial);

    // Tooltips en grilla de íconos
    document.querySelectorAll('.icon-grid [data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el, { trigger: 'hover' });
    });
});

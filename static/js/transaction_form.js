/**
 * Control de Gastos - Transaction Form JavaScript
 *
 * Lógica compartida para formularios de gastos e ingresos.
 *
 * Uso:
 *   initTransactionForm("expenseForm")
 *   initTransactionForm("incomeForm")
 */

/**
 * Inicializa todas las funcionalidades del formulario de transacción.
 * @param {string} formId - ID del formulario ("expenseForm" o "incomeForm")
 */
function initTransactionForm(formId) {
    initExchangeRateToggle();
    initFormValidation(formId);
    initClearValidation();
}

/**
 * Toggle del campo exchange rate según la moneda seleccionada
 *
 * - USD: muestra el campo y lo habilita
 * - ARS: oculta el campo, lo deshabilita y limpia el valor
 */
function initExchangeRateToggle() {
    const currencySelect = document.getElementById('id_currency');
    const exchangeRateField = document.getElementById('exchangeRateField');
    const exchangeRateInput = document.getElementById('id_exchange_rate');

    if (!currencySelect || !exchangeRateField || !exchangeRateInput) return;

    function toggleExchangeRate() {
        const isUSD = currencySelect.value === 'USD';

        // Toggle visibilidad con d-none de Bootstrap
        exchangeRateField.classList.toggle('d-none', !isUSD);

        // Deshabilitar input cuando es ARS (no se envía al servidor)
        exchangeRateInput.disabled = !isUSD;

        // Limpiar valor cuando cambia a ARS
        if (!isUSD) {
            exchangeRateInput.value = '';
        }

        // Focus en el campo si es USD y está vacío
        if (isUSD && !exchangeRateInput.value) {
            exchangeRateInput.focus();
        }
    }

    currencySelect.addEventListener('change', toggleExchangeRate);

    // Estado inicial
    toggleExchangeRate();
}

/**
 * Validación del formulario antes de enviar
 * @param {string} formId - ID del formulario
 */
function initFormValidation(formId) {
    const form = document.getElementById(formId);

    if (!form) return;

    form.addEventListener('submit', function(e) {
        const amount = document.getElementById('id_amount');
        const categoryRadio = document.querySelector('input[name="category"]:checked');
        const categorySelect = document.getElementById('id_category');
        const categoryValue = categorySelect ? categorySelect.value : (categoryRadio ? categoryRadio.value : '');
        const description = document.getElementById('id_description');

        let isValid = true;
        let firstError = null;

        // Validar monto
        if (!amount.value || parseFloat(amount.value) <= 0) {
            amount.classList.add('is-invalid');
            isValid = false;
            firstError = firstError || amount;
        } else {
            amount.classList.remove('is-invalid');
        }

        // Validar categoría
        if (!categoryValue) {
            const categoryGrid = document.querySelector('.category-grid');
            if (categorySelect) {
                categorySelect.classList.add('is-invalid');
            } else if (categoryGrid) {
                categoryGrid.classList.add('border', 'border-danger', 'rounded', 'p-2');
            }
            isValid = false;
            firstError = firstError || categorySelect || categoryGrid;
        } else if (categorySelect) {
            categorySelect.classList.remove('is-invalid');
        }

        // Validar descripción solo si está requerida en el formulario
        if (description && description.required && !description.value.trim()) {
            description.classList.add('is-invalid');
            isValid = false;
            firstError = firstError || description;
        } else if (description) {
            description.classList.remove('is-invalid');
        }

        // Validar exchange rate si es USD
        const currency = document.getElementById('id_currency');
        const exchangeRate = document.getElementById('id_exchange_rate');

        if (currency && currency.value === 'USD') {
            if (!exchangeRate.value || parseFloat(exchangeRate.value) <= 0) {
                exchangeRate.classList.add('is-invalid');
                isValid = false;
                firstError = firstError || exchangeRate;
            } else {
                exchangeRate.classList.remove('is-invalid');
            }
        }

        if (!isValid) {
            e.preventDefault();

            // Mostrar toast de error
            if (typeof showToast === 'function') {
                showToast('Por favor completá todos los campos requeridos', 'danger');
            }

            if (firstError && firstError.focus) {
                firstError.focus();
            } else if (firstError && firstError.scrollIntoView) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
}

/**
 * Limpiar validación visual al cambiar valores
 */
function initClearValidation() {
    // Limpiar error de monto al escribir
    const amount = document.getElementById('id_amount');
    if (amount) {
        amount.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }

    // Limpiar error de descripción al escribir
    const description = document.getElementById('id_description');
    if (description) {
        description.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }

    // Limpiar error de categoría al seleccionar
    const categoryRadios = document.querySelectorAll('input[name="category"]');
    categoryRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const categoryGrid = document.querySelector('.category-grid');
            if (categoryGrid) {
                categoryGrid.classList.remove('border', 'border-danger', 'rounded', 'p-2');
            }
        });
    });

    const categorySelect = document.getElementById('id_category');
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            this.classList.remove('is-invalid');
        });
    }

    // Limpiar error de exchange rate al escribir
    const exchangeRate = document.getElementById('id_exchange_rate');
    if (exchangeRate) {
        exchangeRate.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }
}

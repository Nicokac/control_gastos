/**
 * Control de Gastos - Income Form JavaScript
 * 
 * Funcionalidades:
 * - Toggle de exchange rate según moneda
 * - Validación client-side
 */

document.addEventListener('DOMContentLoaded', function() {
    initExchangeRateToggle();
    initFormValidation();
    initClearValidation();
});

/**
 * Toggle del campo exchange rate según la moneda seleccionada
 */
function initExchangeRateToggle() {
    const currencySelect = document.getElementById('id_currency');
    const exchangeRateField = document.getElementById('exchangeRateField');
    
    if (!currencySelect || !exchangeRateField) return;
    
    function toggleExchangeRate() {
        if (currencySelect.value === 'USD') {
            exchangeRateField.classList.add('show');
        } else {
            exchangeRateField.classList.remove('show');
        }
    }
    
    currencySelect.addEventListener('change', toggleExchangeRate);
    toggleExchangeRate();
}

/**
 * Validación del formulario antes de enviar
 */
function initFormValidation() {
    const form = document.getElementById('incomeForm');
    
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        const amount = document.getElementById('id_amount');
        const category = document.querySelector('input[name="category"]:checked');
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
        if (!category) {
            const categoryGrid = document.querySelector('.category-grid');
            if (categoryGrid) {
                categoryGrid.classList.add('border', 'border-danger', 'rounded', 'p-2');
            }
            isValid = false;
            firstError = firstError || categoryGrid;
        }
        
        // Validar descripción
        if (!description.value.trim()) {
            description.classList.add('is-invalid');
            isValid = false;
            firstError = firstError || description;
        } else {
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
            if (firstError && firstError.focus) {
                firstError.focus();
            }
        }
    });
}

/**
 * Limpiar validación visual al cambiar valores
 */
function initClearValidation() {
    const amount = document.getElementById('id_amount');
    if (amount) {
        amount.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }
    
    const description = document.getElementById('id_description');
    if (description) {
        description.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }
    
    const categoryRadios = document.querySelectorAll('input[name="category"]');
    categoryRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const categoryGrid = document.querySelector('.category-grid');
            if (categoryGrid) {
                categoryGrid.classList.remove('border', 'border-danger', 'rounded', 'p-2');
            }
        });
    });
    
    const exchangeRate = document.getElementById('id_exchange_rate');
    if (exchangeRate) {
        exchangeRate.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    }
}
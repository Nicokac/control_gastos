// Carga rápida de gastos: interpreta "15000 super débito", muestra una vista previa y guarda al confirmar.
document.addEventListener('DOMContentLoaded', function () {
    const root = document.getElementById('quickExpense');
    if (!root) return;

    const inputForm = document.getElementById('quickExpenseInput');
    const textInput = document.getElementById('quickExpenseText');
    const errorBox = document.getElementById('quickExpenseError');
    const preview = document.getElementById('quickExpensePreview');
    const categorySelect = document.getElementById('quickExpenseCategory');
    const submitButton = inputForm.querySelector('button[type="submit"]');
    const csrfToken = preview.querySelector('input[name="csrfmiddlewaretoken"]').value;
    // Starts disabled in the HTML so Enter can't submit the bare form before this script runs.
    submitButton.disabled = false;

    function part(name) {
        return preview.querySelector('[data-preview="' + name + '"]');
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');
        preview.classList.add('d-none');
    }

    function hidePreview() {
        preview.classList.add('d-none');
        errorBox.classList.add('d-none');
        textInput.focus();
    }

    function setOptional(name, text) {
        const el = part(name);
        el.textContent = text || '';
        el.classList.toggle('d-none', !text);
    }

    function fillPreview(data) {
        ['amount', 'currency', 'exchange_rate', 'date', 'payment_method', 'description'].forEach(function (field) {
            preview.elements[field].value = data[field] || '';
        });
        part('amount').textContent = data.amount_display;
        part('date').textContent = data.date_display;
        setOptional('conversion', data.conversion_display);
        setOptional('payment', data.payment_method_display);
        setOptional('description', data.description ? '“' + data.description + '”' : '');

        const hint = part('category-hint');
        const hasOption = data.category_id && categorySelect.querySelector('option[value="' + data.category_id + '"]');
        categorySelect.value = hasOption ? String(data.category_id) : '';
        categorySelect.classList.toggle('is-invalid', !hasOption);
        if (hasOption) {
            hint.textContent = data.category_source === 'historial'
                ? 'Sugerida por tus gastos anteriores.'
                : 'Sugerida por el nombre de la categoría.';
        } else {
            hint.textContent = 'No pude adivinar la categoría: elegila para guardar.';
        }
        hint.classList.remove('d-none');

        const params = new URLSearchParams({ from_quick: '1' });
        ['amount', 'currency', 'exchange_rate', 'date', 'payment_method', 'description'].forEach(function (field) {
            if (data[field]) params.set(field, data[field]);
        });
        if (hasOption) params.set('category', data.category_id);
        part('full-form').href = root.dataset.fullFormUrl + '?' + params.toString();

        errorBox.classList.add('d-none');
        preview.classList.remove('d-none');
        (hasOption ? preview.querySelector('button[type="submit"]') : categorySelect).focus();
    }

    inputForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const text = textInput.value.trim();
        if (!text) {
            showError('Escribí el gasto, por ejemplo: 15000 super débito.');
            return;
        }
        submitButton.disabled = true;
        fetch(root.dataset.parseUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ text: text }),
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.ok) fillPreview(data);
                else showError(data.error);
            })
            .catch(function () { showError('No pudimos interpretar el gasto. Probá de nuevo.'); })
            .finally(function () { submitButton.disabled = false; });
    });

    categorySelect.addEventListener('change', function () {
        categorySelect.classList.toggle('is-invalid', !categorySelect.value);
        const link = part('full-form');
        const url = new URL(link.href, window.location.origin);
        if (categorySelect.value) url.searchParams.set('category', categorySelect.value);
        else url.searchParams.delete('category');
        link.href = url.pathname + url.search;
    });

    part('cancel').addEventListener('click', hidePreview);
    preview.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') hidePreview();
    });
});

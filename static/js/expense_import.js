document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('import-data');
    if (!container) return;

    const QUICK_CREATE_URL = container.dataset.quickCreateUrl;
    const CSRF = container.dataset.csrf;
    const rows = JSON.parse(container.dataset.rows);

    const table = document.getElementById('preview-table');
    const jsonInput = document.getElementById('rows-json-input');
    const checkAll = document.getElementById('check-all');
    const btnConfirm = document.getElementById('btn-confirm');
    const selectedCountBadge = document.getElementById('selected-count');
    const categorizedCountEl = document.getElementById('categorized-count');
    const includedCountEl = document.getElementById('included-count');

    const tomSelects = [];
    table.querySelectorAll('.row-category').forEach(function (sel) {
        const ts = new TomSelect(sel, {
            placeholder: '-- Sin categoría --',
            allowEmptyOption: true,
            maxOptions: 200,
        });
        tomSelects.push(ts);
        ts.on('change', updateCounters);
    });

    function updateCounters() {
        const checks = Array.from(table.querySelectorAll('.row-check'));
        const included = checks.filter(function (c) { return c.checked; }).length;
        const categorized = checks.filter(function (c, i) {
            if (!c.checked) return false;
            const ts = tomSelects[i];
            return ts && ts.getValue() !== '';
        }).length;

        selectedCountBadge.textContent = included;
        categorizedCountEl.textContent = categorized;
        includedCountEl.textContent = included;

        btnConfirm.disabled = included === 0 || categorized < included;
    }

    checkAll.addEventListener('change', function () {
        table.querySelectorAll('.row-check').forEach(function (cb) {
            cb.checked = checkAll.checked;
        });
        updateCounters();
    });

    table.addEventListener('change', function (e) {
        if (e.target.classList.contains('row-check')) {
            const allChecked = Array.from(table.querySelectorAll('.row-check')).every(function (c) {
                return c.checked;
            });
            checkAll.checked = allChecked;
            updateCounters();
        }
    });

    document.getElementById('confirm-form').addEventListener('submit', function () {
        const result = [];
        table.querySelectorAll('tbody tr').forEach(function (tr, i) {
            const checked = tr.querySelector('.row-check').checked;
            const description = tr.querySelector('.row-description').value;
            const ts = tomSelects[i];
            const categoryPk = ts ? ts.getValue() : '';
            result.push({
                include: checked,
                date: rows[i].date,
                description: description,
                amount: rows[i].amount,
                currency: rows[i].currency,
                category_pk: categoryPk,
            });
        });
        jsonInput.value = JSON.stringify(result);
    });

    const modal = new bootstrap.Modal(document.getElementById('modalNuevaCat'));
    const modalParent = document.getElementById('modal-parent');
    const modalName = document.getElementById('modal-name');
    const modalError = document.getElementById('modal-error');
    const modalSave = document.getElementById('modal-save');
    let targetTomSelect = null;

    table.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-new-cat');
        if (!btn) return;
        const tr = btn.closest('tr');
        const idx = parseInt(tr.dataset.idx, 10);
        targetTomSelect = tomSelects[idx];
        modalName.value = '';
        modalError.textContent = '';
        modalError.classList.add('d-none');
        modal.show();
        setTimeout(function () { modalName.focus(); }, 300);
    });

    modalSave.addEventListener('click', async function () {
        const parentPk = modalParent.value;
        const name = modalName.value.trim();
        modalError.classList.add('d-none');

        if (!parentPk || !name) {
            modalError.textContent = 'Completá el grupo y el nombre.';
            modalError.classList.remove('d-none');
            return;
        }

        modalSave.disabled = true;
        try {
            const res = await fetch(QUICK_CREATE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
                body: JSON.stringify({ parent_pk: parseInt(parentPk, 10), name: name }),
            });
            const data = await res.json();
            if (!res.ok) {
                modalError.textContent = data.error || 'Error al crear la categoría.';
                modalError.classList.remove('d-none');
                return;
            }

            tomSelects.forEach(function (ts) {
                ts.addOption({ value: String(data.pk), text: data.label });
                ts.refreshOptions(false);
            });

            if (targetTomSelect) {
                targetTomSelect.setValue(String(data.pk));
            }

            modal.hide();
            updateCounters();
        } catch {
            modalError.textContent = 'Error de conexión.';
            modalError.classList.remove('d-none');
        } finally {
            modalSave.disabled = false;
        }
    });

    modalName.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') modalSave.click();
    });

    updateCounters();
});

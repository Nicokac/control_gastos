document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('import-data');
    if (!container) return;

    const QUICK_CREATE_URL = container.dataset.quickCreateUrl;
    const EXCHANGE_RATE_URL = container.dataset.exchangeRateUrl;
    const CSRF = container.dataset.csrf;
    const rows = JSON.parse(container.dataset.rows);
    const previewHash = container.dataset.previewHash;

    const table = document.getElementById('preview-table');
    const jsonInput = document.getElementById('rows-json-input');
    const checkAll = document.getElementById('check-all');
    const btnConfirm = document.getElementById('btn-confirm');
    const selectedCountBadge = document.getElementById('selected-count');
    const categorizedCountEl = document.getElementById('categorized-count');
    const includedCountEl = document.getElementById('included-count');
    const usdRateInput = document.getElementById('usd-exchange-rate');

    const PROGRESS_KEY = previewHash ? 'expense_import_progress_' + previewHash : null;

    function saveProgress() {
        if (!PROGRESS_KEY) return;
        const state = [];
        table.querySelectorAll('tbody tr').forEach(function (tr, i) {
            state.push({
                include: tr.querySelector('.row-check').checked,
                category_pk: tomSelects[i] ? tomSelects[i].getValue() : '',
                type: tr.querySelector('.row-type').value,
                installment_current: tr.querySelector('.row-installment-current').value,
                installment_total: tr.querySelector('.row-installment-total').value,
            });
        });
        try {
            localStorage.setItem(PROGRESS_KEY, JSON.stringify(state));
        } catch {}
    }

    function loadProgress() {
        if (!PROGRESS_KEY) return null;
        try {
            const raw = localStorage.getItem(PROGRESS_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    }

    function clearProgress() {
        if (!PROGRESS_KEY) return;
        try {
            localStorage.removeItem(PROGRESS_KEY);
        } catch {}
    }

    if (usdRateInput && EXCHANGE_RATE_URL) {
        fetch(EXCHANGE_RATE_URL)
            .then(function (res) { return res.ok ? res.json() : null; })
            .then(function (data) {
                if (data && data.venta && !usdRateInput.value) {
                    usdRateInput.value = data.venta;
                    updateCounters();
                }
            })
            .catch(function () {});
        usdRateInput.addEventListener('input', updateCounters);
    }

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

    function toggleInstallmentFields(tr) {
        const typeSelect = tr.querySelector('.row-type');
        const fields = tr.querySelector('.row-installment-fields');
        fields.classList.toggle('d-none', typeSelect.value !== 'installment');

        const recurringMatch = tr.querySelector('.row-recurring-match');
        const matchesExisting = typeSelect.dataset.matchesRecurring === '1';
        const isRecurringType = typeSelect.value === 'fixed' || typeSelect.value === 'installment';
        recurringMatch.classList.toggle('d-none', !(matchesExisting && isRecurringType));
    }

    table.querySelectorAll('tbody tr').forEach(function (tr) {
        toggleInstallmentFields(tr);
        tr.querySelector('.row-type').addEventListener('change', function () {
            toggleInstallmentFields(tr);
            updateCounters();
        });
        tr.querySelector('.row-installment-current').addEventListener('input', updateCounters);
        tr.querySelector('.row-installment-total').addEventListener('input', updateCounters);
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

        const includedUsd = checks.some(function (c, i) {
            return c.checked && rows[i].currency === 'USD';
        });
        const rateValid = !usdRateInput || parseFloat(usdRateInput.value) > 0;

        const rowsEls = Array.from(table.querySelectorAll('tbody tr'));
        const invalidInstallment = rowsEls.some(function (tr, i) {
            if (!checks[i].checked) return false;
            if (tr.querySelector('.row-type').value !== 'installment') return false;
            const current = tr.querySelector('.row-installment-current').value;
            const total = tr.querySelector('.row-installment-total').value;
            return !current || !total;
        });

        btnConfirm.disabled =
            included === 0 ||
            categorized < included ||
            (includedUsd && !rateValid) ||
            invalidInstallment;

        saveProgress();
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
        clearProgress();
        const usdRate = usdRateInput ? usdRateInput.value : '';
        const result = [];
        table.querySelectorAll('tbody tr').forEach(function (tr, i) {
            const checked = tr.querySelector('.row-check').checked;
            const description = tr.querySelector('.row-description').value;
            const ts = tomSelects[i];
            const categoryPk = ts ? ts.getValue() : '';
            const type = tr.querySelector('.row-type').value;
            result.push({
                include: checked,
                date: rows[i].date,
                description: description,
                amount: rows[i].amount,
                currency: rows[i].currency,
                category_pk: categoryPk,
                exchange_rate: rows[i].currency === 'USD' ? usdRate : '',
                type: type,
                installment_current: type === 'installment' ? tr.querySelector('.row-installment-current').value : '',
                installment_total: type === 'installment' ? tr.querySelector('.row-installment-total').value : '',
            });
        });
        jsonInput.value = JSON.stringify(result);
    });

    const modal = new bootstrap.Modal(document.getElementById('modalNuevaCat'));
    const modalParent = document.getElementById('modal-parent');
    const modalNewGroupWrapper = document.getElementById('modal-new-group-wrapper');
    const modalNewGroupName = document.getElementById('modal-new-group-name');
    const modalName = document.getElementById('modal-name');
    const modalError = document.getElementById('modal-error');
    const modalSave = document.getElementById('modal-save');
    let targetTomSelect = null;

    modalParent.addEventListener('change', function () {
        modalNewGroupWrapper.classList.toggle('d-none', modalParent.value !== 'new');
    });

    table.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-new-cat');
        if (!btn) return;
        const tr = btn.closest('tr');
        const idx = parseInt(tr.dataset.idx, 10);
        targetTomSelect = tomSelects[idx];
        modalParent.value = '';
        modalNewGroupWrapper.classList.add('d-none');
        modalNewGroupName.value = '';
        modalName.value = '';
        modalError.textContent = '';
        modalError.classList.add('d-none');
        modal.show();
        setTimeout(function () { modalName.focus(); }, 300);
    });

    modalSave.addEventListener('click', async function () {
        const parentPk = modalParent.value;
        const newGroupName = modalNewGroupName.value.trim();
        const name = modalName.value.trim();
        modalError.classList.add('d-none');

        if (!parentPk || !name || (parentPk === 'new' && !newGroupName)) {
            modalError.textContent = 'Completá el grupo y el nombre.';
            modalError.classList.remove('d-none');
            return;
        }

        modalSave.disabled = true;
        try {
            const payload = { parent_pk: parentPk === 'new' ? 'new' : parseInt(parentPk, 10), name: name };
            if (parentPk === 'new') payload.new_group_name = newGroupName;

            const res = await fetch(QUICK_CREATE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
                body: JSON.stringify(payload),
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

            if (parentPk === 'new') {
                const newGroupOption = document.createElement('option');
                newGroupOption.value = String(data.parent_pk);
                newGroupOption.textContent = data.parent_name;
                modalParent.insertBefore(newGroupOption, modalParent.querySelector('option[value="new"]'));
            }

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

    const savedProgress = loadProgress();
    if (savedProgress && savedProgress.length === tomSelects.length) {
        const rowsEls = table.querySelectorAll('tbody tr');
        savedProgress.forEach(function (state, i) {
            const tr = rowsEls[i];
            if (!tr) return;
            tr.querySelector('.row-check').checked = !!state.include;
            if (tomSelects[i] && state.category_pk) tomSelects[i].setValue(state.category_pk, true);
            if (state.type) {
                tr.querySelector('.row-type').value = state.type;
                toggleInstallmentFields(tr);
            }
            if (state.installment_current) tr.querySelector('.row-installment-current').value = state.installment_current;
            if (state.installment_total) tr.querySelector('.row-installment-total').value = state.installment_total;
        });
        const banner = document.getElementById('progress-restored-banner');
        if (banner) banner.classList.remove('d-none');
        checkAll.checked = Array.from(table.querySelectorAll('.row-check')).every(function (c) {
            return c.checked;
        });
    }

    const closeBanner = document.getElementById('progress-restored-close');
    if (closeBanner) {
        closeBanner.addEventListener('click', function () {
            document.getElementById('progress-restored-banner').classList.add('d-none');
        });
    }

    updateCounters();
});

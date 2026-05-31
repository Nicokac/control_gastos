const INCOME_SUMMARY_KEY = 'income_summary_open';

document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('deleteIncomeModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function (e) {
            const btn = e.relatedTarget;
            document.getElementById('deleteIncomeDescription').textContent = btn.dataset.description;
            document.getElementById('deleteIncomeForm').action = btn.dataset.deleteUrl;
        });
    }

    const collapse = document.getElementById('incomeSummaryDetail');
    if (collapse) {
        const chevron = document.querySelector('.income-summary-toggle .summary-chevron');
        function setChevron(open) {
            if (chevron) chevron.style.transform = open ? 'rotate(180deg)' : '';
        }

        // Restaurar estado desde localStorage
        const isOpen = localStorage.getItem(INCOME_SUMMARY_KEY) === 'true';
        if (isOpen) {
            collapse.classList.add('show');
        }
        setChevron(isOpen);

        // Persistir estado al toggle
        collapse.addEventListener('shown.bs.collapse', function () {
            localStorage.setItem(INCOME_SUMMARY_KEY, 'true');
            setChevron(true);
        });
        collapse.addEventListener('hidden.bs.collapse', function () {
            localStorage.setItem(INCOME_SUMMARY_KEY, 'false');
            setChevron(false);
        });
    }
});

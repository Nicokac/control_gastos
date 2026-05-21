document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('deleteIncomeModal');
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function (e) {
        const btn = e.relatedTarget;
        document.getElementById('deleteIncomeDescription').textContent = btn.dataset.description;
        document.getElementById('deleteIncomeForm').action = btn.dataset.deleteUrl;
    });
});

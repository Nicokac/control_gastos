document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('deleteExpenseModal');
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function (e) {
        const btn = e.relatedTarget;
        document.getElementById('deleteExpenseDescription').textContent = btn.dataset.description;
        document.getElementById('deleteExpenseForm').action = btn.dataset.deleteUrl;
    });
});

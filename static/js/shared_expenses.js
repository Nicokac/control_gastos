document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('deleteModal');
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function (e) {
        var btn = e.relatedTarget;
        document.getElementById('deleteDescription').textContent = btn.dataset.description;
        document.getElementById('deleteForm').action = btn.dataset.deleteUrl;
    });
});

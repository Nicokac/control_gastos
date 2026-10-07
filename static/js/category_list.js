document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.category-search').forEach(function (input) {
        const containerId = input.dataset.target;
        const container = document.getElementById(containerId);
        const clearBtn = input.closest('.input-group').querySelector('.category-search-clear');
        if (!container) return;

        function filter(q) {
            container.querySelectorAll('[data-group-id]').forEach(function (groupEl) {
                const groupName = groupEl.dataset.groupName || '';
                const groupMatch = !q || groupName.includes(q);
                const subItems = groupEl.querySelectorAll('[data-sub-name]');
                let anySubMatch = false;

                subItems.forEach(function (subEl) {
                    const subName = subEl.dataset.subName || '';
                    const match = !q || groupMatch || subName.includes(q);
                    subEl.style.display = match ? '' : 'none';
                    if (match) anySubMatch = true;
                });

                const visible = !q || groupMatch || anySubMatch;
                groupEl.style.display = visible ? '' : 'none';

                if (q && visible) {
                    const collapseEl = groupEl.querySelector('.collapse');
                    if (collapseEl && !collapseEl.classList.contains('show')) {
                        collapseEl.classList.add('show');
                    }
                }
            });
        }

        input.addEventListener('input', function () {
            filter(this.value.trim().toLowerCase());
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                input.value = '';
                filter('');
                input.focus();
            });
        }
    });

    document.querySelectorAll('.category-toggle-hidden').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const pk = btn.dataset.pk;
            const isHidden = btn.dataset.hidden === 'true';
            const action = isHidden ? 'unhide' : 'hide';

            fetch(`/categories/${pk}/${action}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
            }).then(function (res) {
                if (res.ok) {
                    window.location.reload();
                } else if (typeof showToast === 'function') {
                    showToast('No se pudo actualizar la categoría.', 'danger');
                }
            }).catch(function () {
                if (typeof showToast === 'function') {
                    showToast('Error al actualizar la categoría.', 'danger');
                }
            });
        });
    });
});

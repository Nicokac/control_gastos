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
});

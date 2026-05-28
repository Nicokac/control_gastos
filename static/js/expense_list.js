document.addEventListener('DOMContentLoaded', function () {
    // Modal eliminar
    const modal = document.getElementById('deleteExpenseModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function (e) {
            const btn = e.relatedTarget;
            document.getElementById('deleteExpenseDescription').textContent = btn.dataset.description;
            document.getElementById('deleteExpenseForm').action = btn.dataset.deleteUrl;
        });
    }

    // Donut chart de categorías
    initExpenseDonut();
});

function initExpenseDonut() {
    const canvas = document.getElementById('expenseDonutChart');
    if (!canvas) return;

    const labels = JSON.parse(document.getElementById('expense-donut-labels').textContent);
    const data = JSON.parse(document.getElementById('expense-donut-data').textContent);
    const colors = JSON.parse(document.getElementById('expense-donut-colors').textContent);
    const pks = JSON.parse(document.getElementById('expense-donut-pks').textContent);

    if (!data.length) return;

    const params = new URLSearchParams(window.location.search);

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff',
                hoverOffset: 6,
            }]
        },
        options: {
            cutout: '68%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                            return ' ' + formatARS(ctx.parsed) + ' (' + pct + '%)';
                        }
                    }
                }
            },
            onClick: function (evt, elements) {
                if (!elements.length) return;
                const idx = elements[0].index;
                const pk = pks[idx];
                const newParams = new URLSearchParams(params);
                newParams.set('category', pk);
                newParams.delete('subcategory');
                window.location.search = newParams.toString();
            },
            onHover: function (evt, elements) {
                evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
            }
        }
    });
}

function formatARS(value) {
    return '$ ' + value.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

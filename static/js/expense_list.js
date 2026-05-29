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

    // El donut se inicializa cuando el collapse se abre por primera vez
    const collapse = document.getElementById('expenseSummaryDetail');
    if (collapse) {
        collapse.addEventListener('shown.bs.collapse', function () {
            initExpenseDonut();
            initLegendFade();
        }, { once: true });
    }
});

function initExpenseDonut() {
    const canvas = document.getElementById('expenseDonutChart');
    if (!canvas) return;

    const labelsEl = document.getElementById('expense-donut-labels');
    if (!labelsEl) return;

    const labels = JSON.parse(labelsEl.textContent);
    const data = JSON.parse(document.getElementById('expense-donut-data').textContent);
    const colors = JSON.parse(document.getElementById('expense-donut-colors').textContent);
    const pks = JSON.parse(document.getElementById('expense-donut-pks').textContent);

    if (!data.length) return;

    const totalLabel = document.getElementById('expenseDonutLabel');
    const totalVal = document.getElementById('expenseDonutTotal');
    const originalTotal = totalVal ? totalVal.textContent : '';
    const params = new URLSearchParams(window.location.search);
    let selectedIndex = null;

    const chart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff',
                hoverOffset: 8,
            }]
        },
        options: {
            cutout: '68%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    position: 'nearest',
                    callbacks: {
                        label: function (ctx) {
                            const total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                            return ' ' + formatARS(ctx.parsed) + ' (' + pct + '%)';
                        }
                    }
                }
            },
            onClick: function (evt, elements) {
                if (!elements.length) {
                    // click en zona vacía → deseleccionar
                    if (selectedIndex !== null) {
                        resetSelection();
                    }
                    return;
                }
                const idx = elements[0].index;
                if (selectedIndex === idx) {
                    // segundo click en la misma porción → deseleccionar
                    resetSelection();
                    return;
                }
                selectedIndex = idx;
                highlightSlice(idx);

                const pk = pks[idx];
                const newParams = new URLSearchParams(params);
                newParams.set('category', pk);
                newParams.delete('subcategory');
                window.location.search = newParams.toString();
            },
            onHover: function (evt, elements) {
                evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                if (!elements.length) return;
                const idx = elements[0].index;
                if (totalLabel) totalLabel.textContent = labels[idx];
                if (totalVal) totalVal.textContent = formatARS(data[idx]);
            }
        }
    });

    // Restaurar centro al salir del canvas
    canvas.addEventListener('mouseleave', function () {
        if (selectedIndex === null) {
            if (totalLabel) totalLabel.textContent = 'Total';
            if (totalVal) totalVal.textContent = originalTotal;
        }
    });

    function highlightSlice(idx) {
        const bgColors = colors.map(function (c, i) {
            return i === idx ? c : hexToRgba(c, 0.3);
        });
        chart.data.datasets[0].backgroundColor = bgColors;
        chart.update();
        if (totalLabel) totalLabel.textContent = labels[idx];
        if (totalVal) totalVal.textContent = formatARS(data[idx]);
    }

    function resetSelection() {
        selectedIndex = null;
        chart.data.datasets[0].backgroundColor = colors;
        chart.update();
        if (totalLabel) totalLabel.textContent = 'Total';
        if (totalVal) totalVal.textContent = originalTotal;
    }
}

function initLegendFade() {
    const legend = document.getElementById('expenseGroupLegend');
    const fade = document.getElementById('expenseLegendFade');
    if (!legend || !fade) return;

    function updateFade() {
        const atBottom = legend.scrollHeight - legend.scrollTop <= legend.clientHeight + 2;
        fade.style.display = atBottom ? 'none' : 'block';
    }

    updateFade();
    legend.addEventListener('scroll', updateFade);
}

function formatARS(value) {
    return '$ ' + Number(value).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
}

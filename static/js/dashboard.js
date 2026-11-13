document.addEventListener('DOMContentLoaded', function () {
    initDonutChart();
    initAmountsToggle();
});

function initAmountsToggle() {
    const STORAGE_KEY = 'dashboard_amounts_hidden';
    const btn = document.getElementById('toggle-amounts-btn');
    const icon = document.getElementById('toggle-amounts-icon');
    if (!btn || !icon) return;

    function applyState(hidden) {
        document.body.classList.toggle('amounts-hidden', hidden);
        icon.classList.toggle('bi-eye', !hidden);
        icon.classList.toggle('bi-eye-slash', hidden);
        btn.title = hidden ? 'Mostrar montos' : 'Ocultar montos';
    }

    let hidden = false;
    try {
        hidden = localStorage.getItem(STORAGE_KEY) === '1';
    } catch {}
    applyState(hidden);

    btn.addEventListener('click', function () {
        hidden = !hidden;
        applyState(hidden);
        try {
            localStorage.setItem(STORAGE_KEY, hidden ? '1' : '0');
        } catch {}
    });
}

function initDonutChart() {
    const ctx = document.getElementById('expenseChart');
    if (!ctx) return;

    try {
        const labelsNode    = document.getElementById('chart-labels-data');
        const valuesNode    = document.getElementById('chart-values-data');
        const colorsNode    = document.getElementById('chart-colors-data');
        const totalNode     = document.getElementById('chart-grand-total-data');

        if (!labelsNode || !valuesNode || !colorsNode) return;

        const labels = JSON.parse(labelsNode.textContent);
        const data   = JSON.parse(valuesNode.textContent);
        const colors = JSON.parse(colorsNode.textContent);
        const grandTotal = totalNode ? JSON.parse(totalNode.textContent) : null;

        if (!labels.length || !data.length) return;

        const formatARS = value =>
            '$ ' + value.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });

        const centerTextPlugin = {
            id: 'centerText',
            afterDraw(chart) {
                if (!grandTotal) return;
                const { ctx: c, chartArea: { top, bottom, left, right } } = chart;
                const cx = (left + right) / 2;
                const cy = (top + bottom) / 2;
                const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
                c.save();
                c.textAlign = 'center';
                c.textBaseline = 'middle';
                c.fillStyle = isDark ? '#9ca3af' : '#6b7280';
                c.font = '13px system-ui, sans-serif';
                c.fillText('Total gastado', cx, cy - 14);
                c.fillStyle = '#dc3545';
                c.font = 'bold 18px system-ui, sans-serif';
                c.fillText(formatARS(grandTotal), cx, cy + 10);
                c.restore();
            },
        };

        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        new Chart(ctx, {
            type: 'doughnut',
            plugins: [centerTextPlugin],
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: isDark ? '#2c3136' : '#fff',
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return ` ${formatARS(value)} (${percentage}%)`;
                            },
                        },
                    },
                },
                cutout: '65%',
            },
        });
    } catch (e) {}
}

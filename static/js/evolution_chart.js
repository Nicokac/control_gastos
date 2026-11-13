// Gráfico de evolución mensual (dashboard y reporte anual, DT-112).
// Ingresos y gastos en barras, balance como línea recta. Un mes sin movimientos llega como null y queda como hueco.
document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('evolutionChart');
    if (!canvas || typeof Chart === 'undefined') return;

    function read(id) {
        const node = document.getElementById(id);
        return node ? JSON.parse(node.textContent) : [];
    }

    const labels = read('evolution-labels-data');
    if (!labels.length) return;
    const income = read('evolution-income-data');
    const expenses = read('evolution-expenses-data');
    const savings = read('evolution-savings-data');
    const balance = read('evolution-balance-data');
    const monthUrls = read('evolution-month-urls-data');

    const formatARS = function (value) {
        return '$ ' + Number(value).toLocaleString('es-AR', { maximumFractionDigits: 0 });
    };
    const formatCompact = function (value) {
        const abs = Math.abs(value);
        const sign = value < 0 ? '-' : '';
        if (abs >= 1000000) return sign + '$ ' + (abs / 1000000).toLocaleString('es-AR', { maximumFractionDigits: 1 }) + ' M';
        if (abs >= 1000) return sign + '$ ' + Math.round(abs / 1000) + 'k';
        return sign + '$ ' + abs;
    };

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const datasets = [
        { type: 'bar', label: 'Ingresos', data: income, backgroundColor: 'rgba(25, 135, 84, 0.75)', borderRadius: 3, order: 2 },
        { type: 'bar', label: 'Gastos', data: expenses, backgroundColor: 'rgba(220, 53, 69, 0.75)', borderRadius: 3, order: 2 },
    ];
    if (savings.some(function (v) { return v; })) {
        datasets.push({ type: 'bar', label: 'Ahorro', data: savings, backgroundColor: 'rgba(13, 202, 240, 0.75)', borderRadius: 3, order: 2 });
    }
    datasets.push({
        type: 'line',
        label: 'Balance',
        data: balance,
        borderColor: '#6f42c1',
        backgroundColor: '#6f42c1',
        borderWidth: 2,
        tension: 0,
        pointRadius: 3,
        pointHoverRadius: 5,
        order: 1,
    });

    new Chart(canvas, {
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        font: { size: 11 },
                        sort: function (a, b) { return a.datasetIndex - b.datasetIndex; },
                    },
                },
                tooltip: {
                    filter: function (item) { return item.raw !== null; },
                    callbacks: {
                        label: function (ctx) { return ' ' + ctx.dataset.label + ': ' + formatARS(ctx.raw); },
                        footer: function (items) {
                            return items.length && monthUrls.length ? 'Click para ver ese mes' : '';
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxRotation: 0, autoSkip: true },
                },
                y: {
                    grid: { color: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 11 }, maxTicksLimit: 6, callback: formatCompact },
                },
            },
            onClick: function (event, elements) {
                if (!elements.length) return;
                const url = monthUrls[elements[0].index];
                if (url) window.location.href = url;
            },
            onHover: function (event, elements) {
                event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
            },
        },
    });
});

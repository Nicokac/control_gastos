document.addEventListener('DOMContentLoaded', function () {
    initDonutChart();
    initEvolutionChart();
});

function initDonutChart() {
    const ctx = document.getElementById('expenseChart');
    if (!ctx) return;

    try {
        const labelsNode = document.getElementById('chart-labels-data');
        const valuesNode = document.getElementById('chart-values-data');
        const colorsNode = document.getElementById('chart-colors-data');

        if (!labelsNode || !valuesNode || !colorsNode) return;

        const labels = JSON.parse(labelsNode.textContent);
        const data = JSON.parse(valuesNode.textContent);
        const colors = JSON.parse(colorsNode.textContent);

        if (!labels.length || !data.length) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff',
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
                                return `$ ${value.toLocaleString('es-AR', { minimumFractionDigits: 2 })} (${percentage}%)`;
                            },
                        },
                    },
                },
                cutout: '60%',
            },
        });
    } catch (e) {}
}

function initEvolutionChart() {
    const ctx = document.getElementById('evolutionChart');
    if (!ctx) return;

    const labelsNode   = document.getElementById('evolution-labels-data');
    const incomeNode   = document.getElementById('evolution-income-data');
    const expensesNode = document.getElementById('evolution-expenses-data');
    const savingsNode  = document.getElementById('evolution-savings-data');

    if (!labelsNode || !incomeNode || !expensesNode || !savingsNode) return;

    const labels   = JSON.parse(labelsNode.textContent);
    const income   = JSON.parse(incomeNode.textContent);
    const expenses = JSON.parse(expensesNode.textContent);
    const savings  = JSON.parse(savingsNode.textContent);

    if (!labels.length) return;

    const formatARS = value =>
        '$ ' + value.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ingresos',
                    data: income,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Gastos',
                    data: expenses,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Ahorro',
                    data: savings,
                    borderColor: '#0dcaf0',
                    backgroundColor: 'rgba(13, 202, 240, 0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: ${formatARS(context.raw)}`;
                        },
                    },
                },
            },
            scales: {
                y: {
                    ticks: {
                        callback: value => formatARS(value),
                    },
                },
            },
        },
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('expenseChart');
    if (!ctx) {
        return;
    }

    try {
        const labelsNode = document.getElementById('chart-labels-data');
        const valuesNode = document.getElementById('chart-values-data');
        const colorsNode = document.getElementById('chart-colors-data');

        if (!labelsNode || !valuesNode || !colorsNode) {
            return;
        }

        const labels = JSON.parse(labelsNode.textContent);
        const data = JSON.parse(valuesNode.textContent);
        const colors = JSON.parse(colorsNode.textContent);

        if (!labels.length || !data.length) {
            return;
        }

        // Crear gráfico
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
                    legend: {
                        display: false,
                    },
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
    } catch (error) {
        // Silenciar errores de parsing en producción
    }
});

const EXPENSE_SUMMARY_KEY = 'expense_summary_open';

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

    const collapse = document.getElementById('expenseSummaryDetail');
    if (collapse) {
        // Inicializar gráficos la primera vez que se abre (o al restaurar desde localStorage)
        let chartsInitialized = false;
        function initCharts() {
            if (chartsInitialized) return;
            chartsInitialized = true;
            initExpenseDonut();
            initLegendFade();
            initExpenseDailyChart();
            initExpenseDailyBarChart();
            initExpenseMonthlyChart();
            initSmallDonut('expenseMethodDonut', 'expense-method-labels', 'expense-method-data', 'expense-method-colors');
        }

        // Restaurar estado desde localStorage
        if (localStorage.getItem(EXPENSE_SUMMARY_KEY) === 'true') {
            collapse.classList.add('show');
            initCharts();
        }

        const chevron = document.querySelector('.expense-summary-toggle .summary-chevron');
        function setChevron(open) {
            if (chevron) chevron.style.transform = open ? 'rotate(180deg)' : '';
        }

        // Estado inicial del chevron
        setChevron(localStorage.getItem(EXPENSE_SUMMARY_KEY) === 'true');

        // Persistir estado al toggle
        collapse.addEventListener('shown.bs.collapse', function () {
            localStorage.setItem(EXPENSE_SUMMARY_KEY, 'true');
            setChevron(true);
            initCharts();
        });
        collapse.addEventListener('hidden.bs.collapse', function () {
            localStorage.setItem(EXPENSE_SUMMARY_KEY, 'false');
            setChevron(false);
        });
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

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const chart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: isDark ? '#2c3136' : '#fff',
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

function initExpenseDailyChart() {
    const canvas = document.getElementById('expenseDailyChart');
    if (!canvas) return;

    const labelsEl = document.getElementById('expense-daily-labels');
    const dataEl = document.getElementById('expense-daily-data');
    if (!labelsEl || !dataEl) return;

    const labels = JSON.parse(labelsEl.textContent);
    const data = JSON.parse(dataEl.textContent);
    if (!data.length) return;

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220,53,69,0.08)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (ctx) { return 'Día ' + ctx[0].label; },
                        label: function (ctx) { return ' ' + formatARS(ctx.parsed.y); }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)' },
                    ticks: {
                        font: { size: 11 },
                        callback: function (v) { return '$ ' + Number(v).toLocaleString('es-AR', { maximumFractionDigits: 0 }); }
                    }
                }
            }
        }
    });
}

function initExpenseDailyBarChart() {
    const canvas = document.getElementById('expenseDailyBarChart');
    if (!canvas) return;

    const labelsEl = document.getElementById('expense-daily-labels');
    const dataEl = document.getElementById('expense-daily-bar-data');
    if (!labelsEl || !dataEl) return;

    const labels = JSON.parse(labelsEl.textContent);
    const data = JSON.parse(dataEl.textContent);
    if (!data.length) return;

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const metaEl = document.getElementById('expense-daily-meta');
    const meta = metaEl ? JSON.parse(metaEl.textContent) : {};
    const month = meta.month || 0;
    const year = meta.year || 0;

    function padTwo(n) { return String(n).padStart(2, '0'); }

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: 'rgba(220,53,69,0.7)',
                borderWidth: 0,
                borderRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (ctx) { return 'Día ' + ctx[0].label; },
                        label: function (ctx) {
                            if (!ctx.parsed.y) return null;
                            return ' ' + formatARS(ctx.parsed.y);
                        }
                    }
                }
            },
            onClick: function (evt, elements) {
                if (!elements.length || !month || !year) return;
                const day = labels[elements[0].index];
                if (!day) return;
                const dateStr = year + '-' + padTwo(month) + '-' + padTwo(day);
                const params = new URLSearchParams(window.location.search);
                params.set('date_from', dateStr);
                params.set('date_to', dateStr);
                window.location.search = params.toString();
            },
            onHover: function (evt, elements) {
                evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)' },
                    ticks: {
                        font: { size: 11 },
                        callback: function (v) {
                            if (v >= 1000000) return '$ ' + (v / 1000000).toFixed(1) + 'M';
                            if (v >= 1000) return '$ ' + (v / 1000).toFixed(0) + 'k';
                            return '$ ' + v;
                        }
                    }
                }
            }
        }
    });
}

function initExpenseMonthlyChart() {
    const canvas = document.getElementById('expenseMonthlyChart');
    if (!canvas) return;

    const labelsEl = document.getElementById('expense-monthly-labels');
    const datasetsEl = document.getElementById('expense-monthly-datasets');
    if (!labelsEl || !datasetsEl) return;

    const labels = JSON.parse(labelsEl.textContent);
    const rawDatasets = JSON.parse(datasetsEl.textContent);
    if (!rawDatasets.length) return;

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const datasets = rawDatasets.map(function (ds) {
        return {
            label: ds.label,
            data: ds.data,
            backgroundColor: ds.color,
            borderWidth: 0,
            borderRadius: 2,
        };
    });

    new Chart(canvas, {
        type: 'bar',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: { boxWidth: 10, font: { size: 11 }, padding: 8 }
                },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            if (!ctx.parsed.y) return null;
                            return ' ' + ctx.dataset.label + ': ' + formatARS(ctx.parsed.y);
                        }
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { font: { size: 11 } } },
                y: {
                    stacked: true,
                    grid: { color: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)' },
                    ticks: {
                        font: { size: 11 },
                        callback: function (v) {
                            if (v >= 1000000) return '$ ' + (v / 1000000).toFixed(1) + 'M';
                            if (v >= 1000) return '$ ' + (v / 1000).toFixed(0) + 'k';
                            return '$ ' + v;
                        }
                    }
                }
            }
        }
    });
}

function initSmallDonut(canvasId, labelsId, dataId, colorsId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const labelsEl = document.getElementById(labelsId);
    const dataEl = document.getElementById(dataId);
    const colorsEl = document.getElementById(colorsId);
    if (!labelsEl || !dataEl || !colorsEl) return;

    const labels = JSON.parse(labelsEl.textContent);
    const data = JSON.parse(dataEl.textContent);
    const colors = JSON.parse(colorsEl.textContent);
    if (!data.length) return;

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: isDark ? '#2c3136' : '#fff',
                hoverOffset: 4,
            }]
        },
        options: {
            cutout: '65%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                            return ' ' + formatARS(ctx.parsed) + ' (' + pct + '%)';
                        }
                    }
                }
            }
        }
    });
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

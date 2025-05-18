
// Initialize Lucide icons
lucide.createIcons();

// Initialize date range picker
const dateRangePicker = flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "d/m/Y",
    locale: "vn",
    defaultDate: ["01/{{ today.month }}/{{ today.year }}", "{{ today.day }}/{{ today.month }}/{{ today.year }}"],
    maxDate: "today"
});

// Initialize charts
document.addEventListener('DOMContentLoaded', function() {
    const inventoryCtx = document.getElementById('inventoryPieChart').getContext('2d');
    const inventoryPieChart = new Chart(inventoryCtx, {
        type: 'pie',
        data: {
            labels: ['Nhập kho', 'Xuất kho'],
            datasets: [{
                data: [{{ gia_tri_nhap_kho }}, {{ gia_tri_xuat_kho }}],
                backgroundColor: ['rgba(59, 130, 246, 0.8)', 'rgba(16, 185, 129, 0.8)'],
                borderColor: ['rgba(59, 130, 246, 1)', 'rgba(16, 185, 129, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value.toLocaleString()}đ (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });

    const categoryCtx = document.getElementById('categoryPieChart').getContext('2d');
    const categoryData = {{ overview_chart_data|safe }};
    const categoryPieChart = new Chart(categoryCtx, {
        type: 'pie',
        data: {
            labels: categoryData.map(item => item.name),
            datasets: [{
                data: categoryData.map(item => item.value),
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(139, 92, 246, 0.8)'
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(16, 185, 129, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(139, 92, 246, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${Math.round(value)}%`;
                        }
                    }
                }
            }
        }
    });

    // AJAX update function
    function updateDashboard() {
        const selectedDates = dateRangePicker.selectedDates;
        if (selectedDates.length === 2) {
            const startDate = selectedDates[0].toLocaleDateString('vi-VN');
            const endDate = selectedDates[1].toLocaleDateString('vi-VN');
            const dateRange = `${startDate} to ${endDate}`;

            fetch(`/report/ajax/?dateRange=${encodeURIComponent(dateRange)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }
                    document.querySelectorAll('.metric-value.text-dark')[0].textContent = data.so_don_hang;
                    document.querySelectorAll('.metric-value.text-dark')[1].textContent = `${data.doanh_thu.toLocaleString()}đ`;
                    document.querySelectorAll('.metric-value.text-dark')[2].textContent = `${data.gia_tri_nhap_kho.toLocaleString()}đ`;

                   document.querySelectorAll('.metric-value.text-dark')[3].textContent = `${data.gia_tri_xuat_kho.toLocaleString()}đ`;
                    document.querySelector('.metric-value.text-danger').textContent = `${data.no_phai_tra.toLocaleString()}đ`;
                    document.querySelector('.metric-value.text-success').textContent = `${data.no_phai_thu.toLocaleString()}đ`;
                    document.querySelector('.progress-bar.bg-danger').style.width = `${data.no_phai_tra_progress}%`;
                    document.querySelector('.progress-bar.bg-success').style.width = `${data.no_phai_thu_progress}%`;

                    inventoryPieChart.data.datasets[0].data = [data.gia_tri_nhap_kho, data.gia_tri_xuat_kho];
                    inventoryPieChart.update();

                    categoryPieChart.data.labels = data.overview_chart_data.map(item => item.name);
                    categoryPieChart.data.datasets[0].data = data.overview_chart_data.map(item => item.value);
                    categoryPieChart.update();
                })
                .catch(error => console.error('Error fetching data:', error));
        }
    }

    document.getElementById('dateRange').addEventListener('change', updateDashboard);
    document.querySelector('.btn-primary').addEventListener('click', updateDashboard);
});

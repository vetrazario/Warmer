// Глобальные переменные для графиков
let emailsChart = null;
let campaignsChart = null;

// Функция для отображения уведомлений
function showAlert(message, type = "success") {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const alertContainer = document.getElementById("alertContainer");
    alertContainer.appendChild(alertDiv);
    
    // Автоматически скрыть уведомление через 5 секунд
    setTimeout(() => {
        alertDiv.classList.remove("show");
        setTimeout(() => alertDiv.remove(), 500);
    }, 5000);
}

// Загрузка статистики для дашборда
function loadDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при загрузке статистики');
            }
            return response.json();
        })
        .then(stats => {
            // Обновляем счетчики кампаний
            document.getElementById('total-campaigns').textContent = stats.campaigns.total;
            document.getElementById('active-campaigns').textContent = stats.campaigns.active;
            document.getElementById('paused-campaigns').textContent = stats.campaigns.paused;
            document.getElementById('completed-campaigns').textContent = stats.campaigns.completed;
            
            // Обновляем счетчики писем
            document.getElementById('total-emails').textContent = stats.emails.total;
            document.getElementById('delivered-emails').textContent = stats.emails.delivered;
            document.getElementById('replied-emails').textContent = stats.emails.replied;
            document.getElementById('spam-emails').textContent = stats.emails.spam;
            
            // Обновляем прогресс-бары
            updateProgressBar('delivery-rate', stats.emails.delivery_rate);
            updateProgressBar('reply-rate', stats.emails.reply_rate);
            updateProgressBar('spam-rate', stats.emails.spam_rate);
            
            // Обновляем прогресс-бар процента отвечающих ящиков
            // Используем среднее значение reply_rate из всех активных кампаний
            const avgReplyRate = stats.active_campaigns.length > 0 
                ? stats.active_campaigns.reduce((sum, campaign) => sum + (campaign.reply_rate || 0), 0) / stats.active_campaigns.length 
                : 0;
            updateProgressBar('responding-mailboxes-rate', Math.round(avgReplyRate));
            
            // Создаем графики
            createEmailsChart(stats.daily_stats);
            createCampaignsChart(stats.campaigns);
            
            // Обновляем список активных кампаний
            updateActiveCampaignsList(stats.active_campaigns);
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showAlert('Ошибка при загрузке статистики', 'danger');
        });
}

// Обновление прогресс-бара
function updateProgressBar(id, value) {
    const progressBar = document.getElementById(id);
    progressBar.style.width = `${value}%`;
    progressBar.textContent = `${value}%`;
    progressBar.setAttribute('aria-valuenow', value);
}

// Создание графика отправки писем
function createEmailsChart(dailyStats) {
    const ctx = document.getElementById('emailsChart').getContext('2d');
    
    // Если график уже существует, уничтожаем его
    if (emailsChart) {
        emailsChart.destroy();
    }
    
    // Подготавливаем данные для графика
    const labels = dailyStats.map(item => item.date);
    const sentData = dailyStats.map(item => item.sent);
    const deliveredData = dailyStats.map(item => item.delivered);
    
    // Создаем новый график
    emailsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Отправлено',
                    data: sentData,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Доставлено',
                    data: deliveredData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Создание графика кампаний
function createCampaignsChart(campaignsStats) {
    const ctx = document.getElementById('campaignsChart').getContext('2d');
    
    // Если график уже существует, уничтожаем его
    if (campaignsChart) {
        campaignsChart.destroy();
    }
    
    // Подготавливаем данные для графика
    const data = [
        campaignsStats.active,
        campaignsStats.paused,
        campaignsStats.completed
    ];
    
    // Создаем новый график
    campaignsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Активные', 'Приостановленные', 'Завершенные'],
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(40, 167, 69, 0.7)',
                    'rgba(255, 193, 7, 0.7)',
                    'rgba(108, 117, 125, 0.7)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Обновление списка активных кампаний
function updateActiveCampaignsList(campaigns) {
    const campaignsTable = document.getElementById('active-campaigns-table');
    
    if (campaigns.length === 0) {
        campaignsTable.innerHTML = '<tr><td colspan="8" class="text-center">Нет активных кампаний</td></tr>';
        return;
    }
    
    let html = '';
    campaigns.forEach(campaign => {
        // Форматируем даты
        const startDate = new Date(campaign.start_date).toLocaleDateString('ru-RU');
        const expectedEndDate = campaign.expected_end_date ? new Date(campaign.expected_end_date).toLocaleDateString('ru-RU') : 'Не определено';
        
        html += `
            <tr>
                <td>${campaign.name}</td>
                <td>${campaign.smtp_server_name || 'Неизвестно'}</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: ${campaign.progress}%" aria-valuenow="${campaign.progress}" aria-valuemin="0" aria-valuemax="100">${campaign.progress}%</div>
                    </div>
                </td>
                <td>${campaign.current_emails_per_day}</td>
                <td>${campaign.reply_rate || 30}%</td>
                <td>${startDate}</td>
                <td>${expectedEndDate}</td>
                <td>
                    <button class="btn btn-sm btn-warning pause-campaign" data-id="${campaign.id}">Пауза</button>
                    <a href="/campaign-stats/${campaign.id}" class="btn btn-sm btn-info">Статистика</a>
                </td>
            </tr>
        `;
    });
    
    campaignsTable.innerHTML = html;
    
    // Добавляем обработчики событий для кнопок
    document.querySelectorAll('.pause-campaign').forEach(button => {
        button.addEventListener('click', function() {
            const campaignId = this.dataset.id;
            pauseCampaign(campaignId);
        });
    });
}

// Приостановка кампании
function pauseCampaign(campaignId) {
    if (confirm('Вы уверены, что хотите приостановить эту кампанию?')) {
        fetch(`/api/campaigns/${campaignId}/pause`, {
            method: 'POST'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка при приостановке кампании');
                }
                return response.json();
            })
            .then(data => {
                showAlert(data.message, 'success');
                loadDashboardStats();
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showAlert('Ошибка при приостановке кампании', 'danger');
            });
    }
}

// Загружаем статистику при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    
    // Обновляем статистику каждые 60 секунд
    setInterval(loadDashboardStats, 60000);
}); 
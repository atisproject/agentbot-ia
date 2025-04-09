// Dashboard.js - Scripts for dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Function to format numbers with commas for thousands
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Update dashboard statistics in real-time (if needed)
    function updateDashboardStats() {
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                // Update statistics if the API endpoint is implemented
                if (data.total_leads) {
                    document.getElementById('total-leads').innerText = formatNumber(data.total_leads);
                }
                if (data.leads_convertidos) {
                    document.getElementById('leads-convertidos').innerText = formatNumber(data.leads_convertidos);
                }
                if (data.leads_novos) {
                    document.getElementById('leads-novos').innerText = formatNumber(data.leads_novos);
                }
                if (data.taxa_conversao) {
                    document.getElementById('taxa-conversao').innerText = data.taxa_conversao + '%';
                }
            })
            .catch(error => {
                console.error('Error fetching dashboard stats:', error);
            });
    }

    // Uncomment to enable auto-refresh of dashboard stats every 5 minutes
    // setInterval(updateDashboardStats, 300000);

    // Handle form submission for quick actions
    const quickActionForm = document.getElementById('quick-action-form');
    if (quickActionForm) {
        quickActionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const action = document.getElementById('quick-action').value;
            const leadId = document.getElementById('quick-action-lead').value;
            
            if (!action || !leadId) {
                alert('Por favor, selecione uma ação e um lead.');
                return;
            }
            
            // Submit the action via fetch API
            fetch('/api/quick-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: action,
                    lead_id: leadId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'sucesso') {
                    alert('Ação realizada com sucesso!');
                    // Reset form
                    quickActionForm.reset();
                } else {
                    alert('Erro: ' + data.mensagem);
                }
            })
            .catch(error => {
                console.error('Error performing quick action:', error);
                alert('Ocorreu um erro ao executar a ação. Tente novamente.');
            });
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the InsightLens page
    const analyticsContainer = document.getElementById('analytics-container');
    if (!analyticsContainer) return;
    
    // Get analytics data from the data attribute
    const analyticsDataStr = analyticsContainer.getAttribute('data-analytics');
    if (!analyticsDataStr) return;
    
    const analyticsData = JSON.parse(analyticsDataStr);
    if (!analyticsData || analyticsData.length === 0) return;
    
    // Prepare data for charts
    const campaignLabels = analyticsData.map(d => `Campaign ${d.campaign_id}`);
    const openRates = analyticsData.map(d => d.open_rate * 100); // Convert to percentage
    const responseRates = analyticsData.map(d => d.response_rate * 100); // Convert to percentage
    
    // Channel distribution data
    const channels = [...new Set(analyticsData.map(d => d.channel))];
    const channelCounts = channels.map(channel => {
        return analyticsData.filter(d => d.channel === channel).length;
    });
    
    // Compliance status data
    const complianceStatuses = [...new Set(analyticsData.map(d => d.compliance_status))];
    const complianceCounts = complianceStatuses.map(status => {
        return analyticsData.filter(d => d.compliance_status === status).length;
    });
    
    // Create engagement rates chart
    const engagementChartCtx = document.getElementById('engagement-chart').getContext('2d');
    new Chart(engagementChartCtx, {
        type: 'bar',
        data: {
            labels: campaignLabels,
            datasets: [
                {
                    label: 'Open Rate (%)',
                    data: openRates,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Response Rate (%)',
                    data: responseRates,
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Campaign Engagement Rates'
                },
                legend: {
                    position: 'top'
                }
            }
        }
    });
    
    // Create channel distribution chart
    const channelChartCtx = document.getElementById('channel-chart').getContext('2d');
    new Chart(channelChartCtx, {
        type: 'doughnut',
        data: {
            labels: channels,
            datasets: [{
                data: channelCounts,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Channel Distribution'
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    // Create compliance status chart
    const complianceChartCtx = document.getElementById('compliance-chart').getContext('2d');
    new Chart(complianceChartCtx, {
        type: 'pie',
        data: {
            labels: complianceStatuses,
            datasets: [{
                data: complianceCounts,
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 206, 86, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Compliance Status Distribution'
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    // Create flags resolved chart
    const flagsData = analyticsData.map(d => d.flags_resolved);
    const flagsChartCtx = document.getElementById('flags-chart').getContext('2d');
    new Chart(flagsChartCtx, {
        type: 'bar',
        data: {
            labels: campaignLabels,
            datasets: [{
                label: 'Flags Resolved',
                data: flagsData,
                backgroundColor: 'rgba(153, 102, 255, 0.7)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Number of Flags'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Compliance Flags Resolved'
                }
            }
        }
    });
});

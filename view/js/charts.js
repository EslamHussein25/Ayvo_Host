class ExcelChartsManager {
    constructor() {
        this.data = {};
        this.currentChart = 'overall';
        this.chart = null;
        this.init();
    }

    async init() {
        await this.loadExcelFile();
        this.setupEventListeners();
        this.displayChart(this.currentChart);
    }

    async loadExcelFile() {
        try {
            document.getElementById('charts-loading').style.display = 'block';
            document.getElementById('chart-container').style.display = 'none';
            
            const response = await fetch('../../outputFiles/models_comparison_report.xlsx');
            if (!response.ok) {
                throw new Error('Could not load Excel file');
            }
            
            const arrayBuffer = await response.arrayBuffer();
            const workbook = XLSX.read(arrayBuffer, { type: 'array' });
            
            // Process all sheets
            workbook.SheetNames.forEach(sheetName => {
                const worksheet = workbook.Sheets[sheetName];
                const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: "" });
                this.data[sheetName] = jsonData;
            });
            
            console.log('Loaded chart data from sheets:', Object.keys(this.data));
            
            document.getElementById('charts-loading').style.display = 'none';
            document.getElementById('chart-container').style.display = 'block';
            
        } catch (error) {
            console.error('Error loading Excel file:', error);
            document.getElementById('charts-loading').innerHTML = 
                '<div class="chart-error">Error loading Excel file. Please make sure "models_comparison_report.xlsx" is in the same directory.</div>';
        }
    }

    setupEventListeners() {
        document.querySelectorAll('.charts-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chartType = e.target.getAttribute('data-chart');
                this.switchChart(chartType);
            });
        });
    }

    switchChart(chartType) {
        // Update active tab
        document.querySelectorAll('.charts-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-chart="${chartType}"]`).classList.add('active');
        
        // Display the selected chart
        this.currentChart = chartType;
        this.displayChart(chartType);
    }

    displayChart(chartType) {
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        const ctx = document.getElementById('main-chart').getContext('2d');

        switch(chartType) {
            case 'overall':
                this.createOverallChart(ctx);
                break;
            case 'faithfulness':
                this.createMetricChart(ctx, 'Faithfulness Comparison', 'Faithfulness Scores');
                break;
            case 'answer-relevance':
                this.createMetricChart(ctx, 'Answer Relevance Comparison', 'Answer Relevance Scores');
                break;
            case 'context-relevance':
                this.createMetricChart(ctx, 'Context Relevance Comparison', 'Context Relevance Scores');
                break;
            case 'correctness':
                this.createMetricChart(ctx, 'correctness Comparison', 'Correctness Scores');
                break;
            case 'category-comparison':
                this.createCategoryChart(ctx);
                break;
        }
    }

    createOverallChart(ctx) {
        const overallData = this.data['Overall Score Comparison'];
        if (!overallData) {
            this.showError('Overall Score Comparison data not found');
            return;
        }

        // Get OVERALL row data
        const overallRow = overallData.find(row => 
            Object.values(row).some(val => String(val).toUpperCase().includes('OVERALL'))
        );

        if (!overallRow) {
            this.showError('Overall scores not found');
            return;
        }

        const models = Object.keys(overallRow).filter(key => key !== 'Category');
        const scores = models.map(model => parseFloat(overallRow[model]) || 0);

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: models,
                datasets: [{
                    label: 'Overall Score',
                    data: scores,
                    backgroundColor: [
                        '#3498db',
                        '#e74c3c',
                        '#f39c12',
                        '#2ecc71',
                        '#9b59b6'
                    ],
                    borderColor: [
                        '#2980b9',
                        '#c0392b',
                        '#e67e22',
                        '#27ae60',
                        '#8e44ad'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Overall Model Performance Comparison',
                        font: { size: 18, weight: 'bold' }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        title: {
                            display: true,
                            text: 'Score (0-10)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Models'
                        }
                    }
                }
            }
        });

        this.updateChartInfo('Overall Performance Comparison', 'Comparing overall scores across all LLM models');
    }

    createMetricChart(ctx, sheetName, chartTitle) {
        const metricData = this.data[sheetName];
        if (!metricData) {
            this.showError(`${sheetName} data not found`);
            return;
        }

        // Get categories (excluding OVERALL)
        const categories = metricData
            .filter(row => !Object.values(row).some(val => String(val).toUpperCase().includes('OVERALL')))
            .map(row => row.Category || Object.values(row)[0]);

        const models = Object.keys(metricData[0]).filter(key => key !== 'Category');
        
        const datasets = models.map((model, index) => ({
            label: model,
            data: metricData
                .filter(row => !Object.values(row).some(val => String(val).toUpperCase().includes('OVERALL')))
                .map(row => parseFloat(row[model]) || 0),
            backgroundColor: [
                '#3498db',
                '#e74c3c', 
                '#f39c12',
                '#2ecc71',
                '#9b59b6'
            ][index % 5] + '80',
            borderColor: [
                '#3498db',
                '#e74c3c',
                '#f39c12', 
                '#2ecc71',
                '#9b59b6'
            ][index % 5],
            borderWidth: 2
        }));

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: categories,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartTitle,
                        font: { size: 18, weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        title: {
                            display: true,
                            text: 'Score (0-10)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Categories'
                        }
                    }
                }
            }
        });

        this.updateChartInfo(chartTitle, `Performance comparison across different categories for ${chartTitle.toLowerCase()}`);
    }

    createCategoryChart(ctx) {
        const modelData = this.data['Model Comparison'];
        if (!modelData) {
            this.showError('Model Comparison data not found');
            return;
        }

        // Get unique categories and models
        const categories = [...new Set(modelData.map(row => row.Category || row.category))];
        const models = [...new Set(modelData.map(row => row.Model || row.model))];

        // Create radar chart data
        const datasets = models.map((model, index) => {
            const modelRows = modelData.filter(row => (row.Model || row.model) === model);
            const overallRow = modelRows.find(row => 
                (row.Category || row.category).toUpperCase().includes('OVERALL')
            );
            
            if (!overallRow) return null;

            return {
                label: model,
                data: [
                    parseFloat(overallRow.faithfulness || overallRow.Faithfulness) || 0,
                    parseFloat(overallRow.answerRelevance || overallRow['Answer Relevance']) || 0,
                    parseFloat(overallRow.contextRelevance || overallRow['Context Relevance']) || 0,
                    parseFloat(overallRow.correctness || overallRow.Correctness) || 0,
                    parseFloat(overallRow.overallScore || overallRow['Overall Score']) || 0
                ],
                backgroundColor: [
                    '#3498db',
                    '#e74c3c',
                    '#f39c12', 
                    '#2ecc71',
                    '#9b59b6'
                ][index % 5] + '40',
                borderColor: [
                    '#3498db',
                    '#e74c3c',
                    '#f39c12',
                    '#2ecc71', 
                    '#9b59b6'
                ][index % 5],
                borderWidth: 2
            };
        }).filter(dataset => dataset !== null);

        this.chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Faithfulness', 'Answer Relevance', 'Context Relevance', 'Correctness', 'Overall Score'],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Multi-Metric Model Comparison',
                        font: { size: 18, weight: 'bold' }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            stepSize: 2
                        }
                    }
                }
            }
        });

        this.updateChartInfo('Multi-Metric Comparison', 'Radar chart showing model performance across all metrics');
    }

    updateChartInfo(title, description) {
        document.getElementById('chart-title').textContent = title;
        document.getElementById('chart-description').textContent = description;
    }

    showError(message) {
        document.getElementById('chart-container').innerHTML = 
            `<div class="chart-error">${message}</div>`;
    }
}

// Initialize the charts manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ExcelChartsManager();
});

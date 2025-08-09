class ExcelComparisonDashboard {
    constructor() {
        this.data = {};
        this.currentSheet = 'Model Comparison';
        this.init();
    }

    async init() {
        await this.loadExcelFile();
        this.setupEventListeners();
        this.displaySheet(this.currentSheet);
    }

    async loadExcelFile() {
        try {
            // Show loading message
            document.getElementById('compare-table-body').innerHTML = 
                '<tr><td colspan="100%" class="compare-loading">Loading comparison data from Excel file...</td></tr>';
            
            // Load the Excel file
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
            
            console.log('Loaded comparison sheets:', Object.keys(this.data));
            
        } catch (error) {
            console.error('Error loading Excel file:', error);
            document.getElementById('compare-table-body').innerHTML = 
                '<tr><td colspan="100%" class="compare-error">Error loading Excel file. Please make sure "models_comparison_report.xlsx" is in the same directory.</td></tr>';
        }
    }

    setupEventListeners() {
        document.querySelectorAll('.compare-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sheetName = e.target.getAttribute('data-sheet');
                this.switchTab(sheetName);
            });
        });
    }

    switchTab(sheetName) {
        // Update active tab
        document.querySelectorAll('.compare-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-sheet="${sheetName}"]`).classList.add('active');
        
        // Display the selected sheet
        this.currentSheet = sheetName;
        this.displaySheet(sheetName);
    }

    displaySheet(sheetName) {
        if (!this.data[sheetName]) {
            document.getElementById('compare-table-body').innerHTML = 
                '<tr><td colspan="100%" class="compare-error">Sheet not found: ' + sheetName + '</td></tr>';
            return;
        }

        const data = this.data[sheetName];
        if (!data || data.length === 0) {
            document.getElementById('compare-table-body').innerHTML = 
                '<tr><td colspan="100%" class="compare-error">No data found in sheet: ' + sheetName + '</td></tr>';
            return;
        }

        // Create table header
        this.createTableHeader(data[0]);
        
        // Create table body
        this.createTableBody(data, sheetName);
    }

    createTableHeader(firstRow) {
        const thead = document.getElementById('compare-table-head');
        const columns = Object.keys(firstRow);
        
        thead.innerHTML = `
            <tr>
                ${columns.map(col => `<th>${this.formatColumnName(col)}</th>`).join('')}
            </tr>
        `;
    }

    createTableBody(data, sheetName) {
        const tbody = document.getElementById('compare-table-body');
        tbody.innerHTML = '';

        data.forEach(row => {
            const tr = document.createElement('tr');
            
            // Check if this is an OVERALL row
            const isOverallRow = Object.values(row).some(value => 
                String(value).toUpperCase().includes('OVERALL')
            );
            
            if (isOverallRow) {
                tr.classList.add('compare-overall-row');
            }

            const columns = Object.keys(row);
            columns.forEach((col, index) => {
                const td = document.createElement('td');
                const value = row[col];
                
                // Apply specific styling based on column and content
                if (index === 0) {
                    // First column (Model or Category)
                    if (sheetName === 'Model Comparison') {
                        td.classList.add('compare-model-name');
                    } else {
                        td.classList.add('compare-category-name');
                    }
                } else if (this.isNumericScore(value)) {
                    // Numeric score columns
                    td.classList.add(this.getScoreClass(value));
                }
                
                td.textContent = this.formatCellValue(value);
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
    }

    formatColumnName(columnName) {
        // Clean up column names
        return columnName
            .replace(/([A-Z])/g, ' $1') // Add space before capital letters
            .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
            .trim();
    }

    formatCellValue(value) {
        if (this.isNumericScore(value)) {
            const num = parseFloat(value);
            return num.toFixed(2);
        }
        return String(value);
    }

    isNumericScore(value) {
        const num = parseFloat(value);
        return !isNaN(num) && isFinite(num) && num >= 0 && num <= 10;
    }

    getScoreClass(score) {
        const numScore = parseFloat(score);
        if (numScore >= 8.5) return 'compare-score-excellent';
        if (numScore >= 6.5) return 'compare-score-good';
        return 'compare-score-fair';
    }
}

// Initialize the comparison dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ExcelComparisonDashboard();
});

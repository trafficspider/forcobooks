document.addEventListener('DOMContentLoaded', function() {
    const exportPdfBtn = document.getElementById('exportPdfBtn');

    exportPdfBtn.addEventListener('click', function() {
        // Get current filter parameters
        const urlParams = new URLSearchParams(window.location.search);
        const startDate = urlParams.get('start_date') || '';
        const endDate = urlParams.get('end_date') || '';

        // Construct the URL for PDF export
        const exportUrl = `/export_pdf?start_date=${startDate}&end_date=${endDate}`;

        // Make an AJAX request to check for invoices
        fetch(exportUrl)
            .then(response => {
                if (response.headers.get('Content-Type').includes('application/json')) {
                    return response.json();
                } else {
                    return response.blob();
                }
            })
            .then(data => {
                if (data instanceof Blob) {
                    // If the response is a Blob, it's the PDF file
                    if (confirm('Not all invoices are attached. Are you sure you want to download the file?')) {
                        downloadPDF(data, startDate, endDate);
                    }
                } else if (data.all_invoices_attached) {
                    if (confirm(data.message)) {
                        // User clicked "OK", highlight rows and generate PDF
                        highlightRowsAndGeneratePDF(startDate, endDate);
                    } else {
                        // User clicked "Cancel", generate PDF without highlighting
                        downloadPDFWithoutHighlight(startDate, endDate);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while exporting the PDF.');
            });
    });

    function highlightRowsAndGeneratePDF(startDate, endDate) {
        // Get all transaction rows
        const transactionRows = document.querySelectorAll('tr[data-transaction-id]');
        const highlightPromises = [];

        transactionRows.forEach(row => {
            const transactionId = row.dataset.transactionId;
            const highlightPromise = fetch('/toggle_highlight', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transaction_id: transactionId
                })
            }).then(response => response.json());

            highlightPromises.push(highlightPromise);
        });

        // Wait for all highlight operations to complete
        Promise.all(highlightPromises)
            .then(() => {
                // Generate PDF after highlighting
                downloadPDFWithoutHighlight(startDate, endDate);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while highlighting rows.');
            });
    }

    function downloadPDFWithoutHighlight(startDate, endDate) {
        const downloadUrl = `/generate_pdf?start_date=${startDate}&end_date=${endDate}`;
        
        fetch(downloadUrl)
            .then(response => response.blob())
            .then(blob => {
                downloadPDF(blob, startDate, endDate);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while downloading the PDF.');
            });
    }

    function downloadPDF(blob, startDate, endDate) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Create the filename
        let filename = 'financial_report';
        if (startDate) filename += `_${startDate}`;
        if (endDate) filename += `_${endDate}`;
        filename += '.pdf';

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const transactionRows = document.querySelectorAll('tr[data-transaction-id]');

    transactionRows.forEach(row => {
        const highlightBtn = row.querySelector('.highlightBtn');
        if (highlightBtn) {
            highlightBtn.addEventListener('click', function() {
                const transactionId = this.closest('tr').dataset.transactionId;
                toggleHighlight(transactionId, row);
            });
        }
    });

    function toggleHighlight(transactionId, row) {
        fetch('/toggle_highlight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transaction_id: transactionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                row.classList.toggle('highlighted', data.highlight);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while toggling highlight.');
        });
    }
});

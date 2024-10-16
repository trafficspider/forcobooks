document.addEventListener('DOMContentLoaded', function() {
    const calculateVatBtns = document.querySelectorAll('.calculateVatBtn');
    const removeVatBtns = document.querySelectorAll('.removeVatBtn');

    function updateVatCell(cell, vat, transactionId) {
        cell.innerHTML = `
            ${parseFloat(vat).toFixed(2)}
            <button class="btn btn-sm btn-secondary removeVatBtn" data-transaction-id="${transactionId}">X</button>
        `;
        attachRemoveVatListener(cell.querySelector('.removeVatBtn'));
    }

    function resetVatCell(cell, transactionId) {
        cell.innerHTML = `
            <button class="btn btn-sm btn-secondary calculateVatBtn" data-transaction-id="${transactionId}">Calculate VAT</button>
        `;
        attachCalculateVatListener(cell.querySelector('.calculateVatBtn'));
    }

    function attachCalculateVatListener(btn) {
        btn.addEventListener('click', function() {
            const transactionId = this.dataset.transactionId;
            const cell = this.closest('td');

            fetch('/calculate_vat', {
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
                if (data.error) {
                    alert(data.error);
                } else {
                    updateVatCell(cell, data.vat, transactionId);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while calculating VAT.');
            });
        });
    }

    function attachRemoveVatListener(btn) {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure you want to remove the VAT?')) {
                const transactionId = this.dataset.transactionId;
                const cell = this.closest('td');

                fetch('/remove_vat', {
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
                    if (data.error) {
                        alert(data.error);
                    } else {
                        resetVatCell(cell, transactionId);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while removing VAT.');
                });
            }
        });
    }

    calculateVatBtns.forEach(attachCalculateVatListener);
    removeVatBtns.forEach(attachRemoveVatListener);
});

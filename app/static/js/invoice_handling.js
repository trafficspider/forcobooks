document.addEventListener('DOMContentLoaded', function() {
    const uploadInvoiceBtns = document.querySelectorAll('.uploadInvoiceBtn');
    const viewInvoiceBtns = document.querySelectorAll('.viewInvoiceBtn');

    // Create modal HTML
    const modalHTML = `
    <div id="invoiceModal" class="invoice-modal">
      <div class="invoice-modal-content">
        <div class="invoice-modal-header">
          <h4>View Invoice</h4>
          <span class="close">&times;</span>
        </div>
        <div class="invoice-modal-body">
          <iframe id="invoiceFrame"></iframe>
        </div>
        <div class="invoice-modal-footer">
          <button id="deleteInvoiceBtn" class="btn btn-danger">Delete</button>
        </div>
      </div>
    </div>
    `;

    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = document.getElementById('invoiceModal');
    const invoiceFrame = document.getElementById('invoiceFrame');
    const deleteInvoiceBtn = document.getElementById('deleteInvoiceBtn');
    const closeBtn = modal.querySelector('.close');

    function updateInvoiceCell(cell, invoicePath, transactionId) {
        cell.innerHTML = `
            <button class="btn btn-sm btn-success viewInvoiceBtn" data-invoice-path="${invoicePath}" data-transaction-id="${transactionId}">View</button>
        `;
        attachViewInvoiceListener(cell.querySelector('.viewInvoiceBtn'));
    }

    function resetInvoiceCell(cell, transactionId) {
        cell.innerHTML = `
            <button class="btn btn-sm btn-secondary uploadInvoiceBtn" data-transaction-id="${transactionId}">Add</button>
        `;
        attachUploadInvoiceListener(cell.querySelector('.uploadInvoiceBtn'));
    }

    function attachUploadInvoiceListener(btn) {
        btn.addEventListener('click', function() {
            const transactionId = this.dataset.transactionId;
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf,.jpg,.jpeg,.png';

            input.onchange = e => {
                const file = e.target.files[0];
                const formData = new FormData();
                formData.append('file', file);
                formData.append('transaction_id', transactionId);

                fetch('/upload_invoice', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        updateInvoiceCell(this.closest('td'), data.file_path, transactionId);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while uploading the invoice.');
                });
            };

            input.click();
        });
    }

    function attachViewInvoiceListener(btn) {
        btn.addEventListener('click', function() {
            const invoicePath = this.dataset.invoicePath;
            const transactionId = this.dataset.transactionId;
            fetch(`/view_invoice/${invoicePath}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err; });
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    invoiceFrame.src = url;
                    deleteInvoiceBtn.dataset.transactionId = transactionId;
                    modal.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(error.error || 'Failed to load the invoice.');
                });
        });
    }

    deleteInvoiceBtn.addEventListener('click', function() {
        const transactionId = this.dataset.transactionId;
        if (confirm('Are you sure you want to delete this invoice?')) {
            const cell = document.querySelector(`.viewInvoiceBtn[data-transaction-id="${transactionId}"]`).closest('td');

            fetch('/delete_invoice', {
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
                    resetInvoiceCell(cell, transactionId);
                    modal.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting the invoice.');
            });
        }
    });

    closeBtn.onclick = function() {
        modal.style.display = 'none';
    };

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    function viewInvoice(invoicePath, transactionId) {
        fetch(`/view_invoice/${invoicePath}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw err; });
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');
            })
            .catch(error => {
                console.error('Error:', error);
                alert(error.error || 'Failed to load the invoice.');
            });
    }
});

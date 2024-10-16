document.addEventListener('DOMContentLoaded', function() {
    const commentBtns = document.querySelectorAll('.commentBtn');
    let currentTransactionId = null;

    // Create modal HTML
    const modalHTML = `
    <div class="modal fade" id="commentModal" tabindex="-1" role="dialog" aria-labelledby="commentModalLabel" aria-hidden="true" data-backdrop="static" data-keyboard="false">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h4 class="modal-title" id="commentModalLabel">Add/Edit Comment</h4>
          </div>
          <div class="modal-body">
            <textarea id="commentText" class="form-control" rows="4"></textarea>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="clearComment">Clear</button>
            <button type="button" class="btn btn-primary" id="saveComment">OK</button>
          </div>
        </div>
      </div>
    </div>
    `;

    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = $('#commentModal');
    const commentText = document.getElementById('commentText');
    const clearBtn = document.getElementById('clearComment');
    const saveBtn = document.getElementById('saveComment');

    commentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTransactionId = this.dataset.transactionId;
            const currentComment = this.dataset.comment || '';
            commentText.value = currentComment;
            modal.modal({
                backdrop: 'static',
                keyboard: false
            });
        });
    });

    clearBtn.addEventListener('click', function() {
        commentText.value = '';
    });

    saveBtn.addEventListener('click', function() {
        const newComment = commentText.value;
        saveComment(currentTransactionId, newComment);
    });

    modal.on('shown.bs.modal', function () {
        commentText.focus();
    });

    function saveComment(transactionId, comment) {
        fetch('/add_comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transaction_id: transactionId,
                comment: comment
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                const btn = document.querySelector(`.commentBtn[data-transaction-id="${transactionId}"]`);
                btn.dataset.comment = comment;
                if (comment) {
                    btn.textContent = 'Edit';
                    btn.classList.remove('btn-secondary');
                    btn.classList.add('btn-warning');
                } else {
                    btn.textContent = 'Add';
                    btn.classList.remove('btn-warning');
                    btn.classList.add('btn-secondary');
                }
                modal.modal('hide');
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving the comment.');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const uploadCsvBtn = document.getElementById('uploadCsvBtn');
    const csvFileInput = document.getElementById('csvFileInput');

    uploadCsvBtn.addEventListener('click', function() {
        csvFileInput.click();
    });

    csvFileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload_csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while uploading the CSV file.');
            });
        }
    });
});
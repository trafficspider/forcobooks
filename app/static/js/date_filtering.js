document.addEventListener('DOMContentLoaded', function() {
    const filterDatesBtn = document.getElementById('filterDatesBtn');
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    filterDatesBtn.addEventListener('click', function() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        // Construct the URL with query parameters
        let url = new URL(window.location.href);
        url.searchParams.set('start_date', startDate);
        url.searchParams.set('end_date', endDate);
        url.searchParams.set('page', '1');  // Reset to first page when filtering

        // Navigate to the new URL
        window.location.href = url.toString();
    });

    clearFilterBtn.addEventListener('click', function() {
        // Clear the input fields
        startDateInput.value = '';
        endDateInput.value = '';

        // Remove date parameters from the URL and navigate
        let url = new URL(window.location.href);
        url.searchParams.delete('start_date');
        url.searchParams.delete('end_date');
        url.searchParams.set('page', '1');  // Reset to first page when clearing filter

        // Navigate to the new URL
        window.location.href = url.toString();
    });

    // Set initial values if they exist in the URL
    let urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('start_date')) {
        startDateInput.value = urlParams.get('start_date');
    }
    if (urlParams.has('end_date')) {
        endDateInput.value = urlParams.get('end_date');
    }
});

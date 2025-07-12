// Example: Confirm before deleting swap
document.addEventListener('DOMContentLoaded', function () {
    const deleteLinks = document.querySelectorAll('a[href*="delete_swap"]');
    deleteLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to cancel this swap request?')) {
                e.preventDefault();
            }
        });
    });
});

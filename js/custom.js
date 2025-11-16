document.addEventListener('DOMContentLoaded', function () {
    // Confirm delete action
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Navbar toggler and collapse handling
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('#navbarNav');

    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function () {
            if (navbarCollapse.classList.contains('show')) {
                navbarToggler.setAttribute('aria-expanded', 'false');
            } else {
                navbarToggler.setAttribute('aria-expanded', 'true');
            }
        });

        // Close navbar when a link is clicked
        navbarCollapse.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (navbarCollapse.classList.contains('show')) {
                    new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    }).hide();
                }
            });
        });
    }
});
// htmx: 401/403 error handling
document.addEventListener('htmx:responseError', function(evt) {
    var status = evt.detail.xhr.status;
    if (status === 401) alert('Your session has expired. Please log in again.');
    if (status === 403) alert('Sorry, you are not authorised to access this page.');
});

// jQuery fallback: 401/403 for non-htmx AJAX (Select2, legacy calls)
jQuery.ajaxSetup({
    statusCode: {
        401: function() { alert('Your session has expired. Please log in again.'); },
        403: function() { alert('Sorry, you are not authorised to access this page.'); }
    }
});

// Select2: initialize with Bootstrap theme on page load
if ($.fn.select2) {
    $.fn.select2.defaults.set('theme', 'bootstrap');
    $(function() {
        $('.select2').select2();
    });
}

// Select2: re-initialize inside Bootstrap modals when they open
$(function() {
    $(document).on('shown.bs.modal', '.modal', function() {
        $(this).find('select.select2').select2();
    });
});

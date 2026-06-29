document.addEventListener("click", function (event) {
    const button = event.target.closest(".btn-toggle");
    if (!button) return;

    const container = button.closest(".tools-toggle");
    if (!container) return;

    container.querySelectorAll(".btn-toggle").forEach((btn) => {
        btn.classList.remove("active");
    });

    button.classList.add("active");
});

function closeModal(event = null) {
    if (event && event.target !== event.currentTarget) return;

    const shouldClose = confirm("Are you sure you want to cancel? \n Your changes will be lost.");
    if (!shouldClose) return;

    document.getElementById('modal-container').innerHTML = '';
}

function closeModalAndRefresh(url) {
    document.getElementById('modal-container').innerHTML = '';

    if (!url) return;

    htmx.ajax('GET', url, {
        target: '#objects-content',
        swap: 'innerHTML'
    });
}

function prepareAddressForm(event) {
    const form = event.target;

    const ipv4Type = form.querySelector('#ipv4_type')?.value || '';
    const ipv6Type = form.querySelector('#ipv6_type')?.value || '';

    if (!ipv4Type && !ipv6Type) {
        event.preventDefault();
        alert('At least one of IPv4 or IPv6 must be selected.');
        return;
    }
}

function toggleAddressFields(form) {
    const ipv4Type = form.querySelector('#ipv4_type')?.value || '';
    const ipv6Type = form.querySelector('#ipv6_type')?.value || '';

    const ipv4StandardFields = form.querySelector('#ipv4-standard-fields');
    const ipv4CustomFields = form.querySelector('#ipv4-custom-fields');
    const ipv6StandardFields = form.querySelector('#ipv6-standard-fields');
    const ipv6CustomFields = form.querySelector('#ipv6-custom-fields');

    if (ipv4StandardFields) {
        ipv4StandardFields.style.display = ipv4Type === 'standard' ? 'block' : 'none';
    }

    if (ipv4CustomFields) {
        ipv4CustomFields.style.display = ipv4Type === 'custom' ? 'flex' : 'none';
    }

    if (ipv6StandardFields) {
        ipv6StandardFields.style.display = ipv6Type === 'standard' ? 'block' : 'none';
    }

    if (ipv6CustomFields) {
        ipv6CustomFields.style.display = ipv6Type === 'custom' ? 'flex' : 'none';
    }
}
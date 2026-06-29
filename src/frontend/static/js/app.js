// Handle clicks on toggle buttons.
document.addEventListener("click", function (event) {
    const button = event.target.closest(".btn-toggle");
    if (!button) return;

    const container = button.closest(".tools-toggle");
    if (!container) return;

    container.querySelectorAll(".btn-toggle").forEach((btn) => {
        btn.classList.remove("active"); // Removes the active state from sibling buttons
    });

    button.classList.add("active"); // Marks the clicked button as active.
});

// Close the modal, and ask for confirmation before clearing the modal content.
function closeModal(event = null) {
    if (event && event.target !== event.currentTarget) return;

    const shouldClose = confirm("Are you sure you want to cancel? \n Your changes will be lost.");
    if (!shouldClose) return;

    document.getElementById('modal-container').innerHTML = '';
}

// Close the modal and refresh the objects content area. If a refresh URL is provided, reload the relevant page content with HTMX.
function closeModalAndRefresh(url) {
    document.getElementById('modal-container').innerHTML = '';

    if (!url) return;

    htmx.ajax('GET', url, {
        target: '#objects-content',
        swap: 'innerHTML'
    });
}

// Validate the address form before submit. At least one of IPv4 or IPv6 must be selected, if neither dropdown has a value, prevent form submission.
function prepareAddressForm(event) {
    const form = event.target;
    const ipv4Type = form.querySelector('#ipv4_type');
    const ipv6Type = form.querySelector('#ipv6_type');

    if (!ipv4Type || !ipv6Type) return;

    ipv4Type.setCustomValidity('');
    ipv6Type.setCustomValidity('');

    if (!ipv4Type.value && !ipv6Type.value) {
        event.preventDefault();
        ipv4Type.setCustomValidity('Please select at least one of IPv4 or IPv6.');
        ipv4Type.reportValidity();
    }
}

/*
Show or hide IPv4/IPv6 input fields based on the selected dropdown value.
- "standard" shows the single network input
- "custom" shows the start/end range inputs
- empty selection hides both field groups
*/
function toggleAddressFields(form) {
    const ipv4Type = form.querySelector('#ipv4_type')?.value || '';
    const ipv6Type = form.querySelector('#ipv6_type')?.value || '';

    const ipv4Select = form.querySelector('#ipv4_type');
    const ipv6Select = form.querySelector('#ipv6_type');

    if (ipv4Select) ipv4Select.setCustomValidity('');
    if (ipv6Select) ipv6Select.setCustomValidity('');

    const ipv4StandardFields = form.querySelector('#ipv4-standard-fields');
    const ipv4CustomFields = form.querySelector('#ipv4-custom-fields');
    const ipv6StandardFields = form.querySelector('#ipv6-standard-fields');
    const ipv6CustomFields = form.querySelector('#ipv6-custom-fields');

    const ipv4Network = form.querySelector('#ipv4Network');
    const ipv4AddressStart = form.querySelector('#ipv4Address_start');
    const ipv4AddressEnd = form.querySelector('#ipv4Address_end');
    const ipv6Network = form.querySelector('#ipv6Network');
    const ipv6AddressStart = form.querySelector('#ipv6Address_start');
    const ipv6AddressEnd = form.querySelector('#ipv6Address_end');

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

    if (ipv4Network) {
        ipv4Network.required = ipv4Type === 'standard';
    }

    if (ipv4AddressStart) {
        ipv4AddressStart.required = ipv4Type === 'custom';
    }

    if (ipv4AddressEnd) {
        ipv4AddressEnd.required = ipv4Type === 'custom';
    }

    if (ipv6Network) {
        ipv6Network.required = ipv6Type === 'standard';
    }

    if (ipv6AddressStart) {
        ipv6AddressStart.required = ipv6Type === 'custom';
    }

    if (ipv6AddressEnd) {
        ipv6AddressEnd.required = ipv6Type === 'custom';
    }
}

// Listen for the HTMX event that fires after new HTML has been swapped into the page.
document.body.addEventListener("htmx:afterSwap", function (event) {

    event.target.querySelectorAll("form").forEach((form) => {
        // Only run the address field toggle logic for forms that contain either the IPv4 type select or the IPv6 type select.
        if (form.querySelector("#ipv4_type") || form.querySelector("#ipv6_type")) {
            // Show or hide the correct address input fields based on the currently selected IPv4/IPv6 type values.
            toggleAddressFields(form);
        }
    });
});
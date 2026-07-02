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
    const ipv4Type = form.querySelector('#ipv4_type')?.value || '';
    const ipv6Type = form.querySelector('#ipv6_type')?.value || '';

    form.querySelector('#ipv4_type')?.setCustomValidity('');
    form.querySelector('#ipv6_type')?.setCustomValidity('');

    // If neither dropdown has a selected value, prevent the form from submitting
    if (!ipv4Type && !ipv6Type) {
        event.preventDefault();
        form.querySelector('#ipv4_type')?.setCustomValidity('Please select at least one of IPv4 or IPv6.'); // Show the browser validation message on the IPv4 dropdown.
        form.querySelector('#ipv4_type')?.reportValidity();
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

    // Clear any previous custom validation message when the selection changes.
    form.querySelector('#ipv4_type')?.setCustomValidity('');
    form.querySelector('#ipv6_type')?.setCustomValidity('');

    // Toggle visible field groups based on the selected address type.
    form.querySelector('#ipv4-standard-fields').style.display = ipv4Type === 'standard' ? 'block' : 'none';
    form.querySelector('#ipv4-custom-fields').style.display = ipv4Type === 'custom_range' ? 'flex' : 'none';
    form.querySelector('#ipv6-standard-fields').style.display = ipv6Type === 'standard' ? 'block' : 'none';
    form.querySelector('#ipv6-custom-fields').style.display = ipv6Type === 'custom_range' ? 'flex' : 'none';

    // Update required validation so only the visible, relevant fields are required.
    form.querySelector('#ipv4Network').required = ipv4Type === 'standard';
    form.querySelector('#ipv4Address_start').required = ipv4Type === 'custom_range';
    form.querySelector('#ipv4Address_end').required = ipv4Type === 'custom_range';

    form.querySelector('#ipv6Network').required = ipv6Type === 'standard';
    form.querySelector('#ipv6Address_start').required = ipv6Type === 'custom_range';
    form.querySelector('#ipv6Address_end').required = ipv6Type === 'custom_range';
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
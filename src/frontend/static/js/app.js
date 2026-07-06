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

// Validate the address form before submit. At least one of IPv4 or IPv6 must be selected.
function prepareAddressForm(event) {
    const form = event.target;
    const ipv4InputField = form.querySelector('[name="ipv4_input"]');
    const ipv6InputField = form.querySelector('[name="ipv6_input"]');

    const ipv4Input = ipv4InputField?.value.trim() || '';
    const ipv6Input = ipv6InputField?.value.trim() || '';

    ipv4InputField?.setCustomValidity('');
    ipv6InputField?.setCustomValidity('');

    if (!ipv4Input && !ipv6Input) {
        event.preventDefault();
        ipv4InputField?.setCustomValidity('Please enter at least one IPv4 or IPv6 value.');
        ipv4InputField?.reportValidity();
        return;
    }
}
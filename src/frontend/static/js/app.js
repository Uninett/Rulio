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
    const ipv4TypeField = form.querySelector('[name="ipv4_type"]');
    const ipv6TypeField = form.querySelector('[name="ipv6_type"]');

    const ipv4Type = ipv4TypeField?.value || '';
    const ipv6Type = ipv6TypeField?.value || '';

    ipv4TypeField?.setCustomValidity('');
    ipv6TypeField?.setCustomValidity('');

    if (!ipv4Type && !ipv6Type) {
        event.preventDefault();
        ipv4TypeField?.setCustomValidity('Please select at least one of IPv4 or IPv6.');
        ipv4TypeField?.reportValidity();
    }
}

/*
Show or hide IPv4/IPv6 input fields based on the selected dropdown value.
- "standard" shows the single network input
- "custom" shows the start/end range inputs
- empty selection hides both field groups
*/
function toggleAddressFields(form) {
    const ipv4Type = form.querySelector('[name="ipv4_type"]').value;
    const ipv6Type = form.querySelector('[name="ipv6_type"]').value;

    const ipv4StandardFields = form.querySelector('#ipv4-standard-fields');
    const ipv4CustomFields = form.querySelector('#ipv4-custom-fields');
    const ipv6StandardFields = form.querySelector('#ipv6-standard-fields');
    const ipv6CustomFields = form.querySelector('#ipv6-custom-fields');

    const ipv4Network = form.querySelector('[name="ipv4Network"]');
    const ipv4Start = form.querySelector('[name="ipv4Address_start"]');
    const ipv4End = form.querySelector('[name="ipv4Address_end"]');

    const ipv6Network = form.querySelector('[name="ipv6Network"]');
    const ipv6Start = form.querySelector('[name="ipv6Address_start"]');
    const ipv6End = form.querySelector('[name="ipv6Address_end"]');

    function setDisabled(inputs, disabled) {
        inputs.forEach(input => {
            if (input) input.disabled = disabled;
        });
    }

    if (ipv4Type === "standard") {
        ipv4StandardFields.style.display = "block";
        ipv4CustomFields.style.display = "none";
        if (ipv4Start) ipv4Start.value = "";
        if (ipv4End) ipv4End.value = "";
        setDisabled([ipv4Network], false);
        setDisabled([ipv4Start, ipv4End], true);
    } else if (ipv4Type === "custom_range") {
        ipv4StandardFields.style.display = "none";
        ipv4CustomFields.style.display = "flex";
        if (ipv4Network) ipv4Network.value = "";
        setDisabled([ipv4Network], true);
        setDisabled([ipv4Start, ipv4End], false);
    } else {
        ipv4StandardFields.style.display = "none";
        ipv4CustomFields.style.display = "none";
        if (ipv4Network) ipv4Network.value = "";
        if (ipv4Start) ipv4Start.value = "";
        if (ipv4End) ipv4End.value = "";
        setDisabled([ipv4Network, ipv4Start, ipv4End], true);
    }

    if (ipv6Type === "standard") {
        ipv6StandardFields.style.display = "block";
        ipv6CustomFields.style.display = "none";
        if (ipv6Start) ipv6Start.value = "";
        if (ipv6End) ipv6End.value = "";
        setDisabled([ipv6Network], false);
        setDisabled([ipv6Start, ipv6End], true);
    } else if (ipv6Type === "custom_range") {
        ipv6StandardFields.style.display = "none";
        ipv6CustomFields.style.display = "flex";
        if (ipv6Network) ipv6Network.value = "";
        setDisabled([ipv6Network], true);
        setDisabled([ipv6Start, ipv6End], false);
    } else {
        ipv6StandardFields.style.display = "none";
        ipv6CustomFields.style.display = "none";
        if (ipv6Network) ipv6Network.value = "";
        if (ipv6Start) ipv6Start.value = "";
        if (ipv6End) ipv6End.value = "";
        setDisabled([ipv6Network, ipv6Start, ipv6End], true);
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
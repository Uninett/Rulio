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

    const ipv4Network = form.querySelector('#ipv4Network')?.value.trim();
    const ipv6Network = form.querySelector('#ipv6Network')?.value.trim();
    const ipv4Type = form.querySelector('#ipv4_type');
    const ipv6Type = form.querySelector('#ipv6_type');

    if (ipv4Type) {
        ipv4Type.value = ipv4Network ? 'standard' : '';
    }

    if (ipv6Type) {
        ipv6Type.value = ipv6Network ? 'standard' : '';
    }
}
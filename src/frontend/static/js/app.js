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

function initializeMembershipSelectors(root = document) {
    root.querySelectorAll(".membership-selector").forEach((selector) => {
        const inputName = selector.dataset.inputName;
        const availableList = selector.querySelector('.membership-list-available');
        const selectedList = selector.querySelector('.membership-list-selected');

        let draggedItem = null;

        selector.querySelectorAll(".membership-list-item").forEach(setupDraggableItem);

        function setupDraggableItem(item) {
            item.addEventListener("dragstart", () => {
                draggedItem = item;
                item.classList.add("dragging");
            });

            item.addEventListener("dragend", () => {
                item.classList.remove("dragging");
                draggedItem = null;
            });
        }

        function ensureHiddenInput(item, shouldExist) {
            let hiddenInput = item.querySelector(`input[type="hidden"][name="${inputName}"]`);

            if (shouldExist && !hiddenInput) {
                hiddenInput = document.createElement("input");
                hiddenInput.type = "hidden";
                hiddenInput.name = inputName;
                hiddenInput.value = item.dataset.id;
                item.appendChild(hiddenInput);
            }

            if (!shouldExist && hiddenInput) {
                hiddenInput.remove();
            }
        }

        function moveItem(targetList) {
            if (!draggedItem) return;

            const alreadyExists = Array.from(targetList.querySelectorAll(".membership-list-item"))
                .some(item => item.dataset.id === draggedItem.dataset.id);

            if (alreadyExists) return;

            targetList.appendChild(draggedItem);

            if (targetList === selectedList) {
                ensureHiddenInput(draggedItem, true);
            } else {
                ensureHiddenInput(draggedItem, false);
            }
        }

        [availableList, selectedList].forEach((list) => {
            list.addEventListener("dragover", (event) => {
                event.preventDefault();
            });

            list.addEventListener("drop", (event) => {
                event.preventDefault();
                moveItem(list);
            });
        });

        selector.querySelectorAll(".membership-list-item").forEach((item) => {
            item.addEventListener("dblclick", () => {
                const currentList = item.parentElement;
                if (currentList === availableList) {
                    draggedItem = item;
                    moveItem(selectedList);
                } else {
                    draggedItem = item;
                    moveItem(availableList);
                }
                draggedItem = null;
            });
        });
    });
}

document.body.addEventListener("htmx:afterSwap", function (event) {
    initializeMembershipSelectors(event.target);
});

document.addEventListener("DOMContentLoaded", function () {
    initializeMembershipSelectors(document);
});
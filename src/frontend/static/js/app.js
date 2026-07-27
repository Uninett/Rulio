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

(function () {
    let activeDrag = null;
    let suppressBackdropClick = false;

    function makeModalDraggable(modalId, headerId) {
        const modal = document.getElementById(modalId);
        const header = document.getElementById(headerId);

        if (!modal || !header || header.dataset.dragBound === 'true') return;
        header.dataset.dragBound = 'true';

        header.addEventListener('mousedown', function (e) {
            if (e.button !== 0) return;

            e.preventDefault();
            e.stopPropagation();

            const rect = modal.getBoundingClientRect();

            activeDrag = {
                modal,
                offsetX: e.clientX - rect.left,
                offsetY: e.clientY - rect.top
            };

            modal.style.left = `${rect.left}px`;
            modal.style.top = `${rect.top}px`;
            modal.style.transform = 'none';

            document.body.style.userSelect = 'none';
        });

        header.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    document.addEventListener('mousemove', function (e) {
        if (!activeDrag) return;

        const { modal, offsetX, offsetY } = activeDrag;
        const rect = modal.getBoundingClientRect();

        let newLeft = e.clientX - offsetX;
        let newTop = e.clientY - offsetY;

        const maxLeft = window.innerWidth - rect.width;
        const maxTop = window.innerHeight - rect.height;

        newLeft = Math.max(0, Math.min(newLeft, maxLeft));
        newTop = Math.max(0, Math.min(newTop, maxTop));

        modal.style.left = `${newLeft}px`;
        modal.style.top = `${newTop}px`;

        suppressBackdropClick = true;
    });

    document.addEventListener('mouseup', function () {
        if (!activeDrag) return;

        activeDrag = null;
        document.body.style.userSelect = '';

        setTimeout(() => {
            suppressBackdropClick = false;
        }, 0);
    });

    document.addEventListener('click', function (e) {
        if (!suppressBackdropClick) return;

        const backdrop = e.target.closest('.modal-backdrop');
        if (backdrop) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, true);

    function initDraggableModal() {
        makeModalDraggable('draggable-modal', 'draggable-modal-header');
    }

    document.addEventListener('DOMContentLoaded', initDraggableModal);
    document.addEventListener('htmx:afterSwap', initDraggableModal);

    window.initDraggableModal = initDraggableModal;
})();

// Close the modal, and ask for confirmation before clearing the modal content.
function closeModal(event = null) {
    if (event && event.target !== event.currentTarget) return;

    const shouldClose = confirm("Are you sure you want to cancel? \n Your changes will be lost.");
    if (!shouldClose) return;

    document.getElementById('modal-container').innerHTML = '';
}

// Close the modal and refresh the objects content area. If a refresh URL is provided, reload the relevant page content with HTMX.
function closeModalAndRefresh(url, target) {
    const modalContainer = document.getElementById("modal-container");
    if (modalContainer) {
        modalContainer.innerHTML = "";
    }

    if (!url || !target) return;

    htmx.ajax("GET", url, {
        target: target,
        swap: "innerHTML"
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

// Initialize all membership selector components inside the given root element.
function initializeMembershipSelectors(root = document) {

    // Find every membership selector component in the current root.
    root.querySelectorAll(".membership-selector").forEach((selector) => {
        const inputName = selector.dataset.inputName;
        const availableList = selector.querySelector('.membership-list-available');
        const selectedList = selector.querySelector('.membership-list-selected');

        let draggedItem = null;

        // Attach drag handlers to every existing item inside this selector.
        selector.querySelectorAll(".membership-list-item").forEach(setupDraggableItem);

        // Add drag start/end behavior to one item.
        function setupDraggableItem(item) {
            // When dragging starts, store the current item.
            item.addEventListener("dragstart", () => {
                draggedItem = item;
                item.classList.add("dragging");
            });

            // When dragging ends, clear the stored item.
            item.addEventListener("dragend", () => {
                item.classList.remove("dragging");
                draggedItem = null;
            });
        }

        // Ensure that the dragged/selected item either has or does not have a hidden input.
        function ensureHiddenInput(item, shouldExist) {
            // Look for an existing hidden input with the configured input name inside this item.
            let hiddenInput = item.querySelector(`input[type="hidden"][name="${inputName}"]`);

            // If the input should exist but does not yet exist, create it.
            if (shouldExist && !hiddenInput) {
                hiddenInput = document.createElement("input");
                hiddenInput.type = "hidden";
                hiddenInput.name = inputName;
                hiddenInput.value = item.dataset.id;
                item.appendChild(hiddenInput);
            }

            // If the input should not exist but does exist, remove it.
            if (!shouldExist && hiddenInput) {
                hiddenInput.remove();
            }
        }

        // Find the item before which the dragged element should be inserted, by compareing the current mouse Y position with the vertical midpoint of each item.
        function getDropTarget(list, y) {
            // Get all items except the one currently being dragged.
            const items = [...list.querySelectorAll(".membership-list-item:not(.dragging)")];

            // Return the first item whose midpoint is below the mouse position.
            return items.find((item) => {
                const rect = item.getBoundingClientRect();
                return y < rect.top + rect.height / 2;
            }) || null;
        }

        // Move the dragged item into the target list. If a Y position is provided, insert the item at the dropped position.
        function moveItem(targetList, y = null) {
            if (!draggedItem) return;

            // Prevent the same item from existing twice in the target list.
            const alreadyExists = Array.from(targetList.querySelectorAll(".membership-list-item"))
                .some(item => item !== draggedItem && item.dataset.id === draggedItem.dataset.id);

            if (alreadyExists) return;

            // If a drop position was provided, find the closest target item.
            const dropTarget = y !== null ? getDropTarget(targetList, y) : null;

            // If there is a drop target, insert before it.
            if (dropTarget) {
                targetList.insertBefore(draggedItem, dropTarget); // If there is a drop target, insert before it.
            } else {
                targetList.appendChild(draggedItem); // Otherwise, append to the end of the list.
            }

            // If the item is now in the selected list, make sure it has a hidden input.
            if (targetList === selectedList) {
                ensureHiddenInput(draggedItem, true);
            } else {
                ensureHiddenInput(draggedItem, false); // If it is in the available list, remove the hidden input.
            }
        }

        // Enable dropping on both lists.
        [availableList, selectedList].forEach((list) => {
            // Prevent the browser’s default handling so dropping is allowed.
            list.addEventListener("dragover", (event) => {
                event.preventDefault();
            });

            // When the item is dropped, move it into this list at the drop position.
            list.addEventListener("drop", (event) => {
                event.preventDefault();
                moveItem(list, event.clientY);
            });
        });

        // Support double-click as a quicker alternative to drag-and-drop.
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

// Re-initialize membership selectors after HTMX swaps new HTML into the page.
document.body.addEventListener("htmx:afterSwap", function (event) {
    initializeMembershipSelectors(event.target);
});

// Initialize membership selectors on the initial page load.
document.addEventListener("DOMContentLoaded", function () {
    initializeMembershipSelectors(document);
});


// Toggle the visibility of the user menu dropdown when the profile button is clicked.
function toggleUserMenu(event) {
    event.stopPropagation();

    const dropdown = document.getElementById("user-menu-dropdown");
    if (!dropdown) return;

    dropdown.classList.toggle("hidden");
}

document.addEventListener("click", function (event) {
    const menu = document.querySelector(".user-menu");
    if (!menu) return;

    const dropdown = document.getElementById("user-menu-dropdown");
    if (!dropdown) return;

    if (!menu.contains(event.target)) {
        dropdown.classList.add("hidden");
    }
});


function expandRow(rowId) {
    const detailsRow = document.getElementById(`details-${rowId}`);
    const openedRow = document.getElementById(`row-${rowId}`);


    if (detailsRow.style.display === "table-row") {
        detailsRow.style.display = "none";
        openedRow.classList.remove("expanded-row");
    } else {
        detailsRow.style.display = "table-row";
        openedRow.classList.add("expanded-row");
    }
}

function focusAndExpandFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const rowId = params.get("expand_id"); //get expand id
    if (!rowId) return;

    let attempts = 0;
    const maxAttempts = 30;

    const interval = setInterval(function () {
        const row = document.getElementById(`row-${rowId}`); //get row
        const detailsRow = document.getElementById(`details-${rowId}`); //get detail row

        if (row && detailsRow) { //if both exists
            if (window.getComputedStyle(detailsRow).display !== "table-row") { //if not currently visible
                expandRow(rowId); //expand
            }

            setTimeout(function () {
                row.scrollIntoView({ //scroll to the row
                    behavior: "smooth",
                    block: "center"
                });
            }, 200); // waits 200ms, than scroll row into view

            clearInterval(interval); //stop when found

            window.history.replaceState({}, "", window.location.pathname); //clean URL to pathname
        }

        attempts++;
        if (attempts >= maxAttempts) {
            clearInterval(interval);
        }
    }, 200);
}

document.addEventListener("DOMContentLoaded", focusAndExpandFromUrl);
document.body.addEventListener("htmx:afterSwap", focusAndExpandFromUrl);
document.body.addEventListener("htmx:afterSettle", focusAndExpandFromUrl);
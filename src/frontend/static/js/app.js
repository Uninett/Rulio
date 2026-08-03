/*
====================================================================
Toggle Buttons
====================================================================
*/

function handleToggleButtonClick(event) {
    const button = event.target.closest(".btn-toggle");
    if (!button) return;

    const container = button.closest(".tools-toggle");
    if (!container) return;

    container.querySelectorAll(".btn-toggle").forEach((btn) => {
        btn.classList.remove("active");
    });

    button.classList.add("active");
}


/*
====================================================================
Modal
====================================================================
*/

function closeModal(event = null) {
    if (event && event.target !== event.currentTarget) return;

    const shouldClose = confirm("Are you sure you want to cancel? \n Your changes will be lost.");
    if (!shouldClose) return;

    document.getElementById("modal-container").innerHTML = "";
}

function closeModalAndRefresh(url, target) {
    const modalContainer = document.getElementById("modal-container");
    if (modalContainer) {
        modalContainer.innerHTML = "";
    }

    if (!url || !target) return;

    const refreshTarget = document.querySelector(target);
    let savedScrollTop = 0;

    if (refreshTarget) {
        const scrollContainer = refreshTarget.querySelector(".table-container");
        if (scrollContainer) {
            savedScrollTop = scrollContainer.scrollTop;
        }
    }

    htmx.ajax("GET", url, {
        target: target,
        swap: "innerHTML"
    }).then(() => {
        const updatedTarget = document.querySelector(target);
        if (!updatedTarget) return;

        const updatedScrollContainer = updatedTarget.querySelector(".table-container");
        if (updatedScrollContainer) {
            updatedScrollContainer.scrollTop = savedScrollTop;
        }
    });
}


/*
====================================================================
Draggable Modal
====================================================================
*/

const draggableModalState = {
    activeDrag: null,
    suppressBackdropClick: false
};

function makeModalDraggable(modalId, headerId) {
    const modal = document.getElementById(modalId);
    const header = document.getElementById(headerId);

    if (!modal || !header || header.dataset.dragBound === "true") return;
    header.dataset.dragBound = "true";

    header.addEventListener("mousedown", function (e) {
        if (e.button !== 0) return;

        e.preventDefault();
        e.stopPropagation();

        const rect = modal.getBoundingClientRect();

        draggableModalState.activeDrag = {
            modal,
            offsetX: e.clientX - rect.left,
            offsetY: e.clientY - rect.top
        };

        modal.style.left = `${rect.left}px`;
        modal.style.top = `${rect.top}px`;
        modal.style.transform = "none";

        document.body.style.userSelect = "none";
    });

    header.addEventListener("click", function (e) {
        e.stopPropagation();
    });
}

function initDraggableModal() {
    makeModalDraggable("draggable-modal", "draggable-modal-header");
}

function handleModalMouseMove(e) {
    if (!draggableModalState.activeDrag) return;

    const { modal, offsetX, offsetY } = draggableModalState.activeDrag;

    let newLeft = e.clientX - offsetX;
    let newTop = e.clientY - offsetY;

    modal.style.left = `${newLeft}px`;
    modal.style.top = `${newTop}px`;

    draggableModalState.suppressBackdropClick = true;
}

function handleModalMouseUp() {
    if (!draggableModalState.activeDrag) return;

    draggableModalState.activeDrag = null;
    document.body.style.userSelect = "";

    setTimeout(() => {
        draggableModalState.suppressBackdropClick = false;
    }, 0);
}

function handleBackdropClickSuppression(e) {
    if (!draggableModalState.suppressBackdropClick) return;

    const backdrop = e.target.closest(".modal-backdrop");
    if (backdrop) {
        e.preventDefault();
        e.stopPropagation();
    }
}


/*
====================================================================
Address Form
====================================================================
*/

function prepareAddressForm(event) {
    const form = event.target;
    const ipv4InputField = form.querySelector('[name="ipv4_input"]');
    const ipv6InputField = form.querySelector('[name="ipv6_input"]');

    const ipv4Input = ipv4InputField?.value.trim() || "";
    const ipv6Input = ipv6InputField?.value.trim() || "";

    ipv4InputField?.setCustomValidity("");
    ipv6InputField?.setCustomValidity("");

    if (!ipv4Input && !ipv6Input) {
        event.preventDefault();
        ipv4InputField?.setCustomValidity("Please enter at least one IPv4 or IPv6 value.");
        ipv4InputField?.reportValidity();
    }
}


/*
====================================================================
Membership Selectors
====================================================================
*/

function initializeMembershipSelectors(root = document) {
    root.querySelectorAll(".membership-selector").forEach((selector) => {
        const inputName = selector.dataset.inputName;
        const availableList = selector.querySelector(".membership-list-available");
        const selectedList = selector.querySelector(".membership-list-selected");

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

            item.addEventListener("dblclick", () => {
                const currentList = item.parentElement;
                draggedItem = item;

                if (currentList === availableList) {
                    moveItem(selectedList);
                } else {
                    moveItem(availableList);
                }

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

        function getDropTarget(list, y) {
            const items = [...list.querySelectorAll(".membership-list-item:not(.dragging)")];

            return items.find((item) => {
                const rect = item.getBoundingClientRect();
                return y < rect.top + rect.height / 2;
            }) || null;
        }

        function moveItem(targetList, y = null) {
            if (!draggedItem) return;

            const alreadyExists = Array.from(targetList.querySelectorAll(".membership-list-item"))
                .some(item => item !== draggedItem && item.dataset.id === draggedItem.dataset.id);

            if (alreadyExists) return;

            const dropTarget = y !== null ? getDropTarget(targetList, y) : null;

            if (dropTarget) {
                targetList.insertBefore(draggedItem, dropTarget);
            } else {
                targetList.appendChild(draggedItem);
            }

            ensureHiddenInput(draggedItem, targetList === selectedList);
        }

        [availableList, selectedList].forEach((list) => {
            list.addEventListener("dragover", (event) => {
                event.preventDefault();
            });

            list.addEventListener("drop", (event) => {
                event.preventDefault();
                moveItem(list, event.clientY);
            });
        });
    });
}


/*
====================================================================
User Menu
====================================================================
*/

function toggleUserMenu(event) {
    event.stopPropagation();

    const dropdown = document.getElementById("user-menu-dropdown");
    if (!dropdown) return;

    dropdown.classList.toggle("hidden");
}

function closeUserMenuOnOutsideClick(event) {
    const menu = document.querySelector(".user-menu");
    if (!menu) return;

    const dropdown = document.getElementById("user-menu-dropdown");
    if (!dropdown) return;

    if (!menu.contains(event.target)) {
        dropdown.classList.add("hidden");
    }
}


/*
====================================================================
Expandable Rows
====================================================================
*/

function expandRow(rowId) {
    const detailsRow = document.getElementById(`details-${rowId}`);
    const openedRow = document.getElementById(`row-${rowId}`);

    if (!detailsRow || !openedRow) return;

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
    const rowId = params.get("expand_id");
    if (!rowId) return;

    let attempts = 0;
    const maxAttempts = 30;

    const interval = setInterval(function () {
        const row = document.getElementById(`row-${rowId}`);
        const detailsRow = document.getElementById(`details-${rowId}`);

        if (row && detailsRow) {
            if (window.getComputedStyle(detailsRow).display !== "table-row") {
                expandRow(rowId);
            }

            setTimeout(function () {
                row.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }, 200);

            clearInterval(interval);
            window.history.replaceState({}, "", window.location.pathname);
        }

        attempts++;
        if (attempts >= maxAttempts) {
            clearInterval(interval);
        }
    }, 200);
}

function focusAndExpandRow(rowId) {
    const row = document.getElementById(`row-${rowId}`);
    const detailsRow = document.getElementById(`details-${rowId}`);

    if (!row || !detailsRow) return;

    if (window.getComputedStyle(detailsRow).display !== "table-row") {
        expandRow(rowId);
    }

    row.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });
}

/*
====================================================================
Generate Config For Interface
====================================================================
*/

async function handleGenerateConfig(interfaceId) {
    const response = await fetch(`/devices/interfaces/${interfaceId}/check-config/`, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    });

    // Error handling for non-OK responses
    if (!response.ok) {
        throw new Error(`Config check failed with status ${response.status}`);
    }

    const data = await response.json();

    // Error case: If the response is not ok, show an error modal
    if (data.errors && data.errors.length > 0) {
        showConfigResultModal({
            title: "Error generating config",
            errors: data.errors,
            warnings: data.warnings || [],
            allowCancel: false,
            onConfirm: null
        });
        return;
    }
    // Warning case: If there are warnings, show a warning modal
    if (data.warnings && data.warnings.length > 0) {
        showConfigResultModal({
            title: "Warnings while generating config",
            errors: [],
            warnings: data.warnings,
            allowCancel: true,
            onConfirm: () => {
                if (data.download_url) {
                    window.location.href = data.download_url;
                }
            }
        });
        return;
    }
    // Success case: If there are no errors or warnings, proceed to download the config
    if (data.can_download && data.download_url) {
        window.location.href = data.download_url;
    }
}

function showConfigResultModal({ title, errors = [], warnings = [], allowCancel = false, onConfirm = null }) {
    // Link the modal elements
    const modal = document.getElementById("config-result-modal");
    const titleEl = document.getElementById("config-result-modal-title");
    const bodyEl = document.getElementById("config-result-modal-body");
    const confirmBtn = document.getElementById("config-result-modal-confirm");
    const cancelBtn = document.getElementById("config-result-modal-cancel");

    titleEl.textContent = title; // TextContent is safer than innerHTML to avoid XSS vulnerabilities
    bodyEl.innerHTML = ""; // Clear previous content

    // Display errors if any
    if (errors.length > 0) {
        const errorsHeader = document.createElement("h4");
        errorsHeader.textContent = "Errors";
        bodyEl.appendChild(errorsHeader);

        const errorsList = document.createElement("ul");
        errors.forEach((errorText) => {
            const li = document.createElement("li"); // Create a new list item for each error
            li.textContent = errorText;
            errorsList.appendChild(li);
        });
        bodyEl.appendChild(errorsList); // Append the list of errors to the modal body
    }

    // Display warnings if any
    if (warnings.length > 0) {
        const warningsHeader = document.createElement("h4");
        warningsHeader.textContent = "Warnings";
        bodyEl.appendChild(warningsHeader);

        const warningsList = document.createElement("ul");
        warnings.forEach((warningText) => {
            const li = document.createElement("li"); // Create a new list item for each warning
            li.textContent = warningText;
            warningsList.appendChild(li);
        });
        bodyEl.appendChild(warningsList); // Append the list of warnings to the modal body
    }

    cancelBtn.style.display = allowCancel ? "inline-block" : "none"; // Display the cancel button based if the allowCancel flag is true

    confirmBtn.onclick = () => {
        closeConfigResultModal();
        if (typeof onConfirm === "function") {
            onConfirm();
        }
    };

    cancelBtn.onclick = () => {
        closeConfigResultModal();
    };

    modal.hidden = false;
}

function handleGenerateConfigButtonClick(event) {
    const button = event.target.closest(".generate-config-btn");
    if (!button) return;

    const interfaceId = button.dataset.interfaceId;
    if (!interfaceId) return;

    handleGenerateConfig(interfaceId).catch((error) => {
        showConfigResultModal({
            title: "Error generating config",
            errors: ["An unexpected error occurred while checking config generation."],
            warnings: [],
            allowCancel: false,
            onConfirm: null
        });
        console.error(error);
    });
}


/*
====================================================================
Event Listeners
====================================================================
*/

document.addEventListener("click", handleToggleButtonClick);
document.addEventListener("click", closeUserMenuOnOutsideClick);
document.addEventListener("mousemove", handleModalMouseMove);
document.addEventListener("mouseup", handleModalMouseUp);
document.addEventListener("click", handleBackdropClickSuppression, true);

document.addEventListener("DOMContentLoaded", function () {
    initDraggableModal();
    initializeMembershipSelectors(document);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSwap", function (event) {
    initDraggableModal();
    initializeMembershipSelectors(event.target);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSettle", focusAndExpandFromUrl);
document.addEventListener("click", handleGenerateConfigButtonClick);
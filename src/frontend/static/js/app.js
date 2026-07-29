/*
====================================================================
Set Z-Index for Modals
====================================================================
*/

let modalZIndexCounter = 1000;

function getNextModalZIndex() {
    modalZIndexCounter += 1;
    return modalZIndexCounter;
}

function bringModalToFront(modal) {
    if (!modal) return;
    const next = getNextModalZIndex();
    modal.style.zIndex = next;
}

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

function closeThisModal(button) {
    const modal = button.closest(".draggable-modal");
    if (!modal) return;

    modal.remove();
}

function applyRuleSelectorSelection(selectorType, button) {
    const modal = button.closest(".draggable-modal");
    if (!modal) return;

    const selectedList = modal.querySelector(".membership-list-selected");
    if (!selectedList) return;

    const selectedItems = Array.from(selectedList.querySelectorAll(".membership-list-item"));

    const selectedIds = selectedItems.map(item => item.dataset.id);
    const selectedNames = selectedItems.map(item => {
        // get only visible text, not hidden input values
        return item.childNodes[0]?.textContent.trim() || item.textContent.trim();
    });

    let hiddenInputId = "";
    let summaryId = "";
    let emptyText = "";

    if (selectorType === "source") {
        hiddenInputId = "rule-source-ids";
        summaryId = "rule-source-summary";
        emptyText = "No source objects selected.";
    } else if (selectorType === "destination") {
        hiddenInputId = "rule-destination-ids";
        summaryId = "rule-destination-summary";
        emptyText = "No destination objects selected.";
    } else if (selectorType === "service") {
        hiddenInputId = "rule-service-ids";
        summaryId = "rule-services-summary";
        emptyText = "No services selected.";
    }

    const hiddenInput = document.getElementById(hiddenInputId);
    const summary = document.getElementById(summaryId);

    if (hiddenInput) {
        hiddenInput.value = selectedIds.join(",");
    }

    if (summary) {
        if (selectedNames.length > 0) {
            summary.innerHTML = selectedNames
                .map(name => `<div>${name}</div>`)
                .join("");
        } else {
            summary.textContent = emptyText;
        }
    }

    closeThisModal(button);
}

function makeModalDraggable(modal, header) {
    if (!modal || !header || header.dataset.dragBound === "true") return;
    header.dataset.dragBound = "true";

    bringModalToFront(modal);

    header.addEventListener("mousedown", function (e) {
        if (e.button !== 0) return;

        bringModalToFront(modal);

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
        bringModalToFront(modal);
    });

    modal.addEventListener("mousedown", function () {
        bringModalToFront(modal);
    });
}
function initDraggableModals() {
    document.querySelectorAll(".draggable-modal").forEach((modal) => {
        const header = modal.querySelector(".draggable-modal-header");
        makeModalDraggable(modal, header);
    });
}

function handleModalMouseMove(e) {
    if (!draggableModalState.activeDrag) return;

    const { modal, offsetX, offsetY } = draggableModalState.activeDrag;

    const newLeft = e.clientX - offsetX;
    const newTop = e.clientY - offsetY;

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

document.addEventListener("mousemove", handleModalMouseMove);
document.addEventListener("mouseup", handleModalMouseUp);
document.addEventListener("click", handleBackdropClickSuppression, true);
document.addEventListener("DOMContentLoaded", initDraggableModals);
document.body.addEventListener("htmx:afterSwap", initDraggableModals);


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
    initDraggableModals();
    initializeMembershipSelectors(document);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSwap", function (event) {
    initDraggableModals();
    initializeMembershipSelectors(event.target);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSettle", focusAndExpandFromUrl);

function openRuleSelectorModal(selectorType, url) {
    const existing = document.getElementById(`submodal-${selectorType}`);
    if (existing) {
        existing.style.zIndex = getNextModalZIndex();
        return;
    }

    let selectedIds = "";

    if (selectorType === "source") {
        selectedIds = document.getElementById("rule-source-ids")?.value || "";
    } else if (selectorType === "destination") {
        selectedIds = document.getElementById("rule-destination-ids")?.value || "";
    } else if (selectorType === "service") {
        selectedIds = document.getElementById("rule-service-ids")?.value || "";
    }

    const separator = url.includes("?") ? "&" : "?";
    const fullUrl = `${url}${separator}selected_ids=${encodeURIComponent(selectedIds)}`;

    htmx.ajax("GET", fullUrl, {
        target: "#submodal-container",
        swap: "beforeend"
    });
}


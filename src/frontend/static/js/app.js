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

const RULE_SELECTOR_CONFIG = {
    source_address: {
        inputId: "rule-source-address-ids",
        summaryId: "rule-source-addresses-summary",
        emptyText: "No source addresses selected.",
    },

    destination_address: {
        inputId: "rule-destination-address-ids",
        summaryId: "rule-destination-addresses-summary",
        emptyText: "No destination addresses selected.",
    },

    source_service: {
        inputId: "rule-source-service-ids",
        summaryId: "rule-source-services-summary",
        emptyText: "No source services selected.",
    },

    destination_service: {
        inputId: "rule-destination-service-ids",
        summaryId: "rule-destination-services-summary",
        emptyText: "No destination services selected.",
    },
};


function openRuleSelectorModal(selectorType, url) {
    const config = RULE_SELECTOR_CONFIG[selectorType];

    if (!config) {
        console.error(`Unsupported rule selector type: ${selectorType}`);
        return;
    }

    const existing = document.getElementById(`submodal-${selectorType}`);

    if (existing) {
        existing.style.zIndex = getNextModalZIndex();
        return;
    }

    const selectedInput = document.getElementById(config.inputId);
    const selectedIds = selectedInput?.value || "";

    const separator = url.includes("?") ? "&" : "?";
    const fullUrl = (
        `${url}${separator}selected_ids=${encodeURIComponent(selectedIds)}`
    );

    htmx.ajax("GET", fullUrl, {
        target: "#submodal-container",
        swap: "beforeend",
    });
}


function applyRuleSelectorSelection(selectorType, button) {
    const config = RULE_SELECTOR_CONFIG[selectorType];

    if (!config) {
        console.error(`Unsupported rule selector type: ${selectorType}`);
        return;
    }

    const modal = button.closest(".draggable-modal");

    if (!modal) {
        console.error("Could not find parent selector modal.");
        return;
    }

    const selectedList = modal.querySelector(".membership-list-selected");

    if (!selectedList) {
        console.error("Could not find selected-items list in selector modal.");
        return;
    }

    const selectedItems = Array.from(
        selectedList.querySelectorAll(".membership-list-item")
    );

    const selectedIds = selectedItems.map((item) => item.dataset.id);

    const selectedNames = selectedItems.map((item) => {
        // Prefer explicit data-name if present in the template.
        if (item.dataset.name) {
            return item.dataset.name;
        }

        // Fall back to visible text, excluding the hidden input.
        return item.childNodes[0]?.textContent.trim() || item.textContent.trim();
    });

    const hiddenInput = document.getElementById(config.inputId);
    const summary = document.getElementById(config.summaryId);

    if (!hiddenInput) {
        console.error(
            `Could not find hidden input "${config.inputId}" for ${selectorType}.`
        );
        return;
    }

    if (!summary) {
        console.error(
            `Could not find summary "${config.summaryId}" for ${selectorType}.`
        );
        return;
    }

    // Stores typed IDs, for example:
    // address-1,addressgroup-2
    // service-4,servicegroup-3
    hiddenInput.value = selectedIds.join(",");

    if (selectedNames.length === 0) {
        summary.textContent = config.emptyText;
    } else {
        summary.innerHTML = selectedNames
            .map((name) => `<div>${name}</div>`)
            .join("");
    }

    closeThisModal(button);
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

    const toggleVisibilityIcon = (isExpanded) => {
        const icon = openedRow.querySelector(".row-visibility-icon");
        if (!icon) return;

        const openIcon = icon.dataset.eyeOpen;
        const closedIcon = icon.dataset.eyeClosed;
        if (!openIcon || !closedIcon) return;

        icon.src = isExpanded ? closedIcon : openIcon;
    };

    if (detailsRow.style.display === "table-row") {
        detailsRow.style.display = "none";
        openedRow.classList.remove("expanded-row");
        toggleVisibilityIcon(false);
    } else {
        detailsRow.style.display = "table-row";
        openedRow.classList.add("expanded-row");
        toggleVisibilityIcon(true);
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
Rule Reordering
====================================================================
*/

function getCsrfToken() {
    const cookieValue = document.cookie
        .split(";")
        .map((cookie) => cookie.trim())
        .find((cookie) => cookie.startsWith("csrftoken="));

    if (!cookieValue) return "";

    return decodeURIComponent(cookieValue.split("=")[1]);
}

function getRuleMainRows(rulesBody) {
    return Array.from(rulesBody.querySelectorAll("tr[id^='row-rule-']"));
}

function getRuleIdFromMainRow(mainRow) {
    const fullId = mainRow?.id || "";
    if (!fullId.startsWith("row-rule-")) return null;

    const idValue = Number(fullId.replace("row-rule-", ""));
    return Number.isInteger(idValue) ? idValue : null;
}

function getDetailsRowForMainRow(mainRow) {
    if (!mainRow?.id) return null;
    return document.getElementById(mainRow.id.replace("row-", "details-"));
}

function moveRuleRowPair(draggedMainRow, targetMainRow, placeBefore) {
    if (!draggedMainRow || !targetMainRow || draggedMainRow === targetMainRow) return;

    const draggedDetailsRow = getDetailsRowForMainRow(draggedMainRow);
    const targetDetailsRow = getDetailsRowForMainRow(targetMainRow);

    if (placeBefore) {
        targetMainRow.parentNode.insertBefore(draggedMainRow, targetMainRow);
        if (draggedDetailsRow) {
            targetMainRow.parentNode.insertBefore(draggedDetailsRow, targetMainRow);
        }
    } else {
        const insertionAnchor = targetDetailsRow?.nextSibling || targetMainRow.nextSibling;
        targetMainRow.parentNode.insertBefore(draggedMainRow, insertionAnchor);
        if (draggedDetailsRow) {
            targetMainRow.parentNode.insertBefore(draggedDetailsRow, insertionAnchor);
        }
    }
}

function refreshRulesTableContent(rulesBody) {
    if (!rulesBody) return;

    const contentUrl = rulesBody.dataset.contentUrl;
    const filterId = rulesBody.dataset.filterId;
    if (!contentUrl || !filterId) return;

    const params = new URLSearchParams(window.location.search);
    const filterName = params.get("filter_name") || "";
    const refreshUrl = `${contentUrl}?filter_id=${encodeURIComponent(filterId)}&filter_name=${encodeURIComponent(filterName)}`;

    // Rules are rendered in different content roots depending on page context.
    const refreshTarget = document.querySelector("#rules-content")
        ? "#rules-content"
        : "#filters-content";
    const contentRoot = document.querySelector(refreshTarget);
    let savedScrollTop = 0;

    if (contentRoot) {
        const scrollContainer = contentRoot.querySelector(".table-container");
        if (scrollContainer) {
            savedScrollTop = scrollContainer.scrollTop;
        }
    }

    htmx.ajax("GET", refreshUrl, {
        target: refreshTarget,
        swap: "innerHTML",
    }).then(() => {
        const updatedRoot = document.querySelector(refreshTarget);
        if (!updatedRoot) return;

        const updatedScrollContainer = updatedRoot.querySelector(".table-container");
        if (updatedScrollContainer) {
            updatedScrollContainer.scrollTop = savedScrollTop;
        }
    });
}

function initializeRuleRowDragAndDrop(root = document) {
    const rulesBody = root.querySelector("#rules-table");

    if (!rulesBody || rulesBody.dataset.dragInitialized === "true") {
        return;
    }

    const reorderUrl = rulesBody.dataset.reorderUrl;
    const filterId = rulesBody.dataset.filterId;

    if (!reorderUrl || !filterId) {
        return;
    }

    rulesBody.dataset.dragInitialized = "true";

    let draggedMainRow = null;

    // Only include actual draggable rule rows.
    // Do not include any expanded/detail/child rows in the sequence calculation.
    const getMainRows = () => {
        return Array.from(
            rulesBody.querySelectorAll(
                "tr[data-rules-draggable='true'][id^='row-rule-']"
            )
        );
    };

    getMainRows().forEach((row) => {
        row.addEventListener("dragstart", (event) => {
            draggedMainRow = row;
            row.classList.add("dragging");

            if (event.dataTransfer) {
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", row.id);
            }
        });

        row.addEventListener("dragend", () => {
            row.classList.remove("dragging");
            draggedMainRow = null;
        });
    });

    rulesBody.addEventListener("dragover", (event) => {
        if (!draggedMainRow) {
            return;
        }

        event.preventDefault();

        const targetMainRow = event.target.closest(
            "tr[data-rules-draggable='true'][id^='row-rule-']"
        );

        if (!targetMainRow || targetMainRow === draggedMainRow) {
            return;
        }

        const rect = targetMainRow.getBoundingClientRect();
        const placeBefore = event.clientY < rect.top + rect.height / 2;

        moveRuleRowPair(draggedMainRow, targetMainRow, placeBefore);
    });

    rulesBody.addEventListener("drop", async (event) => {
        if (!draggedMainRow) {
            return;
        }

        event.preventDefault();

        const ruleId = getRuleIdFromMainRow(draggedMainRow);

        if (!ruleId) {
            return;
        }

        // Get the rows after moveRuleRowPair() has updated the DOM.
        const mainRows = getMainRows();
        const rowIndex = mainRows.indexOf(draggedMainRow);

        if (rowIndex === -1) {
            return;
        }

        // The backend expects a 1-indexed sequence:
        // first row = 1, second row = 2, etc.
        const newSequence = rowIndex + 1;

        const csrfToken = getCsrfToken();

        try {
            const response = await fetch(reorderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-CSRFToken": csrfToken,
                },
                body: new URLSearchParams({
                    rule_id: String(ruleId),
                    filter_id: String(filterId),
                    new_sequence: String(newSequence),
                }),
            });

            if (!response.ok) {
                console.error("Failed to reorder rules.", await response.text());
                refreshRulesTableContent(rulesBody);
                return;
            }

            refreshRulesTableContent(rulesBody);
        } catch (error) {
            console.error("Error while reordering rules.", error);
            refreshRulesTableContent(rulesBody);
        }
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
    initDraggableModals();
    initializeMembershipSelectors(document);
    initializeRuleRowDragAndDrop(document);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSwap", function (event) {
    initDraggableModals();
    initializeMembershipSelectors(event.target);
    initializeRuleRowDragAndDrop(event.target);
    focusAndExpandFromUrl();
});

document.addEventListener("htmx:afterSettle", focusAndExpandFromUrl);
document.addEventListener("click", handleGenerateConfigButtonClick);

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

    ingoing_filter: {
        inputId: "interface-ingoing-filter-ids",
        summaryId: "interface-ingoing-filters-summary",
        emptyText: "No ingoing filters selected.",
    },

    outgoing_filter: {
        inputId: "interface-outgoing-filter-ids",
        summaryId: "interface-outgoing-filters-summary",
        emptyText: "No outgoing filters selected.",
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

// Turns the interface table into a JavaScript list of interface objects.
function getDeviceInterfaceDraftFromTable(table) {
    if (!table) return []; // If there is no table, return an empty list.

    // Finds every row in the table body and processes each one. Array.from converts the browser’s list of rows into a normal JavaScript array.
    return Array.from(table.querySelectorAll("tbody tr")).map((row) => {
        const cells = row.querySelectorAll("td");
        const name = cells[0]?.textContent?.trim() || "";
        if (!name) return null; // A row without a name is ignored.

        return {
            id: row.dataset.interfaceId ? Number(row.dataset.interfaceId) : null,
            name,
            description: cells[1]?.textContent?.trim() || "",
            type: cells[2]?.textContent?.trim() || "",
            vrf: cells[3]?.textContent?.trim() || "",
        };
    }).filter(Boolean); // Removes any null results, such as rows with no name.
}

// Getting the current draft on the parent device form.
function getDeviceInterfaceDraftState(form) {
    if (!form) return ""; // If there’s no form, return an empty string.

    // Checks the form’s data-interface-draft value.
    if (form.dataset.interfaceDraft) {
        return form.dataset.interfaceDraft;
    }

    // If the form doesn’t have a draft saved there, it looks for the hidden input named interface_fields.
    const hiddenInput = form.querySelector('input[name="interface_fields"]');

    // // If the hidden input has a value, the function copies it onto the form’s dataset and returns it.
    if (hiddenInput && hiddenInput.value) {
        form.dataset.interfaceDraft = hiddenInput.value;
        return hiddenInput.value;
    }

    return ""; // If neither place contains a draft, return an empty string.
}

// Opening the interface modal
function openDeviceInterfaceModal(button) {
    const form = button.closest("form"); // Finds the device form containing the button.

    // Gets the modal URL from the button’s data-device-interface-url attribute. If there is no URL, stop.
    const url = button.dataset.deviceInterfaceUrl;
    if (!url) return;

    const draftState = getDeviceInterfaceDraftState(form); // Gets the current draft from the parent form, if one exists.

    // Creates URL query parameters and includes the draft under the name interface_fields when there is draft data.
    const params = new URLSearchParams();
    if (draftState) {
        params.set("interface_fields", draftState);
    }

    const fullUrl = params.toString() ? `${url}?${params.toString()}` : url; // If there are query parameters, adds them to the URL. Otherwise, uses the URL as-is.
    htmx.ajax("GET", fullUrl, {
        target: "#submodal-container",
        swap: "innerHTML",
    });
}

// A helper function for finding the device form that contains the hidden interface field.
function getDeviceInterfaceParentForm() {
    // It finds the hidden input, then returns its closest form. If there is no hidden input, it returns null.
    const hiddenInput = document.getElementById("device-interface-field-input");
    return hiddenInput ? hiddenInput.closest("form") : null;
}

// Updates the interface names and count shown in the main device form.
function updateDeviceInterfaceSummaryInParentForm(draftList) {
    // Finds the form; if it isn’t present, there’s nothing to update.
    const parentForm = getDeviceInterfaceParentForm();
    if (!parentForm) return;

    // Looks for the elements that display the interface names and count.
    const namesEl = parentForm.querySelector(".device-interface-names");
    const countEl = parentForm.querySelector(".device-interface-count");
    const emptyState = parentForm.querySelector(".empty-state");

    // If either is missing, the function creates those display elements.
    if (!namesEl || !countEl) {
        // Inserts that paragraph before the Manage button and hides the “No interfaces” message if it exists.
        const formContainer = parentForm.querySelector(".device-interfaces-group");
        if (!formContainer) return;

        const names = document.createElement("span");
        names.className = "device-interface-names";
        const count = document.createElement("span");
        count.className = "device-interface-count";
        const wrapper = document.createElement("p");
        wrapper.className = "device-interfaces";
        wrapper.appendChild(names);
        wrapper.appendChild(document.createTextNode(" "));
        wrapper.appendChild(count);
        formContainer.insertBefore(wrapper, formContainer.querySelector("button"));

        if (formContainer.querySelector(".empty-state")) {
            formContainer.querySelector(".empty-state").style.display = "none";
        }
    }

    // Finds the display elements again, including the empty-state message.
    const visibleNames = parentForm.querySelector(".device-interface-names");
    const visibleCount = parentForm.querySelector(".device-interface-count");
    const visibleEmpty = parentForm.querySelector(".empty-state");

    if (!visibleNames || !visibleCount) return; // Stops if the required display elements could not be found.

    // If the draft has no interfaces, clear the names, show (0), and show the empty-state message.
    if (draftList.length === 0) {
        visibleNames.textContent = "";
        visibleCount.textContent = "(0)";
        if (visibleEmpty) visibleEmpty.style.display = "";
        return;
    }

    // Displays the interface names separated by commas and shows the total count.
    visibleNames.textContent = draftList.map((entry) => entry.name).join(", ");
    visibleCount.textContent = `(${draftList.length})`;
    if (visibleEmpty) visibleEmpty.style.display = "none";
}

// Applying the modal changes to the parent form
function applyDeviceInterfaceSelection(button) {
    // Finds the modal containing the clicked button. If there isn’t one, stop.
    const modal = button.closest(".draggable-modal");
    if (!modal) return;

    // Finds the modal’s interface table and converts its rows into a list of interface objects.
    const table = modal.querySelector(".device-interface-table");
    const draftList = getDeviceInterfaceDraftFromTable(table);

    // Finds the main device form. If there’s no parent form, close the modal and stop.
    const parentForm = getDeviceInterfaceParentForm();

    if (!parentForm) {
        closeThisModal(button);
        return;
    }

    // Finds the hidden field that will hold the interface list. If the field doesn’t exist, the code creates one and adds it to the form.
    let hiddenInput = parentForm.querySelector('input[name="interface_fields"]');
    if (!hiddenInput) {
        hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "interface_fields";
        parentForm.appendChild(hiddenInput);
    }

    const draftValue = JSON.stringify(draftList); // Converts the JavaScript list into a JSON string.
    hiddenInput.value = draftValue; // Stores the draft in the hidden input, so it is included when the device form is submitted.
    parentForm.dataset.interfaceDraft = draftValue; // Stores the draft in the form’s dataset, so the modal-opening code can access it next time.

    // Updates the names and count on the parent form, then closes the modal.
    updateDeviceInterfaceSummaryInParentForm(draftList);
    closeThisModal(button);
}

// Adding an interface row
function addDeviceInterfaceRow(button) {
    // Finds the table and its body. If the table body isn’t available, stop.
    const table = button.closest(".device-interface-table");
    const tbody = table?.querySelector("tbody");
    if (!tbody) return;

    const nameInput = table.querySelector("#new-interface-name");
    const descriptionInput = table.querySelector("#new-interface-description");
    const typeInput = table.querySelector("#new-interface-type");
    const vrfInput = table.querySelector("#new-interface-vrf");

    // If no name was entered, show an alert and don’t add a row.
    const name = nameInput?.value.trim() || "";
    if (!name) {
        nameInput?.setCustomValidity("Interface name is required.");
        nameInput?.reportValidity();
        nameInput?.focus();
        return;
    }

    nameInput?.setCustomValidity("");

    const row = document.createElement("tr");
    const fields = [
        name,
        descriptionInput?.value.trim() || "",
        typeInput?.value.trim() || "",
        vrfInput?.value.trim() || "",
    ];

    fields.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        cell.title = value;
        row.appendChild(cell);
    });

    const actionCell = document.createElement("td");
    actionCell.className = "device-interface-actions-column";

    // Adds a delete button and appends the row to the table
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "actions-btn device-interface-icon-button device-interface-delete-button";
    deleteButton.setAttribute("aria-label", "Delete interface");
    deleteButton.setAttribute("title", "Delete interface");
    deleteButton.innerHTML = '<img class="btn-icon actions-icon" src="/static/images/delete.svg" alt="" aria-hidden="true">';
    deleteButton.setAttribute("onclick", "removeDeviceInterfaceRow(this)");
    actionCell.appendChild(deleteButton);
    row.appendChild(actionCell);
    tbody.appendChild(row);

    // Clears the four inputs so the user can enter another interface.
    if (nameInput) nameInput.value = "";
    if (descriptionInput) descriptionInput.value = "";
    if (typeInput) typeInput.value = "";
    if (vrfInput) vrfInput.value = "";
}

// Remove an interface row
function removeDeviceInterfaceRow(button) {
    // Finds the table row containing the clicked delete button and removes it from the page.
    const row = button.closest("tr");
    if (row) row.remove();
}

// Buttons in the initial page
window.addEventListener("DOMContentLoaded", () => {
    // Finds all Add buttons on the page, and set up.
    const addButtons = document.querySelectorAll(".device-interface-add-button");
    addButtons.forEach((button) => {
        if (button.dataset.bound === "true") return;
        button.dataset.bound = "true";
        button.setAttribute("onclick", "addDeviceInterfaceRow(this)");
    });

    // Finds all Delete buttons on the page, and set up.
    const deleteButtons = document.querySelectorAll(".device-interface-delete-button");
    deleteButtons.forEach((button) => {
        if (button.dataset.bound === "true") return;
        button.dataset.bound = "true";
        button.setAttribute("onclick", "removeDeviceInterfaceRow(this)");
    });
});

// Buttons added by HTMX after update
document.body.addEventListener("htmx:afterSwap", () => {
    const addButtons = document.querySelectorAll(".device-interface-add-button");
    addButtons.forEach((button) => {
        if (button.dataset.bound === "true") return;
        button.dataset.bound = "true";
        button.setAttribute("onclick", "addDeviceInterfaceRow(this)");
    });

    const deleteButtons = document.querySelectorAll(".device-interface-delete-button");
    deleteButtons.forEach((button) => {
        if (button.dataset.bound === "true") return;
        button.dataset.bound = "true";
        button.setAttribute("onclick", "removeDeviceInterfaceRow(this)");
    });
});

/*
====================================================================
Interface Filter Draft (Ingoing/Outgoing)
====================================================================
*/

const interfaceFilterDraft = { in: null, out: null };
const interfaceFilterBaseline = { in: null, out: null };
let interfaceFiltersDirty = false;
let showingInterfaceDifferences = false;

function markInterfaceFiltersDirty() {
    interfaceFiltersDirty = true;
    updateInterfaceActionButtonsState();
}

function updateInterfaceActionButtonsState() {
    document.querySelectorAll(".interface-save-btn").forEach((btn) => {
        btn.disabled = !interfaceFiltersDirty;
    });
    document.querySelectorAll(".interface-discard-btn").forEach((btn) => {
        btn.disabled = !interfaceFiltersDirty;
    });
}

function readInterfaceFilterListFromDom(direction) {
    const container = document.querySelector(
        `.objects-interface-table[data-interface-filter-list="${direction}"]`
    );
    if (!container) return [];

    return Array.from(
        container.querySelectorAll(".objects-interface-table-row[data-filter-id]")
    ).map((rowEl) => ({
        id: rowEl.dataset.filterId,
        name: rowEl.dataset.filterName || "",
        description: rowEl.dataset.filterDescription || "",
        enabled: rowEl.dataset.filterEnabled === "true",
    }));
}

function ensureInterfaceFilterDraft(direction) {
    if (!interfaceFilterDraft[direction]) {
        const initial = readInterfaceFilterListFromDom(direction);
        interfaceFilterDraft[direction] = initial;
        interfaceFilterBaseline[direction] = initial.map((item) => ({ ...item }));
    }
    return interfaceFilterDraft[direction];
}

function computeInterfaceFilterDiff(direction) {
    const baseline = interfaceFilterBaseline[direction] || [];
    const current = interfaceFilterDraft[direction] || [];
    const currentIds = new Set(current.map((item) => item.id));
    const baselineIndexById = new Map(baseline.map((item, index) => [item.id, index]));


    const removedBeforeId = new Map();
    let pendingRemoved = [];
    baseline.forEach((item, baselineIndex) => {
        if (currentIds.has(item.id)) {
            if (pendingRemoved.length) {
                removedBeforeId.set(item.id, pendingRemoved);
                pendingRemoved = [];
            }
        } else {
            pendingRemoved.push({ ...item, diffStatus: "removed", previousSequence: baselineIndex + 1 });
        }
    });
    const trailingRemoved = pendingRemoved;

    const combined = [];
    current.forEach((item, index) => {
        const anchoredRemovals = removedBeforeId.get(item.id);
        if (anchoredRemovals) combined.push(...anchoredRemovals);

        const baselineIndex = baselineIndexById.get(item.id);
        if (baselineIndex === undefined) {
            combined.push({ ...item, diffStatus: "added", displaySequence: index + 1 });
        } else {
            combined.push({
                ...item,
                diffStatus: "unchanged",
                enabledChanged: item.enabled !== baseline[baselineIndex].enabled,
                previousEnabled: baseline[baselineIndex].enabled,
                sequenceChanged: index !== baselineIndex,
                previousSequence: baselineIndex + 1,
                displaySequence: index + 1,
            });
        }
    });
    combined.push(...trailingRemoved);

    return combined;
}

function discardInterfaceFilterChanges(button) {
    if (!interfaceFiltersDirty) return;

    const shouldDiscard = confirm("Discard all unsaved filter changes?");
    if (!shouldDiscard) return;

    ["in", "out"].forEach((direction) => {
        ensureInterfaceFilterDraft(direction);
        interfaceFilterDraft[direction] = (interfaceFilterBaseline[direction] || []).map((item) => ({ ...item }));
    });

    interfaceFiltersDirty = false;
    showingInterfaceDifferences = false;
    document.querySelectorAll(".interface-diff-btn").forEach((btn) => {
        btn.classList.remove("active");
        btn.textContent = "Show Differences";
    });

    renderInterfaceFilterRow("in");
    renderInterfaceFilterRow("out");
    updateInterfaceActionButtonsState();
}

function toggleInterfaceFilterDifferences(button) {
    showingInterfaceDifferences = !showingInterfaceDifferences;

    document.querySelectorAll(".interface-diff-btn").forEach((btn) => {
        btn.classList.toggle("active", showingInterfaceDifferences);
        btn.textContent = showingInterfaceDifferences ? "Hide Differences" : "Show Differences";
    });

    renderInterfaceFilterRow("in");
    renderInterfaceFilterRow("out");
}

function toggleInterfaceFilterEnabled(direction, filterId, button) {
    const draft = ensureInterfaceFilterDraft(direction);
    const entry = draft.find((item) => item.id === filterId);
    if (!entry) return;

    entry.enabled = !entry.enabled;
    markInterfaceFiltersDirty();

    if (showingInterfaceDifferences) {
        renderInterfaceFilterRow(direction);
        return;
    }

    button.dataset.enabled = entry.enabled ? "true" : "false";
    button.setAttribute("aria-checked", entry.enabled ? "true" : "false");
    button.setAttribute("aria-label", entry.enabled ? "Enabled" : "Disabled");
    button.title = entry.enabled ? "Enabled" : "Disabled";

    const rowEl = button.closest(".objects-interface-table-row");
    if (rowEl) rowEl.dataset.filterEnabled = entry.enabled ? "true" : "false";
}

function toggleSelectorFilterEnabled(button) {
    const isEnabled = button.dataset.enabled === "true";
    const nowEnabled = !isEnabled;
    button.dataset.enabled = nowEnabled ? "true" : "false";
    button.setAttribute("aria-checked", nowEnabled ? "true" : "false");
    button.setAttribute("aria-label", nowEnabled ? "Enabled" : "Disabled");
    button.title = nowEnabled ? "Enabled" : "Disabled";

    const item = button.closest(".membership-list-item");
    if (item) item.dataset.enabled = button.dataset.enabled;
}


function openInterfaceRowFilterEditor(direction, baseUrl) {
    const draft = ensureInterfaceFilterDraft(direction);
    const selectedIds = draft.map((item) => item.id).join(",");

    const separator = baseUrl.includes("?") ? "&" : "?";
    const fullUrl = `${baseUrl}${separator}selected_ids=${encodeURIComponent(selectedIds)}`;

    htmx.ajax("GET", fullUrl, {
        target: "#modal-container",
        swap: "innerHTML",
    }).then(() => reconcileInterfaceSelectorWithDraft(direction));
}

function reconcileInterfaceSelectorWithDraft(direction) {
    const draft = ensureInterfaceFilterDraft(direction);
    const selectedList = document.querySelector("#modal-container .membership-list-selected");
    const availableList = document.querySelector("#modal-container .membership-list-available");
    if (!selectedList || !availableList) return;

    const itemsById = new Map();
    [...selectedList.children, ...availableList.children].forEach((item) => {
        itemsById.set(item.dataset.id, item);
    });

    draft.forEach((entry) => {
        const item = itemsById.get(String(entry.id));
        if (!item) return;

        item.dataset.enabled = entry.enabled ? "true" : "false";

        const toggle = item.querySelector(".filter-enabled-toggle");
        if (toggle) {
            toggle.dataset.enabled = item.dataset.enabled;
            toggle.setAttribute("aria-checked", item.dataset.enabled);
            toggle.setAttribute("aria-label", entry.enabled ? "Enabled" : "Disabled");
            toggle.title = entry.enabled ? "Enabled" : "Disabled";
        }

        selectedList.appendChild(item);
    });
}

function applyInterfaceRowFilterSelection(selectorType, direction, button) {
    const modal = button.closest(".draggable-modal");
    if (!modal) return;

    const selectedList = modal.querySelector(".membership-list-selected");
    if (!selectedList) return;

    const items = Array.from(selectedList.querySelectorAll(".membership-list-item"));

    interfaceFilterDraft[direction] = items.map((item) => ({
        id: item.dataset.id,
        name: item.dataset.name || "",
        description: item.dataset.description || "",
        enabled: item.dataset.enabled !== "false",
    }));

    renderInterfaceFilterRow(direction);
    markInterfaceFiltersDirty();

    const modalContainer = document.getElementById("modal-container");
    if (modalContainer) modalContainer.innerHTML = "";
}

function renderInterfaceFilterRow(direction) {
    ensureInterfaceFilterDraft(direction);
    const currentEntries = interfaceFilterDraft[direction] || [];
    const entries = showingInterfaceDifferences
        ? computeInterfaceFilterDiff(direction)
        : currentEntries;

    const countCell = document.querySelector(`[data-interface-filter-count="${direction}"]`);
    if (countCell) {
        const textEl = countCell.querySelector(".cell-text") || countCell;
        textEl.textContent = currentEntries.length;
    }

    const listContainer = document.querySelector(
        `.objects-interface-table[data-interface-filter-list="${direction}"]`
    );
    if (!listContainer) return;

    listContainer.querySelectorAll(".objects-interface-table-row").forEach((rowEl) => rowEl.remove());
    const emptyEl = listContainer.querySelector(".objects-interface-empty");

    if (entries.length === 0) {
        if (emptyEl) emptyEl.style.display = "";
        return;
    }
    if (emptyEl) emptyEl.style.display = "none";

    entries.forEach((entry, index) => {
        const rowEl = document.createElement("div");
        rowEl.className = "objects-interface-table-row";
        if (entry.diffStatus === "added") rowEl.classList.add("row-diff-added");
        if (entry.diffStatus === "removed") rowEl.classList.add("row-diff-removed");
        rowEl.dataset.filterId = entry.id;
        rowEl.dataset.filterName = entry.name;
        rowEl.dataset.filterDescription = entry.description;
        rowEl.dataset.filterEnabled = entry.enabled ? "true" : "false";

        rowEl.innerHTML = `
            <div class="objects-interface-table-cell truncate"></div>
            <div class="objects-interface-table-cell truncate"></div>
            <div class="objects-interface-table-cell truncate"></div>
            <div class="objects-interface-table-cell truncate">
                <button type="button" class="btn-reset center-box filter-enabled-toggle" role="switch"
                    aria-checked="${entry.enabled ? "true" : "false"}" data-enabled="${entry.enabled ? "true" : "false"}"
                    aria-label="${entry.enabled ? "Enabled" : "Disabled"}" title="${entry.enabled ? "Enabled" : "Disabled"}">
                    <span class="filter-enabled-toggle-check"></span>
                </button>
            </div>
        `;

        rowEl.children[0].textContent = entry.diffStatus === "removed" ? entry.previousSequence : (entry.displaySequence ?? index + 1);
        rowEl.children[1].textContent = entry.name;
        rowEl.children[2].textContent = entry.description;

        if (entry.sequenceChanged && entry.previousSequence !== entry.displaySequence) {
            rowEl.children[0].textContent = `${entry.previousSequence} → ${entry.displaySequence}`;
            rowEl.children[0].title = `Moved from position ${entry.previousSequence} to ${entry.displaySequence}`;
        }

        if (entry.enabledChanged) {
            const enabledCell = rowEl.children[3];
            enabledCell.classList.add(entry.enabled ? "cell-diff-enabled-on" : "cell-diff-enabled-off");
            enabledCell.title = `Changed from ${entry.previousEnabled ? "Enabled" : "Disabled"} to ${entry.enabled ? "Enabled" : "Disabled"}`;
        }

        const toggleButton = rowEl.querySelector(".filter-enabled-toggle");
        if (entry.diffStatus === "removed") {
            toggleButton.disabled = true;
        } else {
            toggleButton.addEventListener("click", (event) => {
                event.stopPropagation();
                toggleInterfaceFilterEnabled(direction, entry.id, toggleButton);
            });
        }

        listContainer.appendChild(rowEl);
    });
}

function encodeInterfaceFilterSelection(direction) {
    const draft = ensureInterfaceFilterDraft(direction);
    return draft.map((item) => `${item.id}:${item.enabled ? "true" : "false"}`).join(",");
}

async function saveInterfaceFilterChanges(button) {
    const interfaceId = button.dataset.interfaceId;
    const saveUrl = button.dataset.saveUrl;
    if (!interfaceId || !saveUrl) return;

    button.disabled = true;

    try {
        const response = await fetch(saveUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "X-CSRFToken": getCsrfToken(),
            },
            body: new URLSearchParams({
                interface_id: interfaceId,
                ingoing_filter_ids: encodeInterfaceFilterSelection("in"),
                outgoing_filter_ids: encodeInterfaceFilterSelection("out"),
            }),
        });

        if (!response.ok) {
            console.error("Failed to save interface filters.", await response.text());
            alert("Unable to save filter changes. Please try again.");
            return;
        }

        interfaceFiltersDirty = false;
        ["in", "out"].forEach((direction) => {
            interfaceFilterBaseline[direction] = (interfaceFilterDraft[direction] || []).map((item) => ({ ...item }));
        });
        updateInterfaceActionButtonsState();
        if (showingInterfaceDifferences) {
            renderInterfaceFilterRow("in");
            renderInterfaceFilterRow("out");
        }
    } catch (error) {
        console.error("Error while saving interface filters.", error);
        alert("Unable to save filter changes. Please try again.");
    } finally {
        updateInterfaceActionButtonsState();
    }
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

    if (!ipv4Input && !ipv6Input) {
        event.preventDefault();
        ipv4InputField?.setCustomValidity("Please enter at least one IPv4 or IPv6 value.");
        ipv4InputField?.reportValidity();
    }

    ipv4InputField?.setCustomValidity("");
    ipv6InputField?.setCustomValidity("");


}


/*
====================================================================
Membership Selectors
====================================================================
*/

function initializeMembershipSelectors(root = document) {
    root.querySelectorAll(".membership-selector").forEach((selector) => {
        if (selector.dataset.membershipInitialized === "true") {
            return;
        }
        selector.dataset.membershipInitialized = "true";

        const inputName = selector.dataset.inputName;
        const isFilterSelector = selector.dataset.selectorType === "ingoing_filter"
            || selector.dataset.selectorType === "outgoing_filter";
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

        function ensureFilterEnabledToggle(item) {
            if (item.querySelector(".filter-enabled-toggle")) return;

            if (item.dataset.enabled === undefined) {
                item.dataset.enabled = "true";
            }

            const enabled = item.dataset.enabled !== "false";
            const button = document.createElement("button");
            button.type = "button";
            button.className = "btn-reset center-box filter-enabled-toggle";
            button.setAttribute("role", "switch");
            button.dataset.enabled = enabled ? "true" : "false";
            button.setAttribute("aria-checked", enabled ? "true" : "false");
            button.setAttribute("aria-label", enabled ? "Enabled" : "Disabled");
            button.title = enabled ? "Enabled" : "Disabled";
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                toggleSelectorFilterEnabled(button);
            });

            const check = document.createElement("span");
            check.className = "filter-enabled-toggle-check";
            button.appendChild(check);

            item.appendChild(button);
        }

        function removeFilterEnabledToggle(item) {
            item.querySelector(".filter-enabled-toggle")?.remove();
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

            if (isFilterSelector) {
                if (targetList === selectedList) {
                    ensureFilterEnabledToggle(draggedItem);
                } else {
                    removeFilterEnabledToggle(draggedItem);
                }
            }
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

// Rows that also navigate on double-click wait before expanding,
// so a double-click doesn't open and close the row before redirecting.
const ROW_DBLCLICK_DELAY_MS = 180;
const pendingRowExpands = {};

function expandRowDelayed(event, rowId) {
    if (event.detail > 1) return;

    clearTimeout(pendingRowExpands[rowId]);
    pendingRowExpands[rowId] = setTimeout(() => {
        delete pendingRowExpands[rowId];
        expandRow(rowId);
    }, ROW_DBLCLICK_DELAY_MS);
}

function navigateFromRow(event, rowId, url) {
    if (event.target.closest("button, a")) return;

    clearTimeout(pendingRowExpands[rowId]);
    delete pendingRowExpands[rowId];
    window.location.href = url;
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

function closeConfigResultModal() {
    const modal = document.getElementById("config-result-modal");
    if (!modal) return;

    modal.hidden = true;
}

function handleGenerateConfigButtonClick(event) {
    const button = event.target.closest(".generate-config-btn");
    if (!button) return;

    if (interfaceFiltersDirty) {
        const proceed = confirm(
            "You have unsaved filter changes. Generate ACL anyway without saving?"
        );
        if (!proceed) return;
    }

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
    if (!contentUrl) return;

    const refreshUrl = contentUrl;

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
Tag List Overflow
====================================================================
*/

function initTagOverflow(root = document) {
    root.querySelectorAll(".tag-list-container").forEach((container) => {
        const previousIndicator = container.querySelector(".tag-overflow-indicator");
        previousIndicator?.remove();

        const items = Array.from(container.querySelectorAll(".tag-item"));
        items.forEach((item) => {
            item.style.display = "";
        });

        if (items.length === 0 || container.scrollWidth <= container.clientWidth) {
            return;
        }

        const containerWidth = container.clientWidth;
        const indicator = document.createElement("span");
        indicator.className = "cell-text truncate tag-item tag-pill tag-pill--muted tag-overflow-indicator";
        const indicatorWidth = measureIndicatorWidth(container, indicator);

        let usedWidth = 0;
        let firstHiddenIndex = items.length;
        for (let i = 0; i < items.length; i += 1) {
            usedWidth += outerWidth(items[i]);
            if (usedWidth > containerWidth - indicatorWidth) {
                firstHiddenIndex = i;
                break;
            }
        }

        const hiddenItems = items.slice(firstHiddenIndex);
        if (hiddenItems.length === 0) {
            return;
        }

        hiddenItems.forEach((item) => {
            item.style.display = "none";
        });

        indicator.textContent = `+${hiddenItems.length}`;
        indicator.title = hiddenItems.map((item) => item.title || item.textContent.trim()).join(", ");
        container.appendChild(indicator);
    });
}

function outerWidth(element) {
    const marginRight = parseFloat(getComputedStyle(element).marginRight) || 0;
    return element.offsetWidth + marginRight;
}

function measureIndicatorWidth(container, indicator) {
    indicator.textContent = "+99";
    indicator.style.visibility = "hidden";
    indicator.style.position = "absolute";
    container.appendChild(indicator);
    const width = outerWidth(indicator);
    indicator.remove();
    indicator.style.visibility = "";
    indicator.style.position = "";
    return width;
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
    initTagOverflow(document);
});

document.addEventListener("htmx:afterSwap", function (event) {
    initDraggableModals();
    initializeMembershipSelectors(event.target);
    initializeRuleRowDragAndDrop(event.target);
    focusAndExpandFromUrl();
    initTagOverflow(event.target);
});

document.addEventListener("htmx:afterSettle", focusAndExpandFromUrl);
document.addEventListener("click", handleGenerateConfigButtonClick);

document.addEventListener("click", function (event) {
    if (!interfaceFiltersDirty) return;

    const link = event.target.closest("a[href]");
    if (!link || link.target === "_blank") return;
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    const proceed = confirm("You have unsaved filter changes that haven't been saved. Leave this page anyway?");
    if (!proceed) {
        event.preventDefault();
        return;
    }

    // Confirmed via the custom dialog above; suppress the native beforeunload prompt for this navigation.
    interfaceFiltersDirty = false;
});

window.addEventListener("beforeunload", function (event) {
    if (!interfaceFiltersDirty) return;

    event.preventDefault();
});

let tagOverflowResizeTimeout = null;
window.addEventListener("resize", function () {
    clearTimeout(tagOverflowResizeTimeout);
    tagOverflowResizeTimeout = setTimeout(() => initTagOverflow(document), 150);
});

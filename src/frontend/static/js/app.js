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

function closeModal(event) {
    document.getElementById('modal-container').innerHTML = '';
}
/* UNIMAP Profile picture viewer */

(function () {
    const button = document.getElementById("openOwnProfilePicture");
    if (!button) return;

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value ?? "";
        return div.innerHTML;
    }

    function openViewer(name, url) {
        document.getElementById("profilePictureViewer")?.remove();

        const viewer = document.createElement("div");
        viewer.className = "profile-picture-viewer";
        viewer.id = "profilePictureViewer";
        viewer.innerHTML = `
            <div class="profile-picture-viewer-backdrop" data-close-profile-viewer></div>
            <section class="profile-picture-viewer-panel" role="dialog" aria-modal="true" aria-label="Profile picture">
                <button type="button" class="profile-picture-viewer-close" data-close-profile-viewer aria-label="Close">×</button>
                ${url
                    ? `<img src="${url}" alt="${escapeHtml(name || "Profile picture")}">`
                    : `<div class="profile-picture-viewer-initials">${escapeHtml((name || "UN").trim().split(/\\s+/).map(x => x[0]).slice(0,2).join("").toUpperCase())}</div>`
                }
                <h2>${escapeHtml(name || "UNIMAP user")}</h2>
            </section>
        `;

        document.body.appendChild(viewer);
        document.body.classList.add("profile-picture-viewer-open");
    }

    function closeViewer() {
        document.getElementById("profilePictureViewer")?.remove();
        document.body.classList.remove("profile-picture-viewer-open");
    }

    button.addEventListener("click", () => {
        openViewer(button.dataset.profileName, button.dataset.profilePicture || "");
    });

    document.addEventListener("click", event => {
        if (event.target.closest("[data-close-profile-viewer]")) closeViewer();
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeViewer();
    });
})();

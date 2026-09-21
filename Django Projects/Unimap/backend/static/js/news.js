document.addEventListener("DOMContentLoaded", () => {
    const newsContainer = document.getElementById("news");
    const newsForm = document.getElementById("newsForm");
    const composer = document.getElementById("newsComposer");
    const openComposer = document.getElementById("openNewsComposer");
    const closeComposer = document.getElementById("closeNewsComposer");
    const attachmentInput = document.getElementById("newsAttachments");
    const attachmentList = document.getElementById("attachmentList");

    let currentTab = "all";
    let currentScope = "all";
    let selectedFiles = [];

    /* ---------------------------------------------------------
       ICONS
    --------------------------------------------------------- */

    const icons = {
        studyGroup: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
        `,

        campusNews: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M4 4h16v16H4z"/>
                <path d="M8 8h8"/>
                <path d="M8 12h8"/>
                <path d="M8 16h5"/>
            </svg>
        `,

        refresh: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M20 11a8.1 8.1 0 0 0-15.5-2"/>
                <path d="M4 4v5h5"/>
                <path d="M4 13a8.1 8.1 0 0 0 15.5 2"/>
                <path d="M20 20v-5h-5"/>
            </svg>
        `,

        file: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <path d="M14 2v6h6"/>
                <path d="M8 13h8"/>
                <path d="M8 17h6"/>
            </svg>
        `,

        image: `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="m21 15-5-5L5 21"/>
            </svg>
        `
    };

    /* ---------------------------------------------------------
       HELPERS
    --------------------------------------------------------- */

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function escapeAttribute(value) {
        return escapeHtml(value);
    }

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (const cookie of cookies) {
            const trimmed = cookie.trim();

            if (trimmed.startsWith(name + "=")) {
                return decodeURIComponent(trimmed.substring(name.length + 1));
            }
        }

        return "";
    }

    function getInitials(name) {
        const clean = String(name || "").trim();

        if (!clean) return "U";

        const parts = clean.split(/\s+/);

        if (parts.length >= 2) {
            return (
                parts[0].charAt(0) +
                parts[parts.length - 1].charAt(0)
            ).toUpperCase();
        }

        return clean.substring(0, 2).toUpperCase();
    }

    function formatDate(value) {
        if (!value) return "";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return escapeHtml(value);
        }

        return date.toLocaleDateString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    }

    function getFileExtension(filename) {
        const name = String(filename || "");

        if (!name.includes(".")) return "FILE";

        return name
            .split(".")
            .pop()
            .toUpperCase()
            .substring(0, 5);
    }

    function isImageAttachment(file) {
        const name = String(file?.original_name || file?.file || "").toLowerCase();

        return (
            /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(name)
        );
    }

    function getAttachmentUrl(attachment) {
        return (
            attachment?.file_url ||
            attachment?.url ||
            attachment?.file ||
            ""
        );
    }

    /* ---------------------------------------------------------
       TABS / FILTERS
    --------------------------------------------------------- */

    window.setTab = function (button) {
        document
            .querySelectorAll(".news-tab")
            .forEach(tab => tab.classList.remove("active"));

        if (button) {
            button.classList.add("active");
        }
    };

    window.setScope = function (button) {
        document
            .querySelectorAll(".scope-button")
            .forEach(scope => scope.classList.remove("active"));

        if (button) {
            button.classList.add("active");
        }
    };

    window.toggleFilters = function () {
        const filters = document.getElementById("newsFilters");

        if (!filters) return;

        filters.classList.toggle("is-open");
    };

    /* ---------------------------------------------------------
       IMAGE VIEWER
    --------------------------------------------------------- */

    function createImageViewer() {
        if (document.getElementById("newsImageViewer")) {
            return;
        }

        const viewer = document.createElement("div");

        viewer.id = "newsImageViewer";
        viewer.className = "news-image-viewer";
        viewer.hidden = true;

        viewer.innerHTML = `
            <div class="news-image-viewer-backdrop" data-close-image-viewer></div>

            <div class="news-image-viewer-panel" role="dialog" aria-modal="true">
                <button
                    type="button"
                    class="news-image-viewer-close"
                    aria-label="Close image"
                    data-close-image-viewer
                >
                    ×
                </button>

                <img
                    id="newsViewerImage"
                    class="news-viewer-image"
                    src=""
                    alt=""
                >

                <div id="newsViewerName" class="news-viewer-name"></div>
            </div>
        `;

        document.body.appendChild(viewer);

        viewer.addEventListener("click", event => {
            if (event.target.closest("[data-close-image-viewer]")) {
                closeImageViewer();
            }
        });
    }

    function showImage(url, name = "") {
        if (!url) return;

        createImageViewer();

        const viewer = document.getElementById("newsImageViewer");
        const image = document.getElementById("newsViewerImage");
        const label = document.getElementById("newsViewerName");

        image.src = url;
        image.alt = name || "News image";
        label.textContent = name || "";

        viewer.hidden = false;
        document.body.classList.add("news-viewer-open");
    }

    function closeImageViewer() {
        const viewer = document.getElementById("newsImageViewer");

        if (!viewer) return;

        viewer.hidden = true;
        document.body.classList.remove("news-viewer-open");

        const image = document.getElementById("newsViewerImage");

        if (image) {
            image.src = "";
        }
    }

    /* ---------------------------------------------------------
       PUBLIC PROFILE VIEWER
    --------------------------------------------------------- */

    function createPublicProfileViewer() {
        if (document.getElementById("newsPublicProfileViewer")) {
            return;
        }

        const viewer = document.createElement("div");

        viewer.id = "newsPublicProfileViewer";
        viewer.className = "news-public-profile-viewer";
        viewer.hidden = true;

        viewer.innerHTML = `
            <div class="news-public-profile-backdrop" data-close-public-profile></div>

            <section
                class="news-public-profile-panel"
                role="dialog"
                aria-modal="true"
                aria-labelledby="newsPublicProfileName"
            >
                <button
                    type="button"
                    class="news-public-profile-close"
                    aria-label="Close profile"
                    data-close-public-profile
                >
                    ×
                </button>

                <div class="news-public-profile-avatar" id="newsPublicProfileAvatar"></div>

                <h2 id="newsPublicProfileName"></h2>
            </section>
        `;

        document.body.appendChild(viewer);

        viewer.addEventListener("click", event => {
            if (event.target.closest("[data-close-public-profile]")) {
                closePublicProfile();
            }
        });
    }

    function showPublicProfile(name, avatarUrl) {
        createPublicProfileViewer();

        const viewer = document.getElementById("newsPublicProfileViewer");
        const avatar = document.getElementById("newsPublicProfileAvatar");
        const nameElement = document.getElementById("newsPublicProfileName");

        const safeName = name || "UNIMAP User";

        if (avatarUrl) {
            avatar.innerHTML = `
                <img
                    src="${escapeAttribute(avatarUrl)}"
                    alt="${escapeAttribute(safeName)}"
                    onerror="this.style.display='none'; this.parentElement.textContent='${escapeAttribute(getInitials(safeName))}'"
                >
            `;
        } else {
            avatar.textContent = getInitials(safeName);
        }

        nameElement.textContent = safeName;

        viewer.hidden = false;
        document.body.classList.add("news-profile-open");
    }

    function closePublicProfile() {
        const viewer = document.getElementById("newsPublicProfileViewer");

        if (!viewer) return;

        viewer.hidden = true;
        document.body.classList.remove("news-profile-open");
    }

    /* ---------------------------------------------------------
       ATTACHMENT RENDERING
    --------------------------------------------------------- */

    function renderSingleImage(attachment, index) {
        const url = getAttachmentUrl(attachment);

        if (!url) return "";

        const name =
            attachment?.original_name ||
            `News image ${index + 1}`;

        return `
            <div class="news-attachment-image">
                <button
                    type="button"
                    class="news-image-button"
                    data-image-url="${escapeAttribute(url)}"
                    data-image-name="${escapeAttribute(name)}"
                    aria-label="Open image"
                >
                    <img
                        src="${escapeAttribute(url)}"
                        alt="${escapeAttribute(name)}"
                        loading="lazy"
                        decoding="async"
                        onerror="this.closest('.news-attachment-image')?.remove()"
                    >
                </button>
            </div>
        `;
    }

    function renderDocument(attachment) {
        const url = getAttachmentUrl(attachment);

        if (!url) return "";

        const name =
            attachment?.original_name ||
            "Document";

        const extension = getFileExtension(name);

        return `
            <a
                class="news-attachment-file"
                href="${escapeAttribute(url)}"
                target="_blank"
                rel="noopener noreferrer"
                title="${escapeAttribute(name)}"
            >
                <span class="news-attachment-file-icon">
                    ${escapeHtml(extension)}
                </span>

                <span class="news-attachment-file-copy">
                    <span class="news-attachment-file-name">
                        ${escapeHtml(name)}
                    </span>

                    <span class="news-attachment-file-action">
                        Open document
                    </span>
                </span>

                <span class="news-attachment-file-arrow" aria-hidden="true">
                    ↗
                </span>
            </a>
        `;
    }

    function renderAttachments(attachments) {
        if (!Array.isArray(attachments) || attachments.length === 0) {
            return "";
        }

        const images = attachments.filter(isImageAttachment);
        const documents = attachments.filter(file => !isImageAttachment(file));

        let html = "";

        if (images.length) {
            const visibleImages = images.slice(0, 4);
            const extraCount = images.length - visibleImages.length;

            html += `
                <div class="news-image-gallery gallery-count-${Math.min(images.length, 4)}">
            `;

            visibleImages.forEach((attachment, index) => {
                const url = getAttachmentUrl(attachment);
                const name =
                    attachment?.original_name ||
                    `News image ${index + 1}`;

                if (!url) return;

                html += `
                    <div class="news-gallery-item">
                        <button
                            type="button"
                            class="news-gallery-image-button"
                            data-image-url="${escapeAttribute(url)}"
                            data-image-name="${escapeAttribute(name)}"
                            aria-label="Open image"
                        >
                            <img
                                src="${escapeAttribute(url)}"
                                alt="${escapeAttribute(name)}"
                                loading="lazy"
                                decoding="async"
                                onerror="this.closest('.news-gallery-item')?.remove()"
                            >
                `;

                if (
                    extraCount > 0 &&
                    index === visibleImages.length - 1
                ) {
                    html += `
                            <span class="news-gallery-more">
                                +${extraCount}
                            </span>
                    `;
                }

                html += `
                        </button>
                    </div>
                `;
            });

            html += `</div>`;
        }

        if (documents.length) {
            html += `
                <div class="news-document-list">
                    ${documents.map(renderDocument).join("")}
                </div>
            `;
        }

        return `
            <div class="news-attachments">
                ${html}
            </div>
        `;
    }

    /* ---------------------------------------------------------
       AUTHOR
    --------------------------------------------------------- */

    function renderAuthor(post) {
        const name =
            post.author_name ||
            post.author_full_name ||
            "UNIMAP User";

        const avatarUrl =
            post.author_avatar_url ||
            post.author_profile_picture ||
            post.profile_picture_url ||
            "";

        return `
            <button
                type="button"
                class="news-author"
                data-profile-name="${escapeAttribute(name)}"
                data-profile-avatar="${escapeAttribute(avatarUrl)}"
            >
                <span class="news-author-avatar">
                    ${
                        avatarUrl
                            ? `
                                <img
                                    src="${escapeAttribute(avatarUrl)}"
                                    alt="${escapeAttribute(name)}"
                                    loading="lazy"
                                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                >
                                <span class="news-author-initials" style="display:none;">
                                    ${escapeHtml(getInitials(name))}
                                </span>
                              `
                            : `
                                <span class="news-author-initials">
                                    ${escapeHtml(getInitials(name))}
                                </span>
                              `
                    }
                </span>

                <span class="news-author-copy">
                    <span class="news-author-name">
                        ${escapeHtml(name)}
                    </span>

                    <span class="news-author-action">
                        View profile
                    </span>
                </span>
            </button>
        `;
    }

    /* ---------------------------------------------------------
       POST RENDERING
    --------------------------------------------------------- */

    function renderPost(post) {
        const postType =
            post.post_type === "campus_news"
                ? "Campus News"
                : "Study Group";

        const typeClass =
            post.post_type === "campus_news"
                ? "campus-news"
                : "study-group";

        const title = post.title || "Untitled post";
        const body = post.body || "";

        return `
            <article class="news-post">
                <div class="news-post-top">
                    <div class="news-post-author-wrap">
                        ${renderAuthor(post)}
                    </div>

                    <time class="news-date">
                        ${formatDate(post.created_at)}
                    </time>
                </div>

                <div class="news-post-type ${typeClass}">
                    ${
                        post.post_type === "campus_news"
                            ? icons.campusNews
                            : icons.studyGroup
                    }
                    <span>${escapeHtml(postType)}</span>
                </div>

                <h3 class="news-post-title">
                    ${escapeHtml(title)}
                </h3>

                ${
                    body
                        ? `
                            <p class="news-post-body">
                                ${escapeHtml(body).replace(/\n/g, "<br>")}
                            </p>
                          `
                        : ""
                }

                ${renderAttachments(post.attachments)}
            </article>
        `;
    }

    /* ---------------------------------------------------------
       EMPTY / ERROR / LOADING
    --------------------------------------------------------- */

    function renderLoading() {
        newsContainer.innerHTML = `
            <div class="news-loading">
                <div class="news-loading-spinner"></div>
                <span>Loading updates...</span>
            </div>
        `;
    }

    function renderEmpty() {
        newsContainer.innerHTML = `
            <div class="news-empty">
                <div class="news-empty-icon">
                    ${icons.campusNews}
                </div>

                <h3>No updates yet</h3>

                <p>
                    There are no posts matching this filter right now.
                </p>
            </div>
        `;
    }

    function renderError(message) {
        newsContainer.innerHTML = `
            <div class="news-error">
                <strong>Unable to load News</strong>
                <span>${escapeHtml(message || "Please try again.")}</span>

                <button type="button" onclick="load()">
                    Try again
                </button>
            </div>
        `;
    }

    /* ---------------------------------------------------------
       LOAD FEED
    --------------------------------------------------------- */

    window.load = async function (
        type = currentTab,
        scope = currentScope
    ) {
        currentTab = type || "all";
        currentScope = scope || "all";

        if (!newsContainer) return;

        renderLoading();

        const params = new URLSearchParams();

        if (currentTab && currentTab !== "all") {
            params.set("type", currentTab);
        }

        if (currentScope && currentScope !== "all") {
            params.set("scope", currentScope);
        }

        const query = params.toString();

        const url = `/api/academic/news/${query ? `?${query}` : ""}`;

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    Accept: "application/json"
                },
                credentials: "same-origin"
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}.`);
            }

            const data = await response.json();

            const posts = Array.isArray(data)
                ? data
                : Array.isArray(data.results)
                    ? data.results
                    : Array.isArray(data.posts)
                        ? data.posts
                        : [];

            if (!posts.length) {
                renderEmpty();
                return;
            }

            newsContainer.innerHTML = posts
                .map(renderPost)
                .join("");
        } catch (error) {
            console.error("UNIMAP News:", error);

            renderError(
                "We couldn't retrieve the latest updates."
            );
        }
    };

    /* ---------------------------------------------------------
       IMAGE / PROFILE CLICK EVENTS
    --------------------------------------------------------- */

    document.addEventListener("click", event => {
        const imageButton = event.target.closest(
            ".news-image-button, .news-gallery-image-button"
        );

        if (imageButton) {
            event.preventDefault();

            showImage(
                imageButton.dataset.imageUrl,
                imageButton.dataset.imageName
            );

            return;
        }

        const author = event.target.closest(".news-author");

        if (author) {
            event.preventDefault();

            showPublicProfile(
                author.dataset.profileName,
                author.dataset.profileAvatar
            );
        }
    });

    /* ---------------------------------------------------------
       COMPOSER
    --------------------------------------------------------- */

    function openNewsComposer() {
        if (!composer) return;

        composer.hidden = false;
        document.body.classList.add("news-composer-open");

        const title = document.getElementById("newsTitle");

        if (title) {
            setTimeout(() => title.focus(), 100);
        }
    }

    function closeNewsComposer() {
        if (!composer) return;

        composer.hidden = true;
        document.body.classList.remove("news-composer-open");
    }

    if (openComposer) {
        openComposer.addEventListener("click", openNewsComposer);
    }

    if (closeComposer) {
        closeComposer.addEventListener("click", closeNewsComposer);
    }

    document.addEventListener("click", event => {
        if (event.target.closest("[data-close-news-modal]")) {
            closeNewsComposer();
        }
    });

    /* ---------------------------------------------------------
       ATTACHMENT SELECTION
    --------------------------------------------------------- */

    function renderSelectedFiles() {
        if (!attachmentList) return;

        if (!selectedFiles.length) {
            attachmentList.innerHTML = "";
            return;
        }

        attachmentList.innerHTML = selectedFiles
            .map((file, index) => {
                const isImage = file.type.startsWith("image/");

                return `
                    <div class="selected-attachment">
                        <span class="selected-attachment-icon">
                            ${
                                isImage
                                    ? icons.image
                                    : icons.file
                            }
                        </span>

                        <span class="selected-attachment-name">
                            ${escapeHtml(file.name)}
                        </span>

                        <button
                            type="button"
                            class="selected-attachment-remove"
                            data-remove-file="${index}"
                            aria-label="Remove ${escapeAttribute(file.name)}"
                        >
                            ×
                        </button>
                    </div>
                `;
            })
            .join("");
    }

    if (attachmentInput) {
        attachmentInput.addEventListener("change", () => {
            const newFiles = Array.from(
                attachmentInput.files || []
            );

            selectedFiles = [
                ...selectedFiles,
                ...newFiles
            ];

            renderSelectedFiles();

            /*
             * Reset the input so selecting the same file again
             * still triggers the change event.
             */
            attachmentInput.value = "";
        });
    }

    document.addEventListener("click", event => {
        const removeButton = event.target.closest(
            "[data-remove-file]"
        );

        if (!removeButton) return;

        const index = Number(
            removeButton.dataset.removeFile
        );

        selectedFiles.splice(index, 1);

        renderSelectedFiles();
    });

    /* ---------------------------------------------------------
       CREATE POST
    --------------------------------------------------------- */

    if (newsForm) {
        newsForm.addEventListener("submit", async event => {
            event.preventDefault();

            const publishButton =
                newsForm.querySelector(".publish-news-button");

            if (!publishButton) return;

            const originalButton = publishButton.innerHTML;

            publishButton.disabled = true;
            publishButton.innerHTML = `
                <span>Publishing...</span>
            `;

            try {
                const formData = new FormData(newsForm);

                /*
                 * The file input is manually managed because we allow
                 * users to remove selected files before publishing.
                 */
                formData.delete("attachments");

                selectedFiles.forEach(file => {
                    formData.append("attachments", file);
                });

                const csrfToken = getCookie("csrftoken");

                const response = await fetch(
                    "/api/academic/news/",
                    {
                        method: "POST",
                        body: formData,
                        credentials: "same-origin",
                        headers: {
                            Accept: "application/json",
                            ...(csrfToken
                                ? {
                                    "X-CSRFToken": csrfToken
                                }
                                : {})
                        }
                    }
                );

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    let message =
                        data.detail ||
                        "The post could not be published.";

                    if (typeof data === "object") {
                        const errors = [];

                        Object.entries(data).forEach(
                            ([field, value]) => {
                                if (Array.isArray(value)) {
                                    errors.push(
                                        `${field}: ${value.join(", ")}`
                                    );
                                } else if (
                                    typeof value === "string"
                                ) {
                                    errors.push(
                                        `${field}: ${value}`
                                    );
                                }
                            }
                        );

                        if (errors.length) {
                            message = errors.join(" ");
                        }
                    }

                    throw new Error(message);
                }

                newsForm.reset();
                selectedFiles = [];
                renderSelectedFiles();

                closeNewsComposer();

                await load(
                    currentTab,
                    currentScope
                );
            } catch (error) {
                console.error(
                    "UNIMAP News publish:",
                    error
                );

                alert(
                    error.message ||
                    "The post could not be published."
                );
            } finally {
                publishButton.disabled = false;
                publishButton.innerHTML = originalButton;
            }
        });
    }

   

    document.addEventListener("keydown", event => {
        if (event.key !== "Escape") return;

        closeImageViewer();
        closePublicProfile();
        closeNewsComposer();
    });


    createImageViewer();
    createPublicProfileViewer();

    load("all", "all");
});
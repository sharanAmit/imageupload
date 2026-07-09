// Trip Memories Platform - Global Photos Timeline Module (Google Photos Style)
import API from '../api.js';

export async function renderPhotosTimeline(container) {
    // Show skeletal loader
    container.innerHTML = `
        <div class="animate-fade-in">
            <h2 class="fw-bold mb-4">Photos</h2>
            <div class="timeline-group">
                <div class="card-premium skeleton mb-4" style="height: 40px; width: 250px;"></div>
                <div class="row g-3">
                    <div class="col-md-3"><div class="card-premium skeleton" style="height: 200px;"></div></div>
                    <div class="col-md-3"><div class="card-premium skeleton" style="height: 280px;"></div></div>
                    <div class="col-md-3"><div class="card-premium skeleton" style="height: 180px;"></div></div>
                    <div class="col-md-3"><div class="card-premium skeleton" style="height: 240px;"></div></div>
                </div>
            </div>
        </div>
    `;

    try {
        const photos = await API.getAllPhotos();
        const currentUser = JSON.parse(localStorage.getItem("user") || "{}");

        if (photos.length === 0) {
            container.innerHTML = `
                <div class="animate-fade-in text-center py-5">
                    <div class="text-secondary fs-1 mb-3"><i class="bi bi-images"></i></div>
                    <h3 class="fw-bold">Welcome to your Memories Vault</h3>
                    <p class="text-secondary max-w-400 mx-auto mb-4">You haven't uploaded any photos or videos yet. Start by creating a Trip and uploading your travel files!</p>
                    <a href="#/trips" class="btn btn-premium">
                        <i class="bi bi-compass"></i> Explore Trips
                    </a>
                </div>
            `;
            return;
        }

        // Group photos by date
        const dateGroups = {};
        photos.forEach(photo => {
            const dateObj = new Date(photo.created_at);
            const dateStr = dateObj.toLocaleDateString(undefined, {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            if (!dateGroups[dateStr]) {
                dateGroups[dateStr] = [];
            }
            dateGroups[dateStr].push(photo);
        });

        // Render groups
        let timelineHTML = `
            <div class="animate-fade-in">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-4">
                    <h2 class="fw-bold mb-0">Photos</h2>
                    <span class="badge bg-light text-secondary border rounded-pill fs-8 px-3 py-2">${photos.length} items</span>
                </div>
        `;

        Object.keys(dateGroups).forEach(date => {
            const items = dateGroups[date];
            timelineHTML += `
                <div class="timeline-group">
                    <div class="timeline-date-header">
                        <i class="bi bi-calendar3"></i> ${date}
                    </div>
                    <div class="gallery-grid">
                        ${items.map(item => {
                            const privateUrl = API.getMediaUrl(item.uuid);
                            if (item.media_type === "photo") {
                                return `
                                    <div class="gallery-item animate-fade-in" data-uuid="${item.uuid}" data-trip="${(item.trip_name || '').toLowerCase()}" data-date="${date.toLowerCase()}">
                                        <img src="${privateUrl}" loading="lazy" alt="Memory">
                                        <div class="position-absolute top-0 start-0 m-2 bg-dark bg-opacity-50 text-white rounded-pill px-2.5 py-1 d-flex align-items-center gap-1 shadow-sm" style="font-size: 0.65rem; backdrop-filter: blur(4px); pointer-events: none; z-index: 2;">
                                            <i class="bi bi-compass-fill" style="color: #4285F4;"></i>
                                            <span>${item.trip_name || 'Trip'}</span>
                                        </div>
                                        <div class="gallery-info-overlay">
                                            <div class="gallery-overlay-text">
                                                <h4>Photo</h4>
                                                <p>${item.trip_name || 'View details'}</p>
                                            </div>
                                            <i class="bi bi-zoom-in text-white fs-5"></i>
                                        </div>
                                    </div>
                                `;
                            } else {
                                return `
                                    <div class="gallery-item animate-fade-in" data-uuid="${item.uuid}" data-trip="${(item.trip_name || '').toLowerCase()}" data-date="${date.toLowerCase()}">
                                        <video src="${privateUrl}" muted playsinline preload="metadata"></video>
                                        <div class="position-absolute top-0 start-0 m-2 bg-dark bg-opacity-50 text-white rounded-pill px-2.5 py-1 d-flex align-items-center gap-1 shadow-sm" style="font-size: 0.65rem; backdrop-filter: blur(4px); pointer-events: none; z-index: 2;">
                                            <i class="bi bi-play-circle-fill" style="color: #EA4335;"></i>
                                            <span>${item.trip_name || 'Trip'}</span>
                                        </div>
                                        <div class="gallery-info-overlay">
                                            <div class="gallery-overlay-text">
                                                <h4>Video</h4>
                                                <p>${item.trip_name || 'Play memory'}</p>
                                            </div>
                                            <i class="bi bi-play-circle-fill text-white fs-5"></i>
                                        </div>
                                    </div>
                                `;
                            }
                        }).join("")}
                    </div>
                </div>
            `;
        });

        timelineHTML += `</div>`;
        container.innerHTML = timelineHTML;

        // Lightbox modal setup
        const modalEl = document.getElementById("lightbox-modal");
        const mediaMount = document.getElementById("lightbox-media-mount");
        const titleEl = document.getElementById("lightbox-title");
        const tripNameEl = document.getElementById("lightbox-trip-name");
        const uploaderEl = document.getElementById("lightbox-uploader");
        const dateEl = document.getElementById("lightbox-date");
        const sizeEl = document.getElementById("lightbox-size");
        const mimeEl = document.getElementById("lightbox-mime");
        const downloadBtn = document.getElementById("lightbox-download-btn");
        const deleteBtn = document.getElementById("lightbox-delete-btn");

        document.querySelectorAll(".gallery-item").forEach(item => {
            item.addEventListener("click", () => {
                const uuid = item.getAttribute("data-uuid");
                const mediaItem = photos.find(g => g.uuid === uuid);
                if (!mediaItem) return;

                const privateUrl = API.getMediaUrl(mediaItem.uuid);
                
                if (mediaItem.media_type === "photo") {
                    mediaMount.innerHTML = `<img src="${privateUrl}" alt="Preview">`;
                } else {
                    mediaMount.innerHTML = `<video src="${privateUrl}" controls autoplay></video>`;
                }

                const sizeMB = (mediaItem.file_size / (1024 * 1024)).toFixed(2);
                const date = new Date(mediaItem.created_at).toLocaleString();
                
                titleEl.textContent = mediaItem.media_type === "photo" ? "Photo Memory" : "Video Memory";
                tripNameEl.textContent = mediaItem.trip_name || "-";
                uploaderEl.textContent = `User #${mediaItem.uploaded_by}`;
                dateEl.textContent = date;
                sizeEl.textContent = `${sizeMB} MB`;
                mimeEl.textContent = mediaItem.mime_type;

                downloadBtn.href = API.getMediaUrl(mediaItem.uuid, true);

                // Setup delete handler (only uploader can delete globally from here, or owner on their trip)
                const isUploader = (mediaItem.uploaded_by === currentUser.id);
                if (isUploader) {
                    deleteBtn.style.display = "block";
                    deleteBtn.onclick = async () => {
                        if (confirm("Delete this memory forever? This action cannot be undone.")) {
                            try {
                                await API.deleteMedia(mediaItem.uuid);
                                window.showToast("Memory deleted.", "success");
                                modalEl.style.display = "none";
                                mediaMount.innerHTML = "";
                                // Refresh timeline
                                renderPhotosTimeline(container);
                            } catch (err) {
                                window.showToast(err.message, "danger");
                            }
                        }
                    };
                } else {
                    deleteBtn.style.display = "none";
                }

                modalEl.style.display = "flex";
            });
        });

        // Close lightbox hooks (redundancy safeguard)
        document.getElementById("lightbox-close").onclick = () => {
            modalEl.style.display = "none";
            mediaMount.innerHTML = "";
        };

        modalEl.onclick = (e) => {
            if (e.target === modalEl) {
                modalEl.style.display = "none";
                mediaMount.innerHTML = "";
            }
        };

    } catch (err) {
        window.showToast("Failed to load timeline.", "danger");
        console.error("Photos timeline error:", err);
    }
}

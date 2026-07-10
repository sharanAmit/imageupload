// Trip Memories Platform - Trips & Trip Details Page Module
import API from '../api.js';

export async function renderTrips(container) {
    container.innerHTML = `
        <div class="animate-fade-in">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-5">
                <div>
                    <h1 class="fw-bold mb-1">My Trips</h1>
                    <p class="text-secondary mb-0">Manage and browse your shared travel journals.</p>
                </div>
                <div class="d-flex gap-3">
                    <button class="btn btn-premium-secondary btn-premium" data-bs-toggle="modal" data-bs-target="#join-trip-modal">
                        <i class="bi bi-person-plus"></i> Join Trip
                    </button>
                    <button class="btn btn-premium" data-bs-toggle="modal" data-bs-target="#create-trip-modal">
                        <i class="bi bi-plus-lg"></i> Create Trip
                    </button>
                </div>
            </div>
            
            <div id="trips-list" class="row g-4">
                <!-- Skeletal load -->
                <div class="col-md-4"><div class="card-premium skeleton" style="height: 250px;"></div></div>
                <div class="col-md-4"><div class="card-premium skeleton" style="height: 250px;"></div></div>
                <div class="col-md-4"><div class="card-premium skeleton" style="height: 250px;"></div></div>
            </div>
        </div>

        <!-- Create Trip Modal -->
        <div class="modal fade" id="create-trip-modal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow-lg">
                    <div class="modal-header border-0 pb-0">
                        <h5 class="modal-title fw-bold">Create a New Trip</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form id="create-trip-form">
                        <div class="modal-body py-4">
                            <div class="form-group">
                                <label class="form-label">Trip Name</label>
                                <input type="text" id="trip-name" class="form-control" required placeholder="Summer in Greece 2026">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Description</label>
                                <textarea id="trip-desc" class="form-control" rows="3" placeholder="Describe the adventure, places visited, dates..."></textarea>
                            </div>
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-premium-secondary btn-premium" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-premium" id="submit-create-btn">Create</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Join Trip Modal -->
        <div class="modal fade" id="join-trip-modal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content rounded-4 border-0 shadow-lg">
                    <div class="modal-header border-0 pb-0">
                        <h5 class="modal-title fw-bold">Join a Trip</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form id="join-trip-form">
                        <div class="modal-body py-4">
                            <p class="text-secondary fs-7">Enter the Trip UUID shared by the trip owner to join.</p>
                            <div class="form-group">
                                <label class="form-label">Trip UUID</label>
                                <input type="text" id="trip-uuid-input" class="form-control" required placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000">
                            </div>
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-premium-secondary btn-premium" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-premium" id="submit-join-btn">Join</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;

    // Fetch and render trips
    const loadTrips = async () => {
        const listContainer = document.getElementById("trips-list");
        try {
            const trips = await API.getTrips();
            if (trips.length === 0) {
                listContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <div class="text-secondary fs-1 mb-3"><i class="bi bi-compass"></i></div>
                        <h3 class="fw-bold">No trips yet</h3>
                        <p class="text-secondary">Create a new trip or ask for an invitation to join one.</p>
                        <button class="btn btn-premium mt-3" data-bs-toggle="modal" data-bs-target="#create-trip-modal">
                            Create First Trip
                        </button>
                    </div>
                `;
                return;
            }

            listContainer.innerHTML = trips.map(trip => {
                const date = new Date(trip.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'long'
                });
                
                // Let's use a beautiful placeholder or dynamic colored gradient if no cover image
                const coverStyle = trip.cover_image 
                    ? `background-image: url('${trip.cover_image}');`
                    : `background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);`;

                return `
                    <div class="col-md-6 col-lg-4 animate-fade-in">
                        <div class="card-premium h-100 p-0 overflow-hidden" onclick="window.location.hash='#/trip/${trip.uuid}'" style="cursor: pointer;">
                            <div style="height: 160px; ${coverStyle} background-size: cover; background-position: center;"></div>
                            <div class="p-4">
                                <h4 class="fw-bold text-truncate mb-1">${trip.trip_name}</h4>
                                <p class="fs-8 text-secondary mb-3">${date}</p>
                                <p class="fs-7 text-secondary text-truncate-2 mb-0">${trip.description || 'No description added.'}</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        } catch (err) {
            window.showToast("Failed to fetch trips.", "danger");
            listContainer.innerHTML = `<div class="col-12 text-center text-danger py-5">Error: ${err.message}</div>`;
        }
    };

    // Modal listeners
    const createForm = document.getElementById("create-trip-form");
    createForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("trip-name").value.trim();
        const desc = document.getElementById("trip-desc").value.trim();
        const submitBtn = document.getElementById("submit-create-btn");

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Creating...`;

        try {
            await API.createTrip(name, desc);
            window.showToast("Trip created successfully!", "success");
            
            // Clean up and close modal
            createForm.reset();
            const modalEl = document.getElementById("create-trip-modal");
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();
            
            // Refresh
            loadTrips();
        } catch (err) {
            window.showToast(err.message, "danger");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Create";
        }
    });

    const joinForm = document.getElementById("join-trip-form");
    joinForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const uuid = document.getElementById("trip-uuid-input").value.trim();
        const submitBtn = document.getElementById("submit-join-btn");

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Joining...`;

        try {
            await API.joinTrip(uuid);
            window.showToast("Joined trip successfully!", "success");
            
            // Clean up and close
            joinForm.reset();
            const modalEl = document.getElementById("join-trip-modal");
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();
            
            // Refresh
            loadTrips();
        } catch (err) {
            window.showToast(err.message, "danger");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Join";
        }
    });

    // Run first load
    loadTrips();
}

export async function renderTripDetails(container, params) {
    const tripUuid = params.tripUuid;
    
    // Set layout structure with skeletons
    container.innerHTML = `
        <div class="animate-fade-in">
            <div class="mb-4">
                <a href="#/trips" class="text-decoration-none text-dark fw-semibold fs-7">
                    <i class="bi bi-arrow-left"></i> All Trips
                </a>
            </div>
            
            <!-- Detail Header Skeleton -->
            <div class="card-premium p-0 overflow-hidden mb-5 skeleton" style="height: 350px;"></div>
            
            <div class="row g-5">
                <div class="col-lg-8">
                    <h3 class="fw-bold mb-4">Gallery</h3>
                    <div class="card-premium skeleton" style="height: 300px;"></div>
                </div>
                <div class="col-lg-4">
                    <h3 class="fw-bold mb-4">Members</h3>
                    <div class="card-premium skeleton" style="height: 180px;"></div>
                </div>
            </div>
        </div>
    `;

    try {
        const token = localStorage.getItem("access_token");
        const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
        const trip = await API.getTripDetails(tripUuid);
        const gallery = await API.getGallery(tripUuid);
        const activities = await API.getTripActivities(tripUuid);
        
        // Find current user's membership details
        const myMembership = trip.members.find(m => m.user_id === currentUser.id);
        const isOwner = myMembership && myMembership.role === "owner";
        const isCoOwner = myMembership && myMembership.role === "co-owner";
        const canInvite = isOwner || isCoOwner;

        // Setup cover block styling
        const coverStyle = trip.cover_image 
            ? `background-image: url('${trip.cover_image}');`
            : `background: linear-gradient(135deg, #0F172A 0%, #334155 100%);`;

        container.innerHTML = `
            <div class="animate-fade-in">
                <div class="mb-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
                    <a href="#/trips" class="text-decoration-none text-secondary fw-medium fs-7">
                        <i class="bi bi-arrow-left"></i> Back to Trips
                    </a>
                    
                    ${isOwner ? `
                        <div class="d-flex gap-2">
                            <button class="btn btn-premium-secondary btn-premium py-2 px-3" data-bs-toggle="modal" data-bs-target="#edit-trip-modal">
                                <i class="bi bi-pencil"></i> Edit
                            </button>
                            <button class="btn btn-danger-premium btn-premium py-2 px-3" id="delete-trip-btn">
                                <i class="bi bi-trash"></i> Delete Trip
                            </button>
                        </div>
                    ` : ""}
                </div>
                
                <!-- Large Elegant Trip Header -->
                <div class="card-premium p-0 overflow-hidden mb-5 border-0 position-relative" style="height: 300px; ${coverStyle} background-size: cover; background-position: center; border-radius: var(--radius-lg);">
                    <div class="position-absolute bottom-0 start-0 right-0 p-5 text-white w-100" style="background: linear-gradient(to top, rgba(15,23,42,0.9) 0%, rgba(15,23,42,0) 100%);">
                        <h1 class="fw-bold text-white mb-2">${trip.trip_name}</h1>
                        <p class="text-light mb-0 fs-6 max-w-600">${trip.description || 'No description provided.'}</p>
                    </div>
                </div>

                <div class="row g-5">
                    <!-- Left Gallery and Upload Section -->
                    <div class="col-lg-8">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h3 class="fw-bold mb-0">Gallery</h3>
                            
                            <label class="btn btn-premium btn-premium-secondary mb-0 cursor-pointer">
                                <i class="bi bi-cloud-upload"></i> Upload Memory
                                <input type="file" id="media-upload-input" accept="image/*,video/*" multiple class="d-none">
                            </label>
                        </div>

                        <!-- Gallery View -->
                        ${gallery.length === 0 ? `
                            <div class="card-premium text-center py-5 bg-white">
                                <i class="bi bi-images fs-1 text-secondary"></i>
                                <h5 class="fw-bold mt-3">Trip gallery is empty</h5>
                                <p class="text-secondary fs-7">Be the first to upload a photo or video memory!</p>
                            </div>
                        ` : `
                            <div class="gallery-grid" id="masonry-gallery">
                                ${gallery.map(item => {
                                    // Construct the authenticated, private image URL
                                    const privateUrl = API.getMediaUrl(item.uuid);
                                    
                                    if (item.media_type === "photo") {
                                        return `
                                            <div class="gallery-item animate-fade-in" data-uuid="${item.uuid}">
                                                <img src="${privateUrl}" loading="lazy" alt="Trip memory">
                                                <div class="gallery-info-overlay">
                                                    <div class="gallery-overlay-text">
                                                        <h4>${new Date(item.created_at).toLocaleDateString()}</h4>
                                                        <p>View Details</p>
                                                    </div>
                                                    <i class="bi bi-zoom-in text-white fs-5"></i>
                                                </div>
                                            </div>
                                        `;
                                    } else {
                                        return `
                                            <div class="gallery-item animate-fade-in" data-uuid="${item.uuid}">
                                                <video src="${privateUrl}" muted playsinline preload="metadata"></video>
                                                <div class="gallery-info-overlay">
                                                    <div class="gallery-overlay-text">
                                                        <h4>Video Memory</h4>
                                                        <p>Play Memory</p>
                                                    </div>
                                                    <i class="bi bi-play-circle-fill text-white fs-5"></i>
                                                </div>
                                            </div>
                                        `;
                                    }
                                }).join("")}
                            </div>
                        `}
                    </div>

                    <!-- Right Metadata, Member & Activity Section -->
                    <div class="col-lg-4">
                        <!-- Members Card -->
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h3 class="fw-bold mb-0">Members</h3>
                            ${canInvite ? `
                                <button class="btn btn-premium btn-premium-secondary py-1 px-2 fs-8" data-bs-toggle="modal" data-bs-target="#invite-member-modal">
                                    <i class="bi bi-plus-lg"></i> Invite
                                </button>
                            ` : ""}
                        </div>
                        
                        <div class="card-premium mb-5 p-4 bg-white">
                            <div class="d-flex flex-column gap-3">
                                ${trip.members.map(member => {
                                    const mUser = member.user || {};
                                    const isPending = member.status === "pending";
                                    const isDeclined = member.status === "declined";
                                    return `
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div class="d-flex align-items-center gap-2">
                                                <div class="rounded-circle bg-secondary d-flex align-items-center justify-content-center fw-bold text-dark fs-7" style="width: 32px; height: 32px;">
                                                    ${mUser.name ? mUser.name.charAt(0).toUpperCase() : '?'}
                                                </div>
                                                <div>
                                                    <div class="fw-semibold fs-7">
                                                        ${mUser.name || 'Member'}
                                                        ${isPending ? `<span class="badge bg-warning text-dark rounded-pill fs-9 py-1 px-2 ms-1">Pending</span>` : ""}
                                                        ${isDeclined ? `<span class="badge bg-danger rounded-pill fs-9 py-1 px-2 ms-1">Declined</span>` : ""}
                                                    </div>
                                                    <div class="fs-9 text-secondary">${mUser.email}</div>
                                                </div>
                                            </div>
                                            <div class="d-flex align-items-center gap-2">
                                                ${isDeclined ? "" : (isOwner && member.user_id !== trip.created_by ? `
                                                    <select class="member-role-select form-select form-select-sm border bg-light rounded-pill py-0.5 px-2 fw-semibold text-uppercase text-center" style="font-size: 0.7rem; width: 110px; cursor: pointer; height: auto;" data-id="${member.id}">
                                                        <option value="member" ${member.role === 'member' ? 'selected' : ''}>Member</option>
                                                        <option value="co-owner" ${(member.role === 'owner' || member.role === 'co-owner') ? 'selected' : ''}>Co-Owner</option>
                                                    </select>
                                                ` : `
                                                    <span class="badge ${member.user_id === trip.created_by ? 'bg-dark' : 'bg-light text-dark border'} rounded-pill fs-9 py-1 px-2 text-uppercase">
                                                        ${member.user_id === trip.created_by ? 'owner' : (member.role === 'owner' ? 'co-owner' : member.role)}
                                                    </span>
                                                `)}
                                                ${isOwner && member.user_id !== currentUser.id ? `
                                                    <button class="btn btn-link text-danger p-0 ms-1 remove-member-btn" data-id="${member.id}" data-name="${mUser.name}">
                                                        <i class="bi bi-trash fs-8"></i>
                                                    </button>
                                                ` : ""}
                                            </div>
                                        </div>
                                    `;
                                }).join("")}
                            </div>
                        </div>

                        <!-- Trip Metadata / ID Copy -->
                        <h3 class="fw-bold mb-4">Sharing Info</h3>
                        <div class="card-premium mb-5 p-4 bg-white">
                            <div class="form-group mb-0">
                                <label class="form-label fs-9 mb-1">Trip UUID (Invite Code)</label>
                                <div class="input-group">
                                    <input type="text" id="trip-uuid-val" class="form-control py-1 px-2 fs-8 bg-light border-0" readonly value="${trip.uuid}">
                                    <button class="btn btn-premium py-1 px-2 border-0" id="copy-uuid-btn" style="background-color: var(--accent);">
                                        <i class="bi bi-copy"></i>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Trip Activities Card -->
                        <h3 class="fw-bold mb-4">Activities</h3>
                        <div class="card-premium p-4 bg-white">
                            ${activities.length === 0 ? `
                                <p class="text-secondary fs-8 mb-0">No activity logged.</p>
                            ` : `
                                <div class="activity-timeline py-2" style="font-size: 0.8rem; border-left-width: 1px;">
                                    ${activities.slice(0, 8).map(act => {
                                        const actor = act.user ? act.user.name : "Member";
                                        let actStr = act.action;
                                        if (act.action === "uploaded_media") actStr = "uploaded memory";
                                        else if (act.action === "deleted_media") actStr = "deleted memory";
                                        else if (act.action === "invited_member") actStr = "invited a member";
                                        else if (act.action === "invited_guest") actStr = "sent an invite";
                                        else if (act.action === "accepted_invite") actStr = "accepted an invite";
                                        else if (act.action === "removed_invite") actStr = "removed a pending invite";
                                        else if (act.action === "joined_trip") actStr = "joined trip";
                                        
                                        return `
                                            <div class="activity-item mb-3" style="padding-left: 0.5rem;">
                                                <div class="text-dark fw-semibold">${actor} <span class="fw-normal text-secondary">${actStr}</span></div>
                                            </div>
                                        `;
                                    }).join("")}
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Edit Trip Modal -->
            <div class="modal fade" id="edit-trip-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content rounded-4 border-0 shadow-lg">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fw-bold">Edit Trip Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <form id="edit-trip-form">
                            <div class="modal-body py-4">
                                <div class="form-group">
                                    <label class="form-label">Trip Name</label>
                                    <input type="text" id="edit-trip-name" class="form-control" required value="${trip.trip_name}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Description</label>
                                    <textarea id="edit-trip-desc" class="form-control" rows="3">${trip.description || ''}</textarea>
                                </div>
                            </div>
                            <div class="modal-footer border-0 pt-0">
                                <button type="button" class="btn btn-premium-secondary btn-premium" data-bs-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-premium" id="submit-edit-btn">Save Changes</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Invite Member Modal -->
            <div class="modal fade" id="invite-member-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content rounded-4 border-0 shadow-lg">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fw-bold">Invite a Member</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <form id="invite-member-form">
                            <div class="modal-body py-4">
                                <div class="form-group position-relative">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" id="invite-email" class="form-control" required placeholder="collaborator@example.com" autocomplete="off">
                                    <div id="search-suggestions" class="list-group position-absolute w-100 shadow rounded-4 border bg-white" style="z-index: 1050; display: none; max-height: 200px; overflow-y: auto; margin-top: 2px;"></div>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Role</label>
                                    <select id="invite-role" class="form-select form-control">
                                        <option value="member">Member (Can upload, view & delete own media)</option>
                                        <option value="co-owner">Co-Owner (Can manage trip, invite others & delete any media)</option>
                                    </select>
                                </div>
                            </div>
                            <div class="modal-footer border-0 pt-0">
                                <button type="button" class="btn btn-premium-secondary btn-premium" data-bs-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-premium" id="submit-invite-btn">Send Invite</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Event hooks
        // Media Upload Hook
        const fileInput = document.getElementById("media-upload-input");
        fileInput.addEventListener("change", async (e) => {
            const files = Array.from(e.target.files);
            if (files.length === 0) return;
            
            window.showToast(`Uploading ${files.length} memory item(s)...`, "info");
            
            let uploadedCount = 0;
            for (const file of files) {
                try {
                    await API.uploadMedia(tripUuid, file);
                    uploadedCount++;
                } catch (err) {
                    window.showToast(`Upload failed for ${file.name}: ${err.message}`, "danger");
                }
            }
            
            if (uploadedCount > 0) {
                window.showToast(`Successfully uploaded ${uploadedCount} memory item(s)!`, "success");
                // Reload page view to display new media
                renderTripDetails(container, params);
            }
        });

        // Copy UUID to Clipboard
        document.getElementById("copy-uuid-btn").addEventListener("click", () => {
            const copyText = document.getElementById("trip-uuid-val");
            copyText.select();
            copyText.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(copyText.value);
            window.showToast("Trip UUID copied to clipboard!", "success");
        });

        // Delete Trip
        if (isOwner) {
            document.getElementById("delete-trip-btn").addEventListener("click", async () => {
                if (confirm("Are you absolutely sure you want to delete this trip? All uploaded photos and videos will be permanently lost!")) {
                    try {
                        await API.deleteTrip(tripUuid);
                        window.showToast("Trip deleted successfully.", "success");
                        window.location.hash = "#/trips";
                    } catch (err) {
                        window.showToast(err.message, "danger");
                    }
                }
            });

            // Edit Trip Form
            const editForm = document.getElementById("edit-trip-form");
            editForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const name = document.getElementById("edit-trip-name").value.trim();
                const desc = document.getElementById("edit-trip-desc").value.trim();
                const submitBtn = document.getElementById("submit-edit-btn");

                submitBtn.disabled = true;
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Saving...`;

                try {
                    await API.updateTrip(tripUuid, name, desc);
                    window.showToast("Trip details updated!", "success");
                    
                    // Close modal and refresh
                    const modalEl = document.getElementById("edit-trip-modal");
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    modalInstance.hide();
                    
                    renderTripDetails(container, params);
                } catch (err) {
                    window.showToast(err.message, "danger");
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = "Save Changes";
                }
            });

            // Invite Member Form
            const inviteForm = document.getElementById("invite-member-form");
            inviteForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const email = document.getElementById("invite-email").value.trim();
                const role = document.getElementById("invite-role").value;
                const submitBtn = document.getElementById("submit-invite-btn");

                submitBtn.disabled = true;
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Inviting...`;

                try {
                    await API.inviteMember(tripUuid, email, role);
                    window.showToast("Invitation sent! They'll join once they accept.", "success");
                    
                    // Close modal and refresh
                    inviteForm.reset();
                    const modalEl = document.getElementById("invite-member-modal");
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    modalInstance.hide();
                    
                    renderTripDetails(container, params);
                } catch (err) {
                    window.showToast(err.message, "danger");
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = "Send Invite";
                }
            });

            // User search autocomplete suggestions logic
            const inviteEmailInput = document.getElementById("invite-email");
            const suggestionsContainer = document.getElementById("search-suggestions");
            let debounceTimeout = null;

            inviteEmailInput.addEventListener("input", () => {
                clearTimeout(debounceTimeout);
                const query = inviteEmailInput.value.trim();
                if (!query) {
                    suggestionsContainer.style.display = "none";
                    suggestionsContainer.innerHTML = "";
                    return;
                }

                debounceTimeout = setTimeout(async () => {
                    try {
                        const matches = await API.searchUsers(query);
                        if (matches.length === 0) {
                            suggestionsContainer.style.display = "none";
                            suggestionsContainer.innerHTML = "";
                            return;
                        }

                        suggestionsContainer.innerHTML = matches.map(user => `
                            <button type="button" class="list-group-item list-group-item-action d-flex align-items-center gap-2 py-2 px-3 border-0" style="font-size: 0.8rem;" data-email="${user.email}">
                                <div class="rounded-circle bg-secondary d-flex align-items-center justify-content-center fw-bold text-dark fs-8" style="width: 24px; height: 24px;">
                                    ${user.name.charAt(0).toUpperCase()}
                                </div>
                                <div class="text-start">
                                    <div class="fw-semibold">${user.name}</div>
                                    <div class="text-secondary fs-9">${user.email}</div>
                                </div>
                            </button>
                        `).join("");

                        suggestionsContainer.style.display = "block";

                        // Hook clicks on suggestions
                        suggestionsContainer.querySelectorAll("button").forEach(btn => {
                            btn.addEventListener("click", () => {
                                inviteEmailInput.value = btn.getAttribute("data-email");
                                suggestionsContainer.style.display = "none";
                                suggestionsContainer.innerHTML = "";
                            });
                        });
                    } catch (err) {
                        console.error("Suggestions search error:", err);
                    }
                }, 200);
            });

            // Close suggestions when clicking outside
            document.addEventListener("click", (e) => {
                if (e.target !== inviteEmailInput && e.target !== suggestionsContainer) {
                    if (suggestionsContainer) {
                        suggestionsContainer.style.display = "none";
                    }
                }
            });

            // Member Role Change Event Listeners
            document.querySelectorAll(".member-role-select").forEach(select => {
                select.addEventListener("change", async (e) => {
                    const memberId = select.getAttribute("data-id");
                    const newRole = e.target.value;
                    try {
                        await API.updateMemberRole(tripUuid, memberId, newRole);
                        window.showToast("Collaborator role updated successfully!", "success");
                        renderTripDetails(container, params);
                    } catch (err) {
                        window.showToast(err.message, "danger");
                        renderTripDetails(container, params);
                    }
                });
            });

            // Remove Member Buttons
            document.querySelectorAll(".remove-member-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const memberId = btn.getAttribute("data-id");
                    const memberName = btn.getAttribute("data-name");
                    if (confirm(`Remove ${memberName} from this trip?`)) {
                        try {
                            await API.removeMember(tripUuid, memberId);
                            window.showToast(`${memberName} removed.`, "success");
                            renderTripDetails(container, params);
                        } catch (err) {
                            window.showToast(err.message, "danger");
                        }
                    }
                });
            });
        }

        // Lightbox Preview Trigger Hooks
        const modalEl = document.getElementById("lightbox-modal");
        const mediaMount = document.getElementById("lightbox-media-mount");
        const titleEl = document.getElementById("lightbox-title");
        const uploaderEl = document.getElementById("lightbox-uploader");
        const dateEl = document.getElementById("lightbox-date");
        const sizeEl = document.getElementById("lightbox-size");
        const mimeEl = document.getElementById("lightbox-mime");
        const downloadBtn = document.getElementById("lightbox-download-btn");
        const deleteBtn = document.getElementById("lightbox-delete-btn");

        document.querySelectorAll(".gallery-item").forEach(item => {
            item.addEventListener("click", () => {
                const uuid = item.getAttribute("data-uuid");
                const mediaItem = gallery.find(g => g.uuid === uuid);
                if (!mediaItem) return;

                // Configure lightbox contents
                const privateUrl = API.getMediaUrl(mediaItem.uuid);
                
                if (mediaItem.media_type === "photo") {
                    mediaMount.innerHTML = `<img src="${privateUrl}" alt="Preview">`;
                } else {
                    mediaMount.innerHTML = `<video src="${privateUrl}" controls autoplay></video>`;
                }

                // Populate Meta details
                const sizeMB = (mediaItem.file_size / (1024 * 1024)).toFixed(2);
                const date = new Date(mediaItem.created_at).toLocaleString();
                
                titleEl.textContent = mediaItem.media_type === "photo" ? "Photo Memory" : "Video Memory";
                uploaderEl.textContent = `User #${mediaItem.uploaded_by}`; // Wait, we can map to user list if available, or keep it basic.
                dateEl.textContent = date;
                sizeEl.textContent = `${sizeMB} MB`;
                mimeEl.textContent = mediaItem.mime_type;

                // Setup download URL
                downloadBtn.href = API.getMediaUrl(mediaItem.uuid, true);

                // Setup Delete Permissions
                // Owner can delete any media. Member can delete own media.
                const canDelete = isOwner || (mediaItem.uploaded_by === currentUser.id);
                if (canDelete) {
                    deleteBtn.style.display = "block";
                    // Hook delete button click handler
                    deleteBtn.onclick = async () => {
                        if (confirm("Delete this memory forever? This action cannot be undone.")) {
                            try {
                                await API.deleteMedia(mediaItem.uuid);
                                window.showToast("Memory deleted.", "success");
                                // Close lightbox
                                modalEl.style.display = "none";
                                mediaMount.innerHTML = "";
                                // Refresh gallery
                                renderTripDetails(container, params);
                            } catch (err) {
                                window.showToast(err.message, "danger");
                            }
                        }
                    };
                } else {
                    deleteBtn.style.display = "none";
                }

                // Show Lightbox overlay
                modalEl.style.display = "flex";
            });
        });

        // Close Lightbox handler
        document.getElementById("lightbox-close").onclick = () => {
            modalEl.style.display = "none";
            mediaMount.innerHTML = ""; // Stop videos if playing
        };

        // Close lightbox on clicking backdrop
        modalEl.onclick = (e) => {
            if (e.target === modalEl) {
                modalEl.style.display = "none";
                mediaMount.innerHTML = "";
            }
        };

    } catch (err) {
        window.showToast("Failed to load trip details.", "danger");
        console.error("Trip details error:", err);
    }
}

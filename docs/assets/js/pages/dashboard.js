// Trip Memories Platform - Dashboard Page Module
import API from '../api.js';

export async function renderDashboard(container) {
    // Show skeleton loaders first
    container.innerHTML = `
        <div class="animate-fade-in">
            <h1 class="fw-bold mb-1">Dashboard</h1>
            <p class="text-secondary mb-5">Overview of your private self-hosted memories.</p>
            
            <div class="dashboard-grid">
                <div class="card-premium skeleton" style="height: 140px;"></div>
                <div class="card-premium skeleton" style="height: 140px;"></div>
                <div class="card-premium skeleton" style="height: 140px;"></div>
            </div>
            
            <div class="row g-4 mt-1">
                <div class="col-md-8">
                    <h3 class="fw-bold mb-4">Recent Activity</h3>
                    <div class="card-premium skeleton" style="height: 300px;"></div>
                </div>
                <div class="col-md-4">
                    <h3 class="fw-bold mb-4">Quick Actions</h3>
                    <div class="card-premium skeleton" style="height: 200px;"></div>
                </div>
            </div>
        </div>
    `;

    try {
        const user = JSON.parse(localStorage.getItem("user") || "{}");
        const trips = await API.getTrips();
        const activities = await API.getMyActivities();
        
        // Let's compute overall media count and size asynchronously
        let mediaCount = 0;
        let totalSizeBytes = 0;

        for (const trip of trips) {
            try {
                const gallery = await API.getGallery(trip.uuid);
                mediaCount += gallery.length;
                totalSizeBytes += gallery.reduce((acc, item) => acc + item.file_size, 0);
            } catch (err) {
                console.warn(`Could not fetch gallery for trip ${trip.uuid}`, err);
            }
        }

        // Format storage usage
        const storageMB = (totalSizeBytes / (1024 * 1024)).toFixed(1);
        const storageDisplay = storageMB > 1024 
            ? `${(storageMB / 1024).toFixed(1)} GB`
            : `${storageMB} MB`;

        // Render actual dashboard dashboard content
        container.innerHTML = `
            <div class="animate-fade-in">
                <h1 class="fw-bold mb-1">Hello, ${user.name || 'Traveler'}</h1>
                <p class="text-secondary mb-5">Welcome back to your private trip memory vault.</p>
                
                <div class="dashboard-grid">
                    <div class="card-premium">
                        <div class="text-secondary fs-7 text-uppercase fw-semibold tracking-wider">Total Trips</div>
                        <div class="stat-num">${trips.length}</div>
                        <div class="fs-8 text-secondary"><a href="#/trips" class="text-decoration-none text-dark">View trips →</a></div>
                    </div>
                    
                    <div class="card-premium">
                        <div class="text-secondary fs-7 text-uppercase fw-semibold tracking-wider">Total Media</div>
                        <div class="stat-num">${mediaCount}</div>
                        <div class="fs-8 text-secondary">Photos and videos archived</div>
                    </div>
                    
                    <div class="card-premium">
                        <div class="text-secondary fs-7 text-uppercase fw-semibold tracking-wider">Storage Used</div>
                        <div class="stat-num">${storageDisplay}</div>
                        <div class="fs-8 text-secondary">Self-hosted local disk space</div>
                    </div>
                </div>
                
                <div class="row g-4 mt-3">
                    <div class="col-md-8">
                        <h3 class="fw-bold mb-4">Recent Activity</h3>
                        <div class="card-premium">
                            ${activities.length === 0 ? `
                                <div class="text-center py-4 text-secondary">
                                    <i class="bi bi-clock-history fs-2"></i>
                                    <p class="mt-2 mb-0">No activities recorded yet.</p>
                                </div>
                            ` : `
                                <div class="activity-timeline">
                                    ${activities.slice(0, 5).map(act => {
                                        const date = new Date(act.created_at).toLocaleDateString(undefined, {
                                            month: 'short',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        });
                                        
                                        // User context
                                        const actor = act.user ? act.user.name : "You";
                                        
                                        let actionText = "";
                                        if (act.action === "created_trip") actionText = "created a new trip.";
                                        else if (act.action === "updated_trip") actionText = "updated trip details.";
                                        else if (act.action === "uploaded_media") actionText = "uploaded a new memory.";
                                        else if (act.action === "deleted_media") actionText = "deleted a memory.";
                                        else if (act.action === "invited_member") actionText = "invited a member to join.";
                                        else if (act.action === "joined_trip") actionText = "joined the trip.";
                                        else if (act.action === "removed_member") actionText = "removed a member.";
                                        else actionText = act.action;

                                        return `
                                            <div class="activity-item">
                                                <div class="fw-semibold text-dark fs-6">${actor} <span class="fw-normal text-secondary">${actionText}</span></div>
                                                <div class="fs-8 text-secondary mt-1">${date}</div>
                                            </div>
                                        `;
                                    }).join("")}
                                </div>
                            `}
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <h3 class="fw-bold mb-4">Quick Actions</h3>
                        <div class="card-premium d-flex flex-column gap-3">
                            <div class="quick-action-card p-2 rounded-3 border-0" onclick="window.location.hash='#/trips'">
                                <div class="quick-action-icon">
                                    <i class="bi bi-plus-lg"></i>
                                </div>
                                <div>
                                    <div class="fw-semibold">Create Trip</div>
                                    <p class="fs-8 mb-0 text-secondary">Start a new memory timeline</p>
                                </div>
                            </div>
                            
                            <div class="quick-action-card p-2 rounded-3 border-0" onclick="window.location.hash='#/profile'">
                                <div class="quick-action-icon">
                                    <i class="bi bi-shield-lock"></i>
                                </div>
                                <div>
                                    <div class="fw-semibold">Security Settings</div>
                                    <p class="fs-8 mb-0 text-secondary">Update account details</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        window.showToast("Failed to load dashboard data.", "danger");
        console.error("Dashboard error:", err);
    }
}

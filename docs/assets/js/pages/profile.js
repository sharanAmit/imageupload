// Trip Memories Platform - Profile Page Module
import API from '../api.js';

export async function renderProfile(container) {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    
    container.innerHTML = `
        <div class="animate-fade-in" style="max-width: 600px;">
            <h1 class="fw-bold mb-1">Profile Settings</h1>
            <p class="text-secondary mb-5">Manage your personal information and security credentials.</p>
            
            <div class="card-premium p-4 mb-5 bg-white">
                <h4 class="fw-bold mb-4">Account Information</h4>
                <div class="d-flex align-items-center gap-4 mb-4 pb-4 border-bottom">
                    <div class="rounded-circle bg-dark d-flex align-items-center justify-content-center text-white fw-bold fs-3" style="width: 72px; height: 72px;">
                        ${user.name ? user.name.charAt(0).toUpperCase() : '?'}
                    </div>
                    <div>
                        <h4 class="fw-bold mb-0 text-dark">${user.name || 'Member'}</h4>
                        <p class="text-secondary mb-0 fs-7">${user.email}</p>
                        <span class="badge bg-light text-secondary rounded-pill border fs-9 mt-1">Self-Hosted User</span>
                    </div>
                </div>
                
                <div class="form-group mb-3">
                    <label class="form-label fs-8 text-secondary">Unique User UUID</label>
                    <input type="text" class="form-control bg-light border-0 py-2 px-3 text-secondary fs-8" readonly value="${user.uuid}">
                </div>
                
                <div class="form-group mb-0">
                    <label class="form-label fs-8 text-secondary">Account Created On</label>
                    <input type="text" class="form-control bg-light border-0 py-2 px-3 text-secondary fs-8" readonly value="${new Date(user.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}">
                </div>
            </div>
            
            <div class="card-premium p-4 bg-white">
                <h4 class="fw-bold mb-4">Change Password</h4>
                
                <form id="change-pass-form">
                    <div class="form-group">
                        <label class="form-label">Current Password</label>
                        <input type="password" id="curr-password" class="form-control" required placeholder="••••••••">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">New Password</label>
                        <input type="password" id="new-password" class="form-control" required minlength="6" placeholder="At least 6 characters">
                    </div>
                    
                    <button type="submit" class="btn btn-premium mt-3" id="save-pass-btn">
                        Update Password
                    </button>
                </form>
            </div>
        </div>
    `;

    // Change Password submit handler
    const form = document.getElementById("change-pass-form");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const currentPassword = document.getElementById("curr-password").value;
        const newPassword = document.getElementById("new-password").value;
        const submitBtn = document.getElementById("save-pass-btn");

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Updating...`;

        try {
            await API.changePassword(currentPassword, newPassword);
            window.showToast("Password updated successfully!", "success");
            form.reset();
        } catch (err) {
            window.showToast(err.message || "Failed to update password.", "danger");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Update Password";
        }
    });
}

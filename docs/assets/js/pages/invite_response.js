// Trip Memories Platform - Invite Accept/Decline Response Page
import API from '../api.js';

function renderShell(container, bodyHtml) {
    container.innerHTML = `
        <div class="auth-container animate-slide-up text-center">
            <div class="logo-fan mx-auto mb-3" style="width:36px; height:36px;">
                <span class="fan-leaf leaf-blue" style="width:18px; height:18px;"></span>
                <span class="fan-leaf leaf-red" style="width:18px; height:18px; left:18px;"></span>
                <span class="fan-leaf leaf-yellow" style="width:18px; height:18px; left:18px; top:18px;"></span>
                <span class="fan-leaf leaf-green" style="width:18px; height:18px; top:18px;"></span>
            </div>
            ${bodyHtml}
        </div>
    `;
}

function renderError(container, message) {
    renderShell(container, `
        <h2 class="mt-2 mb-3 fw-bold">Invitation Unavailable</h2>
        <p class="text-secondary">${message}</p>
        <a href="#/login" class="btn btn-premium w-100 mt-3">Go to Sign In</a>
    `);
}

export async function renderInviteResponse(container, params) {
    const { token, action } = params;
    const isAuthenticated = !!localStorage.getItem("access_token");

    renderShell(container, `
        <div class="d-flex justify-content-center py-4">
            <div class="spinner-border text-dark" role="status"><span class="visually-hidden">Loading...</span></div>
        </div>
    `);

    let invite;
    try {
        invite = await API.getInviteDetails(token);
    } catch (err) {
        renderError(container, "This invitation link is invalid, has expired, or has already been responded to.");
        return;
    }

    if (action === "decline") {
        try {
            await API.declineInvite(token);
            renderShell(container, `
                <h2 class="mt-2 mb-3 fw-bold">Invitation Declined</h2>
                <p class="text-secondary">You've declined the invite to join <strong>"${invite.trip_name}"</strong>. No account changes were made.</p>
                <a href="${isAuthenticated ? '#/trips' : '#/login'}" class="btn btn-premium w-100 mt-3">
                    ${isAuthenticated ? 'Back to Trips' : 'Go to Sign In'}
                </a>
            `);
        } catch (err) {
            renderError(container, err.message || "We couldn't process your decline. Please try again.");
        }
        return;
    }

    // action === "accept"
    if (!invite.account_exists) {
        renderShell(container, `
            <h2 class="mt-2 mb-1 fw-bold">You're Invited!</h2>
            <p class="text-secondary">Create your account to accept and join <strong>"${invite.trip_name}"</strong> as a <strong>${invite.role}</strong>.</p>
            <a href="#/register?invite_token=${encodeURIComponent(token)}" class="btn btn-premium w-100 mt-3">Create Account &amp; Accept</a>
        `);
        return;
    }

    try {
        const result = await API.acceptInvite(token);
        renderShell(container, `
            <h2 class="mt-2 mb-3 fw-bold">Welcome Aboard!</h2>
            <p class="text-secondary">You've accepted the invite and joined <strong>"${result.trip_name}"</strong> as a <strong>${result.role}</strong>.</p>
            <a href="${isAuthenticated ? '#/trips' : '#/login'}" class="btn btn-premium w-100 mt-3">
                ${isAuthenticated ? 'View Your Trips' : 'Sign In to View'}
            </a>
        `);
    } catch (err) {
        renderError(container, err.message || "We couldn't process your acceptance. Please try again.");
    }
}

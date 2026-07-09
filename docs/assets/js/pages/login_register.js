// Trip Memories Platform - Auth Page Module
import API from '../api.js';

export async function renderLogin(container) {
    container.innerHTML = `
        <div class="auth-container animate-slide-up">
            <div class="text-center mb-5">
                <div class="logo-fan mx-auto mb-3" style="width:36px; height:36px;">
                    <span class="fan-leaf leaf-blue" style="width:18px; height:18px;"></span>
                    <span class="fan-leaf leaf-red" style="width:18px; height:18px; left:18px;"></span>
                    <span class="fan-leaf leaf-yellow" style="width:18px; height:18px; left:18px; top:18px;"></span>
                    <span class="fan-leaf leaf-green" style="width:18px; height:18px; top:18px;"></span>
                </div>
                <h2 class="mt-2 mb-1 fw-bold">Sign In</h2>
                <p class="text-secondary">Welcome back. Access your private memories.</p>
            </div>
            
            <form id="login-form">
                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" id="email" class="form-control" required placeholder="name@example.com">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="password" class="form-control" required placeholder="••••••••">
                </div>
                
                <button type="submit" class="btn btn-premium w-100 mt-3" id="submit-btn">
                    Sign In
                </button>
            </form>
            
            <div class="text-center my-3 text-secondary fs-8">or</div>
            <div id="google-signin-button" class="w-100 d-flex justify-content-center"></div>
            
            <div class="text-center mt-4 pt-2 border-top">
                <p class="text-secondary mb-0">
                    Don't have an account? 
                    <a href="#/register" class="text-dark fw-semibold text-decoration-none">Sign up</a>
                </p>
            </div>
        </div>
    `;

    const form = document.getElementById("login-form");
    const submitBtn = document.getElementById("submit-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Signing In...`;

        try {
            await API.login(email, password);
            window.showToast("Successfully authenticated!", "success");
            window.location.hash = "#/photos";
        } catch (err) {
            window.showToast(err.message || "Failed to login. Please try again.", "danger");
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Sign In";
        }
    });

    // Initialize Google SSO dynamically
    initializeGoogleButton();
}

export async function renderRegister(container) {
    // Check for invite token in hash query params
    const hash = window.location.hash;
    let inviteToken = null;
    let inviteDetails = null;
    const queryIdx = hash.indexOf("?");
    if (queryIdx !== -1) {
        const queryStr = hash.substring(queryIdx + 1);
        const pairs = queryStr.split("&");
        for (const pair of pairs) {
            const [k, v] = pair.split("=");
            if (k === "invite_token") {
                inviteToken = decodeURIComponent(v);
                break;
            }
        }
    }

    if (inviteToken) {
        try {
            inviteDetails = await API.getInviteDetails(inviteToken);
        } catch (err) {
            console.error("Failed to load invite details:", err);
            window.showToast("Invitation token is invalid or already used.", "danger");
        }
    }

    const inviteBannerHTML = inviteDetails ? `
        <div class="alert alert-info border-0 rounded-4 p-3 mb-4 text-start animate-fade-in" style="background-color: #E8F0FE; color: #1967D2; font-size: 0.8rem; line-height: 1.4;">
            <i class="bi bi-gift-fill me-2 fs-6"></i>
            You are invited to collaborate on <strong>"${inviteDetails.trip_name}"</strong> as a <strong>${inviteDetails.role}</strong>! Create your account below to accept.
        </div>
    ` : '';

    const emailValue = inviteDetails ? inviteDetails.email : '';
    const emailReadOnly = inviteDetails ? 'readonly style="background-color: var(--bg-secondary); cursor: not-allowed;"' : '';

    container.innerHTML = `
        <div class="auth-container animate-slide-up">
            <div class="text-center mb-5">
                <div class="logo-fan mx-auto mb-3" style="width:36px; height:36px;">
                    <span class="fan-leaf leaf-blue" style="width:18px; height:18px;"></span>
                    <span class="fan-leaf leaf-red" style="width:18px; height:18px; left:18px;"></span>
                    <span class="fan-leaf leaf-yellow" style="width:18px; height:18px; left:18px; top:18px;"></span>
                    <span class="fan-leaf leaf-green" style="width:18px; height:18px; top:18px;"></span>
                </div>
                <h2 class="mt-2 mb-1 fw-bold">Create Account</h2>
                <p class="text-secondary">Join to self-host your travel memories.</p>
            </div>
            
            ${inviteBannerHTML}
            
            <form id="register-form">
                <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" id="name" class="form-control" required placeholder="John Doe">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" id="email" class="form-control" required placeholder="name@example.com" value="${emailValue}" ${emailReadOnly}>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="password" class="form-control" required minlength="6" placeholder="At least 6 characters">
                </div>
                
                <button type="submit" class="btn btn-premium w-100 mt-3" id="submit-btn">
                    Register & Join
                </button>
            </form>
            
            <div class="text-center my-3 text-secondary fs-8">or</div>
            <div id="google-signin-button" class="w-100 d-flex justify-content-center"></div>
            
            <div class="text-center mt-4 pt-2 border-top">
                <p class="text-secondary mb-0">
                    Already have an account? 
                    <a href="#/login" class="text-dark fw-semibold text-decoration-none">Sign in</a>
                </p>
            </div>
        </div>
    `;

    const form = document.getElementById("register-form");
    const submitBtn = document.getElementById("submit-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Registering...`;

        try {
            await API.register(name, email, password, inviteToken);
            window.showToast("Account created successfully! Joining your trip...", "success");
            
            // Auto-login after registration for seamless onboarding
            try {
                await API.login(email, password);
                window.location.hash = "#/photos";
            } catch (loginErr) {
                window.location.hash = "#/login";
            }
        } catch (err) {
            window.showToast(err.message || "Failed to create account.", "danger");
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Register & Join";
        }
    });

    // Initialize Google SSO dynamically
    initializeGoogleButton();
}

async function initializeGoogleButton() {
    try {
        const config = await API.getAuthConfig();
        const btnContainer = document.getElementById("google-signin-button");
        if (!btnContainer) return;

        if (config && config.google_client_id) {
            google.accounts.id.initialize({
                client_id: config.google_client_id,
                callback: window.handleGoogleSignIn
            });
            google.accounts.id.renderButton(
                btnContainer,
                { theme: "outline", size: "large", width: "340", shape: "pill" }
            );
        } else {
            btnContainer.innerHTML = `
                <div class="google-config-alert text-start w-100">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <strong>Google Login Not Set</strong>: Add <code>GOOGLE_CLIENT_ID</code> in <code>.env</code> and restart backend to enable Google SSO.
                </div>
            `;
        }
    } catch (err) {
        console.warn("Failed to dynamically configure Google SSO button:", err);
    }
}


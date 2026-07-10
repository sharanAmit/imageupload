// Trip Memories Platform - Main JS & Client-Side Router
import API from './api.js';

// Global UI Utilities
const showToast = (message, type = "info") => {
    const toastEl = document.getElementById("live-toast");
    const toastBody = document.getElementById("toast-message");
    
    // Set color based on type
    toastEl.className = "toast align-items-center text-white border-0 rounded-4 shadow-lg";
    if (type === "success") {
        toastEl.classList.add("bg-success");
    } else if (type === "danger") {
        toastEl.classList.add("bg-danger");
    } else if (type === "warning") {
        toastEl.classList.add("bg-warning");
    } else {
        toastEl.classList.add("bg-dark");
    }
    
    toastBody.textContent = message;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
};

const showSpinner = () => {
    const main = document.getElementById("main-content");
    main.innerHTML = `
        <div class="d-flex justify-content-center align-items-center flex-grow-1 py-5 animate-fade-in">
            <div class="spinner-border text-dark" role="status" style="width: 2.5rem; height: 2.5rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
};

// Google OAuth Sign-in callback handler
window.handleGoogleSignIn = async (response) => {
    const idToken = response.credential;
    
    // Extract invite token from hash URL query string if present
    const hash = window.location.hash;
    let inviteToken = null;
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
    
    try {
        showSpinner();
        await API.loginWithGoogle(idToken, inviteToken);
        showToast("Signed in with Google successfully!", "success");
        window.location.hash = "#/photos";
    } catch (err) {
        showToast("Google Sign-In failed: " + err.message, "danger");
        setTimeout(() => window.location.reload(), 1500);
    }
};

// Route mapping
const routes = {
    "#/login": { protected: false, file: "login_register.js", action: "renderLogin" },
    "#/register": { protected: false, file: "login_register.js", action: "renderRegister" },
    "#/photos": { protected: true, file: "photos.js", action: "renderPhotosTimeline" },
    "#/dashboard": { protected: true, file: "dashboard.js", action: "renderDashboard" },
    "#/trips": { protected: true, file: "trips.js", action: "renderTrips" },
    "#/profile": { protected: true, file: "profile.js", action: "renderProfile" }
};

// Dynamic Route Matcher (e.g. for #/trip/uuid)
const dynamicRoutes = [
    {
        pattern: /^#\/trip\/([a-zA-Z0-9-]+)$/,
        protected: true,
        file: "trips.js",
        action: "renderTripDetails",
        paramName: "tripUuid"
    },
    {
        pattern: /^#\/invite\/([a-zA-Z0-9-]+)\/(accept|decline)$/,
        protected: false,
        file: "invite_response.js",
        action: "renderInviteResponse",
        paramNames: ["token", "action"]
    }
];

// SPA Router class
class Router {
    constructor() {
        this.sidebar = document.getElementById("app-sidebar");
        this.appHeader = document.getElementById("app-header");
        this.mainContent = document.getElementById("main-content");
        this.initEventListeners();
    }

    initEventListeners() {
        window.addEventListener("hashchange", () => this.route());
        window.addEventListener("load", () => this.route());
        
        // Setup Search handler (Real-time Filtering across Photos timeline and Trips dashboard)
        document.getElementById("global-search-input").addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const hash = window.location.hash || "#/photos";
            
            if (hash === "#/photos") {
                document.querySelectorAll(".timeline-group").forEach(group => {
                    let visibleItems = 0;
                    group.querySelectorAll(".gallery-item").forEach(item => {
                        const trip = item.getAttribute("data-trip") || "";
                        const date = item.getAttribute("data-date") || "";
                        const isVideo = item.querySelector("video") !== null;
                        const type = isVideo ? "video" : "photo";
                        
                        if (query === "" || trip.includes(query) || date.includes(query) || type.includes(query)) {
                            item.style.display = "block";
                            visibleItems++;
                        } else {
                            item.style.display = "none";
                        }
                    });
                    if (visibleItems === 0) {
                        group.style.display = "none";
                    } else {
                        group.style.display = "block";
                    }
                });
            } else if (hash === "#/trips") {
                document.querySelectorAll("#trips-list > .col-md-6, #trips-list > .col-lg-4").forEach(card => {
                    const title = card.querySelector("h4")?.textContent.toLowerCase() || "";
                    const desc = card.querySelector("p")?.textContent.toLowerCase() || "";
                    if (title.includes(query) || desc.includes(query)) {
                        card.style.display = "block";
                    } else {
                        card.style.display = "none";
                    }
                });
            }
        });

        // Setup Logout handler
        document.getElementById("nav-logout").addEventListener("click", (e) => {
            e.preventDefault();
            API.logout();
            showToast("Logged out successfully.", "success");
        });
    }

    async route() {
        let hash = window.location.hash || "#/photos";
        
        // Strip query string for routing lookup
        let cleanHash = hash;
        const queryIdx = hash.indexOf("?");
        if (queryIdx !== -1) {
            cleanHash = hash.substring(0, queryIdx);
        }
        
        // Normalize hash trailing slash
        if (cleanHash.endsWith("/")) cleanHash = cleanHash.slice(0, -1);
        
        // Find matching route
        let routeMatch = routes[cleanHash];
        let params = {};
        
        if (!routeMatch) {
            // Check dynamic routes
            for (const dynRoute of dynamicRoutes) {
                const match = cleanHash.match(dynRoute.pattern);
                if (match) {
                    routeMatch = dynRoute;
                    if (dynRoute.paramNames) {
                        dynRoute.paramNames.forEach((name, i) => {
                            params[name] = match[i + 1];
                        });
                    } else {
                        params[dynRoute.paramName] = match[1];
                    }
                    break;
                }
            }
        }
        
        // Fallback for Page Not Found
        if (!routeMatch) {
            this.mainContent.innerHTML = `
                <div class="text-center py-5">
                    <h2>Page Not Found</h2>
                    <p>The page you are looking for does not exist.</p>
                    <a href="#/photos" class="btn btn-premium mt-3">Back to Photos</a>
                </div>
            `;
            return;
        }

        // Auth Gate
        const isAuthenticated = !!localStorage.getItem("access_token");
        if (routeMatch.protected && !isAuthenticated) {
            window.location.hash = "#/login";
            return;
        }
        if (!routeMatch.protected && isAuthenticated && (cleanHash === "#/login" || cleanHash === "#/register")) {
            window.location.hash = "#/photos";
            return;
        }

        // Update navigation sidebar and header visibility
        if (routeMatch.protected) {
            this.sidebar.style.display = "flex";
            this.appHeader.style.display = "flex";
            
            // Populate profile avatar bubble
            const user = JSON.parse(localStorage.getItem("user") || "{}");
            const avatarEl = document.getElementById("header-profile-avatar");
            if (user.profile_image) {
                avatarEl.innerHTML = `<img src="${user.profile_image}" alt="Profile">`;
            } else {
                avatarEl.textContent = user.name ? user.name.charAt(0).toUpperCase() : "?";
            }
            
            // Set active class on sidebar links
            document.querySelectorAll(".sidebar-link").forEach(link => {
                link.classList.remove("active");
                if (link.getAttribute("href") === cleanHash || (cleanHash.startsWith("#/trip/") && link.id === "nav-trips")) {
                    link.classList.add("active");
                }
            });
        } else {
            this.sidebar.style.display = "none";
            this.appHeader.style.display = "none";
        }

        // Dynamically load page module and call render action
        showSpinner();
        try {
            const modulePath = `./pages/${routeMatch.file}`;
            const module = await import(modulePath);
            await module[routeMatch.action](this.mainContent, params);
        } catch (err) {
            console.error("Router error:", err);
            this.mainContent.innerHTML = `
                <div class="text-center py-5">
                    <h2>Failed to Load Page</h2>
                    <p class="text-danger">${err.message}</p>
                    <button onclick="window.location.reload()" class="btn btn-premium mt-3">Reload Page</button>
                </div>
            `;
        }
    }
}

// Initialize application router
const appRouter = new Router();

// Expose toast utilities globally
window.showToast = showToast;
window.showSpinner = showSpinner;

// Trip Memories Platform - API Client

const API_BASE_URL = localStorage.getItem("api_base_url") || "http://localhost:8050";

const API = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        // Add headers
        options.headers = options.headers || {};
        
        const accessToken = localStorage.getItem("access_token");
        if (accessToken && !options.headers["Authorization"]) {
            options.headers["Authorization"] = `Bearer ${accessToken}`;
        }
        
        if (!(options.body instanceof FormData) && !options.headers["Content-Type"]) {
            options.headers["Content-Type"] = "application/json";
        }

        try {
            let response = await fetch(url, options);
            
            // Handle unauthorized (token expired) - attempt refresh
            if (response.status === 401 && localStorage.getItem("refresh_token")) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry original request with new token
                    options.headers["Authorization"] = `Bearer ${localStorage.getItem("access_token")}`;
                    response = await fetch(url, options);
                } else {
                    // Refresh failed, redirect to login
                    this.clearSession();
                    window.location.hash = "#/login";
                    throw new Error("Session expired. Please login again.");
                }
            }
            
            // Check success status
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData.detail || errorData.message || `HTTP error! status: ${response.status}`;
                throw new Error(message);
            }
            
            // If response is 204 No Content, return null
            if (response.status === 204) {
                return null;
            }
            
            // Check content type before parsing
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return await response.json();
            }
            
            return response; // Return response stream (e.g. for media)
        } catch (error) {
            console.error(`API Request Failure on ${endpoint}:`, error);
            throw error;
        }
    },

    async refreshToken() {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) return false;
        
        try {
            const url = `${API_BASE_URL}/refresh`;
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem("access_token", data.access_token);
                localStorage.setItem("refresh_token", data.refresh_token);
                return true;
            }
        } catch (err) {
            console.error("Token refresh failed:", err);
        }
        
        return false;
    },

    clearSession() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
    },

    async loginWithGoogle(idToken, inviteToken = null) {
        let url = "/auth/google";
        if (inviteToken) {
            url += `?invite_token=${encodeURIComponent(inviteToken)}`;
        }
        const data = await this.request(url, {
            method: "POST",
            body: JSON.stringify({ id_token: idToken })
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        
        // Fetch and store user profile details
        const user = await this.getCurrentUser();
        localStorage.setItem("user", JSON.stringify(user));
        return user;
    },

    async getAuthConfig() {
        return await this.request("/auth/config");
    },

    async searchUsers(query) {
        return await this.request(`/users/search?q=${encodeURIComponent(query)}`);
    },

    async getInviteDetails(token) {
        return await this.request(`/auth/invite/${encodeURIComponent(token)}`);
    },

    // Auth endpoints
    async login(email, password) {
        const data = await this.request("/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        
        // Fetch and store user profile details
        const user = await this.getCurrentUser();
        localStorage.setItem("user", JSON.stringify(user));
        return user;
    },

    async register(name, email, password, inviteToken = null) {
        let endpoint = "/register";
        if (inviteToken) {
            endpoint += `?invite_token=${encodeURIComponent(inviteToken)}`;
        }
        return await this.request(endpoint, {
            method: "POST",
            body: JSON.stringify({ name, email, password })
        });
    },

    async getCurrentUser() {
        return await this.request("/me");
    },

    async changePassword(currentPassword, newPassword) {
        return await this.request("/change-password", {
            method: "POST",
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
        });
    },

    async logout() {
        try {
            await this.request("/logout", { method: "POST" });
        } catch (err) {
            console.warn("Logout request failed on server, cleaning local session anyway.");
        }
        this.clearSession();
        window.location.hash = "#/login";
    },

    // Trips endpoints
    async getTrips() {
        return await this.request("/trip");
    },

    async getTripDetails(uuid) {
        return await this.request(`/trip/${uuid}`);
    },

    async createTrip(tripName, description, coverImage = "") {
        return await this.request("/trip", {
            method: "POST",
            body: JSON.stringify({ trip_name: tripName, description, cover_image: coverImage })
        });
    },

    async updateTrip(uuid, tripName, description, coverImage = null) {
        return await this.request(`/trip/${uuid}`, {
            method: "PUT",
            body: JSON.stringify({ trip_name: tripName, description, cover_image: coverImage })
        });
    },

    async deleteTrip(uuid) {
        return await this.request(`/trip/${uuid}`, {
            method: "DELETE"
        });
    },

    async inviteMember(tripUuid, email, role = "member") {
        return await this.request(`/trip/${tripUuid}/invite`, {
            method: "POST",
            body: JSON.stringify({ email, role })
        });
    },

    async joinTrip(tripUuid) {
        return await this.request(`/trip/${tripUuid}/join`, {
            method: "POST"
        });
    },

    async removeMember(tripUuid, memberId) {
        return await this.request(`/trip/${tripUuid}/member/${memberId}`, {
            method: "DELETE"
        });
    },

    async updateMemberRole(tripUuid, memberId, role) {
        return await this.request(`/trip/${tripUuid}/member/${memberId}/role`, {
            method: "PUT",
            body: JSON.stringify({ role })
        });
    },

    // Media endpoints
    async uploadMedia(tripUuid, file, onProgress) {
        const formData = new FormData();
        formData.append("file", file);
        
        return await this.request(`/trip/${tripUuid}/upload`, {
            method: "POST",
            body: formData
        });
    },

    async getGallery(tripUuid) {
        return await this.request(`/trip/${tripUuid}/gallery`);
    },

    async getAllPhotos() {
        return await this.request("/media");
    },

    async deleteMedia(mediaUuid) {
        return await this.request(`/media/${mediaUuid}`, {
            method: "DELETE"
        });
    },
    
    getMediaUrl(mediaUuid, download = false) {
        const token = localStorage.getItem("access_token");
        return `${API_BASE_URL}/media/${mediaUuid}?download=${download}&token=${token}`; 
        // Note: For serving files via standard tag requests, we append the token to URL or access directly.
        // Wait, standard <img src> requests don't send auth headers, so we can support token in query parameter inside FastAPI backend, or rely on public uploads URL (like `/uploads/...`). 
        // Wait, the API routes return the public URL as `/uploads/...` which is statically mounted and open, which makes loading images super fast and simple. 
        // Alternatively, the API.js can return the raw /uploads url returned by the media object, which is exactly how our media response schema handles it!
    },

    // Activity endpoints
    async getTripActivities(tripUuid) {
        return await this.request(`/trip/${tripUuid}/activities`);
    },
    
    async getMyActivities() {
        return await this.request("/activities/me");
    }
};

window.API = API; // Make globally accessible
export default API;

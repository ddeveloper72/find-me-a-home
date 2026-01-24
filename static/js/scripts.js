// Custom JavaScript for Find Me a Home

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function () {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Toggle favorite property
function toggleFavorite(propertyId) {
    const btn = document.querySelector(`#favorite-btn-${propertyId}`);
    const icon = btn.querySelector('i');

    fetch(`/properties/${propertyId}/favorite`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.is_favorite) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    btn.classList.add('active');
                    showToast('Property added to favorites!', 'success');
                } else {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    btn.classList.remove('active');
                    showToast('Property removed from favorites.', 'info');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Failed to update favorite status.', 'danger');
        });
}

// Update favorite property notes and rank
function updateFavorite(propertyId, rank, notes) {
    fetch(`/properties/${propertyId}/favorite/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rank, notes })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Favorite updated!', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Failed to update favorite.', 'danger');
        });
}

// Save search criteria
function saveSearch(criteria) {
    const name = prompt('Enter a name for this search:');
    if (!name) return;

    criteria.name = name;

    fetch('/search/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(criteria)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Search saved successfully!', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Failed to save search.', 'danger');
        });
}

// Delete saved search
function deleteSavedSearch(searchId) {
    if (!confirm('Are you sure you want to delete this saved search?')) return;

    fetch(`/search/saved/${searchId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Search deleted successfully!', 'success');
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Failed to delete search.', 'danger');
        });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '11';
    document.body.appendChild(container);
    return container;
}

// Initialize Leaflet map
function initMap(elementId, center = [53.349805, -6.26031], zoom = 7) {
    const map = L.map(elementId).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    return map;
}

// Add property markers to map
function addPropertyMarkers(map, properties) {
    const propertyIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    properties.forEach(property => {
        if (property.latitude && property.longitude) {
            const marker = L.marker([property.latitude, property.longitude], { icon: propertyIcon })
                .bindPopup(`
                    <div class="property-popup">
                        <h6><a href="/properties/${property.id}">${property.title}</a></h6>
                        <p class="mb-1"><strong>€${property.price.toLocaleString()}</strong></p>
                        <p class="mb-0 small">${property.address}</p>
                    </div>
                `)
                .addTo(map);
        }
    });
}

// Add school markers to map
function addSchoolMarkers(map, schools) {
    const schoolIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    schools.forEach(school => {
        if (school.latitude && school.longitude) {
            const marker = L.marker([school.latitude, school.longitude], { icon: schoolIcon })
                .bindPopup(`
                    <div class="school-popup">
                        <h6><a href="/schools/${school.id}">${school.name}</a></h6>
                        <p class="mb-0 small">${school.address}</p>
                        ${school.distance ? `<p class="mb-0 small"><strong>${school.distance} km away</strong></p>` : ''}
                    </div>
                `)
                .addTo(map);
        }
    });
}

// Add transport markers to map
function addTransportMarkers(map, stations) {
    const transportIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    stations.forEach(station => {
        if (station.latitude && station.longitude) {
            const marker = L.marker([station.latitude, station.longitude], { icon: transportIcon })
                .bindPopup(`
                    <div class="transport-popup">
                        <h6><a href="/transport/${station.id}">${station.name}</a></h6>
                        <p class="mb-0 small">${station.station_type}</p>
                        ${station.distance ? `<p class="mb-0 small"><strong>${station.distance} km away</strong></p>` : ''}
                    </div>
                `)
                .addTo(map);
        }
    });
}

// Form validation
function validateSearchForm() {
    const minPrice = parseFloat(document.getElementById('min_price')?.value);
    const maxPrice = parseFloat(document.getElementById('max_price')?.value);

    if (minPrice && maxPrice && minPrice > maxPrice) {
        showToast('Minimum price cannot be greater than maximum price', 'warning');
        return false;
    }

    return true;
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

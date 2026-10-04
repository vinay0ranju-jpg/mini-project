/**
 * Personal Shopping Agent - Dynamic Comparison Manager
 * Handles multi-product checkbox selection, floating comparison dock, and route navigation.
 */

window.ComparisonManager = (function () {
    const STORAGE_KEY = "psa_selected_comparisons";

    function getSelectedIds() {
        try {
            const data = sessionStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            return [];
        }
    }

    function saveSelectedIds(ids) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
        } catch (e) {
            console.error("Storage error:", e);
        }
        updateUI();
    }

    function toggleProduct(productId) {
        let ids = getSelectedIds();
        if (ids.includes(productId)) {
            ids = ids.filter(id => id !== productId);
        } else {
            if (ids.length >= 4) {
                alert("You can compare up to 4 products at a time for optimal layout.");
                return false;
            }
            ids.push(productId);
        }
        saveSelectedIds(ids);
        return true;
    }

    function clear() {
        sessionStorage.removeItem(STORAGE_KEY);
        // Uncheck all checkboxes on current page
        document.querySelectorAll(".compare-checkbox").forEach(cb => {
            cb.checked = false;
        });
        updateUI();
    }

    function updateUI() {
        const ids = getSelectedIds();
        const tray = document.getElementById("comparison-floating-tray");
        const countSpan = document.getElementById("tray-selected-count");
        const navBadge = document.getElementById("nav-compare-badge");

        // Update nav badge
        if (navBadge) {
            if (ids.length > 0) {
                navBadge.textContent = ids.length;
                navBadge.classList.remove("d-none");
            } else {
                navBadge.classList.add("d-none");
            }
        }

        // Update floating tray
        if (tray && countSpan) {
            countSpan.textContent = ids.length;
            if (ids.length > 0) {
                tray.classList.remove("d-none");
            } else {
                tray.classList.add("d-none");
            }
        }

        // Sync checkboxes on current page
        document.querySelectorAll(".compare-checkbox").forEach(cb => {
            const pid = cb.getAttribute("data-id");
            cb.checked = ids.includes(pid);
        });
    }

    // Initialize listeners
    document.addEventListener("DOMContentLoaded", function () {
        // Wire up checkbox clicks
        document.querySelectorAll(".compare-checkbox").forEach(cb => {
            cb.addEventListener("change", function (e) {
                const pid = this.getAttribute("data-id");
                const success = toggleProduct(pid);
                if (!success) {
                    this.checked = false;
                }
            });
        });

        // Wire up floating tray buttons
        const trayCompareBtn = document.getElementById("btn-tray-compare");
        if (trayCompareBtn) {
            trayCompareBtn.addEventListener("click", function () {
                const ids = getSelectedIds();
                if (ids.length < 2) {
                    alert("Please select at least 2 products to compare.");
                    return;
                }
                window.location.href = `/compare?ids=${encodeURIComponent(ids.join(","))}`;
            });
        }

        const trayClearBtn = document.getElementById("btn-tray-clear");
        if (trayClearBtn) {
            trayClearBtn.addEventListener("click", function () {
                clear();
            });
        }

        updateUI();
    });

    return {
        getSelectedIds: getSelectedIds,
        toggleProduct: toggleProduct,
        clear: clear,
        updateUI: updateUI
    };
})();

/**
 * Personal Shopping Agent - Main Script
 * Handles input validation, UI interactions, and search state.
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Search Form Validation
    const searchForm = document.getElementById("main-search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", function (e) {
            const queryInput = document.getElementById("query");
            const minPrice = document.getElementById("min_price");
            const maxPrice = document.getElementById("max_price");

            if (!queryInput || !queryInput.value.trim()) {
                e.preventDefault();
                alert("Please enter a product name to search.");
                queryInput.focus();
                return false;
            }

            if (minPrice && maxPrice && minPrice.value && maxPrice.value) {
                const minVal = parseFloat(minPrice.value);
                const maxVal = parseFloat(maxPrice.value);
                if (minVal > maxVal) {
                    e.preventDefault();
                    alert(`Minimum price (₹${minVal}) cannot be greater than maximum price (₹${maxVal}).`);
                    minPrice.focus();
                    return false;
                }
            }

            // Show loading state on submit button
            const submitBtn = searchForm.querySelector("button[type='submit']");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>Searching Stores...`;
            }
        });
    }

    // 2. Reset Filters Button
    const resetBtn = document.getElementById("reset-filters-btn");
    if (resetBtn && searchForm) {
        resetBtn.addEventListener("click", function () {
            const selects = searchForm.querySelectorAll("select");
            selects.forEach(s => s.selectedIndex = 0);
            const numInputs = searchForm.querySelectorAll("input[type='number']");
            numInputs.forEach(i => i.value = "");
        });
    }

    // 3. Clear Comparison Page Button
    const clearCompBtn = document.getElementById("btn-clear-comparison-page");
    if (clearCompBtn) {
        clearCompBtn.addEventListener("click", function () {
            if (window.ComparisonManager) {
                window.ComparisonManager.clear();
            }
            window.location.href = "/products?q=all";
        });
    }
});

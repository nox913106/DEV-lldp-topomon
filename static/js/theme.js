/**
 * Theme management - applies saved theme on page load
 * Include this script in all pages to ensure consistent theming
 */

(function () {
    // Apply saved theme immediately to prevent flash
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

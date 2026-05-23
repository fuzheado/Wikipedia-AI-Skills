/**
 * Wikimedia CDN Asset Loader
 *
 * Dynamically loads JavaScript/CSS libraries from Wikimedia's privacy-preserving
 * CDN mirror. Use this in Toolforge web apps to avoid loading assets from
 * external, user-tracking CDNs.
 *
 * Usage:
 *   // Load a single script
 *   loadCDNScript('d3', '7.9.0', 'd3.min.js')
 *     .then(() => console.log('D3 loaded'))
 *     .catch(err => console.error('Failed:', err));
 *
 *   // Load multiple assets in parallel
 *   loadCDNAssets({
 *     scripts: [
 *       ['jquery', '3.6.0', 'jquery.min.js'],
 *       ['d3', '7.9.0', 'd3.min.js'],
 *     ],
 *     styles: [
 *       ['twitter-bootstrap', '5.3.0', 'css/bootstrap.min.css'],
 *     ]
 *   }).then(() => {
 *     console.log('All assets loaded');
 *     // Your app code here
 *   });
 */

const CDN_BASE = 'https://tools-static.wmflabs.org/cdnjs/ajax/libs';

/**
 * Load a single script from the Wikimedia CDN mirror.
 * @param {string} library - Library name (e.g., 'd3', 'jquery')
 * @param {string} version - Version number (e.g., '7.9.0')
 * @param {string} file - File path (e.g., 'd3.min.js')
 * @returns {Promise<void>}
 */
function loadCDNScript(library, version, file) {
    const url = `${CDN_BASE}/${library}/${version}/${file}`;
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load: ${url}`));
        document.head.appendChild(script);
    });
}

/**
 * Load a single stylesheet from the Wikimedia CDN mirror.
 * @param {string} library - Library name (e.g., 'twitter-bootstrap')
 * @param {string} version - Version number (e.g., '5.3.0')
 * @param {string} file - File path (e.g., 'css/bootstrap.min.css')
 * @returns {Promise<void>}
 */
function loadCDNStyle(library, version, file) {
    const url = `${CDN_BASE}/${library}/${version}/${file}`;
    return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.onload = () => resolve();
        link.onerror = () => reject(new Error(`Failed to load: ${url}`));
        document.head.appendChild(link);
    });
}

/**
 * Load multiple assets from the Wikimedia CDN mirror in parallel.
 * @param {Object} options
 * @param {Array<[string, string, string]>} options.scripts - Array of [library, version, file]
 * @param {Array<[string, string, string]>} options.styles - Array of [library, version, file]
 * @returns {Promise<void>}
 *
 * Example:
 *   loadCDNAssets({
 *     scripts: [
 *       ['jquery', '3.6.0', 'jquery.min.js'],
 *       ['d3', '7.9.0', 'd3.min.js'],
 *     ],
 *     styles: [
 *       ['twitter-bootstrap', '5.3.0', 'css/bootstrap.min.css'],
 *       ['font-awesome', '6.5.1', 'css/all.min.css'],
 *     ]
 *   }).then(() => {
 *     // All assets loaded. Safe to use jQuery, D3, Bootstrap, etc.
 *     $(document).ready(function() {
 *       d3.select('body').append('p').text('D3 loaded!');
 *     });
 *   }).catch(console.error);
 */
function loadCDNAssets({ scripts = [], styles = [] } = {}) {
    const promises = [
        ...scripts.map(([lib, ver, file]) => loadCDNScript(lib, ver, file)),
        ...styles.map(([lib, ver, file]) => loadCDNStyle(lib, ver, file)),
    ];
    return Promise.all(promises);
}

// ──────────────────────────────────────────────
// Example: Quick bootstrap with common libraries
// ──────────────────────────────────────────────
function loadCommonAssets() {
    return loadCDNAssets({
        scripts: [
            ['jquery', '3.6.0', 'jquery.min.js'],
        ],
        styles: [
            ['twitter-bootstrap', '5.3.0', 'css/bootstrap.min.css'],
            ['font-awesome', '6.5.1', 'css/all.min.css'],
        ],
    });
}

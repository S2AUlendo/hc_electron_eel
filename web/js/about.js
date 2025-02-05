// In your about window's renderer script (about.js)
window.addEventListener('DOMContentLoaded', () => {
    window.electronAPI.onAboutData((data) => {
        console.log(data)
        // Application Details
        document.querySelector('.app-version').textContent = data.version;
        document.querySelector('.electron-version').textContent = data.electronVersion;
        document.querySelector('.node-version').textContent = data.nodeVersion;
        document.querySelector('.chromium-version').textContent = data.chromiumVersion;

        // License Information
        const statusElement = document.querySelector('.license-status');
        statusElement.textContent = data.activated ? "Activated" : "Not Activated";
        
        if(!data.activated) {
            statusElement.parentElement.style.backgroundColor = '#ffebee';
            statusElement.parentElement.querySelector('.status-icon').innerHTML = 
                '<i class="fas fa-times-circle" style="color: #d32f2f;"></i>';
        }

        document.querySelector('.feature-level').textContent = `Tier ${data.feature}`;
        document.querySelector('.license-key').textContent = data.license_key;
        document.querySelector('.days-remaining').textContent = data.days_remaining;

        // Optional: Add expiration warning
        if(data.days_remaining <= 7) {
            document.querySelector('.days-remaining').style.color = '#d32f2f';
            document.querySelector('.days-remaining').insertAdjacentHTML('beforeend', 
                ' <i class="fas fa-exclamation-triangle"></i>');
        }
    });
});
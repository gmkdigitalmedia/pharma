document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // File input change handler
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0].name;
            const label = document.querySelector('label[for="file"]');
            label.textContent = fileName;
        });
    }

    // Content preview handler for ContentCraft
    const contentCraftForm = document.getElementById('contentcraft-form');
    if (contentCraftForm) {
        const hcpSelect = document.getElementById('hcp');
        
        hcpSelect.addEventListener('change', function() {
            const hcpTag = hcpSelect.options[hcpSelect.selectedIndex].text.match(/\((.*?)\)/)[1];
            
            // Show loading state
            const previewContainer = document.getElementById('content-preview');
            if (previewContainer) {
                previewContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Generating content...</p></div>';
            }
            
            // In a real application, this would be an API call
            // For this MVP, we'll simulate content generation
            setTimeout(() => {
                fetch('/static/data/content_blocks.json')
                    .then(response => response.json())
                    .then(data => {
                        if (!data[hcpTag]) {
                            hcpTag = 'balanced'; // Fallback tag
                        }
                        
                        // Generate content (simplified version of backend logic)
                        const blocks = data[hcpTag];
                        const block = blocks[Math.floor(Math.random() * blocks.length)];
                        const hcpName = hcpSelect.options[hcpSelect.selectedIndex].text.split(' (')[0];
                        
                        let content = `Dear ${hcpName},\n\n`;
                        const therapyAreas = ["cardiovascular health", "diabetes management", "oncology"];
                        content += block.replace('{therapy_area}', therapyAreas[Math.floor(Math.random() * therapyAreas.length)])
                            .replace('{percent}', Math.floor(Math.random() * 30) + 15)
                            .replace('{sample_size}', Math.floor(Math.random() * 4500) + 500);
                        
                        content += `\n\nWe would be pleased to discuss how this might benefit your patients. Please let me know if you would like to schedule a meeting or webinar.\n\nBest regards,\nYour Xupra Representative`;
                        
                        // Update content preview
                        if (previewContainer) {
                            previewContainer.textContent = content;
                        }
                    })
                    .catch(error => {
                        console.error('Error loading content blocks:', error);
                        if (previewContainer) {
                            previewContainer.textContent = 'Error generating content. Please try again.';
                        }
                    });
            }, 1000); // Simulate loading time
        });
    }

    // Campaign planning handler
    const engageOpticForm = document.getElementById('engageoptic-form');
    if (engageOpticForm) {
        const hcpSelect = document.getElementById('hcp');
        
        hcpSelect.addEventListener('change', function() {
            // In a real application, this would update content options
            // based on the selected HCP
            console.log('HCP selection changed');
        });
    }

    // Highlight flagged words in content
    const contentElements = document.querySelectorAll('.content-text');
    if (contentElements.length > 0) {
        contentElements.forEach(element => {
            const content = element.textContent;
            const flagsStr = element.getAttribute('data-flags');
            
            if (flagsStr && flagsStr !== '[]') {
                const flags = JSON.parse(flagsStr);
                let html = content;
                
                flags.forEach(flag => {
                    const regex = new RegExp('\\b' + flag + '\\b', 'gi');
                    html = html.replace(regex, `<span class="flagged-word" data-bs-toggle="tooltip" title="This word may have compliance issues">${flag}</span>`);
                });
                
                element.innerHTML = html;
                
                // Re-initialize tooltips
                const newTooltips = [].slice.call(element.querySelectorAll('[data-bs-toggle="tooltip"]'));
                newTooltips.map(function (tooltipEl) {
                    return new bootstrap.Tooltip(tooltipEl);
                });
            }
        });
    }
});

// Function to update progress bar
function updateProgress(progress) {
    const progressBar = document.getElementById('workflow-progress');
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = progress + '%';
    }
}

// Function to highlight active sidebar item
function setActiveSidebarItem(module) {
    const sidebarItems = document.querySelectorAll('.sidebar .nav-link');
    sidebarItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href').includes(module)) {
            item.classList.add('active');
        }
    });
}

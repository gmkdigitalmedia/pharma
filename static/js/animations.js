document.addEventListener('DOMContentLoaded', function() {
    // Initialize mesh animation for the hero section
    initHeroMeshAnimation();
    
    // Animate the feature cards on scroll
    const featureCards = document.querySelectorAll('.feature-card');
    
    if (featureCards.length > 0) {
        // Initially hide all cards
        featureCards.forEach(card => {
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        });
        
        // Show cards when they enter viewport
        const showCards = () => {
            featureCards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = "1";
                    card.style.transform = "translateY(0)";
                }, 150 * index); // Stagger animation
            });
        };
        
        // Trigger animation after a short delay
        setTimeout(showCards, 700); // Give more time for the hero mesh to load
    }
    
    // Animate the hero text
    const heroTitle = document.querySelector('.hero-title');
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroButton = document.querySelector('.hero-button');
    
    if (heroTitle && heroSubtitle && heroButton) {
        heroTitle.style.opacity = "0";
        heroTitle.style.transform = "translateY(-20px)";
        heroTitle.style.transition = "opacity 0.8s ease, transform 0.8s ease";
        
        heroSubtitle.style.opacity = "0";
        heroSubtitle.style.transition = "opacity 0.8s ease";
        
        heroButton.style.opacity = "0";
        heroButton.style.transform = "scale(0.9)";
        heroButton.style.transition = "opacity 0.8s ease, transform 0.8s ease";
        
        // Animate hero elements sequentially
        setTimeout(() => {
            heroTitle.style.opacity = "1";
            heroTitle.style.transform = "translateY(0)";
            
            setTimeout(() => {
                heroSubtitle.style.opacity = "1";
                
                setTimeout(() => {
                    heroButton.style.opacity = "1";
                    heroButton.style.transform = "scale(1)";
                }, 300);
            }, 300);
        }, 500); // Delay longer to let mesh initialize
    }
    
    // Dynamic shimmer effect for the hero banner
    const heroBanner = document.querySelector('.hero-banner');
    if (heroBanner) {
        setInterval(() => {
            const shimmer = document.createElement('div');
            shimmer.classList.add('hero-shimmer');
            heroBanner.appendChild(shimmer);
            
            setTimeout(() => {
                shimmer.remove();
            }, 1500);
        }, 3000);
    }
    
    // Animate the floating particles in the hero section
    const particles = document.querySelectorAll('.particle');
    
    if (particles.length > 0) {
        particles.forEach(particle => {
            // Random animation duration between 20-40s
            const duration = 20 + Math.random() * 20;
            // Random animation delay
            const delay = Math.random() * 5;
            
            particle.style.animationDuration = `${duration}s`;
            particle.style.animationDelay = `${delay}s`;
        });
    }
});

// Wave animation for the hero background
function createWaveAnimation() {
    const waveContainer = document.getElementById('wave-animation');
    if (!waveContainer) return;
    
    const waveColors = ['rgba(33, 150, 243, 0.3)', 'rgba(30, 136, 229, 0.2)', 'rgba(25, 118, 210, 0.1)'];
    
    waveColors.forEach((color, index) => {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '50');
        svg.setAttribute('class', 'wave-svg');
        svg.style.position = 'absolute';
        svg.style.bottom = `${index * 15}px`;
        svg.style.left = '0';
        svg.style.right = '0';
        
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute('fill', color);
        path.setAttribute('class', 'wave-path');
        
        // Set different animation for each wave
        path.style.animation = `wave ${7 + index * 2}s ease-in-out infinite`;
        path.style.animationDelay = `${index * 0.5}s`;
        
        svg.appendChild(path);
        waveContainer.appendChild(svg);
        
        // Set initial path
        updateWavePath(path);
    });
}

// Update wave path points for animation
function updateWavePath(path) {
    const width = window.innerWidth;
    const height = 50;
    const amplitude = 15;
    const frequency = 0.01;
    
    let d = `M 0 ${height/2}`;
    
    for (let x = 0; x <= width; x += 10) {
        const y = Math.sin(x * frequency) * amplitude + (height/2);
        d += ` L ${x} ${y}`;
    }
    
    d += ` L ${width} ${height} L 0 ${height} Z`;
    path.setAttribute('d', d);
}

// Resize wave paths when window is resized
window.addEventListener('resize', function() {
    const wavePaths = document.querySelectorAll('.wave-path');
    wavePaths.forEach(path => updateWavePath(path));
    
    // Also update mesh if it exists
    if (window.meshPoints && window.meshCanvas) {
        resizeMeshCanvas();
    }
});

// Interactive mesh animation for hero section
function initHeroMeshAnimation() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;
    
    // Create canvas for the mesh animation
    const canvas = document.createElement('canvas');
    canvas.id = 'hero-mesh-canvas';
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '1';
    canvas.style.pointerEvents = 'none'; // Allow clicks to pass through
    
    // Insert canvas as the first child of hero section
    if (heroSection.firstChild) {
        heroSection.insertBefore(canvas, heroSection.firstChild);
    } else {
        heroSection.appendChild(canvas);
    }
    
    // Initialize mesh
    window.meshCanvas = canvas;
    initMesh();
    
    // Add mouse move event for interaction
    heroSection.addEventListener('mousemove', handleMeshMouseMove);
    
    // Also add touch support for mobile
    heroSection.addEventListener('touchmove', function(e) {
        if (e.touches.length > 0) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            handleMeshMouseMove(mouseEvent);
        }
    });
}

function initMesh() {
    const canvas = window.meshCanvas;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Set canvas dimensions
    resizeMeshCanvas();
    
    // Create mesh points
    const spacing = 50;
    const xCount = Math.ceil(canvas.width / spacing) + 2;
    const yCount = Math.ceil(canvas.height / spacing) + 2;
    
    const points = [];
    
    for (let x = 0; x < xCount; x++) {
        for (let y = 0; y < yCount; y++) {
            const px = (x * spacing) - spacing/2;
            const py = (y * spacing) - spacing/2;
            
            points.push({
                x: px,
                y: py,
                originX: px,
                originY: py,
                vx: 0,
                vy: 0,
                dx: 0, // Distance from influence point
                dy: 0,
                color: `rgba(255, 255, 255, ${Math.random() * 0.15 + 0.1})` // White dots with random opacity
            });
        }
    }
    
    window.meshPoints = points;
    
    // Start animation
    animateMesh();
}

function resizeMeshCanvas() {
    const canvas = window.meshCanvas;
    if (!canvas) return;
    
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
}

function handleMeshMouseMove(e) {
    if (!window.meshCanvas || !window.meshPoints) return;
    
    const rect = window.meshCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Update influence point for each mesh point
    window.meshPoints.forEach(point => {
        const dx = mouseX - point.x;
        const dy = mouseY - point.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // The farther the point, the less influence
        const influence = Math.max(0, 150 - distance) / 150;
        
        if (influence > 0) {
            point.dx = dx;
            point.dy = dy;
            
            // Move points away from cursor
            point.vx += dx * influence * 0.01;
            point.vy += dy * influence * 0.01;
        }
    });
}

function animateMesh() {
    if (!window.meshCanvas || !window.meshPoints) return;
    
    const canvas = window.meshCanvas;
    const ctx = canvas.getContext('2d');
    const points = window.meshPoints;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Update points
    points.forEach(point => {
        // Apply a bit of drift
        point.vx += (Math.random() - 0.5) * 0.05;
        point.vy += (Math.random() - 0.5) * 0.05;
        
        // Apply spring forces to return to original position
        point.vx += (point.originX - point.x) * 0.03;
        point.vy += (point.originY - point.y) * 0.03;
        
        // Apply damping
        point.vx *= 0.92;
        point.vy *= 0.92;
        
        // Update position
        point.x += point.vx;
        point.y += point.vy;
    });
    
    // Draw connecting lines
    ctx.beginPath();
    
    // Connect nearby points
    for (let i = 0; i < points.length; i++) {
        const point = points[i];
        
        for (let j = i + 1; j < points.length; j++) {
            const neighbor = points[j];
            const dx = point.x - neighbor.x;
            const dy = point.y - neighbor.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < 100) {
                // Opacity based on distance
                const opacity = 1 - (dist / 100);
                
                // White lines for better visibility
                ctx.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.25})`;
                ctx.lineWidth = opacity * 0.8;
                
                ctx.beginPath();
                ctx.moveTo(point.x, point.y);
                ctx.lineTo(neighbor.x, neighbor.y);
                ctx.stroke();
            }
        }
    }
    
    // Draw points
    points.forEach(point => {
        ctx.fillStyle = point.color;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Schedule next frame
    requestAnimationFrame(animateMesh);
}
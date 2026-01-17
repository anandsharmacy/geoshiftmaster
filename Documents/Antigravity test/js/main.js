import { events, competitions, schedule, sponsors } from './data.js';

// Navbar Logic
const initNavbar = () => {
    const header = document.getElementById('main-header');
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    // Sticky Header
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Mobile Menu
    toggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        toggle.classList.toggle('active');
    });

    // Close menu on link click
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            toggle.classList.remove('active');
        });
    });
};

// Hero Canvas Animation
const initHeroAnimation = () => {
    const container = document.getElementById('hero-canvas-container');
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Set Dimensions
    const setSize = () => {
        canvas.width = container.offsetWidth;
        canvas.height = container.offsetHeight;
    };

    setSize();
    container.appendChild(canvas);
    window.addEventListener('resize', setSize);

    // Particles
    const particles = [];
    const particleCount = 50;

    class Particle {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 1;
            this.speedX = Math.random() * 1 - 0.5;
            this.speedY = Math.random() * 1 - 0.5;
            this.color = Math.random() > 0.5 ? '#00f3ff' : '#bc13fe';
            this.alpha = Math.random() * 0.5 + 0.1;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;

            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }

        draw() {
            ctx.globalAlpha = this.alpha;
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }

    const animate = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw Connecting Lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 1;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.update();
            p.draw();

            // Connect nearby particles
            for (let j = i; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(animate);
    };

    animate();
};

// Render Functions
const renderEvents = () => {
    const grid = document.getElementById('events-grid');
    if (!grid) return;

    grid.innerHTML = events.map((event, index) => `
        <div class="event-card reveal" style="transition-delay: ${index * 0.1}s">
            <span class="event-cat">${event.category}</span>
            <h3>${event.icon} ${event.title}</h3>
            <p>${event.desc}</p>
            <a href="#" class="btn-text">Details &rarr;</a>
        </div>
    `).join('');
};

const renderCompetitions = () => {
    const container = document.querySelector('.carousel-container');
    if (!container) return;

    container.innerHTML = competitions.map(comp => `
        <div class="comp-card reveal">
            <div class="comp-icon">${comp.icon}</div>
            <h4>${comp.title}</h4>
            <p class="comp-meta"><span>📅 ${comp.date}</span> <span>🏆 ${comp.prize}</span></p>
            <a href="#" class="btn btn-outline btn-sm">Join</a>
        </div>
    `).join('');
};

const renderSchedule = () => {
    const container = document.getElementById('timeline');
    if (!container) return;

    container.innerHTML = schedule.map((item, index) => `
        <div class="timeline-item reveal" style="transition-delay: ${index * 0.2}s">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <span class="time">${item.time}</span>
                <h4>${item.event}</h4>
                <p>📍 ${item.location} | ${item.day}</p>
            </div>
        </div>
    `).join('');
};

const renderSponsors = () => {
    const grid = document.querySelector('.sponsor-grid');
    if (!grid) return;

    grid.innerHTML = sponsors.map(sponsor => `
        <div class="sponsor-card reveal">
            <div class="sponsor-logo-placeholder">${sponsor.name.substring(0, 2)}</div>
            <p>${sponsor.name}</p>
            <span class="sponsor-type">${sponsor.type}</span>
        </div>
    `).join('');
};

// Scroll Observer (Reveal on Scroll)
const initScrollObserver = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

    // Observe dynamic elements after render
    setTimeout(() => {
        document.querySelectorAll('.event-card, .comp-card, .timeline-item, .sponsor-card').forEach(el => observer.observe(el));
    }, 100);
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initHeroAnimation();
    renderEvents();
    renderCompetitions();
    renderSchedule();
    renderSponsors();
    initScrollObserver();
});

// Additive 3D polish: mouse-tilt, count-up, staggered entrance, button
// ripple, ambient particles. Purely cosmetic — no app logic lives here.
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.card-3d');
    cards.forEach((card, i) => {
        card.style.setProperty('--card-i', i);
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform = `perspective(1400px) rotateX(${-y * 6}deg) rotateY(${x * 6}deg) translateY(-6px) translateZ(10px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1400px) rotateX(0.8deg) rotateY(-0.8deg) translateZ(0)';
        });
    });

    document.querySelectorAll('[data-count-to]').forEach((el) => {
        const target = parseFloat(el.dataset.countTo);
        if (Number.isNaN(target)) return;
        const decimals = el.dataset.countDecimals ? parseInt(el.dataset.countDecimals, 10) : 0;
        const suffix = el.dataset.countSuffix || '';
        const duration = 900;
        const start = performance.now();
        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = target * eased;
            el.textContent = value.toFixed(decimals) + suffix;
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    });

    const bar = document.querySelector('.training-progress .bar');
    if (bar && bar.dataset.width) {
        requestAnimationFrame(() => { bar.style.width = bar.dataset.width; });
    }

    // Ripple feedback on any .btn-3d click.
    document.querySelectorAll('.btn-3d').forEach((btn) => {
        btn.addEventListener('click', function (e) {
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height);
            ripple.className = 'ripple';
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 650);
        });
    });

    // Ambient drifting particles behind the content (cheap, pure CSS driven).
    const particles = document.createElement('div');
    particles.className = 'particles';
    const count = window.innerWidth < 768 ? 10 : 22;
    for (let i = 0; i < count; i++) {
        const p = document.createElement('span');
        const size = 2 + Math.random() * 3;
        p.style.width = p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + 'vw';
        p.style.setProperty('--drift', (Math.random() * 60 - 30) + 'px');
        p.style.animationDuration = (14 + Math.random() * 16) + 's';
        p.style.animationDelay = (Math.random() * 20) + 's';
        particles.appendChild(p);
    }
    document.body.appendChild(particles);
});

document.addEventListener('DOMContentLoaded', function () {
    const overlay = document.getElementById('lightbox');
    const img = document.getElementById('lightboxImg');
    if (!overlay || !img) return;

    document.querySelectorAll('.showcase-img-wrapper img').forEach(function (el) {
        el.addEventListener('click', function () {
            img.src = el.src;
            img.alt = el.alt;
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    function close() {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    document.getElementById('lightboxClose').addEventListener('click', close);
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) close();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') close();
    });
});

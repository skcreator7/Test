// Smooth scroll to links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href')).scrollIntoView({
      behavior: 'smooth'
    });
  });
});

// Copy link functionality
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const link = btn.dataset.link;
    try {
      await navigator.clipboard.writeText(link);
      btn.textContent = 'Copied!';
      setTimeout(() => {
        btn.textContent = 'Copy Link';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  });
});

// Lazy load images
const lazyImages = document.querySelectorAll('img.lazy');
const imageObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.remove('lazy');
      imageObserver.unobserve(img);
    }
  });
});

lazyImages.forEach(img => imageObserver.observe(img));

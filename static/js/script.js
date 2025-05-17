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

// Notification system
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Error handling for failed API calls
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled rejection:', event.reason);
  showNotification('An error occurred', 'error');
});

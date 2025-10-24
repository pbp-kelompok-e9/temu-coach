function showToast(title, message, type = 'normal', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toastComponent) return;

    // Reset semua gaya dulu
    toastComponent.style = '';
    toastComponent.style.transition = 'all 0.4s ease';
    toastComponent.style.borderRadius = '12px';
    toastComponent.style.padding = '16px 20px';
    toastComponent.style.color = '#fff';
    toastComponent.style.backdropFilter = 'blur(8px)';
    toastComponent.style.boxShadow = '0 8px 25px rgba(0,0,0,0.25)';
    toastComponent.style.transform = 'translateY(80px)';
    toastComponent.style.opacity = '0';
    toastComponent.style.position = 'fixed';
    toastComponent.style.bottom = '30px';
    toastComponent.style.right = '30px';
    toastComponent.style.minWidth = '240px';
    toastComponent.style.zIndex = '40';

    
    if (type === 'success') {
        toastComponent.style.background = 'linear-gradient(135deg, #10b981, #34d399)';
        toastComponent.style.boxShadow = '0 0 20px rgba(16,185,129,0.4)';
    } else if (type === 'error') {
        toastComponent.style.background = 'linear-gradient(135deg, #ef4444, #f87171)';
        toastComponent.style.boxShadow = '0 0 20px rgba(239,68,68,0.4)';
    } else {
        toastComponent.style.background = 'linear-gradient(135deg, #475569, #64748b)';
        toastComponent.style.boxShadow = '0 0 20px rgba(71,85,105,0.4)';
    }

  
    toastTitle.style.fontWeight = '700';
    toastTitle.style.fontSize = '1rem';
    toastTitle.style.marginBottom = '4px';
    toastMessage.style.fontWeight = '400';
    toastMessage.style.fontSize = '0.875rem';
    toastMessage.style.opacity = '0.9';

    toastTitle.textContent = title;
    toastMessage.textContent = message;

    
    requestAnimationFrame(() => {
        toastComponent.style.transform = 'translateY(0)';
        toastComponent.style.opacity = '1';
    });

    
    setTimeout(() => {
        toastComponent.style.transform = 'translateY(80px)';
        toastComponent.style.opacity = '0';
    }, duration);
}

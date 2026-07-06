// Initializes SweetAlert2 helper if needed

if (typeof Swal !== 'undefined') {
  // Optional sanity check (uncomment for debug)
  // Swal.fire("SweetAlert2 is working!");

  function showToast(type, message) {
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: type,
      title: message,
      showConfirmButton: false,
      timer: 4000,
      timerProgressBar: true,
      customClass: { popup: 'colored-toast' }
    });
  }

  function showSuccess(message) { showToast('success', message); }
  function showError(message) { showToast('error', message); }

} else {
  console.warn('SweetAlert2 (Swal) is not loaded. Falling back to alert/toast fallback.');

  function showToast(type, message) {
    // Simple fallback for environments without SweetAlert2
    try {
      if (type === 'error') {
        alert('Error: ' + message);
      } else if (type === 'success') {
        alert('Success: ' + message);
      } else {
        alert(message);
      }
    } catch (e) {
      // silent
    }
  }

  function showSuccess(message) { showToast('success', message); }
  function showError(message) { showToast('error', message); }

}

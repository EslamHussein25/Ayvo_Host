document.addEventListener('DOMContentLoaded', function() {
  const btnUpload = document.getElementById('btn_upload');
  const btnResult = document.getElementById('btn_result');
  const btnCompare = document.getElementById('btn_compare');
  const btnCharts = document.getElementById('btn_charts');
  const btnPython = document.getElementById('btn_python');
  const iframe = document.getElementById('content-iframe');

  // Initial active state
  btnUpload.classList.add('active');

  // Switch to upload page
  btnUpload.addEventListener('click', () => {
    setActiveButton(btnUpload);
    iframe.src = 'upload.html';
  });

  // Switch to result page
  btnResult.addEventListener('click', () => {
    setActiveButton(btnResult);
    iframe.src = 'result.html';
  });

  // Switch to compare page
  btnCompare.addEventListener('click', () => {
    setActiveButton(btnCompare);
    iframe.src = 'compare.html';
  });

  // Switch to charts page
  btnCharts.addEventListener('click', () => {
    setActiveButton(btnCharts);
    iframe.src = 'charts.html';
  });

  // Switch to python runner page
  btnPython.addEventListener('click', () => {
    setActiveButton(btnPython);
    iframe.src = 'python-runner.html';
  });

  // Helper function to set active button
  function setActiveButton(activeBtn) {
    [btnUpload, btnResult, btnCompare, btnCharts, btnPython].forEach(btn => {
      btn.classList.remove('active');
    });
    activeBtn.classList.add('active');
  }

  // Listen for message from upload.html to switch to result
  window.addEventListener('message', (event) => {
    if (event.data === 'navigate-to-result') {
      btnResult.click();
    }
  });
});

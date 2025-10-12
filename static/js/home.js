        let currentHistory = [];
        let currentPage = 1;
        let totalPages = 1;
        let historyLimit = 10;

        // Load conversion history and stats on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadConversionHistory();
            loadUserStats();

            // Add event listeners for FAQ toggles
            document.querySelectorAll('.faq-question').forEach(question => {
                question.addEventListener('click', function() {
                    const toggle = this.querySelector('.faq-toggle');
                    toggle.classList.toggle('rotate');
                });
            });
        });

        // Basic file upload preview functionality
        document.getElementById('documentUpload').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    document.getElementById('originalPreview').src = event.target.result;
                    document.getElementById('uploadArea').classList.add('d-none');
                    document.getElementById('previewSection').classList.remove('d-none');
                    
                    // Add animation class
                    document.getElementById('previewSection').classList.add('fade-in');
                    
                    // Reset result area
                    document.getElementById('textOutput').classList.remove('d-none');
                    document.getElementById('resultPreview').classList.add('d-none');
                    document.getElementById('downloadResultBtn').classList.add('d-none');
                    document.getElementById('textOutput').innerHTML = '<p class="text-muted mb-0">Digitized content will appear here...</p>';
                }
                reader.readAsDataURL(file);
            }
        });

        document.getElementById('cancelBtn').addEventListener('click', function() {
            document.getElementById('documentUpload').value = '';
            document.getElementById('uploadArea').classList.remove('d-none');
            document.getElementById('previewSection').classList.add('d-none');
            
            // Reset result area
            document.getElementById('textOutput').classList.remove('d-none');
            document.getElementById('resultPreview').classList.add('d-none');
            document.getElementById('downloadResultBtn').classList.add('d-none');
            document.getElementById('textOutput').innerHTML = '<p class="text-muted mb-0">Digitized content will appear here...</p>';
        });

        // Convert button functionality
        document.getElementById('convertBtn').addEventListener('click', async function() {
            const convertBtn = document.getElementById('convertBtn');
            const originalText = convertBtn.innerHTML;
            const fileInput = document.getElementById('documentUpload');
            const file = fileInput.files[0];
            const selectedModelElement = document.querySelector('.model-dropdown-item.selected');
            const selectedModel = selectedModelElement ? selectedModelElement.dataset.model : null;
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');

            // Validate file selection
            if (!file) {
                showAlert('Please select a file first', 'warning');
                return;
            }

            // Validate model selection
            // Check if a model is actually selected (not just the default placeholder)
            const selectedModelText = document.getElementById('selectedModel').textContent.trim();
            if (!selectedModel || selectedModelText === 'Select model') {
                showAlert('Please select an AI model before converting', 'warning');
                return;
            }

            // Show progress bar
            progressContainer.classList.remove('d-none');
            progressBar.style.width = '0%';

            // Update button text based on selected model
            const modelName = selectedModelElement ? selectedModelElement.textContent.trim() : 'AI Model';
            convertBtn.disabled = true;
            convertBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing with ${modelName}...`;

            try {
                // Simulate progress
                simulateProgress(progressBar);

                // Create FormData and append the file
                const formData = new FormData();
                formData.append('image', file);
                formData.append('model', selectedModel);

                // Make API call
                const response = await fetch('/convert', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }

                const result = await response.json();

                if (result.success) {
                    // Display the result
                    document.getElementById('textOutput').classList.add('d-none');
                    document.getElementById('resultPreview').classList.remove('d-none');
                    document.getElementById('resultPreview').src = `data:image/png;base64,${result.digitized_image}`;

                    // Show the download button for result
                    document.getElementById('downloadResultBtn').classList.remove('d-none');

                    // Store the result data for download
                    document.getElementById('downloadResultBtn').dataset.filename = result.filename;
                    document.getElementById('downloadResultBtn').dataset.imageData = result.digitized_image;

                    showAlert(`Document successfully digitized using ${result.model_used || modelName}!`, 'success');
                    
                    // Refresh history and stats after successful conversion
                    setTimeout(() => {
                        loadConversionHistory(1); // Always go to page 1 to show the latest conversion
                        loadUserStats(); // Refresh stats
                    }, 1000);
                } else {
                    // Handle timeout errors specifically
                    if (result.message && (result.message.includes('timeout') || result.message.includes('504'))) {
                        showAlert(result.message, 'warning');
                    } else {
                        showAlert(result.message || 'Conversion failed', 'danger');
                    }
                }

            } catch (error) {
                console.error('Conversion error:', error);
                // Handle timeout errors specifically
                if (error.message && (error.message.includes('timeout') || error.message.includes('504'))) {
                    showAlert(`Request timeout with ${modelName}. This model may be taking longer than expected. Try using a faster model like 'gemini-2.5-flash' for quicker results.`, 'warning');
                } else {
                    showAlert('Conversion failed. Please try again.', 'danger');
                }
            } finally {
                convertBtn.disabled = false;
                convertBtn.innerHTML = originalText;
                
                // Hide progress bar
                setTimeout(() => {
                    progressContainer.classList.add('d-none');
                    progressBar.style.width = '0%';
                }, 500);
            }
        });

        // Simulate progress for better UX
        function simulateProgress(progressBar) {
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 10;
                if (progress >= 90) {
                    progress = 90;
                    clearInterval(interval);
                }
                progressBar.style.width = `${progress}%`;
            }, 200);
        }

        // Load conversion history with pagination
        async function loadConversionHistory(page = 1) {
            const historyContainer = document.getElementById('historyContainer');
            
            try {
                const response = await fetch(`/history?page=${page}&limit=${historyLimit}`);
                const data = await response.json();

                if (data.success) {
                    currentHistory = data.history;
                    currentPage = data.page;
                    totalPages = data.total_pages;
                    
                    if (data.history.length > 0) {
                        renderHistoryItems(data.history);
                        renderPagination(data);
                    } else {
                        historyContainer.innerHTML = `
                            <div class="text-center py-4">
                                <i class="bi bi-clock-history" style="font-size: 2rem; color: #ccc;"></i>
                                <p class="mt-2 text-muted">No conversion history found</p>
                                <small class="text-muted">Your digitized documents will appear here</small>
                            </div>
                        `;
                        hidePagination();
                    }
                } else {
                    historyContainer.innerHTML = `
                        <div class="text-center py-4">
                            <i class="bi bi-clock-history" style="font-size: 2rem; color: #ccc;"></i>
                            <p class="mt-2 text-muted">No conversion history found</p>
                            <small class="text-muted">Your digitized documents will appear here</small>
                        </div>
                    `;
                    hidePagination();
                }
            } catch (error) {
                console.error('Error loading history:', error);
                historyContainer.innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                        <p class="mt-2 text-muted">Failed to load conversion history</p>
                        <button class="btn btn-sm btn-outline-primary" onclick="loadConversionHistory(${currentPage})">
                            <i class="bi bi-arrow-clockwise me-1"></i>Try Again
                        </button>
                    </div>
                `;
                hidePagination();
            }
        }

        // Load user statistics
        async function loadUserStats() {
            try {
                const response = await fetch(`/history?page=1&limit=100`); // Get more items to calculate stats
                const data = await response.json();

                if (data.success) {
                    const history = data.history;
                    const total = history.length;
                    const successful = history.filter(item => item.success).length;
                    
                    // Calculate this month's conversions
                    const now = new Date();
                    const thisMonth = history.filter(item => {
                        const itemDate = new Date(item.created_at);
                        return itemDate.getMonth() === now.getMonth() && 
                               itemDate.getFullYear() === now.getFullYear();
                    }).length;

                    // Update stats
                    document.getElementById('totalConversions').textContent = total;
                    document.getElementById('successfulConversions').textContent = successful;
                    document.getElementById('thisMonthConversions').textContent = thisMonth;
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        // Render history items
        function renderHistoryItems(history) {
            const historyContainer = document.getElementById('historyContainer');
            
            const historyHTML = history.map(item => {
                const statusBadge = item.success ? 
                    '<span class="badge badge-success">Completed</span>' :
                    '<span class="badge badge-danger">Failed</span>';
                
                const createdDate = new Date(item.created_at).toLocaleDateString();
                const processingTime = parseFloat(item.processing_time).toFixed(2);

                return `
                    <div class="history-item fade-in">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6 class="mb-1">${item.filename}</h6>
                                <small class="text-muted">
                                    Converted on ${createdDate} | ${item.model_used} | ${processingTime}s
                                </small>
                            </div>
                            <div>
                                ${statusBadge}
                                <button class="btn btn-sm btn-outline-primary ms-2" 
                                        onclick="showHistoryDetails('${item.id || item._id}')">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            historyContainer.innerHTML = historyHTML;
        }

        // Render pagination controls
        function renderPagination(data) {
            const paginationContainer = document.getElementById('paginationContainer');
            const pagination = document.getElementById('historyPagination');
            
            if (data.total_pages <= 1) {
                hidePagination();
                return;
            }
            
            let paginationHTML = '';
            
            // Previous button
            if (data.has_prev) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="loadConversionHistory(${data.page - 1})" aria-label="Previous">
                            <span aria-hidden="true">&laquo;</span>
                        </a>
                    </li>
                `;
            } else {
                paginationHTML += `
                    <li class="page-item disabled">
                        <span class="page-link" aria-label="Previous">
                            <span aria-hidden="true">&laquo;</span>
                        </span>
                    </li>
                `;
            }
            
            // Page numbers
            const startPage = Math.max(1, data.page - 2);
            const endPage = Math.min(data.total_pages, data.page + 2);
            
            // First page if not in range
            if (startPage > 1) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="loadConversionHistory(1)">1</a>
                    </li>
                `;
                if (startPage > 2) {
                    paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
                }
            }
            
            // Current range of pages
            for (let i = startPage; i <= endPage; i++) {
                if (i === data.page) {
                    paginationHTML += `
                        <li class="page-item active">
                            <span class="page-link">${i}</span>
                        </li>
                    `;
                } else {
                    paginationHTML += `
                        <li class="page-item">
                            <a class="page-link" href="#" onclick="loadConversionHistory(${i})">${i}</a>
                        </li>
                    `;
                }
            }
            
            // Last page if not in range
            if (endPage < data.total_pages) {
                if (endPage < data.total_pages - 1) {
                    paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
                }
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="loadConversionHistory(${data.total_pages})">${data.total_pages}</a>
                    </li>
                `;
            }
            
            // Next button
            if (data.has_next) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="loadConversionHistory(${data.page + 1})" aria-label="Next">
                            <span aria-hidden="true">&raquo;</span>
                        </a>
                    </li>
                `;
            } else {
                paginationHTML += `
                    <li class="page-item disabled">
                        <span class="page-link" aria-label="Next">
                            <span aria-hidden="true">&raquo;</span>
                        </span>
                    </li>
                `;
            }
            
            pagination.innerHTML = paginationHTML;
            paginationContainer.classList.remove('d-none');
        }
        
        // Hide pagination
        function hidePagination() {
            document.getElementById('paginationContainer').classList.add('d-none');
        }

        // Show history details in modal
        async function showHistoryDetails(conversionId) {
            try {
                const response = await fetch(`/history/${conversionId}`);
                const data = await response.json();

                if (data.success && data.details) {
                    const details = data.details;
                    
                    document.getElementById('modalFilename').textContent = details.filename;
                    document.getElementById('modalDate').textContent = new Date(details.created_at).toLocaleString();
                    document.getElementById('modalModel').textContent = details.model_used;
                    document.getElementById('modalProcessingTime').textContent = `${parseFloat(details.processing_time).toFixed(2)} seconds`;
                    
                    const statusHtml = details.success ? 
                        '<span class="badge badge-success">Completed</span>' :
                        '<span class="badge badge-danger">Failed</span>';
                    document.getElementById('modalStatus').innerHTML = statusHtml;
                    
                    document.getElementById('modalExtractedText').innerHTML = 
                        details.extracted_text ? 
                        `<pre style="white-space: pre-wrap; font-family: inherit;">${details.extracted_text}</pre>` :
                        '<p class="text-muted mb-0">No extracted text available</p>';

                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
                    modal.show();
                } else {
                    showAlert('Failed to load conversion details', 'danger');
                }
            } catch (error) {
                console.error('Error loading details:', error);
                showAlert('Failed to load conversion details', 'danger');
            }
        }

        // Refresh history button
        document.getElementById('refreshHistoryBtn').addEventListener('click', function() {
            const btn = this;
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Loading...';
            btn.disabled = true;

            loadConversionHistory(currentPage).finally(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            });
        });

        // Download functionality
        document.getElementById('downloadOriginalBtn').addEventListener('click', function() {
            const file = document.getElementById('documentUpload').files[0];
            if (file) {
                const url = URL.createObjectURL(file);
                const a = document.createElement('a');
                a.href = url;
                a.download = file.name || 'document';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        });

        document.getElementById('downloadResultBtn').addEventListener('click', function() {
            const btn = this;
            const filename = btn.dataset.filename || 'digitized_document.png';
            const imageData = btn.dataset.imageData;

            if (imageData) {
                const link = document.createElement('a');
                link.href = `data:image/png;base64,${imageData}`;
                link.download = filename.replace(/\.[^/.]+$/, "") + "_digitized.png";
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        });

        // Drag and drop functionality
        const uploadArea = document.getElementById('uploadArea');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            uploadArea.classList.add('drag-over');
        }

        function unhighlight(e) {
            uploadArea.classList.remove('drag-over');
        }

        uploadArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            document.getElementById('documentUpload').files = files;

            // Trigger the change event
            const event = new Event('change');
            document.getElementById('documentUpload').dispatchEvent(event);
        }

        // Utility function to show alerts
        function showAlert(message, type = 'info') {
            // Remove existing alerts
            const existingAlerts = document.querySelectorAll('.alert-temporary');
            existingAlerts.forEach(alert => alert.remove());

            // Create new alert
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-temporary`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;

            // Insert at the top of main content
            const mainContent = document.querySelector('.col-lg-10');
            mainContent.insertBefore(alertDiv, mainContent.firstChild);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
        
        // Add pulse animation to upload area when page loads
        window.addEventListener('load', function() {
            setTimeout(() => {
                document.getElementById('uploadArea').classList.add('pulse');
                setTimeout(() => {
                    document.getElementById('uploadArea').classList.remove('pulse');
                }, 2000);
            }, 1000);
        });
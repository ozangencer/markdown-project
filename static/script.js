document.addEventListener("DOMContentLoaded", () => {
    // Tab switching elements
    const fileTabButton = document.getElementById("fileTabButton");
    const youtubeTabButton = document.getElementById("youtubeTabButton");
    const fileTab = document.getElementById("fileTab");
    const youtubeTab = document.getElementById("youtubeTab");

    // File upload elements
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("fileInput");
    const uploadForm = document.getElementById("uploadForm");
    const markdownContent = document.getElementById("markdownContent");
    const downloadButton = document.getElementById("downloadButton");
    const downloadSection = document.getElementById("downloadSection");
    const filenameInput = document.getElementById("filenameInput");
    const filePreview = document.getElementById("filePreview");
    const clearButton = document.getElementById("clearButton");
    
    // Store selected files
    let selectedFiles = [];

    // YouTube elements
    const youtubeForm = document.getElementById("youtubeForm");
    const youtubeUrlsList = document.getElementById("youtubeUrlsList");
    const addYoutubeUrlButton = document.getElementById("addYoutubeUrl");
    const clearYoutubeButton = document.getElementById("clearYoutubeButton");
    const summarizeYoutubeButton = document.getElementById("summarizeYoutubeButton");
    
    // AI Provider elements
    const aiProviderSelect = document.getElementById("aiProviderSelect");
    const setProviderButton = document.getElementById("setProviderButton");
    const providerStatus = document.getElementById("providerStatus");
    
    // Store YouTube transcripts and current markdown content
    let youtubeTranscripts = [];
    let currentMarkdownContent = "";
    let currentDownloadUrl = "";

    // Tab switching functionality
    fileTabButton.addEventListener("click", () => {
        fileTabButton.classList.add("active");
        youtubeTabButton.classList.remove("active");
        fileTab.style.display = "block";
        youtubeTab.style.display = "none";
    });

    youtubeTabButton.addEventListener("click", () => {
        youtubeTabButton.classList.add("active");
        fileTabButton.classList.remove("active");
        youtubeTab.style.display = "block";
        fileTab.style.display = "none";
    });

    // Dosya türü ile ikon eşleştirmeleri
    const fileIcons = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel.png',
        'application/vnd.ms-excel': 'excel.png',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'word.png',
        'application/msword': 'word.png',
        'application/pdf': 'pdf.png',
        'image/png': 'image.png',
        'image/jpeg': 'image.png',
        'image/gif': 'image.png',
        'default': 'default.png'
    };

    // MIME türü veya dosya uzantısına göre ikon seçimi
    const getFileIcon = (type, name) => {
        if (fileIcons[type]) {
            return `/static/icons/${fileIcons[type]}`;
        }

        // MIME türü boşsa veya bulunamazsa dosya uzantısına göre kontrol yap
        const extension = name.split('.').pop().toLowerCase();
        const extensionIcons = {
            'xlsx': 'excel.png',
            'xls': 'excel.png',
            'docx': 'word.png',
            'doc': 'word.png',
            'pdf': 'pdf.png',
            'png': 'image.png',
            'jpg': 'image.png',
            'jpeg': 'image.png',
            'gif': 'image.png'
        };

        return `/static/icons/${extensionIcons[extension] || fileIcons['default']}`;
    };

    // Sürükle-bırak alanına tıklama ile dosya seçimi açılır
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    // Sürükleme alanında hover durumunda çerçeve rengi değişir
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#8585ff";
    });

    // Sürükleme alanından çıkıldığında çerçeve rengi varsayılan haline döner
    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "#646cff";
    });

    // Dosya sürükleyip bırakıldığında işleme alınır
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#646cff";

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            displaySelectedFiles(files);
        }
    });

    // Dosya manuel olarak seçildiğinde işleme alınır
    fileInput.addEventListener("change", () => {
        const files = fileInput.files;
        if (files.length > 0) {
            displaySelectedFiles(files);
        }
    });
    
    // Display selected files with preview
    function displaySelectedFiles(files) {
        selectedFiles = Array.from(files);
        filePreview.innerHTML = '';
        filePreview.style.display = 'block';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.innerHTML = `
                <div class="file-info">
                    <img class="file-icon" src="${getFileIcon(file.type, file.name)}" alt="File Icon">
                    <span class="file-name">${file.name}</span>
                </div>
                <button type="button" class="remove-file-btn" data-index="${index}">Remove</button>
            `;
            filePreview.appendChild(fileItem);
        });
        
        // Add remove file event listeners
        document.querySelectorAll('.remove-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                selectedFiles.splice(index, 1);
                updateFileInput();
                displaySelectedFiles(selectedFiles);
            });
        });
    }
    
    // Update file input with remaining files
    function updateFileInput() {
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        
        if (selectedFiles.length === 0) {
            filePreview.style.display = 'none';
        }
    }

    // Loading overlay element
    const loadingOverlay = document.getElementById("loadingOverlay");

    // Form butonları
    const convertButton = document.getElementById("convertButton");
    const convertYoutubeButton = document.getElementById("convertYoutubeButton");


    // Yükleme durumunu göster/gizle
    const showLoading = () => {
        loadingOverlay.style.display = "flex";
        // Butonları devre dışı bırak
        convertButton.disabled = true;
        convertYoutubeButton.disabled = true;
        summarizeYoutubeButton.disabled = true;
        clearButton.disabled = true;
        clearYoutubeButton.disabled = true;
    };

    const hideLoading = () => {
        loadingOverlay.style.display = "none";
        // Butonları tekrar aktif et
        convertButton.disabled = false;
        convertYoutubeButton.disabled = false;
        summarizeYoutubeButton.disabled = false;
        clearButton.disabled = false;
        clearYoutubeButton.disabled = false;
    };

    // Dosya dönüşümü için form gönderimi
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Yükleme durumunu göster
        showLoading();

        try {
            const formData = new FormData(uploadForm);
            const response = await fetch("/convert", {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                currentMarkdownContent = result.markdown;
                currentDownloadUrl = result.download_url;
                markdownContent.textContent = result.markdown;
                downloadSection.style.display = "block";
                filenameInput.value = "";
            } else {
                const error = await response.json();
                markdownContent.textContent = `Error: ${error.error}`;
            }
        } catch (error) {
            markdownContent.textContent = `Error: ${error.message}`;
        } finally {
            // İşlem bittiğinde yükleme durumunu gizle
            hideLoading();
        }
    });

    // YouTube video dönüşümü
    youtubeForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Get all YouTube URLs
        const urlInputs = youtubeUrlsList.querySelectorAll('input[name="youtubeUrl"]');
        const urls = Array.from(urlInputs)
            .map(input => input.value.trim())
            .filter(url => url !== '');

        if (urls.length === 0) {
            alert('Please enter at least one YouTube URL');
            return;
        }

        // Yükleme durumunu göster
        showLoading();

        // Reset transcripts
        youtubeTranscripts = [];
        summarizeYoutubeButton.disabled = true;

        try {
            const response = await fetch("/convert-youtube-multiple", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ urls }),
            });

            if (response.ok) {
                const result = await response.json();
                youtubeTranscripts = result.transcripts || [];
                currentMarkdownContent = result.markdown;
                currentDownloadUrl = result.download_url;
                markdownContent.textContent = result.markdown;
                downloadSection.style.display = "block";
                filenameInput.value = "";

                // Enable summarize button if we have transcripts
                if (youtubeTranscripts.length > 0) {
                    summarizeYoutubeButton.disabled = false;
                }
            } else {
                const error = await response.json();
                markdownContent.textContent = `Error: ${error.error}`;
                summarizeYoutubeButton.disabled = true;
            }
        } catch (error) {
            markdownContent.textContent = `Error: ${error.message}`;
            summarizeYoutubeButton.disabled = true;
        } finally {
            // İşlem bittiğinde yükleme durumunu gizle
            hideLoading();
        }
    });

    // Clear butonu ile önizleme ve diğer içerikler temizlenir
    clearButton.addEventListener("click", () => {
        fileInput.value = "";
        selectedFiles = [];
        filePreview.innerHTML = "";
        filePreview.style.display = "none";
        markdownContent.textContent = "";
        downloadSection.style.display = "none";
        filenameInput.value = "";
        currentMarkdownContent = "";
        currentDownloadUrl = "";
    });

    // YouTube form clear butonu
    clearYoutubeButton.addEventListener("click", () => {
        // Reset to single input
        youtubeUrlsList.innerHTML = `
            <div class="youtube-url-input">
                <input type="url" name="youtubeUrl" placeholder="Enter YouTube URL" required>
                <button type="button" class="remove-url-btn" style="display: none;">Remove</button>
            </div>
        `;
        markdownContent.textContent = "";
        downloadSection.style.display = "none";
        filenameInput.value = "";
        youtubeTranscripts = [];
        summarizeYoutubeButton.disabled = true;
        currentMarkdownContent = "";
        currentDownloadUrl = "";
    });

    // Add another YouTube URL input
    addYoutubeUrlButton.addEventListener("click", () => {
        const newUrlInput = document.createElement('div');
        newUrlInput.className = 'youtube-url-input';
        newUrlInput.innerHTML = `
            <input type="url" name="youtubeUrl" placeholder="Enter YouTube URL" required>
            <button type="button" class="remove-url-btn">Remove</button>
        `;
        
        youtubeUrlsList.appendChild(newUrlInput);
        
        // Update remove buttons visibility
        updateRemoveButtonsVisibility();
        
        // Add event listener to new remove button
        const removeBtn = newUrlInput.querySelector('.remove-url-btn');
        removeBtn.addEventListener('click', () => {
            newUrlInput.remove();
            updateRemoveButtonsVisibility();
        });
    });
    
    // Update visibility of remove buttons
    function updateRemoveButtonsVisibility() {
        const urlInputs = youtubeUrlsList.querySelectorAll('.youtube-url-input');
        urlInputs.forEach((input) => {
            const removeBtn = input.querySelector('.remove-url-btn');
            if (urlInputs.length > 1) {
                removeBtn.style.display = 'block';
            } else {
                removeBtn.style.display = 'none';
            }
        });
    }

    // Summarize butonu ile AI özeti alma
    summarizeYoutubeButton.addEventListener("click", async () => {
        // Check if we have transcripts
        if (!youtubeTranscripts || youtubeTranscripts.length === 0) {
            alert("Please convert YouTube videos first to get transcripts.");
            return;
        }

        // Yükleme durumunu göster
        showLoading();

        try {
            const response = await fetch("/summarize-youtube-multiple", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    transcripts: youtubeTranscripts
                }),
            });

            if (response.ok) {
                const result = await response.json();
                currentMarkdownContent = result.markdown;
                currentDownloadUrl = result.download_url;
                markdownContent.textContent = result.markdown;
                downloadSection.style.display = "block";
                filenameInput.value = "";
            } else {
                const error = await response.json();
                markdownContent.textContent = `Error: ${error.error}`;
            }
        } catch (error) {
            markdownContent.textContent = `Error: ${error.message}`;
        } finally {
            // İşlem bittiğinde yükleme durumunu gizle
            hideLoading();
        }
    });

    // Download butonu için tıklama eventi
    downloadButton.addEventListener("click", async (e) => {
        e.preventDefault();
        
        const customFilename = filenameInput.value.trim();
        
        if (customFilename && currentDownloadUrl && currentMarkdownContent) {
            // Custom filename ile yeni dosya oluştur
            try {
                const response = await fetch("/download-custom", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        content: currentMarkdownContent,
                        filename: customFilename
                    }),
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = customFilename.endsWith('.md') ? customFilename : customFilename + '.md';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    const error = await response.json();
                    alert(`Error: ${error.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        } else if (currentDownloadUrl) {
            // Original dosya adıyla indir
            window.location.href = currentDownloadUrl;
        } else {
            alert("No file available for download.");
        }
    });

    // AI Provider functionality
    async function loadAIProviders() {
        try {
            const response = await fetch("/ai-providers");
            if (response.ok) {
                const data = await response.json();
                
                // Update select options
                Object.keys(data.providers).forEach(provider => {
                    const option = aiProviderSelect.querySelector(`option[value="${provider}"]`);
                    if (option) {
                        const status = data.providers[provider] ? "✓" : "✗";
                        option.textContent = option.textContent.split(" (")[0] + " (" + status + ")";
                    }
                });
                
                // Set current provider
                aiProviderSelect.value = data.current;
                updateProviderStatus(data.current, data.providers[data.current]);
            }
        } catch (error) {
            console.error("Error loading AI providers:", error);
        }
    }

    function updateProviderStatus(provider, isAvailable) {
        providerStatus.className = "provider-status";
        if (isAvailable) {
            providerStatus.classList.add("success");
            providerStatus.textContent = `${provider.toUpperCase()} Ready`;
        } else {
            providerStatus.classList.add("error");
            providerStatus.textContent = `${provider.toUpperCase()} Not Configured`;
        }
    }

    // Auto-set provider on dropdown change
    aiProviderSelect.addEventListener("change", async () => {
        const selectedProvider = aiProviderSelect.value;
        await setProvider(selectedProvider);
    });

    // Set AI Provider (both button click and dropdown change use this)
    async function setProvider(selectedProvider) {
        providerStatus.className = "provider-status loading";
        providerStatus.textContent = "Setting provider...";
        
        try {
            const response = await fetch("/ai-providers", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ provider: selectedProvider }),
            });

            if (response.ok) {
                const result = await response.json();
                updateProviderStatus(selectedProvider, true);
            } else {
                const error = await response.json();
                providerStatus.className = "provider-status error";
                providerStatus.textContent = `Error: ${error.error}`;
            }
        } catch (error) {
            providerStatus.className = "provider-status error";
            providerStatus.textContent = `Error: ${error.message}`;
        }
    }

    // Set AI Provider button (keep for manual refresh if needed)
    setProviderButton.addEventListener("click", async () => {
        const selectedProvider = aiProviderSelect.value;
        await setProvider(selectedProvider);
    });

    // Load AI providers on page load
    loadAIProviders();
});
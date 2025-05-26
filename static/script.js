// Klasör içeriğini recursively okuma fonksiyonu
async function readDirectoryRecursively(directoryEntry) {
    const files = [];
    
    return new Promise((resolve, reject) => {
        const directoryReader = directoryEntry.createReader();
        
        function readEntries() {
            directoryReader.readEntries(async (entries) => {
                if (entries.length === 0) {
                    resolve(files);
                    return;
                }
                
                for (const entry of entries) {
                    if (entry.isFile) {
                        try {
                            const file = await new Promise((resolveFile) => {
                                entry.file(resolveFile);
                            });
                            // Klasör yolu bilgisini dosya adına ekle
                            const relativePath = entry.fullPath.substring(1); // Remove leading slash
                            const newFile = new File([file], relativePath, { type: file.type });
                            files.push(newFile);
                        } catch (error) {
                            console.warn(`Could not read file: ${entry.name}`, error);
                        }
                    } else if (entry.isDirectory) {
                        try {
                            const subFiles = await readDirectoryRecursively(entry);
                            files.push(...subFiles);
                        } catch (error) {
                            console.warn(`Could not read directory: ${entry.name}`, error);
                        }
                    }
                }
                
                // Continue reading more entries if they exist
                readEntries();
            }, reject);
        }
        
        readEntries();
    });
}

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
    
    // Clipboard paste counter for naming pasted images
    let pasteCounter = 0;

    // YouTube elements
    const youtubeForm = document.getElementById("youtubeForm");
    const youtubeUrlsList = document.getElementById("youtubeUrlsList");
    const addYoutubeUrlButton = document.getElementById("addYoutubeUrl");
    const clearYoutubeButton = document.getElementById("clearYoutubeButton");
    const summarizeYoutubeButton = document.getElementById("summarizeYoutubeButton");
    
    // Restructure elements
    const restructureFileButton = document.getElementById("restructureFileButton");
    const restructureYoutubeButton = document.getElementById("restructureYoutubeButton");
    const promptModal = document.getElementById("promptModal");
    const customPrompt = document.getElementById("customPrompt");
    const executePromptButton = document.getElementById("executePromptButton");
    const cancelPromptButton = document.getElementById("cancelPromptButton");
    
    // AI Provider elements
    const aiProviderSelect = document.getElementById("aiProviderSelect");
    const setProviderButton = document.getElementById("setProviderButton");
    const providerStatus = document.getElementById("providerStatus");
    
    // Store YouTube transcripts and current markdown content
    let youtubeTranscripts = [];
    let currentMarkdownContent = "";
    let currentDownloadUrl = "";
    
    // Store prompt templates
    let promptTemplates = {};

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
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'powerpoint.png',
        'application/vnd.ms-powerpoint': 'powerpoint.png',
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
            'pptx': 'powerpoint.png',
            'ppt': 'powerpoint.png',
            'pdf': 'pdf.png',
            'png': 'image.png',
            'jpg': 'image.png',
            'jpeg': 'image.png',
            'gif': 'image.png',
            'panda': 'panda.png'
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
    dropZone.addEventListener("drop", async (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#646cff";

        const items = e.dataTransfer.items;
        const files = [];
        
        // Modern browser support için DataTransferItem kullan
        if (items) {
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (item.kind === 'file') {
                    const entry = item.webkitGetAsEntry();
                    if (entry) {
                        if (entry.isDirectory) {
                            // Klasör ise, içindeki tüm dosyaları recursively al
                            const folderFiles = await readDirectoryRecursively(entry);
                            files.push(...folderFiles);
                        } else if (entry.isFile) {
                            // Normal dosya ise
                            const file = item.getAsFile();
                            if (file) files.push(file);
                        }
                    }
                }
            }
        }
        
        // Fallback: eski yöntem
        if (files.length === 0) {
            const dtFiles = e.dataTransfer.files;
            if (dtFiles.length > 0) {
                files.push(...Array.from(dtFiles));
            }
        }

        if (files.length > 0) {
            addFilesToSelection(files);
        }
    });

    // Dosya manuel olarak seçildiğinde işleme alınır
    fileInput.addEventListener("change", () => {
        const files = fileInput.files;
        if (files.length > 0) {
            addFilesToSelection(Array.from(files));
            // Clear the input so the same file can be selected again if needed
            fileInput.value = '';
        }
    });
    
    // Add new files to existing selection
    function addFilesToSelection(newFiles) {
        // Add new files to existing selection, avoiding duplicates based on name and size
        newFiles.forEach(newFile => {
            const isDuplicate = selectedFiles.some(existingFile => 
                existingFile.name === newFile.name && existingFile.size === newFile.size
            );
            if (!isDuplicate) {
                selectedFiles.push(newFile);
            }
        });
        
        updateFileInput();
        displaySelectedFiles();
    }
    
    // Display selected files with preview
    function displaySelectedFiles() {
        filePreview.innerHTML = '';
        if (selectedFiles.length === 0) {
            filePreview.style.display = 'none';
            return;
        }
        
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
                displaySelectedFiles();
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
        restructureFileButton.disabled = true;
        restructureYoutubeButton.disabled = true;
        clearButton.disabled = true;
        clearYoutubeButton.disabled = true;
    };

    const hideLoading = () => {
        loadingOverlay.style.display = "none";
        // Butonları tekrar aktif et
        convertButton.disabled = false;
        convertYoutubeButton.disabled = false;
        // Sadece content varsa restructure butonlarını aktif et
        if (currentMarkdownContent) {
            restructureFileButton.disabled = false;
            restructureYoutubeButton.disabled = false;
        }
        // Sadece transcript varsa summarize butonunu aktif et
        if (youtubeTranscripts && youtubeTranscripts.length > 0) {
            summarizeYoutubeButton.disabled = false;
        }
        clearButton.disabled = false;
        clearYoutubeButton.disabled = false;
    };

    // Dosya dönüşümü için form gönderimi
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Check if we have selected files
        if (selectedFiles.length === 0) {
            alert('Please select at least one file to convert.');
            return;
        }

        // Yükleme durumunu göster
        showLoading();

        try {
            // Create FormData and manually add selected files
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });
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
                
                // Enable restructure button for files
                restructureFileButton.disabled = false;
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

                // Enable summarize and restructure buttons if we have transcripts
                if (youtubeTranscripts.length > 0) {
                    summarizeYoutubeButton.disabled = false;
                    restructureYoutubeButton.disabled = false;
                }
            } else {
                const error = await response.json();
                markdownContent.textContent = `Error: ${error.error}`;
                summarizeYoutubeButton.disabled = true;
                restructureYoutubeButton.disabled = true;
            }
        } catch (error) {
            markdownContent.textContent = `Error: ${error.message}`;
            summarizeYoutubeButton.disabled = true;
            restructureYoutubeButton.disabled = true;
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
        restructureFileButton.disabled = true;
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
        restructureYoutubeButton.disabled = true;
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

    // Content cleaning function
    function cleanMarkdownContent(content) {
        if (!content) return content;
        
        // Remove markdown code blocks at start and end
        let cleaned = content.replace(/^```markdown\n/, '').replace(/\n```$/, '');
        
        // Replace HTML comments with simpler markers
        cleaned = cleaned.replace(/<!--\s*/g, '-- Start of Image Content\n');
        cleaned = cleaned.replace(/\s*-->/g, '\n-- End of Image Content');
        
        return cleaned;
    }

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
                        content: cleanMarkdownContent(currentMarkdownContent),
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

    // Load prompt templates from server
    async function loadPromptTemplates() {
        try {
            const response = await fetch("/prompt-templates");
            if (response.ok) {
                const data = await response.json();
                promptTemplates = data.templates;
            }
        } catch (error) {
            console.error("Error loading prompt templates:", error);
        }
    }

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

    // Clipboard paste functionality
    document.addEventListener("paste", (e) => {
        // Only handle paste events when file tab is active
        if (fileTab.style.display === "none") return;
        
        const clipboardItems = e.clipboardData?.items;
        if (!clipboardItems) return;
        
        // Look for image items in clipboard
        for (let i = 0; i < clipboardItems.length; i++) {
            const item = clipboardItems[i];
            
            if (item.type.startsWith('image/')) {
                e.preventDefault(); // Prevent default paste behavior
                
                const blob = item.getAsFile();
                if (blob) {
                    // Create a File object from the blob with a descriptive name
                    pasteCounter++;
                    const timestamp = new Date().toISOString().replace(/[:]/g, '-').split('.')[0];
                    const extension = item.type.split('/')[1] || 'png';
                    const fileName = `pasted-image-${pasteCounter}-${timestamp}.${extension}`;
                    
                    const file = new File([blob], fileName, { type: item.type });
                    
                    // Add to selected files using the same function
                    addFilesToSelection([file]);
                    
                    // Show visual feedback
                    dropZone.style.borderColor = "#4ade80";
                    setTimeout(() => {
                        dropZone.style.borderColor = "#646cff";
                    }, 1000);
                }
                break; // Only handle the first image found
            }
        }
    });
    
    // Add visual hint for paste functionality
    dropZone.addEventListener("mouseenter", () => {
        if (fileTab.style.display !== "none") {
            dropZone.title = "Drop files here, click to select, or paste images from clipboard (Ctrl+V / Cmd+V)";
        }
    });

    // Restructure functionality
    let currentRestructureType = null; // 'file' or 'youtube'
    
    // Show prompt modal for restructuring
    function showPromptModal(type) {
        currentRestructureType = type;
        
        // Check if current content contains .panda files
        const isPandaDocument = currentMarkdownContent && 
                                currentMarkdownContent.includes('.panda');
        
        // Set default prompt based on document type
        if (isPandaDocument) {
            // Use .panda template from loaded templates
            customPrompt.value = promptTemplates['.panda'] || '';
        } else {
            // For other file types, try to detect extension from content
            let detectedExtension = null;
            
            // Try to detect file extension from content patterns
            if (currentMarkdownContent.includes('File 1:') || currentMarkdownContent.includes('## File')) {
                // Look for file extensions in the content
                const extensionPatterns = ['.xlsx', '.docx', '.pdf', '.pptx'];
                for (const ext of extensionPatterns) {
                    if (currentMarkdownContent.includes(ext)) {
                        detectedExtension = ext;
                        break;
                    }
                }
            }
            
            // Use appropriate template or empty
            customPrompt.value = detectedExtension && promptTemplates[detectedExtension] ? 
                               promptTemplates[detectedExtension] : '';
        }
        
        promptModal.style.display = 'flex';
        customPrompt.focus();
    }
    
    // Hide prompt modal
    function hidePromptModal() {
        promptModal.style.display = 'none';
        currentRestructureType = null;
    }
    
    // Restructure File button
    restructureFileButton.addEventListener("click", () => {
        if (!currentMarkdownContent) {
            alert('Please convert some files first.');
            return;
        }
        showPromptModal('file');
    });
    
    // Restructure YouTube button
    restructureYoutubeButton.addEventListener("click", () => {
        if (!currentMarkdownContent) {
            alert('Please convert some YouTube videos first.');
            return;
        }
        showPromptModal('youtube');
    });
    
    // Cancel prompt button
    cancelPromptButton.addEventListener("click", hidePromptModal);
    
    // Close modal when clicking outside
    promptModal.addEventListener("click", (e) => {
        if (e.target === promptModal) {
            hidePromptModal();
        }
    });
    
    // Execute custom prompt
    executePromptButton.addEventListener("click", async () => {
        const prompt = customPrompt.value.trim();
        if (!prompt) {
            alert('Please enter a prompt.');
            return;
        }
        
        if (!currentMarkdownContent) {
            alert('No content available for restructuring.');
            return;
        }
        
        hidePromptModal();
        showLoading();
        
        try {
            const response = await fetch("/restructure", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    content: currentMarkdownContent,
                    prompt: prompt
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
            hideLoading();
        }
    });

    // Load AI providers and prompt templates on page load
    loadAIProviders();
    loadPromptTemplates();
});
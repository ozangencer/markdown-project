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
    const filePreview = document.getElementById("filePreview");
    const fileIcon = document.getElementById("fileIcon");
    const fileName = document.getElementById("fileName");
    const clearButton = document.getElementById("clearButton");

    // YouTube elements
    const youtubeForm = document.getElementById("youtubeForm");
    const youtubeUrl = document.getElementById("youtubeUrl");
    const clearYoutubeButton = document.getElementById("clearYoutubeButton");
    const summarizeYoutubeButton = document.getElementById("summarizeYoutubeButton");

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

        const file = e.dataTransfer.files[0];
        if (file) {
            fileInput.files = e.dataTransfer.files;

            // Önizleme için dosya ikonu ve adı ayarlanır
            fileIcon.src = getFileIcon(file.type, file.name);
            fileName.textContent = file.name;
            filePreview.style.display = "flex";
        }
    });

    // Dosya manuel olarak seçildiğinde işleme alınır
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) {
            // Önizleme için dosya ikonu ve adı ayarlanır
            fileIcon.src = getFileIcon(file.type, file.name);
            fileName.textContent = file.name;
            filePreview.style.display = "flex";
        }
    });

    // Loading overlay element
    const loadingOverlay = document.getElementById("loadingOverlay");

    // Form butonları
    const convertButton = document.getElementById("convertButton");
    const convertYoutubeButton = document.getElementById("convertYoutubeButton");

    // Current transcript content
    let currentTranscript = "";

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
                markdownContent.textContent = result.markdown;
                downloadButton.href = result.download_url;
                downloadButton.style.display = "block";
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

        const url = youtubeUrl.value.trim();
        if (!url) return;

        // Yükleme durumunu göster
        showLoading();

        // Başlangıçta özetleme butonunu devre dışı bırak
        summarizeYoutubeButton.disabled = true;
        currentTranscript = "";

        try {
            const response = await fetch("/convert-youtube", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ url }),
            });

            if (response.ok) {
                const result = await response.json();
                currentTranscript = result.markdown; // Transcript'i kaydet
                markdownContent.textContent = result.markdown;
                downloadButton.href = result.download_url;
                downloadButton.style.display = "block";

                // Transcript alındıysa özetleme butonunu aktifleştir
                summarizeYoutubeButton.disabled = false;
            } else {
                const error = await response.json();
                markdownContent.textContent = `Error: ${error.error}`;

                // Hata durumunda özetleme butonunu devre dışı bırak
                summarizeYoutubeButton.disabled = true;
                currentTranscript = "";
            }
        } catch (error) {
            markdownContent.textContent = `Error: ${error.message}`;

            // Hata durumunda özetleme butonunu devre dışı bırak
            summarizeYoutubeButton.disabled = true;
            currentTranscript = "";
        } finally {
            // İşlem bittiğinde yükleme durumunu gizle
            hideLoading();
        }
    });

    // Clear butonu ile önizleme ve diğer içerikler temizlenir
    clearButton.addEventListener("click", () => {
        fileInput.value = "";
        filePreview.style.display = "none";
        markdownContent.textContent = "";
        downloadButton.style.display = "none";
    });

    // YouTube form clear butonu
    clearYoutubeButton.addEventListener("click", () => {
        youtubeUrl.value = "";
        markdownContent.textContent = "";
        downloadButton.style.display = "none";
        currentTranscript = "";
        summarizeYoutubeButton.disabled = true;
    });

    // Summarize butonu ile AI özeti alma
    summarizeYoutubeButton.addEventListener("click", async () => {
        // Eğer transcript yoksa işlem yapma
        if (!currentTranscript) {
            alert("Please convert a YouTube video first to get a transcript.");
            return;
        }

        const url = youtubeUrl.value.trim();
        if (!url) {
            alert("Please enter a valid YouTube URL.");
            return;
        }

        // Yükleme durumunu göster
        showLoading();

        try {
            const response = await fetch("/summarize-youtube", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    url: url,
                    transcript: currentTranscript
                }),
            });

            if (response.ok) {
                const result = await response.json();
                markdownContent.textContent = result.markdown;
                downloadButton.href = result.download_url;
                downloadButton.style.display = "block";
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
});
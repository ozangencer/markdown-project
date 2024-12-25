document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("fileInput");
    const uploadForm = document.getElementById("uploadForm");
    const markdownContent = document.getElementById("markdownContent");
    const downloadButton = document.getElementById("downloadButton");
    const filePreview = document.getElementById("filePreview");
    const fileIcon = document.getElementById("fileIcon");
    const fileName = document.getElementById("fileName");
    const clearButton = document.getElementById("clearButton");

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

    // Dosya dönüşümü için form gönderimi
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

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
    });

    // Clear butonu ile önizleme ve diğer içerikler temizlenir
    clearButton.addEventListener("click", () => {
        fileInput.value = "";
        filePreview.style.display = "none";
        markdownContent.textContent = "";
        downloadButton.style.display = "none";
    });
});
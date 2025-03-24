// Словарь оптимальных OCR-движков для каждого языка
const OPTIMAL_OCR_ENGINES = {
    'ja': { engine: 'mangaocr', name: 'MangaOCR', description: 'используется для японского' },
    'zh': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для китайского' },
    'ko': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для корейского' },
    'en': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для английского' },
    'ru': { engine: 'easyocr', name: 'EasyOCR', description: 'используется для русского' },
    'fr': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для французского' },
    'es': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для испанского' },
    'de': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для немецкого' }
};

// Функция для обновления информации о выбранном OCR-движке
function updateOcrEngineInfo() {
    const sourceLangSelect = document.getElementById('source_language');
    if (!sourceLangSelect) return;
    
    const selectedLang = sourceLangSelect.value;
    const langName = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
    
    // Обновляем скрытые поля форм с правильным OCR движком
    const engineInfo = OPTIMAL_OCR_ENGINES[selectedLang] || OPTIMAL_OCR_ENGINES['zh'];
    
    if (document.getElementById('ocr_engine_individual')) {
        document.getElementById('ocr_engine_individual').value = engineInfo.engine;
    }
    
    if (document.getElementById('ocr_engine_folders')) {
        document.getElementById('ocr_engine_folders').value = engineInfo.engine;
    }
    
    // Обновляем информационный текст на странице
    const languageNameEl = document.getElementById('language-name');
    const engineNameEl = document.getElementById('engine-name');
    
    if (languageNameEl) {
        languageNameEl.textContent = langName.toLowerCase();
    }
    
    if (engineNameEl) {
        engineNameEl.textContent = engineInfo.name;
    }
}

// Toggle API Key Visibility
document.getElementById('toggle-api-key')?.addEventListener('click', function() {
    const apiKeyInput = document.getElementById('openai_api_key');
    const icon = this.querySelector('i');
    
    if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        apiKeyInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
});

// Toggle API Key Field
function toggleApiKeyField() {
    const translationMethod = document.querySelector('input[name="translation_method"]:checked')?.value;
    const apiKeyGroup = document.getElementById('api-key-group');
    
    if (!apiKeyGroup) return;
    
    if (translationMethod === 'openai') {
        apiKeyGroup.style.display = 'block';
    } else {
        apiKeyGroup.style.display = 'none';
    }
}

// Tab Switching
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Deactivate all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab and activate its button
    document.getElementById(tabId)?.classList.add('active');
    document.querySelector(`[data-tab="${tabId}"]`)?.classList.add('active');
}

// Toggle folder content
function toggleFolder(folderId) {
    const content = document.getElementById('folder-content-' + folderId);
    const icon = document.querySelector('.folder-icon-' + folderId);
    
    if (!content || !icon) return;
    
    if (content.style.display === 'block') {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Select all images in a folder
function selectAllImages(folderId) {
    const checkbox = document.getElementById('select-all-' + folderId);
    const folderCheckboxes = document.querySelectorAll('.folder-' + folderId + '-checkbox');
    
    if (!checkbox) return;
    
    folderCheckboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    
    updateSelectedCount(folderId);
}

// Update selected count
function updateSelectedCount(folderId) {
    const folderCheckboxes = document.querySelectorAll('.folder-' + folderId + '-checkbox');
    const selectedCount = document.getElementById('selected-count-' + folderId);
    
    if (!selectedCount) return;
    
    let count = 0;
    folderCheckboxes.forEach(cb => {
        if (cb.checked) count++;
    });
    
    selectedCount.textContent = count;
}

// Toggle details dropdown
function toggleDetails(fileId) {
    const dropdown = document.getElementById('details-dropdown-' + fileId);
    
    if (!dropdown) return;
    
    // Close all other dropdowns
    document.querySelectorAll('.details-dropdown.active').forEach(el => {
        if (el.id !== 'details-dropdown-' + fileId) {
            el.classList.remove('active');
        }
    });
    
    dropdown.classList.toggle('active');
}

// Show dialog
function showDialog(dialogId) {
    // Close all dropdowns
    document.querySelectorAll('.details-dropdown.active').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show dialog
    document.getElementById(dialogId)?.classList.add('active');
    
    // Prevent scrolling of the body
    document.body.style.overflow = 'hidden';
}

// Hide dialog
function hideDialog(dialogId) {
    document.getElementById(dialogId)?.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Navigate reader
function navigateReader(direction) {
    const currentPageEl = document.getElementById('current-page');
    const totalPagesEl = document.getElementById('total-pages');
    const bottomNavCurrentEl = document.getElementById('bottom-nav-current');
    
    if (!currentPageEl || !totalPagesEl) return;
    
    const currentPage = parseInt(currentPageEl.textContent);
    const totalPages = parseInt(totalPagesEl.textContent);
    
    let newPage;
    if (direction === 'prev') {
        newPage = Math.max(1, currentPage - 1);
    } else if (direction === 'next') {
        newPage = Math.min(totalPages, currentPage + 1);
    } else {
        newPage = parseInt(direction);
    }
    
    // Update current page
    currentPageEl.textContent = newPage;
    if (bottomNavCurrentEl) {
        bottomNavCurrentEl.textContent = newPage;
    }
    
    // Hide all images
    document.querySelectorAll('.manga-card').forEach((card, index) => {
        if (index + 1 === newPage) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Update button states
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const bottomPrevButton = document.getElementById('bottom-nav-prev');
    const bottomNextButton = document.getElementById('bottom-nav-next');
    
    if (prevButton) prevButton.disabled = (newPage === 1);
    if (nextButton) nextButton.disabled = (newPage === totalPages);
    if (bottomPrevButton) bottomPrevButton.disabled = (newPage === 1);
    if (bottomNextButton) bottomNextButton.disabled = (newPage === totalPages);
}

// Show spinner
function showSpinner() {
    document.getElementById('spinner-container').style.display = 'flex';
    return true;
}

// Update file count
function updateFileCount() {
    const fileInput = document.getElementById('file-input');
    const fileCount = document.getElementById('file-count');
    const filesPreview = document.getElementById('selected-files-preview');
    const filesGrid = document.getElementById('files-preview-grid');
    
    if (!fileInput || !fileCount || !filesPreview || !filesGrid) return;
    
    if (fileInput.files.length > 0) {
        fileCount.textContent = `Выбрано файлов: ${fileInput.files.length}`;
        
        // Clear previous previews
        filesGrid.innerHTML = '';
        
        // Create preview for each file
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            
            // Create preview item
            const previewItem = document.createElement('div');
            previewItem.className = 'image-item';
            
            // Create preview container
            const previewContainer = document.createElement('div');
            previewContainer.className = 'image-preview';
            
            // Create image element
            const img = document.createElement('img');
            const reader = new FileReader();
            
            reader.onload = function(e) {
                img.src = e.target.result;
            };
            
            reader.readAsDataURL(file);
            previewContainer.appendChild(img);
            
            // Create filename div
            const fileName = document.createElement('div');
            fileName.className = 'image-name';
            fileName.title = file.name;
            fileName.textContent = file.name;
            
            // Add elements to preview item
            previewItem.appendChild(previewContainer);
            previewItem.appendChild(fileName);
            
            // Add preview item to grid
            filesGrid.appendChild(previewItem);
        }
        
        filesPreview.style.display = 'block';
    } else {
        fileCount.textContent = 'Файлы не выбраны';
        filesPreview.style.display = 'none';
    }
}

// Функция для инициализации кнопок скачивания
function initDownloadButtons() {
    // Показываем панель скачивания, если есть результаты
    const resultsContainer = document.querySelector('.results-container');
    const downloadPanel = document.querySelector('.download-options-panel');
    
    if (resultsContainer && downloadPanel) {
        if (resultsContainer.style.display !== 'none') {
            downloadPanel.style.display = 'block';
        }
    }
    
    // Привязываем обработчики к кнопкам скачивания
    document.getElementById('download-pdf')?.addEventListener('click', () => downloadResults('pdf'));
    document.getElementById('download-cbz')?.addEventListener('click', () => downloadResults('cbz'));
    document.getElementById('download-zip')?.addEventListener('click', () => downloadResults('zip'));
}

// Функция скачивания результатов
function downloadResults(format) {
    // Собираем пути ко всем обработанным изображениям
    const imagePaths = [];
    
    console.log("Поиск изображений для скачивания...");
    document.querySelectorAll('.manga-card').forEach(card => {
        if (card.dataset.imagePath && card.dataset.imagePath.trim() !== '') {
            imagePaths.push(card.dataset.imagePath);
            console.log("Добавлен путь:", card.dataset.imagePath);
        } else {
            console.log("У карточки нет пути к изображению или путь пустой");
        }
    });
    
    console.log("Найдено путей:", imagePaths.length);
    
    if (imagePaths.length === 0) {
        showNotification('Нет доступных изображений для скачивания', 'error');
        return;
    }
    
    // Показываем спиннер
    document.getElementById('spinner-container').style.display = 'flex';
    
    let responseRef = null; // Переменная для сохранения ссылки на ответ
    
    // Отправляем запрос на создание файла выбранного формата
    fetch(`/api/download/${format}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_paths: imagePaths
        })
    })
    .then(response => {
        // Сохраняем ответ для последующего использования
        responseRef = response;
        
        // Скрываем спиннер
        document.getElementById('spinner-container').style.display = 'none';
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        // Для успешного ответа начинаем скачивание
        return response.blob();
    })
    .then(blob => {
        // Создаем временную ссылку для скачивания
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        // Определяем имя файла из заголовков ответа, если возможно
        let filename = 'manga_translation';
        
        // Используем сохраненную ссылку на ответ
        if (responseRef) {
            const contentDisposition = responseRef.headers.get('Content-Disposition');
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }
        }
        
        // Добавляем расширение, если оно отсутствует
        if (!filename.includes('.')) {
            filename += `.${format}`;
        }
        
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Освобождаем ресурсы
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification(`Скачивание ${format.toUpperCase()} началось`, 'success');
    })
    .catch(error => {
        document.getElementById('spinner-container').style.display = 'none';
        showNotification(`Ошибка при скачивании: ${error.message}`, 'error');
        console.error('Ошибка скачивания:', error);
    });
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Добавляем иконку в зависимости от типа
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    // Находим или создаем контейнер для уведомлений
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Добавляем уведомление в контейнер
    container.appendChild(notification);
    
    // Автоматически удаляем уведомление через 4 секунды
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Основной обработчик загрузки документа - объединяем все в один
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация табов
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });
    
    // Инициализация переключателей метода перевода
    const radioButtons = document.querySelectorAll('input[name="translation_method"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            // Обновляем видимость поля API ключа
            toggleApiKeyField();
            
            // Синхронизируем значения между формами
            const individualEl = document.getElementById('translation_method_individual');
            const foldersEl = document.getElementById('translation_method_folders');
            
            if (individualEl) individualEl.value = this.value;
            if (foldersEl) foldersEl.value = this.value;
        });
    });
    
    // Инициализация выбора языка источника
    const sourceLangSelect = document.getElementById('source_language');
    if (sourceLangSelect) {
        sourceLangSelect.addEventListener('change', function() {
            // Синхронизируем значения между формами
            const individualEl = document.getElementById('source_language_individual');
            const foldersEl = document.getElementById('source_language_folders');
            
            if (individualEl) individualEl.value = this.value;
            if (foldersEl) foldersEl.value = this.value;
            
            // Обновляем информацию о выбранном OCR-движке
            updateOcrEngineInfo();
        });
    }
    
    // Инициализация выбора языка перевода
    const targetLangSelect = document.getElementById('target_language');
    if (targetLangSelect) {
        targetLangSelect.addEventListener('change', function() {
            const individualEl = document.getElementById('target_language_individual');
            const foldersEl = document.getElementById('target_language_folders');
            
            if (individualEl) individualEl.value = this.value;
            if (foldersEl) foldersEl.value = this.value;
        });
    }
    
    // Инициализация поля API ключа
    const apiKeyInput = document.getElementById('openai_api_key');
    if (apiKeyInput) {
        apiKeyInput.addEventListener('input', function() {
            const individualEl = document.getElementById('openai_api_key_individual');
            const foldersEl = document.getElementById('openai_api_key_folders');
            
            if (individualEl) individualEl.value = this.value;
            if (foldersEl) foldersEl.value = this.value;
        });
    }
    
    // Инициализация поля выбора файлов
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', updateFileCount);
    }
    
    // Инициализация режима редактирования
    const editModeRadios = document.querySelectorAll('input[name="edit_mode"]');
    editModeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const isEditMode = this.value === 'true';
            
            const individualEl = document.getElementById('edit_mode_individual');
            const foldersEl = document.getElementById('edit_mode_folders');
            
            if (individualEl) individualEl.value = this.value;
            if (foldersEl) foldersEl.value = this.value;
            
            // Переключаем видимость описаний режимов
            const autoModeDesc = document.getElementById('auto-mode-description');
            const editModeDesc = document.getElementById('edit-mode-description');
            
            if (autoModeDesc) autoModeDesc.style.display = isEditMode ? 'none' : 'block';
            if (editModeDesc) editModeDesc.style.display = isEditMode ? 'block' : 'none';
        });
    });
    
    // Инициализация просмотрщика
    const mangaCards = document.querySelectorAll('.manga-card');
    if (mangaCards.length > 0) {
        const totalPagesEl = document.getElementById('total-pages');
        const bottomNavTotalEl = document.getElementById('bottom-nav-total');
        
        if (totalPagesEl) totalPagesEl.textContent = mangaCards.length;
        if (bottomNavTotalEl) bottomNavTotalEl.textContent = mangaCards.length;
        
        navigateReader(1);
    }
    
    // Обработка клика вне выпадающих меню
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.details-dropdown') && !event.target.closest('.details-button')) {
            document.querySelectorAll('.details-dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
    
    // Закрытие диалогов по клику вне содержимого
    document.querySelectorAll('.dialog').forEach(dialog => {
        dialog.addEventListener('click', function(event) {
            if (event.target === dialog) {
                dialog.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });
    
    // Клавиатурная навигация
    document.addEventListener('keydown', function(event) {
        // Стрелки для навигации
        if (event.key === 'ArrowLeft') {
            navigateReader('prev');
        } else if (event.key === 'ArrowRight') {
            navigateReader('next');
        }
        // Escape для закрытия диалогов
        else if (event.key === 'Escape') {
            document.querySelectorAll('.dialog.active').forEach(dialog => {
                dialog.classList.remove('active');
                document.body.style.overflow = 'auto';
            });
            
            document.querySelectorAll('.details-dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
    
    // Инициализация видимости поля API ключа
    toggleApiKeyField();
    
    // Инициализация информации об OCR-движке при загрузке
    updateOcrEngineInfo();
    
    // Инициализация кнопок скачивания при наличии результатов
    if (document.querySelector('.results-container')) {
        initDownloadButtons();
    }
    
    // Обработчик для кнопки выхода из режима чтения
    const exitReaderButton = document.getElementById('exit-reader-mode');
    if (exitReaderButton) {
        exitReaderButton.addEventListener('click', function() {
            const readerModeToggle = document.getElementById('reader-mode-toggle');
            if (readerModeToggle) {
                readerModeToggle.click();  // Эмулируем клик по кнопке переключения режима
            }
        });
    }
    
    // Обработчик для нижних кнопок навигации
    const bottomNavPrev = document.getElementById('bottom-nav-prev');
    const bottomNavNext = document.getElementById('bottom-nav-next');
    
    if (bottomNavPrev) {
        bottomNavPrev.addEventListener('click', function() {
            navigateReader('prev');
        });
    }
    
    if (bottomNavNext) {
        bottomNavNext.addEventListener('click', function() {
            navigateReader('next');
        });
    }
    
    // Кнопка прокрутки вверх
    const backToTopButton = document.getElementById('back-to-top');
    if (backToTopButton) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopButton.style.display = 'flex';
            } else {
                backToTopButton.style.display = 'none';
            }
        });
        
        backToTopButton.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
});
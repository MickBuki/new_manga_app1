/**
 * Модуль просмотра и управления изображениями в редакторе
 */

import API from '../utils/api.js';
import Notification from '../modules/notification.js';
import { getElement } from '../utils/helpers.js';

const ImageViewer = {
    /**
     * Текущий режим отображения изображения
     * Возможные значения: 'translated', 'original', 'text-removed'
     */
    displayMode: 'translated',
    
    /**
     * Флаг отображения предпросмотра
     */
    showingPreview: false,
    
    /**
     * Уровень масштабирования изображения
     */
    zoomLevel: 1.0,
    
    /**
     * ID текущей сессии редактирования
     */
    sessionId: '',
    
    /**
     * Глобальный кэш изображений
     */
    imageCache: new Map(),
    
    /**
     * Очередь предзагрузки
     */
    preloadQueue: [],
    
    /**
     * Флаг активной предзагрузки
     */
    isPreloading: false,
    
    /**
     * Инициализация просмотрщика изображений
     * @param {string} sessionId - ID сессии редактирования
     */
    init: (sessionId) => {
        ImageViewer.sessionId = sessionId;
        
        // Инициализация кнопок управления изображением
        const toggleModeBtn = getElement('#toggle-image-mode');
        if (toggleModeBtn) {
            toggleModeBtn.addEventListener('click', ImageViewer.toggleImageMode);
        }
        
        // Кнопки масштабирования
        const zoomInBtn = getElement('#zoom-in');
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', ImageViewer.zoomIn);
        }
        
        const zoomOutBtn = getElement('#zoom-out');
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', ImageViewer.zoomOut);
        }
        
        // Кнопки предпросмотра и сохранения
        const previewBtn = getElement('#preview-button');
        if (previewBtn) {
            previewBtn.addEventListener('click', ImageViewer.generatePreview);
        }
        
        const saveBtn = getElement('#save-button');
        if (saveBtn) {
            saveBtn.addEventListener('click', ImageViewer.showSaveDialog);
        }
        
        const confirmSaveBtn = getElement('#confirm-save');
        if (confirmSaveBtn) {
            confirmSaveBtn.addEventListener('click', ImageViewer.saveEditedImage);
        }
        
        // Предзагрузка соседних файлов
        ImageViewer.preloadAdjacentFiles();
    },
    
    /**
     * Переключение режима отображения изображения
     */
    toggleImageMode: () => {
        const translatedImage = getElement('#translated-image');
        const textRemovedImage = getElement('#text-removed-image');
        const originalImage = getElement('#original-image');
        const previewImage = getElement('#preview-image');
        const toggleButton = getElement('#toggle-image-mode');
        
        // Если показывается предпросмотр, сначала скрываем его
        if (ImageViewer.showingPreview) {
            if (previewImage) {
                previewImage.style.display = 'none';
            }
            ImageViewer.showingPreview = false;
        }
        
        // Циклическое переключение режимов
        if (ImageViewer.displayMode === 'translated') {
            // Переключение на оригинальное изображение
            if (translatedImage) translatedImage.style.display = 'none';
            if (originalImage) originalImage.style.display = 'block';
            if (textRemovedImage) textRemovedImage.style.display = 'none';
            ImageViewer.displayMode = 'original';
            if (toggleButton) {
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать без текста';
            }
        } else if (ImageViewer.displayMode === 'original') {
            // Переключение на изображение без текста
            if (translatedImage) translatedImage.style.display = 'none';
            if (originalImage) originalImage.style.display = 'none';
            if (textRemovedImage) textRemovedImage.style.display = 'block';
            ImageViewer.displayMode = 'text-removed';
            if (toggleButton) {
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать перевод';
            }
        } else {
            // Переключение на переведенное изображение
            if (translatedImage) translatedImage.style.display = 'block';
            if (originalImage) originalImage.style.display = 'none';
            if (textRemovedImage) textRemovedImage.style.display = 'none';
            ImageViewer.displayMode = 'translated';
            if (toggleButton) {
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать оригинал';
            }
        }
    },
    
    /**
     * Генерация предпросмотра с текущими настройками
     */
    generatePreview: () => {
        // Показываем спиннер
        const spinner = getElement('#spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        // Отправляем запрос на генерацию предпросмотра
        API.generatePreview(ImageViewer.sessionId)
            .then(data => {
                // Скрываем спиннер
                if (spinner) {
                    spinner.style.display = 'none';
                }
                
                if (data.success) {
                    // Показываем предпросмотр
                    const previewImage = getElement('#preview-image');
                    if (previewImage) {
                        previewImage.src = 'data:image/png;base64,' + data.preview;
                    }
                    
                    // Скрываем другие изображения
                    const translatedImage = getElement('#translated-image');
                    const originalImage = getElement('#original-image');
                    const textRemovedImage = getElement('#text-removed-image');
                    
                    if (translatedImage) translatedImage.style.display = 'none';
                    if (originalImage) originalImage.style.display = 'none';
                    if (textRemovedImage) textRemovedImage.style.display = 'none';
                    if (previewImage) previewImage.style.display = 'block';
                    
                    ImageViewer.showingPreview = true;
                    
                    // Обновляем текст кнопки
                    const toggleButton = getElement('#toggle-image-mode');
                    if (toggleButton) {
                        toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Скрыть предпросмотр';
                    }
                    
                    Notification.success('Предпросмотр сгенерирован');
                } else {
                    Notification.error('Ошибка генерации предпросмотра: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                if (spinner) {
                    spinner.style.display = 'none';
                }
                Notification.error('Ошибка: ' + error.message);
            });
    },
    
    /**
     * Показывает диалог сохранения изображения
     */
    showSaveDialog: () => {
        // Генерируем предпросмотр для сохранения
        const spinner = getElement('#spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        API.generatePreview(ImageViewer.sessionId)
            .then(data => {
                if (spinner) {
                    spinner.style.display = 'none';
                }
                
                if (data.success) {
                    // Показываем предпросмотр в диалоге
                    const savePreviewImage = getElement('#save-preview-image');
                    if (savePreviewImage) {
                        savePreviewImage.src = 'data:image/png;base64,' + data.preview;
                    }
                    
                    // Показываем диалог
                    const saveDialog = getElement('#save-dialog');
                    if (saveDialog) {
                        saveDialog.style.display = 'flex';
                    }
                } else {
                    Notification.error('Ошибка генерации предпросмотра: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                if (spinner) {
                    spinner.style.display = 'none';
                }
                Notification.error('Ошибка: ' + error.message);
            });
    },
    
    /**
     * Закрывает диалог сохранения
     */
    closeSaveDialog: () => {
        const saveDialog = getElement('#save-dialog');
        if (saveDialog) {
            saveDialog.style.display = 'none';
        }
    },
    
    /**
     * Сохраняет отредактированное изображение
     */
    saveEditedImage: () => {
        const filenameInput = getElement('#save-filename');
        const filename = filenameInput ? filenameInput.value.trim() : '';
        
        if (!filename) {
            Notification.error('Введите имя файла');
            return;
        }
        
        // Показываем спиннер
        const spinner = getElement('#spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        // Закрываем диалог
        ImageViewer.closeSaveDialog();
        
        // Отправляем запрос на сохранение
        API.saveEditedImage(ImageViewer.sessionId, filename)
            .then(data => {
                // Скрываем спиннер
                if (spinner) {
                    spinner.style.display = 'none';
                }
                
                if (data.success) {
                    Notification.success('Изображение успешно сохранено как ' + data.path);
                } else {
                    Notification.error('Ошибка сохранения: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                if (spinner) {
                    spinner.style.display = 'none';
                }
                Notification.error('Ошибка: ' + error.message);
            });
    },
    
    /**
     * Увеличивает масштаб изображения
     */
    zoomIn: () => {
        ImageViewer.zoomLevel = Math.min(ImageViewer.zoomLevel + 0.1, 3.0);
        ImageViewer.applyZoom();
    },
    
    /**
     * Уменьшает масштаб изображения
     */
    zoomOut: () => {
        ImageViewer.zoomLevel = Math.max(ImageViewer.zoomLevel - 0.1, 0.5);
        ImageViewer.applyZoom();
    },
    
    /**
     * Применяет текущий масштаб к изображению
     */
    applyZoom: () => {
        const container = getElement('#image-container');
        if (container) {
            container.style.transform = `scale(${ImageViewer.zoomLevel})`;
        }
    },
    
    /**
     * Предзагрузка соседних файлов
     */
    preloadAdjacentFiles: () => {
        const fileSelector = getElement('#file-selector');
        if (!fileSelector) return;
        
        const options = Array.from(fileSelector.options);
        const currentIndex = options.findIndex(option => option.value === ImageViewer.sessionId);
        
        if (currentIndex === -1) return;
        
        // Предзагружаем следующий и предыдущий файлы
        const indices = [];
        if (currentIndex > 0) indices.push(currentIndex - 1);
        if (currentIndex < options.length - 1) indices.push(currentIndex + 1);
        
        for (const index of indices) {
            const sessionId = options[index].value;
            // Добавляем в очередь предзагрузки
            ImageViewer.queuePreload(sessionId);
        }
        
        // Запускаем процесс предзагрузки
        ImageViewer.startPreloading();
    },
    
    /**
     * Добавляет файл в очередь предзагрузки
     * @param {string} sessionId - ID сессии
     */
    queuePreload: (sessionId) => {
        // Проверяем, не загружен ли уже этот файл
        if (ImageViewer.imageCache.has(sessionId)) return;
        
        // Добавляем в очередь, если еще не добавлен
        if (!ImageViewer.preloadQueue.includes(sessionId)) {
            ImageViewer.preloadQueue.push(sessionId);
        }
    },
    
    /**
     * Запускает процесс предзагрузки
     */
    startPreloading: () => {
        if (ImageViewer.isPreloading || ImageViewer.preloadQueue.length === 0) return;
        
        ImageViewer.isPreloading = true;
        
        // Берем следующий файл из очереди
        const sessionId = ImageViewer.preloadQueue.shift();
        const fileSelector = getElement('#file-selector');
        if (!fileSelector) {
            ImageViewer.isPreloading = false;
            setTimeout(ImageViewer.startPreloading, 100);
            return;
        }
        
        const options = Array.from(fileSelector.options);
        const currentIndex = options.findIndex(option => option.value === sessionId);
        
        if (currentIndex === -1) {
            ImageViewer.isPreloading = false;
            setTimeout(ImageViewer.startPreloading, 100);
            return;
        }
        
        const filename = options[currentIndex].textContent.trim();
        
        // Создаем объекты Image для предзагрузки
        const originalImg = new Image();
        const textRemovedImg = new Image();
        const translatedImg = new Image();
        
        // Счетчик загруженных изображений
        let loadedCount = 0;
        
        // Функция для обработки завершения загрузки
        const onLoad = () => {
            loadedCount++;
            if (loadedCount === 3) {
                // Сохраняем в кэш
                ImageViewer.imageCache.set(sessionId, {
                    original: originalImg,
                    textRemoved: textRemovedImg,
                    translated: translatedImg,
                    timestamp: Date.now()
                });
                
                // Продолжаем предзагрузку
                ImageViewer.isPreloading = false;
                setTimeout(ImageViewer.startPreloading, 100);
            }
        };
        
        // Обработчик ошибок
        const onError = () => {
            loadedCount++;
            if (loadedCount === 3) {
                ImageViewer.isPreloading = false;
                setTimeout(ImageViewer.startPreloading, 100);
            }
        };
        
        // Устанавливаем пути к изображениям
        originalImg.onload = onLoad;
        originalImg.onerror = onError;
        originalImg.src = `/static/editor_images/${sessionId}/original_${filename}`;
        
        textRemovedImg.onload = onLoad;
        textRemovedImg.onerror = onError;
        textRemovedImg.src = `/static/editor_images/${sessionId}/text_removed_${filename}`;
        
        translatedImg.onload = onLoad;
        translatedImg.onerror = onError;
        translatedImg.src = `/static/editor_images/${sessionId}/translated_${filename}`;
    }
};

export default ImageViewer;
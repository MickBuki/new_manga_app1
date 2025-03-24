/**
 * Модуль для скачивания результатов перевода
 */

import API from '../utils/api.js';
import Notification from './notification.js';
import { getFilenameFromContentDisposition } from '../utils/helpers.js';

const Download = {
    /**
     * Инициализирует кнопки скачивания
     */
    init: () => {
        console.log("Инициализация модуля скачивания...");

        // Создаем панель скачивания, если ее нет
        Download.createDownloadPanel();

        // Привязываем обработчики к кнопкам скачивания
        const downloadPdfBtn = document.getElementById('download-pdf');
        const downloadCbzBtn = document.getElementById('download-cbz');
        const downloadZipBtn = document.getElementById('download-zip');

        if (downloadPdfBtn) {
            downloadPdfBtn.addEventListener('click', () => Download.downloadResults('pdf'));
            console.log("Обработчик для скачивания PDF активирован");
        } else {
            console.warn("Кнопка скачивания PDF не найдена");
        }
        
        if (downloadCbzBtn) {
            downloadCbzBtn.addEventListener('click', () => Download.downloadResults('cbz'));
            console.log("Обработчик для скачивания CBZ активирован");
        } else {
            console.warn("Кнопка скачивания CBZ не найдена");
        }
        
        if (downloadZipBtn) {
            downloadZipBtn.addEventListener('click', () => Download.downloadResults('zip'));
            console.log("Обработчик для скачивания ZIP активирован");
        } else {
            console.warn("Кнопка скачивания ZIP не найдена");
        }

        console.log("Модуль скачивания инициализирован");
    },

    /**
     * Создает панель скачивания, если она отсутствует на странице
     */
    createDownloadPanel: () => {
        console.log("Проверка наличия панели скачивания...");
        
        // Проверяем, есть ли контейнер результатов
        const resultsContainer = document.querySelector('.results-container');
        if (!resultsContainer) {
            console.warn("Контейнер результатов не найден, панель скачивания не создается");
            return;
        }
        
        // Проверяем, есть ли уже панель скачивания
        let downloadPanel = document.querySelector('.download-options-panel');
        
        // Если панели нет, создаем её
        if (!downloadPanel) {
            console.log("Создаем новую панель скачивания");
            
            const resultsHeader = document.querySelector('.results-header');
            if (!resultsHeader) {
                console.warn("Заголовок результатов не найден, панель скачивания не создается");
                return;
            }
            
            // Создаем элемент панели скачивания
            downloadPanel = document.createElement('div');
            downloadPanel.className = 'download-options-panel';
            downloadPanel.innerHTML = `
                <div class="download-options-title">Скачать как:</div>
                <div class="download-buttons">
                    <button id="download-pdf" class="btn btn-primary download-btn">
                        <i class="fas fa-file-pdf"></i> PDF
                    </button>
                    <button id="download-cbz" class="btn btn-primary download-btn">
                        <i class="fas fa-book"></i> CBZ
                    </button>
                    <button id="download-zip" class="btn btn-primary download-btn">
                        <i class="fas fa-file-archive"></i> ZIP
                    </button>
                </div>
            `;
            
            // Добавляем панель в заголовок результатов
            resultsHeader.appendChild(downloadPanel);
            
            console.log("Панель скачивания успешно создана");
        } else {
            console.log("Панель скачивания уже существует");
            downloadPanel.style.display = 'block';
        }
    },

    /**
     * Скачивает результаты перевода в выбранном формате
     * @param {string} format - Формат файла (pdf, zip, cbz)
     */
    downloadResults: async (format) => {
        // Собираем пути ко всем обработанным изображениям
        const imagePaths = [];
        
        console.log("Поиск изображений для скачивания...");
        document.querySelectorAll('.manga-card').forEach(card => {
            if (card.dataset.imagePath && card.dataset.imagePath.trim() !== '') {
                imagePaths.push(card.dataset.imagePath);
                console.log("Добавлен путь:", card.dataset.imagePath);
            } else {
                console.warn("У карточки нет пути к изображению или путь пустой:", card);
                
                // Если у карточки нет data-image-path, попробуем найти его в других атрибутах или структуре
                // Это резервный вариант для случаев, когда data-image-path не установлен
                try {
                    // Проверяем наличие img с base64
                    const imgElement = card.querySelector('img');
                    if (imgElement && imgElement.src && imgElement.src.startsWith('data:image/')) {
                        console.log("Найдено изображение с base64 данными, но скачивание возможно только с сервера");
                    }
                    
                    // Проверяем заголовок карточки
                    const titleElement = card.querySelector('.manga-card-title');
                    if (titleElement) {
                        console.log("Название файла из заголовка:", titleElement.textContent);
                    }
                } catch (e) {
                    console.error("Ошибка при резервном поиске пути изображения:", e);
                }
            }
        });
        
        console.log("Найдено путей:", imagePaths.length);
        
        // Если путей нет, но есть карточки, попробуем альтернативный подход
        if (imagePaths.length === 0) {
            const mangaCards = document.querySelectorAll('.manga-card');
            if (mangaCards.length > 0) {
                console.warn("Карточки найдены, но пути к изображениям отсутствуют. Пробуем альтернативный вариант.");
                Notification.warning('Невозможно скачать результаты из-за отсутствия путей к изображениям. Обратитесь к разработчику.');
                return;
            }
        }
        
        if (imagePaths.length === 0) {
            Notification.error('Нет доступных изображений для скачивания');
            return;
        }
        
        // Показываем спиннер
        const spinnerContainer = document.getElementById('spinner-container');
        if (spinnerContainer) {
            spinnerContainer.style.display = 'flex';
        }
        
        try {
            // Отправляем запрос на создание файла выбранного формата
            const result = await API.downloadResults(format, imagePaths);
            
            // Скрываем спиннер
            if (spinnerContainer) {
                spinnerContainer.style.display = 'none';
            }
            
            // Извлекаем имя файла из заголовков, если возможно
            let filename = 'manga_translation';
            const contentDisposition = result.headers.contentDisposition;
            const extractedFilename = getFilenameFromContentDisposition(contentDisposition);
            
            if (extractedFilename) {
                filename = extractedFilename;
            } else if (!filename.includes('.')) {
                // Добавляем расширение, если оно отсутствует
                filename += `.${format}`;
            }
            
            // Создаем временную ссылку для скачивания
            const url = window.URL.createObjectURL(result.blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Освобождаем ресурсы
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            Notification.success(`Скачивание ${format.toUpperCase()} началось`);
        } catch (error) {
            // Скрываем спиннер в случае ошибки
            if (spinnerContainer) {
                spinnerContainer.style.display = 'none';
            }
            
            Notification.error(`Ошибка при скачивании: ${error.message}`);
            console.error('Ошибка скачивания:', error);
        }
    }
};

export default Download;
/**
 * Основной файл приложения Manga Translator
 * Точка входа для главной страницы
 */

import Theme from './modules/theme.js';
import Notification from './modules/notification.js';
import Navigation from './modules/navigation.js';
import TranslationSettings from './modules/translation.js';
import Download from './modules/download.js';
import { addEventHandler, getElement, getElements } from './utils/helpers.js';

// Инициализация всех компонентов
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM загружен, начало инициализации компонентов");
    
    // Инициализация темы оформления
    Theme.init();
    
    // Инициализация настроек перевода
    TranslationSettings.init();
    
    // Инициализация табов
    initTabs();
    
    // Инициализация выбора файлов
    initFileSelection();
    
    // Инициализация списка папок
    initFolders();
    
    // Инициализация деталей и диалогов
    initDetails();
    
    // Если есть результаты, инициализируем навигацию и скачивание
    const resultsContainer = document.querySelector('.results-container');
    if (resultsContainer) {
        console.log("Найден контейнер результатов, проверка карточек манги");
        
        // Прямая проверка наличия карточек манги
        const mangaCards = document.querySelectorAll('.manga-card');
        console.log(`Найдено ${mangaCards.length} карточек манги`);
        
        // Проверяем и исправляем атрибуты data-image-path у карточек манги
        if (mangaCards.length > 0) {
            let hasImagePaths = false;
            
            // Проверяем наличие атрибутов data-image-path у карточек
            mangaCards.forEach((card, index) => {
                if (card.dataset.imagePath && card.dataset.imagePath.trim() !== '') {
                    hasImagePaths = true;
                    console.log(`Карточка ${index+1} имеет путь к изображению: ${card.dataset.imagePath}`);
                } else {
                    console.warn(`Карточка ${index+1} не имеет пути к изображению`);
                }
            });
            
            // Если у карточек нет data-image-path, пытаемся его получить
            if (!hasImagePaths) {
                console.warn("У карточек нет атрибутов data-image-path, попытка восстановления...");
                
                // Добавляем метку для уведомления пользователя
                let notificationAdded = false;
                
                mangaCards.forEach((card, index) => {
                    // Проверяем наличие заголовка карточки
                    const cardTitle = card.querySelector('.manga-card-title');
                    if (cardTitle && cardTitle.textContent) {
                        // Получаем название файла
                        const filename = cardTitle.textContent.trim();
                        console.log(`Попытка получить путь для файла ${filename}`);
                        
                        // Получаем путь из заголовка и добавляем его в атрибут
                        // Это примерная реконструкция пути, который должен был быть
                        const estimatedPath = `/static/output/${filename}`;
                        card.dataset.imagePath = estimatedPath;
                        console.log(`Установлен приблизительный путь: ${estimatedPath}`);
                        
                        // Добавляем предупреждение один раз
                        if (!notificationAdded) {
                            notificationAdded = true;
                            setTimeout(() => {
                                // Загружаем и используем модуль уведомлений
                                import('./modules/notification.js').then(module => {
                                    const Notification = module.default;
                                    Notification.warning('Пути к изображениям были восстановлены приблизительно. Скачивание может не работать корректно.');
                                });
                            }, 2000);
                        }
                    }
                });
            }
        }
        
        // Принудительно отображаем первую карточку перед инициализацией модулей
        // это критично для обеспечения видимости результатов
        if (mangaCards.length > 0) {
            console.log("Отображаем первую карточку манги");
            mangaCards.forEach((card, index) => {
                card.style.display = index === 0 ? 'block' : 'none';
            });
        }
        
        // Инициализируем модули навигации и скачивания
        console.log("Инициализация модулей навигации и скачивания");
        Navigation.init();
        Download.init();
    } else {
        console.log("Контейнер результатов не найден");
    }
    
    // Показываем спиннер при отправке формы
    addEventHandler('#individual-form', 'submit', showSpinner);
    addEventHandler('#folders-form', 'submit', showSpinner);
    
    console.log("Инициализация компонентов завершена");
});

/**
 * Инициализация переключения табов
 */
function initTabs() {
    const tabButtons = getElements('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

/**
 * Переключение на выбранный таб
 * @param {string} tabId - ID таба
 */
function switchTab(tabId) {
    // Скрываем все табы
    getElements('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Убираем активное состояние со всех кнопок
    getElements('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Показываем выбранный таб и активируем его кнопку
    const selectedTab = getElement('#' + tabId);
    if (selectedTab) selectedTab.classList.add('active');
    
    const selectedButton = getElement(`[data-tab="${tabId}"]`);
    if (selectedButton) selectedButton.classList.add('active');
}

/**
 * Инициализация выбора файлов
 */
function initFileSelection() {
    const fileInput = getElement('#file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            updateFileCount();
        });
    }
}

/**
 * Обновление счетчика выбранных файлов
 */
function updateFileCount() {
    const fileInput = getElement('#file-input');
    const fileCount = getElement('#file-count');
    const filesPreview = getElement('#selected-files-preview');
    const filesGrid = getElement('#files-preview-grid');
    
    if (!fileInput || !fileCount || !filesPreview || !filesGrid) return;
    
    if (fileInput.files.length > 0) {
        fileCount.textContent = `Выбрано файлов: ${fileInput.files.length}`;
        
        // Очищаем предыдущие превью
        filesGrid.innerHTML = '';
        
        // Создаем превью для каждого файла
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            
            // Создаем элемент превью
            const previewItem = document.createElement('div');
            previewItem.className = 'image-item';
            
            // Создаем контейнер превью
            const previewContainer = document.createElement('div');
            previewContainer.className = 'image-preview';
            
            // Создаем элемент изображения
            const img = document.createElement('img');
            const reader = new FileReader();
            
            reader.onload = function(e) {
                img.src = e.target.result;
            };
            
            reader.readAsDataURL(file);
            previewContainer.appendChild(img);
            
            // Создаем элемент с именем файла
            const fileName = document.createElement('div');
            fileName.className = 'image-name';
            fileName.title = file.name;
            fileName.textContent = file.name;
            
            // Добавляем элементы в превью
            previewItem.appendChild(previewContainer);
            previewItem.appendChild(fileName);
            
            // Добавляем превью в сетку
            filesGrid.appendChild(previewItem);
        }
        
        filesPreview.style.display = 'block';
    } else {
        fileCount.textContent = 'Файлы не выбраны';
        filesPreview.style.display = 'none';
    }
}

/**
 * Инициализация папок с мангой
 */
function initFolders() {
    // Обработчики для выбора всех изображений в папке
    const selectAllCheckboxes = getElements('[id^="select-all-"]');
    selectAllCheckboxes.forEach(checkbox => {
        const folderId = checkbox.id.replace('select-all-', '');
        checkbox.addEventListener('change', () => {
            selectAllImages(folderId);
        });
    });
}

/**
 * Выбор всех изображений в папке
 * @param {string} folderId - ID папки
 */
function selectAllImages(folderId) {
    const checkbox = getElement('#select-all-' + folderId);
    const folderCheckboxes = getElements('.folder-' + folderId + '-checkbox');
    
    if (!checkbox) return;
    
    folderCheckboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    
    updateSelectedCount(folderId);
}

/**
 * Обновление счетчика выбранных изображений
 * @param {string} folderId - ID папки
 */
function updateSelectedCount(folderId) {
    const folderCheckboxes = getElements('.folder-' + folderId + '-checkbox');
    const selectedCount = getElement('#selected-count-' + folderId);
    
    if (!selectedCount) return;
    
    let count = 0;
    folderCheckboxes.forEach(cb => {
        if (cb.checked) count++;
    });
    
    selectedCount.textContent = count;
}

/**
 * Переключение отображения содержимого папки
 * @param {string} folderId - ID папки
 */
function toggleFolder(folderId) {
    const content = getElement('#folder-content-' + folderId);
    const icon = getElement('.folder-icon-' + folderId);
    
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

/**
 * Инициализация деталей и диалогов
 */
function initDetails() {
    // Обработка клика вне выпадающих меню
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.details-dropdown') && !event.target.closest('.details-button')) {
            getElements('.details-dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
    
    // Закрытие диалогов по клику вне содержимого
    getElements('.dialog').forEach(dialog => {
        dialog.addEventListener('click', function(event) {
            if (event.target === dialog) {
                dialog.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });
}

/**
 * Показать диалог с деталями
 * @param {string} dialogId - ID диалога
 */
function showDialog(dialogId) {
    // Закрываем все выпадающие меню
    getElements('.details-dropdown.active').forEach(el => {
        el.classList.remove('active');
    });
    
    // Показываем диалог
    const dialog = getElement('#' + dialogId);
    if (dialog) {
        dialog.classList.add('active');
        
        // Предотвращаем скроллинг основного содержимого
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Скрыть диалог
 * @param {string} dialogId - ID диалога
 */
function hideDialog(dialogId) {
    const dialog = getElement('#' + dialogId);
    if (dialog) {
        dialog.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
}

/**
 * Показать спиннер загрузки
 */
function showSpinner() {
    const spinnerContainer = getElement('#spinner-container');
    if (spinnerContainer) {
        spinnerContainer.style.display = 'flex';
    }
    return true;
}

// Делаем функции доступными глобально
window.toggleFolder = toggleFolder;
window.selectAllImages = selectAllImages;
window.updateSelectedCount = updateSelectedCount;
window.toggleDetails = function(fileId) {
    const dropdown = getElement('#details-dropdown-' + fileId);
    
    if (!dropdown) return;
    
    // Закрываем все остальные выпадающие меню
    getElements('.details-dropdown.active').forEach(el => {
        if (el.id !== 'details-dropdown-' + fileId) {
            el.classList.remove('active');
        }
    });
    
    dropdown.classList.toggle('active');
};
window.showDialog = showDialog;
window.hideDialog = hideDialog;
window.showSpinner = showSpinner;

// КРИТИЧЕСКИ ВАЖНАЯ ФУНКЦИЯ для навигации по результатам
// Используется напрямую из HTML через onClick
window.navigateReader = function(direction) {
    console.log(`Вызван navigateReader с направлением: ${direction}`);
    
    // Используем модуль Navigation, если он инициализирован
    if (Navigation && Navigation.currentPage !== undefined) {
        console.log("Используем модуль Navigation для навигации");
        
        if (direction === 'prev') {
            Navigation.navigateTo(Navigation.currentPage - 1);
        } else if (direction === 'next') {
            Navigation.navigateTo(Navigation.currentPage + 1);
        } else {
            const page = parseInt(direction);
            if (!isNaN(page)) {
                Navigation.navigateTo(page);
            }
        }
    } else {
        // Запасной вариант для прямой навигации (если модуль не инициализирован)
        console.log("Используем прямую навигацию (без модуля)");
        
        const currentPageEl = document.getElementById('current-page');
        const totalPagesEl = document.getElementById('total-pages');
        const bottomNavCurrentEl = document.getElementById('bottom-nav-current');
        
        if (!currentPageEl || !totalPagesEl) {
            console.error("Элементы навигации не найдены");
            return;
        }
        
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
        
        // Обновляем текущую страницу
        currentPageEl.textContent = newPage;
        if (bottomNavCurrentEl) {
            bottomNavCurrentEl.textContent = newPage;
        }
        
        // Показываем/скрываем соответствующие карточки
        document.querySelectorAll('.manga-card').forEach((card, index) => {
            if (index + 1 === newPage) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Обновляем состояние кнопок
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');
        const bottomPrevButton = document.getElementById('bottom-nav-prev');
        const bottomNextButton = document.getElementById('bottom-nav-next');
        
        if (prevButton) prevButton.disabled = (newPage === 1);
        if (nextButton) nextButton.disabled = (newPage === totalPages);
        if (bottomPrevButton) bottomPrevButton.disabled = (newPage === 1);
        if (bottomNextButton) bottomNextButton.disabled = (newPage === totalPages);
    }
};
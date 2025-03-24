/**
 * Основной файл редактора манги
 * Точка входа для страницы редактирования
 */

import Theme from './modules/theme.js';
import TextBlocks from './editor/textBlocks.js';
import Formatting from './editor/formatting.js';
import ImageViewer from './editor/imageViewer.js';
import SessionManager from './editor/sessionManager.js';

// Инициализация всех компонентов при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Получаем ID сессии и данные о текстовых блоках из глобальных переменных
    const sessionId = window.sessionId;
    const textBlocks = window.textBlocks;
    
    // Проверяем, что необходимые данные доступны
    if (!sessionId) {
        console.error('Ошибка: ID сессии не определен');
        return;
    }
    
    if (!textBlocks) {
        console.error('Ошибка: данные о текстовых блоках не определены');
        return;
    }
    
    // Инициализация темы оформления
    Theme.init();
    
    // Инициализация управления текстовыми блоками
    TextBlocks.init(sessionId, textBlocks);
    
    // Инициализация форматирования текста
    Formatting.init();
    
    // Инициализация просмотрщика изображений
    ImageViewer.init(sessionId);
    
    // Инициализация менеджера сессий
    SessionManager.init(sessionId);
    
    // Проверяем и применяем отложенное обновление
    TextBlocks.applyPendingUpdate();
});

// Функции для глобального доступа из HTML
window.closeSaveDialog = function() {
    const saveDialog = document.getElementById('save-dialog');
    if (saveDialog) {
        saveDialog.style.display = 'none';
    }
};
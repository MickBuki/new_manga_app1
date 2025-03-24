/**
 * Модуль управления сессиями редактирования и навигации между файлами
 */

import { getElement } from '../utils/helpers.js';
import TextBlocks from './textBlocks.js';

const SessionManager = {
    /**
     * ID текущей сессии редактирования
     */
    sessionId: '',
    
    /**
     * Инициализация менеджера сессий
     * @param {string} sessionId - ID текущей сессии
     */
    init: (sessionId) => {
        SessionManager.sessionId = sessionId;
        
        // Инициализация навигации между файлами
        const fileSelector = getElement('#file-selector');
        const prevFileBtn = getElement('#prev-file');
        const nextFileBtn = getElement('#next-file');
        
        // Проверяем, есть ли элементы навигации (они могут отсутствовать, если нет связанных файлов)
        if (!fileSelector) {
            console.log('Селектор файлов не найден - навигация отключена');
            return;
        }
        
        console.log(`Инициализация навигации с ${fileSelector.options.length} файлами`);
        
        // Добавляем обработчик изменения выпадающего списка
        fileSelector.addEventListener('change', function() {
            const selectedSessionId = fileSelector.value;
            console.log(`Выбран файл ${selectedSessionId} через выпадающий список`);
            
            if (selectedSessionId && selectedSessionId !== SessionManager.sessionId) {
                // Сохраняем текущее состояние перед переходом
                TextBlocks.savePendingUpdate(function() {
                    SessionManager.navigateToSession(selectedSessionId);
                });
            }
        });
        
        // Обработчики кнопок навигации
        if (prevFileBtn) {
            prevFileBtn.addEventListener('click', function() {
                console.log('Нажата кнопка "Предыдущий файл"');
                SessionManager.navigateToAdjacentFile(-1);
            });
        }
        
        if (nextFileBtn) {
            nextFileBtn.addEventListener('click', function() {
                console.log('Нажата кнопка "Следующий файл"');
                SessionManager.navigateToAdjacentFile(1);
            });
        }
        
        // Добавляем горячие клавиши для навигации между файлами
        document.addEventListener('keydown', function(event) {
            // Alt + Left Arrow = предыдущий файл
            if (event.altKey && event.key === 'ArrowLeft') {
                event.preventDefault();
                console.log('Горячая клавиша Alt+Left для перехода к предыдущему файлу');
                SessionManager.navigateToAdjacentFile(-1);
            }
            // Alt + Right Arrow = следующий файл
            else if (event.altKey && event.key === 'ArrowRight') {
                event.preventDefault();
                console.log('Горячая клавиша Alt+Right для перехода к следующему файлу');
                SessionManager.navigateToAdjacentFile(1);
            }
        });
        
        // Обновляем состояние кнопок навигации
        SessionManager.updateNavigationState();
    },
    
    /**
     * Навигация к соседнему файлу
     * @param {number} direction - Направление (-1 = предыдущий, 1 = следующий)
     */
    navigateToAdjacentFile: (direction) => {
        const fileSelector = getElement('#file-selector');
        if (!fileSelector) {
            console.log('Селектор файлов не найден - невозможно перейти к соседнему файлу');
            return;
        }
        
        const options = Array.from(fileSelector.options);
        const currentIndex = options.findIndex(option => option.value === SessionManager.sessionId);
        
        console.log(`Текущий индекс: ${currentIndex}, Всего опций: ${options.length}, Направление: ${direction}`);
        
        if (currentIndex === -1) {
            console.log('Текущая сессия не найдена в списке файлов');
            return;
        }
        
        const newIndex = currentIndex + direction;
        console.log(`Пытаемся перейти к индексу ${newIndex}`);
        
        if (newIndex >= 0 && newIndex < options.length) {
            const newSessionId = options[newIndex].value;
            console.log(`Переход к сессии ${newSessionId}`);
            
            // Сохраняем текущее состояние перед переходом
            TextBlocks.savePendingUpdate(function() {
                SessionManager.navigateToSession(newSessionId);
            });
        } else {
            console.log(`Невозможно перейти - за пределами массива (0-${options.length-1})`);
        }
    },
    
    /**
     * Переход к конкретной сессии
     * @param {string} targetSessionId - ID сессии назначения
     */
    navigateToSession: (targetSessionId) => {
        if (TextBlocks.currentBlockId !== null) {
            // Сохраняем ID блока в sessionStorage перед переходом
            sessionStorage.setItem('lastEditedBlockId_' + SessionManager.sessionId, TextBlocks.currentBlockId);
        }
        
        const spinner = getElement('#spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        window.location.href = `/edit/${targetSessionId}?direct=1`;
    },
    
    /**
     * Обновляет состояние кнопок навигации
     */
    updateNavigationState: () => {
        const fileSelector = getElement('#file-selector');
        const prevFileBtn = getElement('#prev-file');
        const nextFileBtn = getElement('#next-file');
        
        if (!fileSelector || !prevFileBtn || !nextFileBtn) {
            console.log('Элементы навигации не найдены - невозможно обновить состояние');
            return;
        }
        
        const options = Array.from(fileSelector.options);
        const currentIndex = options.findIndex(option => option.value === SessionManager.sessionId);
        
        if (currentIndex === -1) {
            console.log('Текущая сессия не найдена в списке - не обновляем состояние кнопок');
            return;
        }
        
        console.log(`Обновление состояния навигации: индекс ${currentIndex}, всего ${options.length} опций`);
        
        // Отключаем кнопку "Предыдущий файл", если мы на первом файле
        const isPrevDisabled = (currentIndex === 0);
        prevFileBtn.disabled = isPrevDisabled;
        console.log(`Кнопка "Предыдущий файл" ${isPrevDisabled ? 'отключена' : 'включена'}`);
        
        // Отключаем кнопку "Следующий файл", если мы на последнем файле
        const isNextDisabled = (currentIndex === options.length - 1);
        nextFileBtn.disabled = isNextDisabled;
        console.log(`Кнопка "Следующий файл" ${isNextDisabled ? 'отключена' : 'включена'}`);
    }
};

export default SessionManager;
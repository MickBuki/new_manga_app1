/**
 * Модуль для управления текстовыми блоками в редакторе
 */

import API from '../utils/api.js';
import Notification from '../modules/notification.js';
import { getElement } from '../utils/helpers.js';

const TextBlocks = {
    // Текущий выбранный блок
    currentBlockId: null,
    
    // Все текстовые блоки из сессии
    blocks: [],
    
    // ID текущей сессии
    sessionId: '',
    
    /**
     * Инициализация модуля управления текстовыми блоками
     * @param {string} sessionId - ID сессии редактирования
     * @param {Array} textBlocks - Массив текстовых блоков
     */
    init: (sessionId, textBlocks) => {
        TextBlocks.sessionId = sessionId;
        TextBlocks.blocks = textBlocks;
        
        // Инициализация выпадающего списка
        const blockSelector = getElement('#text-block-selector');
        if (blockSelector) {
            blockSelector.addEventListener('change', () => {
                const blockId = parseInt(blockSelector.value);
                if (!isNaN(blockId)) {
                    TextBlocks.selectBlock(blockId);
                } else {
                    TextBlocks.hideTextEditor();
                }
            });
        }
        
        // Обработчики кнопок редактирования
        const updateBlockBtn = getElement('#update-block');
        if (updateBlockBtn) {
            updateBlockBtn.addEventListener('click', TextBlocks.updateCurrentBlock);
        }
        
        const nextBlockBtn = getElement('#next-block');
        if (nextBlockBtn) {
            nextBlockBtn.addEventListener('click', TextBlocks.goToNextBlock);
        }
        
        // Обработка клика по блокам на изображении
        document.querySelectorAll('.text-block').forEach(block => {
            block.addEventListener('click', () => {
                const blockId = parseInt(block.dataset.id);
                TextBlocks.selectBlock(blockId);
            });
        });
        
        // Восстанавливаем последний редактируемый блок из sessionStorage
        setTimeout(() => {
            const lastBlockId = sessionStorage.getItem('lastEditedBlockId_' + sessionId);
            if (lastBlockId !== null) {
                TextBlocks.selectBlock(parseInt(lastBlockId));
            }
        }, 300);
        
        // Обработчик клавиш
        document.addEventListener('keydown', (event) => {
            // Если открыт редактор текста
            if (TextBlocks.currentBlockId !== null) {
                // Ctrl + Enter для обновления блока
                if (event.ctrlKey && event.key === 'Enter') {
                    event.preventDefault();
                    TextBlocks.updateCurrentBlock();
                }
                // Tab для перехода к следующему блоку
                else if (event.key === 'Tab') {
                    event.preventDefault();
                    TextBlocks.goToNextBlock();
                }
            }
        });
    },
    
    /**
     * Выбор текстового блока для редактирования
     * @param {number} blockId - ID блока
     */
    selectBlock: (blockId) => {
        TextBlocks.currentBlockId = blockId;
        
        // Подсветка выбранного блока на изображении
        document.querySelectorAll('.text-block').forEach(block => {
            block.classList.remove('active');
        });
        
        const blockElement = document.querySelector(`.text-block[data-id="${blockId}"]`);
        if (blockElement) {
            blockElement.classList.add('active');
            
            // Прокрутка изображения к выбранному блоку
            const container = document.getElementById('image-container');
            const rect = blockElement.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();
            
            if (rect.top < containerRect.top || rect.bottom > containerRect.bottom ||
                rect.left < containerRect.left || rect.right > containerRect.right) {
                blockElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        
        // Выбор в выпадающем списке
        const blockSelector = getElement('#text-block-selector');
        if (blockSelector) {
            blockSelector.value = blockId;
        }
        
        // Заполнение полей редактора
        const block = TextBlocks.blocks.find(b => b.id === blockId);
        if (block) {
            const originalTextElement = getElement('#original-text');
            const translatedTextElement = getElement('#translated-text');
            
            if (originalTextElement) {
                originalTextElement.textContent = block.text || "(нет текста)";
            }
            
            if (translatedTextElement) {
                translatedTextElement.value = block.translated_text || "";
                // Устанавливаем фокус и курсор в конец текста
                translatedTextElement.focus();
                translatedTextElement.setSelectionRange(
                    translatedTextElement.value.length,
                    translatedTextElement.value.length
                );
            }
            
            // Импортируем и инициализируем модуль форматирования, если он существует
            import('./formatting.js').then(module => {
                const Formatting = module.default;
                // Загружаем стиль блока или используем стиль по умолчанию
                const style = block.style || {
                    font_weight: 'normal',
                    font_style: 'normal',
                    font_size: 16,
                    align: 'center',
                    offset_x: 0,
                    offset_y: 0
                };
                Formatting.setCurrentStyle(style);
                Formatting.updateStyleUI();
            }).catch(err => {
                console.error('Ошибка импорта модуля форматирования:', err);
            });
            
            TextBlocks.showTextEditor();
        }
    },
    
    /**
     * Показать редактор текста
     */
    showTextEditor: () => {
        const noBlockElement = getElement('#no-block-selected');
        const textEditorElement = getElement('#text-editor');
        
        if (noBlockElement) {
            noBlockElement.style.display = 'none';
        }
        
        if (textEditorElement) {
            textEditorElement.style.display = 'block';
        }
    },
    
    /**
     * Скрыть редактор текста
     */
    hideTextEditor: () => {
        const noBlockElement = getElement('#no-block-selected');
        const textEditorElement = getElement('#text-editor');
        
        if (noBlockElement) {
            noBlockElement.style.display = 'flex';
        }
        
        if (textEditorElement) {
            textEditorElement.style.display = 'none';
        }
        
        TextBlocks.currentBlockId = null;
        
        // Снимаем выделение со всех блоков
        document.querySelectorAll('.text-block').forEach(block => {
            block.classList.remove('active');
        });
    },
    
    /**
     * Обновляет текущий текстовый блок
     * @param {Function} [callback] - Функция обратного вызова после обновления
     */
    updateCurrentBlock: (callback) => {
        if (TextBlocks.currentBlockId === null) {
            if (callback && typeof callback === 'function') {
                callback();
            }
            return;
        }
        
        const translatedText = getElement('#translated-text')?.value || '';
        
        // Показываем спиннер
        const spinner = getElement('#spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
        
        // Получаем текущий стиль из модуля форматирования
        import('./formatting.js').then(module => {
            const Formatting = module.default;
            const currentStyle = Formatting.getCurrentStyle();
            
            // Принудительно обновляем локальные данные перед отправкой на сервер
            const blockIndex = TextBlocks.blocks.findIndex(b => b.id === TextBlocks.currentBlockId);
            if (blockIndex !== -1) {
                TextBlocks.blocks[blockIndex].translated_text = translatedText;
                TextBlocks.blocks[blockIndex].style = {...currentStyle};
            }
            
            // Отправляем запрос на обновление блока
            API.updateTranslation(
                TextBlocks.sessionId,
                TextBlocks.currentBlockId,
                translatedText,
                currentStyle
            )
            .then(data => {
                // Скрываем спиннер
                if (spinner) {
                    spinner.style.display = 'none';
                }
                
                if (data.success) {
                    Notification.success('Текст и стиль успешно обновлены');
                    
                    // Вызываем колбэк, если он передан
                    if (callback && typeof callback === 'function') {
                        callback();
                    }
                } else {
                    console.error('Ошибка сохранения:', data.error);
                    Notification.error('Ошибка обновления: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Ошибка запроса:', error);
                if (spinner) {
                    spinner.style.display = 'none';
                }
                Notification.error('Ошибка: ' + error.message);
            });
        }).catch(err => {
            console.error('Ошибка импорта модуля форматирования:', err);
            if (spinner) {
                spinner.style.display = 'none';
            }
            Notification.error('Ошибка импорта модуля форматирования: ' + err.message);
        });
    },
    
    /**
     * Перейти к следующему блоку
     */
    goToNextBlock: () => {
        if (TextBlocks.currentBlockId === null) return;
        
        // Находим индекс текущего блока
        const blockIndex = TextBlocks.blocks.findIndex(b => b.id === TextBlocks.currentBlockId);
        if (blockIndex !== -1 && blockIndex < TextBlocks.blocks.length - 1) {
            // Сохраняем текущий блок перед переходом к следующему
            TextBlocks.updateCurrentBlock(() => {
                // Переходим к следующему блоку
                const nextBlockId = TextBlocks.blocks[blockIndex + 1].id;
                TextBlocks.selectBlock(nextBlockId);
            });
        } else if (blockIndex === TextBlocks.blocks.length - 1) {
            // Если это последний блок, показываем уведомление
            Notification.info('Это последний блок текста');
        }
    },
    
    /**
     * Сохраняет отложенное обновление блока
     * @param {Function} [callback] - Функция обратного вызова
     */
    savePendingUpdate: (callback) => {
        if (TextBlocks.currentBlockId !== null) {
            const translatedText = getElement('#translated-text')?.value || '';
            
            // Сохраняем в sessionStorage
            sessionStorage.setItem('pendingUpdate', JSON.stringify({
                sessionId: TextBlocks.sessionId,
                blockId: TextBlocks.currentBlockId,
                text: translatedText
            }));
        }
        
        if (callback && typeof callback === 'function') {
            callback();
        }
    },
    
    /**
     * Применяет отложенное обновление блока
     */
    applyPendingUpdate: () => {
        const pendingUpdateStr = sessionStorage.getItem('pendingUpdate');
        if (!pendingUpdateStr) return;
        
        try {
            const pendingUpdate = JSON.parse(pendingUpdateStr);
            
            // Проверяем, относится ли обновление к текущей сессии
            if (pendingUpdate.sessionId === TextBlocks.sessionId) {
                // Отправляем запрос на обновление без ожидания ответа
                API.updateTranslation(
                    pendingUpdate.sessionId,
                    pendingUpdate.blockId,
                    pendingUpdate.text,
                    null // Стиль сохранится текущий
                ).catch(error => {
                    console.error('Ошибка применения отложенного обновления:', error);
                });
            }
        } catch (e) {
            console.error('Ошибка разбора отложенного обновления:', e);
        }
        
        // Удаляем примененное обновление
        sessionStorage.removeItem('pendingUpdate');
    }
};

export default TextBlocks;
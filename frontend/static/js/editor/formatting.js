/**
 * Модуль управления форматированием текста в редакторе
 */

import { getElement } from '../utils/helpers.js';

const Formatting = {
    /**
     * Текущие стилевые настройки
     */
    currentStyle: {
        font_weight: 'normal',
        font_style: 'normal',
        font_size: 16,
        align: 'center',
        offset_x: 0,
        offset_y: 0
    },
    
    /**
     * Инициализация модуля форматирования
     */
    init: () => {
        // Жирный текст
        const boldBtn = getElement('#format-bold');
        if (boldBtn) {
            boldBtn.addEventListener('click', () => {
                Formatting.toggleStyle('font_weight', 'normal', 'bold');
            });
        }
        
        // Курсив
        const italicBtn = getElement('#format-italic');
        if (italicBtn) {
            italicBtn.addEventListener('click', () => {
                Formatting.toggleStyle('font_style', 'normal', 'italic');
            });
        }
        
        // Размер шрифта
        const decreaseFontBtn = getElement('#font-decrease');
        if (decreaseFontBtn) {
            decreaseFontBtn.addEventListener('click', () => {
                Formatting.changeStyle('font_size', Math.max(8, Formatting.currentStyle.font_size - 2));
            });
        }
        
        const increaseFontBtn = getElement('#font-increase');
        if (increaseFontBtn) {
            increaseFontBtn.addEventListener('click', () => {
                Formatting.changeStyle('font_size', Math.min(32, Formatting.currentStyle.font_size + 2));
            });
        }
        
        // Выравнивание
        const alignLeftBtn = getElement('#align-left');
        if (alignLeftBtn) {
            alignLeftBtn.addEventListener('click', () => {
                Formatting.changeStyle('align', 'left');
                Formatting.updateAlignButtons('left');
            });
        }
        
        const alignCenterBtn = getElement('#align-center');
        if (alignCenterBtn) {
            alignCenterBtn.addEventListener('click', () => {
                Formatting.changeStyle('align', 'center');
                Formatting.updateAlignButtons('center');
            });
        }
        
        const alignRightBtn = getElement('#align-right');
        if (alignRightBtn) {
            alignRightBtn.addEventListener('click', () => {
                Formatting.changeStyle('align', 'right');
                Formatting.updateAlignButtons('right');
            });
        }
        
        // Позиционирование
        const moveLeftBtn = getElement('#move-left');
        if (moveLeftBtn) {
            moveLeftBtn.addEventListener('click', () => {
                Formatting.changeStyle('offset_x', Formatting.currentStyle.offset_x - 5);
            });
        }
        
        const moveRightBtn = getElement('#move-right');
        if (moveRightBtn) {
            moveRightBtn.addEventListener('click', () => {
                Formatting.changeStyle('offset_x', Formatting.currentStyle.offset_x + 5);
            });
        }
        
        const moveUpBtn = getElement('#move-up');
        if (moveUpBtn) {
            moveUpBtn.addEventListener('click', () => {
                Formatting.changeStyle('offset_y', Formatting.currentStyle.offset_y - 5);
            });
        }
        
        const moveDownBtn = getElement('#move-down');
        if (moveDownBtn) {
            moveDownBtn.addEventListener('click', () => {
                Formatting.changeStyle('offset_y', Formatting.currentStyle.offset_y + 5);
            });
        }
        
        const resetPositionBtn = getElement('#reset-position');
        if (resetPositionBtn) {
            resetPositionBtn.addEventListener('click', () => {
                Formatting.changeStyle('offset_x', 0);
                Formatting.changeStyle('offset_y', 0);
            });
        }
    },
    
    /**
     * Получает текущие стилевые настройки
     * @returns {Object} Объект с текущими стилями
     */
    getCurrentStyle: () => {
        return { ...Formatting.currentStyle };
    },
    
    /**
     * Устанавливает текущие стилевые настройки
     * @param {Object} style - Объект с новыми стилями
     */
    setCurrentStyle: (style) => {
        Formatting.currentStyle = { ...style };
    },
    
    /**
     * Переключение между двумя значениями стиля
     * @param {string} property - Свойство стиля
     * @param {*} value1 - Первое значение
     * @param {*} value2 - Второе значение
     */
    toggleStyle: (property, value1, value2) => {
        const newValue = Formatting.currentStyle[property] === value2 ? value1 : value2;
        Formatting.changeStyle(property, newValue);
        
        // Визуальная индикация состояния кнопки
        if (property === 'font_weight') {
            const formatBoldBtn = getElement('#format-bold');
            if (formatBoldBtn) {
                formatBoldBtn.classList.toggle('active', newValue === value2);
            }
        } else if (property === 'font_style') {
            const formatItalicBtn = getElement('#format-italic');
            if (formatItalicBtn) {
                formatItalicBtn.classList.toggle('active', newValue === value2);
            }
        }
    },
    
    /**
     * Установка конкретного значения стиля
     * @param {string} property - Свойство стиля
     * @param {*} value - Новое значение
     */
    changeStyle: (property, value) => {
        Formatting.currentStyle[property] = value;
        
        // Обновляем отображение значения, если это размер шрифта
        if (property === 'font_size') {
            const fontSizeValue = getElement('#font-size-value');
            if (fontSizeValue) {
                fontSizeValue.textContent = value;
            }
        }
        
        // Уведомляем модуль текстовых блоков об изменениях
        import('./textBlocks.js').then(module => {
            const TextBlocks = module.default;
            // Применяем изменения сразу для предварительного просмотра
            TextBlocks.updateCurrentBlock();
        }).catch(err => {
            console.error('Ошибка импорта модуля textBlocks:', err);
        });
    },
    
    /**
     * Обновление индикаторов выравнивания
     * @param {string} align - Тип выравнивания (left, center, right)
     */
    updateAlignButtons: (align) => {
        const alignLeftBtn = getElement('#align-left');
        const alignCenterBtn = getElement('#align-center');
        const alignRightBtn = getElement('#align-right');
        
        if (alignLeftBtn) {
            alignLeftBtn.classList.toggle('active', align === 'left');
        }
        
        if (alignCenterBtn) {
            alignCenterBtn.classList.toggle('active', align === 'center');
        }
        
        if (alignRightBtn) {
            alignRightBtn.classList.toggle('active', align === 'right');
        }
    },
    
    /**
     * Обновление UI в соответствии с текущим стилем
     */
    updateStyleUI: () => {
        // Кнопка "Жирный"
        const formatBoldBtn = getElement('#format-bold');
        if (formatBoldBtn) {
            formatBoldBtn.classList.toggle('active', Formatting.currentStyle.font_weight === 'bold');
        }
        
        // Кнопка "Курсив"
        const formatItalicBtn = getElement('#format-italic');
        if (formatItalicBtn) {
            formatItalicBtn.classList.toggle('active', Formatting.currentStyle.font_style === 'italic');
        }
        
        // Размер шрифта
        const fontSizeValue = getElement('#font-size-value');
        if (fontSizeValue) {
            fontSizeValue.textContent = Formatting.currentStyle.font_size;
        }
        
        // Кнопки выравнивания
        Formatting.updateAlignButtons(Formatting.currentStyle.align);
    }
};

export default Formatting;
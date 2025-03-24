/**
 * Модуль с вспомогательными функциями
 */

/**
 * Натуральная сортировка строк (учитывающая числа)
 * @param {string} a - Первая строка для сравнения
 * @param {string} b - Вторая строка для сравнения
 * @returns {number} Результат сравнения (-1, 0, 1)
 */
export const naturalSort = (a, b) => {
    const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    return collator.compare(a, b);
};

/**
 * Задержка выполнения (Promise-обертка над setTimeout)
 * @param {number} ms - Время задержки в миллисекундах
 * @returns {Promise<void>} Promise, который разрешится через указанное время
 */
export const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Безопасное получение элемента DOM с выводом ошибки в консоль при отсутствии
 * @param {string} selector - CSS-селектор элемента
 * @param {Element} [parent=document] - Родительский элемент для поиска
 * @returns {Element|null} Найденный элемент или null
 */
export const getElement = (selector, parent = document) => {
    const element = parent.querySelector(selector);
    if (!element) {
        console.error(`Элемент "${selector}" не найден`);
    }
    return element;
};

/**
 * Безопасное получение коллекции элементов DOM
 * @param {string} selector - CSS-селектор элементов
 * @param {Element} [parent=document] - Родительский элемент для поиска
 * @returns {NodeListOf<Element>} Коллекция найденных элементов
 */
export const getElements = (selector, parent = document) => {
    return parent.querySelectorAll(selector);
};

/**
 * Добавляет обработчик события с проверкой существования элемента
 * @param {string|Element} selector - CSS-селектор или элемент DOM
 * @param {string} event - Название события
 * @param {Function} handler - Функция обработчик
 * @param {Object} [options] - Дополнительные параметры обработчика
 */
export const addEventHandler = (selector, event, handler, options) => {
    const element = typeof selector === 'string' ? getElement(selector) : selector;
    if (element) {
        element.addEventListener(event, handler, options);
    }
};

/**
 * Синхронизирует значение между элементами формы
 * @param {string} sourceSelector - CSS-селектор источника
 * @param {string[]} targetSelectors - Массив CSS-селекторов целевых элементов
 * @param {string} [eventType='change'] - Тип события для отслеживания
 */
export const syncFormValues = (sourceSelector, targetSelectors, eventType = 'change') => {
    const sourceElement = getElement(sourceSelector);
    if (!sourceElement) return;
    
    sourceElement.addEventListener(eventType, () => {
        const value = sourceElement.type === 'checkbox' ? sourceElement.checked : sourceElement.value;
        
        targetSelectors.forEach(selector => {
            const targetElement = getElement(selector);
            if (targetElement) {
                if (targetElement.type === 'checkbox') {
                    targetElement.checked = value;
                } else {
                    targetElement.value = value;
                }
            }
        });
    });
};

/**
 * Получает имя файла из заголовка Content-Disposition
 * @param {string} contentDisposition - Значение заголовка Content-Disposition
 * @returns {string|null} Имя файла или null, если не найдено
 */
export const getFilenameFromContentDisposition = (contentDisposition) => {
    if (!contentDisposition) return null;
    
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch && filenameMatch[1]) {
        return filenameMatch[1];
    }
    return null;
};

/**
 * Загружает изображение и возвращает Promise с объектом Image
 * @param {string} src - URL изображения
 * @returns {Promise<HTMLImageElement>} Promise с загруженным изображением
 */
export const loadImage = (src) => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = (e) => reject(new Error(`Ошибка загрузки изображения: ${src}`));
        img.src = src;
    });
};
/**
 * Модуль для работы с API сервера
 */

const API = {
    /**
     * Обновляет перевод текстового блока
     * @param {string} sessionId - ID сессии редактирования
     * @param {number} blockId - ID блока текста
     * @param {string} text - Новый текст перевода
     * @param {Object} style - Стилевые настройки текста
     * @returns {Promise<Object>} - Результат выполнения запроса
     */
    updateTranslation: async (sessionId, blockId, text, style) => {
        try {
            console.log(`API: updateTranslation(sessionId=${sessionId}, blockId=${blockId})`);
            
            const response = await fetch('/api/edit/update_translation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    block_id: blockId,
                    text: text,
                    style: style
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка HTTP: ' + response.status);
            }
            
            const result = await response.json();
            console.log('API: updateTranslation успешно выполнен', result);
            return result;
        } catch (error) {
            console.error('Ошибка API updateTranslation:', error);
            throw error;
        }
    },

    /**
     * Генерирует предпросмотр с текущими настройками перевода
     * @param {string} sessionId - ID сессии редактирования
     * @returns {Promise<Object>} - Результат выполнения запроса с preview в base64
     */
    generatePreview: async (sessionId) => {
        try {
            console.log(`API: generatePreview(sessionId=${sessionId})`);
            
            const response = await fetch('/api/edit/generate_preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка HTTP: ' + response.status);
            }
            
            const result = await response.json();
            console.log('API: generatePreview успешно выполнен');
            return result;
        } catch (error) {
            console.error('Ошибка API generatePreview:', error);
            throw error;
        }
    },

    /**
     * Сохраняет отредактированное изображение
     * @param {string} sessionId - ID сессии редактирования
     * @param {string} filename - Имя файла для сохранения
     * @returns {Promise<Object>} - Результат выполнения запроса
     */
    saveEditedImage: async (sessionId, filename) => {
        try {
            console.log(`API: saveEditedImage(sessionId=${sessionId}, filename=${filename})`);
            
            const response = await fetch('/api/edit/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    filename: filename
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка HTTP: ' + response.status);
            }
            
            const result = await response.json();
            console.log('API: saveEditedImage успешно выполнен', result);
            return result;
        } catch (error) {
            console.error('Ошибка API saveEditedImage:', error);
            throw error;
        }
    },

    /**
     * Скачивает результаты перевода в выбранном формате
     * @param {string} format - Формат файла (pdf, zip, cbz)
     * @param {Array<string>} imagePaths - Массив путей к изображениям
     * @returns {Promise<Blob>} - Blob с данными для скачивания
     */
    downloadResults: async (format, imagePaths) => {
        try {
            console.log(`API: downloadResults(format=${format}, imagePaths=)`, imagePaths);
            
            // Проверяем наличие путей
            if (!imagePaths || imagePaths.length === 0) {
                throw new Error('Не указаны пути к изображениям');
            }
            
            const response = await fetch(`/api/download/${format}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_paths: imagePaths
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                console.error('Ошибка HTTP:', response.status, errText);
                throw new Error(`Ошибка сервера: ${response.status} ${errText.substring(0, 100)}`);
            }
            
            console.log('API: downloadResults успешно выполнен', {
                status: response.status,
                contentType: response.headers.get('Content-Type'),
                contentDisposition: response.headers.get('Content-Disposition')
            });
            
            return {
                blob: await response.blob(),
                headers: {
                    contentDisposition: response.headers.get('Content-Disposition'),
                    contentType: response.headers.get('Content-Type')
                }
            };
        } catch (error) {
            console.error('Ошибка API downloadResults:', error);
            throw error;
        }
    }
};

// Экспортируем модуль API
export default API;
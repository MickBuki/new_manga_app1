/**
 * Модуль для отображения уведомлений
 */

const Notification = {
    /**
     * Показывает уведомление пользователю
     * @param {string} message - Текст уведомления
     * @param {string} type - Тип уведомления (info, success, error, warning)
     * @param {number} duration - Продолжительность показа в мс (по умолчанию 3000мс)
     */
    show: (message, type = 'info', duration = 3000) => {
        // Проверяем, существует ли уже контейнер для уведомлений
        let notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        // Создаем уведомление
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
        
        // Добавляем уведомление в контейнер
        notificationContainer.appendChild(notification);
        
        // Удаляем уведомление через заданное время
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notificationContainer.contains(notification)) {
                    notificationContainer.removeChild(notification);
                }
            }, 300);
        }, duration);
    },
    
    /**
     * Показывает уведомление об успехе
     * @param {string} message - Текст уведомления
     * @param {number} duration - Продолжительность показа в мс
     */
    success: (message, duration = 3000) => {
        Notification.show(message, 'success', duration);
    },
    
    /**
     * Показывает уведомление об ошибке
     * @param {string} message - Текст уведомления
     * @param {number} duration - Продолжительность показа в мс
     */
    error: (message, duration = 4000) => {
        Notification.show(message, 'error', duration);
    },
    
    /**
     * Показывает информационное уведомление
     * @param {string} message - Текст уведомления
     * @param {number} duration - Продолжительность показа в мс
     */
    info: (message, duration = 3000) => {
        Notification.show(message, 'info', duration);
    },
    
    /**
     * Показывает предупреждающее уведомление
     * @param {string} message - Текст уведомления
     * @param {number} duration - Продолжительность показа в мс
     */
    warning: (message, duration = 4000) => {
        Notification.show(message, 'warning', duration);
    }
};

// Экспортируем модуль уведомлений
export default Notification;
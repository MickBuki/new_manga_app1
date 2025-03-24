/**
 * Модуль управления темой оформления
 */

const Theme = {
    /**
     * Текущая тема - светлая или темная
     */
    current: 'light',
    
    /**
     * Инициализация управления темой
     */
    init: () => {
        const toggleSwitch = document.getElementById('theme-switch');
        if (!toggleSwitch) return;
        
        // Загружаем сохраненную тему из localStorage
        Theme.current = localStorage.getItem('theme') || 'light';
        
        // Применяем сохраненную тему при загрузке
        document.documentElement.setAttribute('data-theme', Theme.current);
        toggleSwitch.checked = Theme.current === 'dark';
        
        // Обработчик переключения темы
        toggleSwitch.addEventListener('change', function() {
            Theme.toggle(this.checked);
        });
    },
    
    /**
     * Переключение темы оформления
     * @param {boolean} isDark - Флаг включения темной темы
     */
    toggle: (isDark) => {
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            Theme.current = 'dark';
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            Theme.current = 'light';
        }
    },
    
    /**
     * Проверка, активна ли темная тема
     * @returns {boolean} Флаг активности темной темы
     */
    isDarkMode: () => {
        return Theme.current === 'dark';
    }
};

// Экспортируем модуль темы
export default Theme;
/**
 * Модуль для навигации по результатам перевода
 */

import { getElement, getElements } from '../utils/helpers.js';

const Navigation = {
    /**
     * Текущая страница манги
     */
    currentPage: 1,
    
    /**
     * Общее количество страниц
     */
    totalPages: 0,
    
    /**
     * Активен ли режим чтения на весь экран
     */
    readerMode: false,
    
    /**
     * Инициализация навигации
     */
    init: () => {
        // Находим все карточки манги
        const mangaCards = getElements('.manga-card');
        Navigation.totalPages = mangaCards.length;
        
        if (Navigation.totalPages === 0) return;
        
        // ВАЖНО: Немедленно отображаем первую карточку, чтобы результаты были видны
        mangaCards.forEach((card, index) => {
            card.style.display = index === 0 ? 'block' : 'none';
        });
        
        // Устанавливаем текущую страницу
        Navigation.currentPage = 1;
        
        // Обновляем счетчики страниц
        Navigation.updatePageCounters();
        
        // Инициализируем обработчики нажатий кнопок
        Navigation.initNavigationHandlers();
        
        // Инициализируем режим чтения
        Navigation.initReaderMode();
        
        // Инициализируем навигацию с клавиатуры
        Navigation.initKeyboardNavigation();
        
        // Только после всех инициализаций пробуем загрузить сохраненную страницу
        setTimeout(() => {
            const savedPage = parseInt(localStorage.getItem('currentMangaPage')) || 1;
            if (savedPage > 1 && savedPage <= Navigation.totalPages) {
                Navigation.navigateTo(savedPage);
            }
        }, 100);
        
        // Инициализируем кнопку "наверх"
        Navigation.initBackToTop();
    },
    
    /**
     * Инициализирует обработчики кнопок навигации
     */
    initNavigationHandlers: () => {
        // Верхние кнопки навигации
        const prevPageBtn = getElement('#prev-page');
        const nextPageBtn = getElement('#next-page');
        
        // Нижние кнопки навигации
        const bottomPrevBtn = getElement('#bottom-nav-prev');
        const bottomNextBtn = getElement('#bottom-nav-next');
        
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => Navigation.navigateTo(Navigation.currentPage - 1));
        }
        
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => Navigation.navigateTo(Navigation.currentPage + 1));
        }
        
        if (bottomPrevBtn) {
            bottomPrevBtn.addEventListener('click', () => Navigation.navigateTo(Navigation.currentPage - 1));
        }
        
        if (bottomNextBtn) {
            bottomNextBtn.addEventListener('click', () => Navigation.navigateTo(Navigation.currentPage + 1));
        }
    },
    
    /**
     * Инициализирует режим чтения на весь экран
     */
    initReaderMode: () => {
        const readerToggle = getElement('#reader-mode-toggle');
        const exitReaderBtn = getElement('#exit-reader-mode');
        
        if (!readerToggle) return;
        
        // Загружаем сохраненное состояние режима чтения
        Navigation.readerMode = localStorage.getItem('readerMode') === 'true';
        
        // Устанавливаем начальное состояние
        if (Navigation.readerMode) {
            document.body.classList.add('manga-reader-mode');
            readerToggle.innerHTML = '<i class="fas fa-compress-alt"></i>';
        } else {
            readerToggle.innerHTML = '<i class="fas fa-expand-alt"></i>';
        }
        
        // Обработчик переключения режима чтения
        readerToggle.addEventListener('click', () => {
            Navigation.toggleReaderMode();
        });
        
        // Обработчик выхода из режима чтения
        if (exitReaderBtn) {
            exitReaderBtn.addEventListener('click', () => {
                Navigation.toggleReaderMode(false);
            });
        }
    },
    
    /**
     * Инициализирует навигацию с клавиатуры
     */
    initKeyboardNavigation: () => {
        document.addEventListener('keydown', (event) => {
            // Стрелки для навигации по страницам
            if (event.key === 'ArrowLeft') {
                Navigation.navigateTo(Navigation.currentPage - 1);
            } else if (event.key === 'ArrowRight') {
                Navigation.navigateTo(Navigation.currentPage + 1);
            }
            
            // Escape для закрытия диалогов
            else if (event.key === 'Escape') {
                document.querySelectorAll('.dialog.active').forEach(dialog => {
                    dialog.classList.remove('active');
                    document.body.style.overflow = 'auto';
                });
                
                document.querySelectorAll('.details-dropdown.active').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        });
    },
    
    /**
     * Инициализирует кнопку "наверх"
     */
    initBackToTop: () => {
        const backToTopButton = getElement('#back-to-top');
        if (!backToTopButton) return;
        
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopButton.style.display = 'flex';
            } else {
                backToTopButton.style.display = 'none';
            }
        });
        
        backToTopButton.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    },
    
    /**
     * Переключает режим чтения на весь экран
     * @param {boolean} [enable] - Принудительно включить/выключить режим
     */
    toggleReaderMode: (enable) => {
        const readerToggle = getElement('#reader-mode-toggle');
        if (!readerToggle) return;
        
        // Если enable не передан, инвертируем текущее состояние
        if (enable === undefined) {
            enable = !Navigation.readerMode;
        }
        
        // Устанавливаем новое состояние
        Navigation.readerMode = enable;
        
        if (Navigation.readerMode) {
            document.body.classList.add('manga-reader-mode');
            readerToggle.innerHTML = '<i class="fas fa-compress-alt"></i>';
            localStorage.setItem('readerMode', 'true');
        } else {
            document.body.classList.remove('manga-reader-mode');
            readerToggle.innerHTML = '<i class="fas fa-expand-alt"></i>';
            localStorage.setItem('readerMode', 'false');
        }
    },
    
    /**
     * Навигация к указанной странице
     * @param {number} pageNumber - Номер страницы
     */
    navigateTo: (pageNumber) => {
        // Проверка валидности номера страницы
        const page = Math.max(1, Math.min(pageNumber, Navigation.totalPages));
        
        // Если ничего не изменилось, выходим
        if (page === Navigation.currentPage && Navigation.currentPage !== 0) return;
        
        // Обновляем текущую страницу
        Navigation.currentPage = page;
        
        // Обновляем счетчики страниц
        Navigation.updatePageCounters();
        
        // Обновляем состояние кнопок
        Navigation.updateButtonStates();
        
        // Показываем текущую карточку и скрываем остальные
        const mangaCards = getElements('.manga-card');
        mangaCards.forEach((card, index) => {
            if (index + 1 === Navigation.currentPage) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Сохраняем текущую страницу в localStorage
        localStorage.setItem('currentMangaPage', Navigation.currentPage);
    },
    
    /**
     * Обновляет счетчики текущей страницы
     */
    updatePageCounters: () => {
        // Верхние счетчики
        const currentPageEl = getElement('#current-page');
        const totalPagesEl = getElement('#total-pages');
        
        // Нижние счетчики
        const bottomCurrentEl = getElement('#bottom-nav-current');
        const bottomTotalEl = getElement('#bottom-nav-total');
        
        if (currentPageEl) currentPageEl.textContent = Navigation.currentPage;
        if (totalPagesEl) totalPagesEl.textContent = Navigation.totalPages;
        if (bottomCurrentEl) bottomCurrentEl.textContent = Navigation.currentPage;
        if (bottomTotalEl) bottomTotalEl.textContent = Navigation.totalPages;
    },
    
    /**
     * Обновляет состояние кнопок навигации
     */
    updateButtonStates: () => {
        // Верхние кнопки
        const prevPageBtn = getElement('#prev-page');
        const nextPageBtn = getElement('#next-page');
        
        // Нижние кнопки
        const bottomPrevBtn = getElement('#bottom-nav-prev');
        const bottomNextBtn = getElement('#bottom-nav-next');
        
        const isFirst = Navigation.currentPage === 1;
        const isLast = Navigation.currentPage === Navigation.totalPages;
        
        if (prevPageBtn) prevPageBtn.disabled = isFirst;
        if (bottomPrevBtn) bottomPrevBtn.disabled = isFirst;
        if (nextPageBtn) nextPageBtn.disabled = isLast;
        if (bottomNextBtn) bottomNextBtn.disabled = isLast;
    }
};

export default Navigation;
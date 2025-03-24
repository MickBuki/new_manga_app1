// Управление темной темой
function setupThemeToggle() {
    const toggleSwitch = document.getElementById('theme-switch');
    if (!toggleSwitch) return;
    
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Применяем сохраненную тему при загрузке
    document.documentElement.setAttribute('data-theme', currentTheme);
    toggleSwitch.checked = currentTheme === 'dark';
    
    // Обработчик переключения темы
    toggleSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}

// Управление навигацией манги
function setupMangaNavigation() {
    // Элементы нижней панели навигации
    const bottomNavPrev = document.getElementById('bottom-nav-prev');
    const bottomNavNext = document.getElementById('bottom-nav-next');
    const bottomNavCurrent = document.getElementById('bottom-nav-current');
    const bottomNavTotal = document.getElementById('bottom-nav-total');
    
    // Элементы верхней панели навигации
    const topNavPrev = document.getElementById('prev-page');
    const topNavNext = document.getElementById('next-page');
    const topNavCurrent = document.getElementById('current-page');
    const topNavTotal = document.getElementById('total-pages');
    
    // Проверяем, есть ли элементы навигации на странице
    if (!bottomNavPrev || !bottomNavNext || !topNavPrev || !topNavNext) return;
    
    // Синхронизируем нижнюю и верхнюю навигацию
    function updateNavigation(newPage) {
        // Находим все карточки манги
        const mangaCards = document.querySelectorAll('.manga-card');
        const totalPages = mangaCards.length;
        
        // Проверка валидности номера страницы
        newPage = Math.max(1, Math.min(newPage, totalPages));
        
        // Обновляем счетчики страниц
        bottomNavCurrent.textContent = newPage;
        bottomNavTotal.textContent = totalPages;
        topNavCurrent.textContent = newPage;
        topNavTotal.textContent = totalPages;
        
        // Обновляем состояние кнопок
        bottomNavPrev.disabled = (newPage === 1);
        bottomNavNext.disabled = (newPage === totalPages);
        topNavPrev.disabled = (newPage === 1);
        topNavNext.disabled = (newPage === totalPages);
        
        // Скрываем все карточки и показываем только текущую
        mangaCards.forEach((card, index) => {
            if (index + 1 === newPage) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Сохраняем текущую страницу в localStorage
        localStorage.setItem('currentMangaPage', newPage);
    }
    
    // Функция навигации вперед/назад
    window.navigateReader = function(direction) {
        const currentPage = parseInt(topNavCurrent.textContent);
        const totalPages = parseInt(topNavTotal.textContent);
        
        if (direction === 'prev') {
            updateNavigation(Math.max(1, currentPage - 1));
        } else if (direction === 'next') {
            updateNavigation(Math.min(totalPages, currentPage + 1));
        } else {
            updateNavigation(parseInt(direction));
        }
    };
    
    // Обработчики для кнопок нижней навигации
    bottomNavPrev.addEventListener('click', function() {
        navigateReader('prev');
    });
    
    bottomNavNext.addEventListener('click', function() {
        navigateReader('next');
    });
    
    // Загрузка сохраненной страницы или первой по умолчанию
    const savedPage = parseInt(localStorage.getItem('currentMangaPage')) || 1;
    const mangaCards = document.querySelectorAll('.manga-card');
    
    if (mangaCards.length > 0) {
        const validPage = Math.min(savedPage, mangaCards.length);
        // Вызываем после небольшой задержки, чтобы DOM успел загрузиться
        setTimeout(() => {
            updateNavigation(validPage);
        }, 100);
    }
    
    // Клавиатурная навигация
    document.addEventListener('keydown', function(event) {
        if (event.key === 'ArrowLeft') {
            navigateReader('prev');
        } else if (event.key === 'ArrowRight') {
            navigateReader('next');
        }
    });
}

// Управление кнопкой "Наверх"
function setupBackToTop() {
    const backToTopButton = document.getElementById('back-to-top');
    if (!backToTopButton) return;
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });
    
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Переключение полноэкранного режима чтения
function setupReaderMode() {
    const readerToggle = document.getElementById('reader-mode-toggle');
    const exitReaderBtn = document.getElementById('exit-reader-mode');
    
    if (!readerToggle) return;
    
    // Проверяем сохраненное состояние режима чтения
    const isReaderMode = localStorage.getItem('readerMode') === 'true';
    
    // Функция включения/выключения режима чтения
    function toggleReaderMode(enable) {
        if (enable) {
            document.body.classList.add('manga-reader-mode');
            readerToggle.innerHTML = '<i class="fas fa-compress-alt"></i>';
            localStorage.setItem('readerMode', 'true');
        } else {
            document.body.classList.remove('manga-reader-mode');
            readerToggle.innerHTML = '<i class="fas fa-expand-alt"></i>';
            localStorage.setItem('readerMode', 'false');
        }
    }
    
    // Применяем сохраненное состояние при загрузке
    if (isReaderMode) {
        toggleReaderMode(true);
    }
    
    // Обработчик для кнопки включения режима чтения
    readerToggle.addEventListener('click', function() {
        const isCurrentlyInReaderMode = document.body.classList.contains('manga-reader-mode');
        toggleReaderMode(!isCurrentlyInReaderMode);
    });
    
    // Обработчик для кнопки выхода из режима чтения
    if (exitReaderBtn) {
        exitReaderBtn.addEventListener('click', function() {
            toggleReaderMode(false);
        });
    }
}

// Предварительная загрузка изображений для плавной навигации
function preloadMangaImages() {
    const mangaCards = document.querySelectorAll('.manga-card');
    if (mangaCards.length === 0) return;
    
    // Создаем массив для хранения всех URL изображений
    const imageUrls = [];
    
    mangaCards.forEach(card => {
        const image = card.querySelector('.manga-image');
        if (image && image.src) {
            imageUrls.push(image.src);
        }
    });
    
    // Предварительная загрузка изображений
    imageUrls.forEach(url => {
        const img = new Image();
        img.src = url;
    });
}

// Инициализация переключателя режима редактирования
const editModeRadios = document.querySelectorAll('input[name="edit_mode"]');
editModeRadios.forEach(radio => {
    radio.addEventListener('change', function() {
        // Обновляем описание режима
        const autoDescription = document.getElementById('auto-mode-description');
        const editDescription = document.getElementById('edit-mode-description');
                
        if (this.value === 'true') {
            autoDescription.style.display = 'none';
            editDescription.style.display = 'block';
        } else {
            autoDescription.style.display = 'block';
            editDescription.style.display = 'none';
        }
                
        // Синхронизируем значения между формами
        document.getElementById('edit_mode_individual').value = this.value;
        document.getElementById('edit_mode_folders').value = this.value;
    });
});

// Инициализация всех компонентов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    setupThemeToggle();
    setupMangaNavigation();
    setupBackToTop();
    setupReaderMode();
    preloadMangaImages();
    
    // Добавляем класс к контейнеру для отступа от нижней панели навигации
    if (document.querySelector('.bottom-nav')) {
        document.querySelector('.container').classList.add('with-bottom-nav');
    }
});
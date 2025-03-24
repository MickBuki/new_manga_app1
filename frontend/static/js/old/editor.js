        // Глобальный кэш изображений
        const imageCache = new Map();
        const preloadQueue = [];
        let isPreloading = false;

        // Сохраняем ID сессии для использования в JS
        const sessionId = window.sessionId;
        const textBlocks = window.textBlocks;

        // Текущий выбранный блок
        let currentBlockId = null;
        let displayMode = 'translated'; // 'translated', 'original', 'text-removed'
        let showingPreview = false;
        let zoomLevel = 1.0;

        let currentStyle = {
            font_weight: 'normal',
            font_style: 'normal',
            font_size: 16,
            align: 'center',
            offset_x: 0,
            offset_y: 0
        };

        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            // Инициализация выпадающего списка
            document.getElementById('text-block-selector').addEventListener('change', function() {
                const blockId = parseInt(this.value);
                if (!isNaN(blockId)) {
                    selectTextBlock(blockId);
                } else {
                    hideTextEditor();
                }
            });
            
            // Обработчики кнопок редактирования
            document.getElementById('update-block').addEventListener('click', updateCurrentBlock);
            document.getElementById('next-block').addEventListener('click', goToNextBlock);
            
            // Обработчики кнопок изображения
            document.getElementById('toggle-image-mode').addEventListener('click', toggleImageMode);
            document.getElementById('zoom-in').addEventListener('click', zoomIn);
            document.getElementById('zoom-out').addEventListener('click', zoomOut);
            
            // Обработчики предпросмотра и сохранения
            document.getElementById('preview-button').addEventListener('click', generatePreview);
            document.getElementById('save-button').addEventListener('click', showSaveDialog);
            document.getElementById('confirm-save').addEventListener('click', saveEditedImage);
            
            setTimeout(function() {
                const lastBlockId = sessionStorage.getItem('lastEditedBlockId_' + sessionId);
                if (lastBlockId !== null) {
                    selectTextBlock(parseInt(lastBlockId));
                }
            }, 300);

            // Обработчик клавиш
            document.addEventListener('keydown', handleKeyPress);
        
            // Инициализация навигации между файлами
            initFileNavigation();
        
            // Проверяем и применяем отложенное обновление
            applyPendingUpdate();
            
            // Предзагружаем соседние файлы
            preloadAdjacentFiles();

            // Инициализация кнопок форматирования
            initFormatButtons();
        });
        
        // Обновленная функция выбора текстового блока
        function selectTextBlock(blockId) {
            currentBlockId = blockId;
            
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
            document.getElementById('text-block-selector').value = blockId;
            
            // Заполнение полей редактора
            const block = textBlocks.find(b => b.id === blockId);
            if (block) {
                document.getElementById('original-text').textContent = block.text || "(нет текста)";
                document.getElementById('translated-text').value = block.translated_text || "";
                
                // Загружаем стиль блока или используем стиль по умолчанию
                currentStyle = block.style || {
                    font_weight: 'normal',
                    font_style: 'normal',
                    font_size: 16,
                    align: 'center',
                    offset_x: 0,
                    offset_y: 0
                };
                
                // Обновляем UI в соответствии со стилем
                updateStyleUI();
                
                showTextEditor();
            }
        }
        
        // Показать редактор текста
        function showTextEditor() {
            document.getElementById('no-block-selected').style.display = 'none';
            document.getElementById('text-editor').style.display = 'block';
            document.getElementById('translated-text').focus();
        }
        
        // Скрыть редактор текста
        function hideTextEditor() {
            document.getElementById('no-block-selected').style.display = 'flex';
            document.getElementById('text-editor').style.display = 'none';
            currentBlockId = null;
            
            // Снимаем выделение со всех блоков
            document.querySelectorAll('.text-block').forEach(block => {
                block.classList.remove('active');
            });
        }
        
        // Обновленная функция для обновления текста и стиля блока
        function updateCurrentBlock(callback) {
            if (currentBlockId === null) {
                if (callback && typeof callback === 'function') {
                    callback();
                }
                return;
            }
            
            const translatedText = document.getElementById('translated-text').value;
            
            document.getElementById('spinner').style.display = 'flex';
            console.log('Отправка данных:', {
                session_id: sessionId,
                block_id: currentBlockId,
                text: translatedText,
                style: currentStyle
            });
            
            // Принудительно обновляем локальные данные перед отправкой на сервер
            const blockIndex = textBlocks.findIndex(b => b.id === currentBlockId);
            if (blockIndex !== -1) {
                textBlocks[blockIndex].translated_text = translatedText;
                textBlocks[blockIndex].style = {...currentStyle};
            }
            
            fetch('/api/edit/update_translation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    block_id: currentBlockId,
                    text: translatedText,
                    style: currentStyle
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка HTTP: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('spinner').style.display = 'none';
                
                if (data.success) {
                    showNotification('Текст и стиль успешно обновлены', 'success');
                    
                    // Вызываем колбэк, если он передан
                    if (callback && typeof callback === 'function') {
                        callback();
                    }
                } else {
                    console.error('Ошибка сохранения:', data.error);
                    showNotification('Ошибка обновления: ' + (data.error || 'Неизвестная ошибка'), 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка запроса:', error);
                document.getElementById('spinner').style.display = 'none';
                showNotification('Ошибка: ' + error.message, 'error');
            });
        }
        
        // Перейти к следующему блоку
        function goToNextBlock() {
            if (currentBlockId === null) return;
            
            // Находим индекс текущего блока
            const blockIndex = textBlocks.findIndex(b => b.id === currentBlockId);
            if (blockIndex !== -1 && blockIndex < textBlocks.length - 1) {
                // Переходим к следующему блоку
                selectTextBlock(textBlocks[blockIndex + 1].id);
            } else if (blockIndex === textBlocks.length - 1) {
                // Если это последний блок, показываем уведомление
                showNotification('Это последний блок текста', 'info');
            }
        }

        // Новая функция переключения режимов отображения
        function toggleImageMode() {
            const translatedImage = document.getElementById('translated-image');
            const textRemovedImage = document.getElementById('text-removed-image');
            const originalImage = document.getElementById('original-image');
            const previewImage = document.getElementById('preview-image');
            const toggleButton = document.getElementById('toggle-image-mode');
            
            // Если показывается предпросмотр, сначала скрываем его
            if (showingPreview) {
                previewImage.style.display = 'none';
                showingPreview = false;
            }
            
            // Циклическое переключение режимов
            if (displayMode === 'translated') {
                // Переключение на оригинальное изображение
                translatedImage.style.display = 'none';
                originalImage.style.display = 'block';
                textRemovedImage.style.display = 'none';
                displayMode = 'original';
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать без текста';
            } else if (displayMode === 'original') {
                // Переключение на изображение без текста
                translatedImage.style.display = 'none';
                originalImage.style.display = 'none';
                textRemovedImage.style.display = 'block';
                displayMode = 'text-removed';
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать перевод';
            } else {
                // Переключение на переведенное изображение
                translatedImage.style.display = 'block';
                originalImage.style.display = 'none';
                textRemovedImage.style.display = 'none';
                displayMode = 'translated';
                toggleButton.innerHTML = '<i class="fas fa-exchange-alt"></i> Показать оригинал';
            }
        }
        
        // Генерация предпросмотра
        function generatePreview() {
            // Показываем спиннер
            document.getElementById('spinner').style.display = 'flex';
            
            // Отправляем запрос на генерацию предпросмотра
            fetch('/api/edit/generate_preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Скрываем спиннер
                document.getElementById('spinner').style.display = 'none';
                
                if (data.success) {
                    // Показываем предпросмотр
                    const previewImage = document.getElementById('preview-image');
                    previewImage.src = 'data:image/png;base64,' + data.preview;
                    
                    // Скрываем другие изображения
                    document.getElementById('translated-image').style.display = 'none';
                    document.getElementById('original-image').style.display = 'none';
                    document.getElementById('text-removed-image').style.display = 'none';
                    previewImage.style.display = 'block';
                    
                    showingPreview = true;
                    
                    // Обновляем текст кнопки
                    document.getElementById('toggle-image-mode').innerHTML = '<i class="fas fa-exchange-alt"></i> Скрыть предпросмотр';
                    
                    showNotification('Предпросмотр сгенерирован', 'success');
                } else {
                    showNotification('Ошибка генерации предпросмотра: ' + (data.error || 'Неизвестная ошибка'), 'error');
                }
            })
            .catch(error => {
                document.getElementById('spinner').style.display = 'none';
                showNotification('Ошибка: ' + error.message, 'error');
            });
        }
        
        // Показать диалог сохранения
        function showSaveDialog() {
            // Генерируем предпросмотр для сохранения
            document.getElementById('spinner').style.display = 'flex';
            
            fetch('/api/edit/generate_preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('spinner').style.display = 'none';
                
                if (data.success) {
                    // Показываем предпросмотр в диалоге
                    document.getElementById('save-preview-image').src = 'data:image/png;base64,' + data.preview;
                    
                    // Показываем диалог
                    document.getElementById('save-dialog').style.display = 'flex';
                } else {
                    showNotification('Ошибка генерации предпросмотра: ' + (data.error || 'Неизвестная ошибка'), 'error');
                }
            })
            .catch(error => {
                document.getElementById('spinner').style.display = 'none';
                showNotification('Ошибка: ' + error.message, 'error');
            });
        }
        
        // Закрыть диалог сохранения
        function closeSaveDialog() {
            document.getElementById('save-dialog').style.display = 'none';
        }
        
        // Сохранить отредактированное изображение
        function saveEditedImage() {
            const filename = document.getElementById('save-filename').value.trim();
            if (!filename) {
                showNotification('Введите имя файла', 'error');
                return;
            }
            
            // Показываем спиннер
            document.getElementById('spinner').style.display = 'flex';
            
            // Закрываем диалог
            closeSaveDialog();
            
            // Отправляем запрос на сохранение
            fetch('/api/edit/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    filename: filename
                })
            })
            .then(response => response.json())
            .then(data => {
                // Скрываем спиннер
                document.getElementById('spinner').style.display = 'none';
                
                if (data.success) {
                    showNotification('Изображение успешно сохранено как ' + data.path, 'success');
                } else {
                    showNotification('Ошибка сохранения: ' + (data.error || 'Неизвестная ошибка'), 'error');
                }
            })
            .catch(error => {
                document.getElementById('spinner').style.display = 'none';
                showNotification('Ошибка: ' + error.message, 'error');
            });
        }
        
        // Масштабирование изображения
        function zoomIn() {
            zoomLevel = Math.min(zoomLevel + 0.1, 3.0);
            applyZoom();
        }
        
        function zoomOut() {
            zoomLevel = Math.max(zoomLevel - 0.1, 0.5);
            applyZoom();
        }
        
        function applyZoom() {
            const container = document.getElementById('image-container');
            container.style.transform = `scale(${zoomLevel})`;
        }
        
        // Обработка нажатий клавиш
        function handleKeyPress(event) {
            // Если открыт редактор текста
            if (currentBlockId !== null) {
                // Ctrl + Enter для обновления блока
                if (event.ctrlKey && event.key === 'Enter') {
                    event.preventDefault();
                    updateCurrentBlock();
                }
                // Tab для перехода к следующему блоку
                else if (event.key === 'Tab') {
                    event.preventDefault();
                    goToNextBlock();
                }
            }
        }
        
        // Показать уведомление
        function showNotification(message, type = 'info') {
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
            
            // Удаляем уведомление через 3 секунды
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    notificationContainer.removeChild(notification);
                }, 300);
            }, 3000);
        }

        // Обновим функцию initFileNavigation
        function initFileNavigation() {
            const fileSelector = document.getElementById('file-selector');
            const prevFileBtn = document.getElementById('prev-file');
            const nextFileBtn = document.getElementById('next-file');
            
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
                
                if (selectedSessionId && selectedSessionId !== sessionId) {
                    // Сохраняем текущее состояние перед переходом
                    savePendingUpdate(function() {
                        navigateToSession(selectedSessionId);
                    });
                }
            });
            
            // Обработчики кнопок навигации
            if (prevFileBtn) {
                prevFileBtn.addEventListener('click', function() {
                    console.log('Нажата кнопка "Предыдущий файл"');
                    navigateToAdjacentFile(-1);
                });
            }
            
            if (nextFileBtn) {
                nextFileBtn.addEventListener('click', function() {
                    console.log('Нажата кнопка "Следующий файл"');
                    navigateToAdjacentFile(1);
                });
            }
            
            // Добавляем горячие клавиши для навигации между файлами
            document.addEventListener('keydown', function(event) {
                // Alt + Left Arrow = предыдущий файл
                if (event.altKey && event.key === 'ArrowLeft') {
                    event.preventDefault();
                    console.log('Горячая клавиша Alt+Left для перехода к предыдущему файлу');
                    navigateToAdjacentFile(-1);
                }
                // Alt + Right Arrow = следующий файл
                else if (event.altKey && event.key === 'ArrowRight') {
                    event.preventDefault();
                    console.log('Горячая клавиша Alt+Right для перехода к следующему файлу');
                    navigateToAdjacentFile(1);
                }
            });
            
            // Обновляем состояние кнопок навигации
            updateFileNavigationState();
        }

        // Функция для навигации к соседнему файлу
        function navigateToAdjacentFile(direction) {
            const fileSelector = document.getElementById('file-selector');
            if (!fileSelector) {
                console.log('Селектор файлов не найден - невозможно перейти к соседнему файлу');
                return;
            }
            
            const options = Array.from(fileSelector.options);
            const currentIndex = options.findIndex(option => option.value === sessionId);
            
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
                savePendingUpdate(function() {
                    navigateToSession(newSessionId);
                });
            } else {
                console.log(`Невозможно перейти - за пределами массива (0-${options.length-1})`);
            }
        }

        // Функция для обновления состояния кнопок навигации
        function updateFileNavigationState() {
            const fileSelector = document.getElementById('file-selector');
            const prevFileBtn = document.getElementById('prev-file');
            const nextFileBtn = document.getElementById('next-file');
            
            if (!fileSelector || !prevFileBtn || !nextFileBtn) {
                console.log('Элементы навигации не найдены - невозможно обновить состояние');
                return;
            }
            
            const options = Array.from(fileSelector.options);
            const currentIndex = options.findIndex(option => option.value === sessionId);
            
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
        

        // Функция для предзагрузки соседних файлов
        function preloadAdjacentFiles() {
            const fileSelector = document.getElementById('file-selector');
            if (!fileSelector) return;
            
            const options = Array.from(fileSelector.options);
            const currentIndex = options.findIndex(option => option.value === sessionId);
            
            if (currentIndex === -1) return;
            
            // Предзагружаем следующий и предыдущий файлы
            const indices = [];
            if (currentIndex > 0) indices.push(currentIndex - 1);
            if (currentIndex < options.length - 1) indices.push(currentIndex + 1);
            
            for (const index of indices) {
                const sessionId = options[index].value;
                // Добавляем в очередь предзагрузки
                queuePreload(sessionId);
            }
            
            // Запускаем процесс предзагрузки
            startPreloading();
        }

        // Функция для добавления файла в очередь предзагрузки
        function queuePreload(sessionId) {
            // Проверяем, не загружен ли уже этот файл
            if (imageCache.has(sessionId)) return;
            
            // Добавляем в очередь, если еще не добавлен
            if (!preloadQueue.includes(sessionId)) {
                preloadQueue.push(sessionId);
            }
        }

        // Функция для запуска процесса предзагрузки
        function startPreloading() {
            if (isPreloading || preloadQueue.length === 0) return;
            
            isPreloading = true;
            
            // Берем следующий файл из очереди
            const sessionId = preloadQueue.shift();
            const fileSelector = document.getElementById('file-selector');
            const options = Array.from(fileSelector.options);
            const currentIndex = options.findIndex(option => option.value === sessionId);
            
            if (currentIndex === -1) {
                isPreloading = false;
                setTimeout(startPreloading, 100);
                return;
            }
            
            const filename = options[currentIndex].textContent.trim();
            
            // Создаем объекты Image для предзагрузки
            const originalImg = new Image();
            const textRemovedImg = new Image();
            const translatedImg = new Image();
            
            // Счетчик загруженных изображений
            let loadedCount = 0;
            
            // Функция для обработки завершения загрузки
            const onLoad = () => {
                loadedCount++;
                if (loadedCount === 3) {
                    // Сохраняем в кэш
                    imageCache.set(sessionId, {
                        original: originalImg,
                        textRemoved: textRemovedImg,
                        translated: translatedImg,
                        timestamp: Date.now()
                    });
                    
                    // Продолжаем предзагрузку
                    isPreloading = false;
                    setTimeout(startPreloading, 100);
                }
            };
            
            // Обработчик ошибок
            const onError = () => {
                loadedCount++;
                if (loadedCount === 3) {
                    isPreloading = false;
                    setTimeout(startPreloading, 100);
                }
            };
            
            // Устанавливаем пути к изображениям
            originalImg.onload = onLoad;
            originalImg.onerror = onError;
            originalImg.src = `/static/editor_images/${sessionId}/original_${filename}`;
            
            textRemovedImg.onload = onLoad;
            textRemovedImg.onerror = onError;
            textRemovedImg.src = `/static/editor_images/${sessionId}/text_removed_${filename}`;
            
            translatedImg.onload = onLoad;
            translatedImg.onerror = onError;
            translatedImg.src = `/static/editor_images/${sessionId}/translated_${filename}`;
        }

        // Функция для перехода к конкретной сессии
        function navigateToSession(targetSessionId) {
            if (currentBlockId !== null) {
                // Сохраняем ID блока в sessionStorage перед переходом
                sessionStorage.setItem('lastEditedBlockId_' + sessionId, currentBlockId);
            }
            
            document.getElementById('spinner').style.display = 'flex';
            window.location.href = `/edit/${targetSessionId}?direct=1`;
        }


        // Функция для сохранения отложенного обновления
        function savePendingUpdate(callback) {
            if (currentBlockId !== null) {
                const translatedText = document.getElementById('translated-text').value;
                
                // Сохраняем в sessionStorage
                sessionStorage.setItem('pendingUpdate', JSON.stringify({
                    sessionId: sessionId,
                    blockId: currentBlockId,
                    text: translatedText
                }));
            }
            
            if (callback) callback();
        }

        // Функция для применения отложенного обновления
        function applyPendingUpdate() {
            const pendingUpdateStr = sessionStorage.getItem('pendingUpdate');
            if (!pendingUpdateStr) return;
            
            try {
                const pendingUpdate = JSON.parse(pendingUpdateStr);
                
                // Проверяем, относится ли обновление к текущей сессии
                if (pendingUpdate.sessionId === sessionId) {
                    // Отправляем запрос на обновление без ожидания ответа
                    fetch('/api/edit/update_translation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            session_id: pendingUpdate.sessionId,
                            block_id: pendingUpdate.blockId,
                            text: pendingUpdate.text
                        })
                    }).catch(error => {
                        console.error('Ошибка применения отложенного обновления:', error);
                    });
                }
            } catch (e) {
                console.error('Ошибка разбора отложенного обновления:', e);
            }
            
            // Удаляем примененное обновление
            sessionStorage.removeItem('pendingUpdate');
        }

        // Функция для обновления состояния кнопок навигации
        function updateFileNavigationState() {
            const fileSelector = document.getElementById('file-selector');
            const prevFileBtn = document.getElementById('prev-file');
            const nextFileBtn = document.getElementById('next-file');
            
            if (!fileSelector || !prevFileBtn || !nextFileBtn) return;
            
            const options = Array.from(fileSelector.options);
            const currentIndex = options.findIndex(option => option.value === sessionId);
            
            if (currentIndex === -1) return;
            
            // Отключаем кнопку "Предыдущий файл", если мы на первом файле
            prevFileBtn.disabled = (currentIndex === 0);
            
            // Отключаем кнопку "Следующий файл", если мы на последнем файле
            nextFileBtn.disabled = (currentIndex === options.length - 1);
        }

        // Инициализация управления стилями
        function initFormatButtons() {
            // Жирный текст
            document.getElementById('format-bold').addEventListener('click', function() {
                toggleStyle('font_weight', 'normal', 'bold');
            });
            
            // Курсив
            document.getElementById('format-italic').addEventListener('click', function() {
                toggleStyle('font_style', 'normal', 'italic');
            });
            
            // Размер шрифта
            document.getElementById('font-decrease').addEventListener('click', function() {
                changeStyle('font_size', Math.max(8, currentStyle.font_size - 2));
            });
            
            document.getElementById('font-increase').addEventListener('click', function() {
                changeStyle('font_size', Math.min(32, currentStyle.font_size + 2));
            });
            
            // Выравнивание
            document.getElementById('align-left').addEventListener('click', function() {
                changeStyle('align', 'left');
                updateAlignButtons('left');
            });
            
            document.getElementById('align-center').addEventListener('click', function() {
                changeStyle('align', 'center');
                updateAlignButtons('center');
            });
            
            document.getElementById('align-right').addEventListener('click', function() {
                changeStyle('align', 'right');
                updateAlignButtons('right');
            });
            
            // Позиционирование
            document.getElementById('move-left').addEventListener('click', function() {
                changeStyle('offset_x', currentStyle.offset_x - 5);
            });
            
            document.getElementById('move-right').addEventListener('click', function() {
                changeStyle('offset_x', currentStyle.offset_x + 5);
            });
            
            document.getElementById('move-up').addEventListener('click', function() {
                changeStyle('offset_y', currentStyle.offset_y - 5);
            });
            
            document.getElementById('move-down').addEventListener('click', function() {
                changeStyle('offset_y', currentStyle.offset_y + 5);
            });
            
            document.getElementById('reset-position').addEventListener('click', function() {
                changeStyle('offset_x', 0);
                changeStyle('offset_y', 0);
            });
        }

        // Переключение между двумя значениями стиля
        function toggleStyle(property, value1, value2) {
            const newValue = currentStyle[property] === value2 ? value1 : value2;
            changeStyle(property, newValue);
            
            // Визуальная индикация состояния кнопки
            if (property === 'font_weight') {
                document.getElementById('format-bold').classList.toggle('active', newValue === value2);
            } else if (property === 'font_style') {
                document.getElementById('format-italic').classList.toggle('active', newValue === value2);
            }
        }

        // Установка конкретного значения стиля
        function changeStyle(property, value) {
            currentStyle[property] = value;
            
            // Обновляем отображение значения, если это размер шрифта
            if (property === 'font_size') {
                document.getElementById('font-size-value').textContent = value;
            }
            
            // Применяем изменения сразу для предварительного просмотра
            updateCurrentBlock();
        }

        // Обновление индикаторов выравнивания
        function updateAlignButtons(align) {
            document.getElementById('align-left').classList.toggle('active', align === 'left');
            document.getElementById('align-center').classList.toggle('active', align === 'center');
            document.getElementById('align-right').classList.toggle('active', align === 'right');
        }

        // Обновление UI в соответствии с текущим стилем
        function updateStyleUI() {
            // Кнопка "Жирный"
            document.getElementById('format-bold').classList.toggle('active', currentStyle.font_weight === 'bold');
            
            // Кнопка "Курсив"
            document.getElementById('format-italic').classList.toggle('active', currentStyle.font_style === 'italic');
            
            // Размер шрифта
            document.getElementById('font-size-value').textContent = currentStyle.font_size;
            
            // Кнопки выравнивания
            updateAlignButtons(currentStyle.align);
        }
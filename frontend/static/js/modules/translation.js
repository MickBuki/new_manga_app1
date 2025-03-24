/**
 * Модуль для управления настройками перевода
 */

import { syncFormValues } from '../utils/helpers.js';

// Словарь оптимальных OCR-движков для каждого языка
const OPTIMAL_OCR_ENGINES = {
    'ja': { engine: 'mangaocr', name: 'MangaOCR', description: 'используется для японского' },
    'zh': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для китайского' },
    'ko': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для корейского' },
    'en': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для английского' },
    'ru': { engine: 'easyocr', name: 'EasyOCR', description: 'используется для русского' },
    'fr': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для французского' },
    'es': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для испанского' },
    'de': { engine: 'paddleocr', name: 'PaddleOCR', description: 'используется для немецкого' }
};

const TranslationSettings = {
    /**
     * Инициализация настроек перевода
     */
    init: () => {
        // Инициализируем выпадающие списки и радио-кнопки
        TranslationSettings.initLanguageSelectors();
        TranslationSettings.initTranslationMethod();
        TranslationSettings.initEditMode();
        TranslationSettings.initApiKeyVisibility();
        
        // Синхронизируем значения между формами
        TranslationSettings.syncFormFields();
    },
    
    /**
     * Инициализирует селекторы языка и обработчики их изменения
     */
    initLanguageSelectors: () => {
        const sourceLangSelect = document.getElementById('source_language');
        const targetLangSelect = document.getElementById('target_language');
        
        if (sourceLangSelect) {
            sourceLangSelect.addEventListener('change', () => {
                TranslationSettings.updateOcrEngineInfo();
                
                // Синхронизируем значения между формами
                const sourceValue = sourceLangSelect.value;
                document.querySelectorAll('[name="source_language"]').forEach(input => {
                    input.value = sourceValue;
                });
            });
            
            // Инициализируем информацию о OCR при загрузке
            TranslationSettings.updateOcrEngineInfo();
        }
        
        if (targetLangSelect) {
            targetLangSelect.addEventListener('change', () => {
                // Синхронизируем значения между формами
                const targetValue = targetLangSelect.value;
                document.querySelectorAll('[name="target_language"]').forEach(input => {
                    input.value = targetValue;
                });
            });
        }
    },
    
    /**
     * Инициализирует переключатели методов перевода
     */
    initTranslationMethod: () => {
        const translationMethodRadios = document.querySelectorAll('input[name="translation_method"]');
        translationMethodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                // Обновляем видимость поля API ключа
                TranslationSettings.toggleApiKeyField();
                
                // Синхронизируем значения между формами
                const methodValue = radio.value;
                document.querySelectorAll('[name="translation_method"]').forEach(input => {
                    input.value = methodValue;
                });
            });
        });
        
        // Инициализируем видимость поля API ключа при загрузке
        TranslationSettings.toggleApiKeyField();
    },
    
    /**
     * Инициализирует переключатели режима редактирования
     */
    initEditMode: () => {
        const editModeRadios = document.querySelectorAll('input[name="edit_mode"]');
        editModeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                const isEditMode = radio.value === 'true';
                
                // Синхронизируем значения между формами
                document.querySelectorAll('[name="edit_mode"]').forEach(input => {
                    input.value = radio.value;
                });
                
                // Переключаем видимость описаний режимов
                const autoModeDesc = document.getElementById('auto-mode-description');
                const editModeDesc = document.getElementById('edit-mode-description');
                
                if (autoModeDesc) autoModeDesc.style.display = isEditMode ? 'none' : 'block';
                if (editModeDesc) editModeDesc.style.display = isEditMode ? 'block' : 'none';
            });
        });
    },
    
    /**
     * Инициализирует управление видимостью API ключа
     */
    initApiKeyVisibility: () => {
        const toggleApiKeyBtn = document.getElementById('toggle-api-key');
        if (toggleApiKeyBtn) {
            toggleApiKeyBtn.addEventListener('click', function() {
                const apiKeyInput = document.getElementById('openai_api_key');
                const icon = this.querySelector('i');
                
                if (apiKeyInput.type === 'password') {
                    apiKeyInput.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    apiKeyInput.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        }
        
        // Синхронизируем значение API ключа между формами
        const apiKeyInput = document.getElementById('openai_api_key');
        if (apiKeyInput) {
            apiKeyInput.addEventListener('input', () => {
                document.querySelectorAll('[name="openai_api_key"]').forEach(input => {
                    input.value = apiKeyInput.value;
                });
            });
        }
    },
    
    /**
     * Синхронизирует значения между формами
     */
    syncFormFields: () => {
        // Синхронизируем селекторы языков
        syncFormValues('#source_language', ['#source_language_individual', '#source_language_folders']);
        syncFormValues('#target_language', ['#target_language_individual', '#target_language_folders']);
        
        // Синхронизируем API ключ
        syncFormValues('#openai_api_key', ['#openai_api_key_individual', '#openai_api_key_folders'], 'input');
    },
    
    /**
     * Переключает видимость поля API ключа
     */
    toggleApiKeyField: () => {
        const translationMethod = document.querySelector('input[name="translation_method"]:checked')?.value;
        const apiKeyGroup = document.getElementById('api-key-group');
        
        if (!apiKeyGroup) return;
        
        if (translationMethod === 'openai') {
            apiKeyGroup.style.display = 'block';
        } else {
            apiKeyGroup.style.display = 'none';
        }
    },
    
    /**
     * Обновляет информацию о выбранном OCR-движке
     */
    updateOcrEngineInfo: () => {
        const sourceLangSelect = document.getElementById('source_language');
        if (!sourceLangSelect) return;
        
        const selectedLang = sourceLangSelect.value;
        const langName = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
        
        // Обновляем скрытые поля форм с правильным OCR движком
        const engineInfo = OPTIMAL_OCR_ENGINES[selectedLang] || OPTIMAL_OCR_ENGINES['zh'];
        
        if (document.getElementById('ocr_engine_individual')) {
            document.getElementById('ocr_engine_individual').value = engineInfo.engine;
        }
        
        if (document.getElementById('ocr_engine_folders')) {
            document.getElementById('ocr_engine_folders').value = engineInfo.engine;
        }
        
        // Обновляем информационный текст на странице
        const languageNameEl = document.getElementById('language-name');
        const engineNameEl = document.getElementById('engine-name');
        
        if (languageNameEl) {
            languageNameEl.textContent = langName.toLowerCase();
        }
        
        if (engineNameEl) {
            engineNameEl.textContent = engineInfo.name;
        }
        
        // Показываем предупреждение, если выбран японский язык и не MangaOCR
        const ocrLangWarning = document.getElementById('ocr-lang-warning');
        if (ocrLangWarning) {
            ocrLangWarning.style.display = selectedLang === 'ja' && engineInfo.engine !== 'mangaocr' ? 'block' : 'none';
        }
    }
};

export default TranslationSettings;
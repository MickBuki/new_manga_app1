from . import editor_bp
from flask import render_template, request, send_from_directory
import os
import time
from backend.manga_editor import MangaEditor
from backend.config import get_settings
from backend.auth import api_login_required, login_required, get_current_user

settings = get_settings()
manga_editor = MangaEditor(settings.editor_sessions_dir)

@editor_bp.route('/edit/<session_id>', methods=['GET'])
@login_required
def edit_manga(session_id):
    """Страница редактирования манги"""
    settings = get_settings()
    USE_GPU = settings.use_gpu

    try:
        # Получаем параметры запроса
        direct_mode = request.args.get('direct') == '1'
        use_cache = request.args.get('cache') == '1'
        
        # Всегда перезагружаем данные при переходе по прямой ссылке,
        # чтобы обновить информацию о группе
        force_reload = True
        
        # Засекаем время
        start_time = time.time()
        
        print(f"Запрос редактирования для {session_id} (direct_mode={direct_mode}, use_cache={use_cache}, force_reload={force_reload})")
        
        # Очистка кэша группы, если это требуется
        if request.args.get('clear_cache') == '1':
            print(f"Принудительная очистка кэша для сессии {session_id}")
            manga_editor.clear_session_cache(session_id)
        
        # Получаем данные сессии
        session_data = manga_editor.get_session(session_id, force_reload=force_reload)
        if not session_data:
            return "Сессия не найдена", 404
        
        # Получаем информацию о группе
        group_id = session_data.get('group_id', session_id)
        
        # Проверяем наличие связанных сессий
        all_files = session_data.get('all_files', [])
        has_related = len(all_files) > 1
        
        # Выводим информацию о файлах для отладки
        print(f"Сессия {session_id}, группа {group_id}")
        print(f"Найдено {len(all_files)} файлов в группе. has_related={has_related}")
        for i, file in enumerate(all_files):
            print(f"  {i}: {file['session_id']} - {file['original_filename']} (индекс: {file.get('file_index', 'н/д')})")
        
        # Засекаем время
        load_time = time.time() - start_time
        print(f"Время загрузки сессии: {load_time:.3f} секунд (use_cache={use_cache}, force_reload={force_reload})")
        
        return render_template('edit_manga.html', 
                              session_id=session_id, 
                              session_data=session_data,
                              all_files=all_files,
                              has_related=has_related,
                              direct_mode=direct_mode,
                              load_time=load_time,
                              use_gpu=USE_GPU)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Ошибка загрузки сессии: {str(e)}")
        print(error_traceback)
        return f"Ошибка загрузки сессии: {str(e)}", 500

@editor_bp.route('/static/editor_images/<session_id>/<filename>')
@login_required
def serve_editor_image(session_id, filename):
    """Обслуживание изображений редактора"""
    editor_dir = os.path.join(manga_editor.sessions_dir, session_id)
    return send_from_directory(editor_dir, filename)
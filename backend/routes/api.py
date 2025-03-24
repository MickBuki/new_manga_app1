from . import api_bp
from flask import request, jsonify, send_file
import os
import time
import io
from PIL import Image as PILImage
import uuid
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from backend.manga_editor import MangaEditor

# Инициализация редактора манги
manga_editor = MangaEditor()

@api_bp.route('/edit/update_translation', methods=['POST'])
def api_update_translation():
    """API для обновления переведенного текста и стиля"""
    try:
        data = request.json
        session_id = data.get('session_id')
        block_id = data.get('block_id')
        new_text = data.get('text')
        style = data.get('style')  # Добавлен параметр для стилей
        
        success = manga_editor.update_translation(session_id, block_id, new_text, style)
        if not success:
            return jsonify({"success": False, "error": "Не удалось обновить текст и стиль"}), 400
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/edit/generate_preview', methods=['POST'])
def api_generate_preview():
    """API для генерации предпросмотра с обновленным текстом"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        preview_base64 = manga_editor.generate_preview(session_id)
        if not preview_base64:
            return jsonify({"success": False, "error": "Не удалось создать предпросмотр"}), 400
        
        return jsonify({
            "success": True,
            "preview": preview_base64
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/edit/save', methods=['POST'])
def api_save_edited():
    """API для сохранения отредактированного изображения"""
    try:
        data = request.json
        session_id = data.get('session_id')
        filename = data.get('filename')
        
        success, result = manga_editor.save_edited_image(session_id, filename)
        if not success:
            return jsonify({"success": False, "error": result}), 400
        
        return jsonify({
            "success": True,
            "path": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/download/<format_type>', methods=['POST'])
def api_download_results(format_type):
    """API для скачивания результатов в различных форматах"""
    try:
        data = request.json
        image_paths = data.get('image_paths', [])
        
        if not image_paths:
            return jsonify({"success": False, "error": "Не указаны пути к изображениям"}), 400
        
        # Проверяем существование файлов
        valid_paths = []
        for path in image_paths:
            if os.path.exists(path) and os.path.isfile(path):
                valid_paths.append(path)
            else:
                print(f"Предупреждение: файл {path} не существует или не является файлом")
        
        if not valid_paths:
            return jsonify({"success": False, "error": "Ни один из указанных файлов не существует"}), 400
        
        # Создаем уникальное имя для файла результата
        timestamp = int(time.time())
        result_filename = f"manga_translation_{timestamp}"
        
        if format_type == 'pdf':
            # Создаем PDF из изображений
            pdf_file = create_pdf_from_images(valid_paths, result_filename)
            return send_file(
                pdf_file,
                as_attachment=True,
                download_name=f"{result_filename}.pdf",
                mimetype='application/pdf'
            )
            
        elif format_type == 'zip' or format_type == 'cbz':
            # Создаем ZIP-архив из изображений
            extension = 'cbz' if format_type == 'cbz' else 'zip'
            zip_file = create_zip_from_images(valid_paths, result_filename, extension)
            return send_file(
                zip_file,
                as_attachment=True,
                download_name=f"{result_filename}.{extension}",
                mimetype='application/zip'
            )
            
        elif format_type == 'png':
            # Если запросили конкретное изображение или все в архиве
            if len(valid_paths) == 1:
                return send_file(
                    valid_paths[0],
                    as_attachment=True,
                    download_name=os.path.basename(valid_paths[0]),
                    mimetype='image/png'
                )
            else:
                # Если несколько PNG, упаковываем их в ZIP
                zip_file = create_zip_from_images(valid_paths, result_filename, 'zip')
                return send_file(
                    zip_file,
                    as_attachment=True,
                    download_name=f"{result_filename}_png.zip",
                    mimetype='application/zip'
                )
        else:
            return jsonify({"success": False, "error": f"Неподдерживаемый формат: {format_type}"}), 400
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Ошибка при создании файла для скачивания: {str(e)}")
        print(error_traceback)
        return jsonify({"success": False, "error": str(e)}), 500

def create_pdf_from_images(image_paths, filename):
    """Создает PDF-файл из списка изображений без белых полей"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    # Создаем PDF-документ без указания размера страницы
    c = canvas.Canvas(temp_path)
    
    for img_path in image_paths:
        try:
            # Открываем изображение и определяем его размеры
            img = PILImage.open(img_path)
            img_width, img_height = img.size
            
            # Устанавливаем размер страницы точно по размеру изображения
            c.setPageSize((img_width, img_height))
            
            # Помещаем изображение на страницу без масштабирования, начиная с левого нижнего угла (0,0)
            c.drawImage(img_path, 0, 0, width=img_width, height=img_height)
            c.showPage()  # Завершаем текущую страницу
            
        except Exception as e:
            print(f"Ошибка при добавлении изображения {img_path} в PDF: {e}")
    
    c.save()
    return temp_path

def create_zip_from_images(image_paths, filename, extension='zip'):
    """Создает ZIP-архив из списка изображений"""
    temp_file = tempfile.NamedTemporaryFile(suffix=f'.{extension}', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i, img_path in enumerate(image_paths):
            try:
                # Добавляем изображение в архив с упорядоченным именем
                arcname = f"{i+1:03d}_{os.path.basename(img_path)}"
                zipf.write(img_path, arcname=arcname)
            except Exception as e:
                print(f"Ошибка при добавлении изображения {img_path} в архив: {e}")
    
    return temp_path
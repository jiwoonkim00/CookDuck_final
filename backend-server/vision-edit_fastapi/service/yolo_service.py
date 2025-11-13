from ultralytics import YOLO, settings
import os
import torch
import tempfile
import logging
import time

logger = logging.getLogger(__name__)
settings.update({'sync': False})

class IngredientsDetect():
    def __init__(self, conf=0.7):
        self.model_path = os.getenv('INGREDIENT_MODEL_PATH')
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info("      YOLO 모델 로딩 시작 (device=%s)", self.device)
        load_start = time.perf_counter()
        
        try:
            self.model = YOLO(self.model_path)
        except Exception:
            logger.exception("      YOLO 모델 로딩 실패")
            raise
            
        logger.info("      YOLO 모델 로딩 완료 (%.2f초)", time.perf_counter() - load_start)
        self.conf = conf

    def _prepare_source(self, target):
        cleanup_path = None

        if isinstance(target, str):
            image_path = os.path.abspath(target)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f'이미지 파일을 찾을 수 없습니다: {image_path}')
            return image_path, cleanup_path

        if isinstance(target, (bytes, bytearray)):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(bytes(target))
            temp_file.close()
            cleanup_path = temp_file.name
            return cleanup_path, cleanup_path

        if hasattr(target, 'read'):
            data = target.read()
            if isinstance(data, str):
                data = data.encode('utf-8')
            if hasattr(target, 'seek'):
                target.seek(0)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(data)
            temp_file.close()
            cleanup_path = temp_file.name
            return cleanup_path, cleanup_path

        raise TypeError('이미지 경로, 바이트, 혹은 파일 객체를 입력해야 합니다.')
    
    def _predict_ingredients(self, source):
        try:
            start = time.perf_counter()
            
            results = self.model.predict(
                source=source,
                conf=self.conf,
                device=self.device,
                verbose=False,
                stream=False,
                imgsz=640,
            )
            
            elapsed = time.perf_counter() - start
            logger.info(f"      YOLO 추론 완료 ({elapsed:.2f}초)")
            return results
        except Exception as error:
            logger.error(f"      YOLO 추론 오류: {error}", exc_info=True)
            raise RuntimeError(f'YOLO 추론 중 오류가 발생했습니다: {error}') from error
    
    def _extract_class_names(self, results):
        detected_classes = set()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls)
                    if isinstance(self.model.names, list):
                        class_name = self.model.names[class_id] if class_id < len(self.model.names) else None
                    else:
                        class_name = self.model.names.get(class_id)
                    if class_name:
                        detected_classes.add(class_name)
        
        return detected_classes
    
    def _format_result(self, ingredients):
        unique_ingredients = sorted(set(ingredients))
        message = None
        if not unique_ingredients:
            message = "식재료가 검출되지 않았습니다"
        return {
            'ingredients': unique_ingredients,
            'message': message
        }
    
    def __call__(self, target):
        cleanup_path = None
        
        try:
            source, cleanup_path = self._prepare_source(target)
            
            results = self._predict_ingredients(source)
            detected_classes = self._extract_class_names(results)
            
            if not detected_classes:
                return {
                    'ingredients': [],
                    'message': '식재료가 검출되지 않았습니다'
                }
            
            ingredients = sorted(detected_classes)
            result = self._format_result(ingredients)
            return result
            
        finally:
            if cleanup_path and os.path.exists(cleanup_path):
                try:
                    os.remove(cleanup_path)
                except Exception as e:
                    logger.warning(f"      임시 파일 삭제 실패: {e}")
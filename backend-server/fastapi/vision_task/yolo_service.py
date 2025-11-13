from ultralytics import YOLO, settings
import os
import torch
import tempfile
import logging
import time
"""
    YOLO 식재료 탐지 파일
"""

logger = logging.getLogger(__name__)
settings.update({'sync': False})

# OpenMP/BLAS 다중 쓰레드로 인한 충돌을 피하기 위한 기본 제한
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_LIBRARY", "serial")
os.environ.setdefault("KMP_BLOCKTIME", "0")
os.environ.setdefault("KMP_SETTINGS", "TRUE")
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")
os.environ.setdefault("KMP_AFFINITY", "disabled")

try:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except Exception:
    logger.warning("PyTorch 쓰레드 제한 설정 실패", exc_info=True)

class IngredientsDetect():
    def __init__(self, conf=0.25):  # confidence를 0.7에서 0.25로 낮춤 (더 많은 재료 탐지)
        self.model_path = os.getenv('INGREDIENT_MODEL_PATH')
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info("YOLO 모델 로딩 시작 (device=%s, conf=%.2f)", self.device, conf)
        load_start = time.perf_counter()
        
        try:
            self.model = YOLO(self.model_path)
        except Exception:
            logger.exception("YOLO 모델 로딩 실패")
            raise
            
        logger.info("YOLO 모델 로딩 완료 (%.2f초)", time.perf_counter() - load_start)
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
            logger.info(f"YOLO 추론 완료 ({elapsed:.2f}초)")
            return results
        except Exception as error:
            logger.error(f"YOLO 추론 오류: {error}", exc_info=True)
            raise RuntimeError(f'YOLO 추론 중 오류가 발생했습니다: {error}') from error
    
    def _extract_class_names(self, results):
        detected_classes = set()
        detected_with_conf = []
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls)
                    confidence = float(box.conf)
                    if isinstance(self.model.names, list):
                        class_name = self.model.names[class_id] if class_id < len(self.model.names) else None
                    else:
                        class_name = self.model.names.get(class_id)
                    if class_name:
                        detected_classes.add(class_name)
                        detected_with_conf.append((class_name, confidence))
        
        # 탐지된 재료와 confidence 로깅
        if detected_with_conf:
            logger.info(f"YOLO 탐지 결과: {len(detected_classes)}개 재료")
            for name, conf in sorted(detected_with_conf, key=lambda x: x[1], reverse=True):
                logger.debug(f"  - {name}: {conf:.2f}")
        
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
                    logger.warning(f"임시 파일 삭제 실패: {e}")
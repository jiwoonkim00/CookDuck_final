import os
import logging
from typing import Iterable, Union, Dict, Any, List

from yolo_service import IngredientsDetect
from gptVlm_service import GptVlmIngredientExtractor

logger = logging.getLogger(__name__)


class IngredientDetectionPipeline:
    def __init__(
        self,
        yolo_detector: IngredientsDetect | None = None,
        vlm_detector: GptVlmIngredientExtractor | None = None,
    ):
        self.yolo_detector = yolo_detector or IngredientsDetect()
        self.vlm_detector = vlm_detector or GptVlmIngredientExtractor()

    def _to_bytes(self, target: Union[str, bytes, bytearray, Iterable[bytes]]) -> bytes:
        if isinstance(target, str):
            image_path = os.path.abspath(target)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f'이미지 파일을 찾을 수 없습니다: {image_path}')
            with open(image_path, 'rb') as image_file:
                return image_file.read()

        if isinstance(target, (bytes, bytearray)):
            return bytes(target)

        if hasattr(target, 'read'):
            data = target.read()
            if isinstance(data, str):
                data = data.encode('utf-8')
            if hasattr(target, 'seek'):
                target.seek(0)
            return data

        raise TypeError('이미지 경로, 바이트, 혹은 파일 객체를 입력해야 합니다.')

    def detect(self, target: Union[str, bytes, bytearray, Iterable[bytes]]) -> Dict[str, Any]:
        payload = self._to_bytes(target)

        # YOLO로 먼저 검출 (영어 클래스명)
        yolo_full_result = self.yolo_detector(payload)
        yolo_ingredients_en = yolo_full_result.get('ingredients') or []
        
        # YOLO 결과를 VLM에 전달하여 한국어로 번역 + 추가 검출
        vlm_full_result = self.vlm_detector(payload, yolo_results=yolo_ingredients_en)
        vlm_ingredients_kr = vlm_full_result.get('ingredients') or []
        
        # VLM 결과가 최종 한국어 결과 (YOLO 번역 + VLM 추가 검출)
        final_ingredients = vlm_ingredients_kr
        
        logger.info(f"      YOLO: {len(yolo_ingredients_en)}개 검출 (영어)")
        logger.info(f"      VLM:  {len(vlm_ingredients_kr)}개 변환 (한국어)")
        logger.info(f"      최종: {len(final_ingredients)}개")
        
        message = None
        if not final_ingredients:
            message = 'YOLO와 GPT VLM 모두 식재료를 검출하지 못했습니다.'

        return {
            'ingredients': final_ingredients,
            'count': len(final_ingredients),
            'message': message,
            'details': {
                'yolo': {
                    'count': len(yolo_ingredients_en),
                    'items': yolo_ingredients_en,
                    'message': yolo_full_result.get('message')
                },
                'vlm': {
                    'count': len(vlm_ingredients_kr),
                    'items': vlm_ingredients_kr,
                    'message': vlm_full_result.get('message'),
                    'raw_text': vlm_full_result.get('raw_text', '')
                }
            }
        }

    def __call__(self, target: Union[str, bytes, bytearray, Iterable[bytes]]) -> Dict[str, Any]:
        return self.detect(target)
import os
import logging
from typing import Iterable, Union, Dict, Any, List

from .yolo_service import IngredientsDetect
from .gptVlm_service import GptVlmIngredientExtractor

logger = logging.getLogger(__name__)
"""
    두 모델 처리 과정 통합 파이프라인
"""

class IngredientDetectionPipeline:
    def __init__(
        self,
        # yolo_detector: IngredientsDetect | None = None,
        # vlm_detector: GptVlmIngredientExtractor | None = None,
        yolo_detector: Union[IngredientsDetect, None] = None,
        vlm_detector: Union[GptVlmIngredientExtractor, None] = None,
    ):
        self.yolo_detector = yolo_detector or IngredientsDetect()
        self.vlm_detector = vlm_detector  # None일 수 있음 (VLM 없이 YOLO만 사용)

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
        
        # VLM이 있으면 사용, 없으면 YOLO 결과를 간단한 매핑으로 한국어 변환
        if self.vlm_detector is not None:
            # YOLO 결과를 VLM에 전달하여 한국어로 번역 + 추가 검출
            try:
                vlm_full_result = self.vlm_detector(payload, yolo_results=yolo_ingredients_en)
                vlm_ingredients_kr = vlm_full_result.get('ingredients') or []
            except Exception as e:
                logger.warning(f"VLM 처리 중 오류 발생, YOLO 결과만 사용: {e}")
                vlm_ingredients_kr = self._translate_yolo_to_korean(yolo_ingredients_en)
        else:
            # VLM이 없으면 YOLO 결과를 간단한 매핑으로 한국어 변환
            vlm_ingredients_kr = self._translate_yolo_to_korean(yolo_ingredients_en)
            vlm_full_result = {
                'ingredients': vlm_ingredients_kr,
                'message': 'VLM 없이 YOLO 결과만 사용',
                'raw_text': ''
            }
        
        # VLM 결과가 최종 한국어 결과 (YOLO 번역 + VLM 추가 검출)
        final_ingredients = vlm_ingredients_kr
        
        logger.info(f"YOLO: {len(yolo_ingredients_en)}개 검출 (영어)")
        logger.info(f"VLM:  {len(vlm_ingredients_kr)}개 변환 (한국어)")
        logger.info(f"최종: {len(final_ingredients)}개")
        
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
                    'message': vlm_full_result.get('message', ''),
                    'raw_text': vlm_full_result.get('raw_text', '')
                }
            }
        }
    
    def _translate_yolo_to_korean(self, yolo_ingredients_en: List[str]) -> List[str]:
        """YOLO 영어 결과를 간단한 매핑으로 한국어 변환"""
        # 기본 영어-한국어 매핑 (일반적인 식재료)
        translation_map = {
            # 채소류
            'carrot': '당근',
            'onion': '양파',
            'green onion': '대파',
            'spring onion': '대파',
            'scallion': '대파',
            'potato': '감자',
            'tomato': '토마토',
            'cucumber': '오이',
            'pepper': '고추',
            'bell pepper': '피망',
            'red pepper': '고추',
            'green pepper': '고추',
            'garlic': '마늘',
            'ginger': '생강',
            'cabbage': '양배추',
            'lettuce': '상추',
            'spinach': '시금치',
            'mushroom': '버섯',
            'eggplant': '가지',
            'zucchini': '호박',
            'pumpkin': '호박',
            'broccoli': '브로콜리',
            'cauliflower': '콜리플라워',
            'radish': '무',
            'daikon': '무',
            'celery': '셀러리',
            'corn': '옥수수',
            # 과일류
            'orange': '오렌지',
            'apple': '사과',
            'banana': '바나나',
            'strawberry': '딸기',
            'grape': '포도',
            'watermelon': '수박',
            # 육류/해산물
            'egg': '달걀',
            'chicken': '닭고기',
            'pork': '돼지고기',
            'beef': '소고기',
            'fish': '생선',
            'shrimp': '새우',
            'squid': '오징어',
            'octopus': '문어',
            # 기타
            'tofu': '두부',
            'cheese': '치즈',
            'milk': '우유',
            'bread': '빵',
            'rice': '쌀',
            'noodle': '면',
            'pasta': '파스타',
            'noodles': '면',
        }
        
        korean_ingredients = []
        for ing_en in yolo_ingredients_en:
            ing_lower = ing_en.lower().strip()
            # 매핑에 있으면 변환, 없으면 원본 사용
            korean = translation_map.get(ing_lower, ing_en)
            if korean not in korean_ingredients:
                korean_ingredients.append(korean)
        
        return korean_ingredients

    def __call__(self, target: Union[str, bytes, bytearray, Iterable[bytes]]) -> Dict[str, Any]:
        return self.detect(target)
from pathlib import Path
import sys
import logging
import time
from typing import Union, Iterable, Dict, Any

DETECT_TASK_DIR = Path(__file__).resolve().parent.parent / "service"

if DETECT_TASK_DIR.exists() and str(DETECT_TASK_DIR) not in sys.path:
    sys.path.append(str(DETECT_TASK_DIR))

from yolo_service import IngredientsDetect
from gptVlm_service import GptVlmIngredientExtractor
from fusion_service import IngredientDetectionPipeline

_pipeline: IngredientDetectionPipeline | None = None

logger = logging.getLogger(__name__)


def get_pipeline() -> IngredientDetectionPipeline:
    global _pipeline
    if _pipeline is None:
        logger.info("      비전 파이프라인 초기화 시작")
        start = time.perf_counter()
        try:
            _pipeline = IngredientDetectionPipeline(
                yolo_detector=IngredientsDetect(),
                vlm_detector=GptVlmIngredientExtractor(),
            )
            logger.info("      비전 파이프라인 초기화 완료 (%.2f초)", time.perf_counter() - start)
        except Exception as e:
            logger.exception("      비전 파이프라인 초기화 실패")
            raise RuntimeError(f"비전 파이프라인 초기화 실패: {e}") from e
    else:
        logger.debug("      기존 파이프라인 재사용")
    return _pipeline


def detect_ingredients(image_payload: Union[str, bytes, bytearray, Iterable[bytes]]) -> Dict[str, Any]:
    try:
        start = time.perf_counter()
        
        pipeline = get_pipeline()
        result = pipeline(image_payload)
        
        elapsed = time.perf_counter() - start
        logger.info(f"      전체 처리 시간: {elapsed:.2f}초")
        
        return result
        
    except Exception as e:
        logger.error(f"      탐지 오류: {e}")
        return {
            "ingredients": [],
            "message": f"탐지 중 오류 발생: {str(e)}",
            "error": str(e),
            "yolo": {"count": 0, "message": "오류"},
            "vlm": {"count": 0, "message": "오류"}
        }
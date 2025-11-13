from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# uvicorn app.vision_api:router --host 0.0.0.0 --port 8008
"""
    비전 파이프라인 테스트용 API /test로 시작하는 API는 모두 테스트용임
"""
@router.get("/test/health")
def vision_health_check():
    logger.info("/vision/test/health 호출")

    try:
        from .vision_pipeline import get_pipeline
        pipeline = get_pipeline()
        return {
            "status": "GOOD",
            "message": "비전 파이프라인 정상 작동 중",
            "yolo_loaded": pipeline.yolo_detector is not None,
            "vlm_loaded": pipeline.vlm_detector is not None
        }
    except Exception as e:
        return {
            "status": "BAD",
            "message": str(e)
        }

@router.post("/test/img_upload")
async def test_file_upload(file: UploadFile = File(...)):
    logger.info("=" * 60)
    logger.info("/vision/test/img_upload 호출")
    logger.info(f"파일: {file.filename} ({file.content_type})")
    
    try:
        image_bytes = await file.read()
        logger.info(f"크기: {len(image_bytes)} bytes")
        
        return {
            "status": "success",
            "message": "파일 업로드 정상",
            "filename": file.filename,
            "size": len(image_bytes),
            "content_type": file.content_type
        }
    except Exception as e:
        logger.error(f"오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
        logger.info("=" * 60)

@router.post("/test/yolo")
def test_yolo_only(file: UploadFile = File(...)):
    import time
    
    logger.info("=" * 60)
    logger.info("YOLO 단독 테스트 시작")
    
    try:
        image_bytes = file.file.read()
        logger.info(f"이미지 크기: {len(image_bytes)} bytes")
        
        from .vision_pipeline import get_pipeline
        pipeline = get_pipeline()
        
        logger.info("YOLO 추론 시작")
        start_time = time.perf_counter()
        
        yolo_result = pipeline.yolo_detector(image_bytes)
        
        elapsed = time.perf_counter() - start_time
        logger.info(f"YOLO 추론 완료 ({elapsed:.2f}초)")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "yolo_result": yolo_result,
            "elapsed_time": round(elapsed, 2)
        }
    except Exception as e:
        logger.error(f"YOLO 오류: {e}", exc_info=True)
        logger.error("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()

@router.post("/test/vlm")
def test_vlm_only(file: UploadFile = File(...)):
    logger.info("VLM 단독 테스트 시작")
    
    try:
        image_bytes = file.file.read()
        logger.info(f"이미지 크기: {len(image_bytes)} bytes")
        
        from .vision_pipeline import get_pipeline
        pipeline = get_pipeline()
        
        vlm_result = pipeline.vlm_detector(image_bytes)
        
        return {
            "status": "success",
            "vlm_result": vlm_result
        }
    except Exception as e:
        logger.error(f"VLM 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()


"""
    식재료 검출 요청 -> 이미지 업로드 -> YOLO 영어 검출 후 텍스트 VLM 전달 ->
    VLM 역할: YOLO 검출 결과 번역 + YOLO가 놓친 식재료 추가 검출 ->
    최종적으로 한국어 재료 문자열 반환
"""
@router.post("/detect")
def detect_ingredients(file: UploadFile = File(...)) -> dict:
    from .vision_pipeline import detect_ingredients as run_vision_pipeline
    
    logger.info("=" * 60)
    logger.info(f"파일: {file.filename} ({file.content_type})")
    
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            logger.warning(f"잘못된 파일 타입: {file.content_type}")
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        image_bytes = file.file.read()
        
        if len(image_bytes) == 0:
            logger.error("빈 파일")
            raise HTTPException(status_code=400, detail="빈 파일이 업로드되었습니다.")
        
        logger.info(f"이미지 크기: {len(image_bytes)} bytes")
        
        detection = run_vision_pipeline(image_bytes)
        
        ingredients = detection.get("ingredients") or []
        logger.info(f"완료: 총 {len(ingredients)}개 검출")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "pipeline": detection
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"오류: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500, 
            detail=f"식재료 추론 중 오류가 발생했습니다: {str(e)}"
        )
    finally:
        file.file.close()

@router.post("/predict")
def predict_ingredients(
    file: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
) -> list:
    """
    프론트엔드 호환용 predict 엔드포인트
    재료 리스트만 반환 (List[str])
    """
    from .a_vision_pipeline import detect_ingredients as run_vision_pipeline
    
    upload = file or image
    if upload is None:
        raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다.")
    
    field_name = "file" if upload is file else "image"
    logger.info("=" * 60)
    logger.info(f"/predict 호출 - 필드: {field_name}, 파일: {upload.filename} ({upload.content_type})")
    
    try:
        # content_type 검증: image/로 시작하거나 application/octet-stream 허용
        # (Flutter에서 때때로 octet-stream으로 전송함)
        content_type = upload.content_type or ""
        is_valid_image = (
            content_type.startswith('image/') or 
            content_type == 'application/octet-stream' or
            content_type == ''
        )
        
        # 파일 확장자도 확인
        filename = upload.filename or ""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        has_valid_extension = any(filename.lower().endswith(ext) for ext in valid_extensions)
        
        if not is_valid_image and not has_valid_extension:
            logger.warning(f"잘못된 파일 타입: {content_type}, 파일명: {filename}")
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        image_bytes = upload.file.read()
        
        if len(image_bytes) == 0:
            logger.error("빈 파일")
            raise HTTPException(status_code=400, detail="빈 파일이 업로드되었습니다.")
        
        logger.info(f"이미지 크기: {len(image_bytes)} bytes")
        
        detection = run_vision_pipeline(image_bytes)
        
        ingredients = detection.get("ingredients") or []
        logger.info(f"완료: 총 {len(ingredients)}개 검출")
        logger.info("=" * 60)
        
        # 프론트엔드가 기대하는 형식: 재료 리스트만 반환
        return ingredients
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"오류: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500, 
            detail=f"식재료 추론 중 오류가 발생했습니다: {str(e)}"
        )
    finally:
        if file is not None:
            file.file.close()
        if image is not None and image is not file:
            image.file.close()
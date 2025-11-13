"""
요리 세션 API 엔드포인트
사용자와의 대화형 요리 가이드 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import httpx
import os

from .cook_session import (
    session_manager, 
    constraint_parser, 
    rule_modifier,
    Constraint,
    SessionState
)

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(prefix="/cook", tags=["Cook"])

# 요청 모델들
class SelectRecipeRequest(BaseModel):
    user_id: str
    recipe_id: int

class AddConstraintRequest(BaseModel):
    user_id: str
    message: str
    parsed_constraints: Optional[List[Constraint]] = None

class NextStepRequest(BaseModel):
    user_id: str

class GetCurrentStepRequest(BaseModel):
    user_id: str

# 응답 모델들
class SessionResponse(BaseModel):
    success: bool
    message: str
    session: Optional[SessionState] = None

class StepResponse(BaseModel):
    success: bool
    step_index: int
    original_step: str
    modified_step: str
    applied_constraints: List[Constraint]
    tips: Optional[str] = None

@router.post("/select", response_model=SessionResponse)
async def select_recipe(req: SelectRecipeRequest):
    """레시피 선택 및 세션 생성"""
    try:
        session = session_manager.create_session(req.user_id, req.recipe_id)
        
        # 레시피 데이터 로드 (실제로는 DB에서)
        recipe_data = await load_recipe_data(req.recipe_id)
        session.recipe_data = recipe_data
        
        return SessionResponse(
            success=True,
            message=f"레시피 '{recipe_data.get('title', 'Unknown')}' 선택됨",
            session=session
        )
    except Exception as e:
        logger.error(f"레시피 선택 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레시피 선택 실패: {str(e)}")

@router.post("/constraint", response_model=SessionResponse)
async def add_constraint(req: AddConstraintRequest):
    """제약사항 추가"""
    try:
        session = session_manager.get_session(req.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 자연어 파싱 또는 직접 제약사항 사용
        if req.parsed_constraints:
            constraints = req.parsed_constraints
        else:
            constraints = constraint_parser.parse_message(req.message)
        
        # 제약사항 추가
        for constraint in constraints:
            session_manager.add_constraint(req.user_id, constraint)
        
        return SessionResponse(
            success=True,
            message=f"{len(constraints)}개 제약사항 추가됨",
            session=session
        )
    except Exception as e:
        logger.error(f"제약사항 추가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"제약사항 추가 실패: {str(e)}")

@router.post("/next", response_model=StepResponse)
async def next_step(req: NextStepRequest):
    """다음 단계로 이동"""
    try:
        session = session_manager.get_session(req.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        if not session.recipe_data:
            raise HTTPException(status_code=400, detail="레시피 데이터가 없습니다")
        
        # 현재 단계 텍스트 가져오기
        steps = session.recipe_data.get('instructions', [])
        if session.current_step >= len(steps):
            raise HTTPException(status_code=400, detail="모든 단계를 완료했습니다")
        
        original_step = steps[session.current_step]
        
        # 룰 기반 수정 적용
        modification_result = rule_modifier.apply_modifications(
            original_step, 
            session.constraints
        )
        
        # LLM을 통한 자연어 보정
        modified_step = await generate_modified_step_with_llm(
            session.recipe_data.get('title', ''),
            session.current_step,
            original_step,
            session.constraints
        )
        
        # 다음 단계로 이동
        session.current_step += 1
        
        return StepResponse(
            success=True,
            step_index=session.current_step - 1,
            original_step=original_step,
            modified_step=modified_step,
            applied_constraints=session.constraints
        )
    except Exception as e:
        logger.error(f"다음 단계 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"다음 단계 실패: {str(e)}")

@router.get("/current", response_model=StepResponse)
async def get_current_step(user_id: str):
    """현재 단계 조회"""
    try:
        session = session_manager.get_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        if not session.recipe_data:
            raise HTTPException(status_code=400, detail="레시피 데이터가 없습니다")
        
        steps = session.recipe_data.get('instructions', [])
        if session.current_step >= len(steps):
            raise HTTPException(status_code=400, detail="모든 단계를 완료했습니다")
        
        original_step = steps[session.current_step]
        
        # LLM을 통한 자연어 보정
        modified_step = await generate_modified_step_with_llm(
            session.recipe_data.get('title', ''),
            session.current_step,
            original_step,
            session.constraints
        )
        
        return StepResponse(
            success=True,
            step_index=session.current_step,
            original_step=original_step,
            modified_step=modified_step,
            applied_constraints=session.constraints
        )
    except Exception as e:
        logger.error(f"현재 단계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"현재 단계 조회 실패: {str(e)}")

@router.delete("/session/{user_id}")
async def clear_session(user_id: str):
    """세션 삭제"""
    try:
        success = session_manager.clear_session(user_id)
        if success:
            return {"success": True, "message": "세션이 삭제되었습니다"}
        else:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"세션 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 삭제 실패: {str(e)}")

# 헬퍼 함수들
async def load_recipe_data(recipe_id: int) -> Dict:
    """레시피 데이터 로드 (FAISS 벡터DB에서)"""
    try:
        from .rag_chain import chain
        
        # FAISS에서 레시피 ID로 검색
        all_recipes = chain.all_recipes
        if not all_recipes:
            raise Exception("레시피 데이터가 로드되지 않았습니다")
        
        # 레시피 ID로 검색
        target_recipe = None
        for recipe in all_recipes:
            if recipe.get('id') == recipe_id:
                target_recipe = recipe
                break
        
        if not target_recipe:
            raise Exception(f"레시피 ID {recipe_id}를 찾을 수 없습니다")
        
        # 조리법을 단계별로 분리
        content = target_recipe.get('content', '')
        instructions = []
        
        if content:
            # 줄바꿈으로 분리하고 번호가 있는 단계들만 추출
            lines = content.split('\n')
            step_num = 1
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # 빈 줄과 주석 제외
                    instructions.append(f"{step_num}. {line}")
                    step_num += 1
        
        # 재료 리스트 파싱
        ingredients_str = target_recipe.get('ingredients', '')
        ingredients = []
        if ingredients_str:
            ingredients = [ing.strip() for ing in ingredients_str.split(',') if ing.strip()]
        
        return {
            "id": recipe_id,
            "title": target_recipe.get('title', 'Unknown'),
            "instructions": instructions,
            "ingredients": ingredients,
            "content": content
        }
        
    except Exception as e:
        logger.error(f"레시피 데이터 로드 실패: {str(e)}")
        # 폴백: 기본 데이터
        return {
            "id": recipe_id,
            "title": "김치볶음밥",
            "instructions": [
                "1. 김치를 잘게 썰어 준비합니다",
                "2. 팬에 기름을 두르고 김치를 볶습니다", 
                "3. 밥을 넣고 볶아줍니다",
                "4. 계란을 풀어서 넣고 볶아줍니다",
                "5. 참기름과 깨를 뿌려 완성합니다"
            ],
            "ingredients": ["김치", "계란", "밥", "참기름", "깨"]
        }

async def generate_modified_step_with_llm(
    recipe_title: str,
    step_index: int,
    original_step: str,
    constraints: List[Constraint]
) -> str:
    """LLM을 사용하여 수정된 단계 생성 (Hugging Face 모델 사용)"""
    try:
        from .llm_service import get_llm_service
        
        # 제약사항을 텍스트로 변환
        constraints_text = ", ".join([
            f"{c.type}: {c.action}" + (f" ({c.degree})" if c.degree else "")
            for c in constraints
        ])
        
        prompt = f"""너는 한국 요리 도우미 셰프야. 사용자의 즉석 요구를 반영해 현재 단계만 안전하게 수정하되, 재료/비율/불 세기/타이밍을 구체적으로 제시해.

레시피 제목: {recipe_title}
현재 단계 번호: {step_index}
원문 단계: {original_step}

사용자 요구(누적): {constraints_text}

주어진 요구를 반영하여, "수정된 단계"만 2~3문장으로 출력하고, 가능하면 대체재 1가지와 주의사항 1가지를 덧붙여줘."""
        
        # LLM 서비스 호출
        llm_service = get_llm_service()
        modified_step = llm_service.generate(
            prompt=prompt,
            max_length=256,
            temperature=0.7
        )
        
        return modified_step if modified_step else original_step
                
    except Exception as e:
        logger.error(f"LLM 요청 오류: {str(e)}")
        # LLM 실패 시 룰 기반 결과 반환
        return f"{original_step} (사용자 요구사항이 반영되었습니다: {', '.join([c.type for c in constraints])})"

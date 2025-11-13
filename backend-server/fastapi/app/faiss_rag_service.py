"""
FAISS + RAG 통합 서비스
FAISS로 레시피 검색 후, LLM으로 추천 문구 생성
"""

import logging
from typing import List, Dict, Optional
import httpx
import os

logger = logging.getLogger(__name__)

# AI 서버 URL (환경변수에서 가져오거나 기본값 사용)
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://203.252.240.65:8001")


async def enhance_recipes_with_llm(
    recipes: List[Dict],
    user_ingredients: List[str],
    top_n: Optional[int] = None
) -> List[Dict]:
    """
    FAISS로 검색된 레시피에 LLM 기반 추천 문구 추가 (RAG)
    
    Args:
        recipes: FAISS로 검색된 레시피 목록
        user_ingredients: 사용자 보유 재료
        top_n: LLM으로 설명을 생성할 상위 레시피 개수 (None이면 전체 처리)
    
    Returns:
        LLM 설명이 추가된 레시피 목록
    """
    if not recipes:
        return recipes
    
    # top_n이 지정되지 않으면 전체 레시피 처리
    if top_n is None:
        recipes_to_enhance = recipes
    else:
        recipes_to_enhance = recipes[:top_n]
    
    enhanced_recipes = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 병렬 처리를 위한 태스크 리스트
            tasks = []
            
            # 각 레시피에 대한 비동기 처리 함수
            async def process_recipe(r: Dict) -> Dict:
                try:
                    # 레시피 정보 추출
                    title = r.get("title", "")
                    ingredients = r.get("ingredients", "")
                    matched_ingredients = r.get("matched_ingredients", [])
                    
                    # LLM 프롬프트 생성
                    prompt = f"""사용자가 보유한 재료: {', '.join(user_ingredients)}

레시피 정보:
- 제목: {title}
- 재료: {ingredients}
- 매칭된 재료: {', '.join(matched_ingredients) if matched_ingredients else '없음'}

위 레시피를 사용자의 보유 재료를 고려하여 2-3문장으로 추천 문구를 작성해주세요.
예시: "이 레시피는 보유하신 [재료명]을 활용하여 만들 수 있습니다. [특징 설명]"
간결하고 친근한 톤으로 작성해주세요."""

                    # LLM 호출
                    response = await client.post(
                        f"{AI_SERVER_URL}/llm-generate",
                        json={"prompt": prompt}
                    )
                    response.raise_for_status()
                    llm_response = response.json()
                    recommendation_text = llm_response.get("response", "")
                    
                    # 레시피에 LLM 설명 추가
                    r["recommendation_text"] = recommendation_text
                    r["enhanced"] = True
                    
                except Exception as e:
                    logger.warning(f"레시피 '{r.get('title', 'Unknown')}' LLM 처리 실패: {e}")
                    r["recommendation_text"] = ""
                    r["enhanced"] = False
                
                return r
            
            # 모든 레시피에 대해 태스크 생성 (클로저 문제 방지를 위해 recipe를 직접 전달)
            for recipe in recipes_to_enhance:
                tasks.append(process_recipe(recipe))
            
            # 모든 레시피를 병렬로 처리 (예외 발생 시에도 계속 처리)
            import asyncio
            enhanced_recipes = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외가 발생한 경우 처리
            valid_recipes = []
            for result in enhanced_recipes:
                if isinstance(result, Exception):
                    logger.warning(f"레시피 처리 중 예외 발생: {result}")
                    continue
                valid_recipes.append(result)
            enhanced_recipes = valid_recipes
            
            # top_n이 지정된 경우 나머지 레시피 추가
            if top_n is not None and top_n < len(recipes):
                for recipe in recipes[top_n:]:
                    recipe["recommendation_text"] = ""
                    recipe["enhanced"] = False
                    enhanced_recipes.append(recipe)
    
    except Exception as e:
        logger.error(f"LLM 처리 중 오류: {e}")
        # LLM 실패 시 원본 레시피 반환 (recommendation_text는 빈 문자열)
        for recipe in recipes:
            if "recommendation_text" not in recipe:
                recipe["recommendation_text"] = ""
                recipe["enhanced"] = False
        return recipes
    
    return list(enhanced_recipes)


def create_rag_prompt_for_recipes(
    recipes: List[Dict],
    user_ingredients: List[str]
) -> str:
    """
    여러 레시피를 한 번에 LLM에 전달하는 프롬프트 생성
    """
    recipes_text = ""
    for i, recipe in enumerate(recipes[:5], 1):  # 상위 5개만
        title = recipe.get("title", "")
        ingredients = recipe.get("ingredients", "")
        matched = recipe.get("matched_ingredients", [])
        
        recipes_text += f"""
{i}. {title}
   - 재료: {ingredients}
   - 매칭된 재료: {', '.join(matched) if matched else '없음'}
"""
    
    prompt = f"""사용자가 보유한 재료: {', '.join(user_ingredients)}

다음은 보유 재료로 만들 수 있는 레시피 목록입니다:

{recipes_text}

각 레시피에 대해 사용자의 보유 재료를 고려한 2-3문장 추천 문구를 작성해주세요.
각 레시피마다 번호와 함께 작성해주세요.
예시:
1. [레시피명]: 이 레시피는 보유하신 [재료명]을 활용하여...
2. [레시피명]: [추천 문구]...

간결하고 친근한 톤으로 작성해주세요."""
    
    return prompt


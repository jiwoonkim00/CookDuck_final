"""
RAG 프롬프트 사용 예시
실제 사용 방법을 보여주는 예제 코드
"""

from .rag_prompt_builder import (
    build_llama3_2_prompt,
    create_system_prompt,
    create_step_prompt,
    create_greeting_user_prompt,
    create_next_step_user_prompt
)


# ============================================================
# 예시 1: 2단계 - 대화 시작 (인사말 받기)
# ============================================================

def example_greeting_prompt(recipe_id: int):
    """
    레시피 선택 후 인사말 생성용 프롬프트 생성 예시
    """
    # 레시피 데이터 (실제로는 DB에서 가져옴)
    recipe_json = {
        "title": "나물비빔밥",
        "ingredients": ["쌀", "안심", "콩나물", "청포묵", "미나리"],
        "steps": [
            "1. 양지머리로 육수를 낸 후 식혀 기름을 걷어낸 후, 불린 쌀을 넣어 고슬고슬하게 밥을 짓는다.",
            "2. 안심은 얇게 썰어 소금, 후추로 밑간을 한 뒤 팬에 볶는다.",
            "3. 콩나물은 데쳐서 물기를 제거하고, 청포묵은 끓는 물에 데쳐서 썬다.",
            "4. 미나리는 다듬어서 씻고, 고사리는 데쳐서 물기를 제거한다.",
            "5. 밥 위에 나물들을 예쁘게 담고, 고추장 양념장을 곁들여 낸다."
        ],
        "content": "전체 조리법 내용..."
    }
    
    # 1. 시스템 프롬프트 생성
    system_prompt = create_system_prompt(recipe_json)
    
    # 2. 사용자 프롬프트 (인사말 트리거)
    user_prompt = create_greeting_user_prompt()
    
    # 3. 최종 프롬프트 생성
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    
    # 4. ai서버에 전송할 준비 완료
    # 이제 final_prompt를 ai서버의 /llm-generate에 전송하면 됨
    return final_prompt


# ============================================================
# 예시 2: 3단계 - 대화 루프 (다음 단계 요청)
# ============================================================

def example_next_step_prompt(recipe_json: Dict, current_step_index: int):
    """
    다음 단계 요청용 프롬프트 생성 예시
    """
    # 현재 단계 텍스트 가져오기
    steps = recipe_json.get("steps", [])
    if current_step_index >= len(steps):
        return None  # 모든 단계 완료
    
    current_step_text = steps[current_step_index]
    
    # 1. 단계 안내용 시스템 프롬프트 생성
    system_prompt = create_step_prompt(
        recipe_json, 
        current_step_index, 
        current_step_text
    )
    
    # 2. 사용자 프롬프트 ("다음")
    user_prompt = create_next_step_user_prompt()
    
    # 3. 최종 프롬프트 생성
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    
    # 4. ai서버에 전송할 준비 완료
    return final_prompt


# ============================================================
# 실제 사용 예시 (WebSocket이나 API에서 사용)
# ============================================================

async def generate_greeting_with_rag(recipe_id: int, ai_server_url: str):
    """
    레시피 선택 후 인사말 생성 (RAG 프롬프트 사용)
    """
    import httpx
    
    # 레시피 데이터 로드 (실제로는 DB에서)
    recipe_json = await load_recipe_data(recipe_id)
    
    # 프롬프트 생성
    system_prompt = create_system_prompt({
        "title": recipe_json.get("title"),
        "ingredients": recipe_json.get("ingredients", []),
        "steps": recipe_json.get("instructions", []),
        "content": recipe_json.get("content", "")
    })
    user_prompt = create_greeting_user_prompt()
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    
    # ai서버에 전송
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{ai_server_url}/llm-generate",
            json={"prompt": final_prompt}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


async def generate_next_step_with_rag(
    recipe_json: Dict, 
    current_step_index: int, 
    ai_server_url: str
):
    """
    다음 단계 안내 생성 (RAG 프롬프트 사용)
    """
    import httpx
    
    steps = recipe_json.get("steps", recipe_json.get("instructions", []))
    if current_step_index >= len(steps):
        return None
    
    current_step_text = steps[current_step_index]
    
    # 프롬프트 생성
    system_prompt = create_step_prompt(
        recipe_json,
        current_step_index,
        current_step_text
    )
    user_prompt = create_next_step_user_prompt()
    final_prompt = build_llama3_2_prompt(system_prompt, user_prompt)
    
    # ai서버에 전송
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{ai_server_url}/llm-generate",
            json={"prompt": final_prompt}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


# 헬퍼 함수 (실제 구현 필요)
async def load_recipe_data(recipe_id: int) -> Dict:
    """레시피 데이터 로드 (실제로는 DB에서)"""
    # 실제 구현은 cook_api.py의 load_recipe_data 참고
    pass


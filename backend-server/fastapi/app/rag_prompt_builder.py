"""
RAG 프롬프트 구성 모듈
Llama 3.2 형식의 프롬프트를 생성하는 유틸리티
사용자 맞춤화 기능 (제약사항 반영) 포함
"""

from typing import List, Dict, Optional


def build_llama3_2_prompt(system_prompt: str, user_prompt: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Llama 3.2 공식 프롬프트 형식으로 '완성된' 문자열을 만듭니다.
    ai서버의 /llm-generate 엔드포인트에 전송할 최종 프롬프트입니다.
    
    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 사용자 프롬프트
        chat_history: 이전 대화 기록 (선택적)
    
    Returns:
        완성된 Llama 3.2 형식 프롬프트 문자열
    """
    
    # 1. 시스템 프롬프트 포장
    prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    
    # 2. (선택적) 이전 대화 기록 포장
    if chat_history:
        for turn in chat_history:
            # turn = {"role": "user", "content": "..."}
            # turn = {"role": "assistant", "content": "..."}
            role = turn.get("role", "user")
            content = turn.get("content", "")
            prompt_str += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
    
    # 3. 현재 사용자 질문 포장
    prompt_str += f"<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>"
    
    # 4. LLM이 응답을 시작할 부분
    prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    
    return prompt_str


def create_system_prompt(recipe_json: Dict, constraints: List[Dict] = None) -> str:
    """
    레시피 정보로부터 인사말 생성용 시스템 프롬프트를 만듭니다.
    사용자 맞춤화 기능 (제약사항 반영) 포함.
    
    Args:
        recipe_json: 레시피 정보 딕셔너리
            {
                "title": "나물비빔밥",
                "ingredients": ["쌀", "안심", ...],
                "steps": ["1. 양지머리로...", "2. 안심...", ...],
                "content": "전체 조리법 내용"
            }
        constraints: 사용자 제약사항 리스트 (선택적)
            [
                {"type": "spice_level", "action": "decrease", "degree": "light"},
                {"type": "low_salt", "action": "decrease", "degree": "medium"},
                ...
            ]
    
    Returns:
        시스템 프롬프트 문자열
    """
    
    title = recipe_json.get("title", "레시피")
    ingredients = recipe_json.get("ingredients", [])
    steps = recipe_json.get("steps", [])
    content = recipe_json.get("content", "")
    
    # 재료 목록 문자열 생성
    ingredients_str = ", ".join(ingredients) if isinstance(ingredients, list) else str(ingredients)
    
    # 단계 목록 문자열 생성
    steps_str = "\n".join(steps) if isinstance(steps, list) else str(steps)
    
    # 제약사항 문자열 생성
    constraints_text = ""
    if constraints:
        constraints_list = []
        for constraint in constraints:
            c_type = constraint.get("type", "")
            action = constraint.get("action", "")
            degree = constraint.get("degree", "")
            value = constraint.get("value", "")
            
            # 제약사항을 자연어로 변환
            if c_type == "spice_level":
                if action == "decrease":
                    if degree == "light":
                        constraints_list.append("매운맛을 조금 줄여주세요")
                    elif degree == "medium":
                        constraints_list.append("매운맛을 적당히 줄여주세요")
                    else:
                        constraints_list.append("매운맛을 많이 줄여주세요")
                elif action == "increase":
                    if degree == "medium":
                        constraints_list.append("매운맛을 적당히 늘려주세요")
                    else:
                        constraints_list.append("매운맛을 많이 늘려주세요")
            elif c_type == "low_salt":
                if action == "decrease":
                    if degree == "medium":
                        constraints_list.append("짠맛을 적당히 줄여주세요")
                    else:
                        constraints_list.append("짠맛을 많이 줄여주세요 (저염)")
                elif action == "increase":
                    constraints_list.append("짠맛을 늘려주세요")
            elif c_type == "oil":
                if action == "decrease":
                    if degree == "medium":
                        constraints_list.append("기름을 적당히 줄여주세요")
                    else:
                        constraints_list.append("기름을 많이 줄여주세요 (저지방)")
                elif action == "increase":
                    constraints_list.append("기름을 늘려주세요")
            elif c_type == "vegan":
                if action == "enforce":
                    constraints_list.append("비건/채식 요리로 만들어주세요 (육류, 해산물, 계란 제외)")
            elif c_type == "allergy":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 알레르기가 있으니 제외해주세요")
            elif c_type == "low_calorie":
                if action == "decrease":
                    constraints_list.append("저칼로리 요리로 만들어주세요 (칼로리 최소화)")
            elif c_type == "low_sugar":
                if action == "decrease":
                    constraints_list.append("저당 요리로 만들어주세요 (설탕, 당분 최소화)")
            elif c_type == "low_cholesterol":
                if action == "decrease":
                    constraints_list.append("저콜레스테롤 요리로 만들어주세요")
            elif c_type == "cooking_method":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 조리법을 사용하지 마세요")
                elif action == "enforce" and value:
                    constraints_list.append(f"{value} 조리법을 사용해주세요")
            elif c_type == "simple_cooking":
                if action == "enforce":
                    constraints_list.append("간단하고 쉬운 조리법으로 만들어주세요")
            elif c_type == "quick_cooking":
                if action == "enforce":
                    if degree == "strong":
                        constraints_list.append("5분 이내 빠른 조리법으로 만들어주세요")
                    elif degree == "medium":
                        constraints_list.append("10분 이내 빠른 조리법으로 만들어주세요")
                    else:
                        constraints_list.append("15분 이내 빠른 조리법으로 만들어주세요")
            elif c_type == "ingredient_remove":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 재료를 제외해주세요")
            elif c_type == "gluten_free":
                if action == "enforce":
                    constraints_list.append("글루텐 프리 요리로 만들어주세요 (밀, 밀가루 제외)")
            elif c_type == "lactose_free":
                if action == "enforce":
                    constraints_list.append("유당 프리 요리로 만들어주세요 (우유, 유제품 제외)")
            elif c_type == "halal":
                if action == "enforce":
                    constraints_list.append("할랄 요리로 만들어주세요 (돼지고기, 알코올 제외)")
            elif c_type == "kosher":
                if action == "enforce":
                    constraints_list.append("코셔 요리로 만들어주세요")
            elif c_type == "sweetness":
                if action == "increase":
                    constraints_list.append("단맛을 늘려주세요")
                elif action == "decrease":
                    constraints_list.append("단맛을 줄여주세요")
            elif c_type == "sourness":
                if action == "increase":
                    constraints_list.append("신맛을 늘려주세요 (식초 추가)")
                elif action == "decrease":
                    constraints_list.append("신맛을 줄여주세요")
            elif c_type == "clean_taste":
                if action == "enforce":
                    constraints_list.append("깔끔하고 담백한 맛으로 만들어주세요")
            elif c_type == "rich_taste":
                if action == "enforce":
                    constraints_list.append("진하고 깊은 맛으로 만들어주세요")
        
        if constraints_list:
            constraints_text = "\n".join([f"- {c}" for c in constraints_list])
    
    # 제약사항 섹션
    constraints_section = ""
    if constraints_text:
        constraints_section = f"""
[사용자 맞춤화 요구사항]
{constraints_text}

[맞춤화 규칙]
- 위 요구사항을 반영하여 레시피를 수정해주세요
- 재료나 양을 조절할 때는 구체적으로 명시해주세요 (예: "고추장 1큰술 → 고추장 1/2큰술")
- 대체 재료가 있으면 제시해주세요 (예: "돼지고기 → 두부")
- 안전하고 맛있게 조리할 수 있도록 조언해주세요
- 단계별로 요구사항을 자연스럽게 반영해주세요
"""
    
    system_prompt = f"""당신은 "쿡덕"입니다. 친절하고 전문적인 요리 도우미 AI입니다.

[안내 규칙]
1. 사용자가 "안녕하세요" 또는 "시작해주세요" 같은 인사말을 하면, [인사말] 규칙을 따라 친절하게 인사하고 레시피를 소개하세요.
2. 사용자가 "다음"이라고 말하면, [전체 레시피]에서 현재 단계를 확인하고, [사용자 맞춤화 요구사항]이 있으면 이를 반영하여 수정된 단계를 출력하세요.
3. 사용자가 특정 단계에 대해 질문하면, 해당 단계의 내용을 바탕으로 친절하게 답변하세요.
4. 사용자가 제약사항을 언급하면 (예: "매운걸 잘 못먹어요", "기름 적게", "저염"), 이를 반영하여 레시피를 수정해주세요.

[레시피 정보]
제목: {title}
재료: {ingredients_str}

[전체 레시피]
{steps_str if steps_str else content}
{constraints_section}
[인사말 규칙]
- "안녕하세요 쿡덕입니다!"로 시작
- 레시피 제목을 언급
- 주요 재료를 간단히 소개
- [사용자 맞춤화 요구사항]이 있으면 이를 언급 (예: "매운맛을 줄여서 안내해드리겠습니다")
- "차근차근 안내해드리겠습니다"로 마무리
- 2-3문장으로 간결하게 작성

[단계 안내 규칙]
- 사용자가 "다음"이라고 말하면:
  1. [전체 레시피]에서 현재 단계를 확인
  2. [사용자 맞춤화 요구사항]이 있으면 이를 반영하여 수정
  3. 수정된 단계를 출력 (원문 번호는 유지, 내용만 수정)
- 수정 시 구체적인 양이나 재료 변경사항을 명시
- 안전하고 맛있게 조리할 수 있도록 조언 포함
- 원문의 핵심 조리법은 유지하되, 요구사항에 맞게 조절"""
    
    return system_prompt


def create_step_prompt(recipe_json: Dict, current_step_index: int, step_text: str, constraints: List[Dict] = None) -> str:
    """
    단계별 안내용 시스템 프롬프트를 만듭니다.
    사용자 맞춤화 기능 (제약사항 반영) 포함.
    
    Args:
        recipe_json: 레시피 정보 딕셔너리
        current_step_index: 현재 단계 인덱스 (0부터 시작)
        step_text: 현재 단계 텍스트
        constraints: 사용자 제약사항 리스트 (선택적)
    
    Returns:
        단계 안내용 시스템 프롬프트 문자열
    """
    
    title = recipe_json.get("title", "레시피")
    steps = recipe_json.get("steps", [])
    
    # 전체 레시피 단계 목록 생성
    all_steps_text = "\n".join(steps) if isinstance(steps, list) else str(steps)
    
    # 제약사항 문자열 생성
    constraints_text = ""
    if constraints:
        constraints_list = []
        for constraint in constraints:
            c_type = constraint.get("type", "")
            action = constraint.get("action", "")
            degree = constraint.get("degree", "")
            value = constraint.get("value", "")
            
            # 제약사항을 자연어로 변환
            if c_type == "spice_level":
                if action == "decrease":
                    if degree == "light":
                        constraints_list.append("매운맛을 조금 줄이기 (고추장, 고춧가루 70% 정도)")
                    elif degree == "medium":
                        constraints_list.append("매운맛을 적당히 줄이기 (고추장, 고춧가루 50% 정도)")
                    else:
                        constraints_list.append("매운맛을 많이 줄이기 (고추장, 고춧가루 최소화 또는 생략)")
                elif action == "increase":
                    if degree == "medium":
                        constraints_list.append("매운맛을 적당히 늘리기 (고추장, 고춧가루 1.15배)")
                    else:
                        constraints_list.append("매운맛을 많이 늘리기 (고추장, 고춧가루 1.3배 또는 청양고추 추가)")
            elif c_type == "low_salt":
                if action == "decrease":
                    if degree == "medium":
                        constraints_list.append("짠맛을 적당히 줄이기 (간장, 소금 80% 정도)")
                    else:
                        constraints_list.append("짠맛을 많이 줄이기 (간장, 소금 60% 정도, 식초나 후추로 맛 보완)")
                elif action == "increase":
                    constraints_list.append("짠맛을 늘리기 (간장, 소금 추가)")
            elif c_type == "oil":
                if action == "decrease":
                    if degree == "medium":
                        constraints_list.append("기름을 적당히 줄이기 (식용유 70% 정도, 물 추가)")
                    else:
                        constraints_list.append("기름을 많이 줄이기 (식용유 50% 정도, 물 추가)")
                elif action == "increase":
                    constraints_list.append("기름을 늘리기 (식용유 추가)")
            elif c_type == "vegan":
                if action == "enforce":
                    constraints_list.append("비건/채식 요리 (돼지고기→두부, 소고기→두부, 닭고기→두부, 멸치→다시마, 새우→버섯, 계란→두부)")
            elif c_type == "allergy":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 알레르기 (해당 재료 완전 제외)")
            elif c_type == "low_calorie":
                if action == "decrease":
                    constraints_list.append("저칼로리 요리 (기름 최소화, 튀김 대신 찜/굽기, 고기 대신 채소 위주)")
            elif c_type == "low_sugar":
                if action == "decrease":
                    constraints_list.append("저당 요리 (설탕 최소화 또는 생략, 대체 감미료 사용)")
            elif c_type == "low_cholesterol":
                if action == "decrease":
                    constraints_list.append("저콜레스테롤 요리 (동물성 지방 최소화, 식물성 기름 사용)")
            elif c_type == "cooking_method":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 조리법 제외 (다른 조리법 사용)")
                elif action == "enforce" and value:
                    constraints_list.append(f"{value} 조리법 사용")
            elif c_type == "simple_cooking":
                if action == "enforce":
                    constraints_list.append("간단하고 쉬운 조리법 (재료 최소화, 단계 간소화)")
            elif c_type == "quick_cooking":
                if action == "enforce":
                    if degree == "strong":
                        constraints_list.append("5분 이내 빠른 조리 (준비 시간 최소화, 간단한 조리법)")
                    elif degree == "medium":
                        constraints_list.append("10분 이내 빠른 조리 (준비 시간 단축)")
                    else:
                        constraints_list.append("15분 이내 빠른 조리")
            elif c_type == "ingredient_remove":
                if action == "remove" and value:
                    constraints_list.append(f"{value} 재료 제외 (대체 재료 제시)")
            elif c_type == "gluten_free":
                if action == "enforce":
                    constraints_list.append("글루텐 프리 (밀, 밀가루 제외, 쌀가루나 감자전분 사용)")
            elif c_type == "lactose_free":
                if action == "enforce":
                    constraints_list.append("유당 프리 (우유, 유제품 제외, 식물성 우유 사용)")
            elif c_type == "halal":
                if action == "enforce":
                    constraints_list.append("할랄 요리 (돼지고기, 알코올 제외)")
            elif c_type == "kosher":
                if action == "enforce":
                    constraints_list.append("코셔 요리 (유대교 규율 준수)")
            elif c_type == "sweetness":
                if action == "increase":
                    constraints_list.append("단맛 증가 (설탕, 꿀 추가)")
                elif action == "decrease":
                    constraints_list.append("단맛 감소 (설탕 최소화)")
            elif c_type == "sourness":
                if action == "increase":
                    constraints_list.append("신맛 증가 (식초, 레몬 추가)")
                elif action == "decrease":
                    constraints_list.append("신맛 감소 (식초 최소화)")
            elif c_type == "clean_taste":
                if action == "enforce":
                    constraints_list.append("깔끔하고 담백한 맛 (양념 최소화, 재료 본연의 맛)")
            elif c_type == "rich_taste":
                if action == "enforce":
                    constraints_list.append("진하고 깊은 맛 (양념 강화, 육수 사용)")
        
        if constraints_list:
            constraints_text = "\n".join([f"- {c}" for c in constraints_list])
    
    # 제약사항 섹션
    constraints_section = ""
    if constraints_text:
        constraints_section = f"""
[사용자 맞춤화 요구사항]
{constraints_text}

[맞춤화 적용 방법]
- 위 요구사항을 현재 단계에 자연스럽게 반영
- 재료나 양을 변경할 때는 구체적으로 명시 (예: "고추장 1큰술" → "고추장 1/2큰술")
- 대체 재료가 있으면 제시 (예: "돼지고기 200g" → "두부 200g")
- 원문의 조리법 구조는 유지하되, 양이나 재료만 조절
- 안전하고 맛있게 조리할 수 있도록 조언 포함
"""
    
    system_prompt = f"""당신은 "쿡덕"입니다.

[안내 규칙] 2번 규칙에 따라, 다음 [사용자 입력]을 보고, [전체 레시피]에서 다음 단계를 확인하고, [사용자 맞춤화 요구사항]이 있으면 이를 반영하여 수정된 단계를 출력하세요.

[레시피 제목]
{title}

[전체 레시피]
{all_steps_text}

[현재 단계]
{step_text}
{constraints_section}
[규칙]
- 사용자가 "다음"이라고 말하면:
  1. [전체 레시피]에서 현재 단계 다음의 단계를 확인
  2. [사용자 맞춤화 요구사항]이 있으면 이를 반영하여 수정
  3. 수정된 단계를 출력 (원문 번호는 유지, 내용만 수정)
- 수정 시 구체적인 양이나 재료 변경사항을 명시 (예: "고추장 1큰술" → "고추장 1/2큰술")
- 대체 재료가 있으면 명시 (예: "돼지고기 200g" → "두부 200g")
- 안전하고 맛있게 조리할 수 있도록 조언 포함
- 원문의 핵심 조리법은 유지하되, 요구사항에 맞게 조절"""
    
    return system_prompt


def create_greeting_user_prompt() -> str:
    """
    인사말을 트리거하기 위한 사용자 프롬프트를 반환합니다.
    
    Returns:
        인사말 트리거용 사용자 프롬프트
    """
    return "안녕하세요. 이 레시피로 요리 안내를 시작해주세요."


def create_next_step_user_prompt() -> str:
    """
    다음 단계를 요청하는 사용자 프롬프트를 반환합니다.
    
    Returns:
        다음 단계 요청용 사용자 프롬프트
    """
    return "다음"


def constraints_to_dict_list(constraints) -> List[Dict]:
    """
    Constraint 객체 리스트를 Dict 리스트로 변환합니다.
    
    Args:
        constraints: Constraint 객체 리스트 또는 Dict 리스트
    
    Returns:
        Dict 리스트
    """
    if not constraints:
        return []
    
    result = []
    for constraint in constraints:
        if isinstance(constraint, dict):
            result.append(constraint)
        else:
            # Pydantic 모델인 경우
            result.append({
                "type": getattr(constraint, "type", ""),
                "action": getattr(constraint, "action", ""),
                "degree": getattr(constraint, "degree", None),
                "value": getattr(constraint, "value", None)
            })
    
    return result


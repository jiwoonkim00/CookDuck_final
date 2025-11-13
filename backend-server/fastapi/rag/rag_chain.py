# fastapi/rag/rag_chain.py
from pydantic import BaseModel
from typing import List
import json

class RecipeStep(BaseModel):
    order: int
    text: str

class RecipeCard(BaseModel):
    title: str
    reason: str
    ingredients: List[str]
    substitutes: List[str]
    steps: List[RecipeStep]
    source_refs: List[str]

def simple_rag_chain(query: str) -> RecipeCard:
    """간단한 RAG 체인 (실제 LLM 없이)"""
    
    # 사용자 입력에서 재료 추출
    ingredients = query.replace("이 재료들로 만들 수 있는 요리:", "").strip().split(",")
    ingredients = [ing.strip() for ing in ingredients]
    
    # 간단한 레시피 추천 로직
    if "김치" in ingredients and "계란" in ingredients:
        recipe = RecipeCard(
            title="김치계란볶음밥",
            reason="김치의 신맛과 계란의 부드러움이 잘 어울리는 간단한 볶음밥입니다.",
            ingredients=["김치", "계란", "밥", "식용유", "소금", "후추"],
            substitutes=["밥 대신 쌀국수", "김치 대신 배추"],
            steps=[
                RecipeStep(order=1, text="김치를 적당한 크기로 자릅니다."),
                RecipeStep(order=2, text="팬에 기름을 두르고 김치를 볶습니다."),
                RecipeStep(order=3, text="계란을 풀어서 김치와 함께 볶습니다."),
                RecipeStep(order=4, text="밥을 넣고 함께 볶아 완성합니다.")
            ],
            source_refs=["recipe_001", "recipe_002"]
        )
    elif "김치" in ingredients:
        recipe = RecipeCard(
            title="김치찌개",
            reason="김치의 깊은 맛이 살아있는 얼큰한 찌개입니다.",
            ingredients=["김치", "돼지고기", "두부", "대파", "고춧가루"],
            substitutes=["돼지고기 대신 소고기", "두부 대신 순두부"],
            steps=[
                RecipeStep(order=1, text="김치를 적당한 크기로 자릅니다."),
                RecipeStep(order=2, text="돼지고기를 볶아 기름을 냅니다."),
                RecipeStep(order=3, text="김치를 넣고 볶습니다."),
                RecipeStep(order=4, text="물을 넣고 끓인 후 두부를 넣어 완성합니다.")
            ],
            source_refs=["recipe_003", "recipe_004"]
        )
    else:
        recipe = RecipeCard(
            title="간단 볶음요리",
            reason="입력하신 재료들로 만드는 간단한 볶음 요리입니다.",
            ingredients=ingredients + ["식용유", "소금", "후추"],
            substitutes=["식용유 대신 올리브오일"],
            steps=[
                RecipeStep(order=1, text="재료들을 적당한 크기로 자릅니다."),
                RecipeStep(order=2, text="팬에 기름을 두르고 재료들을 볶습니다."),
                RecipeStep(order=3, text="소금과 후추로 간을 맞춰 완성합니다.")
            ],
            source_refs=["recipe_005"]
        )
    
    return recipe

# 체인 함수
def chain(query: str) -> RecipeCard:
    """RAG 체인 실행"""
    return simple_rag_chain(query)
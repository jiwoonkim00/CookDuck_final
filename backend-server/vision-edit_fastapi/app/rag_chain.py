"""
RAG (Retrieval-Augmented Generation) 체인 구현
LangChain을 사용한 레시피 추천 시스템
"""

import os
import logging
from typing import List, Dict, Any
import pickle

logger = logging.getLogger(__name__)

class RAGChain:
    def __init__(self):
        self.metadata_path = "/app/faiss_store/metadata.pkl"
        self.all_recipes = []
        self._load_recipes()
    
    def _load_recipes(self):
        """metadata.pkl에서 레시피 데이터 로드"""
        try:
            logger.info(f"레시피 데이터 로드 시도: {self.metadata_path}")
            
            # 파일 존재 확인
            if not os.path.exists(self.metadata_path):
                logger.error(f"파일이 존재하지 않음: {self.metadata_path}")
                
                # 대체 경로 시도
                alternative_paths = [
                    "./faiss_store/metadata.pkl",
                    "/backend-server/fastapi/faiss_store/metadata.pkl",
                    "./backend-server/fastapi/faiss_store/metadata.pkl"
                ]
                
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        logger.info(f"대체 경로 발견: {alt_path}")
                        self.metadata_path = alt_path
                        break
                else:
                    logger.error("모든 경로에서 파일을 찾을 수 없음")
                    return
            
            # 파일 권한 확인
            if not os.access(self.metadata_path, os.R_OK):
                logger.error(f"파일 읽기 권한 없음: {self.metadata_path}")
                return
            
            # 파일 크기 확인
            file_size = os.path.getsize(self.metadata_path)
            logger.info(f"파일 크기: {file_size / (1024*1024):.2f} MB")
            
            # pickle 로드 (allow_pickle 명시적 설정)
            with open(self.metadata_path, "rb") as f:
                self.all_recipes = pickle.load(f)
            
            logger.info(f"✅ 총 {len(self.all_recipes)}개 레시피 로드 완료")
            
            # 첫 번째 레시피 샘플 출력
            if self.all_recipes:
                sample = self.all_recipes[0]
                logger.info(f"샘플 레시피: {sample.get('title', 'N/A')}")
                logger.info(f"샘플 재료: {sample.get('ingredients', 'N/A')[:100]}")
            
        except Exception as e:
            logger.error(f"❌ 레시피 로드 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _search_recipes(self, ingredients: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """재료 기반 레시피 검색"""
        if not self.all_recipes:
            logger.warning("로드된 레시피가 없음")
            return []
        
        logger.info(f"검색 시작 - 재료: {ingredients}, 총 {len(self.all_recipes)}개 레시피")
        
        # 재료 매칭 점수 계산
        scored_recipes = []
        
        for recipe in self.all_recipes:
            recipe_ingredients = recipe.get("ingredients", "").lower()
            recipe_title = recipe.get("title", "")
            recipe_content = recipe.get("content", "")
            
            # 매칭 점수 계산
            match_count = 0
            matched_ingredients = []
            
            for user_ingredient in ingredients:
                user_ingredient_lower = user_ingredient.lower()
                if user_ingredient_lower in recipe_ingredients:
                    match_count += 1
                    matched_ingredients.append(user_ingredient)
            
            # 최소 1개 이상 매칭되면 추가 (더 많은 결과를 위해)
            if match_count > 0:
                # 재료 리스트 파싱
                ingredients_list = [ing.strip() for ing in recipe_ingredients.split(',')]
                
                scored_recipes.append({
                    "recipe": recipe,
                    "score": match_count,
                    "matched_ingredients": matched_ingredients,
                    "title": recipe_title,
                    "description": f"{recipe_title} - {recipe_content[:100]}..." if len(recipe_content) > 100 else recipe_content,
                    "ingredients": ingredients_list,
                    "instructions": recipe_content.split('\n')[:8] if recipe_content else ["조리법을 확인해주세요"],
                    "tips": f"사용자 재료 {match_count}개가 포함된 레시피입니다: {', '.join(matched_ingredients)}"
                })
        
        logger.info(f"매칭된 레시피 수: {len(scored_recipes)}")
        
        # 점수 기준 정렬 (내림차순)
        scored_recipes.sort(key=lambda x: x["score"], reverse=True)
        
        # 상위 top_k개 반환
        top_recipes = scored_recipes[:top_k]
        
        # recipe 키 제거 (응답에 포함 불필요)
        for recipe in top_recipes:
            recipe.pop("recipe", None)
        
        return top_recipes
    
    def __call__(self, query: str, ingredients: List[str] = None):
        """RAG 체인 실행"""
        try:
            logger.info(f"RAG 체인 호출 - query: {query}, ingredients: {ingredients}")
            
            # 재료가 직접 전달된 경우 사용, 아니면 쿼리에서 추출
            if ingredients is None or len(ingredients) == 0:
                logger.warning("재료가 제공되지 않음")
                return {
                    "result": "재료를 입력해주세요.",
                    "recommendations": [],
                    "total_count": 0,
                    "source_documents": [],
                    "method": "No_Ingredients"
                }
            
            # 레시피 검색 (더 많은 결과를 위해 top_k 증가)
            recommendations = self._search_recipes(ingredients, top_k=50)
            
            if recommendations:
                logger.info(f"✅ {len(recommendations)}개 레시피 찾음")
                return {
                    "result": f"'{', '.join(ingredients)}' 재료로 만들 수 있는 요리를 {len(recommendations)}개 찾았습니다!",
                    "recommendations": recommendations,
                    "total_count": len(recommendations),
                    "source_documents": [
                        {
                            "page_content": f"재료: {', '.join(ingredients)}",
                            "metadata": {"source": "metadata.pkl", "type": "ingredient_search"}
                        }
                    ],
                    "method": "RAG_metadata.pkl"
                }
            else:
                logger.info("❌ 매칭되는 레시피 없음")
                return {
                    "result": f"'{', '.join(ingredients)}' 재료로 만들 수 있는 요리를 찾을 수 없습니다.",
                    "recommendations": [],
                    "total_count": 0,
                    "source_documents": [],
                    "method": "No_Results"
                }
            
        except Exception as e:
            logger.error(f"❌ RAG 체인 실행 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "result": f"RAG 처리 중 오류가 발생했습니다: {str(e)}",
                "recommendations": [],
                "total_count": 0,
                "source_documents": [],
                "method": "Error"
            }

# 전역 RAG 체인 인스턴스
chain = RAGChain()
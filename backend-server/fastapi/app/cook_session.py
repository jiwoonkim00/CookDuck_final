"""
요리 세션 관리 시스템
사용자별 세션 상태와 제약사항을 관리하는 모듈
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
import re
import logging

logger = logging.getLogger(__name__)

class Constraint(BaseModel):
    """제약사항 모델"""
    type: str  # "spice_level" | "oil" | "low_salt" | "vegan" | "allergy"
    action: str  # "increase" | "decrease" | "enforce" | "remove"
    degree: Optional[str] = None  # "light" | "medium" | "strong"
    value: Optional[str] = None  # 구체적인 값 (예: "고추장", "청양고추")

class SessionState(BaseModel):
    """세션 상태 모델"""
    user_id: str
    recipe_id: Optional[int] = None
    current_step: int = 0
    constraints: List[Constraint] = []
    recipe_data: Optional[Dict] = None

class CookSessionManager:
    """요리 세션 관리자"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
    
    def create_session(self, user_id: str, recipe_id: int) -> SessionState:
        """새 세션 생성"""
        session = SessionState(
            user_id=user_id,
            recipe_id=recipe_id,
            current_step=0,
            constraints=[]
        )
        self.sessions[user_id] = session
        logger.info(f"세션 생성: {user_id}, 레시피: {recipe_id}")
        return session
    
    def get_session(self, user_id: str) -> Optional[SessionState]:
        """세션 조회"""
        return self.sessions.get(user_id)
    
    def add_constraint(self, user_id: str, constraint: Constraint) -> bool:
        """제약사항 추가"""
        session = self.get_session(user_id)
        if not session:
            return False
        
        # 중복 제약사항 제거 (같은 타입의 기존 제약사항)
        session.constraints = [
            c for c in session.constraints 
            if c.type != constraint.type
        ]
        
        session.constraints.append(constraint)
        logger.info(f"제약사항 추가: {user_id}, {constraint}")
        return True
    
    def clear_session(self, user_id: str) -> bool:
        """세션 삭제"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"세션 삭제: {user_id}")
            return True
        return False

class ConstraintParser:
    """자연어를 제약사항으로 파싱하는 클래스"""
    
    def __init__(self):
        # 키워드 매핑 테이블
        self.keyword_mapping = {
            # ========== 매운맛 관련 ==========
            "매운": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "매콤": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "맵게": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "더 매운": {"type": "spice_level", "action": "increase", "degree": "strong"},
            "아주 매운": {"type": "spice_level", "action": "increase", "degree": "strong"},
            "엄청 매운": {"type": "spice_level", "action": "increase", "degree": "strong"},
            "덜 매운": {"type": "spice_level", "action": "decrease", "degree": "light"},
            "안 매운": {"type": "spice_level", "action": "decrease", "degree": "strong"},
            "안매운": {"type": "spice_level", "action": "decrease", "degree": "strong"},
            "매운걸 잘 못먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운걸 잘 못 먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운거 못먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운거 못 먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운맛 못먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운맛 못 먹어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운맛 싫어": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "매운맛 안 좋아": {"type": "spice_level", "action": "decrease", "degree": "medium"},
            "고추": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "청양고추": {"type": "spice_level", "action": "increase", "degree": "strong"},
            "고춧가루": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "고추장": {"type": "spice_level", "action": "increase", "degree": "medium"},
            
            # ========== 기름 관련 ==========
            "기름": {"type": "oil", "action": "decrease", "degree": "medium"},
            "덜 기름": {"type": "oil", "action": "decrease", "degree": "medium"},
            "기름 적게": {"type": "oil", "action": "decrease", "degree": "strong"},
            "기름 없이": {"type": "oil", "action": "decrease", "degree": "strong"},
            "기름 최소": {"type": "oil", "action": "decrease", "degree": "strong"},
            "저지방": {"type": "oil", "action": "decrease", "degree": "strong"},
            "저지방식": {"type": "oil", "action": "decrease", "degree": "strong"},
            "기름 많이": {"type": "oil", "action": "increase", "degree": "medium"},
            "기름진": {"type": "oil", "action": "increase", "degree": "medium"},
            
            # ========== 소금 관련 ==========
            "덜 짜게": {"type": "low_salt", "action": "decrease", "degree": "medium"},
            "덜 짜": {"type": "low_salt", "action": "decrease", "degree": "medium"},
            "저염": {"type": "low_salt", "action": "decrease", "degree": "strong"},
            "저염식": {"type": "low_salt", "action": "decrease", "degree": "strong"},
            "소금 적게": {"type": "low_salt", "action": "decrease", "degree": "medium"},
            "간장 적게": {"type": "low_salt", "action": "decrease", "degree": "medium"},
            "짠맛": {"type": "low_salt", "action": "increase", "degree": "medium"},
            "더 짜게": {"type": "low_salt", "action": "increase", "degree": "medium"},
            "짠맛 좋아": {"type": "low_salt", "action": "increase", "degree": "medium"},
            
            # ========== 비건/채식 관련 ==========
            "비건": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "채식": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "채식주의": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "육류 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "고기 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "돼지고기 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "소고기 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "닭고기 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "해산물 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "생선 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "계란 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "달걀 없이": {"type": "vegan", "action": "enforce", "degree": "strong"},
            
            # ========== 알레르기 관련 ==========
            "견과류": {"type": "allergy", "action": "remove", "value": "견과류"},
            "땅콩": {"type": "allergy", "action": "remove", "value": "땅콩"},
            "아몬드": {"type": "allergy", "action": "remove", "value": "아몬드"},
            "호두": {"type": "allergy", "action": "remove", "value": "호두"},
            "우유": {"type": "allergy", "action": "remove", "value": "우유"},
            "우유 알레르기": {"type": "allergy", "action": "remove", "value": "우유"},
            "유당": {"type": "allergy", "action": "remove", "value": "우유"},
            "유당 불내증": {"type": "allergy", "action": "remove", "value": "우유"},
            "달걀": {"type": "allergy", "action": "remove", "value": "달걀"},
            "계란": {"type": "allergy", "action": "remove", "value": "달걀"},
            "계란 알레르기": {"type": "allergy", "action": "remove", "value": "달걀"},
            "달걀 알레르기": {"type": "allergy", "action": "remove", "value": "달걀"},
            "갑각류": {"type": "allergy", "action": "remove", "value": "갑각류"},
            "새우": {"type": "allergy", "action": "remove", "value": "새우"},
            "게": {"type": "allergy", "action": "remove", "value": "게"},
            "랍스터": {"type": "allergy", "action": "remove", "value": "랍스터"},
            "조개": {"type": "allergy", "action": "remove", "value": "조개"},
            "굴": {"type": "allergy", "action": "remove", "value": "굴"},
            "밀": {"type": "allergy", "action": "remove", "value": "밀"},
            "밀가루": {"type": "allergy", "action": "remove", "value": "밀"},
            "글루텐": {"type": "allergy", "action": "remove", "value": "글루텐"},
            "글루텐 알레르기": {"type": "allergy", "action": "remove", "value": "글루텐"},
            "대두": {"type": "allergy", "action": "remove", "value": "대두"},
            "콩": {"type": "allergy", "action": "remove", "value": "콩"},
            "두부": {"type": "allergy", "action": "remove", "value": "두부"},
            "된장": {"type": "allergy", "action": "remove", "value": "된장"},
            "간장": {"type": "allergy", "action": "remove", "value": "간장"},
            "참깨": {"type": "allergy", "action": "remove", "value": "참깨"},
            "깨": {"type": "allergy", "action": "remove", "value": "참깨"},
            "참깨 알레르기": {"type": "allergy", "action": "remove", "value": "참깨"},
            
            # ========== 건강 관련 (칼로리/당분) ==========
            "저칼로리": {"type": "low_calorie", "action": "decrease", "degree": "strong"},
            "다이어트": {"type": "low_calorie", "action": "decrease", "degree": "strong"},
            "칼로리 적게": {"type": "low_calorie", "action": "decrease", "degree": "medium"},
            "저당": {"type": "low_sugar", "action": "decrease", "degree": "strong"},
            "당분 적게": {"type": "low_sugar", "action": "decrease", "degree": "medium"},
            "설탕 적게": {"type": "low_sugar", "action": "decrease", "degree": "medium"},
            "단맛 적게": {"type": "low_sugar", "action": "decrease", "degree": "medium"},
            "당뇨": {"type": "low_sugar", "action": "decrease", "degree": "strong"},
            "당뇨식": {"type": "low_sugar", "action": "decrease", "degree": "strong"},
            "저콜레스테롤": {"type": "low_cholesterol", "action": "decrease", "degree": "strong"},
            "콜레스테롤 적게": {"type": "low_cholesterol", "action": "decrease", "degree": "medium"},
            
            # ========== 조리법 관련 ==========
            "튀김 없이": {"type": "cooking_method", "action": "remove", "value": "튀김"},
            "튀기지 말고": {"type": "cooking_method", "action": "remove", "value": "튀김"},
            "볶음": {"type": "cooking_method", "action": "enforce", "value": "볶음"},
            "찜": {"type": "cooking_method", "action": "enforce", "value": "찜"},
            "삶기": {"type": "cooking_method", "action": "enforce", "value": "삶기"},
            "데치기": {"type": "cooking_method", "action": "enforce", "value": "데치기"},
            "굽기": {"type": "cooking_method", "action": "enforce", "value": "굽기"},
            "구워": {"type": "cooking_method", "action": "enforce", "value": "굽기"},
            "전자레인지": {"type": "cooking_method", "action": "enforce", "value": "전자레인지"},
            "간단하게": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            "빠르게": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            "간단한": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            "간편하게": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            
            # ========== 재료 관련 ==========
            "돼지고기 없이": {"type": "ingredient_remove", "action": "remove", "value": "돼지고기"},
            "소고기 없이": {"type": "ingredient_remove", "action": "remove", "value": "소고기"},
            "닭고기 없이": {"type": "ingredient_remove", "action": "remove", "value": "닭고기"},
            "양파 없이": {"type": "ingredient_remove", "action": "remove", "value": "양파"},
            "마늘 없이": {"type": "ingredient_remove", "action": "remove", "value": "마늘"},
            "파 없이": {"type": "ingredient_remove", "action": "remove", "value": "파"},
            "대파 없이": {"type": "ingredient_remove", "action": "remove", "value": "대파"},
            "고추 없이": {"type": "ingredient_remove", "action": "remove", "value": "고추"},
            "고춧가루 없이": {"type": "ingredient_remove", "action": "remove", "value": "고춧가루"},
            "고추장 없이": {"type": "ingredient_remove", "action": "remove", "value": "고추장"},
            "된장 없이": {"type": "ingredient_remove", "action": "remove", "value": "된장"},
            "멸치 없이": {"type": "ingredient_remove", "action": "remove", "value": "멸치"},
            "새우젓 없이": {"type": "ingredient_remove", "action": "remove", "value": "새우젓"},
            "젓갈 없이": {"type": "ingredient_remove", "action": "remove", "value": "젓갈"},
            
            # ========== 식이 제한 관련 ==========
            "글루텐 프리": {"type": "gluten_free", "action": "enforce", "degree": "strong"},
            "글루텐프리": {"type": "gluten_free", "action": "enforce", "degree": "strong"},
            "무글루텐": {"type": "gluten_free", "action": "enforce", "degree": "strong"},
            "유당 프리": {"type": "lactose_free", "action": "enforce", "degree": "strong"},
            "유당프리": {"type": "lactose_free", "action": "enforce", "degree": "strong"},
            "무유당": {"type": "lactose_free", "action": "enforce", "degree": "strong"},
            "할랄": {"type": "halal", "action": "enforce", "degree": "strong"},
            "할랄식": {"type": "halal", "action": "enforce", "degree": "strong"},
            "코셔": {"type": "kosher", "action": "enforce", "degree": "strong"},
            "코셔식": {"type": "kosher", "action": "enforce", "degree": "strong"},
            
            # ========== 맛 관련 ==========
            "단맛": {"type": "sweetness", "action": "increase", "degree": "medium"},
            "더 달게": {"type": "sweetness", "action": "increase", "degree": "medium"},
            "덜 달게": {"type": "sweetness", "action": "decrease", "degree": "medium"},
            "신맛": {"type": "sourness", "action": "increase", "degree": "medium"},
            "더 시게": {"type": "sourness", "action": "increase", "degree": "medium"},
            "덜 시게": {"type": "sourness", "action": "decrease", "degree": "medium"},
            "식초 많이": {"type": "sourness", "action": "increase", "degree": "medium"},
            "식초 적게": {"type": "sourness", "action": "decrease", "degree": "medium"},
            "깔끔한": {"type": "clean_taste", "action": "enforce", "degree": "medium"},
            "담백한": {"type": "clean_taste", "action": "enforce", "degree": "medium"},
            "진한 맛": {"type": "rich_taste", "action": "enforce", "degree": "medium"},
            "깊은 맛": {"type": "rich_taste", "action": "enforce", "degree": "medium"},
            
            # ========== 시간 관련 ==========
            "빠른": {"type": "quick_cooking", "action": "enforce", "degree": "medium"},
            "빠르게": {"type": "quick_cooking", "action": "enforce", "degree": "medium"},
            "5분": {"type": "quick_cooking", "action": "enforce", "degree": "strong"},
            "10분": {"type": "quick_cooking", "action": "enforce", "degree": "medium"},
            "15분": {"type": "quick_cooking", "action": "enforce", "degree": "light"},
            "간단한": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            "간편한": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
            "쉬운": {"type": "simple_cooking", "action": "enforce", "degree": "medium"},
        }
    
    def parse_message(self, message: str) -> List[Constraint]:
        """자연어 메시지를 제약사항으로 파싱"""
        constraints = []
        message_lower = message.lower()
        
        for keyword, constraint_data in self.keyword_mapping.items():
            if keyword in message_lower:
                constraint = Constraint(**constraint_data)
                constraints.append(constraint)
        
        return constraints

class RuleBasedModifier:
    """룰 기반 레시피 수정 클래스"""
    
    def __init__(self):
        # 변형 규칙 테이블
        self.modification_rules = {
            "spice_level": {
                "increase": {
                    "medium": {"고추장": 1.15, "고춧가루": 1.15},
                    "strong": {"고추장": 1.30, "고춧가루": 1.30, "청양고추": "추가"}
                },
                "decrease": {
                    "light": {"고추장": 0.7, "고춧가루": 0.7}
                }
            },
            "oil": {
                "decrease": {
                    "medium": {"식용유": 0.7, "물": "추가"},
                    "strong": {"식용유": 0.5, "물": "추가"}
                }
            },
            "low_salt": {
                "decrease": {
                    "medium": {"간장": 0.8, "소금": 0.8, "식초": "추가"},
                    "strong": {"간장": 0.6, "소금": 0.6, "식초": "추가", "후추": "추가"}
                }
            },
            "vegan": {
                "enforce": {
                    "strong": {
                        "돼지고기": "두부", "소고기": "두부", "닭고기": "두부",
                        "멸치": "다시마", "새우": "버섯", "계란": "두부"
                    }
                }
            }
        }
    
    def apply_modifications(self, original_text: str, constraints: List[Constraint]) -> Dict:
        """제약사항을 적용하여 수정된 텍스트 생성"""
        modified_text = original_text
        applied_rules = []
        
        for constraint in constraints:
            rule_type = constraint.type
            action = constraint.action
            degree = constraint.degree or "medium"
            
            if rule_type in self.modification_rules:
                if action in self.modification_rules[rule_type]:
                    if degree in self.modification_rules[rule_type][action]:
                        rules = self.modification_rules[rule_type][action][degree]
                        applied_rules.append({
                            "type": rule_type,
                            "action": action,
                            "degree": degree,
                            "rules": rules
                        })
        
        return {
            "original_text": original_text,
            "modified_text": modified_text,
            "applied_rules": applied_rules,
            "constraints": constraints
        }

# 전역 인스턴스
session_manager = CookSessionManager()
constraint_parser = ConstraintParser()
rule_modifier = RuleBasedModifier()

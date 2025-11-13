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
            # 매운맛 관련
            "매운": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "매콤": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "맵게": {"type": "spice_level", "action": "increase", "degree": "medium"},
            "더 매운": {"type": "spice_level", "action": "increase", "degree": "strong"},
            "덜 매운": {"type": "spice_level", "action": "decrease", "degree": "light"},
            
            # 기름 관련
            "기름": {"type": "oil", "action": "decrease", "degree": "medium"},
            "덜 기름": {"type": "oil", "action": "decrease", "degree": "medium"},
            "기름 적게": {"type": "oil", "action": "decrease", "degree": "strong"},
            
            # 소금 관련
            "덜 짜게": {"type": "low_salt", "action": "decrease", "degree": "medium"},
            "저염": {"type": "low_salt", "action": "decrease", "degree": "strong"},
            "짠맛": {"type": "low_salt", "action": "increase", "degree": "medium"},
            
            # 비건 관련
            "비건": {"type": "vegan", "action": "enforce", "degree": "strong"},
            "채식": {"type": "vegan", "action": "enforce", "degree": "strong"},
            
            # 알레르기 관련
            "견과류": {"type": "allergy", "action": "remove", "value": "견과류"},
            "우유": {"type": "allergy", "action": "remove", "value": "우유"},
            "달걀": {"type": "allergy", "action": "remove", "value": "달걀"},
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

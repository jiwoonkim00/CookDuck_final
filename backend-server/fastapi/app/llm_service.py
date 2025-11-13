"""
Hugging Face LLM 서비스
Hugging Face에서 모델을 로드하여 텍스트 생성 제공
"""

import os
import logging
from typing import Optional, List, Dict
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    pipeline
)
import torch

logger = logging.getLogger(__name__)

class HuggingFaceLLMService:
    """Hugging Face 모델을 사용한 LLM 서비스"""
    
    def __init__(self):
        self.model_name = os.getenv(
            "HF_MODEL_NAME", 
            "00PJH/Llama-3.2-Korean-GGACHI-1B-Instruct-v1-koToEn"  # 기본값: Instruct 모델
        )
        # M1 Mac 지원: MPS (Metal Performance Shaders) 우선 사용
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"  # M1 Mac GPU 가속
        else:
            self.device = "cpu"
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.is_instruct_model = "instruct" in self.model_name.lower() or "llama-3.2" in self.model_name.lower()
        self._load_model()
    
    def _load_model(self):
        """모델 로드 (처음 호출 시 한 번만)"""
        try:
            logger.info(f"🤖 Hugging Face 모델 로딩 시작: {self.model_name}")
            logger.info(f"📱 Device: {self.device}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # 모델 로드
            # MPS는 float16을 지원하지 않으므로 float32 사용
            use_fp16 = self.device == "cuda"
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if use_fp16 else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            
            # CPU 또는 MPS로 모델 이동
            if self.device != "cuda":
                self.model = self.model.to(self.device)
            
            # Pipeline 생성
            # device 파라미터: cuda=0, mps=0, cpu=-1
            device_id = 0 if self.device in ["cuda", "mps"] else -1
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device_id,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            # Instruct 모델용 특수 토큰 확인
            if self.is_instruct_model:
                logger.info("📝 Instruct 모델 감지: 특수 프롬프트 템플릿 사용")
            
            logger.info(f"✅ 모델 로딩 완료: {self.model_name}")
            
        except Exception as e:
            logger.error(f"❌ 모델 로딩 실패: {str(e)}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        max_length: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        try:
            if not self.pipeline:
                raise RuntimeError("모델이 로드되지 않았습니다.")
            
            # Instruct 모델용 프롬프트 템플릿
            if self.is_instruct_model:
                # Llama 3.2 Instruct 형식 사용
                full_prompt = self._format_instruct_prompt(prompt)
            else:
                full_prompt = prompt
            
            # 생성 실행
            result = self.pipeline(
                full_prompt,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                num_return_sequences=1,
                return_full_text=False,
                **kwargs
            )
            
            # 결과 추출
            generated_text = result[0]["generated_text"].strip()
            
            # Instruct 모델 응답 정리 (시스템 프롬프트 제거)
            if self.is_instruct_model:
                generated_text = self._clean_instruct_response(generated_text)
            
            logger.info(f"생성 완료 (길이: {len(generated_text)})")
            return generated_text
            
        except Exception as e:
            logger.error(f"텍스트 생성 오류: {str(e)}")
            raise
    
    def _format_instruct_prompt(self, prompt: str) -> str:
        """Instruct 모델용 프롬프트 형식 변환 (토크나이저의 채팅 템플릿 사용)"""
        system_message = "너는 친절하고 유용한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공합니다."
        
        # 프롬프트에서 시스템/사용자 메시지 분리
        if "[시스템]" in prompt:
            parts = prompt.split("[사용자]")
            if len(parts) > 1:
                system_part = parts[0].replace("[시스템]", "").strip()
                user_message = parts[1].strip()
            else:
                user_message = prompt.replace("[시스템]", "").replace("[사용자]", "").strip()
                system_part = system_message
        else:
            user_message = prompt.strip()
            system_part = system_message
        
        # 토크나이저의 apply_chat_template 사용 (가능한 경우)
        if hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template is not None:
            try:
                messages = [
                    {"role": "system", "content": system_part},
                    {"role": "user", "content": user_message}
                ]
                formatted = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                return formatted
            except Exception as e:
                logger.warning(f"apply_chat_template 실패, 기본 형식 사용: {str(e)}")
        
        # Fallback: 기본 Llama 3.2 Instruct 형식
        formatted = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_part}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        return formatted
    
    def _clean_instruct_response(self, response: str) -> str:
        """Instruct 모델 응답에서 불필요한 태그 제거"""
        # Llama 특수 토큰 제거
        response = response.replace("<|eot_id|>", "").strip()
        response = response.replace("<|start_header_id|>", "").strip()
        response = response.replace("<|end_header_id|>", "").strip()
        
        # 헤더 태그 제거
        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()
        
        return response
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_length: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """채팅 형식으로 응답 생성"""
        try:
            # 메시지를 프롬프트로 변환
            prompt = self._format_messages(messages)
            
            return self.generate(
                prompt=prompt,
                max_length=max_length,
                temperature=temperature,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"채팅 오류: {str(e)}")
            raise
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """메시지 리스트를 프롬프트로 변환"""
        if self.is_instruct_model:
            # Instruct 모델용: 토크나이저의 apply_chat_template 사용
            if hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template is not None:
                try:
                    # 메시지 형식 정규화
                    formatted_messages = []
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role in ["system", "user", "assistant"]:
                            formatted_messages.append({"role": role, "content": content})
                    
                    if formatted_messages:
                        formatted = self.tokenizer.apply_chat_template(
                            formatted_messages,
                            tokenize=False,
                            add_generation_prompt=True
                        )
                        return formatted
                except Exception as e:
                    logger.warning(f"apply_chat_template 실패, 수동 변환 사용: {str(e)}")
            
            # Fallback: 수동 변환
            system_msg = None
            user_msgs = []
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    system_msg = content
                elif role == "user":
                    user_msgs.append(content)
            
            user_message = user_msgs[-1] if user_msgs else messages[-1].get("content", "") if messages else ""
            system_message = system_msg or "너는 친절하고 유용한 AI 어시스턴트입니다."
            
            return self._format_instruct_prompt(
                f"[시스템]\n{system_message}\n[사용자]\n{user_message}"
            )
        else:
            # 일반 모델용 형식
            prompt_parts = []
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt_parts.append(f"[시스템]\n{content}\n")
                elif role == "user":
                    prompt_parts.append(f"[사용자]\n{content}\n")
                elif role == "assistant":
                    prompt_parts.append(f"[어시스턴트]\n{content}\n")
            
            # 마지막에 어시스턴트 응답 시작 표시
            prompt_parts.append("[어시스턴트]\n")
            
            return "\n".join(prompt_parts)
    
    def is_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self.model is not None and self.tokenizer is not None


# 전역 인스턴스 (싱글톤 패턴)
_llm_service: Optional[HuggingFaceLLMService] = None

def get_llm_service() -> HuggingFaceLLMService:
    """LLM 서비스 인스턴스 가져오기 (싱글톤)"""
    global _llm_service
    if _llm_service is None:
        _llm_service = HuggingFaceLLMService()
    return _llm_service


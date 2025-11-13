import base64
import os
import re
import logging
from pathlib import Path
from typing import Iterable, List, Union

from openai import OpenAI, OpenAIError
"""
    GPT VLM 기반 식재료 추출 과정
"""
logger = logging.getLogger(__name__)


class GptVlmIngredientExtractor:
    def __init__(
        self,
        # api_key: str | None = None,
        # model: str | None = None,
        # user_prompt: str | None = None,
        # client: OpenAI | None = None,
        api_key: Union[str, None] = None,
        model: Union[str, None] = None,
        user_prompt: Union[str, None] = None,
        client: Union[OpenAI, None] = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            env_path = Path(__file__).resolve().parents[1] / ".env"
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and stripped.startswith("OPENAI_API_KEY="):
                        self.api_key = stripped.split("=", 1)[1].strip()
                        break
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

        self.model = model or os.getenv("OPENAI_VLM_MODEL", "gpt-4o-mini")
        
        self.default_prompt = user_prompt or (
            "사진에서 보이는 모든 식재료 이름을 한국어로 쉼표로 구분하여 한 줄로 나열해 주세요. "
            "식재료명 외의 설명은 하지 않습니다."
        )
        
        logger.info("GPT VLM 클라이언트 초기화 (model=%s)", self.model)
        import time
        start = time.perf_counter()
        try:
            self.client = client or OpenAI(
                api_key=self.api_key,
                timeout=30.0
            )
        except Exception:
            logger.exception("GPT VLM 클라이언트 생성 실패")
            raise
        logger.info("GPT VLM 클라이언트 준비 완료 (%.2f초)", time.perf_counter() - start)

    def _prepare_source(self, target: Union[str, bytes, bytearray, Iterable[bytes]]) -> bytes:
        if isinstance(target, str):
            image_path = os.path.abspath(target)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            with open(image_path, "rb") as image_file:
                return image_file.read()

        if isinstance(target, (bytes, bytearray)):
            return bytes(target)

        if hasattr(target, "read"):
            data = target.read()
            if isinstance(data, str):
                data = data.encode("utf-8")
            if hasattr(target, "seek"):
                target.seek(0)
            return data

        raise TypeError("이미지 경로, 바이트, 혹은 파일 객체를 입력해야 합니다.")

    def _encode_image(self, raw: bytes) -> str:
        return base64.b64encode(raw).decode("utf-8")

    def _request(self, image_base64: str, yolo_results: List[str] = None) -> str:
        try:
            if yolo_results and len(yolo_results) > 0:
                yolo_items = ", ".join(yolo_results)
                prompt = (
                    f"사진에서 보이는 모든 식재료를 한국어로 찾아주세요.\n\n"
                    f"AI 모델이 이미 다음 식재료들을 검출했습니다: {yolo_items}\n\n"
                    f"위 항목들은 한국어로 번역하고, 사진에서 보이는 추가 식재료도 함께 찾아주세요. "
                    f"특히 육류, 해산물 등 AI가 놓친 식재료를 중점적으로 찾아주세요."
                    f"하지만 과일류와 조미료는 빼주세요."
                    f"모든 식재료를 한국에서 자주 쓰이는 식재료명으로 바꿔주고 쉼표로 구분하여 한국어로 번역해서 한 줄로 나열해 주세요. "
                    f"식재료명 외의 설명은 하지 않습니다."
                )
            else:
                prompt = self.default_prompt
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=256,
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
            
        except OpenAIError as error:
            logger.error(f"GPT VLM API 호출 실패: {error}")
            raise RuntimeError(f"GPT VLM API 호출 실패: {error}") from error
        except Exception as error:
            logger.error(f"예상치 못한 오류: {error}")
            raise RuntimeError(f"GPT VLM 처리 중 오류: {error}") from error

    def _parse_ingredients(self, text: str) -> List[str]:
        raw = text.strip()
        if not raw:
            return []

        candidates = re.split(r"[\n,;]+", raw)
        cleaned = []
        for item in candidates:
            name = item.strip().strip("-•*").strip()
            if name:
                cleaned.append(name)

        unique = []
        seen = set()
        for name in cleaned:
            lower = name.lower()
            if lower not in seen:
                seen.add(lower)
                unique.append(name)
        return unique

    def extract(self, target: Union[str, bytes, bytearray, Iterable[bytes]], yolo_results: List[str] = None) -> dict:
        try:
            image_bytes = self._prepare_source(target)
            image_base64 = self._encode_image(image_bytes)
            text = self._request(image_base64, yolo_results)
            ingredients = self._parse_ingredients(text)
            
            message = None if ingredients else "이미지에서 식재료를 찾지 못했습니다."
            
            return {
                "ingredients": ingredients,
                "message": message,
                "raw_text": text,
            }
        except Exception as e:
            logger.error(f"식재료 추출 중 오류: {e}")
            return {
                "ingredients": [],
                "message": f"오류 발생: {str(e)}",
                "raw_text": "",
                "error": str(e)
            }

    def __call__(self, target: Union[str, bytes, bytearray, Iterable[bytes]], yolo_results: List[str] = None) -> dict:
        return self.extract(target, yolo_results)

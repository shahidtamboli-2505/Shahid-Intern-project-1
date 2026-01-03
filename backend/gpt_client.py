# backend/gpt_client.py
from __future__ import annotations

import re
import json
import asyncio
from typing import List, Dict, Any, Optional
import torch

# ✅ Flexible imports (works from anywhere)
try:
    from backend.config import (
        HUGGINGFACE_TOKEN,
        HF_MODEL_NAME,
        USE_4BIT_QUANTIZATION,
        MAX_NEW_TOKENS,
        LLM_TEMPERATURE,
        FORCE_CPU
    )
except ImportError:
    from config import (
        HUGGINGFACE_TOKEN,
        HF_MODEL_NAME,
        USE_4BIT_QUANTIZATION,
        MAX_NEW_TOKENS,
        LLM_TEMPERATURE,
        FORCE_CPU
    )

# Hugging Face imports
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False
    AutoTokenizer = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None


# -----------------------------
# Helpers
# -----------------------------
def _norm(s: Any) -> str:
    s = "" if s is None else str(s)
    s = re.sub(r"\s+", " ", s.strip())
    return s


def _safe_json_load(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None


def _extract_json_from_text(text: str) -> Any:
    """Extract JSON from LLM response (handles markdown code blocks)"""
    text = text.strip()
    
    # Remove markdown code blocks
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Fallback: try parsing whole text
    return _safe_json_load(text)


def _clean_leaders(obj: Any, max_leaders: int = 5) -> List[Dict[str, str]]:
    """
    Accepts:
      - {"leaders": [...]}
      - [...]
    Returns:
      - [{"name": "...", "role": "..."}]
    """
    if max_leaders <= 0:
        max_leaders = 5

    items: Any
    if isinstance(obj, dict):
        items = obj.get("leaders", [])
    elif isinstance(obj, list):
        items = obj
    else:
        items = []

    if not isinstance(items, list):
        return []

    out: List[Dict[str, str]] = []
    seen = set()
    for it in items:
        if not isinstance(it, dict):
            continue
        name = _norm(it.get("name"))
        role = _norm(it.get("role")) or _norm(it.get("designation"))
        if not name or not role:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "role": role})
        if len(out) >= max_leaders:
            break
    return out


# ---------------------------------------------------------
# Hugging Face LLM Client
# ---------------------------------------------------------
class GeminiClient:
    """
    🤖 Hugging Face LLM Client (replacing OpenAI/Gemini)
    Backward-compatible class name for existing code.
    """

    def __init__(self) -> None:
        self.model_name: str = HF_MODEL_NAME
        self._disabled: bool = False
        self.device = "cpu" if FORCE_CPU else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer: Any = None
        self.model: Any = None
        
        print(f"🤖 LLM Client initializing...")
        print(f"📦 Model: {self.model_name}")
        print(f"💻 Device: {self.device}")

    def is_enabled(self) -> bool:
        """Check if Hugging Face is available and configured"""
        if self._disabled:
            return False
        if not HF_AVAILABLE:
            print("❌ Transformers library not available")
            return False
        if not HUGGINGFACE_TOKEN:
            print("❌ Hugging Face token not configured")
            return False
        return True

    def _ensure_model(self) -> bool:
        """Lazy load model only when needed"""
        if not self.is_enabled():
            return False
        
        if self.model is not None and self.tokenizer is not None:
            return True

        try:
            print(f"📥 Loading model: {self.model_name}...")
            
            # Setup quantization config
            quantization_config = None
            if USE_4BIT_QUANTIZATION and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=HUGGINGFACE_TOKEN,
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=HUGGINGFACE_TOKEN,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            if self.device == "cpu":
                self.model = self.model.to("cpu")
            
            print(f"✅ Model loaded successfully on {self.device}!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self._disabled = True
            self.model = None
            self.tokenizer = None
            return False

    def _generate_response(self, prompt: str, max_tokens: int = None) -> str:
        """Generate response from LLM"""
        if not self._ensure_model():
            return "{}"
        
        if max_tokens is None:
            max_tokens = MAX_NEW_TOKENS

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=LLM_TEMPERATURE,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove prompt from response
            response = response.replace(prompt, "").strip()
            
            return response
            
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return "{}"

    async def discovery_search_async(self, company_name: str, website: str) -> List[Dict[str, str]]:
        """
        LLM-only leadership extraction.
        Returns: [{"name":"...","role":"..."}]
        """
        if not self._ensure_model():
            return []

        company_name = _norm(company_name) or "this company"
        website = _norm(website)
        if not website:
            return []

        # Prompt template (varies by model)
        # For Llama-2
        if "llama" in self.model_name.lower():
            prompt = f"""[INST] You are an expert at extracting leadership information.

Task: Extract current top management of the company.

Company: {company_name}
Website: {website}

Return ONLY valid JSON with this exact format:
{{
  "leaders": [
    {{ "name": "Full Name", "role": "CEO" }}
  ]
}}

Rules:
- Maximum 5 leaders
- Focus on: CEO, Founder, Co-Founder, Managing Director, Director, CTO, COO, CFO
- If no information available, return: {{ "leaders": [] }}
- No markdown, no explanations, only JSON

[/INST]"""
        else:
            # Generic prompt
            prompt = f"""Extract current top management of the company.

Company: {company_name}
Website: {website}

Return ONLY JSON:
{{
  "leaders": [
    {{ "name": "Full Name", "role": "Role/Title" }}
  ]
}}

Rules:
- Max 5
- Focus on CEO, Founder, Co-Founder, Managing Director, Director, CTO, COO, CFO
- If unsure, return {{ "leaders": [] }}
"""

        try:
            # Run in thread to avoid blocking
            response = await asyncio.to_thread(self._generate_response, prompt, 300)
            
            data = _extract_json_from_text(response)
            if not data:
                return []
            
            return _clean_leaders(data, max_leaders=5)

        except Exception as e:
            print(f"❌ Discovery search error: {e}")
            return []

    def clean_leadership_data(self, raw_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        LLM cleaning: remove junk/menu items and normalize roles.
        """
        if not raw_data:
            return []

        if not self._ensure_model():
            return raw_data[:5]

        if "llama" in self.model_name.lower():
            prompt = f"""[INST] Clean and normalize this leadership list.

Rules:
- Remove navigation/menu items, slogans, page headings, locations, departments
- Keep only real people with proper names and roles
- Ensure each item has "name" and "role"
- Maximum 5 entries

Return ONLY valid JSON:
{{
  "leaders": [
    {{ "name": "Full Name", "role": "Role/Title" }}
  ]
}}

Data to clean:
{json.dumps(raw_data, ensure_ascii=False)}

[/INST]"""
        else:
            prompt = f"""Clean this leadership list. Remove junk, keep only real people.

Data:
{json.dumps(raw_data, ensure_ascii=False)}

Return ONLY JSON:
{{
  "leaders": [
    {{ "name": "Full Name", "role": "Role/Title" }}
  ]
}}
"""

        try:
            response = self._generate_response(prompt, 300)
            data = _extract_json_from_text(response)
            
            if not data:
                return raw_data[:5]
            
            cleaned = _clean_leaders(data, max_leaders=5)
            return cleaned if cleaned else raw_data[:5]

        except Exception as e:
            print(f"❌ Cleaning error: {e}")
            return raw_data[:5]

    def normalize_top_level_management(self, raw_title: str) -> str:
        """
        Rule-based bucket mapping for consistent dashboard categorization.
        """
        title = (raw_title or "").strip()
        if not title:
            return "General Management"
        t = re.sub(r"\s+", " ", title).lower()

        # Executive Leadership
        if re.search(r"\b(founder|ceo\b|director|president|md\b|chairman|principal|chief executive)\b", t):
            return "Executive Leadership"
        # Finance / Admin
        if re.search(r"\b(cfo\b|finance|accounts|admin|hr\b|human resources|legal|compliance)\b", t):
            return "Finance / Administration"
        # Tech / Ops
        if re.search(r"\b(cto\b|technology|it\b|engineering|operations|ops\b|production|technical)\b", t):
            return "Technology / Operations"
        # Growth / BD
        if re.search(r"\b(sales|growth|business development|bd\b|strategy|revenue|commercial)\b", t):
            return "Business Development / Growth"
        # Marketing
        if re.search(r"\b(marketing|brand|branding|pr\b|communications|digital)\b", t):
            return "Marketing / Branding"

        return "Other Management"
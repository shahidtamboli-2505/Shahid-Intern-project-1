# backend/gpt_client.py
# GOOGLE PLACES ONLY PROJECT
# GPT is DISABLED (safe stub)

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GPTClient:
    """
    Stub GPT client.
    Project currently uses ONLY Google Places data.
    GPT categorization is intentionally disabled.
    """

    def is_enabled(self) -> bool:
        return False

    def classify_primary_category_case1(
        self,
        name: str,
        raw_category: str = "",
        address: str = "",
        allowed: Optional[List[str]] = None,
    ) -> str:
        """
        GPT disabled → always return empty string.
        Miner will fallback to raw_category.
        """
        return ""

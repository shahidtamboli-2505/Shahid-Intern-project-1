# backend/gpt_client.py
# GOOGLE PLACES ONLY PROJECT
# 🔒 GPT is DISABLED (SAFE STUB)
# ✅ Case-2 ready structure (no GPT calls)

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GPTClient:
    """
    GPT Client Stub (INTENTIONALLY DISABLED)

    Purpose:
    - Maintain clean pipeline architecture
    - Allow future AI extension (Case-2 / Case-3)
    - Ensure current project remains deterministic + exam-safe

    ⚠️ No OpenAI calls are made from this class.
    """

    # -----------------------------
    # Global toggle
    # -----------------------------
    def is_enabled(self) -> bool:
        """
        Always False.
        Used by pipeline to ensure GPT logic is never triggered.
        """
        return False

    # -----------------------------
    # Case-1: Primary category classification (DISABLED)
    # -----------------------------
    def classify_primary_category_case1(
        self,
        name: str,
        raw_category: str = "",
        address: str = "",
        allowed: Optional[List[str]] = None,
    ) -> str:
        """
        GPT disabled → return empty string.

        Fallback behavior:
        - Miner uses raw_category from Google Places
        """
        return ""

    # -----------------------------
    # Case-2: Top-level management role normalization (STUB)
    # -----------------------------
    def normalize_top_level_management(
        self,
        raw_title: str,
        context: str = "",
    ) -> str:
        """
        Case-2 PLACEHOLDER (no GPT).

        Example inputs:
          - "Managing Director"
          - "Principal"
          - "Head of IT"
          - "Chief Marketing Officer"

        Future normalized outputs:
          - Executive Leadership
          - Technology / Operations
          - Finance / Administration
          - Business Development / Growth
          - Marketing / Branding

        Current behavior:
          - GPT disabled
          - Rule-based logic will be used instead
        """
        return ""

    # -----------------------------
    # Case-2: Relationship extraction (STUB)
    # -----------------------------
    def extract_relationship_type(
        self,
        text: str,
    ) -> str:
        """
        Placeholder for future:
        - Client / Vendor / Partner classification

        GPT disabled → always empty.
        """
        return ""

# backend/gpt_client.py
# GOOGLE PLACES ONLY PROJECT
# 🔒 GPT is DISABLED (SAFE STUB)
# ✅ Case-2 ready: RULE-BASED bucket mapping (no OpenAI calls)

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class GPTClient:
    """
    GPT Client Stub (INTENTIONALLY DISABLED)

    What this file DOES now:
    - Keeps pipeline architecture clean
    - NO OpenAI calls
    - Provides rule-based normalization for Case-2 management buckets (optional but useful)

    Buckets:
    - Executive Leadership
    - Technology / Operations
    - Finance / Administration
    - Business Development / Growth
    - Marketing / Branding
    """

    # -----------------------------
    # Global toggle
    # -----------------------------
    def is_enabled(self) -> bool:
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
        # GPT disabled → return empty string.
        return ""

    # -----------------------------
    # Case-2: Rule-based bucket mapping (NO GPT)
    # -----------------------------
    def normalize_top_level_management(
        self,
        raw_title: str,
        context: str = "",
    ) -> str:
        """
        Map a designation/title into one of 5 buckets WITHOUT GPT.

        Inputs: "CEO", "Founder", "CTO", "Dean", "Principal", "Head of Operations", etc.

        Returns one of:
          - "Executive Leadership"
          - "Technology / Operations"
          - "Finance / Administration"
          - "Business Development / Growth"
          - "Marketing / Branding"
          - "" (unknown)
        """
        title = (raw_title or "").strip()
        if not title:
            return ""

        t = re.sub(r"\s+", " ", title).lower()

        # Executive Leadership
        if re.search(
            r"\b(founder|co-founder|chairman|chairperson|managing director|md\b|"
            r"chief executive officer|ceo\b|director|president|principal|dean|"
            r"vice chancellor|chancellor|registrar)\b",
            t,
        ):
            return "Executive Leadership"

        # Finance / Administration
        if re.search(
            r"\b(cfo\b|chief financial|finance|accounts|accounting|controller|admin|"
            r"administration|hr\b|human resources|compliance|legal)\b",
            t,
        ):
            return "Finance / Administration"

        # Technology / Operations
        if re.search(
            r"\b(cto\b|chief technology|technology|it\b|engineering|developer|devops|"
            r"operations|ops\b|plant head|production|maintenance|quality|qa\b|hod\b|head of)\b",
            t,
        ):
            return "Technology / Operations"

        # Business Development / Growth
        if re.search(
            r"\b(business development|bd\b|sales|growth|partnerships?|alliances?|revenue|"
            r"commercial|strategy)\b",
            t,
        ):
            return "Business Development / Growth"

        # Marketing / Branding
        if re.search(
            r"\b(cmo\b|chief marketing|marketing|brand|branding|communications?|pr\b|"
            r"public relations|digital marketing|social media)\b",
            t,
        ):
            return "Marketing / Branding"

        return ""

    # -----------------------------
    # Case-2: Relationship extraction (STUB)
    # -----------------------------
    def extract_relationship_type(self, text: str) -> str:
        # GPT disabled → always empty.
        return ""

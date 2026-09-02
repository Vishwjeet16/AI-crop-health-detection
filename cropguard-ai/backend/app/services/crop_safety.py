"""
Deterministic guardrail for treatment advice.

Section 33 of the spec: the system must never invent pesticide names, doses, or
chemical concentrations. For the template-based recommendation engine that rule
is satisfied by review — every string in recommendation_service.TEMPLATES is
written by hand. The AI assistant generates text at runtime, so review isn't
available and a mechanical check is needed instead.

This module is that check. It is deliberately a blunt regex scan rather than a
model-based judgement: a farmer acting on a hallucinated dose is a real-world
harm, so the failure mode has to be "refuses something harmless" rather than
"lets one through". Both the assistant's output and the reviewed templates are
scanned against it (see tests/test_recommendation_service.py), so the same
standard applies to hand-written and generated text.
"""

from __future__ import annotations

import re

# Active ingredients commonly sold to Indian farmers. Not exhaustive — no such
# list could be — which is why the dose-unit patterns below matter just as much:
# a chemical this list misses is still caught the moment a quantity is attached.
_ACTIVE_INGREDIENTS = (
    "mancozeb",
    "chlorothalonil",
    "copper oxychloride",
    "copper hydroxide",
    "bordeaux mixture",
    "imidacloprid",
    "carbendazim",
    "propiconazole",
    "azoxystrobin",
    "difenoconazole",
    "tebuconazole",
    "hexaconazole",
    "metalaxyl",
    "cymoxanil",
    "cymoxanyl",
    "dimethomorph",
    "fosetyl",
    "thiamethoxam",
    "acetamiprid",
    "acephate",
    "chlorpyrifos",
    "quinalphos",
    "monocrotophos",
    "dimethoate",
    "profenofos",
    "cypermethrin",
    "deltamethrin",
    "lambda.?cyhalothrin",
    "fipronil",
    "emamectin",
    "abamectin",
    "spinosad",
    "chlorantraniliprole",
    "flubendiamide",
    "indoxacarb",
    "thiodicarb",
    "buprofezin",
    "diafenthiuron",
    "spiromesifen",
    "propargite",
    "dicofol",
    "streptomycin",
    "validamycin",
    "kasugamycin",
    "paraquat",
    "glyphosate",
    "atrazine",
    "pendimethalin",
    # 2,4-D and its spacing variants. Tight on purpose: a looser pattern
    # matched innocent numbers like "24 d(ays)".
    r"2\s*,\s*4[-\s]?d",
)

# (label, pattern). The label is what gets logged when something is blocked, so
# it should say which rule fired without echoing the blocked text.
PROHIBITED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "named active ingredient",
        re.compile(r"\b(?:%s)\b" % "|".join(_ACTIVE_INGREDIENTS), re.IGNORECASE),
    ),
    (
        # "2 ml/litre", "500 g per acre", "1.5 kg/ha"
        "dose per unit volume or area",
        re.compile(
            r"\b\d+(?:[.,]\d+)?\s*"
            r"(?:ml|mL|millilit(?:re|er)s?|g|gm|gram(?:s)?|kg|l|lit(?:re|er)s?)\s*"
            r"(?:/|per\s+)\s*"
            r"(?:l\b|lit(?:re|er)s?|acre|ha\b|hectare|plant|pump|tank|bigha|guntha)",
            re.IGNORECASE,
        ),
    ),
    (
        # Bare unit ratios with no leading number: "ml/l", "g/acre".
        "dose unit ratio",
        re.compile(
            r"\b(?:ml|g|gm|kg)\s*/\s*(?:l|lit(?:re|er)|acre|ha|hectare)\b",
            re.IGNORECASE,
        ),
    ),
    (
        # Formulation strengths: "75% WP", "25 % EC".
        "formulation concentration",
        re.compile(r"\b\d+(?:[.,]\d+)?\s*%\s*(?:ec|sc|wp|wg|sl|sp|ws|as|me|od|fs)\b", re.IGNORECASE),
    ),
    (
        # A spray concentration expressed as a percentage: "spray at 0.2%".
        "spray concentration",
        re.compile(
            r"\b(?:spray|dilut\w*|mix|solution|concentration|drench)\b[^.\n]{0,40}?"
            r"\b\d+(?:[.,]\d+)?\s*%",
            re.IGNORECASE,
        ),
    ),
)


def find_prohibited(text: str) -> list[str]:
    """Return the labels of every rule the text trips. Empty means clean."""
    if not text:
        return []
    return [label for label, pattern in PROHIBITED_PATTERNS if pattern.search(text)]


def contains_prohibited(text: str) -> bool:
    return bool(find_prohibited(text))

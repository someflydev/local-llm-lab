from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator

import yaml
from pydantic import BaseModel, Field


class HardwareProfile(BaseModel):
    unified_memory_gb: int
    free_storage_gb: int
    recommended_max_class: str
    safe_default_num_ctx: int
    cautious_max_num_ctx: int
    notes: list[str] = Field(default_factory=list)


class ModelEntry(BaseModel):
    name: str
    provider: str
    roles: list[str]
    priority: int
    notes: str
    default_temperature: float | None = None
    default_num_ctx: int | None = None


class FallbackRules(BaseModel):
    prefer_roles: dict[str, list[str]] = Field(default_factory=dict)
    min_priority: int = 0
    notes: str | None = None


class ModelsConfig(BaseModel):
    version: int
    hardware_profiles: dict[str, HardwareProfile]
    known_good: list[ModelEntry] = Field(default_factory=list)
    preferred_variants: list[ModelEntry] = Field(default_factory=list)
    embedding_models: list[ModelEntry] = Field(default_factory=list)
    candidates_reasoning: list[ModelEntry] = Field(default_factory=list)
    candidates_long_context: list[ModelEntry] = Field(default_factory=list)
    fallback_rules: FallbackRules


@lru_cache(maxsize=1)
def load_models_config() -> ModelsConfig:
    path = Path("experiments") / "models.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ModelsConfig.model_validate(data)


def get_hardware_profile(profile_name: str = "mac_m3_pro_18gb_sonoma_14_5") -> HardwareProfile:
    return load_models_config().hardware_profiles[profile_name]


def iter_all_model_entries() -> Iterator[ModelEntry]:
    cfg = load_models_config()
    for bucket in (
        cfg.known_good,
        cfg.preferred_variants,
        cfg.embedding_models,
        cfg.candidates_reasoning,
        cfg.candidates_long_context,
    ):
        yield from bucket


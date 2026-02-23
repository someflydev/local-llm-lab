from __future__ import annotations

import subprocess
from typing import Literal

from lab.modelspec import ModelEntry, get_hardware_profile, iter_all_model_entries, load_models_config
from lab.ollama_client import parse_ollama_list_output

TaskName = Literal["chat", "rag_qa", "embeddings"]


def _base_name(model_name: str) -> str:
    return model_name.split(":", 1)[0].strip().lower()


def _matches(installed_name: str, policy_name: str) -> bool:
    return _base_name(installed_name) == policy_name.strip().lower()


def _find_installed_match(policy_name: str, installed: set[str]) -> str | None:
    for name in sorted(installed):
        if _matches(name, policy_name):
            return name
    return None


def installed_models() -> set[str]:
    proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Failed to run `ollama list`")
    return set(parse_ollama_list_output(proc.stdout))


def policy_models() -> list[ModelEntry]:
    return list(iter_all_model_entries())


def match_installed_to_policy() -> dict[str, list[ModelEntry]]:
    cfg = load_models_config()
    installed = installed_models()

    def available(entries: list[ModelEntry]) -> list[ModelEntry]:
        return [entry for entry in entries if _find_installed_match(entry.name, installed)]

    recommended = cfg.known_good + cfg.preferred_variants + cfg.embedding_models
    return {
        "available_known_good": available(cfg.known_good),
        "available_preferred_variants": available(cfg.preferred_variants),
        "available_embeddings": available(cfg.embedding_models),
        "available_candidates": available(cfg.candidates_reasoning + cfg.candidates_long_context),
        "missing_recommended": [entry for entry in recommended if not _find_installed_match(entry.name, installed)],
    }


def _task_matches_entry(task: TaskName, entry: ModelEntry) -> bool:
    cfg = load_models_config()
    if task in entry.roles:
        return True
    fallback_roles = cfg.fallback_rules.prefer_roles.get(task, [])
    return any(role in entry.roles for role in fallback_roles)


def _select_best(installed: set[str], entries: list[ModelEntry], task: TaskName) -> tuple[ModelEntry | None, str | None]:
    cfg = load_models_config()
    eligible = [
        entry
        for entry in entries
        if entry.priority >= cfg.fallback_rules.min_priority
        and _task_matches_entry(task, entry)
        and _find_installed_match(entry.name, installed)
    ]
    if not eligible:
        return None, None

    best = sorted(eligible, key=lambda item: item.priority, reverse=True)[0]
    return best, _find_installed_match(best.name, installed)


def recommend(task: TaskName) -> dict:
    cfg = load_models_config()
    hardware = get_hardware_profile()
    installed = installed_models()

    chosen_entry: ModelEntry | None = None
    chosen_model_name: str | None = None
    reason = ""

    if task in {"chat", "rag_qa"}:
        match = _find_installed_match("llama3", installed)
        if match:
            chosen_entry = next((entry for entry in cfg.known_good if entry.name == "llama3"), None)
            chosen_model_name = match
            reason = "Preferred known-good default for chat and RAG QA."

    if task == "embeddings" and chosen_entry is None:
        chosen_entry, chosen_model_name = _select_best(installed, cfg.embedding_models, task)
        if chosen_entry:
            reason = "Selected highest-priority installed embeddings policy model."

    if chosen_entry is None:
        chosen_entry, chosen_model_name = _select_best(installed, policy_models(), task)
        if chosen_entry:
            reason = "Selected highest-priority installed model matching task or fallback roles."

    defaults = {
        "temperature": (chosen_entry.default_temperature if chosen_entry else None) or 0.2,
        "num_ctx": (chosen_entry.default_num_ctx if chosen_entry else None) or hardware.safe_default_num_ctx,
    }

    suggestions: list[str] = []
    for entry in sorted(policy_models(), key=lambda item: item.priority, reverse=True):
        if _task_matches_entry(task, entry) and not _find_installed_match(entry.name, installed):
            if entry.name not in suggestions:
                suggestions.append(entry.name)

    if chosen_model_name is None and not reason:
        reason = "No installed model matched the policy for this task."

    return {
        "chosen_model": chosen_model_name,
        "reason": reason,
        "suggested_pulls": suggestions[:5],
        "defaults": defaults,
    }


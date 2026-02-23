.DEFAULT_GOAL := help

PYTHON_VERSION ?= 3.12
RUNS_DIR ?= runs

.PHONY: help bootstrap check verify smoke-fixture clean-runs-preview clean-runs release-check

help: ## Show available targets
	@awk 'BEGIN {FS = ": .*## "}; /^[a-zA-Z0-9_.-]+: .*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Run local bootstrap checks/setup (may check live Ollama)
	./scripts/bootstrap_mac.sh

check: ## Deterministic lint + tests (no live Ollama required)
	uv run --python $(PYTHON_VERSION) --with ruff ruff check .
	uv run --python $(PYTHON_VERSION) python -m unittest discover -s tests

verify: ## Run repo verification script (may use live Ollama if available)
	./scripts/verify.sh

smoke-fixture: ## Deterministic fixture/mocked smoke tests
	uv run --python $(PYTHON_VERSION) python -m unittest \
		tests.test_cli_parser \
		tests.test_rag_threshold \
		tests.test_integration_basics \
		tests.test_web_smoke

clean-runs-preview: ## Show what would be deleted under RUNS_DIR (default: runs)
	@runs_dir="$(RUNS_DIR)"; \
	if [ ! -d "$$runs_dir" ]; then \
		echo "[clean-runs-preview] $$runs_dir does not exist"; \
		exit 0; \
	fi; \
	echo "[clean-runs-preview] Candidates under $$runs_dir:"; \
	found=0; \
	for path in "$$runs_dir"/*; do \
		if [ -e "$$path" ]; then \
			found=1; \
			echo "  $$path"; \
		fi; \
	done; \
	if [ "$$found" -eq 0 ]; then \
		echo "  (none)"; \
	fi

clean-runs: ## Delete contents under RUNS_DIR (guarded; requires CONFIRM=1)
	@runs_dir="$(RUNS_DIR)"; \
	if [ "$${CONFIRM:-0}" != "1" ]; then \
		echo "[clean-runs] Refusing to delete. Re-run with CONFIRM=1"; \
		exit 1; \
	fi; \
	if [ ! -d "$$runs_dir" ]; then \
		echo "[clean-runs] $$runs_dir does not exist"; \
		exit 0; \
	fi; \
	case "$$runs_dir" in \
		""|"/"|".") echo "[clean-runs] Refusing unsafe RUNS_DIR=$$runs_dir"; exit 1 ;; \
	esac; \
	echo "[clean-runs] Deleting contents under $$runs_dir"; \
	find "$$runs_dir" -mindepth 1 -maxdepth 1 -exec rm -rf {} +; \
	echo "[clean-runs] Done"

release-check: ## Run release prep checks (set ALLOW_DIRTY=1 while iterating)
	@dirty_flag=""; \
	if [ "$${ALLOW_DIRTY:-0}" = "1" ]; then dirty_flag="--allow-dirty"; fi; \
	./scripts/release_prep.sh --check $$dirty_flag

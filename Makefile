.PHONY: molecule

# Also needs to be updated in galaxy.yml
VERSION = 1.0.3

SANITY_TEST_ARGS ?= --docker --color
UNITS_TEST_ARGS ?= --docker --color
PYTHON_VERSION ?= `python3 -c 'import platform; print("{0}.{1}".format(platform.python_version_tuple()[0], platform.python_version_tuple()[1]))'`

clean:
	rm -f network-offline_migration_sdn_to_ovnk-$(VERSION).tar.gz
	rm -rf $(HOME)/.ansible/collections/ansible_collections/*

build: clean
	ansible-galaxy collection build --force .

install: build
	ansible-galaxy collection install --force ./network-offline_migration_sdn_to_ovnk-*.tar.gz

sanity: install
	cd $(HOME)/.ansible/collections/ansible_collections/network/offline_migration_sdn_to_ovnk && ansible-test sanity -v --python $(PYTHON_VERSION) $(SANITY_TEST_ARGS)

lint: install
	cd $(HOME)/.ansible/collections/ansible_collections/network/offline_migration_sdn_to_ovnk && ansible-lint --profile production

test-integration-incluster:
	./ci/incluster_integration.sh

test-integration:
	./ci/test-integration.sh

# ---------------------------------------------------------------------------
# Validate the collection with galaxy-importer (direct git-clone-path mode)
#  • Auto-installs galaxy-importer 0.4.31 if it is missing
#  • Streams output to both the console and ./logs/collection_ci.log
# ---------------------------------------------------------------------------
LOGFILE ?= ./logs/collection_ci.log  # override: make LOGFILE=/tmp/foo.log import
PYTHON  := $(shell command -v python3 2>/dev/null || command -v python)

# Helper: 0 = importer present, 1 = missing
define CHECK_GALAXY_IMPORTER
$(PYTHON) - <<'PY' 2>/dev/null
try:
    import galaxy_importer
except ImportError:
    raise SystemExit(1)
PY
endef

.PHONY: import
import:                     ## make import   → validate collection
	@# ─── 0. Prerequisite checks + optional install ────────────────────────
	@{ \
	  PYTHON="$(PYTHON)"; \
	  if [ -z "$$PYTHON" ]; then \
	    echo "❌  python3 (or python) not found in PATH" >&2; exit 127; \
	  fi; \
	  if ! "$$PYTHON" -c 'import importlib.util,sys; sys.exit(0 if importlib.util.find_spec("galaxy_importer") else 1)'; then \
	    echo "🔧  Installing galaxy-importer==0.4.31 …"; \
	    "$$PYTHON" -m pip install --user --quiet galaxy-importer==0.4.31; \
	  fi; \
	}

	@# ─── 1. Prepare log directory & tidy up any stale tarball ──────────────
	@mkdir -p $(dir $(LOGFILE))
	@rm -f /tmp/network-offline_migration_sdn_to_ovnk-*.tar.gz

	@# ─── 2. Kick-off message (console + log) ──────────────────────────────
	@echo "`date '+%F %T'` 🚀  Starting galaxy-importer validation (git-clone-path mode)" | tee -a $(LOGFILE)

	@# ─── 3. Run galaxy-importer itself ────────────────────────────────────
	@{ \
	  PYTHON="$(PYTHON)"; \
	  GAL_CFG=$$(mktemp); \
	  printf "[galaxy-importer]\nCHECK_REQUIRED_TAGS=True\n" > "$$GAL_CFG"; \
	  echo "`date '+%F %T'` 🔍  Running galaxy-importer …" | tee -a $(LOGFILE); \
	  if ! GALAXY_IMPORTER_CONFIG="$$GAL_CFG" "$$PYTHON" -m galaxy_importer.main \
	       --git-clone-path . --output-path /tmp 2>&1 | tee -a $(LOGFILE); then \
	    echo "`date '+%F %T'` ❌  galaxy-importer failed" | tee -a $(LOGFILE); \
	    exit 1; \
	  fi; \
	}

	@# ─── 4. Success message ───────────────────────────────────────────────
	@echo "`date '+%F %T'` ✅  Collection validated successfully" | tee -a $(LOGFILE)

.PHONY: publish
publish:  ## Build the collection and publish it to Automation Hub
	@echo "==> Publishing collection (requires AH_TOKEN)…"
	bash hack/publish_collection.sh



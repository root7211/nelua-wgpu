# nelua-wgpu - WebGPU bindings for Nelua
#
# Usage:
#   make setup        - Clone nelua-decl and build GCC Lua plugin
#   make generate     - Generate all bindings from C headers
#   make test         - Run binding tests (requires GPU)
#   make test-all     - Run all tests
#   make update       - Fetch latest headers + regenerate
#   make analyze      - Show API analysis report
#   make validate     - Run binding validation
#   make clean        - Remove generated files
#
# Configuration:
#   NELUA_DECL_PATH   - Path to nelua-decl (default: ./deps/nelua-decl)
#   WGPU_NATIVE_PATH  - Path to wgpu-native libs (default: ./deps/wgpu-native)

NELUA_DECL_PATH ?= ./deps/nelua-decl
WGPU_NATIVE_PATH ?= ./deps/wgpu-native

# Nelua compilation flags for wgpu
WGPU_CFLAGS = -I$(WGPU_NATIVE_PATH)/include
WGPU_LDFLAGS = -L$(WGPU_NATIVE_PATH) -lwgpu_native -ldl -lpthread -lm
NELUA_FLAGS = --add-path . --cflags="$(WGPU_CFLAGS)" --ldflags="$(WGPU_LDFLAGS)"

.PHONY: all setup generate update analyze validate clean help test test-bindings test-highlevel test-all

help:
	@echo "nelua-wgpu - WebGPU bindings for Nelua"
	@echo ""
	@echo "Targets:"
	@echo "  make setup       - Clone nelua-decl and build GCC Lua plugin"
	@echo "  make generate    - Generate all bindings from C headers"
	@echo "  make test        - Run comprehensive binding test"
	@echo "  make test-hl     - Run high-level API test"
	@echo "  make test-all    - Run all tests"
	@echo "  make update      - Fetch latest headers + regenerate"
	@echo "  make macros      - Generate only macro constants (no GCC plugin needed)"
	@echo "  make analyze     - Show API analysis report"
	@echo "  make validate    - Run binding validation"
	@echo "  make clean       - Remove generated files"
	@echo ""
	@echo "Configuration:"
	@echo "  NELUA_DECL_PATH=$(NELUA_DECL_PATH)"

all: generate

# ============================================================================
# Setup: Clone and build nelua-decl
# ============================================================================

setup:
	@echo "=== Setting up nelua-decl ==="
	@if [ ! -d "$(NELUA_DECL_PATH)" ]; then \
		echo "Cloning nelua-decl..."; \
		git clone --recurse-submodules https://github.com/edubart/nelua-decl.git $(NELUA_DECL_PATH); \
	else \
		echo "nelua-decl already exists at $(NELUA_DECL_PATH)"; \
	fi
	@echo "Building GCC Lua plugin..."
	$(MAKE) -C $(NELUA_DECL_PATH)/gcc-lua
	@echo "Setup complete!"

# ============================================================================
# Binding generation
# ============================================================================

generate:
	$(MAKE) -C wgpu-c/codegen NELUA_DECL_PATH=$(abspath $(NELUA_DECL_PATH)) generate

macros:
	@echo "Generating macro constants..."
	cd wgpu-c/codegen && python3 ../../scripts/extract_macros.py webgpu.h wgpu.h > ../webgpu_macros.nelua
	@echo "Done: wgpu-c/webgpu_macros.nelua"

# ============================================================================
# Update from upstream
# ============================================================================

update:
	bash scripts/update.sh

update-tag:
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make update-tag TAG=v27.0.4.0"; \
		exit 1; \
	fi
	bash scripts/update.sh --tag $(TAG)

# ============================================================================
# Tests (require wgpu-native in deps/wgpu-native)
# ============================================================================

test: test-bindings

test-bindings:
	LD_LIBRARY_PATH=$(WGPU_NATIVE_PATH) nelua tests/test_bindings.nelua $(NELUA_FLAGS)

test-hl:
	LD_LIBRARY_PATH=$(WGPU_NATIVE_PATH) nelua tests/test_highlevel.nelua $(NELUA_FLAGS)

test-all: test-bindings test-hl
	@echo "All tests passed!"

# ============================================================================
# Analysis and validation
# ============================================================================

analyze:
	python3 scripts/analyze_api.py

validate:
	python3 tests/validate_bindings.py

# ============================================================================
# Cleanup
# ============================================================================

clean:
	rm -f wgpu-c/webgpu.nelua wgpu-c/webgpu_macros.nelua
	rm -f VERSION
	@echo "Cleaned generated files"

distclean: clean
	rm -rf deps/nelua-decl
	rm -f wgpu-c/codegen/webgpu.h wgpu-c/codegen/wgpu.h
	@echo "Cleaned everything including deps and headers"

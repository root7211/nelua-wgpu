# Makefile for nelua-wgpu binding generation
#
# Prerequisites:
#   - GCC 9+ with plugin support (Linux only)
#   - nelua-decl: https://github.com/edubart/nelua-decl
#   - wgpu-native headers (webgpu.h + wgpu.h) in this directory
#
# Usage:
#   make generate    - Generate Nelua bindings from C headers
#   make download    - Download latest headers from upstream
#   make clean       - Remove generated files
#   make all         - Download headers + generate bindings

# Path to nelua-decl (override with: make NELUA_DECL_PATH=...)
NELUA_DECL_PATH ?= ../../../nelua-decl

# GCC Lua plugin path
GCC_LUA_PLUGIN ?= $(NELUA_DECL_PATH)/gcc-lua/gcc/gcclua.so

# Lua path so the GCC plugin can find nldecl.lua
NLDECL_LUA_PATTERN = $(NELUA_DECL_PATH)/?.lua;;

# Output files
WEBGPU_NELUA = ../webgpu.nelua
MACROS_NELUA = ../webgpu_macros.nelua

# Source files
WEBGPU_C = webgpu_all.c
WEBGPU_LUA = webgpu.lua
MACROS_C = webgpu_macros.c

# Header URLs
WEBGPU_H_URL = https://raw.githubusercontent.com/webgpu-native/webgpu-headers/main/webgpu.h
WGPU_H_URL = https://raw.githubusercontent.com/gfx-rs/wgpu-native/trunk/ffi/wgpu.h

# wgpu-native release info
WGPU_NATIVE_RELEASES_URL = https://api.github.com/repos/gfx-rs/wgpu-native/releases/latest

# ============================================================================
# Targets
# ============================================================================

.PHONY: all generate download clean check-plugin macros version-info

all: download generate

generate: check-plugin $(WEBGPU_NELUA) macros
	@echo "=== Bindings generated successfully ==="
	@echo "Output: $(WEBGPU_NELUA)"
	@echo "Macros: $(MACROS_NELUA)"

$(WEBGPU_NELUA): $(WEBGPU_C) $(WEBGPU_LUA) webgpu.h wgpu.h
	@echo "Generating WebGPU bindings..."
	LUA_PATH="$(NLDECL_LUA_PATTERN)" LUA_PATH_5_3="$(NLDECL_LUA_PATTERN)" LUA_PATH_5_4="$(NLDECL_LUA_PATTERN)" \
		gcc -S $(WEBGPU_C) \
		-fplugin=$(GCC_LUA_PLUGIN) \
		-fplugin-arg-gcclua-script=$(WEBGPU_LUA) \
		> $(WEBGPU_NELUA)
	@echo "Generated: $(WEBGPU_NELUA) ($$(wc -l < $(WEBGPU_NELUA)) lines)"

macros: $(MACROS_NELUA)

$(MACROS_NELUA): webgpu.h wgpu.h
	@echo "Generating macro constants..."
	python3 ../../scripts/extract_macros.py webgpu.h wgpu.h > $(MACROS_NELUA)
	@echo "Generated: $(MACROS_NELUA)"

download:
	@echo "Downloading latest WebGPU headers..."
	curl -sL -o webgpu.h "$(WEBGPU_H_URL)"
	curl -sL -o wgpu.h "$(WGPU_H_URL)"
	@echo "Downloaded: webgpu.h ($$(wc -l < webgpu.h) lines)"
	@echo "Downloaded: wgpu.h ($$(wc -l < wgpu.h) lines)"

version-info:
	@echo "Fetching latest wgpu-native version..."
	@curl -s $(WGPU_NATIVE_RELEASES_URL) | python3 -c \
		"import sys,json; d=json.load(sys.stdin); print('Latest:', d.get('tag_name','unknown'))"

check-plugin:
	@if [ ! -f "$(GCC_LUA_PLUGIN)" ]; then \
		echo "ERROR: GCC Lua plugin not found at: $(GCC_LUA_PLUGIN)"; \
		echo ""; \
		echo "Setup nelua-decl first:"; \
		echo "  git clone --recurse-submodules https://github.com/edubart/nelua-decl.git"; \
		echo "  make -C nelua-decl/gcc-lua"; \
		echo ""; \
		echo "Or set NELUA_DECL_PATH:"; \
		echo "  make NELUA_DECL_PATH=/path/to/nelua-decl generate"; \
		exit 1; \
	fi
	@echo "GCC Lua plugin found: $(GCC_LUA_PLUGIN)"

clean:
	rm -f $(WEBGPU_NELUA) $(MACROS_NELUA)
	@echo "Cleaned generated files"

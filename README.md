# nelua-wgpu

Auto-generated [WebGPU](https://www.w3.org/TR/webgpu/) bindings for [Nelua](https://nelua.io/), powered by [wgpu-native](https://github.com/gfx-rs/wgpu-native).

Bindings are generated directly from the official C headers using [nelua-decl](https://github.com/edubart/nelua-decl). When upstream releases a new version, run `make update` and you're done.

## Quick start

### Prerequisites

- [Nelua](https://nelua.io/) compiler
- GCC with plugin support (for binding generation)
- Python 3 (for macro extraction)
- Linux x86_64 (other platforms: adjust link flags)

On Ubuntu/Debian:

```bash
sudo apt install gcc gcc-13-plugin-dev python3
```

Replace `13` with your GCC major version (`gcc --version`).

### Setup

```bash
git clone https://github.com/root7211/nelua-wgpu.git
cd nelua-wgpu

# Build the GCC Lua plugin used by nelua-decl
make setup
```

### Download wgpu-native

Grab the pre-built library from [wgpu-native releases](https://github.com/gfx-rs/wgpu-native/releases):

```bash
mkdir -p deps/wgpu-native && cd deps/wgpu-native
curl -L -o wgpu.zip \
  https://github.com/gfx-rs/wgpu-native/releases/download/v25.0.2.1/wgpu-linux-x86_64-release.zip
unzip wgpu.zip && cd ../..
```

After this you should have `deps/wgpu-native/libwgpu_native.so` and `deps/wgpu-native/include/webgpu/webgpu.h`.

### Generate bindings and test

```bash
make generate   # runs nelua-decl -> wgpu-c/webgpu.nelua + webgpu_macros.nelua
make test-all   # 30 GPU tests covering the full pipeline
```

### Run the triangle example

Needs a display (X11) and GLFW:

```bash
sudo apt install libglfw3-dev

LD_LIBRARY_PATH=./deps/wgpu-native nelua examples/triangle.nelua \
  --add-path . --add-path examples \
  --cflags="-I./deps/wgpu-native/include" \
  --ldflags="-L./deps/wgpu-native -lwgpu_native -ldl -lpthread -lm"
```

## Using nelua-wgpu in your own project

### Raw bindings

```lua
require 'wgpu-c.webgpu'

local desc: WGPUInstanceDescriptor = {}
local instance = wgpuCreateInstance(&desc)
-- the full WebGPU C API is available as-is
```

### With utility helpers

```lua
require 'wgpu'  -- raw bindings + helpers

local label = wgpu_string("my-device")         -- Nelua string -> WGPUStringView
local clear = wgpu_color(0.1, 0.1, 0.1, 1.0)   -- -> WGPUColor
local size = wgpu_extent_2d(800, 600)            -- -> WGPUExtent3D
local orange = wgpu_color_hex(0xFF8800FF)        -- 0xRRGGBBAA -> WGPUColor
```

The helpers only touch `WGPUStringView`, `WGPUColor`, and `WGPUExtent3D` -- types that essentially never change between spec revisions.

### Compile flags

```bash
nelua your_app.nelua \
  --add-path /path/to/nelua-wgpu \
  --cflags="-I/path/to/wgpu-native/include" \
  --ldflags="-L/path/to/wgpu-native -lwgpu_native -ldl -lpthread -lm"
```

With `.so` you also need `LD_LIBRARY_PATH` at runtime. To avoid that, link the `.a` statically instead.

## Updating bindings

```bash
make update                       # latest from trunk
make update-tag TAG=v25.0.2.1    # pin to a specific release
```

This fetches fresh headers, regenerates everything, and runs validation. Review the diff before committing.

## How it works

```
webgpu.h + wgpu.h
       |
       v
  GCC + gcc-lua plugin
       |
       v
  nelua-decl (Lua) -----> wgpu-c/webgpu.nelua        (types, functions)
       |
  extract_macros.py ----> wgpu-c/webgpu_macros.nelua  (#define constants)
```

1. GCC compiles `wgpu-c/codegen/webgpu_all.c` with the [gcc-lua](https://github.com/nicknisi/gcc-lua) plugin
2. The plugin walks the GCC AST and calls `wgpu-c/codegen/webgpu.lua`
3. nelua-decl converts C declarations to Nelua syntax
4. A separate Python script handles `#define` macros (invisible to GCC plugins)

The result is a complete, correct `.nelua` binding file covering all opaque types, enums, structs, callbacks, and functions from both `webgpu.h` and the wgpu-native extension `wgpu.h`.

## Project structure

```
wgpu-c/
  webgpu.nelua            generated raw bindings (~1700 lines)
  webgpu_macros.nelua     generated macro constants
  codegen/
    webgpu.h, wgpu.h      upstream C headers
    webgpu_all.c           includes both headers for GCC
    webgpu.lua             nelua-decl filter rules
    Makefile               codegen build automation
wgpu/
  init.nelua              stable helpers (string, color, extent)
examples/
  triangle.nelua          GLFW window + colored triangle
  glfw.nelua              minimal GLFW bindings
tests/
  test_bindings.nelua     comprehensive GPU pipeline test (30 checks)
  test_highlevel.nelua    helper + compute verification
scripts/
  fetch_headers.sh        download headers from upstream
  extract_macros.py       C #define -> Nelua constants
  update.sh               full update pipeline
  analyze_api.py          API coverage analysis
```

## Design decisions

**Only raw bindings + minimal helpers.** No context managers, no pipeline builders, no render abstractions. Why:

- Raw bindings regenerate mechanically. High-level wrappers hardcode struct layouts and break when upstream changes callback signatures or renames fields.
- Different projects need different abstractions. A game engine and a UI framework want very different things on top of WebGPU.
- The helpers that *are* included (`wgpu_string`, `wgpu_color`, `wgpu_extent_2d`) depend on types so fundamental they'll never change.

## Make targets

| Target | What it does |
|---|---|
| `make setup` | Clone nelua-decl, build GCC Lua plugin |
| `make generate` | Generate bindings from C headers |
| `make macros` | Generate only macro constants (no GCC plugin needed) |
| `make test` | Run comprehensive binding test |
| `make test-hl` | Run helper function test |
| `make test-all` | Run all tests |
| `make update` | Fetch latest headers + regenerate |
| `make update-tag TAG=...` | Pin to specific version |
| `make analyze` | API analysis report |
| `make validate` | Binding coverage validation |
| `make clean` | Remove generated files |
| `make distclean` | Remove generated files + deps |

## License

MIT

## Credits

- [wgpu-native](https://github.com/gfx-rs/wgpu-native) -- the WebGPU implementation
- [nelua-decl](https://github.com/edubart/nelua-decl) -- the binding generator
- [Nelua](https://nelua.io/) -- the language

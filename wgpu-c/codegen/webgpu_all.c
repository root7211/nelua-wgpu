/**
 * webgpu_all.c - C source file for nelua-decl binding generation
 *
 * This file includes all WebGPU headers that we want to generate bindings for.
 * It is compiled by GCC with the Lua plugin to extract type/function information.
 *
 * Compile with: -I<path-to-wgpu-native>/include/webgpu
 * The include path must point to the directory containing webgpu.h and wgpu.h
 * from the same wgpu-native release to ensure header compatibility.
 */

#include <stdint.h>
#include <stddef.h>

/* Standard WebGPU API + wgpu-native extensions (from wgpu-native release) */
#include "webgpu.h"
#include "wgpu.h"

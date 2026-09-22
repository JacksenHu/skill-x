---
name: binary-reverse-engineering
description: Deep reverse engineering for PE, ELF, Mach-O, firmware, drivers, APK/DEX, .NET, Go, Rust, Unity IL2CPP, Unreal, packed binaries, custom VMs, and undocumented protocols. Use when the workspace contains a binary, disassembly, pseudocode, crash artifact, native library, game artifact, firmware image, or obfuscated application, or the task needs IDA/Ghidra/Frida/angr/Unicorn automation, algorithm recovery, unpacking, patching, or protocol reconstruction. 逆向、逆向工程、反编译、脱壳、hook 时使用。
license: MIT
compatibility: Scripts require Python 3 (standard library only). Analysis tooling (IDA/Ghidra/radare2/Frida) used when available.
metadata:
  author: skillhub
  version: "1.0.0"
---

# Binary Reverse Engineering

Work from artifact to verified recovered behavior.

## Start

1. Hash and triage the artifact with `scripts/triage_binary.py`.
2. Preserve original files; place derived files in a separate work directory.
3. Identify format, architecture, compiler/runtime clues, protections, imports, strings, and likely entry paths.
4. Build an address/function/structure map while analyzing.

## Select references

- Extended specialized skill map: read `references/extended-tool-routing.md`.
- Native PE/ELF/Mach-O, drivers, firmware: read `references/native-workflow.md`.
- .NET, Java/Android, Go/Rust, Unity/Unreal: read `references/managed-game.md`.
- Packers, anti-debug, virtualization, control-flow obfuscation: read `references/unpacking-obfuscation.md`.
- Network messages or binary formats: read `references/protocol-reverse.md`.

## Execute

- Combine static decompilation with debugger traces, watchpoints, hooks, dumps, and controlled input changes.
- Recover calling conventions, structs, vtables, state machines, packet layouts, and data transformations.
- Prefer scripts for repeatable extraction: IDAPython, Ghidra, r2pipe, Frida, angr/Z3, Unicorn, parsers, scanners, and patchers.
- Test recovered algorithms against original samples.

## Deliver

Return the artifact hash, target profile, key addresses/functions, recovered data structures, confirmed behavior, scripts, debugger commands, and verification results. Distinguish confirmed observations from hypotheses.

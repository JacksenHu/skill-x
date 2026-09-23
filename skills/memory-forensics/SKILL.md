---
name: memory-forensics
description: Cross-platform process memory, dump, runtime, heap, pointer-chain, signature, structure, and memory-forensics analysis for Windows, Linux, Android, Unity IL2CPP, Unreal, native applications, crash dumps, and raw memory images. Use when the task involves a PID, process name, memory dump, module offset, AOB pattern, pointer chain, runtime address, crash dump, Volatility artifact, or Frida target, or needs ReadProcessMemory/process_vm_readv code, map/module discovery, structure reconstruction, memory diffing, hooks, watchpoints, or rollback-safe patch tooling. 内存分析、内存取证、内存扫描、堆分析、指针链、AOB 扫描、转储分析时使用。
license: MIT
compatibility: Scripts require Python 3 (standard library only).
metadata:
  author: skillhub
  version: "1.0.0"
  name-zh: 内存取证分析
  description-zh: 跨平台进程内存与转储分析:模块映射、指针链、签名扫描、结构重建、内存 diff 与可回滚补丁工具。
  category: forensics
---

# Memory Forensics

Resolve runtime addresses and structures from evidence, then produce repeatable tooling.

## Start

1. Establish architecture, pointer width, endianness, target OS/runtime, and artifact type.
2. Distinguish absolute addresses, module-relative offsets, signatures, pointer chains, handles, and generated references.
3. Record module mappings, page protections, thread/heap context, and address provenance.
4. Use `scripts/aob_scan.py` for wildcard byte-pattern scans and `scripts/dump_strings.py` for offset-aware ASCII/UTF-16 extraction.

## Select references

- Windows live process, dumps, WinDbg, RPM/WPM: read `references/windows.md`.
- Linux, Android, Frida, IL2CPP: read `references/linux-android.md`.
- Raw dumps, structures, pointer chains, memory forensics: read `references/dump-structures.md`.

## Execute

- Prefer module resolution, signatures, and validated pointer paths over hard-coded absolute addresses.
- Use controlled state changes, memory diffs, watchpoints, allocation hooks, and access-width patterns to recover structures.
- Verify readable/writable regions and bounds before access.
- For patches, capture original bytes, validate expected bytes, restore protections, and provide rollback.

## Deliver

Return the address derivation, mapping evidence, recovered structure, complete reader/scanner/hook/patch code, error handling, logs, and verification steps.

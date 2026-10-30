#pragma once

// Microsoft integer and calling-convention spellings used by the pinned
// KisakBlack headers. Android AArch64 is LP64: int is 32-bit and long long
// is 64-bit. Keep __declspec(align(...)) compiler-parsed via -fdeclspec.
#if !defined(_WIN32)
#ifndef __int8
#define __int8 char
#endif
#ifndef __int16
#define __int16 short
#endif
#ifndef __int32
#define __int32 int
#endif
#ifndef __int64
#define __int64 long long
#endif
#ifndef __cdecl
#define __cdecl
#endif
#endif

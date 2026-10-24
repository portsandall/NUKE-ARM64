#pragma once
#include <cstdlib>

#define iassert(expression) do { if (!(expression)) std::abort(); } while (false)

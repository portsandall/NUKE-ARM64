#include <qcommon/snapfloat_rounding.h>

#include <cfenv>
#include <climits>
#include <cmath>
#include <limits>

namespace
{
bool expect(float value, int expected)
{
    return nuke_port::snapFloatToInt(value) == expected;
}

int fail(int code, int original_rounding)
{
    std::fesetround(original_rounding);
    return code;
}
} // namespace

int main()
{
    const int original_rounding = std::fegetround();
    if (original_rounding == -1)
        return 1;

    if (std::fesetround(FE_TONEAREST) != 0)
        return fail(2, original_rounding);

    if (!expect(0.5f, 0) || !expect(1.5f, 2) || !expect(2.5f, 2) ||
        !expect(3.5f, 4) || !expect(-0.5f, 0) || !expect(-1.5f, -2) ||
        !expect(-2.5f, -2) || !expect(-3.5f, -4))
        return fail(3, original_rounding);

    if (!expect(std::nextafter(2147483648.0f, 0.0f), 2147483520) ||
        !expect(2147483648.0f, INT_MIN) ||
        !expect(-2147483904.0f, INT_MIN) ||
        !expect(-2147483648.0f, INT_MIN) ||
        !expect(std::numeric_limits<float>::quiet_NaN(), INT_MIN) ||
        !expect(std::numeric_limits<float>::infinity(), INT_MIN) ||
        !expect(-std::numeric_limits<float>::infinity(), INT_MIN))
        return fail(4, original_rounding);

    if (std::fesetround(FE_DOWNWARD) != 0)
        return fail(5, original_rounding);
    if (!expect(1.75f, 1) || !expect(-1.25f, -2))
        return fail(6, original_rounding);

    if (std::fesetround(FE_UPWARD) != 0)
        return fail(7, original_rounding);
    if (!expect(1.25f, 2) || !expect(-1.75f, -1))
        return fail(8, original_rounding);

    if (std::fesetround(FE_TOWARDZERO) != 0)
        return fail(9, original_rounding);
    if (!expect(1.75f, 1) || !expect(-1.75f, -1))
        return fail(10, original_rounding);

    if (std::fesetround(original_rounding) != 0)
        return 11;
    return 0;
}

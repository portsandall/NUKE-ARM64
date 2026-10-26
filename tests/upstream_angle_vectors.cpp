#include "com_math_anglevectors.h"

#include <cmath>

// The translation unit also defines AnglesToQuat, which references this
// unrelated upstream helper. The regression below does not call that path.
void __cdecl AxisToQuat(const float (*)[3], float *quat)
{
    quat[0] = 0.0f;
    quat[1] = 0.0f;
    quat[2] = 0.0f;
    quat[3] = 1.0f;
}

static bool near(float actual, float expected)
{
    return std::fabs(actual - expected) <= 0.001f;
}

int main()
{
    const float zero_angles[3] = {0.0f, 0.0f, 0.0f};
    float forward[3] = {};
    float right[3] = {};
    float up[3] = {};

    AngleVectors(zero_angles, forward, right, up);
    if (!near(forward[0], 1.0f) || !near(forward[1], 0.0f) ||
        !near(forward[2], 0.0f) || !near(right[0], 0.0f) ||
        !near(right[1], -1.0f) || !near(right[2], 0.0f) ||
        !near(up[0], 0.0f) || !near(up[1], 0.0f) || !near(up[2], 1.0f))
        return 1;

    float axis[3][3] = {};
    AnglesToAxis(zero_angles, axis);
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            const float expected = row == col ? 1.0f : 0.0f;
            if (!near(axis[row][col], expected))
                return 2;
        }
    }

    // Exercises the second row that was previously accessed as (*axis)[3..5].
    float recovered[3] = {};
    AxisToSignedAngles(axis, recovered);
    if (!near(recovered[0], 0.0f) || !near(recovered[1], 0.0f) ||
        !near(recovered[2], 0.0f))
        return 3;

    const float yaw_90[3] = {0.0f, 90.0f, 0.0f};
    AnglesToAxis(yaw_90, axis);
    AxisToSignedAngles(axis, recovered);
    if (!near(recovered[0], 0.0f) || !near(recovered[1], 90.0f) ||
        !near(recovered[2], 0.0f))
        return 4;

    return 0;
}

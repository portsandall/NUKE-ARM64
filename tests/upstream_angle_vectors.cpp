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

    // Exercise a mixed pitch/yaw/roll basis, not only identity and pure yaw.
    const float mixed_angles[3] = {23.0f, 41.0f, -17.0f};
    float mixed_forward[3] = {};
    float mixed_right[3] = {};
    float mixed_up[3] = {};
    AngleVectors(mixed_angles, mixed_forward, mixed_right, mixed_up);
    AnglesToAxis(mixed_angles, axis);

    for (int i = 0; i < 3; ++i) {
        if (!near(mixed_forward[i], axis[0][i]))
            return 5;
        if (!near(mixed_right[i], -axis[1][i]))
            return 6;
        if (!near(mixed_up[i], axis[2][i]))
            return 7;
    }

    // Each row must be unit length and pairwise perpendicular.
    for (int row = 0; row < 3; ++row) {
        float length_squared = 0.0f;
        for (int col = 0; col < 3; ++col)
            length_squared += axis[row][col] * axis[row][col];
        if (!near(length_squared, 1.0f))
            return 8;

        for (int other = row + 1; other < 3; ++other) {
            float dot = 0.0f;
            for (int col = 0; col < 3; ++col)
                dot += axis[row][col] * axis[other][col];
            if (!near(dot, 0.0f))
                return 9;
        }
    }

    // QuatToAxis must preserve the identity orientation.
    const float identity_quat[4] = {0.0f, 0.0f, 0.0f, 1.0f};
    float quat_axis[3][3] = {};
    QuatToAxis(identity_quat, quat_axis);
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            const float expected = row == col ? 1.0f : 0.0f;
            if (!near(quat_axis[row][col], expected))
                return 10;
        }
    }

    // A +90-degree yaw quaternion must match the engine's angle basis.
    const float half_sqrt = 0.70710678118f;
    const float yaw_90_quat[4] = {0.0f, 0.0f, half_sqrt, half_sqrt};
    float yaw_axis[3][3] = {};
    QuatToAxis(yaw_90_quat, yaw_axis);
    AnglesToAxis(yaw_90, axis);
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            if (!near(yaw_axis[row][col], axis[row][col]))
                return 11;
        }
    }

    return 0;
}

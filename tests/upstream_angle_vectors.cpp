#include "com_math_anglevectors.h"

#include <cmath>

void ikAxisToQuat(const float (*mat)[3], float *out);

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

    // Exercise the real upstream AxisToQuat through AnglesToQuat.
    float identity_from_angles[4] = {};
    AnglesToQuat(zero_angles, identity_from_angles);
    if (!near(identity_from_angles[0], 0.0f) ||
        !near(identity_from_angles[1], 0.0f) ||
        !near(identity_from_angles[2], 0.0f) ||
        !near(identity_from_angles[3], 1.0f))
        return 12;

    float yaw_from_angles[4] = {};
    AnglesToQuat(yaw_90, yaw_from_angles);
    if (!near(yaw_from_angles[0], 0.0f) ||
        !near(yaw_from_angles[1], 0.0f) ||
        !near(yaw_from_angles[2], half_sqrt) ||
        !near(yaw_from_angles[3], half_sqrt))
        return 13;

    // A mixed rotation must survive angle -> quaternion -> axis conversion.
    float mixed_quat[4] = {};
    AnglesToQuat(mixed_angles, mixed_quat);
    float mixed_quat_axis[3][3] = {};
    QuatToAxis(mixed_quat, mixed_quat_axis);
    AnglesToAxis(mixed_angles, axis);
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            if (!near(mixed_quat_axis[row][col], axis[row][col]))
                return 14;
        }
    }

    // Test the duplicate IK converter through all nontrivial diagonal branches.
    const float half_turns[3][3] = {
        {180.0f, 0.0f, 0.0f},
        {0.0f, 180.0f, 0.0f},
        {0.0f, 0.0f, 180.0f},
    };
    for (int turn = 0; turn < 3; ++turn) {
        float turn_axis[3][3] = {};
        float engine_quat[4] = {};
        float ik_quat[4] = {};
        float rebuilt_axis[3][3] = {};
        AnglesToAxis(half_turns[turn], turn_axis);
        AnglesToQuat(half_turns[turn], engine_quat);
        ikAxisToQuat(turn_axis, ik_quat);

        for (int component = 0; component < 4; ++component) {
            if (!near(ik_quat[component], engine_quat[component]))
                return 15;
        }

        QuatToAxis(ik_quat, rebuilt_axis);
        for (int row = 0; row < 3; ++row) {
            for (int col = 0; col < 3; ++col) {
                if (!near(rebuilt_axis[row][col], turn_axis[row][col]))
                    return 16;
            }
        }
    }

    return 0;
}

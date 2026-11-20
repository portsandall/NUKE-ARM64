#include <cstdio>

struct phys_vec3 {
    float x;
    float y;
    float z;
};

struct phys_mat44 {
    phys_vec3 x;
    phys_vec3 y;
    phys_vec3 z;
    phys_vec3 w;
};

inline void Phys_Vec3ToNitrousVec(const float * const inVector, phys_vec3 *outVector)
{
    outVector->x = inVector[0];
    outVector->y = inVector[1];
    outVector->z = inVector[2];
}

inline void assert_mat44_initialized(const phys_mat44&)
{
}

/* PHYS_AXIS_TO_NITROUS_MAT */
/* PHYS_MAT4_TO_NITROUS_MAT */
/* PHYS_NITROUS_MAT44_TO_VEC33 */

namespace {

bool equal(const phys_vec3& value, float x, float y, float z)
{
    return value.x == x && value.y == y && value.z == z;
}

} // namespace

int main()
{
    float axis[3][3] = {
        {1.0f, 2.0f, 3.0f},
        {4.0f, 5.0f, 6.0f},
        {7.0f, 8.0f, 9.0f},
    };
    phys_mat44 matrix{};
    Phys_AxisToNitrousMat(axis, &matrix);
    if (!equal(matrix.x, 1.0f, 2.0f, 3.0f) ||
        !equal(matrix.y, 4.0f, 5.0f, 6.0f) ||
        !equal(matrix.z, 7.0f, 8.0f, 9.0f)) {
        std::fprintf(stderr, "3x3 axis row conversion failed\n");
        return 1;
    }

    float mat4[4][3] = {
        {11.0f, 12.0f, 13.0f},
        {14.0f, 15.0f, 16.0f},
        {17.0f, 18.0f, 19.0f},
        {20.0f, 21.0f, 22.0f},
    };
    Phys_Mat4ToNitrousMat(mat4, &matrix);
    if (!equal(matrix.x, 11.0f, 12.0f, 13.0f) ||
        !equal(matrix.y, 14.0f, 15.0f, 16.0f) ||
        !equal(matrix.z, 17.0f, 18.0f, 19.0f) ||
        !equal(matrix.w, 20.0f, 21.0f, 22.0f)) {
        std::fprintf(stderr, "4x3 matrix row conversion failed\n");
        return 2;
    }

    float restored[3][3]{};
    Phys_NitrousMat44ToVec33(&matrix, restored);
    if (restored[0][0] != 11.0f || restored[0][1] != 12.0f ||
        restored[0][2] != 13.0f || restored[1][0] != 14.0f ||
        restored[1][1] != 15.0f || restored[1][2] != 16.0f ||
        restored[2][0] != 17.0f || restored[2][1] != 18.0f ||
        restored[2][2] != 19.0f) {
        std::fprintf(stderr, "3x3 matrix extraction failed\n");
        return 3;
    }

    std::puts("physics matrix row adapters: 3x3, 4x3 and reverse conversion passed");
    return 0;
}

#include "base64.h"

#include <array>
#include <cstring>

int main() {
    // Include embedded NUL and high-bit bytes to prove the API is binary-safe.
    constexpr std::array<unsigned char, 4> input{{0x00, 0xff, 0x10, 0x00}};
    constexpr unsigned int input_size = static_cast<unsigned int>(input.size());
    constexpr unsigned int expected_encoded_size = 8;
    if (b64e_size(input_size) != expected_encoded_size) return 1;

    // b64_encode writes a trailing NUL; its return value excludes that NUL.
    std::array<unsigned char, expected_encoded_size + 1> encoded{};
    const unsigned int encoded_size = b64_encode(input.data(), input_size, encoded.data());
    if (encoded_size != expected_encoded_size ||
        std::strcmp(reinterpret_cast<const char*>(encoded.data()), "AP8QAA==") != 0) return 2;

    std::array<unsigned char, input.size()> decoded{};
    const unsigned int decoded_size = b64_decode(encoded.data(), encoded_size, decoded.data());
    if (decoded_size != input_size ||
        std::memcmp(decoded.data(), input.data(), input.size()) != 0) return 3;

    // Exercise the two-byte remainder path and its single '=' padding.
    constexpr std::array<unsigned char, 2> two_byte_input{{0xff, 0x10}};
    std::array<unsigned char, 5> two_byte_encoded{};
    const unsigned int two_byte_encoded_size =
        b64_encode(two_byte_input.data(), static_cast<unsigned int>(two_byte_input.size()),
                   two_byte_encoded.data());
    if (b64e_size(static_cast<unsigned int>(two_byte_input.size())) != 4 ||
        two_byte_encoded_size != 4 ||
        std::strcmp(reinterpret_cast<const char*>(two_byte_encoded.data()), "/xA=") != 0) return 5;
    std::array<unsigned char, 2> two_byte_decoded{};
    const unsigned int two_byte_decoded_size =
        b64_decode(two_byte_encoded.data(), two_byte_encoded_size, two_byte_decoded.data());
    if (two_byte_decoded_size != two_byte_input.size() ||
        std::memcmp(two_byte_decoded.data(), two_byte_input.data(), two_byte_input.size()) != 0) return 6;

    // Exercise the one-byte remainder path and its double '=' padding.
    constexpr std::array<unsigned char, 1> one_byte_input{{0xff}};
    std::array<unsigned char, 5> one_byte_encoded{};
    const unsigned int one_byte_encoded_size =
        b64_encode(one_byte_input.data(), static_cast<unsigned int>(one_byte_input.size()),
                   one_byte_encoded.data());
    if (b64e_size(static_cast<unsigned int>(one_byte_input.size())) != 4 ||
        one_byte_encoded_size != 4 ||
        std::strcmp(reinterpret_cast<const char*>(one_byte_encoded.data()), "/w==") != 0) return 7;
    std::array<unsigned char, 1> one_byte_decoded{};
    const unsigned int one_byte_decoded_size =
        b64_decode(one_byte_encoded.data(), one_byte_encoded_size, one_byte_decoded.data());
    if (one_byte_decoded_size != one_byte_input.size() ||
        std::memcmp(one_byte_decoded.data(), one_byte_input.data(), one_byte_input.size()) != 0) return 8;

    std::array<unsigned char, 1> empty{};
    if (b64e_size(0) != 0 || b64_encode(nullptr, 0, empty.data()) != 0 || empty[0] != 0) return 4;
    return 0;
}

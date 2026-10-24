#include <qcommon/bitarray.h>

int main() {
    const bitarray<64> bits(1u, 31u, 32u, 63u, ~0u);
    if (!bits.testBit(1) || !bits.testBit(31) ||
        !bits.testBit(32) || !bits.testBit(63)) {
        return 1;
    }
    if (bits.testBit(0) || bits.testBit(2) ||
        bits.testBit(30) || bits.testBit(33)) {
        return 2;
    }
    return 0;
}

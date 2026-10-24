#include <jni.h>
#include <string>
#include <base64.h>
extern "C" JNIEXPORT jstring JNICALL
Java_org_bitflipunix_nuke_MainActivity_nativeStatus(JNIEnv* env, jclass) {
    const unsigned char message[] = "mp_nuked";
    unsigned char encoded[4 * ((sizeof(message) - 1 + 2) / 3) + 1] = {};
    const unsigned int length = b64_encode(message, sizeof(message) - 1, encoded);
    std::string text = "Android AArch64 native JNI loaded.\nKisakBlack Base64 source linked.\nMap identifier encoded: ";
    text.append(reinterpret_cast<const char*>(encoded), length);
    return env->NewStringUTF(text.c_str());
}

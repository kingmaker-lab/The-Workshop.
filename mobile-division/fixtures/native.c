#include <jni.h>
JNIEXPORT jint JNICALL
Java_lab_workshop_pulsefixture_MainActivity_nativeAnswer(JNIEnv *env, jclass type) {
    (void)env;
    (void)type;
    return 42;
}

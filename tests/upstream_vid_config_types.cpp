#include <qcommon/vid_config_types.h>

int main()
{
    vidConfig_t config{};
    config.sceneWidth = 640;
    config.sceneHeight = 480;
    config.displayWidth = 640;
    config.displayHeight = 480;
    config.aspectRatioWindow = 4.0F / 3.0F;
    config.deviceSupportsGamma = true;
    return config.sceneWidth == 640 && config.displayHeight == 480 &&
                   config.deviceSupportsGamma
               ? 0
               : 1;
}

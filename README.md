# generate-arduino-makefile

This tool reads build instructions from your arduino IDE's installed packages and generates a Makefile, so you don't need to use the IDE.

**Notice:** This tool is work in progress, so it might not work with your board, on your machine, or with your code. Please [report any bugs](https://github.com/opatut/generate-arduino-makefile) you encounter, so I can continue to improve it.

## Disclaimer

You use this tool at your own risk. Nobody except you can be held liable for any damage done to anything or anybody by this tool.

This includes of course your precious hardware, so if you brick your device using this tool, that will be entirely your problem. Buy a new one and use something else.

## Usage

See `generate-arduino-makefile.py --help` for command line instructions.

Example usage:

```
path/to/generate-arduino-makefile.py \
    --vendor adafruit \
    --board adafruit_feather_m0 \
    --architecture SAMD \
    --output Makefile \
    --source-dir src \
    --build-dir build \
    --lib Wire \
    --lib I2Cdev
make
make upload
```

## Acknowledgements

This work is heavily inspired by [Arduino-Makefile](https://github.com/sudar/Arduino-Makefile), and contains part of its source.

The arduino reset CLI tool [ard-reset-arduino](https://github.com/sudar/Arduino-Makefile/blob/master/bin/ard-reset-arduino) was written by Simon John and was published as part of Arduino-Makefile under LGPL v2.1.

## What to do when things break

This tool might generate bad code for your device, and it might freeze. Maybe your PC won't detect it anymore. In this case, see if your vendor has instructions available for a bad code upload, and try resetting (reprogramming) the bootloader.

## License

This tool and the related documentation and examples are free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or (at your option) any later version. See LICENSE.txt for the full license text.

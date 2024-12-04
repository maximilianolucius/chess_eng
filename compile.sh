#!/bin/bash

g++ -Os -flto -std=c++20 -ffunction-sections -fdata-sections *.cpp -o AltairChess -Wl,-s -Wl,--gc-sections -Wl,-s -pthread -fexceptions -fno-rtti -fmerge-all-constants -fvisibility=hidden -fomit-frame-pointer
size AltairChess
upx --best --lzma AltairChess
size AltairChess


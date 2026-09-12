/**
 * @file gd3rd_data.c
 * Load request table
 */

#include "sf33rd/Source/Game/io/gd3rd_data.h"

const LoadRequestEntry ldreq_tbl[] = {
    [0] = { .type = LDREQ_TEXTURE, .ix = 1, .frre = 2, .kokey = 3 },
    [1] = { .type = LDREQ_TEXTURE, .ix = 27, .frre = 2, .kokey = 3 },
    [2] = { .type = LDREQ_TEXTURE, .ix = 35, .frre = 2, .kokey = 3 },
    [3] = { .type = LDREQ_COLOR, .ix = 0, .frre = 1, .kokey = 10 },
    [4] = { .type = LDREQ_SOUND, .ix = 130, .frre = 1, .kokey = 22 },
    [5] = { .type = LDREQ_TEXTURE, .ix = 2, .frre = 2, .kokey = 3 },
    [6] = { .type = LDREQ_COLOR, .ix = 1, .frre = 1, .kokey = 10 },
    [7] = { .type = LDREQ_SOUND, .ix = 131, .frre = 1, .kokey = 22 },
    [8] = { .type = LDREQ_SOUND, .ix = 153, .frre = 1, .kokey = 21 },
    [9] = { .type = LDREQ_TEXTURE, .ix = 38, .frre = 1, .kokey = 12 },
    [10] = { .type = LDREQ_TEXTURE, .ix = 3, .frre = 2, .kokey = 3 },
    [11] = { .type = LDREQ_TEXTURE, .ix = 89, .frre = 2, .kokey = 3 },
    [12] = { .type = LDREQ_COLOR, .ix = 2, .frre = 1, .kokey = 10 },
    [13] = { .type = LDREQ_SOUND, .ix = 132, .frre = 1, .kokey = 22 },
    [14] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [15] = { .type = LDREQ_TEXTURE, .ix = 4, .frre = 2, .kokey = 3 },
    [16] = { .type = LDREQ_COLOR, .ix = 3, .frre = 1, .kokey = 10 },
    [17] = { .type = LDREQ_COLOR, .ix = 85, .frre = 1, .kokey = 10 },
    [18] = { .type = LDREQ_SOUND, .ix = 133, .frre = 1, .kokey = 22 },
    [19] = { .type = LDREQ_TEXTURE, .ix = 5, .frre = 2, .kokey = 3 },
    [20] = { .type = LDREQ_COLOR, .ix = 4, .frre = 1, .kokey = 10 },
    [21] = { .type = LDREQ_SOUND, .ix = 134, .frre = 1, .kokey = 22 },
    [22] = { .type = LDREQ_COLOR, .ix = 84, .frre = 1, .kokey = 2 },
    [23] = { .type = LDREQ_TEXTURE, .ix = 61, .frre = 1, .kokey = 2 },
    [24] = { .type = LDREQ_SCREEN, .ix = 154, .frre = 1, .kokey = 29 },
    [25] = { .type = LDREQ_TEXTURE, .ix = 6, .frre = 2, .kokey = 3 },
    [26] = { .type = LDREQ_TEXTURE, .ix = 27, .frre = 2, .kokey = 3 },
    [27] = { .type = LDREQ_COLOR, .ix = 5, .frre = 1, .kokey = 10 },
    [28] = { .type = LDREQ_COLOR, .ix = 86, .frre = 1, .kokey = 10 },
    [29] = { .type = LDREQ_SOUND, .ix = 135, .frre = 1, .kokey = 22 },
    [30] = { .type = LDREQ_TEXTURE, .ix = 7, .frre = 2, .kokey = 3 },
    [31] = { .type = LDREQ_COLOR, .ix = 6, .frre = 1, .kokey = 10 },
    [32] = { .type = LDREQ_COLOR, .ix = 155, .frre = 1, .kokey = 10 },
    [33] = { .type = LDREQ_SOUND, .ix = 136, .frre = 1, .kokey = 22 },
    [34] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [35] = { .type = LDREQ_TEXTURE, .ix = 8, .frre = 2, .kokey = 3 },
    [36] = { .type = LDREQ_TEXTURE, .ix = 90, .frre = 2, .kokey = 3 },
    [37] = { .type = LDREQ_COLOR, .ix = 7, .frre = 1, .kokey = 10 },
    [38] = { .type = LDREQ_COLOR, .ix = 87, .frre = 1, .kokey = 10 },
    [39] = { .type = LDREQ_SOUND, .ix = 137, .frre = 1, .kokey = 22 },
    [40] = { .type = LDREQ_TEXTURE, .ix = 9, .frre = 2, .kokey = 3 },
    [41] = { .type = LDREQ_COLOR, .ix = 8, .frre = 1, .kokey = 10 },
    [42] = { .type = LDREQ_SOUND, .ix = 138, .frre = 1, .kokey = 22 },
    [43] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [44] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [45] = { .type = LDREQ_TEXTURE, .ix = 10, .frre = 2, .kokey = 3 },
    [46] = { .type = LDREQ_TEXTURE, .ix = 91, .frre = 2, .kokey = 3 },
    [47] = { .type = LDREQ_COLOR, .ix = 9, .frre = 1, .kokey = 10 },
    [48] = { .type = LDREQ_SOUND, .ix = 139, .frre = 1, .kokey = 22 },
    [49] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [50] = { .type = LDREQ_TEXTURE, .ix = 11, .frre = 2, .kokey = 3 },
    [51] = { .type = LDREQ_COLOR, .ix = 10, .frre = 1, .kokey = 10 },
    [52] = { .type = LDREQ_SOUND, .ix = 140, .frre = 1, .kokey = 22 },
    [53] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [54] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [55] = { .type = LDREQ_TEXTURE, .ix = 12, .frre = 2, .kokey = 3 },
    [56] = { .type = LDREQ_TEXTURE, .ix = 92, .frre = 2, .kokey = 3 },
    [57] = { .type = LDREQ_COLOR, .ix = 11, .frre = 1, .kokey = 10 },
    [58] = { .type = LDREQ_SOUND, .ix = 141, .frre = 1, .kokey = 22 },
    [59] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [60] = { .type = LDREQ_TEXTURE, .ix = 13, .frre = 2, .kokey = 3 },
    [61] = { .type = LDREQ_TEXTURE, .ix = 93, .frre = 2, .kokey = 3 },
    [62] = { .type = LDREQ_COLOR, .ix = 12, .frre = 1, .kokey = 10 },
    [63] = { .type = LDREQ_SOUND, .ix = 142, .frre = 1, .kokey = 22 },
    [64] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [65] = { .type = LDREQ_TEXTURE, .ix = 14, .frre = 2, .kokey = 3 },
    [66] = { .type = LDREQ_TEXTURE, .ix = 94, .frre = 2, .kokey = 3 },
    [67] = { .type = LDREQ_COLOR, .ix = 13, .frre = 1, .kokey = 10 },
    [68] = { .type = LDREQ_SOUND, .ix = 143, .frre = 1, .kokey = 22 },
    [69] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [70] = { .type = LDREQ_TEXTURE, .ix = 15, .frre = 2, .kokey = 3 },
    [71] = { .type = LDREQ_TEXTURE, .ix = 95, .frre = 2, .kokey = 3 },
    [72] = { .type = LDREQ_COLOR, .ix = 14, .frre = 1, .kokey = 10 },
    [73] = { .type = LDREQ_SOUND, .ix = 144, .frre = 1, .kokey = 22 },
    [74] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [75] = { .type = LDREQ_TEXTURE, .ix = 16, .frre = 2, .kokey = 3 },
    [76] = { .type = LDREQ_TEXTURE, .ix = 96, .frre = 2, .kokey = 3 },
    [77] = { .type = LDREQ_COLOR, .ix = 15, .frre = 1, .kokey = 10 },
    [78] = { .type = LDREQ_SOUND, .ix = 145, .frre = 1, .kokey = 22 },
    [79] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [80] = { .type = LDREQ_TEXTURE, .ix = 17, .frre = 2, .kokey = 3 },
    [81] = { .type = LDREQ_COLOR, .ix = 16, .frre = 1, .kokey = 10 },
    [82] = { .type = LDREQ_SOUND, .ix = 146, .frre = 1, .kokey = 22 },
    [83] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [84] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [85] = { .type = LDREQ_TEXTURE, .ix = 18, .frre = 2, .kokey = 3 },
    [86] = { .type = LDREQ_COLOR, .ix = 17, .frre = 1, .kokey = 10 },
    [87] = { .type = LDREQ_SOUND, .ix = 147, .frre = 1, .kokey = 22 },
    [88] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [89] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [90] = { .type = LDREQ_TEXTURE, .ix = 19, .frre = 2, .kokey = 3 },
    [91] = { .type = LDREQ_COLOR, .ix = 18, .frre = 1, .kokey = 10 },
    [92] = { .type = LDREQ_SOUND, .ix = 148, .frre = 1, .kokey = 22 },
    [93] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [94] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [95] = { .type = LDREQ_TEXTURE, .ix = 20, .frre = 2, .kokey = 3 },
    [96] = { .type = LDREQ_TEXTURE, .ix = 97, .frre = 2, .kokey = 3 },
    [97] = { .type = LDREQ_COLOR, .ix = 19, .frre = 1, .kokey = 10 },
    [98] = { .type = LDREQ_SOUND, .ix = 149, .frre = 1, .kokey = 22 },
    [99] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [100] = { .type = LDREQ_COLOR, .ix = 21, .frre = 1, .kokey = 2 },
    [101] = { .type = LDREQ_TEXTURE, .ix = 83, .frre = 1, .kokey = 19 },
    [102] = { .type = LDREQ_TEXTURE, .ix = 84, .frre = 1, .kokey = 19 },
    [103] = { .type = LDREQ_TEXTURE, .ix = 52, .frre = 1, .kokey = 19 },
    [104] = { .type = LDREQ_SCREEN, .ix = 41, .frre = 1, .kokey = 18 },
    [105] = { .type = LDREQ_COLOR, .ix = 22, .frre = 1, .kokey = 2 },
    [106] = { .type = LDREQ_TEXTURE, .ix = 44, .frre = 1, .kokey = 19 },
    [107] = { .type = LDREQ_SCREEN, .ix = 42, .frre = 1, .kokey = 18 },
    [108] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [109] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [110] = { .type = LDREQ_COLOR, .ix = 23, .frre = 1, .kokey = 2 },
    [111] = { .type = LDREQ_TEXTURE, .ix = 58, .frre = 1, .kokey = 19 },
    [112] = { .type = LDREQ_SCREEN, .ix = 43, .frre = 1, .kokey = 18 },
    [113] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [114] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [115] = { .type = LDREQ_COLOR, .ix = 24, .frre = 1, .kokey = 2 },
    [116] = { .type = LDREQ_TEXTURE, .ix = 45, .frre = 1, .kokey = 19 },
    [117] = { .type = LDREQ_SCREEN, .ix = 44, .frre = 1, .kokey = 18 },
    [118] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [119] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [120] = { .type = LDREQ_COLOR, .ix = 25, .frre = 1, .kokey = 2 },
    [121] = { .type = LDREQ_TEXTURE, .ix = 50, .frre = 1, .kokey = 19 },
    [122] = { .type = LDREQ_SCREEN, .ix = 45, .frre = 1, .kokey = 18 },
    [123] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [124] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [125] = { .type = LDREQ_COLOR, .ix = 26, .frre = 1, .kokey = 2 },
    [126] = { .type = LDREQ_TEXTURE, .ix = 42, .frre = 1, .kokey = 19 },
    [127] = { .type = LDREQ_SCREEN, .ix = 46, .frre = 1, .kokey = 18 },
    [128] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [129] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [130] = { .type = LDREQ_COLOR, .ix = 27, .frre = 1, .kokey = 2 },
    [131] = { .type = LDREQ_TEXTURE, .ix = 47, .frre = 1, .kokey = 19 },
    [132] = { .type = LDREQ_SCREEN, .ix = 47, .frre = 1, .kokey = 18 },
    [133] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [134] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [135] = { .type = LDREQ_COLOR, .ix = 28, .frre = 1, .kokey = 2 },
    [136] = { .type = LDREQ_TEXTURE, .ix = 53, .frre = 1, .kokey = 19 },
    [137] = { .type = LDREQ_SCREEN, .ix = 48, .frre = 1, .kokey = 18 },
    [138] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [139] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [140] = { .type = LDREQ_COLOR, .ix = 29, .frre = 1, .kokey = 2 },
    [141] = { .type = LDREQ_TEXTURE, .ix = 43, .frre = 1, .kokey = 19 },
    [142] = { .type = LDREQ_SCREEN, .ix = 49, .frre = 1, .kokey = 18 },
    [143] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [144] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [145] = { .type = LDREQ_COLOR, .ix = 30, .frre = 1, .kokey = 2 },
    [146] = { .type = LDREQ_TEXTURE, .ix = 48, .frre = 1, .kokey = 19 },
    [147] = { .type = LDREQ_SCREEN, .ix = 50, .frre = 1, .kokey = 18 },
    [148] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [149] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [150] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [151] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [152] = { .type = LDREQ_SCREEN, .ix = 51, .frre = 1, .kokey = 18 },
    [153] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [154] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [155] = { .type = LDREQ_COLOR, .ix = 32, .frre = 1, .kokey = 2 },
    [156] = { .type = LDREQ_TEXTURE, .ix = 86, .frre = 1, .kokey = 19 },
    [157] = { .type = LDREQ_SCREEN, .ix = 52, .frre = 1, .kokey = 18 },
    [158] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [159] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [160] = { .type = LDREQ_COLOR, .ix = 88, .frre = 1, .kokey = 2 },
    [161] = { .type = LDREQ_TEXTURE, .ix = 87, .frre = 1, .kokey = 19 },
    [162] = { .type = LDREQ_SCREEN, .ix = 53, .frre = 1, .kokey = 18 },
    [163] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [164] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [165] = { .type = LDREQ_COLOR, .ix = 33, .frre = 1, .kokey = 2 },
    [166] = { .type = LDREQ_TEXTURE, .ix = 49, .frre = 1, .kokey = 19 },
    [167] = { .type = LDREQ_SCREEN, .ix = 54, .frre = 1, .kokey = 18 },
    [168] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [169] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [170] = { .type = LDREQ_COLOR, .ix = 34, .frre = 1, .kokey = 2 },
    [171] = { .type = LDREQ_TEXTURE, .ix = 46, .frre = 1, .kokey = 19 },
    [172] = { .type = LDREQ_SCREEN, .ix = 55, .frre = 1, .kokey = 18 },
    [173] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [174] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [175] = { .type = LDREQ_COLOR, .ix = 35, .frre = 1, .kokey = 2 },
    [176] = { .type = LDREQ_TEXTURE, .ix = 56, .frre = 1, .kokey = 19 },
    [177] = { .type = LDREQ_SCREEN, .ix = 56, .frre = 1, .kokey = 18 },
    [178] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [179] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [180] = { .type = LDREQ_COLOR, .ix = 36, .frre = 1, .kokey = 2 },
    [181] = { .type = LDREQ_TEXTURE, .ix = 51, .frre = 1, .kokey = 19 },
    [182] = { .type = LDREQ_SCREEN, .ix = 57, .frre = 1, .kokey = 18 },
    [183] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [184] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [185] = { .type = LDREQ_COLOR, .ix = 32, .frre = 1, .kokey = 2 },
    [186] = { .type = LDREQ_TEXTURE, .ix = 86, .frre = 1, .kokey = 19 },
    [187] = { .type = LDREQ_SCREEN, .ix = 52, .frre = 1, .kokey = 18 },
    [188] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [189] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [190] = { .type = LDREQ_COLOR, .ix = 37, .frre = 1, .kokey = 2 },
    [191] = { .type = LDREQ_TEXTURE, .ix = 88, .frre = 1, .kokey = 19 },
    [192] = { .type = LDREQ_SCREEN, .ix = 59, .frre = 1, .kokey = 18 },
    [193] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [194] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [195] = { .type = LDREQ_COLOR, .ix = 38, .frre = 1, .kokey = 2 },
    [196] = { .type = LDREQ_TEXTURE, .ix = 55, .frre = 1, .kokey = 19 },
    [197] = { .type = LDREQ_SCREEN, .ix = 60, .frre = 1, .kokey = 18 },
    [198] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [199] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [200] = { .type = LDREQ_COLOR, .ix = 39, .frre = 1, .kokey = 2 },
    [201] = { .type = LDREQ_TEXTURE, .ix = 54, .frre = 1, .kokey = 19 },
    [202] = { .type = LDREQ_TEXTURE, .ix = 34, .frre = 2, .kokey = 19 },
    [203] = { .type = LDREQ_SCREEN, .ix = 61, .frre = 1, .kokey = 18 },
    [204] = { .type = LDREQ_TEXTURE, .ix = 33, .frre = 2, .kokey = 19 },
    [205] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [206] = { .type = LDREQ_COLOR, .ix = 40, .frre = 1, .kokey = 2 },
    [207] = { .type = LDREQ_TEXTURE, .ix = 59, .frre = 1, .kokey = 19 },
    [208] = { .type = LDREQ_TEXTURE, .ix = 34, .frre = 2, .kokey = 19 },
    [209] = { .type = LDREQ_SCREEN, .ix = 62, .frre = 1, .kokey = 18 },
    [210] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [211] = { .type = LDREQ_INVALID, .ix = 0, .frre = 0, .kokey = 0 },
    [212] = { .type = LDREQ_COLOR, .ix = 64, .frre = 1, .kokey = 2 },
    [213] = { .type = LDREQ_COLOR, .ix = 65, .frre = 1, .kokey = 2 },
    [214] = { .type = LDREQ_COLOR, .ix = 66, .frre = 1, .kokey = 2 },
    [215] = { .type = LDREQ_COLOR, .ix = 67, .frre = 1, .kokey = 2 },
    [216] = { .type = LDREQ_COLOR, .ix = 68, .frre = 1, .kokey = 2 },
    [217] = { .type = LDREQ_COLOR, .ix = 69, .frre = 1, .kokey = 2 },
    [218] = { .type = LDREQ_COLOR, .ix = 70, .frre = 1, .kokey = 2 },
    [219] = { .type = LDREQ_COLOR, .ix = 71, .frre = 1, .kokey = 2 },
    [220] = { .type = LDREQ_COLOR, .ix = 72, .frre = 1, .kokey = 2 },
    [221] = { .type = LDREQ_COLOR, .ix = 73, .frre = 1, .kokey = 2 },
    [222] = { .type = LDREQ_COLOR, .ix = 74, .frre = 1, .kokey = 2 },
    [223] = { .type = LDREQ_COLOR, .ix = 75, .frre = 1, .kokey = 2 },
    [224] = { .type = LDREQ_COLOR, .ix = 76, .frre = 1, .kokey = 2 },
    [225] = { .type = LDREQ_COLOR, .ix = 77, .frre = 1, .kokey = 2 },
    [226] = { .type = LDREQ_COLOR, .ix = 78, .frre = 1, .kokey = 2 },
    [227] = { .type = LDREQ_COLOR, .ix = 79, .frre = 1, .kokey = 2 },
    [228] = { .type = LDREQ_COLOR, .ix = 80, .frre = 1, .kokey = 2 },
    [229] = { .type = LDREQ_COLOR, .ix = 81, .frre = 1, .kokey = 2 },
    [230] = { .type = LDREQ_COLOR, .ix = 82, .frre = 1, .kokey = 2 },
    [231] = { .type = LDREQ_COLOR, .ix = 83, .frre = 1, .kokey = 2 },
    [232] = { .type = LDREQ_SOUND, .ix = 110, .frre = 1, .kokey = 22 },
    [233] = { .type = LDREQ_SOUND, .ix = 111, .frre = 1, .kokey = 22 },
    [234] = { .type = LDREQ_SOUND, .ix = 112, .frre = 1, .kokey = 22 },
    [235] = { .type = LDREQ_SOUND, .ix = 113, .frre = 1, .kokey = 22 },
    [236] = { .type = LDREQ_SOUND, .ix = 114, .frre = 1, .kokey = 22 },
    [237] = { .type = LDREQ_SOUND, .ix = 115, .frre = 1, .kokey = 22 },
    [238] = { .type = LDREQ_SOUND, .ix = 116, .frre = 1, .kokey = 22 },
    [239] = { .type = LDREQ_SOUND, .ix = 117, .frre = 1, .kokey = 22 },
    [240] = { .type = LDREQ_SOUND, .ix = 118, .frre = 1, .kokey = 22 },
    [241] = { .type = LDREQ_SOUND, .ix = 119, .frre = 1, .kokey = 22 },
    [242] = { .type = LDREQ_SOUND, .ix = 120, .frre = 1, .kokey = 22 },
    [243] = { .type = LDREQ_SOUND, .ix = 121, .frre = 1, .kokey = 22 },
    [244] = { .type = LDREQ_SOUND, .ix = 122, .frre = 1, .kokey = 22 },
    [245] = { .type = LDREQ_SOUND, .ix = 123, .frre = 1, .kokey = 22 },
    [246] = { .type = LDREQ_SOUND, .ix = 124, .frre = 1, .kokey = 22 },
    [247] = { .type = LDREQ_SOUND, .ix = 125, .frre = 1, .kokey = 22 },
    [248] = { .type = LDREQ_SOUND, .ix = 126, .frre = 1, .kokey = 22 },
    [249] = { .type = LDREQ_SOUND, .ix = 127, .frre = 1, .kokey = 22 },
    [250] = { .type = LDREQ_SOUND, .ix = 128, .frre = 1, .kokey = 22 },
    [251] = { .type = LDREQ_SOUND, .ix = 129, .frre = 1, .kokey = 22 },
    [252] = { .type = LDREQ_SOUND, .ix = 130, .frre = 1, .kokey = 22 },
    [253] = { .type = LDREQ_SOUND, .ix = 131, .frre = 1, .kokey = 22 },
    [254] = { .type = LDREQ_SOUND, .ix = 132, .frre = 1, .kokey = 22 },
    [255] = { .type = LDREQ_SOUND, .ix = 133, .frre = 1, .kokey = 22 },
    [256] = { .type = LDREQ_SOUND, .ix = 134, .frre = 1, .kokey = 22 },
    [257] = { .type = LDREQ_SOUND, .ix = 135, .frre = 1, .kokey = 22 },
    [258] = { .type = LDREQ_SOUND, .ix = 136, .frre = 1, .kokey = 22 },
    [259] = { .type = LDREQ_SOUND, .ix = 137, .frre = 1, .kokey = 22 },
    [260] = { .type = LDREQ_SOUND, .ix = 138, .frre = 1, .kokey = 22 },
    [261] = { .type = LDREQ_SOUND, .ix = 139, .frre = 1, .kokey = 22 },
    [262] = { .type = LDREQ_SOUND, .ix = 130, .frre = 1, .kokey = 22 },
    [263] = { .type = LDREQ_SOUND, .ix = 131, .frre = 1, .kokey = 22 },
    [264] = { .type = LDREQ_SOUND, .ix = 132, .frre = 1, .kokey = 22 },
    [265] = { .type = LDREQ_SOUND, .ix = 133, .frre = 1, .kokey = 22 },
    [266] = { .type = LDREQ_SOUND, .ix = 134, .frre = 1, .kokey = 22 },
    [267] = { .type = LDREQ_SOUND, .ix = 135, .frre = 1, .kokey = 22 },
    [268] = { .type = LDREQ_SOUND, .ix = 136, .frre = 1, .kokey = 22 },
    [269] = { .type = LDREQ_SOUND, .ix = 137, .frre = 1, .kokey = 22 },
    [270] = { .type = LDREQ_SOUND, .ix = 138, .frre = 1, .kokey = 22 },
    [271] = { .type = LDREQ_SOUND, .ix = 139, .frre = 1, .kokey = 22 },
    [272] = { .type = LDREQ_COLOR, .ix = 0, .frre = 1, .kokey = 10 },
    [273] = { .type = LDREQ_COLOR, .ix = 1, .frre = 1, .kokey = 10 },
    [274] = { .type = LDREQ_COLOR, .ix = 2, .frre = 1, .kokey = 10 },
    [275] = { .type = LDREQ_COLOR, .ix = 3, .frre = 1, .kokey = 10 },
    [276] = { .type = LDREQ_COLOR, .ix = 4, .frre = 1, .kokey = 10 },
    [277] = { .type = LDREQ_COLOR, .ix = 5, .frre = 1, .kokey = 10 },
    [278] = { .type = LDREQ_COLOR, .ix = 6, .frre = 1, .kokey = 10 },
    [279] = { .type = LDREQ_COLOR, .ix = 7, .frre = 1, .kokey = 10 },
    [280] = { .type = LDREQ_COLOR, .ix = 8, .frre = 1, .kokey = 10 },
    [281] = { .type = LDREQ_COLOR, .ix = 9, .frre = 1, .kokey = 10 },
    [282] = { .type = LDREQ_COLOR, .ix = 10, .frre = 1, .kokey = 10 },
    [283] = { .type = LDREQ_COLOR, .ix = 11, .frre = 1, .kokey = 10 },
    [284] = { .type = LDREQ_COLOR, .ix = 12, .frre = 1, .kokey = 10 },
    [285] = { .type = LDREQ_COLOR, .ix = 13, .frre = 1, .kokey = 10 },
    [286] = { .type = LDREQ_COLOR, .ix = 14, .frre = 1, .kokey = 10 },
    [287] = { .type = LDREQ_COLOR, .ix = 15, .frre = 1, .kokey = 10 },
    [288] = { .type = LDREQ_COLOR, .ix = 16, .frre = 1, .kokey = 10 },
    [289] = { .type = LDREQ_COLOR, .ix = 17, .frre = 1, .kokey = 10 },
    [290] = { .type = LDREQ_COLOR, .ix = 18, .frre = 1, .kokey = 10 },
    [291] = { .type = LDREQ_COLOR, .ix = 19, .frre = 1, .kokey = 10 },
    [292] = { .type = LDREQ_KANJI, .ix = 151, .frre = 2, .kokey = 25 },
    [293] = { .type = LDREQ_KANJI, .ix = 152, .frre = 2, .kokey = 26 },
    /* LES QUINZE ETAGES AJOUTES ONT LEUR PROPRE BLOC.
     *
     * Les deux premieres entrees restent celles de l'etage 10 (Yang) -- ce sont les
     * couleurs et le groupe de graphiques, qui n'ont jamais pose probleme. La
     * TROISIEME, `LDREQ_SCREEN` avec `kokey = 18`, est la notre : elle pointe sur une
     * entree de `color_file[]` dont `.apfn` designe un fichier de `resources/stages/`.
     * C'est elle qui portait toute la contrainte du donneur. */
    [294] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [295] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [296] = { .type = LDREQ_SCREEN, .ix = 161, .frre = 1, .kokey = 18 }, /* etage 22 */
    [297] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [298] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [299] = { .type = LDREQ_SCREEN, .ix = 162, .frre = 1, .kokey = 18 }, /* etage 23 */
    [300] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [301] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [302] = { .type = LDREQ_SCREEN, .ix = 163, .frre = 1, .kokey = 18 }, /* etage 24 */
    [303] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [304] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [305] = { .type = LDREQ_SCREEN, .ix = 164, .frre = 1, .kokey = 18 }, /* etage 25 */
    [306] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [307] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [308] = { .type = LDREQ_SCREEN, .ix = 165, .frre = 1, .kokey = 18 }, /* etage 26 */
    [309] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [310] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [311] = { .type = LDREQ_SCREEN, .ix = 166, .frre = 1, .kokey = 18 }, /* etage 27 */
    [312] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [313] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [314] = { .type = LDREQ_SCREEN, .ix = 167, .frre = 1, .kokey = 18 }, /* etage 28 */
    [315] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [316] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [317] = { .type = LDREQ_SCREEN, .ix = 168, .frre = 1, .kokey = 18 }, /* etage 29 */
    [318] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [319] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [320] = { .type = LDREQ_SCREEN, .ix = 169, .frre = 1, .kokey = 18 }, /* etage 30 */
    [321] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [322] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [323] = { .type = LDREQ_SCREEN, .ix = 170, .frre = 1, .kokey = 18 }, /* etage 31 */
    [324] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [325] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [326] = { .type = LDREQ_SCREEN, .ix = 171, .frre = 1, .kokey = 18 }, /* etage 32 */
    [327] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [328] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [329] = { .type = LDREQ_SCREEN, .ix = 172, .frre = 1, .kokey = 18 }, /* etage 33 */
    [330] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [331] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [332] = { .type = LDREQ_SCREEN, .ix = 173, .frre = 1, .kokey = 18 }, /* etage 34 */
    [333] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [334] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [335] = { .type = LDREQ_SCREEN, .ix = 174, .frre = 1, .kokey = 18 }, /* etage 35 */
    [336] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [337] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [338] = { .type = LDREQ_SCREEN, .ix = 175, .frre = 1, .kokey = 18 }, /* etage 36 */
    /* Les vingt et un etages suivants : New Generation, puis les deux bandes de 2I. */
    [339] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [340] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [341] = { .type = LDREQ_SCREEN, .ix = 176, .frre = 1, .kokey = 18 }, /* etage 37 */
    [342] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [343] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [344] = { .type = LDREQ_SCREEN, .ix = 177, .frre = 1, .kokey = 18 }, /* etage 38 */
    [345] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [346] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [347] = { .type = LDREQ_SCREEN, .ix = 178, .frre = 1, .kokey = 18 }, /* etage 39 */
    [348] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [349] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [350] = { .type = LDREQ_SCREEN, .ix = 179, .frre = 1, .kokey = 18 }, /* etage 40 */
    [351] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [352] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [353] = { .type = LDREQ_SCREEN, .ix = 180, .frre = 1, .kokey = 18 }, /* etage 41 */
    [354] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [355] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [356] = { .type = LDREQ_SCREEN, .ix = 181, .frre = 1, .kokey = 18 }, /* etage 42 */
    [357] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [358] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [359] = { .type = LDREQ_SCREEN, .ix = 182, .frre = 1, .kokey = 18 }, /* etage 43 */
    [360] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [361] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [362] = { .type = LDREQ_SCREEN, .ix = 183, .frre = 1, .kokey = 18 }, /* etage 44 */
    [363] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [364] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [365] = { .type = LDREQ_SCREEN, .ix = 184, .frre = 1, .kokey = 18 }, /* etage 45 */
    [366] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [367] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [368] = { .type = LDREQ_SCREEN, .ix = 185, .frre = 1, .kokey = 18 }, /* etage 46 */
    [369] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [370] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [371] = { .type = LDREQ_SCREEN, .ix = 186, .frre = 1, .kokey = 18 }, /* etage 47 */
    [372] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [373] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [374] = { .type = LDREQ_SCREEN, .ix = 187, .frre = 1, .kokey = 18 }, /* etage 48 */
    [375] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [376] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [377] = { .type = LDREQ_SCREEN, .ix = 188, .frre = 1, .kokey = 18 }, /* etage 49 */
    [378] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [379] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [380] = { .type = LDREQ_SCREEN, .ix = 189, .frre = 1, .kokey = 18 }, /* etage 50 */
    [381] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [382] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [383] = { .type = LDREQ_SCREEN, .ix = 190, .frre = 1, .kokey = 18 }, /* etage 51 */
    [384] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [385] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [386] = { .type = LDREQ_SCREEN, .ix = 191, .frre = 1, .kokey = 18 }, /* etage 52 */
    [387] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [388] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [389] = { .type = LDREQ_SCREEN, .ix = 192, .frre = 1, .kokey = 18 }, /* etage 53 */
    [390] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [391] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [392] = { .type = LDREQ_SCREEN, .ix = 193, .frre = 1, .kokey = 18 }, /* etage 54 */
    [393] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [394] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [395] = { .type = LDREQ_SCREEN, .ix = 194, .frre = 1, .kokey = 18 }, /* etage 55 */
    [396] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [397] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [398] = { .type = LDREQ_SCREEN, .ix = 195, .frre = 1, .kokey = 18 }, /* etage 56 */
    [399] = { .type = LDREQ_COLOR, .ix = 31, .frre = 1, .kokey = 2 },
    [400] = { .type = LDREQ_TEXTURE, .ix = 85, .frre = 1, .kokey = 19 },
    [401] = { .type = LDREQ_SCREEN, .ix = 196, .frre = 1, .kokey = 18 }, /* etage 57 */
};

const Span spans[] = {
    { .start = 0, .length = 5 },   { .start = 5, .length = 3 },   { .start = 10, .length = 4 },
    { .start = 15, .length = 4 },  { .start = 19, .length = 3 },  { .start = 25, .length = 5 },
    { .start = 30, .length = 4 },  { .start = 35, .length = 5 },  { .start = 40, .length = 3 },
    { .start = 45, .length = 4 },  { .start = 50, .length = 3 },  { .start = 55, .length = 4 },
    { .start = 60, .length = 4 },  { .start = 65, .length = 4 },  { .start = 70, .length = 4 },
    { .start = 75, .length = 4 },  { .start = 80, .length = 3 },  { .start = 85, .length = 3 },
    { .start = 90, .length = 3 },  { .start = 95, .length = 4 },  { .start = 100, .length = 5 },
    { .start = 105, .length = 3 }, { .start = 110, .length = 3 }, { .start = 115, .length = 3 },
    { .start = 120, .length = 3 }, { .start = 125, .length = 3 }, { .start = 130, .length = 3 },
    { .start = 135, .length = 3 }, { .start = 140, .length = 3 }, { .start = 145, .length = 3 },
    { .start = 150, .length = 3 }, { .start = 155, .length = 3 }, { .start = 160, .length = 3 },
    { .start = 165, .length = 3 }, { .start = 170, .length = 3 }, { .start = 175, .length = 3 },
    { .start = 180, .length = 3 }, { .start = 185, .length = 3 }, { .start = 190, .length = 3 },
    { .start = 195, .length = 3 }, { .start = 200, .length = 5 }, { .start = 206, .length = 4 },
    { .start = 294, .length = 3 }, /* etage 22 : SON PROPRE BLOC. On n'emprunte plus (avant :
                                      celui de Yang -- ses deux plans etaient pleins,
                                      mais son archive n'a que DEUX plans, et il en faut
                                      trois. Ryu et l'etage 14 sont les seuls a trois.

                                      ATTENTION -- `spans[]` sert DEUX familles :
                                      `Push_LDREQ_Queue_Player` l'indexe par
                                      PERSONNAGE, `Push_LDREQ_Queue_Union` par ETAGE,
                                      et l'etage N est a `spans[N + 20]`. L'etage 10
                                      est bien a `[30]` = {150,3}, l'etage 2 a `[22]`
                                      = {110,3}. Ecrire {10,4} ici -- le bloc du
                                      PERSONNAGE 2 -- faisait charger a l'etage les
                                      fichiers d'un combattant, et le jeu tombait
                                      avant meme d'arriver a `Bg_Texture_Load_EX`. */
    { .start = 297, .length = 3 }, /* etage 23 */
    { .start = 300, .length = 3 }, /* etage 24 */
    { .start = 303, .length = 3 }, /* etage 25 */
    { .start = 306, .length = 3 }, /* etage 26 */
    { .start = 309, .length = 3 }, /* etage 27 */
    { .start = 312, .length = 3 }, /* etage 28 */
    { .start = 315, .length = 3 }, /* etage 29 */
    { .start = 318, .length = 3 }, /* etage 30 */
    { .start = 321, .length = 3 }, /* etage 31 */
    { .start = 324, .length = 3 }, /* etage 32 */
    { .start = 327, .length = 3 }, /* etage 33 */
    { .start = 330, .length = 3 }, /* etage 34 */
    { .start = 333, .length = 3 }, /* etage 35 */
    { .start = 336, .length = 3 }, /* etage 36 */
    { .start = 339, .length = 3 }, /* etage 37 */
    { .start = 342, .length = 3 }, /* etage 38 */
    { .start = 345, .length = 3 }, /* etage 39 */
    { .start = 348, .length = 3 }, /* etage 40 */
    { .start = 351, .length = 3 }, /* etage 41 */
    { .start = 354, .length = 3 }, /* etage 42 */
    { .start = 357, .length = 3 }, /* etage 43 */
    { .start = 360, .length = 3 }, /* etage 44 */
    { .start = 363, .length = 3 }, /* etage 45 */
    { .start = 366, .length = 3 }, /* etage 46 */
    { .start = 369, .length = 3 }, /* etage 47 */
    { .start = 372, .length = 3 }, /* etage 48 */
    { .start = 375, .length = 3 }, /* etage 49 */
    { .start = 378, .length = 3 }, /* etage 50 */
    { .start = 381, .length = 3 }, /* etage 51 */
    { .start = 384, .length = 3 }, /* etage 52 */
    { .start = 387, .length = 3 }, /* etage 53 */
    { .start = 390, .length = 3 }, /* etage 54 */
    { .start = 393, .length = 3 }, /* etage 55 */
    { .start = 396, .length = 3 }, /* etage 56 */
    { .start = 399, .length = 3 }, /* etage 57 */
};

import numpy as np

COLORTABLE = np.array([
    [ 68,   1,  84],
    [ 68,   2,  85],
    [ 69,   3,  87],
    [ 69,   5,  88],
    [ 69,   6,  90],
    [ 70,   8,  91],
    [ 70,   9,  93],
    [ 70,  11,  94],
    [ 70,  12,  96],
    [ 71,  14,  97],
    [ 71,  15,  98],
    [ 71,  17, 100],
    [ 71,  18, 101],
    [ 71,  20, 102],
    [ 72,  21, 104],
    [ 72,  22, 105],
    [ 72,  24, 106],
    [ 72,  25, 108],
    [ 72,  26, 109],
    [ 72,  28, 110],
    [ 72,  29, 111],
    [ 72,  30, 112],
    [ 72,  32, 113],
    [ 72,  33, 115],
    [ 72,  34, 116],
    [ 72,  36, 117],
    [ 72,  37, 118],
    [ 72,  38, 119],
    [ 72,  39, 120],
    [ 71,  41, 121],
    [ 71,  42, 121],
    [ 71,  43, 122],
    [ 71,  44, 123],
    [ 71,  46, 124],
    [ 70,  47, 125],
    [ 70,  48, 126],
    [ 70,  49, 126],
    [ 70,  51, 127],
    [ 69,  52, 128],
    [ 69,  53, 129],
    [ 69,  54, 129],
    [ 68,  56, 130],
    [ 68,  57, 131],
    [ 68,  58, 131],
    [ 67,  59, 132],
    [ 67,  60, 132],
    [ 67,  62, 133],
    [ 66,  63, 133],
    [ 66,  64, 134],
    [ 65,  65, 134],
    [ 65,  66, 135],
    [ 65,  67, 135],
    [ 64,  69, 136],
    [ 64,  70, 136],
    [ 63,  71, 136],
    [ 63,  72, 137],
    [ 62,  73, 137],
    [ 62,  74, 137],
    [ 61,  75, 138],
    [ 61,  77, 138],
    [ 60,  78, 138],
    [ 60,  79, 138],
    [ 59,  80, 139],
    [ 59,  81, 139],
    [ 58,  82, 139],
    [ 58,  83, 139],
    [ 57,  84, 140],
    [ 57,  85, 140],
    [ 56,  86, 140],
    [ 56,  87, 140],
    [ 55,  88, 140],
    [ 55,  89, 140],
    [ 54,  91, 141],
    [ 54,  92, 141],
    [ 53,  93, 141],
    [ 53,  94, 141],
    [ 52,  95, 141],
    [ 52,  96, 141],
    [ 51,  97, 141],
    [ 51,  98, 141],
    [ 51,  99, 141],
    [ 50, 100, 142],
    [ 50, 101, 142],
    [ 49, 102, 142],
    [ 49, 103, 142],
    [ 48, 104, 142],
    [ 48, 105, 142],
    [ 47, 106, 142],
    [ 47, 107, 142],
    [ 47, 108, 142],
    [ 46, 109, 142],
    [ 46, 110, 142],
    [ 45, 111, 142],
    [ 45, 112, 142],
    [ 45, 112, 142],
    [ 44, 113, 142],
    [ 44, 114, 142],
    [ 43, 115, 142],
    [ 43, 116, 142],
    [ 43, 117, 142],
    [ 42, 118, 142],
    [ 42, 119, 142],
    [ 41, 120, 142],
    [ 41, 121, 142],
    [ 41, 122, 142],
    [ 40, 123, 142],
    [ 40, 124, 142],
    [ 40, 125, 142],
    [ 39, 126, 142],
    [ 39, 127, 142],
    [ 38, 128, 142],
    [ 38, 129, 142],
    [ 38, 130, 142],
    [ 37, 131, 142],
    [ 37, 131, 142],
    [ 37, 132, 142],
    [ 36, 133, 142],
    [ 36, 134, 142],
    [ 35, 135, 142],
    [ 35, 136, 142],
    [ 35, 137, 142],
    [ 34, 138, 141],
    [ 34, 139, 141],
    [ 34, 140, 141],
    [ 33, 141, 141],
    [ 33, 142, 141],
    [ 33, 143, 141],
    [ 32, 144, 141],
    [ 32, 145, 140],
    [ 32, 146, 140],
    [ 32, 147, 140],
    [ 31, 147, 140],
    [ 31, 148, 140],
    [ 31, 149, 139],
    [ 31, 150, 139],
    [ 31, 151, 139],
    [ 30, 152, 139],
    [ 30, 153, 138],
    [ 30, 154, 138],
    [ 30, 155, 138],
    [ 30, 156, 137],
    [ 30, 157, 137],
    [ 30, 158, 137],
    [ 30, 159, 136],
    [ 30, 160, 136],
    [ 31, 161, 136],
    [ 31, 162, 135],
    [ 31, 163, 135],
    [ 31, 163, 134],
    [ 32, 164, 134],
    [ 32, 165, 134],
    [ 33, 166, 133],
    [ 33, 167, 133],
    [ 34, 168, 132],
    [ 35, 169, 131],
    [ 35, 170, 131],
    [ 36, 171, 130],
    [ 37, 172, 130],
    [ 38, 173, 129],
    [ 39, 174, 129],
    [ 40, 175, 128],
    [ 41, 175, 127],
    [ 42, 176, 127],
    [ 43, 177, 126],
    [ 44, 178, 125],
    [ 46, 179, 124],
    [ 47, 180, 124],
    [ 48, 181, 123],
    [ 50, 182, 122],
    [ 51, 183, 121],
    [ 53, 183, 121],
    [ 54, 184, 120],
    [ 56, 185, 119],
    [ 57, 186, 118],
    [ 59, 187, 117],
    [ 61, 188, 116],
    [ 62, 189, 115],
    [ 64, 190, 114],
    [ 66, 190, 113],
    [ 68, 191, 112],
    [ 70, 192, 111],
    [ 72, 193, 110],
    [ 73, 194, 109],
    [ 75, 194, 108],
    [ 77, 195, 107],
    [ 79, 196, 106],
    [ 81, 197, 105],
    [ 83, 198, 104],
    [ 85, 198, 102],
    [ 88, 199, 101],
    [ 90, 200, 100],
    [ 92, 201,  99],
    [ 94, 201,  98],
    [ 96, 202,  96],
    [ 98, 203,  95],
    [101, 204,  94],
    [103, 204,  92],
    [105, 205,  91],
    [108, 206,  90],
    [110, 206,  88],
    [112, 207,  87],
    [115, 208,  85],
    [117, 208,  84],
    [119, 209,  82],
    [122, 210,  81],
    [124, 210,  79],
    [127, 211,  78],
    [129, 212,  76],
    [132, 212,  75],
    [134, 213,  73],
    [137, 213,  72],
    [139, 214,  70],
    [142, 215,  68],
    [144, 215,  67],
    [147, 216,  65],
    [149, 216,  63],
    [152, 217,  62],
    [155, 217,  60],
    [157, 218,  58],
    [160, 218,  57],
    [163, 219,  55],
    [165, 219,  53],
    [168, 220,  51],
    [171, 220,  50],
    [173, 221,  48],
    [176, 221,  46],
    [179, 221,  45],
    [181, 222,  43],
    [184, 222,  41],
    [187, 223,  39],
    [189, 223,  38],
    [192, 223,  36],
    [195, 224,  35],
    [197, 224,  33],
    [200, 225,  32],
    [203, 225,  30],
    [205, 225,  29],
    [208, 226,  28],
    [211, 226,  27],
    [213, 226,  26],
    [216, 227,  25],
    [219, 227,  24],
    [221, 227,  24],
    [224, 228,  24],
    [226, 228,  24],
    [229, 228,  24],
    [232, 229,  25],
    [234, 229,  25],
    [237, 229,  26],
    [239, 230,  27],
    [242, 230,  28],
    [244, 230,  30],
    [247, 230,  31],
    [249, 231,  33],
    [251, 231,  35],
    [254, 231,  36]
    ], dtype=np.uint8)

def viridis(val):
    """
    takes a value between 0 and 1, returns an ndarray containing [R,G,B]
    no interpolation, just round to nearest 8-bit value for now
    """
    idx = int(np.clip(val,0,1)*255)
    return COLORTABLE[idx]

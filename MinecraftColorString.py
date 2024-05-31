# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

from typing import Self

ColorName_To_Code = {
    "black": "§0",
    "dark_blue": "§1",
    "dark_green": "§2",
    "dark_aqua": "§3",
    "dark_red": "§4",
    "dark_purple": "§5",
    "gold": "§6",
    "gray": "§7",
    "dark_gray": "§8",
    "blue": "§9",
    "green": "§a",
    "aqua": "§b",
    "red": "§c",
    "light_purple": "§d",
    "yellow": "§e",
    "white": "§f",
}

CtrlName_To_Code = {
    "obfuscated": "§k",
    "bold": "§l",
    "strikethrough": "§m",
    "underline": "§n",
    "italic": "§o",

    "reset": "§r",
}

CodeState = {
    **{v: {"StackableWithOtherCodes": False} for v in ColorName_To_Code.values()},
    **{v: {"StackableWithOtherCodes": True} for v in CtrlName_To_Code.values()},
    "§r": {"StackableWithOtherCodes": False}
}

Code_To_ColorName = {v: k for k, v in ColorName_To_Code.items()}
Code_To_CtrlName = {v: k for k, v in CtrlName_To_Code.items()}

AllName_To_Code = {**ColorName_To_Code, **CtrlName_To_Code}
AllCode_To_Name = {**Code_To_ColorName, **Code_To_CtrlName}

ColorCode_Set = set(ColorName_To_Code.values())
CtrlCode_Set = set(CtrlName_To_Code.values())
AllCode_Set = ColorCode_Set | CtrlCode_Set

ColorName_Set = set(ColorName_To_Code.keys())
CtrlName_Set = set(CtrlName_To_Code.keys())
AllName_Set = ColorName_Set | CtrlName_Set

AllCodes = ColorCode_Set | CtrlCode_Set
AllNames = ColorName_Set | CtrlName_Set

ColorName_To_ANSI = {
    "black": "\033[30m",
    "dark_blue": "\033[34m",
    "dark_green": "\033[32m",
    "dark_aqua": "\033[36m",
    "dark_red": "\033[31m",
    "dark_purple": "\033[35m",
    "gold": "\033[33m",
    "gray": "\033[37m",
    "dark_gray": "\033[90m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "aqua": "\033[96m",
    "red": "\033[91m",
    "light_purple": "\033[95m",
    "yellow": "\033[93m",
    "white": "\033[97m",
}

CtrlName_To_ANSI = {
    "obfuscated": "\033[8m",
    "bold": "\033[1m",
    "strikethrough": "\033[9m",
    "underline": "\033[4m",
    "italic": "\033[3m",

    "reset": "\033[0m",
}

AllName_To_ANSI = {**ColorName_To_ANSI, **CtrlName_To_ANSI}

ColorName_To_RGB = {
    "black": (0, 0, 0),
    "dark_blue": (0, 0, 170),
    "dark_green": (0, 170, 0),
    "dark_aqua": (0, 170, 170),
    "dark_red": (170, 0, 0),
    "dark_purple": (170, 0, 170),
    "gold": (255, 170, 0),
    "gray": (170, 170, 170),
    "dark_gray": (85, 85, 85),
    "blue": (85, 85, 255),
    "green": (85, 255, 85),
    "aqua": (85, 255, 255),
    "red": (255, 85, 85),
    "light_purple": (255, 85, 255),
    "yellow": (255, 255, 85),
    "white": (255, 255, 255),
}

CtrlName_To_RGB = {
    "reset": (255, 255, 255),

    "obfuscated": None,
    "bold": None,
    "strikethrough": None,
    "underline": None,
    "italic": None,
}

AllName_To_RGB = {**ColorName_To_RGB, **CtrlName_To_RGB}
RGB_To_ColorName = {v: k for k, v in ColorName_To_RGB.items()}


def hex_to_rgb(hex_str: str) -> tuple[int, ...]:
    if hex_str.startswith("#"):
        hex_str = hex_str[1:]

    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)

    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_ansi(r, g, b):
    # 计算红、绿、蓝三种颜色通道的强度值所对应的 ANSI 转义码
    return f"\033[38;2;{r};{g};{b}m"


def string_to_code_list(string) -> list[list[list[str] | str]]:
    """Convert the string to a list of lists of strings and codes"""

    color_with_str = []
    cache_codes = []
    cache_string = ''
    while string:
        try:
            i = string.index('§')
        except ValueError:
            break
        try:
            code = string[i:i + 2]
        except IndexError:
            break

        if code not in AllCodes:
            print(f"Unknown code: {code}")
            # 把这个code原样加进去
            cache_string += code
            string = string[i + 1:]
            continue

        tmp_string = string[:i]
        tmp_string.replace(code, '')

        if CodeState[code]["StackableWithOtherCodes"]:
            cache_string += tmp_string
        elif cache_string or cache_codes:
            color_with_str.append([cache_codes.copy(), cache_string + tmp_string])
            cache_codes.clear()
            cache_string = ''

        cache_codes.append(code)

        string = string[i + 2:]

    if string:
        color_with_str.append([cache_codes.copy(), string])

    return color_with_str


def get_similar_RGB(r, g, b):
    build_in_rgb: list[list[int, int, int]] = list(RGB_To_ColorName.keys())
    # 在build_in_rgb中查找与r,g,b最接近的颜色并返回那个最接近的颜色
    nearest_rgb = (None, None, None)
    for i, rgb in enumerate(build_in_rgb):
        if nearest_rgb[0] is None:
            nearest_rgb = rgb
            continue

        abs_r = abs(rgb[0] - r)
        abs_g = abs(rgb[1] - g)
        abs_b = abs(rgb[2] - b)

        if abs_r + abs_g + abs_b < abs(nearest_rgb[0] - r) + abs(nearest_rgb[1] - g) + abs(nearest_rgb[2] - b):
            nearest_rgb = rgb

    return nearest_rgb[0], nearest_rgb[1], nearest_rgb[2]


def generate_html_text(special_controls, color, text):
    # 初始化一个空字符串，用来存放生成的HTML文本
    html_text = ""

    # 设置文本颜色
    html_text += f"<span style='color: rgb({color[0]}, {color[1]}, {color[2]});'>"

    # 根据特殊控制列表，应用相应的HTML标签
    if "bold" in special_controls:
        html_text += "<strong>"

    if "italic" in special_controls:
        html_text += "<em>"

    if "underline" in special_controls:
        html_text += "<u>"

    if "strikethrough" in special_controls:
        html_text += "<s>"

    # 添加文本
    html_text += text

    # 关闭HTML标签
    if "strikethrough" in special_controls:
        html_text += "</s>"

    if "underline" in special_controls:
        html_text += "</u>"

    if "italic" in special_controls:
        html_text += "</em>"

    if "bold" in special_controls:
        html_text += "</strong>"

    # 关闭span标签
    html_text += "</span>"

    return html_text


ColorData = dict[str, list[str] | list[int, int, int] | str]


class ColorString:
    def __init__(self, raw_data: list[ColorData]):
        self._raw_data = raw_data

    @property
    def raw_data(self) -> list[ColorData]:
        return self._raw_data.copy()

    @classmethod
    def from_dict(cls, json_dict) -> Self:
        class ParseType:
            Extra = "extra"
            Text = "text"
            UnKnow = None

        if "extra" in json_dict:
            parse_type = ParseType.Extra
        elif "text" in json_dict:
            parse_type = ParseType.Text
        elif "translate" in json_dict:
            parse_type = ParseType.Text
            json_dict["text"] = json_dict["translate"]
        elif type(json_dict) is str:
            parse_type = ParseType.Text
            json_dict = cls.from_string(json_dict).to_dict()
        elif type(json_dict) is list:
            parse_type = ParseType.Extra
            json_dict = {"extra": json_dict}
        else:
            raise ValueError("Unknown json dict")

        def _parse_extra(data) -> list[ColorData]:
            rets = []
            for item in data["extra"]:
                rets.append(_parse_text(item))

            return rets

        def _parse_text(data: dict) -> ColorData:
            if type(data) is not dict:
                data = {"text": str(data)}

            string = data["text"]

            ctrls = []
            rgb_color = (255, 255, 255)

            for code in CtrlName_Set:
                if data.get(code):
                    ctrls.append(code)

            if data.get("color"):
                color: str = data["color"]
                if color not in ColorName_Set:
                    if not color.startswith("#"):
                        raise ValueError(f"Unknown color: {color}")
                    rgb_color = hex_to_rgb(color)
                else:
                    rgb_color = AllName_To_RGB[color]

            return {"ctrls": ctrls, "rgb": rgb_color, "text": string}

        if parse_type == ParseType.Extra:
            result = _parse_extra(json_dict)

        elif parse_type == ParseType.Text:
            result = [_parse_text(json_dict)]
        else:
            print(json_dict)
            raise ValueError("Unknown parse type")

        return cls(result)

    @classmethod
    def from_string(cls, string: str) -> Self:
        data = []
        for code_list, text in string_to_code_list(string):
            ctrls = []
            color_rgb = (255, 255, 255)
            for code in code_list:
                code_name = AllCode_To_Name[code]
                if code in CtrlCode_Set:
                    ctrls.append(code_name)
                    continue

                color_rgb = ColorName_To_RGB[code_name]

            data.append({"ctrls": ctrls, "rgb": color_rgb, "text": text})
        return cls(data)

    def to_ansi(self):
        string = ''
        for item in self._raw_data:
            ansi_cache = []
            for ctrl in item["ctrls"]:
                ansi_cache.append(AllName_To_ANSI[ctrl])
            ansi_cache.append(rgb_to_ansi(*item["rgb"]))
            string += ''.join(ansi_cache)
            string += item["text"]

        return string

    def to_string(self):
        string = ''
        for item in self._raw_data:
            code_cache = []
            for ctrl in item["ctrls"]:
                code_cache.append(CtrlName_To_Code[ctrl])

            code_cache.insert(0, ColorName_To_Code[RGB_To_ColorName[get_similar_RGB(*item["rgb"])]])
            string += ''.join(code_cache)
            string += item["text"]

        return string

    def to_html(self):
        html_text = ""
        for item in self._raw_data:
            html_text += generate_html_text(item["ctrls"], item["rgb"], item["text"])
        return html_text

    def to_dict(self):
        ret_dict = {"text": '', "extra": []}

        for item in self._raw_data:
            this_dict = {}
            for ctrl in item["ctrls"]:
                this_dict[ctrl] = True

            if item["rgb"] in RGB_To_ColorName:
                this_dict["color"] = RGB_To_ColorName[item["rgb"]]
            else:
                this_dict["color"] = rgb_to_hex(*item["rgb"])
            this_dict["text"] = item["text"]

            ret_dict["extra"].append(this_dict)

        return ret_dict

    def to_json(self):
        import json
        return json.dumps(self.to_dict())

    def __repr__(self):
        return f"<ColorString: {self._raw_data}>"

    def __str__(self):
        return str(self._raw_data)


def example():
    # Hello World

    string = "&aHello &bWorld"
    print(string)
    cs = ColorString.from_string(string.replace('&', '§'))
    print(cs.to_ansi() + "\033[0m")
    print(cs.to_string())
    print(cs.to_html())
    print(cs.to_dict())
    print(cs.to_json())
    print(cs.raw_data)


if __name__ == '__main__':
    example()

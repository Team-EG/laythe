from .flags import LaytheSettingFlags


def parse_second(time: int):
    parsed_time = ""
    day = time // (24 * 60 * 60)
    time -= day * (24 * 60 * 60)
    hour = time // (60 * 60)
    time -= hour * (60 * 60)
    minute = time // 60
    time -= minute * 60
    if day:
        parsed_time += f"{day}일 "
    if hour:
        parsed_time += f"{hour}시간 "
    if minute:
        parsed_time += f"{minute}분 "
    parsed_time += f"{time}초"
    return parsed_time


def parse_bytesize(bytesize: float):
    gb = round(bytesize / (1000 * 1000 * 1000), 1)
    if gb < 1:
        mb = round(bytesize / (1000 * 1000), 1)
        if mb < 1:
            return f"{bytesize}KB"
        return f"{mb}MB"
    return f"{gb}GB"


def to_setting_flags(flags):
    return LaytheSettingFlags.from_value(flags)


def to_readable_bool(tf: bool):
    return "네" if tf else "아니요"

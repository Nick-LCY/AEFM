from time import time
from .logger import log

timer_dict = {}


def timer(name: str, total_count: int = 0, level: str = "info"):
    def inner(func):
        def wrapper(*args, **kwargs):
            if name not in timer_dict:
                timer_dict[name] = {
                    "start": int(time()),
                    "count": 0,
                    "current": int(time()),
                }
                if total_count != 0:
                    timer_dict[name]["total_count"] = total_count
                log.debug(f"Create timer for \"{name}\".")
                return func(*args, **kwargs)

            named_timer = timer_dict[name]
            named_timer["current"] = int(time())
            named_timer["count"] += 1
            info = f"Time cost by \"{name}\" - "
            total = named_timer["current"] - named_timer["start"]
            info += f"Total: {parser(total)}; "
            average = total // named_timer["count"]
            info += f"Average: {parser(average)}; "
            if "total_count" in named_timer:
                est = (named_timer["total_count"] - named_timer["count"]) * average
                info += f"Estimated left: {parser(est)}; "
            log.log(info[:-2], level=level)
            return func(*args, **kwargs)

        return wrapper

    return inner


def parser(seconds: int):
    hours = format(seconds // 3600, "02d")
    minutes = format((seconds % 3600) // 60, "02d")
    secs = format(seconds % 3600 % 60, "02d")
    return f"{hours}:{minutes}:{secs}"

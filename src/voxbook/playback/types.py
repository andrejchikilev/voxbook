from typing import Callable, Literal

LogFn = Callable[[str], None]
PlaybackResult = Literal["completed", "next", "previous", "stopped"]

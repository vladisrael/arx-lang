from dataclasses import dataclass, field
from typing import Set

@dataclass
class ArtemisData:
    map_paths:Set[str] = field(default_factory=set)
    library_paths:Set[str] = field(default_factory=set)
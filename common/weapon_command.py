from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.projectile import ProjectileModifier

from dataclasses import dataclass, field
from datetime import timedelta, datetime

@dataclass
class WeaponCommand:
    id: str
    delay: timedelta = field(default=timedelta(seconds=0))
    modifiers: list[ProjectileModifier] = field(default_factory=list)
    time: datetime = field(default_factory=datetime.now, init=False)
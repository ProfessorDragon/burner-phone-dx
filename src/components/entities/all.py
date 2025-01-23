from typing import Any
from components.entities.button import ButtonEntity
from components.entities.checkpoint import CheckpointEntity
from components.entities.entity import Entity
from components.entities.lake import LakeEnemy
from components.entities.patrol import PatrolEnemy
from components.entities.security_camera import SecurityCameraEnemy
from components.entities.sign import SignEntity
from components.entities.spike_trap import SpikeTrapEnemy
from components.entities.spotlight import SpotlightEnemy
from components.entities.zombie import ZombieEnemy


ENTITY_CLASSES = [
    # enemies
    LakeEnemy,
    SpikeTrapEnemy,
    SecurityCameraEnemy,
    ZombieEnemy,
    PatrolEnemy,
    SpotlightEnemy,
    # other
    ButtonEntity,
    SignEntity,
    CheckpointEntity,
]


def entity_from_json(js: dict[str, Any]) -> Entity:
    for cls in ENTITY_CLASSES:
        if cls.__name__ == js["class"]:
            return cls.from_json(js)
    return None

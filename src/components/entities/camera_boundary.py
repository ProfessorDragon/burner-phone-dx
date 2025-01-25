import pygame

import core.assets as a
import core.constants as c
from components.motion import Direction
from components.camera import Camera, camera_rect, camera_to_screen_shake
from components.entities.entity import Entity
from components.player import Player
from scenes.scene import PLAYER_OR_FG, RenderLayer


class CameraBoundaryEntity(Entity):
    def __init__(self):
        super().__init__()
        self.w, self.h = 1, 1
        self.direction = Direction.N
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            self.motion.position.x,
            self.motion.position.y,
            c.TILE_SIZE * self.w,
            c.TILE_SIZE * self.h,
        )

    def to_json(self):
        return {
            "pos": (*self.motion.position,),
            "w": self.w,
            "h": self.h,
            "direction": self.direction.name,
        }

    @staticmethod
    def from_json(js):
        ent = CameraBoundaryEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.w, ent.h = js.get("w", 1), js.get("h", 1)
        if js.get("direction"):
            ent.direction = Direction[js["direction"]]
        return ent

    def reset(self) -> None:
        pass

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        # because collision uses the actual camera position, the bounds will only 'unlock'
        # once the velocity of the camera is great enough to to avoid collision over the
        # span of one frame. this gives the locking a nice snappy feel. however, if the
        # boundary is approached from the wrong direction, this makes it practically
        # impossible to unlock until the player crosses the boundary onto the correct side.
        crect = camera_rect(camera)
        hitbox = self.get_hitbox()
        if self.direction in (Direction.N, Direction.S):
            if crect.colliderect(hitbox.inflate(0, 2)):
                if self.direction == Direction.N:
                    target = hitbox.top - crect.h // 2
                else:
                    target = hitbox.bottom + crect.h // 2
                camera.motion.position.y = target
        elif self.direction in (Direction.E, Direction.W):
            if crect.colliderect(hitbox.inflate(2, 0)):
                if self.direction == Direction.E:
                    target = hitbox.right + crect.width // 2
                else:
                    target = hitbox.left - crect.width // 2
                camera.motion.position.x = target

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_OR_FG and c.DEBUG_HITBOXES:
            text = a.DEBUG_FONT.render(self.direction.name, False, c.RED)
            hitbox = self.get_hitbox()
            surface.blit(
                text,
                camera_to_screen_shake(
                    camera,
                    hitbox.centerx - text.get_width() // 2,
                    hitbox.centery - text.get_height() // 2,
                ),
            )

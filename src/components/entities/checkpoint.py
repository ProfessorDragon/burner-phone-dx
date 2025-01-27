import pygame

import core.assets as a
import core.constants as c
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import Entity
from components.player import (
    MainStoryProgress,
    Player,
    PlayerInteraction,
    player_rect,
    player_set_checkpoint,
)
from scenes.scene import PLAYER_OR_FG, RenderLayer


class CheckpointEntity(Entity):
    def __init__(self):
        super().__init__()
        self.w, self.h = 1, 1
        self.story: MainStoryProgress = None
        self.scene_name: str = None
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
            "story": (None if self.story is None else self.story.name),
            "scene_name": self.scene_name,
        }

    @staticmethod
    def from_json(js):
        ent = CheckpointEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.w, ent.h = js.get("w", 1), js.get("h", 1)
        if js.get("story"):
            ent.story = MainStoryProgress[js["story"]]
        ent.scene_name = js.get("scene_name")
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
        hitbox = self.get_hitbox()
        if player_rect(player.motion).colliderect(hitbox):
            player_set_checkpoint(player, hitbox.center)
            if self.story is not None and player.progression.main_story < self.story:
                player.progression.main_story = self.story
            if self.scene_name is not None:
                player.interaction = PlayerInteraction(self.scene_name, False)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_OR_FG and c.DEBUG_HITBOXES:
            content = ""
            if self.story is not None:
                content = self.story.name
            if self.scene_name is not None:
                content += "*"
            if content:
                text = a.DEBUG_FONT.render(content, False, c.RED)
                hitbox = self.get_hitbox()
                surface.blit(
                    text,
                    camera_to_screen_shake(
                        camera,
                        hitbox.centerx - text.get_width() // 2,
                        hitbox.centery - text.get_height() // 2,
                    ),
                )

import pygame

import core.constants as c
from components.motion import Direction
from components.camera import Camera
from components.entities.entity import Entity
from components.player import MainStoryProgress, Player, player_rect
from scenes.scene import RenderLayer


# todo [copied from checkpoint rn]
class CameraBoundaryEntity(Entity):
    def __init__(self):
        super().__init__()
        self.w, self.h = 1, 1
        self.direction = Direction.N
        self.main_story_progress: MainStoryProgress = None
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
            "main_story": self.main_story_progress.name,
        }

    @staticmethod
    def from_json(js):
        ent = CameraBoundaryEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.w, ent.h = js.get("w", 1), js.get("h", 1)
        if "main_story" in js:
            ent.main_story_progress = MainStoryProgress[js["main_story"]]
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
            player.progression.checkpoint = hitbox.center - pygame.Vector2(16, 32)
            if (
                self.main_story_progress is not None
                and player.progression.main_story < self.main_story_progress
            ):
                player.progression.main_story = self.main_story_progress

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        pass

import pygame

import core.assets as a
import core.constants as c
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import Entity
from components.player import Player, PlayerInteraction, player_rect
from scenes.scene import PLAYER_LAYER, PLAYER_OR_BG, PLAYER_OR_FG, RenderLayer


class SignEntity(Entity):
    def __init__(self):
        super().__init__()
        self.scene_name = "DEFAULT SIGN"
        self.color = 0
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x - 2, self.motion.position.y + 16, 20, 20)

    def to_json(self):
        return {"pos": (*self.motion.position,), "scene_name": self.scene_name, "color": self.color}

    @staticmethod
    def from_json(js):
        entity = SignEntity()
        entity.motion.position = pygame.Vector2(js["pos"])
        entity.scene_name = js.get("scene_name", "DEFAULT SIGN")
        entity.color = js.get("color", 0)
        return entity

    def reset(self) -> None:
        self.show_arrow = False

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        if player.z_position == 0 and player_rect(player.motion).colliderect(self.get_hitbox()):
            self.show_arrow = True
            player.interaction = PlayerInteraction(self.scene_name, True)
        else:
            self.show_arrow = False
            if player.interaction.scene_name == self.scene_name:
                player.interaction.scene_name = None

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if (self.color < 2 and layer in PLAYER_LAYER) or (
            self.color >= 2 and layer in PLAYER_OR_BG
        ):
            surface.blit(
                a.TERRAIN,
                camera_to_screen_shake(camera, *self.motion.position),
                (self.color * c.TILE_SIZE, 6 * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE),
            )
        if self.show_arrow and layer in PLAYER_OR_FG:
            x, y = self.motion.position
            x += c.HALF_TILE_SIZE
            y -= 6
            points = [(x - 4, y - 13), (x + 4, y - 13), (x + 4, y - 1), (x, y + 2), (x - 4, y - 1)]
            pygame.draw.polygon(
                surface, c.BLACK, [camera_to_screen_shake(camera, *point) for point in points]
            )
            points = (x - 3, y - 3), (x, y), (x + 3, y - 3)
            pygame.draw.polygon(
                surface, c.WHITE, [camera_to_screen_shake(camera, *point) for point in points]
            )
            text = a.DEBUG_FONT.render("A", False, c.WHITE)
            surface.blit(
                text,
                camera_to_screen_shake(
                    camera, x - text.get_width() // 2, y - text.get_height() - 3
                ),
            )

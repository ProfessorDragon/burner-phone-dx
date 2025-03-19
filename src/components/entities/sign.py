import pygame

from components.motion import Direction
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
        self.floor = False
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        if self.floor:
            return pygame.Rect(self.motion.position.x - 2, self.motion.position.y - 2, 20, 20)
        else:
            return pygame.Rect(self.motion.position.x - 2, self.motion.position.y + 16, 20, 20)

    def to_json(self):
        return {
            "pos": (*self.motion.position,),
            "scene_name": self.scene_name,
            "color": self.color,
            "floor": self.floor,
        }

    @staticmethod
    def from_json(js):
        ent = SignEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.scene_name = js.get("scene_name", "DEFAULT SIGN")
        ent.color = js.get("color", 0)
        ent.floor = js.get("floor", False)
        return ent

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
            player.interaction = PlayerInteraction(
                self.scene_name, True, None if self.floor else Direction.N
            )
        else:
            self.show_arrow = False
            if player.interaction.scene_name == self.scene_name:
                player.interaction.scene_name = None

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if (not self.floor and layer in PLAYER_LAYER) or (self.floor and layer in PLAYER_OR_BG):
            surface.blit(
                a.TERRAIN,
                camera_to_screen_shake(camera, *self.motion.position),
                (self.color * c.TILE_SIZE, 6 * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE),
            )
        if self.show_arrow and layer in PLAYER_OR_FG:
            x, y = self.motion.position
            x += c.HALF_TILE_SIZE
            y -= 4
            points = [
                (x - 18, y - 14),
                (x + 17, y - 14),
                (x + 17, y - 4),
                (x + 6, y - 4),
                (x, y + 2),
                (x - 6, y - 4),
                (x - 18, y - 4),
            ]
            pygame.draw.polygon(
                surface, c.BLACK, [camera_to_screen_shake(camera, *point) for point in points]
            )
            points = [(x - 3, y - 3), (x, y), (x + 3, y - 3)]
            pygame.draw.polygon(
                surface, c.WHITE, [camera_to_screen_shake(camera, *point) for point in points]
            )
            text = a.DEBUG_FONT.render("JUMP", False, c.WHITE)
            surface.blit(
                text,
                camera_to_screen_shake(
                    camera, x - text.get_width() // 2, y - text.get_height() - 3
                ),
            )

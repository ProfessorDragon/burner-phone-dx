import pygame

from components.audio import AudioChannel, play_sound
import core.assets as a
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import Entity
from components.player import Player, player_rect
from scenes.scene import RenderLayer


class ButtonEntity(Entity):
    def __init__(self):
        super().__init__()
        self.activated = False
        self.id = "default"
        self.color = 0
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 3, self.motion.position.y + 2, 10, 12)

    def to_json(self):
        return {"pos": (*self.motion.position,), "id": self.id, "color": self.color}

    @staticmethod
    def from_json(js):
        ent = ButtonEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.id = js.get("id", "default")
        ent.color = js.get("color", 0)
        return ent

    def reset(self) -> None:
        self.stepped_on = False

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        # collision
        self.activated = self.id in player.progression.activated_buttons
        if player.z_position == 0:
            prect = player_rect(player.motion)
            prev_stepped = self.stepped_on
            self.stepped_on = prect.colliderect(self.get_hitbox())
            if self.stepped_on and not prev_stepped:
                player.progression.activated_buttons.add(self.id)
                play_sound(AudioChannel.ENTITY, a.ZOMBIE_CHASE)  # todo
        else:
            self.stepped_on = False

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer == RenderLayer.RAYS:
            surface.blit(
                a.BUTTON_FRAMES[self.color * 2 + (self.stepped_on or self.activated)],
                camera_to_screen_shake(camera, *self.motion.position),
            )

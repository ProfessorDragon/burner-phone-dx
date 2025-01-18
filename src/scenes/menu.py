import pygame

import core.constants as c
import core.input as i
import core.assets as a
from components.camera import (
    Camera,
    camera_update,
    camera_to_screen_shake,
    camera_reset,
)
from components.motion import Vector2, Motion
from components.animation import (
    Animator,
    Animation,
    animator_get_frame,
    animator_update,
    animator_initialise,
    animator_switch_animation,
)
from components.settings import Settings, settings_render, settings_update
from components.dialogue import (
    DialogueSystem, dialogue_initialise, dialogue_update, dialogue_add_packet,
    dialogue_render, dialogue_try_reset, dialogue_packet_create
)

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera(Motion.empty(), Vector2(),
                             Vector2(), Vector2(30, 30))

        self.debug = Animator()
        debug_animation_mapping = {0: Animation(a.DEBUG_FRAMES, 0.1)}
        animator_initialise(self.debug, debug_animation_mapping, 0)

        debug_size = animator_get_frame(self.debug).get_size()
        self.debug_pos = Vector2(
            c.WINDOW_CENTRE[0] - debug_size[0] // 2,
            c.WINDOW_CENTRE[1] - debug_size[1] // 2,
        )

        self.settings = Settings()
        self.dialogue = DialogueSystem()
        dialogue_initialise(self.dialogue)
        dialogue_add_packet(self.dialogue, dialogue_packet_create(
            a.DEBUG_SPRITE_SMALL,
            "Unknown",
            "TEsting. Testing? 1, 2, 3!\nbest\ndialogue\nEVER!!!"
        ))
        dialogue_add_packet(self.dialogue, dialogue_packet_create(
            a.DEBUG_SPRITE_SMALL,
            "nwonknu",
            "Dialogue can even be queued!?\nThis is\nAweSOME!"
        ))
        dialogue_add_packet(self.dialogue, dialogue_packet_create(
            a.DEBUG_SPRITE_SMALL,
            "Unknown",
            f"Press <SELECT> to fast skip to end\n!!?!.!?>@?@>./.21\n{'!'*40}"
        ))

    def enter(self) -> None:
        dialogue_try_reset(self.dialogue)
        camera_reset(self.camera)
        animator_switch_animation(self.debug, 0)
        pygame.mixer.Channel(0).play(a.DEBUG_THEME_MENU, -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: i.InputBuffer,
        mouse_buffer: i.InputBuffer,
    ) -> None:
        # INPUT
        if action_buffer[i.Action.START] == i.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.GAME)
            return

        if action_buffer[i.Action.B] == i.InputState.HELD:
            self.camera.trauma += 0.01

        # UPDATE
        camera_update(self.camera, dt)
        animator_update(self.debug, dt)
        in_dialogue = dialogue_update(
            self.dialogue, dt, action_buffer, mouse_buffer
        )

        if not in_dialogue:
            settings_update(self.settings, dt, action_buffer, mouse_buffer)

        # RENDER
        surface.fill(c.WHITE)
        surface.blit(
            animator_get_frame(self.debug),
            camera_to_screen_shake(self.camera, *self.debug_pos),
        )
        dialogue_render(self.dialogue, surface)

        if not in_dialogue:
            settings_render(self.settings, surface)

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()

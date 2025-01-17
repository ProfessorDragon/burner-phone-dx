from enum import IntEnum, auto

# Import all scenes
import scenes.menu
import scenes.game


# Create a SceneState for each scene
class SceneState(IntEnum):
    MENU = 0
    GAME = auto()


# Assign SceneState to a Scene
SCENE_MAPPING = {
    SceneState.MENU: scenes.menu.Menu,
    SceneState.GAME: scenes.game.Game,
}

import arcade
from lobby import Lobby

window_width = 1280
window_height = 720

def main():
    window = arcade.Window(
        width=window_width,
        height=window_height,
        title="poop!",
        fullscreen=True,
        resizable=False
    )
    window.center_window()
    window.show_view(Lobby())
    arcade.run()


if __name__ == "__main__":
    main()
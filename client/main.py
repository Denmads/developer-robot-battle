from time import sleep
from client.core.game_client import GameClient


def main():
    client = GameClient()
    client.start()



if __name__ == "__main__":
    main()
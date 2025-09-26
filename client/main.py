from time import sleep
from client.core.game_client import GameClient


def main():
    id = input("Enter player id: ")
    client = GameClient(id)
    client.start()



if __name__ == "__main__":
    main()
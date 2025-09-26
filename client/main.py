from time import sleep
from client.core.tcp_client import TCPClient
from common.tcp_messages import InputMessage


def main():
    tcp_client = TCPClient()
    tcp_client.connect()

    sleep(0.1)

    tcp_client.send(InputMessage(1, 65, 1))



if __name__ == "__main__":
    main()
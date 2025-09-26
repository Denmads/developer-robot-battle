from common.tcp_messages import InputMessage
from server.tcp_server import TCPServer


def main():
    tcp_server = TCPServer(input_received)
    tcp_server.start()


def input_received(mes: InputMessage):
    print(mes)

if __name__ == "__main__":
    main()
from common.robot import RobotInterface


class MyRobot(RobotInterface):

    def create_robot(self) -> None:
        print("Creating Robot")

    def do_ability(self, index: int) -> None:
        pass
from . import *

class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def exists(self):
        return not select(f"SELECT `user_id` FROM `geoimpostor`.`users` WHERE user_id = '{self.user_id}'").value is None

    def create(self, points: int):
        update(f"INSERT INTO `geoimpostor`.`users` (`user_id`, `points`) VALUES ('{self.user_id}', '{points}')")

    def get_points(self) -> int:
        return int(select(f"SELECT `points` FROM `geoimpostor`.`users` WHERE user_id = '{self.user_id}'").value)

    def add_points(self, amount: int) -> int:
        if self.exists():
            amount = self.get_points() + amount
            update(f"UPDATE `geoimpostor`.`users` SET `points` = '{amount}' WHERE `user_id` = '{self.user_id}'")
        else:
            self.create(amount)
        return amount
    
    @staticmethod
    def reset_guessed():
        update(f"UPDATE `geoimpostor`.`users` SET `has_guessed` = '0'")

    @staticmethod
    def get_top(amount: int):
        return select(f"SELECT `user_id`, `points` FROM `geoimpostor`.`users` ORDER BY `points` DESC LIMIT {amount}").value_all

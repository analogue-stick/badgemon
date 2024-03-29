from game import constants


class Item():
    def __init__(self, item_ty: constants.ItemType, quantity: int):
        self.ty = item_ty
        self.quantity = quantity

    def applies_to_self(self) -> bool:
        """
        Can be only used on your own badgemon
        """
        return self.ty > 4

    def applies_to_other(self) -> bool:
        """
        Can only be used on the enemy badgemon
        """
        return self.ty < 5
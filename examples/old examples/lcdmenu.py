from rpilcdmenu import *
from rpilcdmenu.items import *


class Menu (object):

    def __init__(self):
        self.kill = False

    def fooFunction(self, item_index):
        """
        sample method with a parameter
        """
        print("item %d pressed" % (item_index))


    def initMenu(self):
        self.menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])
        self.function_item1 = FunctionItem("Item 1", self.fooFunction, [1])
        self.function_item2 = FunctionItem("Item 2", self.fooFunction, [2])
        self.menu.append_item(self.function_item1).append_item(self.function_item2)

        # global submenu
        self.submenu = RpiLCDSubMenu(self.menu)
        self.submenu_item = SubmenuItem("SubMenu (3)", self.submenu, self.menu)
        self.menu.append_item(self.submenu_item)

        self.submenu.append_item(FunctionItem("Item 31", self.fooFunction, [31])).append_item(
            FunctionItem("Item 32", self.fooFunction, [32]))
        self.submenu.append_item(FunctionItem("Back", self.exitSubMenu, [self.submenu]))

        self.menu.append_item(FunctionItem("Item 4", self.fooFunction, [4]))

        self.menu.start()
        self.menu.debug()
        print("----")

    def exitSubMenu(self):
        return self.menu.exit()

    def Enter(self):
        return self.menu.processEnter()

    def scrollUp(self):
        return self.menu.processDown()

    def scrollDown(self):
        return self.menu.processUp()

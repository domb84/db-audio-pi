from rpilcdmenu import *
from rpilcdmenu.items import *
from time import sleep


class Menu():

    def __init__(self):
        self.menu = RpiLCDMenu(7, 8, [25, 24, 23, 15])
        self.submenu = RpiLCDSubMenu(self.menu)

        # global self.submenu
        function_item1 = FunctionItem("Item 1", self.fooFunction, [1])
        function_item2 = FunctionItem("Item 2", self.fooFunction, [2])
        self.menu.append_item(function_item1).append_item(function_item2)

        submenu_item = SubmenuItem("Submenu (3)", self.submenu, self.menu)
        self.menu.append_item(submenu_item)

        self.submenu.append_item(FunctionItem("Item 31", self.fooFunction, [31])).append_item(
            FunctionItem("Item 32", self.fooFunction, [32]))
        self.submenu.append_item(FunctionItem("Back", self.exitSubMenu, [self.submenu]))

        self.menu.append_item(FunctionItem("Item 4", self.fooFunction, [4]))

        self.menu.start()
        self.menu.debug()
        print("----")

        print(self.menu.parent)


    def fooFunction(self, item_index):
        """
        sample method with a parameter
        """
        print("Item %d pressed" % (item_index))
        return

    def exitSubMenu(self, submenu):
        print(str(submenu) + "  exited")
        return submenu.exit()

    def Enter(self):
        self.menu.processEnter()
        return

    def Up(self):
        self.menu.processUp()
        return

    def Down(self):
        self.menu.processDown()
        return

    def subEnter(self):
        self.submenu.processEnter()
        return

    def subUp(self):
        self.submenu.processUp()
        return

    def subDown(self):
        self.submenu.processDown()
        return

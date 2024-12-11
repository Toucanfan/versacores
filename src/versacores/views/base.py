from versacores.core import Core

class ViewBase:
    def __init__(self, core: Core):
        self._core = core

    @staticmethod
    def say_hello(msg):
        print(msg)
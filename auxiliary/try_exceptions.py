class MyError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else "текст ошибки"



raise MyError('asdfasdfasdfasdf')
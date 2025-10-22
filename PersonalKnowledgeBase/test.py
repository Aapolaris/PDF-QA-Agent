import os


session = {}


def func1():
    print(session[1])


def func2():
    global session
    session = {1: 3}


if __name__ == '__main__':
    # func2()
    # func1()
    val = os.environ.get("MYSQL_PASSWORD")
    print(val)
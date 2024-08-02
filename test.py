from suzakuhk2df import SuzakuHK2DF

if __name__ == "__main__":
    s = SuzakuHK2DF("2010-01-01", "2010-01-05", "D:/suzaku_data")
    print(s.setup(True))
    print(s.hk2df(60))

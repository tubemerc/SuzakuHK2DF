# Example of using SuzakuHK2DF

from suzakuhk2df import SuzakuHK2DF

if __name__ == "__main__":
    s = SuzakuHK2DF("2012-01-23 01:27:51", "2012-01-24 01:27:51", "D:/suzaku_data")
    print(s.setup(True))
    print(s.hk2df(True, 60, 1e-5))

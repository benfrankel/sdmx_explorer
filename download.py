#!/usr/bin/env python3

import client2
import init


# TODO
def main():
    init.init()
    imf = client2.ImfClient()
    data = imf.download()
    save(data)


def save(data):
    pass


if __name__ == "__main__":
    main()

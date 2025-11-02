#!/usr/bin/env python3

import client
import init


def main():
    init.init()
    client.SdmxClient().repl()


if __name__ == "__main__":
    main()

import json
import os as os


def init_node():
    masterchain_config = json.load(open("out/masterchain-config.json"))

    os.system("mkdir -p ~/masterchain/masterchain_data/keystore")
    os.system("mkdir -p ~/masterchain/masterchain_data/masterchain")
    os.system("cp out/rootNodeKey/* ~/masterchain/masterchain_data/keystore")
    os.system("cp -rf out/nodekey ~/masterchain/masterchain_data/masterchain/nodekey")
    os.system("cp out/compiled.js ~/masterchain/")
    os.system("~/masterchain/meth --datadir ~/masterchain/masterchain_data --whitelist \""
              + masterchain_config["whitelist"] + "\" init out/masterchain-genesis.json")

    print("Node established. \n")


def main():
    init_node()


if __name__ == "__main__":
    main()

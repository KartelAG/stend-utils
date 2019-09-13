import json
import os as os


def init_node():
    masterchain_config = json.load(open("out/masterchain-config.json"))

    os.system("mkdir -p ~/masterchain/masterchain_data/keystore")
    os.system("mkdir -p ~/masterchain/masterchain_data/masterchain")
    os.system("cp out/rootNodeSignKey/* ~/masterchain/masterchain_data/keystore")
    os.system("cp out/adminKey/* ~/masterchain/masterchain_data/keystore")
    os.system("cp out/authorityKey/* ~/masterchain/masterchain_data/keystore")
    os.system("cp -rf out/clientkey ~/masterchain/masterchain_data/masterchain/clientkey")
    os.system("cp -rf out/serverkey ~/masterchain/masterchain_data/masterchain/serverkey")
    os.system("cp -rf out/signblockkey ~/masterchain/masterchain_data/masterchain/signblockkey")
    os.system("cp out/compiled.js ~/masterchain/")
    os.system("~/masterchain/meth --datadir ~/masterchain/masterchain_data --whitelist \""
              + masterchain_config["whitelist"] + "\" init out/masterchain-genesis.json")


def main():
    init_node()


if __name__ == "__main__":
    main()

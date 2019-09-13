import binascii
import json
import os
import random as random
import sys as sys
import time as time


def pad(hex_value, size):
    return '0x' + hex_value[2:].zfill(size)


# Whitelist contract required another contract named Masklib.
# We have masklib & whitelist bin strings, saved in templates.
# Masklib and whitelist should have different addresses in chain.


def make_whitelist_address():
    whitelist_bytes = binascii.b2a_hex(os.urandom(20))
    globals()['whitelist'] = '0x' + whitelist_bytes.decode("utf-8")
    masklib_bytes = binascii.b2a_hex(os.urandom(20))
    globals()['masklib'] = '0x' + masklib_bytes.decode("utf-8")


def make_genesis(template):
    config = json.load(open("out/masterchain-config.json"))
    masklib_bin_runtime = open("../templates/masklib_bin_runtime.txt").readline()
    whitelist_bin_runtime = open("../templates/nodewhitelist_bin_runtime.txt").readline()
    masklib_string = open("../templates/masklib_string.txt").readline()
    masklib_addr = str(globals()['masklib'][2:])
    whitelist_bin_runtime = whitelist_bin_runtime.replace(masklib_string, masklib_addr)

    insert_contract_bin(template, whitelist_bin_runtime, masklib_bin_runtime)
    build_storage(template, config)
    fund_accounts(template, config)
    set_additionals(template)

    with open('out/masterchain-genesis.json', 'w') as outfile:
        json.dump(template, outfile, indent=4, sort_keys=True)

    os.system(
        "echo -n 'var wl_authority = \"" + config["authority"] + "\";\n' >> out/compiled.js")
    os.system(
        "echo -n 'var wl_admin = \"" + config["admin"] + "\";\n' >> out/compiled.js")
    os.system(
        "echo -n 'var rootnode = \"" + config["rootNode"] + "\";\n' >> out/compiled.js")


def insert_contract_bin(template, whitelist_bin_runtime, masklib_bin_runtime):
    template["alloc"][globals()['masklib']]["code"] = '0x' + masklib_bin_runtime
    template["alloc"][globals()['whitelist']]["code"] = '0x' + whitelist_bin_runtime


# additional values
def set_additionals(template):
    template["nonce"] = hex(int(random.getrandbits(32)))
    template["timestamp"] = hex(int(time.time()))


# build storage
# magic numbers 2 & 4 is the order of variables in NodeWhitelist.
# NodeWhitelist imports AuthorityOwnable, so AO variables will be first in positions.
# 0 === authority
# 2 === rootNode
# 4 === expirationTime
def build_storage(template, config):
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(0), 64)] = pad(config["authority"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(2), 64)] = pad(config["rootNode"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(4), 64)] = pad(hex(config["expiration_time"]), 16)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(5), 64)] = pad(hex(1), 16)


# fund accounts
def fund_accounts(template, config):
    template["alloc"][config["authority"]] = {}
    template["alloc"][config["authority"]]["balance"] = str(1000000000000000000000000000)
    template["alloc"][config["admin"]] = {}
    template["alloc"][config["admin"]]["balance"] = str(1000000000000000000000000000)
    template["alloc"][config["rootNode"]] = {}
    template["alloc"][config["rootNode"]]["balance"] = str(0)


# With safe procedure, you should generate the key pair only for rootnode.
def generate_keys():
    os.system("rm -rf /tmp/tempMasterData")
    os.system("rm -rf ./out/*")
    os.system("mkdir /tmp/tempMasterData")

    print("[*] ...Nodekey generation")
    rootnode_account_creation = os.system(
        "~/masterchain/meth --datadir /tmp/tempMasterData account list")
    if rootnode_account_creation != 0:
        sys.exit("Check your CSP license")

    os.system("mkdir -p out/rootNodeKey")
    os.system("cp `find /tmp/tempMasterData/keystore/ -name UTC* | sort -n | tail -1` ./out/rootNodeKey")
    os.system("cp /tmp/tempMasterData/masterchain/nodekey ./out/")

    os.system("rm -rf /tmp/tempMasterData")


def prepare_compiled_js():
    os.system("echo -n 'var abi = ' > out/compiled.js")
    os.system("cat ../templates/whitelist_abi.json >> out/compiled.js")
    os.system("echo -n ';\n' >> out/compiled.js")
    os.system(
        "echo -n 'var whitelist = web3.eth.contract(abi).at(\"" + str(
            globals()['whitelist']) + "\");\n' >> out/compiled.js")


def make_config():
    if len(os.listdir("out/rootNodeKey")) != 1:
        sys.exit("Script requires 1 key file")

    masterchain_config = json.load(open("../templates/config.json"))
    masterchain_config["whitelist"] = str(globals()['whitelist'])

    # extract rootNode key
    for key in os.listdir("out/rootNodeKey"):
        json_rootnode_key_data = json.load(open("out/rootNodeKey/" + key))
        masterchain_config["rootNode"] = json_rootnode_key_data["Address"]

    # extract authority key
    masterchain_config["authority"] = str(globals()['wl_authority'])
    masterchain_config["admin"] = str(globals()['wl_admin'])

    print("Authority address: " + masterchain_config["authority"] + ". This is the key to your private network.")
    print("Admin address: " + masterchain_config["admin"])
    print("RootNode address: " + masterchain_config["rootNode"])
    print("Whitelist address: " + masterchain_config["whitelist"])
    with open('out/masterchain-config.json', 'w') as outfile:
        json.dump(masterchain_config, outfile)


def prepare_template():
    template = json.load(open("../templates/genesis_template.json"))
    template["alloc"][globals()['whitelist']] = {}
    template["alloc"][globals()['whitelist']]["code"] = ""
    template["alloc"][globals()['whitelist']]["storage"] = {}
    template["alloc"][globals()['whitelist']]["balance"] = "0"

    template["alloc"][globals()['masklib']] = {}
    template["alloc"][globals()['masklib']]["code"] = ""
    template["alloc"][globals()['masklib']]["storage"] = {}
    template["alloc"][globals()['masklib']]["balance"] = "0"

    return template


def addresses_request(key_type):
    print("\n\n")
    key = input("Please input the " + str(key_type) + " address with 0x prefix: ")
    if len(key) != 42:
        print("Wrong length.")
        sys.exit(-1)
    elif key[0:2] != "0x":
        print("Bad prefix.")
        sys.exit(-1)
    else:
        globals()[key_type] = key
    return True


def welcome_message():
    print("=== MASTERCHAIN SAFE NETWORK SETUP ===\n")
    print("Safe network means all transactions which change Whitelist should be signed with cold wallets. \n"
          "Please use common network setup if this option is not needed.\n\n")
    print("To continue with safe network setup, \n"
          "please generate two different addresses on a separate node without Internet access.\n\n")
    confirmation = input("Continue (y/n): ")
    if confirmation != "y":
        print("\nYou entered 'n'. Exit.\n")
        sys.exit(-1)


def main():
    welcome_message()
    addresses_request('wl_authority')
    addresses_request('wl_admin')
    make_whitelist_address()
    template = prepare_template()
    generate_keys()
    prepare_compiled_js()
    make_config()
    make_genesis(template)


if __name__ == "__main__":
    main()

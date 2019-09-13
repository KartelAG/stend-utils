import binascii
import json
import os
import fnmatch
import re
import random as random
import sys as sys
import time as time


def pad(hex_value, size):
    return '0x' + hex_value[2:].zfill(size)


def make_address():
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
        "echo -n 'var sign_addr = \"" + config["signBlockAddress"] + "\";\n' >> out/compiled.js")
    os.system(
        "echo -n 'var srv_addr = \"" + config["serverAddress"] + "\";\n' >> out/compiled.js")
    os.system(
        "echo -n 'var cln_addr = \"" + config["clientAddress"] + "\";\n' >> out/compiled.js")


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
# 2 === signBlockAddress - blocksigner
# 4 === expirationTime
def build_storage(template, config):
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(0), 64)] = pad(config["authority"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(2), 64)] = pad(config["signBlockAddress"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(3), 64)] = pad(config["serverAddress"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(4), 64)] = pad(config["clientAddress"], 64)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(6), 64)] = pad(hex(config["expiration_time"]), 16)
    template["alloc"][globals()['whitelist']]["storage"][pad(hex(7), 64)] = pad(hex(1), 16)


# fund accounts
def fund_accounts(template, config):
    template["alloc"][config["authority"]] = {}
    template["alloc"][config["authority"]]["balance"] = str(1000000000000000000000000000)
    template["alloc"][config["admin"]] = {}
    template["alloc"][config["admin"]]["balance"] = str(1000000000000000000000000000)
    template["alloc"][config["signBlockAddress"]] = {}
    template["alloc"][config["signBlockAddress"]]["balance"] = str(0)


def generate_keys():
    print("[*] Keys generation\n\n")
    os.system("rm -rf /tmp/tempMasterData")
    os.system("rm -rf ./out/*")
    os.system("mkdir /tmp/tempMasterData")

    print("[*] ...Nodekeys importing. 3 keys will be import")

    print("[*] ...Node tls server key")
    rootnode_serverkey_import = os.system("~/masterchain/meth import-node-keys --datadir /tmp/tempMasterData -serverkey")
    if rootnode_serverkey_import != 0:
        sys.exit("Invalid certificate was chosen")

    print("[*] ...Node tls client key")
    rootnode_clientkey_import = os.system("~/masterchain/meth import-node-keys --datadir /tmp/tempMasterData -clientkey")
    if rootnode_clientkey_import != 0:
        sys.exit("Invalid certificate was chosen")

    print("[*] ...Node sign block key")
    rootnode_signblockkey_import = os.system("~/masterchain/meth import-node-keys --datadir /tmp/tempMasterData -signblockkey")
    if rootnode_signblockkey_import != 0:
        sys.exit("Invalid certificate was chosen")

    rootnode_account_creation = os.system(
        "~/masterchain/meth --datadir /tmp/tempMasterData account list")
    if rootnode_account_creation != 0:
        sys.exit("Check your CSP license")

    os.system("mkdir -p out/rootNodeSignKey")
    os.system("cp `find /tmp/tempMasterData/keystore/ -name UTC* | sort -n | tail -1` ./out/rootNodeSignKey")

    os.system("~/masterchain/meth --datadir /tmp/tempMasterData --exec 'admin.nodeInfo' console  2>&1 |"
              " grep -E \"address:|server:|client:\" >> /tmp/tempMasterData/node_addresses")

    admin_account_creation = os.system(
        "~/masterchain/meth --datadir /tmp/tempMasterData account import-csp-unused")
    if admin_account_creation != 0:
        sys.exit("Authority passphrase mismatch")

    os.system("mkdir -p out/authorityKey")
    os.system("cp `find /tmp/tempMasterData/keystore/ -name UTC* | sort -n | tail -2 | head -1` ./out/authorityKey")

    os.system("mkdir -p out/adminKey")
    os.system("cp `find /tmp/tempMasterData/keystore/ -name UTC* | sort -n | tail -1` ./out/adminKey")

    os.system("cp /tmp/tempMasterData/node_addresses ./out/")
    os.system("cp /tmp/tempMasterData/masterchain/clientkey ./out/")
    os.system("cp /tmp/tempMasterData/masterchain/serverkey ./out/")
    os.system("cp /tmp/tempMasterData/masterchain/signblockkey ./out/")
    os.system("rm -rf /tmp/tempMasterData")


def prepare_compiled_js():
    os.system("echo -n 'var abi = ' > out/compiled.js")
    os.system("cat ../templates/whitelist_abi.json >> out/compiled.js")
    os.system("echo -n ';\n' >> out/compiled.js")
    os.system(
        "echo -n 'var whitelist = web3.eth.contract(abi).at(\"" + str(
            globals()['whitelist']) + "\");\n' >> out/compiled.js")


def make_config():
    if len(fnmatch.filter(os.listdir("out"), "node_addresses")) != 1 \
            | len(os.listdir("out/adminKey")) != 1 \
            | len(os.listdir("out/authorityKey")) != 1:
        sys.exit("Script requires 3 key files")

    masterchain_config = json.load(open("../templates/config.json"))
    masterchain_config["whitelist"] = str(globals()['whitelist'])

    # extract rootNode addresses
    addrs = list()
    s = open("out/node_addresses","r+")
    for line in s.readlines():
        pair = re.split(': \"|\",', line)
        if len(pair) == 3:
            addrs.append(pair[1])
    s.close()

    masterchain_config["signBlockAddress"] = addrs[0]
    masterchain_config["serverAddress"] = addrs[1]
    masterchain_config["clientAddress"] = addrs[2]

    # extract authority key
    for key in os.listdir("out/authorityKey"):
        json_authority_key_data = json.load(open("out/authorityKey/" + key))
        masterchain_config["authority"] = json_authority_key_data["Address"]

    # extract admin key
    for key in os.listdir("out/adminKey"):
        json_admin_key_data = json.load(open("out/adminKey/" + key))
        masterchain_config["admin"] = json_admin_key_data["Address"]

    print(
        "\n\nAuthority address: " + masterchain_config["authority"] + ". You MUST backup this key. This is the key for your "
                                                                  "private network.")
    print("Admin address: " + masterchain_config["admin"])
    print("RootNode sign block address: " + masterchain_config["signBlockAddress"])
    print("RootNode server address: " + masterchain_config["serverAddress"])
    print("RootNode client address: " + masterchain_config["clientAddress"])
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


def main():
    make_address()
    template = prepare_template()
    generate_keys()
    prepare_compiled_js()
    make_config()
    make_genesis(template)


if __name__ == "__main__":
    main()

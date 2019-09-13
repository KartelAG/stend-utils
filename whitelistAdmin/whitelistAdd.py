#!/usr/bin/python3.6

import json
import os
import sys
import time

from web3 import Web3, IPCProvider

json_abi = json.load(open("./whitelist_abi.json", "r"))
wl = "0xc9fa1b7919400b438bed82f58745013bba1818d5"

bootNodeIP = '192.168.201.12'

connectionString = "http://"+bootNodeIP+":20000"
my_provider = Web3.HTTPProvider(connectionString)
w3 = Web3(my_provider)

wl_authority = "0xfb6960d6a753704983f5c1692a424bdf63c9190f";
wl_admin = "0xa64f9cc7f58513a6527de909693222ebfdc2690d";
sign_addr = "0x7b388a986abac5e50b6d28896c62bff3af319571";
srv_addr = "0x3756d2058474c173cbb4076f335bb526dbeb4205";
cln_addr = "0xf0305c5c1790c54b5c4c32d0ceba3fdeee8539cc";

def is_node_activated():
    whitelist = w3.eth.contract(abi=json_abi, address=Web3.toChecksumAddress(wl))
    return not whitelist.functions.rootNodeAllowed().call()

def register_reader_node_addresses(node_name, node_server_address, node_client_address):
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are adding node server/client adresses. \n"
              "You will ne asked about admin account.\n")

        node_reference = node_name
        node_read_mask = 1

        current_admin = Web3.toChecksumAddress(wl_admin)
        # unlock admin
        unlock_result = w3.personal.unlockAccount(current_admin, "")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return 255

        stat1 = register_transaction(node_server_address, node_read_mask, node_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
        stat2 = register_transaction(node_client_address, node_read_mask, node_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat2, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")


def register_signer_node_addresses(node_name, node_signer_address):
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are adding node signer adresses. \n"
              "You will ne asked about admin account.\n")

        node_reference = node_name
        node_read_mask = 2

        current_admin = Web3.toChecksumAddress(wl_admin)
        # unlock admin
        unlock_result = w3.personal.unlockAccount(current_admin, "")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return 255

        stat1 = register_transaction(node_signer_address, node_read_mask, node_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")

def register_transaction(new_node_address, new_node_mask, new_node_reference, current_admin):
    whitelist = w3.eth.contract(abi=json_abi, address=Web3.toChecksumAddress(wl))

    admin_account_privileged = whitelist.functions.isAdmin(Web3.toChecksumAddress(current_admin)).call()
    if not admin_account_privileged:
        print("Account {} is not admin of whitelist. Returning.".format(current_admin))
        return user_dialog()

    register_node_data = whitelist.encodeABI(fn_name='register',
                                             args=[Web3.toChecksumAddress(new_node_address), new_node_mask, new_node_reference])
    new_gas_price = w3.eth.gasPrice + 1000
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(current_admin))
    register_node = {'data': register_node_data, 'to': Web3.toChecksumAddress(wl),
                     'from': Web3.toChecksumAddress(current_admin), 'gas': 4700000, 'gasPrice': new_gas_price, 
                     'nonce': nonce}
    register_node_check = w3.eth.call(register_node)
    if not register_node_check:
        print("Test call returned False. Unable to register node {}, {}".format(new_node_address, new_node_reference))
        return 255

    # send transaction
    print("Sending transaction...")
    register_transact = w3.eth.sendTransaction(register_node)
    return register_transact

def get_transaction_status(transaction_hash, timeout):
    try:
        txn_receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout)
    except Exception:
        return {'status': 'failed', 'error': 'timeout'}
    else:
        return {'status': 'success', 'receipt': txn_receipt}

def truncQuotes(str):
  return str.replace("\n", "").replace("\"", "")

logFile = open("miners.txt", "r")
logFileReader = logFile.readlines()

for nodeLine in logFileReader:
  node = nodeLine.split(" ")
  node = list(map(truncQuotes, node))
  try:
    register_reader_node_addresses(node[0], node[1], node[2])
  except:
    print("Unable to register reader/client  node {}".format(node[0]))
  try:
    register_signer_node_addresses(node[0], node[3])
  except:
    print("Unable to register signer node {}".format(node[0]))


logFile.close()


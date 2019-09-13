import os
import sys
import time
import json
import glob

from web3 import Web3, HTTPProvider, IPCProvider

globals()['masterchain_dir_path'] = '~/masterchain/masterchain_data/'
globals()['meth_ipc_path'] = str("~/masterchain/masterchain_data/meth.ipc")
w3 = Web3()


def welcome_message():
    print("WELCOME TO WHITELIST MANAGEMENT WIZARD\n")
    update_provider_addr('ipc')


def update_provider_addr(provider_type):
    if provider_type == 'ipc':
        print("IPC provider selected. The default provider location: " + globals()['meth_ipc_path'])
        addr = str(input("Please provide a full path to IPC or press Enter to use the default value: "))
        if addr == "":
            print("Using default addr " + globals()['meth_ipc_path'])
        else:
            print("Using new addr " + addr)
            globals()['meth_ipc_path'] = addr


def init_vars():
    global w3
    w3 = Web3(IPCProvider(globals()['meth_ipc_path']))


def check_status():
    print("\n ***Checking node status*** \n ")
    last_block = w3.eth.blockNumber
    is_mining = w3.eth.mining

    print("*Last block: " + str(last_block))
    print("*Mining enabled? " + str(is_mining))

    if not is_mining:
        print("*Enabling mining...")
        w3.miner.start(1)
    print("*Waiting for new block...")
    while w3.eth.blockNumber == last_block:
        print('*', end='')
        time.sleep(10)

    if w3.eth.blockNumber > last_block:
        print("\nChecks are ok.\n")


def read_config_files():
    if (not os.path.isfile("../templates/whitelist_abi.json")) | (not os.path.isfile("out/masterchain-config.json")):
        print("Unable to read abi & config files")
        sys.exit(-1)

    globals()['json_abi'] = json.load(open("../templates/whitelist_abi.json", "r"))
    masterchain_config = json.load(open("out/masterchain-config.json", "r"))
    globals()['whitelist'] = masterchain_config['whitelist']
    globals()['admin'] = masterchain_config['admin']
    globals()['authority'] = masterchain_config['authority']
    globals()['rootNode'] = masterchain_config['rootNode']


def test_whitelist():
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    try:
        print("Whitelist rootNode: " + whitelist.functions.rootNode().call())
        print("Whitelist authority: " + whitelist.functions.authority().call())
    except FileNotFoundError:
        print("{} file not available. Check your node is running.".format(globals()['meth_ipc_path']))
        sys.exit(-1)


def is_node_activated():
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    return not whitelist.functions.rootNodeAllowed().call()


def prepare_register_transaction():
    if is_node_activated():
        print("Whitelist activated. You are free to add any node. "
              "Wizard will ask you new node address and reference below.\n")
        address = enter_address_dialog("node")
        mask = enter_mask_dialog()
        reference = input("Enter new node reference. It can be any string:   ")
    else:
        print("Whitelist is not activated. You only can add rootnode that set in masterchain-config.json")
        address = globals()['rootNode']
        mask = 3
        reference = "rootNode"

    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(globals()['admin']))
    new_gas_price = w3.eth.gasPrice + 1000
    register_node_data = whitelist.encodeABI(fn_name='register',
                                             args=[Web3.toChecksumAddress(address), mask, reference])
    register_node = {'data': register_node_data, 'from': globals()['admin'],
                     'to': globals()['whitelist'], 'gas': 4700000, 'gasPrice': new_gas_price, 'nonce': nonce}
    admin_tx_filename = 'REGISTER_' + str(address) + '_transactions_for_' + globals()['admin']
    with open(admin_tx_filename, 'w') as admin_tx:
        admin_tx.write(json.dumps(register_node))
    print("*** File %s written. Copy this file and sign it using cold wallet ***" % admin_tx_filename)
    user_dialog()


def user_dialog():
    print("\nSelect an action: ")
    print("1. Create ADDADMIN transaction")
    print("2. Create REGISTER transaction")
    print("3. Send signed transaction to network")
    print("4. Check node activated")
    print("5. Exit")
    user_choice = input("Please choose the action:   ")
    if user_choice == '1':
        prepare_addadmin_transaction()
    elif user_choice == '2':
        prepare_register_transaction()
    elif user_choice == '3':
        send_signed_transactions()
    elif user_choice == '4':
        print("Node activated? %s" % is_node_activated())
        return user_dialog()
    elif user_choice == '5':
        sys.exit(0)
    else:
        return user_dialog()


def enter_address_dialog(address_type):
    address = input("Please input the " + str(address_type) + " address with 0x prefix:   ")
    if len(address) != 42:
        print("Wrong length.")
        return enter_address_dialog(address_type)
    elif address[0:2] != "0x":
        print("Bad prefix.")
        return enter_address_dialog(address_type)
    return address


def enter_mask_dialog():
    mask = int(input("Enter node mask: 1 (read) or 3 (read/write):   "))
    if mask != 1 | mask != 3:
        print("Bad mask entered. You can only use 1 or 3.")
        return enter_mask_dialog()
    return mask


def prepare_addadmin_transaction():
    if is_node_activated():
        print("Whitelist activated. You are free to add any account as admin. "
              "Wizard will ask you new admin address and reference below.\n")
        admin_address = enter_address_dialog("admin")
        admin_reference = input("Enter new admin reference. It can be any string:   ")
    else:
        print("Whitelist is not activated. You only can add admin that set in masterchain-config.json")
        admin_address = globals()['admin']
        admin_reference = "firstAdmin"

    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    new_gas_price = w3.eth.gasPrice + 100

    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(globals()['authority']))
    add_admin_data = whitelist.encodeABI(fn_name='addAdmin',
                                         args=[Web3.toChecksumAddress(admin_address), admin_reference])
    add_admin = {'data': add_admin_data, 'from': globals()['authority'], 'to': globals()['whitelist'],
                 'gas': 4700000, 'gasPrice': new_gas_price, 'nonce': nonce}
    authority_tx_filename = 'ADDADMIN_' + str(admin_address) + '_transactions_for_' + globals()['authority']
    with open(authority_tx_filename, 'w') as authority_tx:
        authority_tx.write(json.dumps(add_admin))
    print("*** File %s written. Copy this file and sign it using cold wallet ***" % authority_tx_filename)
    user_dialog()


def tx_file_choose(filetype):
    filenames = glob.glob(filetype + "_signed_by_*")
    if len(filenames) == 0:
        print("No files with the mask %s available." % filetype)
        return None

    print("Available files: ")
    for i in range(0, len(filenames)):
        print("%s: %s" % (i, filenames[i]))
    choice = int(input("Please enter number of file to use: "))
    if choice not in range(0, len(filenames)):
        print("Wrong file id. Try again")
        return tx_file_choose(filetype)
    return filenames[choice]


def send_signed_transactions():
    print("\nYou can send two types transactions: ADDADMIN or REGISTER. \n"
          "1. Send ADDADMIN transaction \n"
          "2. Send REGISTER transaction \n"
          "3. Return to  \n")
    user_choice = int(input("Your choice?  "))
    if user_choice not in range(1, 4):
        print("Bad value entered. Please enter 1 or 2 or 3.")
        return send_signed_transactions()

    filename = None
    if user_choice == 1:
        filename = tx_file_choose("ADDADMIN")
    elif user_choice == 2:
        filename = tx_file_choose("REGISTER")
    elif user_choice == 3:
        return user_dialog()

    if filename is not None:
        status = send_raw_transaction(filename)
        if status['status'] == 'success':
            print("Transaction included in block #%s" % status['receipt']['blockNumber'])
        else:
            print("Transaction execution failed.")
        return user_dialog()
    else:
        return send_signed_transactions()


def send_raw_transaction(filename):
    with open(filename, 'r') as raw_transaction_file:
        raw_string = str(raw_transaction_file.readline())
    raw_tx = raw_string[18:][:-1]
    print("Raw tx: " + raw_tx)

    proceed = str(input("Proceed (y/n)?    "))
    if proceed == "y":
        transaction_hash = w3.eth.sendRawTransaction(raw_tx)
        print("Transaction hash: %s. Waiting for execution..." % transaction_hash.hex())
        try:
            txn_receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=300)
        except Exception:
            return {'status': 'failed', 'error': 'timeout'}
        else:
            return {'status': 'success', 'receipt': txn_receipt}
    else:
        return send_signed_transactions()


def main():
    welcome_message()
    read_config_files()
    init_vars()
    test_whitelist()
    check_status()
    user_dialog()


if __name__ == "__main__":
    main()

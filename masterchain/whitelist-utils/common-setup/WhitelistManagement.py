import getpass
import json
import os
import sys
import time

from web3 import Web3, IPCProvider

globals()['masterchain_dir_path'] = '~/masterchain/masterchain_data/'
globals()['meth_ipc_path'] = str("~/masterchain/masterchain_data/meth.ipc")
w3 = Web3()


def welcome_message():
    print("WELCOME TO WHITELIST MANAGEMENT WIZARD\n")
    update_provider_addr('ipc')


def update_provider_addr(provider_type):
    if provider_type == 'ipc':
        print("IPC provider selected. Default provider location: " + globals()['meth_ipc_path'])
        addr = str(input("Please provide full path to IPC or press Enter to use default: "))
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
    globals()['signBlockAddress'] = masterchain_config['signBlockAddress']
    globals()['serverAddress'] = masterchain_config['serverAddress']
    globals()['clientAddress'] = masterchain_config['clientAddress']


def test_whitelist():
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    try:
        print("Whitelist signBlockAddress: " + whitelist.functions.rootNode().call())
        print("Whitelist authority: " + whitelist.functions.authority().call())
    except FileNotFoundError:
        print("{} file not available. Check your node is running.".format(globals()['meth_ipc_path']))
        sys.exit(-1)


def is_node_activated():
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))
    return not whitelist.functions.rootNodeAllowed().call()


def user_dialog():
    print("\nAvailable actions: ")
    print("1. Add admin")
    print("2. Register rootnode addresses")
    print("3. Register node server/client addresses")
    print("4. Register node signer address")
    print("5. Ban node server/client address")
    print("6. Ban node signer address")
    print("8. Check node activated")
    print("9. Exit")
    user_choice = input("Please choose the action:   ")
    if user_choice == '1':
        add_admin_transaction()
    elif user_choice == '2':
        register_root_addresses()
    elif user_choice == '3':
        register_reader_node_addresses()
    elif user_choice == '4':
        register_signer_node_addresses()
    elif user_choice == '5':
        ban_reader_node_addresses()
    elif user_choice == '6':
        ban_signer_node_addresses()
    # elif user_choice == '3':
    #     send_signed_transactions()
    elif user_choice == '8':
        print("Node address activated? {}".format(is_node_activated()))
        return user_dialog()
    elif user_choice == '9':
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
    mask = int(input("Enter address mask: 1 (read), 2 (mine) or 3 (read/mine):   "))
    if mask != 1 | mask != 2 | mask != 3:
        print("Bad mask entered. You can only use 1, 2 or 3.")
        return enter_mask_dialog()
    return mask


def unlock_account(account, account_type):
    pwd = getpass.getpass("Enter {} {} account password:   ".format(account, account_type))
    try:
        w3.personal.unlockAccount(Web3.toChecksumAddress(account), pwd, 30)
    except ValueError as ex:
        print("Error: {}".format(ex))
        return False
    else:
        return True


def add_admin_transaction():
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
    authority_account = whitelist.functions.authority().call()
    new_gas_price = w3.eth.gasPrice + 100
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(authority_account))

    add_admin_data = whitelist.encodeABI(fn_name='addAdmin',
                                         args=[Web3.toChecksumAddress(admin_address), admin_reference])
    add_admin = {'data': add_admin_data, 'from': Web3.toChecksumAddress(authority_account),
                 'to': Web3.toChecksumAddress(globals()['whitelist']),
                 'gas': 4700000, 'gasPrice': new_gas_price, 'nonce': nonce}
    admin_check = w3.eth.call(add_admin)

    if not admin_check:
        print("Test call returned False. Unable to add admin {}, {}".format(admin_address, admin_reference))
        return user_dialog()
    # unlock authority
    unlock_result = unlock_account(authority_account, "AUTHORITY")
    if not unlock_result:
        print("Unable to unlock account. Returning.")
        return user_dialog()

    # send transaction
    print("Sending transaction...")
    admin_transact = w3.eth.sendTransaction(add_admin)
    print("Transaction execution status: {}".format(get_transaction_status(admin_transact, 300)['status']))
    user_dialog()


def ban_reader_node_addresses():
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are changing mask for node server/client addresses. \n"
              "Wizard will ask you new mask and node server and client addresses.\n"
              "You will be asked about admin account.\n")

        new_mask = 0
        node_server_address = enter_address_dialog("node server")
        node_client_address = enter_address_dialog("node client")
        current_admin = enter_address_dialog("admin")

        # unlock admin
        unlock_result = unlock_account(current_admin, "ADMIN")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return user_dialog()

        stat1 = change_mask_transaction(node_server_address, new_mask, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
        stat2 = change_mask_transaction(node_client_address, new_mask, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat2, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")

    user_dialog()


def ban_signer_node_addresses():
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are changing mask for signing node address.\n"
              "Wizard will ask you new mask and node signer address.\n"
              "You will be asked about admin account.\n")

        new_mask = 0
        node_sign_address = enter_address_dialog("node signer")
        current_admin = enter_address_dialog("admin")

        # unlock admin
        unlock_result = unlock_account(current_admin, "ADMIN")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return user_dialog()

        stat1 = change_mask_transaction(node_sign_address, new_mask, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")

    user_dialog()


def register_reader_node_addresses():
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are adding node server/client adresses. \n"
              "Wizard will ask you new node server and client addresses and reference below.\n"
              "You will ne asked about admin account.\n")

        node_server_address = enter_address_dialog("node server")
        node_client_address = enter_address_dialog("node client")
        node_reference = input("Enter new node reference. It can be any string:   ")
        node_read_mask = 1

        current_admin = enter_address_dialog("admin")
        # unlock admin
        unlock_result = unlock_account(current_admin, "ADMIN")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return user_dialog()

        stat1 = register_transaction(node_server_address, node_read_mask, node_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
        stat2 = register_transaction(node_client_address, node_read_mask, node_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat2, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")

    user_dialog()


def register_signer_node_addresses():
    activated = is_node_activated()
    if activated:
        print("Whitelist is activated. You are adding signing node address.\n"
              "Wizard will ask you new node signer address and reference below.\n"
              "You will be asked about admin account.\n")

        node_sign_address = enter_address_dialog("node signer")
        node_sign_reference = input("Enter new node reference. It can be any string:   ")
        node_sign_mask = 2

        current_admin = enter_address_dialog("admin")

        # unlock admin
        unlock_result = unlock_account(current_admin, "ADMIN")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return user_dialog()

        stat1 = register_transaction(node_sign_address, node_sign_mask, node_sign_reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(stat1, 300)['status']))
    else:
        print("Whitelist is not activated. Select action 2 (Register rootnode addresses).")

    user_dialog()


def register_root_addresses():
    activated = is_node_activated()
    if activated:
        print("You are trying to add rootnode addresses with activated whitelist.\n"
              "Action aborted.\n")
    else:
        print("Whitelist is not activated. Rootnode addresses:\n"
              "signBlockAddress, serverAddress and clientAddress from masterchain-config.json will be added")

        sign_address = globals()['signBlockAddress']
        server_address = globals()['serverAddress']
        client_address = globals()['clientAddress']
        sign_mask = 2
        read_mask = 1
        reference = "Root node"

        current_admin = globals()['admin']
        # unlock admin
        unlock_result = unlock_account(current_admin, "ADMIN")
        if not unlock_result:
            print("Unable to unlock account. Returning.")
            return user_dialog()

        status = register_full_transaction(sign_address, server_address, client_address,
                                           sign_mask, read_mask, reference, current_admin)
        print("Transaction execution status: {}".format(get_transaction_status(status, 300)['status']))

    user_dialog()


def change_mask_transaction(new_node_address, new_node_mask, current_admin):
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))

    admin_account_privileged = whitelist.functions.isAdmin(Web3.toChecksumAddress(current_admin)).call()
    if not admin_account_privileged:
        print("Account {} is not admin of whitelist. Returning.".format(current_admin))
        return user_dialog()

    block_node_data = whitelist.encodeABI(fn_name='setMask',
                                             args=[Web3.toChecksumAddress(new_node_address), new_node_mask])
    new_gas_price = w3.eth.gasPrice + 1000
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(current_admin))
    register_node = {'data': block_node_data, 'to': Web3.toChecksumAddress(globals()['whitelist']),
                     'from': Web3.toChecksumAddress(current_admin), 'gas': 4700000, 'gasPrice': new_gas_price,
                     'nonce': nonce}
    register_node_check = w3.eth.call(register_node)
    if not register_node_check:
        print("Test call returned False. Unable to block node {}".format(new_node_address))
        return user_dialog()

    # send transaction
    print("Sending transaction...")
    register_transact = w3.eth.sendTransaction(register_node)
    return register_transact


def register_transaction(new_node_address, new_node_mask, new_node_reference, current_admin):
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))

    admin_account_privileged = whitelist.functions.isAdmin(Web3.toChecksumAddress(current_admin)).call()
    if not admin_account_privileged:
        print("Account {} is not admin of whitelist. Returning.".format(current_admin))
        return user_dialog()

    register_node_data = whitelist.encodeABI(fn_name='register',
                                             args=[Web3.toChecksumAddress(new_node_address), new_node_mask, new_node_reference])
    new_gas_price = w3.eth.gasPrice + 1000
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(current_admin))
    register_node = {'data': register_node_data, 'to': Web3.toChecksumAddress(globals()['whitelist']),
                     'from': Web3.toChecksumAddress(current_admin), 'gas': 4700000, 'gasPrice': new_gas_price,
                     'nonce': nonce}
    register_node_check = w3.eth.call(register_node)
    if not register_node_check:
        print("Test call returned False. Unable to register node {}, {}".format(new_node_address, new_node_reference))
        return user_dialog()

    # send transaction
    print("Sending transaction...")
    register_transact = w3.eth.sendTransaction(register_node)
    return register_transact


def register_full_transaction(signer_address, server_address, client_address, signer_mask, reader_mask,
                              reference, current_admin):
    whitelist = w3.eth.contract(abi=globals()['json_abi'], address=Web3.toChecksumAddress(globals()['whitelist']))

    admin_account_privileged = whitelist.functions.isAdmin(Web3.toChecksumAddress(current_admin)).call()
    if not admin_account_privileged:
        print("Account {} is not admin of whitelist. Returning.".format(current_admin))
        return user_dialog()

    register_node_data = whitelist.encodeABI(fn_name='registerFull',
                                             args=[Web3.toChecksumAddress(signer_address),
                                                   Web3.toChecksumAddress(server_address),
                                                   Web3.toChecksumAddress(client_address),
                                                   signer_mask, reader_mask, reference])
    new_gas_price = w3.eth.gasPrice + 1000
    nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(current_admin))
    register_node = {'data': register_node_data, 'to': Web3.toChecksumAddress(globals()['whitelist']),
                     'from': Web3.toChecksumAddress(current_admin), 'gas': 4700000, 'gasPrice': new_gas_price,
                     'nonce': nonce}
    register_node_check = w3.eth.call(register_node)
    if not register_node_check:
        print("Test call returned False. Unable to register node:\n"
              "{}, {}, {} - {}".format(signer_address, server_address, client_address, reference))
        return user_dialog()

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


def main():
    welcome_message()
    read_config_files()
    init_vars()
    test_whitelist()
    check_status()
    user_dialog()


if __name__ == "__main__":
    main()

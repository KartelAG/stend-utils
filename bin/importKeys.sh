#!/bin/bash

echo "2" | /home/user/masterchain/meth --datadir /home/user/masterchain/masterchain_data import-node-keys -serverkey
echo "1" | /home/user/masterchain/meth --datadir /home/user/masterchain/masterchain_data import-node-keys -clientkey
echo "0" | /home/user/masterchain/meth --datadir /home/user/masterchain/masterchain_data import-node-keys -signblockkey

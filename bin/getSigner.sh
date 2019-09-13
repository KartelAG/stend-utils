#!/bin/bash
ser=`./meth --datadir ./masterchain_data attach -exec "admin.nodeInfo.server"` 
cli=`./meth --datadir ./masterchain_data attach -exec "admin.nodeInfo.client"` 
sig=`./meth --datadir ./masterchain_data attach -exec "admin.nodeInfo.address"`
hh=`hostname`
echo $hh $ser $cli $sig

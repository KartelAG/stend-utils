#!/bin/bash
ser=`./meth --datadir ./masterchain_data attach -exec "admin.nodeInfo.server"` 
cli=`./meth --datadir ./masterchain_data attach -exec "admin.nodeInfo.client"` 
hh=`hostname`
echo $hh $ser $cli

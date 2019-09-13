
#!/usr/bin/env bash

tmpTxJS=/tmp/tempTxs.js
echo "Please provide the password for the given key: "
read -s pass
echo "personal.unlockAccount(\"$2\", \"$pass\");" > "$tmpTxJS"

filename="$3"
mask=${filename:0:8}

while IFS='' read -r line || [[ -n "$line" ]]; do
	echo "var tnx = eth.signTransaction($line);" >> "$tmpTxJS"
	echo "console.log(\"Raw transaction: \", tnx[\"raw\"]);" >> "$tmpTxJS"
done <"$3"

./meth --datadir $1 --port 12123 --verbosity 0 --exec "loadScript(\"$tmpTxJS\")" console | grep "Raw transaction: " > "$mask"_signed_by_$2
rm "$tmpTxJS"


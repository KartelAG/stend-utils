#echo 'Введите логин пользователя УЦ:'
login='perm'

#echo "Введите пароль:"

password='7753099661'

#echo 'Выберите компонент:'
#echo '1) Узел Мастерчейн'
#echo '2) СПКС'
#echo '3) ДДС'

TYPE='1'

CONT_pref="\\\\.\\HDIMAGE\\"
CONT="Masterchain-"

certs=""
case $TYPE in
    1)
        certs+="Node-Server:tls-srv-node "
        certs+="Node-Client:tls-client-node "
        certs+="Node-Signer:sign-node-miner" ;;
	#certs+="Network-Admin:sign-network-admin-AFT "
	#certs+="Whitelist-Admin:sign-wl-admin-AFT" ;;
    2)
        certs+="Storage-Api-Stunnel-Server:tls-srv-cms-api "
        certs+="Storage-Api-Stunnel-Client:tls-client-cms-api" ;;
    3)
        certs+="DDS-Api-Stunnel-Server:tls-srv-API-IS "
        certs+="DDS-Api-Stunnel-Client:tls-client-API-IS" ;;
    4)
	certs+="DDS-Mch-Acc-1:sign-node-miner "
	certs+="DDS-Mch-Acc-2:sign-node-miner "
	certs+="DDS-Mch-Acc-3:sign-node-miner "
	certs+="DDS-Mch-Acc-4:sign-node-miner "
	certs+="DDS-Mch-Acc-5:sign-node-miner "
	certs+="DDS-Mch-Acc-6:sign-node-miner "
	certs+="DDS-Mch-Acc-7:sign-node-miner "
	certs+="DDS-Mch-Acc-8:sign-node-miner "
	certs+="DDS-Mch-Acc-9:sign-node-miner "
	certs+="DDS-Mch-Acc-10:sign-node-miner "
	certs+="DDS-Mch-Acc-11:sign-node-miner "
esac

CACRED="$login:$password"
CAURL="https://${CACRED}@testca2012.cryptopro.ru/ui/"

CATOKEN=`echo $CAURL | sed -E 's#[^:]*://([^:]*):.*#\1#'`
CAPASSWORD=`echo $CAURL | sed -E 's#[^:]*://[^:]*:([^@]*)@.*#\1#'`
CAURL=`echo $CAURL | sed -E 's#([^:]*://)[^@]*@(.*)$#\1\2#'`

get_line() {
    head -n $1 | tail -n 1
}

HN=`hostname`
RDN='E=KartelAG@cbr.ru,C=RU,CN='$HN
num=0
certs=( $certs )

for tps in ${certs[@]}
do
    RQID=`mktemp`
    RES=`mktemp`
    tp=( $(echo "$tps" | tr ":" " ") )
    echo "installing ${tp[0]} cert"
    curCont="${CONT_pref}${CONT}${tp[0]}"
    /opt/cprocsp/bin/amd64/cryptcp -creatcert -rdn $RDN \
         -provtype 80 -both -ku -hashalg '1.2.643.7.1.1.2.2' \
         -CPCA20 $CAURL -token $CATOKEN -tpassword $CAPASSWORD \
         -tmpl ${tp[1]} -FileID $RQID -cont "${curCont}" -pin "" 

    while : ; do
        /opt/cprocsp/bin/amd64/cryptcp -pendcert -FileID $RQID -cont "${curCont}" \
            -CPCA20 $CAURL -token $CATOKEN -tpassword $CAPASSWORD -pin ""  > $RES 2>&1
        cat $RES
        egrep -q "installed|установлен" $RES && break
        echo "Waiting for certificate request $(<$RQID) to be processed"
        sleep 1
    done
done

echo "Все сертификаты установлены"

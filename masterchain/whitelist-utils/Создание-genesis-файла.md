Genesis-файл необходим для создания начального блока сети (genesis-блока). Genesis-файл должен быть создан на первом узле сети. 

Создание genesis-файла:

1. Перейти в директорию `~/masterchain/whitelist-utils/common-setup`

2. Запустить скрипт `GenerateGenesis.py` для создания genesis-блока и набора ключей для управления Whitelist:
```
python3 GenerateGenesis.py
```
Скрипт последовательно предложит вам выбрать ключевые контейнеры для импорта соответствующих ключей ноды: 
serverkey, clientkey, signblockkey. Выбор контейнера с невалидным сертификатом приведет к заверщению работы скрипта.
Генезис блок в данном случае сформирован не будет.

**ВАЖНО:** при импорте сертификата проверяются oid'ы, x509 флаги, даты выпуска, chain policy, 
а так же наличие сохраненного пароля для привязанного контейнера.

Результатом успешной работы скрипта будут строки следующего вида: 
```
Authority address: %address0%. You MUST backup this key. This is the key to your private network.
Admin address: %address1%
RootNode sign block address: %address2%
RootNode server address: %address3%
RootNode client address: %address4%
Whitelist address: %address5%
```
Authority address – адрес администратора сети, управляет списком администраторов Whitelist,
Admin address – адрес первого администратора Whitelist, управляет списком и ролями узлов,
RootNode sign block address - адрес от ключа для подписи блоков первого узла сети,
RootNode server address- адрес от ключа сервера tls соединения первого узла сети,
RootNode client address- адрес от ключа клиента tls соединения первого узла сети,
Whitelist address – адрес смарт-контракта с Whitelist узлов.

Эти значения сохраняются в файле `~/masterchain/whitelist-utils/common-setup/out/masterchain-config.json`

Адрес Whitelist необходим для запуска первого и последующих узлов.

Далее [Запуск первого узла](https://github.com/fintechru/meth/blob/ft/tls_keys/whitelist-utils/Запуск-первого-узла.md)

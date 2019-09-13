pragma solidity ^0.4.16;

import "./MaskLib.sol";
import "./AuthorityOwnable.sol";

/**
 * The NodeWhitelist contract does this and that...
 */
contract NodeWhitelist is AuthorityOwnable {
    using MaskLib for MaskLib.Mask;


    address public rootNode;
    address public srvNode;
    address public clnNode;
    mapping (address => AddressRecord) registry;
    uint256 public expirationTime;
    bool public rootNodeAllowed = true;


    uint16 constant MASK_NOT_SET    = 0;
    uint16 constant FLAG_CAN_READ   = 1;
    uint16 constant FLAG_CAN_MINE   = 2;


    struct AddressRecord {
        MaskLib.Mask mask;
        string reference;
        uint256 creationTime;
        uint256 blockedAtBlock;
    }


    event NodeRegistered (address indexed node, uint16 mask, string reference);
    event NodeFlagsChanged (address indexed node, uint16 mask);
    event NodeReferenceChanged (address indexed node, string reference);
    event NodeBlocked (address indexed node);


    function NodeWhitelist (uint256 _expirationTime) public {
        require (_expirationTime > 0);
        expirationTime = _expirationTime;
    }

    /**
     * @dev     adds new node
     * @param   _address - public key of a new node, should be unique
     * @param   _mask - combination of flags for the new node, should be > 0
     * @param   _reference - mnemonic identifier of new node, cannot be changed later
     */
    function register (address _address, uint16 _mask, string _reference)
        public onlyAdmin onlyNotNode(_address)
        returns (bool)
    {
        require (_address != address(0));
        require (_mask != MASK_NOT_SET);
        registry[_address] = AddressRecord(
            MaskLib.Mask(_mask),
            _reference,
            block.timestamp,
            0
        );
        NodeRegistered(_address, _mask, _reference);
        return true;
    }

    /**
     * @dev     adds new node
     * @param   _addressSign - address from signer public key of a new node, should be unique
     * @param   _addressSrv - address from server public key of a new node, should be unique
     * @param   _addressCln - address from client public key of a new node, should be unique
     * @param   _maskMine - value of miner flag for the new node, should be >= 0
     * @param   _maskRead - value of reader flags for the new node, should be >= 0
     * @param   _reference - mnemonic identifier of new node, cannot be changed later
     */
    function registerFull (address _addressSign, address _addressSrv, address _addressCln, uint16 _maskMine, uint16 _maskRead, string _reference)
        public onlyAdmin
        returns (bool)
    {
        register(_addressSign, _maskMine, _reference);
        register(_addressSrv, _maskRead, _reference);
        register(_addressCln, _maskRead, _reference);
        rootNodeAllowed = false;
        return true;
    }


    /**
     * @dev     raises _flag for an existent node, will throw if any of the flags in _flag already present
     * @param   _address - node identifier
     * @param   _flag - a flag or a combination of flags
     */
    function setFlag (address _address, uint16 _flag)
        public onlyAdmin onlyNeitherBlockedNorExpiredNode(_address)
        returns (bool)
    {
        registry[_address].mask.setFlag(_flag);
        NodeFlagsChanged(_address, registry[_address].mask.flags);
        return true;
    }


    /**
     * @dev     removes _flag for an existent node, will throw if any of the flags in _flag already present
     * @param   _address - node identifier
     * @param   _flag - a flag or a combination of flags
     */
    function removeFlag (address _address, uint16 _flag)
        public onlyAdmin onlyNeitherBlockedNorExpiredNode(_address)
        returns (bool)
    {
        registry[_address].mask.removeFlag(_flag);
        NodeFlagsChanged(_address, registry[_address].mask.flags);
        return true;
    }


    /**
     * @dev     overrides mask for the node
     * @param   _address - node identifier
     * @param   _mask - sum of flags
     */
    function setMask (address _address, uint16 _mask)
        public onlyAdmin onlyNeitherBlockedNorExpiredNode(_address)
        returns (bool)
    {
        registry[_address].mask = MaskLib.Mask(_mask);
        NodeFlagsChanged(_address, _mask);
        return true;
    }


    /**
     * @dev     marks node as blocked, this action cannot be undone
     * @param   _address - node identifier
     */
    function blockNode (address _address)
        public onlyAdmin onlyNeitherBlockedNorExpiredNode(_address)
        returns (bool)
    {
        registry[_address].blockedAtBlock = block.number;
        NodeBlocked(_address);
        return true;
    }


    // Reading methods

    /**
     * @dev             returns mask for not blocked node, throws if the node is blocked
     * @param _address  - node identifier
     */
    function getMask (address _address) public view
        onlyNeitherBlockedNorExpiredNode(_address) returns (uint16)
    {
        if (rootNodeAllowed) {
            if (_address == rootNode) {
                return FLAG_CAN_MINE;
            } else if (_address == srvNode || _address == clnNode) {
                return FLAG_CAN_READ;
            }
        }
        return registry[_address].mask.flags;
    }


    /**
     * @dev             returns true if flag is set for the node, throws if the node is blocked
     * @param _address  - node identifier
     */
    function isFlagSet (address _address, uint16 _flag) public view
        onlyNeitherBlockedNorExpiredNode(_address) returns (bool)
    {
        return registry[_address].mask.isFlagSet(_flag);
    }


    /**
     * @dev             returns true if the node is blocked
     * @param _address  - node identifier
     */
    function isBlocked (address _address) public view
        onlyNode(_address) returns (bool)
    {
        return registry[_address].blockedAtBlock != 0;
    }

    /**
     * @dev             returns true if the node is expired
     * @param _address  - node identifier
     */
    function isExpired (address _address) public view
        onlyNode(_address) returns (bool)
    {
        return block.timestamp - registry[_address].creationTime > expirationTime;
    }


    /**
     * @dev             returns node reference
     * @param _address  - node identifier
     */
    function getReference (address _address) public view
        onlyNode(_address) returns (string)
    {
        return registry[_address].reference;
    }

    /**
     * @dev             returns node creation time
     * @param _address  - node identifier
     */
    function getCreationTime (address _address) public view
        onlyNode(_address) returns (uint256)
    {
        return registry[_address].creationTime;
    }

    /**
     * @dev             returns true if the node is exsts
     * @param _address  - node identifier
     */
    function isNode (address _address) public view returns (bool)
    {
        return registry[_address].creationTime > 0;
    }


    // Modifiers

    modifier onlyNotNode (address _nodeAddress) {
        require (registry[_nodeAddress].creationTime == 0);
        _;
    }

    modifier onlyNode (address _nodeAddress) {
        require (registry[_nodeAddress].creationTime != 0);
        _;
    }

    modifier onlyNeitherBlockedNorExpiredNode (address _nodeAddress) {
        if (rootNodeAllowed) {
            require (_nodeAddress == rootNode || _nodeAddress == srvNode || _nodeAddress == clnNode);
        } else {
            require (registry[_nodeAddress].creationTime != 0);
            require (registry[_nodeAddress].blockedAtBlock == 0);
            require (block.timestamp - registry[_nodeAddress].creationTime < expirationTime);
        }
        _;
    }

}

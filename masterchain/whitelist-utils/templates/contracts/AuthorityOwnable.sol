pragma solidity ^0.4.16;

/**
 * The AuthorityOwnable contract does this and that...
 */
contract AuthorityOwnable   {

    struct AdminRecord {
        uint256 creationTime;
        string reference;
    }

    event AuthorityChanged(address newAuthority);
    event AdminRemoved(address indexed oldAdmin, string reference);
    event AdminAdded(address indexed newAdmin, string reference);

    address public authority;
    mapping (address => AdminRecord) public admins;


    function AuthorityOwnable () public {
        authority = msg.sender;
        AuthorityChanged(authority);
    }

    /**
     * @dev     immediately changes authority of the contracts
     * @param   _newAuthority new authority
     */
    function transferAuthorityRole (address _newAuthority)
        onlyAuthority
        onlySuitableAddress(_newAuthority)
        public returns (bool)
    {
        require (_newAuthority != address(0));
        authority = _newAuthority;
        AuthorityChanged(authority);
        return true;
    }


    /**
     * @dev
     * @param
     */
    function addAdmin (address _newAdmin, string _reference)
        onlyAuthority
        onlySuitableAddress(_newAdmin)
        public returns (bool)
    {
        admins[_newAdmin] = AdminRecord( block.timestamp, _reference );
        AdminAdded(_newAdmin, _reference);
        return true;
    }


    /**
     * @dev
     * @param
     */
    function removeAdmin (address _adminForRemoval)
        onlyAuthority public returns (bool)
    {
        require (admins[_adminForRemoval].creationTime != 0);
        string oldReference = admins[msg.sender].reference;
        delete admins[_adminForRemoval];
        AdminRemoved( _adminForRemoval, oldReference);
        return true;
    }


    /**
     * @dev
     * @param
     */
    function transferAdminRole (address _newAdmin, string _reference)
        onlyAdmin
        onlySuitableAddress(_newAdmin)
        public returns (bool)
    {
        require (_newAdmin != msg.sender);
        string oldReference = admins[msg.sender].reference;
        delete admins[msg.sender];
        admins[_newAdmin] = AdminRecord( block.timestamp, _reference );
        AdminRemoved(msg.sender, oldReference);
        AdminAdded(_newAdmin, _reference);
        return true;
    }


    /**
     * @dev
     * @param
     */
    function isAdmin (address _candidate)
        public view returns (bool)
    {
        return admins[_candidate].creationTime > 0;
    }

    function getAdminReference (address _admin)
        public view returns (string)
    {
        return admins[_admin].reference;
    }

    modifier onlyAuthority () {
        require (msg.sender == authority);
        _;
    }

    modifier onlySuitableAddress (address _a) {
        require (admins[_a].creationTime == 0);
        require (_a != authority);
        require (_a != address(0));
        _;
    }

    modifier onlyAdmin () {
        require (admins[msg.sender].creationTime != 0);
        _;
    }

}

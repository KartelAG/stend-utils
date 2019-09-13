pragma solidity ^0.4.16;

/**
 * The Mask library does this and that...
 */
library MaskLib {
    struct Mask { uint16 flags; }

    function setFlag (Mask storage _self, uint16 _flag) public {
        require (_flag != 0);
        require (_self.flags & _flag == 0);
        _self.flags += _flag;
    }

    function removeFlag (Mask storage _self, uint16 _flag) public {
        require (_flag != 0);
        require (_self.flags & _flag == _flag);
        _self.flags -= _flag;
    }

    function isFlagSet (Mask storage _self, uint16 _flag) public view returns (bool) {
        require (_flag != 0);
        return _self.flags & _flag == _flag;
    }

    function isMaskNotSet (Mask storage _self) public view returns (bool) {
        return _self.flags == 0;
    }

}
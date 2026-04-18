/* SPDX-License-Identifier: MIT */
pragma solidity ^0.8.28;

import "../contracts/EthicBitAnchor.sol";

contract EthicBitAnchorTest {
    EthicBitAnchor public anchor;

    function setUp() public {
        anchor = new EthicBitAnchor();
    }

    function testAnchorState() public {
        bytes32 hash = keccak256("test-state");
        anchor.anchorState(hash, 0);
        require(anchor.currentVersion() == 1, "Version should be 1");
        require(anchor.verifyState(hash), "Hash should verify");
    }
}

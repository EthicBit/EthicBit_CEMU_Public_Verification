// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../contracts/ClosureAnchor.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
    function expectRevert(bytes calldata) external;
}

contract ClosureAnchorTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    ClosureAnchor internal anchor;
    address internal guardian = address(0xBEEF);
    address internal outsider = address(0xCAFE);

    bytes32 internal constant ROOT_ONE = keccak256("root-one");
    bytes32 internal constant ROOT_TWO = keccak256("root-two");
    bytes32 internal constant ANCHOR_TYPE_HASH = keccak256("case_003");
    bytes32 internal constant ARTIFACT_TYPE_HASH = keccak256("closure_state");
    bytes32 internal constant VERSION_HASH = keccak256("v1.0.0");
    bytes32 internal constant MANIFEST_HASH = keccak256("ar://manifest");
    bytes32 internal constant RECEIPT_HASH = keccak256("ar://receipt");

    function setUp() public {
        anchor = new ClosureAnchor(address(0));
    }

    function _anchor(bytes32 rootHash, uint256 nonce) internal {
        anchor.anchorClosure(
            rootHash,
            ANCHOR_TYPE_HASH,
            ARTIFACT_TYPE_HASH,
            VERSION_HASH,
            MANIFEST_HASH,
            RECEIPT_HASH,
            block.chainid,
            nonce
        );
    }

    function testAnchorClosureStoresRecordAndAdvancesNonce() public {
        _anchor(ROOT_ONE, 1);

        require(anchor.isAnchored(ROOT_ONE), "root should be anchored");
        require(anchor.nextNonce() == 2, "nonce should advance");
        require(anchor.totalAnchors() == 1, "total anchors should increase");
        require(anchor.rootHashAt(0) == ROOT_ONE, "root hash index mismatch");

        ClosureAnchor.AnchorRecord memory record = anchor.getAnchor(ROOT_ONE);
        require(record.rootHash == ROOT_ONE, "record root mismatch");
        require(record.anchorer == address(this), "anchorer mismatch");
        require(record.anchorTypeHash == ANCHOR_TYPE_HASH, "anchor type mismatch");
        require(record.artifactTypeHash == ARTIFACT_TYPE_HASH, "artifact type mismatch");
        require(record.versionHash == VERSION_HASH, "version mismatch");
        require(record.manifestURIHash == MANIFEST_HASH, "manifest mismatch");
        require(record.receiptURIHash == RECEIPT_HASH, "receipt mismatch");
        require(record.nonce == 1, "record nonce mismatch");
        require(record.chainId == block.chainid, "chain id mismatch");
        require(record.exists, "record should exist");
    }

    function testAnchorClosureRejectsDuplicateRoot() public {
        _anchor(ROOT_ONE, 1);

        vm.expectRevert(abi.encodeWithSelector(ClosureAnchor.AlreadyAnchored.selector, ROOT_ONE));
        _anchor(ROOT_ONE, 2);
    }

    function testAnchorClosureRejectsInvalidNonce() public {
        vm.expectRevert(abi.encodeWithSelector(ClosureAnchor.InvalidNonce.selector, 1, 2));
        _anchor(ROOT_ONE, 2);
    }

    function testOnlyAuthorizedCanAnchor() public {
        vm.prank(outsider);
        vm.expectRevert(ClosureAnchor.Unauthorized.selector);
        _anchor(ROOT_ONE, 1);
    }

    function testGuardianCanAnchor() public {
        anchor.setGuardian(guardian, true);

        vm.prank(guardian);
        anchor.anchorClosure(
            ROOT_ONE,
            ANCHOR_TYPE_HASH,
            ARTIFACT_TYPE_HASH,
            VERSION_HASH,
            MANIFEST_HASH,
            RECEIPT_HASH,
            block.chainid,
            1
        );

        require(anchor.isAnchored(ROOT_ONE), "guardian should be authorized");
    }

    function testPausedContractBlocksAnchoring() public {
        anchor.setPaused(true);

        vm.expectRevert(ClosureAnchor.ContractPaused.selector);
        _anchor(ROOT_TWO, 1);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../contracts/CEMUEthicalOracle.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
    function expectRevert(bytes calldata) external;
    function warp(uint256) external;
}

contract CEMUEthicalOracleTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    CEMUEthicalOracle internal oracle;
    address internal outsider = address(0xCAFE);
    address internal newAdmin = address(0xBEEF);

    bytes32 internal constant INITIAL_ROOT = keccak256("initial-root");
    bytes32 internal constant INITIAL_VERSION_TAG = keccak256("v1");
    bytes32 internal constant NEXT_ROOT = keccak256("next-root");
    bytes32 internal constant NEXT_VERSION_TAG = keccak256("v2");

    function setUp() public {
        oracle = new CEMUEthicalOracle(INITIAL_ROOT, INITIAL_VERSION_TAG);
    }

    function testInitialStateAndRoles() public view {
        require(oracle.admin() == address(this), "admin must be deployer");

        bytes32 adminRole = oracle.DEFAULT_ADMIN_ROLE();
        bytes32 oracleRole = oracle.CEMU_ORACLE_ROLE();

        require(oracle.hasRole(adminRole, address(this)), "deployer must have admin role");
        require(oracle.hasRole(oracleRole, address(this)), "deployer must have oracle role");

        (bytes32 rootHash, uint64 lastUpdateTimestamp, uint64 updateCount) = oracle.cemuState();
        require(rootHash == INITIAL_ROOT, "initial root mismatch");
        require(updateCount == 1, "initial update count mismatch");
        require(lastUpdateTimestamp > 0, "timestamp should be initialized");
    }

    function testOracleRoleCanUpdateRootHash() public {
        oracle.updateCemuRootHash(NEXT_ROOT, NEXT_VERSION_TAG);

        (bytes32 rootHash, , uint64 updateCount) = oracle.cemuState();
        require(rootHash == NEXT_ROOT, "new root should be stored");
        require(updateCount == 2, "update count should increment");
        require(oracle.verifyCurrentClosure(NEXT_ROOT), "current closure should verify");
    }

    function testNonOracleCannotUpdateRootHash() public {
        bytes32 oracleRole = oracle.CEMU_ORACLE_ROLE();

        vm.prank(outsider);
        vm.expectRevert(abi.encodeWithSelector(CEMUEthicalOracle.MissingRole.selector, oracleRole, outsider));
        oracle.updateCemuRootHash(NEXT_ROOT, NEXT_VERSION_TAG);
    }

    function testUpdateRejectsUnchangedRootHash() public {
        vm.expectRevert(CEMUEthicalOracle.HashUnchanged.selector);
        oracle.updateCemuRootHash(INITIAL_ROOT, NEXT_VERSION_TAG);
    }

    function testAdminTransferFlowMovesRoles() public {
        bytes32 adminRole = oracle.DEFAULT_ADMIN_ROLE();
        bytes32 oracleRole = oracle.CEMU_ORACLE_ROLE();

        oracle.startAdminTransfer(newAdmin);
        require(oracle.pendingAdmin() == newAdmin, "pending admin mismatch");

        vm.prank(newAdmin);
        oracle.acceptAdminTransfer();

        require(oracle.admin() == newAdmin, "admin should transfer");
        require(oracle.pendingAdmin() == address(0), "pending admin should reset");
        require(oracle.hasRole(adminRole, newAdmin), "new admin role missing");
        require(oracle.hasRole(oracleRole, newAdmin), "new oracle role missing");
        require(!oracle.hasRole(adminRole, address(this)), "old admin role should be revoked");
        require(!oracle.hasRole(oracleRole, address(this)), "old oracle role should be revoked");
    }

    function testEthicalComplianceExpiresAfterThirtyDays() public {
        require(oracle.isEthicallyCompliant(), "fresh state should be compliant");

        vm.warp(block.timestamp + 31 days);
        require(!oracle.isEthicallyCompliant(), "state should expire after 30 days");
    }
}

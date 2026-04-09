// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract CEMUEthicalOracle {
    bytes32 public constant DEFAULT_ADMIN_ROLE = keccak256("DEFAULT_ADMIN_ROLE");
    bytes32 public constant CEMU_ORACLE_ROLE = keccak256("CEMU_ORACLE_ROLE");

    string public constant CEMU_VERSION = "EthicBit_CEMU_v3.7.0";
    string public constant CONSTITUTION_ID = "EthicFi_Genesis_Vault_v1";

    address public admin;
    address public pendingAdmin;

    mapping(bytes32 => mapping(address => bool)) private _hasRole;

    bytes32 public currentCemuRootHash;
    uint64 public lastUpdateTimestamp;
    uint64 public updateCount;

    error MissingRole(bytes32 role, address account);
    error InvalidAddress();
    error InvalidHash();
    error HashUnchanged();
    error InvalidVersionTag();
    error PendingAdminNotSet();
    error NotPendingAdmin();
    error CannotRevokeCurrentAdmin();

    event CemuRootHashUpdated(
        bytes32 indexed newRootHash,
        uint64 timestamp,
        uint64 indexed nonce,
        bytes32 indexed versionTag,
        address operator
    );
    event RoleGranted(bytes32 indexed role, address indexed account, address indexed by);
    event RoleRevoked(bytes32 indexed role, address indexed account, address indexed by);
    event AdminTransferStarted(address indexed oldAdmin, address indexed pendingAdmin);
    event AdminTransferAccepted(address indexed oldAdmin, address indexed newAdmin);
    event AdminTransferCancelled(address indexed oldAdmin);
    event EthicalComplianceChecked(address indexed caller, bool compliant);

    modifier onlyRole(bytes32 role) {
        if (!_hasRole[role][msg.sender]) revert MissingRole(role, msg.sender);
        _;
    }

    constructor(bytes32 initialRootHash, bytes32 initialVersionTag) {
        if (initialRootHash == bytes32(0)) revert InvalidHash();
        if (initialVersionTag == bytes32(0)) revert InvalidVersionTag();

        admin = msg.sender;
        _hasRole[DEFAULT_ADMIN_ROLE][msg.sender] = true;
        _hasRole[CEMU_ORACLE_ROLE][msg.sender] = true;

        currentCemuRootHash = initialRootHash;
        lastUpdateTimestamp = uint64(block.timestamp);
        updateCount = 1;

        emit RoleGranted(DEFAULT_ADMIN_ROLE, msg.sender, msg.sender);
        emit RoleGranted(CEMU_ORACLE_ROLE, msg.sender, msg.sender);
        emit CemuRootHashUpdated(
            initialRootHash,
            lastUpdateTimestamp,
            updateCount,
            initialVersionTag,
            msg.sender
        );
    }

    function hasRole(bytes32 role, address account) external view returns (bool) {
        return _hasRole[role][account];
    }

    function grantRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (account == address(0)) revert InvalidAddress();
        if (!_hasRole[role][account]) {
            _hasRole[role][account] = true;
            emit RoleGranted(role, account, msg.sender);
        }
    }

    function revokeRole(bytes32 role, address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (account == address(0)) revert InvalidAddress();
        if (role == DEFAULT_ADMIN_ROLE && account == admin) revert CannotRevokeCurrentAdmin();

        if (_hasRole[role][account]) {
            _hasRole[role][account] = false;
            emit RoleRevoked(role, account, msg.sender);
        }
    }

    function updateCemuRootHash(bytes32 newRootHash, bytes32 versionTag)
        external
        onlyRole(CEMU_ORACLE_ROLE)
    {
        if (newRootHash == bytes32(0)) revert InvalidHash();
        if (versionTag == bytes32(0)) revert InvalidVersionTag();
        if (newRootHash == currentCemuRootHash) revert HashUnchanged();

        currentCemuRootHash = newRootHash;
        lastUpdateTimestamp = uint64(block.timestamp);
        unchecked {
            updateCount += 1;
        }

        emit CemuRootHashUpdated(
            newRootHash,
            lastUpdateTimestamp,
            updateCount,
            versionTag,
            msg.sender
        );
    }

    function isEthicallyCompliant() public view returns (bool) {
        return
            currentCemuRootHash != bytes32(0) &&
            block.timestamp - uint256(lastUpdateTimestamp) < 30 days;
    }

    function verifyCurrentClosure(bytes32 providedRootHash) external view returns (bool) {
        return providedRootHash == currentCemuRootHash;
    }

    function checkAndEmitEthicalCompliance() external returns (bool) {
        bool compliant = isEthicallyCompliant();
        emit EthicalComplianceChecked(msg.sender, compliant);
        return compliant;
    }

    function startAdminTransfer(address newAdmin) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newAdmin == address(0)) revert InvalidAddress();
        pendingAdmin = newAdmin;
        emit AdminTransferStarted(admin, newAdmin);
    }

    function acceptAdminTransfer() external {
        if (pendingAdmin == address(0)) revert PendingAdminNotSet();
        if (msg.sender != pendingAdmin) revert NotPendingAdmin();

        address oldAdmin = admin;
        address newAdmin = pendingAdmin;

        pendingAdmin = address(0);
        admin = newAdmin;

        _hasRole[DEFAULT_ADMIN_ROLE][oldAdmin] = false;
        _hasRole[CEMU_ORACLE_ROLE][oldAdmin] = false;

        _hasRole[DEFAULT_ADMIN_ROLE][newAdmin] = true;
        _hasRole[CEMU_ORACLE_ROLE][newAdmin] = true;

        emit RoleRevoked(DEFAULT_ADMIN_ROLE, oldAdmin, newAdmin);
        emit RoleRevoked(CEMU_ORACLE_ROLE, oldAdmin, newAdmin);
        emit RoleGranted(DEFAULT_ADMIN_ROLE, newAdmin, newAdmin);
        emit RoleGranted(CEMU_ORACLE_ROLE, newAdmin, newAdmin);
        emit AdminTransferAccepted(oldAdmin, newAdmin);
    }

    function cancelAdminTransfer() external onlyRole(DEFAULT_ADMIN_ROLE) {
        pendingAdmin = address(0);
        emit AdminTransferCancelled(admin);
    }
}

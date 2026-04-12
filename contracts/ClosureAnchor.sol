// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ClosureAnchor {
    error Unauthorized();
    error ContractPaused();
    error EmptyRootHash();
    error AlreadyAnchored(bytes32 rootHash);
    error InvalidChainHint();
    error EmptyAnchorType();
    error EmptyArtifactType();
    error EmptyVersion();
    error InvalidNonce(uint256 expected, uint256 provided);
    error MaxAnchorsReached();   // ← nueva protección contra storage growth

    event OwnerTransferred(address indexed previousOwner, address indexed newOwner);
    event GuardianUpdated(address indexed guardian, bool allowed);
    event PauseStateChanged(bool paused);
    event ClosureAnchored(
        bytes32 indexed rootHash,
        address indexed anchorer,
        bytes32 anchorTypeHash,
        bytes32 artifactTypeHash,
        bytes32 versionHash,
        bytes32 manifestURIHash,
        bytes32 receiptURIHash,
        uint256 nonce,
        uint256 timestamp,
        uint256 chainId,
        bytes32 blockHash
    );

    struct AnchorRecord {
        bytes32 rootHash;
        address anchorer;
        bytes32 anchorTypeHash;     // keccak256(anchorType)
        bytes32 artifactTypeHash;
        bytes32 versionHash;
        bytes32 manifestURIHash;    // ideal para Arweave/AO CID
        bytes32 receiptURIHash;
        uint256 nonce;
        uint256 timestamp;
        uint256 chainId;
        bytes32 blockHash;
        bool exists;
    }

    address public owner;
    bool public paused;
    uint256 public nextNonce = 1;
    uint256 public constant MAX_ANCHORS = 10_000;   // ← límite de gas/storage

    mapping(address => bool) public guardians;
    mapping(bytes32 => AnchorRecord) private _records;
    bytes32[] private _rootHashes;   // puedes eliminarlo si no lo necesitas

    modifier onlyAuthorized() {
        if (msg.sender != owner && !guardians[msg.sender]) revert Unauthorized();
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    constructor(address initialOwner) {
        owner = initialOwner == address(0) ? msg.sender : initialOwner;
        emit OwnerTransferred(address(0), owner);
    }

    function transferOwnership(address newOwner) external {
        if (msg.sender != owner) revert Unauthorized();
        require(newOwner != address(0), "new owner is zero");
        address previous = owner;
        owner = newOwner;
        emit OwnerTransferred(previous, newOwner);
    }

    function setGuardian(address guardian, bool allowed) external {
        if (msg.sender != owner) revert Unauthorized();
        guardians[guardian] = allowed;
        emit GuardianUpdated(guardian, allowed);
    }

    function setPaused(bool isPaused) external {
        if (msg.sender != owner) revert Unauthorized();
        paused = isPaused;
        emit PauseStateChanged(isPaused);
    }

    function anchorClosure(
        bytes32 rootHash,
        bytes32 anchorTypeHash,
        bytes32 artifactTypeHash,
        bytes32 versionHash,
        bytes32 manifestURIHash,
        bytes32 receiptURIHash,
        uint256 expectedChainId,
        uint256 nonce
    ) external onlyAuthorized whenNotPaused {
        if (rootHash == bytes32(0)) revert EmptyRootHash();
        if (_records[rootHash].exists) revert AlreadyAnchored(rootHash);
        if (expectedChainId != 0 && expectedChainId != block.chainid) revert InvalidChainHint();
        if (anchorTypeHash == bytes32(0)) revert EmptyAnchorType();
        if (artifactTypeHash == bytes32(0)) revert EmptyArtifactType();
        if (versionHash == bytes32(0)) revert EmptyVersion();
        if (nonce != nextNonce) revert InvalidNonce(nextNonce, nonce);
        if (_rootHashes.length >= MAX_ANCHORS) revert MaxAnchorsReached();

        bytes32 prevBlockHash = blockhash(block.number - 1);
        _writeAnchorRecord(
            rootHash,
            msg.sender,
            anchorTypeHash,
            artifactTypeHash,
            versionHash,
            manifestURIHash,
            receiptURIHash,
            nonce,
            prevBlockHash
        );

        _rootHashes.push(rootHash);
        nextNonce += 1;

        _emitClosureAnchored(rootHash, msg.sender, nonce, prevBlockHash);
    }

    function _writeAnchorRecord(
        bytes32 rootHash,
        address anchorer,
        bytes32 anchorTypeHash,
        bytes32 artifactTypeHash,
        bytes32 versionHash,
        bytes32 manifestURIHash,
        bytes32 receiptURIHash,
        uint256 nonce,
        bytes32 prevBlockHash
    ) private {
        AnchorRecord storage record = _records[rootHash];
        record.rootHash = rootHash;
        record.anchorer = anchorer;
        record.anchorTypeHash = anchorTypeHash;
        record.artifactTypeHash = artifactTypeHash;
        record.versionHash = versionHash;
        record.manifestURIHash = manifestURIHash;
        record.receiptURIHash = receiptURIHash;
        record.nonce = nonce;
        record.timestamp = block.timestamp;
        record.chainId = block.chainid;
        record.blockHash = prevBlockHash;
        record.exists = true;
    }

    function _emitClosureAnchored(
        bytes32 rootHash,
        address anchorer,
        uint256 nonce,
        bytes32 prevBlockHash
    ) private {
        AnchorRecord storage record = _records[rootHash];
        emit ClosureAnchored(
            rootHash,
            anchorer,
            record.anchorTypeHash,
            record.artifactTypeHash,
            record.versionHash,
            record.manifestURIHash,
            record.receiptURIHash,
            nonce,
            record.timestamp,
            record.chainId,
            prevBlockHash
        );
    }

    function isAnchored(bytes32 rootHash) external view returns (bool) {
        return _records[rootHash].exists;
    }

    function getAnchor(bytes32 rootHash) external view returns (AnchorRecord memory) {
        return _records[rootHash];
    }

    function totalAnchors() external view returns (uint256) {
        return _rootHashes.length;
    }

    function rootHashAt(uint256 index) external view returns (bytes32) {
        return _rootHashes[index];
    }
}

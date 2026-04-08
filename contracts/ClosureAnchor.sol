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

    event OwnerTransferred(address indexed previousOwner, address indexed newOwner);
    event GuardianUpdated(address indexed guardian, bool allowed);
    event PauseStateChanged(bool paused);
    event ClosureAnchored(
        bytes32 indexed rootHash,
        address indexed anchorer,
        string anchorType,
        string artifactType,
        string version,
        string manifestURI,
        string receiptURI,
        uint256 nonce,
        uint256 timestamp,
        uint256 chainId,
        bytes32 blockHash
    );

    struct AnchorRecord {
        bytes32 rootHash;
        address anchorer;
        string anchorType;
        string artifactType;
        string version;
        string manifestURI;
        string receiptURI;
        uint256 nonce;
        uint256 timestamp;
        uint256 chainId;
        bytes32 blockHash;
        bool exists;
    }

    address public owner;
    bool public paused;
    uint256 public nextNonce = 1;

    mapping(address => bool) public guardians;
    mapping(bytes32 => AnchorRecord) private _records;
    bytes32[] private _rootHashes;

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
        string calldata anchorType,
        string calldata artifactType,
        string calldata version,
        string calldata manifestURI,
        string calldata receiptURI,
        uint256 expectedChainId,
        uint256 nonce
    ) external onlyAuthorized whenNotPaused {
        if (rootHash == bytes32(0)) revert EmptyRootHash();
        if (_records[rootHash].exists) revert AlreadyAnchored(rootHash);
        if (expectedChainId != 0 && expectedChainId != block.chainid) revert InvalidChainHint();
        if (bytes(anchorType).length == 0) revert EmptyAnchorType();
        if (bytes(artifactType).length == 0) revert EmptyArtifactType();
        if (bytes(version).length == 0) revert EmptyVersion();
        if (nonce != nextNonce) revert InvalidNonce(nextNonce, nonce);

        bytes32 prevBlockHash = blockhash(block.number - 1);

        AnchorRecord memory record = AnchorRecord({
            rootHash: rootHash,
            anchorer: msg.sender,
            anchorType: anchorType,
            artifactType: artifactType,
            version: version,
            manifestURI: manifestURI,
            receiptURI: receiptURI,
            nonce: nonce,
            timestamp: block.timestamp,
            chainId: block.chainid,
            blockHash: prevBlockHash,
            exists: true
        });

        _records[rootHash] = record;
        _rootHashes.push(rootHash);
        nextNonce += 1;

        emit ClosureAnchored(
            rootHash,
            msg.sender,
            anchorType,
            artifactType,
            version,
            manifestURI,
            receiptURI,
            nonce,
            block.timestamp,
            block.chainid,
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

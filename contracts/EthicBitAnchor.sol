/* SPDX-License-Identifier: MIT */
pragma solidity ^0.8.28;

contract EthicBitAnchor {
    string public constant VERSION = "1.0.0-anchor-hardening-simplified";

    struct StateAnchor {
        bytes32 stateHash;
        uint256 timestamp;
        uint256 version;
        uint256 failClosedCount;
        bytes32 previousAnchor;
    }

    mapping(uint256 => StateAnchor) public anchors;
    uint256 public currentVersion;
    address public owner;

    event CanonicalLinkEstablished(
        uint256 indexed version,
        bytes32 stateHash,
        bytes32 previousAnchor,
        uint256 timestamp
    );

    event FailClosedAnchored(uint256 indexed version, bytes32 stateHash);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function anchorState(bytes32 stateHash, uint256 failClosedCount) external onlyOwner {
        bytes32 previous = currentVersion > 0 ? anchors[currentVersion].stateHash : bytes32(0);

        currentVersion++;
        anchors[currentVersion] = StateAnchor({
            stateHash: stateHash,
            timestamp: block.timestamp,
            version: currentVersion,
            failClosedCount: failClosedCount,
            previousAnchor: previous
        });

        if (failClosedCount > 0) {
            emit FailClosedAnchored(currentVersion, stateHash);
        }
        emit CanonicalLinkEstablished(currentVersion, stateHash, previous, block.timestamp);
    }

    function verifyState(bytes32 stateHash) external view returns (bool) {
        return anchors[currentVersion].stateHash == stateHash;
    }

    function getCurrentAnchor() external view returns (StateAnchor memory) {
        return anchors[currentVersion];
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";

contract Lottery is Ownable, VRFConsumerBase {
    using SafeMath for uint256;
    address payable[] public entrants;
    address payable public recentWinner;
    uint256 public randomness;
    uint256 public usdEntryFee; //converted to wei
    uint256 public fee; //in LINK
    bytes32 public keyhash;
    /*
     *Interfaces
     */
    AggregatorV3Interface internal ethUsdPriceFeed;

    event RequestedRandomness(bytes32 requestId);

    enum LOTTERY_STATE {
        OPEN,
        CALCULATING_WINNER,
        CLOSED
    }
    LOTTERY_STATE public lottery_state;

    constructor(
        address _priceFeed,
        address _vrfCoordinator,
        address _linkToken,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _linkToken) {
        usdEntryFee = 50 * 10**18;
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeed);
        fee = _fee;
        keyhash = _keyhash;
        lottery_state = LOTTERY_STATE.CLOSED;
    }

    function enter() public payable {
        //value needs to be at least entrance fee
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH");
        entrants.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; //price returned is 8 decimals, we want it to be 18 hence 10**10
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice; //by adding another 18 decimals to usdEntryFee we keep it as 18 decimals for returning
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Lottery already started"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.OPEN,
            "Lottery has not started yet"
        );
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Not ready for randomness"
        );
        require(_randomness > 0, "random-not-found");
        uint256 indexOfWinner = _randomness % entrants.length;
        recentWinner = entrants[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        //Reset
        entrants = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}

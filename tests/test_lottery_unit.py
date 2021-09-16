from brownie.network import account
from toolz.itertoolz import get
from scripts.utils import (
    LOCAL_BLOCKCHAIN_ENVINROMENTS,
    fund_with_link,
    get_account,
    get_contract,
)
from brownie import network, config, exceptions
from web3 import Web3
from scripts.deploy import deploy_lottery
import pytest

# $50 entry / $3615 eth price
# conversion = 0.014 eth (msg.value should equal around = 14000000000000000 wei)
# price feed returned (value * 10**10) to make it have 18 "decimals"  = 3615149872380000000000
# 50000000000000000000
# 50000000000000000000000000000000000000/3615149872380000000000
def test_get_entrance_fee():
    network_check()

    lottery = deploy_lottery()
    # Eth price = $2000
    # Entrance Fee = $50
    # 0.025 ETH entry
    expected_entry_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    assert entrance_fee == expected_entry_fee


def test_enter_only_on_started():
    network_check()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_enter_lottery():
    network_check()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    assert lottery.entrants(0) == account


def test_end_lottery():
    network_check()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)
    lottery.endLottery()
    assert lottery.lottery_state() == 1


def test_pick_winner():
    network_check()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)

    accountStartingBalance = account.balance()
    lotteryBalanceBeforeEnd = lottery.balance()

    tx = lottery.endLottery({"from": account})
    requestId = tx.events["RequestedRandomness"]["requestId"]
    get_contract("vrf_coordinator").callBackWithRandomness(
        requestId, 777, lottery.address
    )
    # 777/3 = 0 - index 0 wins - our account
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == accountStartingBalance + lotteryBalanceBeforeEnd


def network_check():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVINROMENTS:
        pytest.skip()

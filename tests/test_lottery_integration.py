from scripts.deploy import deploy_lottery
from brownie import network
from scripts.utils import (
    LOCAL_BLOCKCHAIN_ENVINROMENTS,
    fund_with_link,
    get_account,
)
import pytest
import time


def test_pick_winner_integration():
    network_check()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    time.sleep(30)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


def network_check():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVINROMENTS:
        pytest.skip()

import time
from brownie import accounts, network, Lottery, MockV3Aggregator
from brownie.network import account
from scripts.utils import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVINROMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from brownie import config, network


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()].get("fee"),
        config["networks"][network.show_active()].get("key_hash"),
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Lottery deployed!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    start_tx = lottery.startLottery({"from": account})
    start_tx.wait(1)

    print("Lottery started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    entrance_fee = lottery.getEntranceFee() + 100000000
    enter_tx = lottery.enter({"from": account, "value": entrance_fee})
    enter_tx.wait(1)


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # fund lottery contract with LINK token
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)

    # time.sleep(60)
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()

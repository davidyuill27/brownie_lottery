from brownie import (
    network,
    accounts,
    config,
    Contract,
    interface,
    MockV3Aggregator,
    LinkToken,
    MockOracle,
    VRFCoordinatorMock,
)
from web3 import Web3

# variables
DECIMALS = 8
STARTING_PRICE = 200000000000

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork"]
LOCAL_BLOCKCHAIN_ENVINROMENTS = ["development", "ganache-local"]

# Util function to get account depending on network used
def get_account(index=None, id=None):

    if index:
        return accounts[index]
    if id:
        accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVINROMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "link_token": LinkToken,
    "vrf_coordinator": VRFCoordinatorMock,
    # "oracle": MockOracle,
}


def get_contract(contract_name):
    """This function will grab the contract addresses from brownie yaml
    if defined, otherwise, will deploy a mock version of that contract and return it

        Args:
        contract_name(string)

        Returns:
        brownie.network.contract.ProjectContract: the most recenrtly deployed version of that contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVINROMENTS:
        if (len(contract_type)) <= 0:
            deployMocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


# Deploys mocks (if not already)
def deployMocks():
    account = get_account()
    MockV3Aggregator.deploy(DECIMALS, STARTING_PRICE, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks deployed as on local instance...")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1 LINK
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    # link_token_contract = interface.LinkTokenInterface(link_token.address) # example of using interface instead of get_contract()
    tx = link_token.transfer(
        contract_address,
        amount,
        {
            "from": account,
        },
    )
    tx.wait(1)
    return tx

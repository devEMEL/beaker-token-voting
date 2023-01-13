from pyteal import *
from beaker import *
from typing import Final

class Token(Application):

  token_id: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )

  # constants

  MIN_BAL = Int(100000)
  FEE = Int(1000)


  @create
  def create(self):
    return Seq(
      self.initialize_application_state()
    )

  @external(authorize=Authorize.only(Global.creator_address()))
  def create_asset(self, asset_name: abi.String, unit_name: abi.String, total_supply: abi.Uint64, decimals: abi.Uint64):

    return Seq(
      Assert(self.token_id == Int(0)),
      InnerTxnBuilder.Execute({
        TxnField.type_enum: TxnType.AssetConfig,
        TxnField.config_asset_name: asset_name.get(),
        TxnField.config_asset_unit_name: unit_name.get(),
        TxnField.config_asset_total: total_supply.get(),
        TxnField.config_asset_decimals: decimals.get(),
        TxnField.config_asset_manager: self.address,
        TxnField.fee: self.FEE
      }),
      self.token_id.set(InnerTxn.created_asset_id())
    )

  @external
  def optin_asset(self, opt_txn: abi.AssetTransferTransaction):
    return Seq(
      Assert(
        Global.group_size() == Int(2),
        Txn.type_enum() == TxnType.AssetTransfer,
        opt_txn.get().asset_amount() == Int(0)
      ),

    )

  # tell success the changes here

  @external(authorize=Authorize.only(Global.creator_address()))
  def transfer_asset(self, receiver: abi.Address, amount: abi.Uint64):
    return Seq(
      # check if user is opted into the asset
      (bal := AssetHolding.balance(account=Txn.sender(), asset=self.token_id)),
      Assert(bal.hasValue()),

      InnerTxnBuilder.Execute({
        TxnField.type_enum: TxnType.AssetTransfer,
        TxnField.asset_receiver: receiver.get(),
        TxnField.xfer_asset: self.token_id,
        TxnField.amount: amount.get(),
        TxnField.fee: self.FEE
      })
    )
  @external(authorize=Authorize.only(Global.creator_address()))
  def send_to_creator(self):
    return Seq(
      (bal := AssetHolding.balance(account=self.address, asset=self.token_id)),
      Assert(bal.hasValue(), bal.value() > Int(0)),
      (rcv := abi.Address()).set(Global.creator_address()),
      (amt := abi.Uint64()).set(bal.value()),
      self.transfer_asset(receiver=rcv, amount=amt)
    )
         
    

  @delete
  def delete(self):
    return Seq(
      (bal := AssetHolding.balance(account=Txn.sender(), asset=self.token_id)),
      If(bal.value() > Int(0), self.send_to_creator())
    )

  @external(read_only=True)
  def get_token_id(self, *, output: abi.Uint64):
    return Seq(
      output.set(self.token_id)
    )

if __name__ == "__main__":
  Token().dump("./artifacts")
from pyteal import *
from beaker import *
from typing import Final

class Voting(Application):

  reg_begin: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )
  reg_end: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )
  vote_begin: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )
  vote_end: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )
  vote_count: Final[ApplicationStateValue] = ApplicationStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )

  vote_choice: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.bytes,
    default=Bytes("abstain")
  )
  vote_amount: Final[AccountStateValue] = AccountStateValue(
    stack_type=TealType.uint64,
    default=Int(0)
  )
  # you should use min vote count instead of hard coding
  token_id = Int(235)

  @create
  def create(self, reg_begin: abi.Uint64, reg_end: abi.Uint64, vote_begin: abi.Uint64, vote_end: abi.Uint64,):
    return Seq(
      self.reg_begin.set(reg_begin.get()),
      self.reg_end.set(reg_end.get()),
      self.vote_begin.set(vote_begin.get()),
      self.vote_end.set(vote_end.get()),

      self.initialize_application_state()
    )

  @opt_in
  def register(self):
    return Seq(
      Assert(Global.round() >= self.reg_begin, Global.round() <= self.reg_end),
      
      self.initialize_account_state()
    )

  @external
  def increment_vote(self):
    return Seq(
      (bal := AssetHolding.balance(account=Txn.sender(), asset=self.token_id)),
      Assert(bal.hasValue(), bal.value() >= Int(1000)),
      self.vote_count.set(self.vote_count + bal.value()),
      self.vote_amount.set(bal.value())
    )

  @external
  def cast_vote(self, vote_choice: abi.String):
    return Seq(
      Assert(Global.round() >= self.vote_begin, Global.round() <= self.vote_end),
      Assert(Or(
        vote_choice.get() == Bytes("yes"),
        vote_choice.get() == Bytes("no"),
        vote_choice.get() == Bytes("abstain")
      )),
      If(self.vote_choice == Bytes("yes"))
      .Then(
        # Make sure asset holding is >= 1000 and increment vote
        self.increment_vote()
      ),
      self.vote_choice.set(vote_choice.get()),

    )

  @bare_external(clear_state=CallConfig.CALL, close_out=CallConfig.CALL)
  def clear_vote(self):
    return Seq(
      Assert(Global.round() >= self.vote_begin, Global.round() <= self.vote_end),

      If(self.vote_choice == Bytes("yes"))
      .Then(
        self.vote_count.set(self.vote_count - self.vote_amount),
        self.vote_amount.set(Int(0))
      ),

      self.vote_choice.set(Bytes(""))
    )

if __name__ == "__main__":
  Voting().dump("./artifacts")
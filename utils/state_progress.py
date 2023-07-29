from loader import StatesGroup, State

class Mailing(StatesGroup):
  start_mail = State()
  new_button = State()

class Welcome(StatesGroup):
  set_manager = State()
  edit_content = State()
  new_button = State()

class Samples(StatesGroup):
  set_manager = State()
  new_sample = State()
  edit_sample = State()
  new_button = State()
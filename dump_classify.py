import inspect
import utils.classify as m

src = inspect.getsource(m.group_instruments)
print(src)
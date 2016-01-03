state
=====
Module to facilitate the use of state design pattern in python.  
Require: python 3.4+
##Basic usage: 
```python
from state import Stateful, State
  
class Window(Stateful):
	class ActiveState(State):
		default = True
		def rightClick(self):
			print('right clicked')
	class InactiveState(State):
		def rightClick(self):
			pass

Window().rightClick()
```

Note that the first argument of *rightClick* is named *self* here, but it’s not the instance of *ActiveState* or *InactiveState*. In fact it’s the instance of *Window*, and subclasses of *State* cannot be instantiated at all. You may name it *owner* or something to avoid confusion, but I think *self* is a more practical name. 

>Implementation detail: all 'normal' methods in subclass of *State* are implicitly staticmethod, and the instance of the owner class is passed as the first argument automatically. 


See example1 and example2 in the source code for more practical use cases. 

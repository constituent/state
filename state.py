#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'''\
Module to facilitate the use of state design pattern. 
'''

import inspect
from functools import partial

__all__ = ['State', 'stateful', 'Stateful']

class behavior():
	def __init__(self, func):
		self.func = func
	def __get__(self, instance, owner=None):
		if instance is None:
			return self
		else:
			return partial(self.func, instance)
	def __call__(self, *args, **kwargs):
		return self.func(*args, **kwargs)

class StateMeta(type): 
	def __new__(cls, name, bases, namespace): 
		for k, v in namespace.items(): 
			if inspect.isfunction(v): 
				namespace[k] = behavior(v)
		return type.__new__(cls, name, bases, namespace)

	def __call__(self, *args, **kwargs): 
		raise TypeError("Cannot instantiate '{}' object".format(self.__name__))

	def __str__(self): 
		return self.__name__

class State(metaclass=StateMeta):
	def __setup__(self):
		pass
	def __clear__(self):
		pass

# Remained as a callable for special use cases
def switch_state(self, new_state, forcedSwitch=True): 
	if forcedSwitch or self.__state != new_state: 
		self.__state.__clear__(self)
		self.__state = new_state
		self.__state.__setup__(self)

@property
def state(self):
	return self.__state

@state.setter
def state(self, new_state): 
	self.switch_state(new_state)

def stateful(cls=None, *, externalStates=None, defaultState=None): 
	if cls is None: 
		return partial(stateful, externalStates=externalStates, defaultState=defaultState)

	if externalStates is None: 
		externalStates = []

	if defaultState is not None and defaultState not in externalStates: 
		raise ValueError('defaultState not found in externalStates')

	cls.state = state
	cls.switch_state = switch_state


	def find_defaults(cls, derivedStates): 
		defaults = []
		# 既处理了不存在__defaultState的情况，也不会从父类那得到__defaultState（对cls.__defaultState赋值不会自动在前面加上_classname）
		defaultState = cls.__dict__.get('__defaultState')
		for value in cls.__dict__.values(): 
			if inspect.isclass(value) and issubclass(value, State) and value.__name__ not in derivedStates: 
				derivedStates.append(value.__name__)

				# Don't search default in base classes
				# Searching default is necessary only for final class whose __defaultState is not determined
				if (value.__dict__.get('default') or value == defaultState): 
					defaults.append(value)
		return defaults

	derivedStates = []
	defaults = find_defaults(cls, derivedStates)
	if defaultState is not None: 
		defaults.append(defaultState)

	# search base classes
	if len(defaults) == 0: 
		mro_iter = iter(cls.__mro__)
		next(mro_iter)# skip cls self
		for base_cls in mro_iter:
			defaults = find_defaults(base_cls, derivedStates)
			if len(defaults) > 0: 
				break

	if len(defaults) > 1: 
		raise AttributeError('{} has more than one default state: {}.'.format(cls.__name__, [cls.__name__ for cls in defaults]))

	if len(defaults) == 1: 
		cls.__defaultState = defaults[0]
	else: 
		cls.__defaultState = None

	for externalState in externalStates: 
		setattr(cls, externalState.__name__, externalState)

	old__init__ = cls.__init__
	old__getattr__ = getattr(cls, '__getattr__') if hasattr(cls, '__getattr__') else None

	def __init__(self, *args, **kwargs):
		old__init__(self, *args, **kwargs)
		if self.__class__ == cls: 
			initState = self.__dict__.get('_'+cls.__name__+'__initState')
			if initState is None: 
				if cls.__defaultState is None: 
					raise AttributeError('{}\'s default state is not found. Or set __initState for every instance.'
						.format(cls.__name__)) from None
				else: 
					initState = cls.__defaultState
			self.__state = initState
			self.__state.__setup__(self)

	def __getattribute__(self, name): 
		# Suppose there is no old__getattribute__
		# See http://bugs.python.org/issue25634 for more information.
		try: 
			return object.__getattribute__(self, name)
		except AttributeError as e: 
			if len(e.args) == 1 and e.args[0] == "'{}' object has no attribute '{}'".format(self.__class__.__name__, name): 
				return self.__getattr__(name)
			else: 
				raise RuntimeError('Unexpected AttributeError in descriptor') from e

	def __getattr__(self, name): 
		if old__getattr__ is not None: 
			try: 
				return old__getattr__(self, name)
			except AttributeError as e: 
				if len(e.args) == 1 and e.args[0] == "'{}' object has no attribute '{}'".format(self.__class__.__name__, name): 
					pass
				else: 
					raise
		try: 
			if self.__class__ == cls and name != '__state': 
				# __dict__无法查询父类
				# getattr对于类方法和静态方法拿不到原始object
				# value = self.__state.__dict__[name]
				# value = getattr(self.__state, name)
				for state_cls in self.__state.__mro__:
					try:
						value = state_cls.__dict__[name]
					except KeyError:
						continue
					else:
						break
				else:
					raise AttributeError

				if isinstance(value, (behavior, property, classmethod, staticmethod)):
					return value.__get__(self)
				else:
					return value
			else: 
				raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))
		except AttributeError: 
			raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name)) from None

	cls.__init__ = __init__
	if __debug__: 
		cls.__getattribute__ = __getattribute__
	cls.__getattr__ = __getattr__

	return cls

class StatefulMeta(type): 
	def __new__(cls, name, bases, namespace, **kwds): 
		return type.__new__(cls, name, bases, namespace)
	def __init__(self, name, bases, namespace, **kwds): 
		type.__init__(self, name, bases, namespace)
		stateful(self, **kwds)

class Stateful(metaclass=StatefulMeta): 
	pass


if __name__ == '__main__': 
	def example1(): 
		class Weekend(State): 
			def day(self): 
				print('play harder')

		class Person(Stateful, externalStates=[Weekend], defaultState=Weekend): 
			class Workday(State): 
				def __setup__(self): 
					pass
				def __clear__(self): 
					pass
			def __init__(self, name): 
				self.name = name
			def run(self): 
				for i in range(1, 8): 
					if i == 6: 
						self.state = self.Weekend
					elif i == 1: 
						self.state = self.Workday
					self.day()

		class Worker(Person): 
			class Workday(State): 
				default = True
				@classmethod
				def _day(cls): 
					print('work hard')
				def day(self): 
					self.state._day()
			def __init__(self, name, worker_id): 
				Person.__init__(self, name)
				self.worker_id = worker_id

		class Student(Person): 
			class Workday(State): 
				@staticmethod
				def _day(): 
					print('study hard')
				def day(self): 
					self.Workday._day()
			def __init__(self, name, student_id): 
				Person.__init__(self, name)
				self.student_id = student_id
				self.__initState = self.Weekend

		class Teacher(Person): 
			def day(self): 
				print('teach hard')
			def run(self): 
				for i in range(1, 8): 
					self.day()

		worker = Worker('a', 123)
		worker.run()
		print('*'*30)
		student = Student('b', 456)
		student.run()
		print('*'*30)
		teacher = Teacher('c')
		teacher.run()
	def example2(): 
		class Person(Stateful): 
			class Workday(State): 
				default = True
				def __setup__(self): 
					State.__setup__(self)
					print('Person setup')
				def __clear__(self): 
					State.__clear__(self)
					print('Person clear')
			class Weekend(State): 
				def day(self): 
					print('play harder')
			def run(self): 
				for i in range(1, 8): 
					if i == 6: 
						self.state = self.Weekend
					elif i == 1: 
						self.state = self.Workday
					self.day()
		class Worker(Person): 
			class Workday(Person.Workday): 
				default = True
				def __setup__(self): 
					Person.Workday.__setup__(self)
					print('Worker setup')
				def __clear__(self): 
					Person.Workday.__clear__(self)
					print('Worker clear')
				def day(self): 
					print('work hard')
		class Worker_(Worker): 
			class Workday(Worker.Workday): 
				default = True
				def __setup__(self): 
					Worker.Workday.__setup__(self)
					print('Worker_ setup')
				def __clear__(self): 
					Worker.Workday.__clear__(self)
					print('Worker_ clear')
		worker = Worker_()
		worker.run()
	def example3():
		class X(Stateful):
			class A(State):
				default = True
				def processOther(self):
					print('xx')
			class B(State):
				pass
			B.processOther = A.processOther
		x = X()
		x.processOther()
		x.state = X.B
		x.processOther()
	example1()
	example2()
	example3()

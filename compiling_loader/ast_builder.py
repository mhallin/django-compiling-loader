import ast


class BaseExpression:
    def __call__(self, *args, **kwargs):
        keywords = kwargs
        kwargs = keywords.pop('__kwargs', None)

        return NativeASTWrapper(ast.Call(
            func=to_ast(self),
            args=[to_ast(a) for a in args],
            keywords=[to_ast(k) for k in keywords],
            kwargs=to_ast(kwargs) if kwargs else None))

    def __getattr__(self, name):
        return NativeASTWrapper(ast.Attribute(
            value=to_ast(self),
            attr=name,
            ctx=ast.Load()))

    def __getitem__(self, key):
        return NativeASTWrapper(ast.Subscript(
            value=to_ast(self),
            slice=ast.Index(to_ast(key)),
            ctx=ast.Load()))

    def __eq__(self, other):
        return NativeASTWrapper(ast.Compare(
            left=to_ast(self),
            ops=[ast.Eq()],
            comparators=[to_ast(other)]))


class NativeASTWrapper(BaseExpression):
    def __init__(self, ast):
        self._ast = ast

    def to_ast(self):
        return self._ast


class ReusableLocal(BaseExpression):
    def __init__(self, name):
        self._name = name

    def to_ast(self):
        return ast.Name(id=self._name, ctx=ast.Load())


class Locals:
    def __init__(self, state):
        self._state = state

    def __getitem__(self, key):
        return ReusableLocal(key)


class Ivars:
    def __init__(self, state):
        self._state = state

    def __getitem__(self, key):
        return NativeASTWrapper(self._state.add_ivar(key))


class Builder:
    def __init__(self, state):
        self._state = state
        self.locals = Locals(state)
        self.ivars = Ivars(state)

    @property
    def context(self):
        return NativeASTWrapper(self._state.context_expr)

    @property
    def emit(self):
        return NativeASTWrapper(self._state.emit_expr)

    @property
    def self(self):
        return NativeASTWrapper(ast.Name(id='self', ctx=ast.Load()))

    def if_(self, test, body, orelse=[]):
        return ast.If(
            test=to_ast(test),
            body=to_stmt_list(body),
            orelse=to_stmt_list(orelse))

    def for_(self, target, iter, body, orelse=[]):
        target = to_ast(target)
        target.ctx = ast.Store()
        if isinstance(target, ast.Tuple):
            for e in target.elts:
                e.ctx = ast.Store()

        return ast.For(
            target=target,
            iter=to_ast(iter),
            body=to_stmt_list(body),
            orelse=to_stmt_list(orelse))

    def with_(self, item, body):
        return ast.With(
            items=[ast.withitem(context_expr=to_ast(item))],
            body=to_stmt_list(body))

    def try_(self, body, handlers, orelse=[], finalbody=[]):
        return ast.Try(
            body=to_stmt_list(body),
            handlers=to_list(handlers),
            orelse=to_stmt_list(orelse),
            finalbody=to_stmt_list(finalbody))

    def except_(self, type, name, body):
        return ast.ExceptHandler(
            type=to_ast(type) if type else None,
            name=to_ast(name) if name else None,
            body=to_stmt_list(body))

    def return_(self, value):
        return ast.Return(value=to_ast(value))

    def is_(self, left, right):
        return ast.Compare(
            left=to_ast(left),
            ops=[ast.Is()],
            comparators=[to_ast(right)])

    def is_not(self, left, right):
        return ast.Compare(
            left=to_ast(left),
            ops=[ast.IsNot()],
            comparators=[to_ast(right)])

    def not_in(self, left, right):
        return ast.Compare(
            left=to_ast(left),
            ops=[ast.NotIn()],
            comparators=[to_ast(right)])

    def not_(self, operand):
        return ast.UnaryOp(
            op=ast.Not(),
            operand=to_ast(operand))

    def assign(self, targets, value):
        targets = to_ast(targets)

        if isinstance(targets, (list, tuple)):
            for x in targets:
                x.ctx = ast.Store()
        else:
            targets.ctx = ast.Store()
            targets = [targets]

        return ast.Assign(targets=targets, value=to_ast(value))

    def dict(self, d):
        kvs = [(to_ast(k), to_ast(v)) for k, v in d.items()]

        return NativeASTWrapper(ast.Dict(
            keys=[k for k, _ in kvs],
            values=[v for _, v in kvs]
        ))

    def list(self, l):
        return NativeASTWrapper(ast.List(
            elts=[to_ast(i) for i in l],
            ctx=ast.Load()))

    def tuple(self, t):
        return NativeASTWrapper(ast.Tuple(
            elts=[to_ast(i) for i in t],
            ctx=ast.Load()))

    def str(self, s):
        return NativeASTWrapper(ast.Str(s=s))

    def pass_(self):
        return ast.Pass()

    def __getitem__(self, key):
        if hasattr(key, '__module__') and hasattr(key, '__name__'):
            return NativeASTWrapper(self._state.add_import(
                key.__module__, key.__name__))

        raise NotImplementedError(
            'Value not supported by __getitem__: {}'.format(key))


def to_stmt_list(obj):
    return to_list(to_stmt(obj))


def to_list(obj):
    if isinstance(obj, (list, tuple)):
        return obj
    else:
        return [obj]


def to_stmt(obj):
    obj = to_ast(obj)

    if isinstance(obj, ast.stmt):
        return obj
    if isinstance(obj, ast.expr):
        return ast.Expr(value=obj)
    if isinstance(obj, (list, tuple)):
        return [to_stmt(i) for i in obj]

    raise NotImplementedError(
        'Value not able to become statement: {}'.format(obj))


def to_ast(obj):
    if hasattr(obj, 'to_ast'):
        return obj.to_ast()
    if isinstance(obj, str):
        return ast.Str(s=obj)
    if isinstance(obj, (ast.stmt, ast.expr)):
        for field in obj._fields:
            f = getattr(obj, field, None)
            if hasattr(f, 'to_ast'):
                setattr(obj, field, f.to_ast())

        return obj
    if isinstance(obj, (list, tuple)):
        return [to_ast(i) for i in obj]
    if obj is None or type(obj) == bool:
        return ast.NameConstant(obj)
    if isinstance(obj, int):
        return ast.Num(obj)

    raise NotImplementedError(
        'Type not supported by AST builder: {}'.format(obj))


def build_expr(state, callback):
    return to_ast(callback(Builder(state)))


def build_stmt(state, callback):
    return to_stmt(callback(Builder(state)))


def new_local_var(state, name=None):
    return Builder(state).locals[state.new_local_var(name)]

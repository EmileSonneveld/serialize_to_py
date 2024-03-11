import typing
import re
from internal.utils import *

safeKeyRegex = r"^[a-zA-Z$_][a-zA-Z$_0-9]*$"


class Ref:
    def __init__(self, references, opts):
        self.opts = merge_two_dicts({}, opts)
        self.breadcrumbs: typing.Union[list, None] = None  # initialised by using code

        self.visitedRefsSource = []
        self.visitedRefsPath = []

    def visitedRefSet(self, source, path):
        if source in self.visitedRefsSource:
            raise Exception("this object was already visited!")
        self.visitedRefsSource.append(source)
        self.visitedRefsPath.append(path)

    def markAsVisited(self, source):
        self.visitedRefSet(source, self.join())

    def unmarkVisited(self, source) -> bool:
        for i in range(len(self.visitedRefsPath)):
            if self.visitedRefsPath == source:
                del self.visitedRefsSource[i]
                del self.visitedRefsPath[i]
                return True
        return False

    def isVisited(self, source) -> bool:
        return source in self.visitedRefsSource

    def getStatementForObject(self, source):
        if not self.isVisited(source):
            raise Exception("Object should be visited first")
        for i in range(len(self.visitedRefsSource)):
            if self.visitedRefsSource[i] == source:
                return self.visitedRefsPath[i]
        raise Exception("Object should be visited first. Catcher")

    def push(self, gettingStatement):
        self.breadcrumbs.append(gettingStatement)

    def pop(self):
        self.breadcrumbs.pop()

    def join(self):
        return "".join(self.breadcrumbs)

    @staticmethod
    def wrapKey(s, opts):
        return quote(s, opts)

    @staticmethod
    def isSafeKey(key):
        if type(key) == int or type(key) == float:
            key = str(key)
        return key != "" and re.match(safeKeyRegex, key)

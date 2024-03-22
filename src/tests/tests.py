import asyncio
import datetime
import json
import unittest
from typing import Optional

from serialize_to_py import *
from internal.utils import *


# cd src
# python -m unittest tests.tests


def jsonLog(arg):
    print(json.dumps(arg))


async def myAsyncFunction():
    await asyncio.sleep(3)
    return "Hello"


isLessV10 = False


def looseJsonParse(objectStr, locals_bag=None):
    """
    :type objectStr: string
    :type locals_bag: dict
    """
    if locals_bag is None:
        locals_bag = {}
    else:
        locals_bag = locals_bag.copy()  # shallow copy
    exec(objectStr, {}, locals_bag)
    # Only one variable should be added to locals
    if "serialise_to_python_temporary_function" in locals_bag:
        return locals_bag["serialise_to_python_temporary_function"]()
    else:
        return eval(objectStr, locals_bag)


def strip(s):
    return re.sub(r"[\s\"';]+", "", s)


class MyTest(unittest.TestCase):
    def serialise_test(self, name, inp, expSubstring=None, unsafe=None, objectsToLinkTo=None, deepStrictEqual=True):
        print("------------ " + name + " -------------")
        # console.log("objectsToLinkTo", objectsToLinkTo)
        codeStr = serialize(inp, {"unsafe": unsafe, "objectsToLinkTo": objectsToLinkTo})
        print("codeStr:")
        print(codeStr)
        if isLessV10 and codeStr.indexOf("\u2028") != -1:  # 'LINE SEPARATOR'
            return
        res = looseJsonParse(codeStr, objectsToLinkTo)

        print("instance:")
        print(inp)
        print("res:")
        print(res)
        if expSubstring:
            expSubstring = strip(expSubstring)
            print("exp:")
            print(expSubstring)
            strCopy = strip(codeStr)
            print("strCopy:")
            print(strCopy)
            self.assertIn(expSubstring, strCopy)

        if deepStrictEqual:
            import pickle

            inpPicle = None
            resPicle = None
            try:
                inpPicle = pickle.dumps(inp)
                resPicle = pickle.dumps(res)
            except Exception as e:
                print("Pickle error: " + str(e))
            if inpPicle and resPicle:
                self.assertEqual(inpPicle, resPicle)

    def test_safe_mode(self):
        self.serialise_test("none", None, "None")
        self.serialise_test("boolean", True, "True")
        self.serialise_test("number", 3.1415, "3.1415")
        self.serialise_test("zero", 0, "0")
        self.serialise_test("negative zero", -0.0, "-0", deepStrictEqual=False)
        self.serialise_test("number int", 3, "3")
        self.serialise_test("number negative int", -13, "-13")
        self.serialise_test("number float", 0.1, "0.1")
        self.serialise_test("number negative float", -0.2, "-0.2")
        self.serialise_test("nan", float("nan"), 'float("nan")')
        self.serialise_test("infinity", float("inf"), 'float("inf")')
        self.serialise_test("simple string", "simple string", '"simple string"')
        self.serialise_test("string", 'string\'s\n"new"     line', '"string\'s\\n\\"new\\"     line"')
        self.serialise_test("empty string", "", '""')
        # 3 ways to represent null char are all the same data:
        self.serialise_test("null char 1", "\0", '"\\x00"')
        self.serialise_test("null char 2", "\u0000", '"\\x00"')
        self.serialise_test("null char 3", "\x00", '"\\x00"')

    def test_safe_mode2(self):
        self.serialise_test("empty object", {}, "{}")
        self.serialise_test("object simple", {"a": 1, "b": 2}, "{'a': 1, 'b': 2}")
        self.serialise_test("object with empty string property", {"a": 1, "": 2}, "2")
        self.serialise_test("object with backslash", {"backslash": "\\"}, '"\\u005C"')
        self.serialise_test(
            "object of primitives",
            {5: 3.1415, "one": True, "two": False, "thr-ee": None, "four": 1, "six": -17, "se ven": "string"},
            '{"5": 3.1415, one: True, two: False, "thr-ee": None, four: 1, six: -17, "se ven": "string"}',
            deepStrictEqual=False,  # TODO: Why does deepStrictEqual not work here?
        )
        # self.serialise_test('object with unsafe property name',
        #     {"</script><script>alert('xss')//": 0},
        #     '"\\u003C\\u002Fscript\\u003E\\u003Cscript\\u003Ealert(\'xss\')\\u002F\\u002F"'
        # )
        # self.serialise_test('object with backslash-escaped quote in property name',
        #     {'\\": 0}; alert(\'xss\')//': 0},
        #     '"\\u005C\\": 0}; alert(\'xss\')\\u002F\\u002F"'
        # )
        self.serialise_test("function", jsonLog, "def jsonLog(arg):\n  print(json.dumps(arg))", None, None, False)
        # self.serialise_test('async function', myAsyncFunction, "Hello", None, None, False)
        # self.serialise_test('lambda function', {'key': lambda a: a + 1}, '(a) => a + 1', None, None, False)
        # self.serialise_test('function link', jsonLog, "fakeGlobal.jsonLog", None, {fakeGlobal}, False)
        self.serialise_test(
            "date", datetime.datetime.fromtimestamp(24 * 12 * 3600), "datetime.datetime(1970, 1, 13, 1, 0)"
        )
        self.serialise_test(
            "date 2", datetime.datetime.fromtimestamp(24 * 12 * 3600).isoformat(), "1970-01-13T01:00:00"
        )
        # self.serialise_test('invalid date') there are no invalid date objects in Python. Good.
        self.serialise_test("exception", Exception("error"), "Exception('error')")
        # self.serialise_test('error with unsafe message',
        #                     Exception("</script><script>alert('xss')"),
        #                     'Exception(\'\\u003C\\u002Fscript\\u003E\\u003Cscript\\u003Ealert(\'xss\')\')'
        #                     )
        self.serialise_test("empty array", [], "[]")
        self.serialise_test(
            "array", [True, False, None, 1, 3.1415, -17, "string"], '[True, False, None, 1, 3.1415, -17, "string"]'
        )
        # Bit arrays not tested

        # self.serialise_test('regex unsafe characters',
        #                     r"<>\/\\\t\n\r\b\0",
        #                     "'\\u003C\\u003E\\u005C\\u002F\\u005C\\u005C\\u005Ct\\u005Cn\\u005Cr\\u005Cb\\u005C0'"
        #                     )

    def test_other(self):
        self.serialise_test(
            "simple nested objects",
            {
                "a": {
                    "a1": 0,
                    "a2": 0,
                },
                "b": {
                    "b1": 0,
                    "b2": 0,
                },
            },
            "b2",
        )

        smallObj = {"key": "originalValue"}
        ob = {
            "a": smallObj,
            "": smallObj,
        }
        self.serialise_test("converting an object with empty property name", ob)
        ob2 = serialize(ob)
        ob3 = looseJsonParse(ob2)
        ob3["a"]["key"] = "Changed!"
        self.assertEqual(ob3[""]["key"], ob3["a"]["key"])

        r = {"one": True, "thr-ee": None, 3: "3", "4 four": {"four": 4}}

        ob = {"a": r, "b": r, "c": {"d": r, 0: r, "spa ce": r}, 0: r["4 four"], "spa ce": r}
        # TODO: Why does deepStrictEqual not work here?
        self.serialise_test("converting an object of objects using references", ob, deepStrictEqual=False)

    def test_converting_an_object_of_objects(self):
        o1 = {"one": True, "thr-ee": None, "3": "3", "4 four": "four\n<test></test>", 'five"(5)': 5}
        ob = {"a": o1, "b": o1}
        res = serialize(ob, {"unsafe": True})
        exp = '{a: {"3": "3", one: true, "thr-ee": undefined, "4 four": "four\\n<test></test>", "five\\"(5)": 5}, b: {"3": "3", one: true, "thr-ee": undefined, "4 four": "four\\n<test></test>", "five\\"(5)": 5}}'

        # assert.deepStrictEqual(looseJsonParse(res), looseJsonParse(exp))

    def test_readme_example(self):
        reusedObject = {"key": "value"}
        reusedObject["cyclicSelf"] = reusedObject
        ob = {
            "s": "hello world!",
            "num": 3.1415,
            "bool": True,
            "None": None,
            "ob": {"foo": "bar", "reusedObject": reusedObject},
            "arr": [1, "2", reusedObject],
            # 'regexp': / ^ test?$ /,
            # 'date': new Date(),
            # buffer: new Uint8Array([1, 2, 3]),
            # set: new Set([1, 2, 3]),
            # map: new
            # Map([['a', 1], ['b', reusedObject]])
        }
        self.serialise_test("readme example", ob)

    def test_object_test(self):
        #         class CarMetaclass(type):
        #             def __repr__(self):
        #                 return """
        # # Simplified Car class.
        # class Car(object):
        #     def __init__(self, name, year):
        #         self.name = name
        #         self.year = year
        # """

        class Car(object):  # , metaclass=CarMetaclass
            def __init__(self, name, year):
                self.name = name
                self.year = year

            def age(self):
                date = datetime.date.today()
                return date.year - self.year

            def __repr__(self):
                return "Car(" + repr(self.name) + ", " + repr(self.year) + ")"

        yaris = Car("Yaris", 2019)
        ob = {
            "yaris": yaris,
        }
        codeStr = serialize(ob)
        objectsToLinkTo = {"Car": Car}
        res = looseJsonParse(codeStr, locals_bag=objectsToLinkTo)
        assert res["yaris"].age is not None
        age = res["yaris"].age()
        print('res["yaris"].age(): ', age)
        assert age is not None
        self.serialise_test("Car object", ob, "Yaris", objectsToLinkTo=objectsToLinkTo)

    def test_logger(self):
        import logging

        logger = logging.getLogger("testLogger")
        logger.info("Some message")

        ob = {
            "logger": logger,
        }

        def trySerializeLogger(obj, opts, indent) -> Optional[str]:
            t = type(obj)
            if t.__name__ != "Logger":
                print("I can not serialize " + str(t))
                # Jump out early to avoid potentially stateful import
                return None
            import logging

            if t != logging.Logger:
                print("I can not serialize " + str(t))
                return None
            print("trySerializeLogger will do an attempt")
            s = ""
            s += f"{opts['space'] * indent}def initializer():\n"
            s += f"{opts['space'] * (indent + 1)}import logging\n"
            s += f"{opts['space'] * (indent + 1)}return logging.getLogger({serialize(obj.name, opts)})\n"
            return s

        opts = {
            "trySerializeList": [trySerializeLogger],
            # "objectsToLinkTo": {'logging': logging}
        }
        codeStr = serialize(ob, opts)

        res = looseJsonParse(codeStr)  # , locals_bag=opts["objectsToLinkTo"]
        assert res["logger"].name is not None
        res["logger"].info("Some message")

    def test_pyspark(self):
        import pyspark

        context = pyspark.SparkContext.getOrCreate()
        rdd = context.parallelize([9, 10, 11, 12])

        def trySerializePysparkObject(source, opts, indent) -> Optional[str]:
            t = type(source)
            if t.__name__ != "RDD":
                print("I can not serialize " + str(t))
                # Jump out early to avoid potentially stateful import
                return None
            import pyspark

            if t != pyspark.RDD:
                print("I can not serialize " + str(t))
                return None
            print("trySerializePysparkObject will do an attempt")
            ret = serialize(source.collect(), opts)
            s = ""
            s += f"{opts['space'] * indent}def initializer():\n"
            # s += f"{opts['space'] * (indent + 1)}{ret['codeBefore']})\n"  # TODO indentation for multiline
            s += f"{opts['space'] * (indent + 1)}return context.parallelize({ret})\n"
            # s += f"{opts['space'] * (indent + 1)}{ret['codeAfter']})\n"
            return s

        opts = {
            # "trySerializeList": [trySerializePysparkObject],
            # "objectsToLinkTo": {'logging': logging}
        }
        codeStr = serialize(rdd, opts)

        res = looseJsonParse(codeStr)  # , locals_bag=opts["objectsToLinkTo"]
        # assert res["logger"].name is not None
        # res["logger"].info("Some message")

        # self.serialise_test("rdd", rdd)

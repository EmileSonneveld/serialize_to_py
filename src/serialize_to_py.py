from internal.reference import Ref
from internal import utils
import math
import inspect


class ObjectIsDirectlyLinkableError(Exception):
    def __int__(self, message, directLink):
        print("TODO: call parent constructor?")
        self.name = "ObjectIsDirectlyLinkableError"
        self.directLink = directLink


def serialize(src: object, opts: dict = None) -> str:
    opts = utils.merge_two_dicts(
        {
            "maxDepth": 99999,
            "evaluateSimpleGetters": True,
            "unsafe": False,
            "space": "  ",
            "alwaysQuote": False,
            "fullPaths": False,
            "needle": None,
            "objectsToLinkTo": None,
            "trySerializeList": [],
        },
        opts,
    )
    if type(opts["space"]) == int:
        opts["space"] = " " * opts["space"]
    elif not opts["space"]:
        print("TODO: Disallow this in Python?")
        opts["space"] = ""
    newline = "\n" if opts["space"] else ""
    refs = Ref([], opts)

    objCounter = 0
    absorbPhase = True

    def stringify(source, indent=2):
        nonlocal objCounter
        codeBefore = ""
        codeMain = ""
        codeAfter = ""

        sourceType = utils.toType(source)
        if absorbPhase and source == src:
            if type(source) == "object" or type(source) == "function":
                raise ObjectIsDirectlyLinkableError("", refs.join())
            else:
                return {codeBefore, codeMain, codeAfter}

        if indent >= opts["maxDepth"]:
            codeMain += "None # >maxDepth "
            return {codeBefore, codeMain, codeAfter}

        try:
            if sourceType == "NoneType":
                codeMain += "None"
            elif sourceType == "str":
                codeMain += utils.quote(source, opts) or '""'
            elif sourceType == "function":
                refs.markAsVisited(source)
                codeMain += '"""TODO: ' + inspect.getsource(source).replace('"""', '\\"""') + '"""'
            elif sourceType == "bool":
                codeMain += str(source)
            elif sourceType == "float" or sourceType == "int":
                if source == 0 and math.copysign(1, source) == -1:
                    codeMain += "-0"  # 0 === -0, so this is probably not important.
                elif math.isfinite(source):
                    codeMain += str(source)
                else:
                    codeMain += f'float("{str(source)}")'
            # elif sourceType == "list": TODO
            elif sourceType == "dict":
                refs.markAsVisited(source)
                tmp = []
                for key in source.keys():
                    # TODO, support hashable objects as keys
                    refs.push(f"[{utils.quote(key, opts)}]")
                    if refs.isVisited(source[key]):
                        # Python does not really have inline comment, so just add temporary string
                        tmp.append(f"{opts['space'] * indent + Ref.wrapKey(key, opts)}: 'Linked later'")
                        codeAfter += f"  {refs.join()} = {refs.getStatementForObject(source[key])};\n"
                    else:
                        ret = stringify(source[key], indent + 1)
                        codeBefore += ret["codeBefore"]
                        tmp.append(f"{opts['space'] * indent + Ref.wrapKey(key, opts)}: {ret['codeMain']}")
                        codeAfter += ret["codeAfter"]
                    refs.breadcrumbs.pop()
                # tmp[len(tmp) - 1] = (tmp[len(tmp) - 1])[0: -1]
                codeMain += "{" + f"{newline}{(',' + newline).join(tmp)}{newline}{opts['space'] * (indent - 1)}" + "}"
            elif sourceType == "datetime":
                codeBefore += "  import datetime\n"
                codeMain += repr(source)
            elif sourceType == "RDD":
                codeBefore += "  import pyspark\n"
                codeBefore += "  context = pyspark.SparkContext.getOrCreate()\n"
                ret = stringify(source.collect(), indent + 1)
                codeBefore += ret["codeBefore"]
                codeMain += f"context.parallelize({ret['codeMain']})"
                codeAfter += ret["codeAfter"]
            elif sourceType == "list":
                refs.markAsVisited(source)
                tmp = []

                # loop over indexes in source:
                for i in range(len(source)):
                    el = source[i]
                    refs.push(f"[{i}]")
                    if refs.isVisited(el):
                        tmp.append(f'{opts["space"] * indent}"Linked later"')
                        codeAfter += f"  {refs.join()} = {refs.getStatementForObject(el)}\n"
                    else:
                        ret = stringify(el, indent + 1)
                        codeBefore += ret["codeBefore"]
                        tmp.append(f"{opts['space'] * indent}{ret['codeMain']}")
                        codeAfter += ret["codeAfter"]
                    refs.breadcrumbs.pop()

                codeMain += "[" + f"{newline}{(',' + newline).join(tmp)}{newline}{opts['space'] * (indent - 1)}" + "]"
            else:
                handled = False
                trySerializeList = opts["trySerializeList"]
                for trySerialize in trySerializeList:
                    strOption = trySerialize(source, opts, 1)
                    if strOption is not None:
                        # TODO: Do a quick verify on result of user specified serializer.
                        objCounter += 1
                        safeItem = "obj" + str(objCounter)
                        codeBefore += strOption
                        codeBefore += f"\n"
                        codeBefore += f"{opts['space'] * 1}{safeItem} = initializer()\n"
                        codeBefore += f"\n"
                        codeMain += safeItem
                        handled = True
                        break
                if not handled:
                    print(f"Unknown type: '{sourceType}' source: '{source}'")
                    codeMain += repr(source)
        except ObjectIsDirectlyLinkableError:
            raise
        except Exception as e:
            if refs.unmarkVisited(source):
                print("Dirty error." + str(e))
            codeMain = f"None # {codeMain.replace('*/', '* /')} {errorToValue(e)} "

        return {"codeBefore": codeBefore, "codeMain": codeMain, "codeAfter": codeAfter}

    def errorToValue(err):
        message = str(err)
        idx = message.find("\n")
        if idx != -1:
            message = message[0:idx]
        return f"Error: {message}.Breadcrumb: {refs.join()}"

    try:
        if opts["objectsToLinkTo"]:
            for key in opts["objectsToLinkTo"]:
                refs.breadcrumbs = [key]
                stringify(opts["objectsToLinkTo"][key])
    except ObjectIsDirectlyLinkableError as error:
        return error.directLink

    # Now reset, and go over the real object
    objCounter = 0
    refs.breadcrumbs = ["root"]
    absorbPhase = False

    ret = stringify(src, 2)
    if ret["codeBefore"] == "" and ret["codeAfter"] == "":
        # Keep compatibility with default JSON
        # TODO: Check for compatibility with example library.
        return ret["codeMain"].replace("\n" + opts["space"], "\n")

    return f"""
def serialise_to_python_temporary_function():
{ret['codeBefore']}
  root = {ret['codeMain']}
{ret['codeAfter']}
  return root
serialise_to_python_temporary_function()
"""

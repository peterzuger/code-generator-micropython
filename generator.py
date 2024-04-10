#!/usr/bin/env python3
import argparse
import token
import tokenize
from datetime import datetime
from os import makedirs, path, remove, rmdir


def micropython_mk_path(module_directory):
    return "{}/micropython.mk".format(module_directory)


def module_code_path(module_directory, module_name):
    return "{}/{}.c".format(module_directory, module_name)


def clear_c_module(module_directory, module_name):
    if path.exists(module_directory) and path.isdir(module_directory):
        if path.exists(micropython_mk_path(module_directory)):
            remove(micropython_mk_path(module_directory))
        if path.exists(module_code_path(module_directory, module_name)):
            remove(module_code_path(module_directory, module_name))
        rmdir(module_directory)


def module_exists_error():
    print("The module directory already exists.")
    print("call with --clear to overwrite existing files.")
    exit(1)


def module_exists(module_directory):
    if path.exists(module_directory):
        return True
    return False


def create_c_module(module_directory, module_name, code, rom_table):
    try:
        makedirs(module_directory)

        script_dir = path.dirname(__file__)

        module_name_u = module_name.upper()
        with open(micropython_mk_path(module_directory), "x") as f:
            with open(path.join(script_dir, "templates/micropython.mk")) as template:
                for line in template:
                    f.write(
                        line.format(
                            module_name_u=module_name_u, module_name=module_name
                        )
                    )

        with open(module_code_path(module_directory, module_name), "x") as f:
            with open(path.join(script_dir, "templates/code.c")) as template:
                for line in template:
                    f.write(
                        line.format(
                            module_name=module_name,
                            date=datetime.now().strftime("%H:%M on %d %m %Y"),
                            generated_code=code,
                            rom_table_entries=rom_table,
                            module_name_u=module_name_u,
                        )
                    )
    except FileExistsError:
        module_exists_error()


def mp_rom_ptr(name, value):
    return "\n    {{ MP_ROM_QSTR(MP_QSTR_{name}), MP_ROM_PTR(&{value}) }},".format(
        name=name, value=value
    )


def mp_rom_int(name, value):
    return "\n    {{ MP_ROM_QSTR(MP_QSTR_{name}), MP_ROM_INT({value}) }},".format(
        name=name, value=value
    )


def mp_rom_qstr(name, value):
    return (
        "\n    {{ MP_ROM_QSTR(MP_QSTR_{name}), MP_ROM_QSTR(MP_QSTR_{value}) }},".format(
            name=name, value=value
        )
    )


def mp_dict(name, elements):
    return "static const mp_rom_map_elem_t {name}_dict_table[]={{{elements}\n}};\nstatic MP_DEFINE_DICT({name}_dict, {name}_dict_table);".format(
        name=name, elements=elements
    )


def mp_qstr(string):
    return "MP_ROM_QSTR(MP_QSTR_{})".format(string)


def mp_int(num):
    return "MP_ROM_INT({})".format(num)


def mp_float(name):
    return mp_ptr(name)


def mp_const_float_name(num):
    return "mp_const_float_{}_obj".format(str(num).replace(".", "_"))


def mp_const_float(name, num):
    return "const mp_obj_float_t {} = {{{{&mp_type_float}}, (mp_float_t){}}};\n".format(
        name, num
    )


def mp_ptr(ptr):
    return "MP_ROM_PTR(&{})".format(ptr)


def mp_dict_element(key, value):
    return "\n    {{ {key}, {value} }},".format(key=key, value=value)


def mp_rom_dict(name):
    return mp_rom_ptr(name, "{}_dict".format(name))


def constant_lookup(name, constants):
    for i in constants:
        if i.name == name:
            return i.value


def parse_failure(tokens):
    for token in tokens:
        print(token)
    exit(1)


class Number:
    floats = []

    def __init__(self, tokens):
        if "." in tokens[0].string:
            self.value = float(tokens[0].string)
            self._name = mp_const_float_name(tokens[0].string)
            self.is_float = True
        else:
            self.value = int(tokens[0].string)
            self.is_float = False

    def name(self):
        return self._name

    def generate_code(self):
        if self.is_float and self.value not in self.floats:
            self.floats.append(self.value)
            return mp_const_float(self.name(), self.value)
        return ""

    def generate_value(self):
        if self.is_float:
            return mp_float(self.name())
        return mp_int(self.value)


class String:
    def __init__(self, tokens):
        self.value = tokens[0].string[1:-1]

    def generate_code(self):
        return ""

    def generate_value(self):
        return mp_qstr(self.value)


class Tuple:
    counter = 0

    def __init__(self, tokens, name, constants):
        self._name = "unnamed_{}_{}".format(name, str(Tuple.counter))
        Tuple.counter += 1
        self.values = []

        i = 1
        while i < len(tokens):
            if tokens[i].exact_type == tokenize.RPAR:
                if len(self.values) == 1 and tokens[i - 1].exact_type != tokenize.COMMA:
                    print("warning: treating (x) as 1 tuple")
                self.len = 1 + i
                break
            elif tokens[i].exact_type == tokenize.COMMA:
                pass  # IGNORE
            elif tokens[i].exact_type == tokenize.STRING:
                self.values.append(String(tokens[i:]))
            elif tokens[i].exact_type == tokenize.NUMBER:
                self.values.append(Number(tokens[i:]))
            else:
                print("--UNMATCHED TUPLE VALUE--")
                parse_failure(tokens[i:])
            i += 1

    @staticmethod
    def match(tokens):
        return tokens[0] == tokenize.LPAR

    def length(self):
        return self.len

    def generate_code(self):
        code = ""
        for v in self.values:
            code += v.generate_code()
        elements = ""
        for v in self.values:
            elements = ",\n    ".join((elements, v.generate_value()))
        return "{code}\n\nstatic MP_DEFINE_TUPLE({name}_tuple, {size}{elements});\n\n".format(
            code=code, name=self.name(), size=len(self.values), elements=elements
        )

    def name(self):
        return self._name


class UnnamedDictionary:
    counter = 0

    def __init__(self, tokens, name, constants):
        self._name = "unnamed_{}_{}".format(name, str(UnnamedDictionary.counter))
        UnnamedDictionary.counter += 1
        self.pairs = []

        i = 1
        while i < len(tokens):
            if tokens[i].exact_type == tokenize.RBRACE:
                self.len = 1 + i
                break
            elif DictionaryElement.match(tokens[i:]):
                c = DictionaryElement(tokens[i:], self.name(), constants)
                i += c.length()
                self.pairs.append(c)
            elif tokens[i].exact_type == tokenize.COMMA:
                pass  # IGNORE
            else:
                print("--UNMATCHED UNNAMED DICT VALUE--")
                parse_failure(tokens[i:])
            i += 1

    @staticmethod
    def match(tokens):
        return (
            tokens[0].exact_type == tokenize.NAME
            or tokens[0].exact_type == tokenize.STRING
            or tokens[0].exact_type == tokenize.NUMBER
        ) and tokens[1].exact_type == tokenize.COLON

    def length(self):
        return self.len

    def generate_code(self):
        element_code = ""
        elements = ""
        for e in self.pairs:
            element_code += e.generate_code()
            elements += e.generate_rom_constant()
        return element_code + mp_dict(self.name(), elements) + "\n\n"

    def name(self):
        return self._name


class DictionaryElement:
    def __init__(self, tokens, name, constants):
        self.name = name
        if tokens[0].exact_type == tokenize.NAME:
            self.key_type = tokenize.NUMBER
            self.key = constant_lookup(tokens[0].string, constants)
        elif tokens[0].exact_type == tokenize.STRING:
            self.key_type = tokenize.STRING
            self.key = tokens[0].string[1:-1]
        else:
            self.key_type = tokens[0].exact_type
            self.key = tokens[0].string

        if tokens[2].exact_type == tokenize.LBRACE:
            self.value = UnnamedDictionary(tokens[2:], self.name, constants)
            self.value_type = tokenize.LBRACE
            self.len = 1 + self.value.length()
        elif tokens[2].exact_type == tokenize.LPAR:
            self.value = Tuple(tokens[2:], self.name, constants)
            self.value_type = tokenize.LPAR
            self.len = 1 + self.value.length()
        elif tokens[2].exact_type == tokenize.NAME:
            self.value = constant_lookup(tokens[2].string, constants)
            self.value_type = "const"
            self.len = 2
        elif tokens[2].exact_type == tokenize.STRING:
            self.value = tokens[2].string[1:-1]
            self.value_type = tokenize.STRING
            self.len = 2
        elif tokens[2].exact_type == tokenize.NUMBER:
            self.value = Number(tokens[2:])
            self.value_type = tokenize.NUMBER
            self.len = 2
        else:
            self.value = tokens[2].string
            self.value_type = tokens[2].exact_type
            self.len = 2

    @staticmethod
    def match(tokens):
        return (
            tokens[0].exact_type == tokenize.NAME
            or tokens[0].exact_type == tokenize.STRING
            or tokens[0].exact_type == tokenize.NUMBER
        ) and tokens[1].exact_type == tokenize.COLON

    def length(self):
        return self.len

    def generate_code(self):
        if self.value_type in [tokenize.LBRACE, tokenize.LPAR, tokenize.NUMBER]:
            return self.value.generate_code()
        return ""

    def generate_rom_constant(self):
        if self.key_type == tokenize.NUMBER:
            key = mp_int(int(self.key, 0))
        elif self.key_type == tokenize.STRING:
            key = mp_qstr(self.key)
        else:
            print("ERROR - generate_code - invalid key type")
            exit(1)

        if self.value_type == tokenize.LBRACE:
            value = mp_ptr(self.value.name() + "_dict")
        elif self.value_type == tokenize.LPAR:
            value = mp_ptr(self.value.name() + "_tuple")
        elif self.value_type == "const":
            value = mp_int(int(self.value, 0))
        elif self.value_type == tokenize.NUMBER:
            value = self.value.generate_value()
        elif self.value_type == tokenize.STRING:
            value = mp_qstr(self.value)

        return mp_dict_element(key, value)


class Dictionary:
    def __init__(self, tokens, constants):
        self.name = tokens[0].string
        self.pairs = []

        i = 3
        while i < len(tokens):
            if tokens[i].exact_type == tokenize.RBRACE:
                self.len = 1 + i
                return
            elif DictionaryElement.match(tokens[i:]):
                c = DictionaryElement(tokens[i:], self.name, constants)
                i += c.length()
                self.pairs.append(c)
            elif tokens[i].exact_type == tokenize.COMMA:
                pass  # IGNORE
            else:
                print("--UNMATCHED DICT VALUE--")
                parse_failure(tokens[i:])
            i += 1

    @staticmethod
    def match(tokens):
        return (
            tokens[0].exact_type == tokenize.NAME
            and tokens[1].exact_type == tokenize.EQUAL
            and tokens[2].exact_type == tokenize.LBRACE
        )

    def length(self):
        return self.len

    def generate_code(self):
        element_code = ""
        elements = ""
        for e in self.pairs:
            element_code += e.generate_code()
            elements += e.generate_rom_constant()
        return element_code + mp_dict(self.name, elements)

    def generate_rom_constant(self):
        return mp_rom_dict(self.name)


class Constant:
    def __init__(self, tokens):
        self.name = tokens[0].string
        self.value = tokens[4].string
        self.len = 7

    @staticmethod
    def match(tokens):
        return (
            tokens[0].exact_type == tokenize.NAME
            and tokens[1].exact_type == tokenize.EQUAL
            and tokens[2].exact_type == tokenize.NAME
            and tokens[2].string == "const"
            and tokens[3].exact_type == tokenize.LPAR
            and tokens[4].exact_type == tokenize.NUMBER
            and tokens[5].exact_type == tokenize.RPAR
            and tokens[6].exact_type == tokenize.NEWLINE
        )

    def length(self):
        return self.len

    def generate_code(self):
        return ""

    def generate_rom_constant(self):
        return mp_rom_int(self.name, self.value)


class Variable:
    def __init__(self, tokens):
        self.name = tokens[0].string
        self.value = tokens[2].string
        self.value_type = tokens[2].exact_type
        self.len = 4

    @staticmethod
    def match(tokens):
        return (
            tokens[0].exact_type == tokenize.NAME
            and tokens[1].exact_type == tokenize.EQUAL
            and (
                tokens[2].exact_type == tokenize.NUMBER
                or tokens[2].exact_type == tokenize.STRING
            )
            and tokens[3].exact_type == tokenize.NEWLINE
        )

    def length(self):
        return self.len

    def generate_code(self):
        return ""

    def generate_rom_constant(self):
        if self.value_type == tokenize.NUMBER:
            return mp_rom_int(self.name, self.value)
        elif self.value_type == tokenize.STRING:
            return mp_rom_qstr(self.name, self.value)


def remove_tokens(g, e):
    for y in g:
        if not y.exact_type in e:
            yield y


def parse_arguments():
    parser = argparse.ArgumentParser(description="MicroPython C code generator")

    parser.add_argument(
        "-f", "--filename", type=str, required=True, help="Python file to parse"
    )
    parser.add_argument(
        "-d", "--directory", type=str, help="Directory for the python module"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Remove existing module directory"
    )
    parser.add_argument(
        "--make", action="store_true", help="do nothing if module exists"
    )
    parser.add_argument("--modulename", type=str, help="Python module to generate")

    return parser.parse_args()


def main():
    args = parse_arguments()

    module_name = (
        args.modulename
        if args.modulename
        else path.splitext(path.basename(args.filename))[0]
    )
    module_directory = args.directory if args.directory else module_name

    if args.clear:
        clear_c_module(module_directory, module_name)
        if args.make:
            return

    if args.make and module_exists(module_directory):
        return

    with tokenize.open(args.filename) as f:
        tokens = list(
            remove_tokens(
                tokenize.generate_tokens(f.readline), [tokenize.COMMENT, tokenize.NL]
            )
        )
        constants = []
        dictionaries = []

        i = 0
        while i < len(tokens):
            if tokens[i].exact_type == tokenize.ENDMARKER:
                break
            elif Constant.match(tokens[i:]):
                c = Constant(tokens[i:])
                i += c.length()
                constants.append(c)
                continue
            elif Dictionary.match(tokens[i:]):
                d = Dictionary(tokens[i:], constants)
                i += d.length()
                dictionaries.append(d)
            else:
                print(token.tok_name[tokens[i].exact_type], tokens[i].string)
            i += 1

        code = ""
        rom_table = ""
        for i in constants:
            rom_table += i.generate_rom_constant()
        rom_table += "\n"

        for i in dictionaries:
            code += i.generate_code()
            rom_table += i.generate_rom_constant()

        create_c_module(module_directory, module_name, code, rom_table)


if __name__ == "__main__":
    main()

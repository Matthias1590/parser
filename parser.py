from __future__ import annotations
import re


class ParseResult:
    FAILED: ParseResult

    def __init__(self, parser: Parser, parsed: str | list[ParseResult]) -> None:
        self.parser = parser
        self.parsed = parsed

    @property
    def length(self) -> int:
        if self == ParseResult.FAILED:
            return 0

        if isinstance(self.parsed, str):
            return len(self.parsed)
        else:  # list[ParseResult]
            raise NotImplementedError

    def __repr__(self) -> str:
        if self == ParseResult.FAILED:
            return "FAILED"

        return repr(self.parsed)


ParseResult.FAILED = ParseResult(None, None)


class Parser:
    def parse(self, text: str, partially: bool = False) -> ParseResult:
        raise NotImplementedError

    def __or__(self, other: Parser) -> GroupParser:
        if isinstance(self, GroupParser):
            if isinstance(other, GroupParser):
                return GroupParser().define(*(self.parsers + other.parsers))

            return GroupParser().define(*(self.parsers + (other,)))
        elif isinstance(other, GroupParser):
            return GroupParser().define(*((self,) + other.parsers))

        return GroupParser().define(self, other)


class LiteralParser(Parser):
    def __init__(self, literal: str) -> None:
        super().__init__()
        self.literal = literal

    def parse(self, text: str, partially: bool = False) -> ParseResult:
        if not text.startswith(self.literal):
            return ParseResult.FAILED

        if not partially and text != self.literal:
            return ParseResult.FAILED

        return ParseResult(self, self.literal)


class RegexParser(Parser):
    def __init__(self, pattern: str) -> None:
        super().__init__()
        self.pattern = re.compile(pattern)

    def parse(self, text: str, partially: bool = False) -> ParseResult:
        if match := self.pattern.match(text):
            if partially:
                return ParseResult(self, text[: match.end()])

            if text != text[: match.end()]:
                return ParseResult.FAILED

            return ParseResult(self, text)

        return ParseResult.FAILED


class CombinedParser(Parser):
    def __init__(self) -> None:
        super().__init__()
        self.parsers = ()

    def define(self, *parsers: Parser) -> CombinedParser:
        if len(parsers) == 1 and isinstance(parsers[0], type(self)):
            parsers = parsers[0].parsers

        self.parsers = parsers

        return self


class SequenceParser(CombinedParser):
    def parse(self, text: str, partially: bool = False) -> ParseResult:
        # TODO: Parse non recursive first

        results = []

        for parser in self.parsers:
            result = parser.parse(text, True)

            if result == ParseResult.FAILED:
                if not partially:
                    return ParseResult.FAILED

                break

            results.append(result)
            text = text[result.length :]

        if not partially and len(text) > 0:
            return ParseResult.FAILED

        return ParseResult(self, results)


class GroupParser(CombinedParser):
    def parse(self, text: str, partially: bool = False) -> ParseResult:
        # TODO: Consider returning the parseresult that consumes most of the input string (or all parseresults that didn't fail)

        for parser in self.parsers:
            result = parser.parse(text, partially)

            if result != ParseResult.FAILED:
                return result

        return ParseResult.FAILED


# ident = RegexParser(r"[A-z]*")
# string = RegexParser(r"\"[^\"]*\"")
# lpar = LiteralParser("(")
# rpar = LiteralParser(")")
# dot = LiteralParser(".")

# call = SequenceParser()
# objseq = SequenceParser()
# object = objseq | ident

# call.define(object, lpar, string, rpar)
# objseq.define(object, dot, ident)

# parsed = call.parse('System.out.println("Hello, world!")')
# parsed = object.parse("System.out.println")

expr = GroupParser()
add = SequenceParser()
mult = SequenceParser()

num = RegexParser(r"[0-9]+")
plus = LiteralParser("+")
star = LiteralParser("*")

expr.define(num, add, mult)
add.define(expr, plus, expr)
mult.define(expr, star, expr)

parsed = expr.parse("1+2")

print(parsed)

import re
from typing import List

from nxcore.middleware.logging_manager import logger

from engine.seclang.seclang_schema import (
    SecComponentSignature,
    SecMarker,
    SecAction,
    SecRule,
    SecBaseSchema,
)


# noinspection PyMethodMayBeStatic,PyListCreation
class RuleSetParser:
    lines = []
    line_index = 0
    c_line = 0

    def __init__(self):
        self.charset = "utf-8"

    def _is_com_break(self, cmd):
        b = cmd.startswith(
            (
                "SecRule",
                "SecMarker",
                "SecAction",
                "SecDefaultAction",
                "SecComponentSignature",
                "SecResponseBodyAccess",
                "#",
            )
        )
        return b

    def _parse_comment(self):
        com = ""
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            if line.startswith("#"):
                com += line[1:]
                self.line_index += 1
            else:
                break
        return com

    def _parse_signature(self, line) -> SecComponentSignature:
        m = SecComponentSignature().load(
            {
                "schema_type": "SecComponentSignature",
                "msg": line.split('"')[1],
                "raw": line,
            }
        )
        self.line_index += 1
        return m

    def _parse_marker(self, line) -> SecMarker:
        m = SecMarker().load(
            {"schema_type": "SecMarker", "msg": line.split('"')[1], "raw": line}
        )
        self.line_index += 1
        return m

    def _parse_action(self, line) -> SecAction:
        a = SecAction().load({"schema_type": "SecAction", "raw": line})

        pattern = re.compile('"(.*)"')
        matcher = pattern.search(line)

        if matcher:
            rule_content = matcher.group(1)
            if rule_content:
                vars_list = rule_content.split(",")
                for token in vars_list:
                    key_pair = token.strip().split(":")
                    key_pair[0] = key_pair[0].strip()
                    if len(key_pair) > 1:
                        key_pair[1] = key_pair[1].strip()
                        if key_pair[0] == "id":
                            a["code"] = int(key_pair[1])
                        elif key_pair[0] == "ver":
                            a["version"] = key_pair[1]
                        elif key_pair[0] == "phase":
                            a["phase"] = int(key_pair[1])
                    else:
                        if key_pair[0].lower() in ["pass", "deny", "block", "config"]:
                            a["action"] = key_pair[0]
                        elif "audit" in key_pair[0]:
                            a["audit_log"] = key_pair[0]
                        elif "log" in key_pair[0]:
                            a["logging"] = key_pair[0]

        self.line_index += 1
        return a

    def _parse_scope(self, scope):
        return [s.strip() for s in scope.split("|")]

    def _parse_rule(self, line, base_path) -> SecRule:
        fi = line.index(" ")
        rule = SecRule().load(
            {
                "schema_type": "SecRule",
                "scope": self._parse_scope(line[fi: line.index(" ", fi + 1)]),
                "tags": [],
                "chain_starter": False,
                "raw": line,
            }
        )

        rule_data = line[line.index(" ", fi + 1):]
        regex = re.compile('"(.*?)(?<!\\\\)"(?:\\s+"(.*)")?')

        matcher = regex.search(rule_data)
        if matcher:
            rule["attachment"] = self._parse_from_file(
                matcher.group(1), base_path=base_path
            )
            rule_content = matcher.group(2)
            if rule_content:
                for token in re.split(",(?=(?:[^']*'[^']*')*[^']*$)", rule_content):
                    self._process_rule_token(rule, token, line, rule_content)

        self.line_index += 1
        logger.debug(rule)

        return rule

    def _process_rule_token(self, rule, token, line, rule_content):
        key_pair = re.split(":(?=(?:[^']*'[^']*')*[^']*$)", token)

        if len(key_pair) > 1:
            self._process_rule_key(rule, key_pair[0].strip(), key_pair[1], line)
        else:
            self._process_rule_action(rule, token, rule_content)

    def _process_rule_key(self, rule, key, val, line):
        if key == "id":
            rule["code"] = int(val)
        elif key == "ver":
            rule["version"] = val
        elif key == "phase":
            rule["phase"] = int(val)
        elif key == "tag":
            rule["tags"].append(val.replace("'", ""))
        elif key == "logdata":
            rule["logdata"] = val
        elif key == "msg":
            rule["msg"] = val
        elif key == "severity":
            rule["severity"] = val

    def _process_rule_action(self, rule, token, rule_content):
        token = token.strip().replace(",", "")
        token_lower = token.lower()
        if token_lower in ["pass", "deny", "block", "config"]:
            rule["action"] = token
        elif "audit" in token_lower:
            rule["audit_log"] = token
        elif "log" in token_lower:
            rule["logging"] = token
        elif token_lower == "multimatch":
            rule["multi_match"] = True
        elif token_lower == "chain":
            rule["chain_starter"] = True
        elif token_lower == "capture":
            rule["capture"] = True
        else:
            logger.error(f"parseRule Unknown token [{token}] from {rule_content}")

    def _parse_from_file(self, source, base_path):
        if source:
            pattern = re.compile(r"@(pmFromFile|ipMatchFromFile|pmf) (.*)")
            m = pattern.search(source)
            if m:
                f_name = m.group(2)
                if f_name:
                    data_lines = []
                    with open(
                        f"{base_path}/{f_name}", "r", encoding=self.charset
                    ) as file:
                        file_content = file.readlines()
                        for line in file_content:
                            if not line.startswith("#"):
                                data_lines.append(line.strip())
                return "\n".join(data_lines)
        return None

    def _load_file(self, ruleset_file, base_path):
        e_lines = []
        self.c_line = 0
        with open(f"{base_path}/{ruleset_file}", "r", encoding="utf-8") as arq:
            file_content = arq.readlines()
            for line in file_content:
                self.c_line += 1
                r = ""
                line = line.rstrip("\r\n").strip()
                if line is not None and len(line) > 2:
                    if line.endswith("\\"):
                        r = line[:-1]
                    else:
                        r = line
                e_lines.append(r.lstrip())

        read_lines = []
        while e_lines:
            line = e_lines.pop(0)
            while e_lines:
                r_line = e_lines.pop(0)
                if self._is_com_break(r_line):
                    e_lines = [r_line] + e_lines
                    read_lines.append(line)
                    break
                else:
                    line += " " + r_line
            if len(line) > 1:
                read_lines.append(line)
        return read_lines

    def load(self, ruleset_name: str, base_path) -> List[SecBaseSchema]:
        logger.debug(ruleset_name)
        self.lines = self._load_file(ruleset_name, base_path=base_path)
        self.line_index = 0
        ruleset = []
        comment = ""
        chain_starter = False
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            if line.startswith("#"):
                comment = self._parse_comment()
            else:
                key = line.split(" ")[0]
                if key == "SecMarker":
                    m = self._parse_marker(line)
                    ruleset.append(m)
                elif key == "SecComponentSignature":
                    s = self._parse_signature(line)
                    ruleset.append(s)
                elif key == "SecAction":
                    a = self._parse_action(line)
                    ruleset.append(a)
                elif key == "SecRule":
                    r = self._parse_rule(line, base_path)
                    if chain_starter:
                        ruleset[-1]["raw"] += "\n" + r["raw"]
                    else:
                        r["comment"] = comment
                        ruleset.append(r)
                    chain_starter = r["chain_starter"]
                else:
                    logger.error(f"parseFile Unknown key [{key}] from {line}")
        logger.info(f"{ruleset_name}: {len(ruleset)} rules")
        return ruleset

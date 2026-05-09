#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Company security compliance pre-scan for Java, Node.js/TypeScript, and Python projects.

This script is a deterministic helper for the company-security-code-review skill.
It narrows review scope and maps findings to company clauses, but it does not
prove full compliance on its own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


INCLUDE_SUFFIXES = {
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".xml",
    ".properties",
    ".yml",
    ".yaml",
    ".json",
    ".env",
}
SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".gradle",
    ".mvn",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "target",
    "build",
    "out",
    "dist",
    "coverage",
    "node_modules",
    "__pycache__",
}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

SENSITIVE_WORD_PATTERN = r"(password|passwd|pwd|token|secret|access[_-]?key|private[_-]?key|api[_-]?key|client[_-]?secret|mobile|phone|email|mail|idcard|bankcard|session)"
SENSITIVE_ROUTE_PATTERN = re.compile(r"(?i)(password|token|secret|mobile|phone|email|mail|idcard|bankcard|session)")

MANUAL_REVIEW_ITEMS = [
    {
        "clauses": ["Checklist 1.8", "SS-006 4.15.4"],
        "title": "HTTPS / TLS 配置",
        "reason": "需要网关、反向代理、容器或运行配置才能确认 TLS 版本与套件。",
    },
    {
        "clauses": ["Checklist 5.3", "SS-006 4.5.3"],
        "title": "登录失败锁定与访问限制",
        "reason": "阈值、锁定策略和验证码触发逻辑常在网关、认证中心或运行配置中。",
    },
    {
        "clauses": ["Checklist 5.6", "SS-006 4.5.6"],
        "title": "多因素认证",
        "reason": "是否强制开启 MFA 往往依赖产品策略、租户配置和外部认证平台。",
    },
    {
        "clauses": ["Checklist 5.9", "SS-006 4.10", "SS-006 4.11"],
        "title": "短信 / 图形验证码策略",
        "reason": "频率、有效期、一次一用等要求需要运行态配置和联调验证。",
    },
    {
        "clauses": ["SS-006 4.6.5"],
        "title": "会话超时",
        "reason": "超时时间通常在配置中心、网关或容器参数中定义。",
    },
    {
        "clauses": ["SS-006 4.7.6"],
        "title": "开放端口收敛",
        "reason": "需要部署清单、容器暴露端口和网络策略才能确认。",
    },
    {
        "clauses": ["SS-006 4.8.1", "SS-006 4.8.2"],
        "title": "密码复杂度与定期轮换",
        "reason": "需要账号中心规则、AD 配置或运行态密码策略才能确认。",
    },
    {
        "clauses": ["SS-006 4.13.8", "SS-006 4.13.9"],
        "title": "文件服务器与目录执行权限",
        "reason": "需要服务器、对象存储和文件系统权限配置才能确认。",
    },
    {
        "clauses": ["SS-006 4.15.3"],
        "title": "KMS / 密钥托管",
        "reason": "代码可能只显示密文配置，是否真实接入 KMS 需要环境与平台信息。",
    },
]


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    confidence: float
    language: str
    file_path: str
    line_number: int
    evidence: str
    rationale: str
    remediation: str
    company_clauses: List[str]


@dataclass
class LineRule:
    rule_id: str
    title: str
    severity: str
    confidence: float
    pattern: re.Pattern[str]
    rationale: str
    remediation: str
    company_clauses: Sequence[str]
    languages: Sequence[str]
    skip_patterns: Sequence[re.Pattern[str]] | None = None


LINE_RULES = [
    LineRule(
        rule_id="hardcoded-secret",
        title="疑似硬编码敏感凭据",
        severity="high",
        confidence=0.9,
        pattern=re.compile(
            rf"(?i)[\w.-]*{SENSITIVE_WORD_PATTERN}[\w.-]*[^\n]{{0,40}}[:=][^\n]{{0,8}}[\"'][^\"']{{4,}}[\"']"
        ),
        skip_patterns=(
            re.compile(r"\$\{[^}]+\}"),
            re.compile(r"process\.env\."),
            re.compile(r"os\.environ|getenv\("),
            re.compile(r"ENC\("),
            re.compile(r"example|sample|dummy|mock", re.I),
        ),
        rationale="敏感凭据直接写入代码或配置，容易导致仓库泄露、环境串用和横向移动。",
        remediation="改为环境变量、密文配置或密钥管理系统，避免把真实凭据提交到仓库。",
        company_clauses=("Checklist 1.11", "Checklist 1.12", "SS-006 4.1.11", "SS-006 4.1.12", "SS-006 4.15.3"),
        languages=("java", "node", "python", "config"),
    ),
    LineRule(
        rule_id="java-sql-injection",
        title="疑似 SQL 注入",
        severity="critical",
        confidence=0.88,
        pattern=re.compile(r"(?i)(executeQuery|executeUpdate|execute|prepareStatement)\s*\([^\n]*\+[^\n]*\)"),
        rationale="SQL 语句或参数通过字符串拼接构造，存在注入风险。",
        remediation="改用参数化查询、预编译语句或 ORM 参数绑定，并保留服务端校验。",
        company_clauses=("Checklist 2.1", "Checklist 2.2", "Checklist 3.2", "SS-006 4.2.1", "SS-006 4.2.2", "SS-006 4.3.2"),
        languages=("java",),
    ),
    LineRule(
        rule_id="node-sql-injection",
        title="疑似 SQL 注入",
        severity="critical",
        confidence=0.84,
        pattern=re.compile(r"(?i)(sequelize\.query|\.query|\.execute)\s*\([^\n]*(\+|`[^\n]*\$\{)"),
        rationale="SQL 查询由拼接或模板插值构造，存在注入风险。",
        remediation="改用参数绑定、query placeholders 或 ORM 安全 API。",
        company_clauses=("Checklist 2.1", "Checklist 2.2", "Checklist 3.2", "SS-006 4.2.1", "SS-006 4.2.2", "SS-006 4.3.2"),
        languages=("node",),
    ),
    LineRule(
        rule_id="python-sql-injection",
        title="疑似 SQL 注入",
        severity="critical",
        confidence=0.84,
        pattern=re.compile(r"(?i)(cursor\.execute|execute)\s*\([^\n]*(f[\"']|\.format\(|%\s*\(|%\s*[a-zA-Z_])"),
        rationale="SQL 语句通过 f-string、format 或 `%` 格式化构造，存在注入风险。",
        remediation="改用参数化查询、ORM 绑定参数，并保留服务端校验。",
        company_clauses=("Checklist 2.1", "Checklist 2.2", "Checklist 3.2", "SS-006 4.2.1", "SS-006 4.2.2", "SS-006 4.3.2"),
        languages=("python",),
    ),
    LineRule(
        rule_id="java-command-injection",
        title="疑似命令注入",
        severity="critical",
        confidence=0.9,
        pattern=re.compile(r"(?i)(Runtime\.getRuntime\(\)\.exec|ProcessBuilder)\s*\([^\n]*(\+|\".*\")"),
        rationale="用户可控内容进入系统命令执行路径，可能导致主机被控。",
        remediation="避免把用户输入直接送入命令执行；必要时使用严格白名单和参数数组。",
        company_clauses=("Checklist 2.1", "Checklist 2.3", "SS-006 4.2.1", "SS-006 4.2.3"),
        languages=("java",),
    ),
    LineRule(
        rule_id="node-command-injection",
        title="疑似命令注入",
        severity="critical",
        confidence=0.88,
        pattern=re.compile(r"(?i)(execSync|exec|spawnSync|spawn)\s*\([^\n]*(\+|`[^\n]*\$\{)"),
        rationale="用户可控内容进入 `child_process` 执行路径，可能导致主机被控。",
        remediation="避免执行拼接命令；必要时使用参数数组和严格白名单。",
        company_clauses=("Checklist 2.1", "Checklist 2.3", "SS-006 4.2.1", "SS-006 4.2.3"),
        languages=("node",),
    ),
    LineRule(
        rule_id="python-command-injection",
        title="疑似命令注入",
        severity="critical",
        confidence=0.88,
        pattern=re.compile(r"(?i)(os\.system|subprocess\.(run|Popen|call|check_output|check_call))\s*\([^\n]*(shell\s*=\s*True|f[\"']|\+)"),
        rationale="用户可控内容进入 shell 或命令执行路径，可能导致主机被控。",
        remediation="避免 shell=True 和命令拼接；必要时使用参数数组和严格白名单。",
        company_clauses=("Checklist 2.1", "Checklist 2.3", "SS-006 4.2.1", "SS-006 4.2.3"),
        languages=("python",),
    ),
    LineRule(
        rule_id="java-open-redirect",
        title="疑似开放重定向",
        severity="high",
        confidence=0.82,
        pattern=re.compile(r"(?i)(sendRedirect|redirect:)[^\n]*(\+|url|next)"),
        rationale="重定向目标来自变量或输入，若无白名单校验，可能跳转到恶意站点。",
        remediation="对重定向地址做白名单校验，避免直接拼接或透传外部 URL。",
        company_clauses=("Checklist 2.4", "SS-006 4.2.4"),
        languages=("java",),
    ),
    LineRule(
        rule_id="node-open-redirect",
        title="疑似开放重定向",
        severity="high",
        confidence=0.8,
        pattern=re.compile(r"(?i)res\.redirect\s*\([^\n]*(req\.(query|body|params)|\+|`[^\n]*\$\{)"),
        rationale="重定向目标来自请求输入，若无白名单校验，可能跳转到恶意站点。",
        remediation="对重定向地址做白名单校验，避免直接透传用户输入。",
        company_clauses=("Checklist 2.4", "SS-006 4.2.4"),
        languages=("node",),
    ),
    LineRule(
        rule_id="python-open-redirect",
        title="疑似开放重定向",
        severity="high",
        confidence=0.8,
        pattern=re.compile(r"(?i)\bredirect\s*\([^\n]*(request\.(args|form)|f[\"']|\+)"),
        rationale="重定向目标来自请求输入，若无白名单校验，可能跳转到恶意站点。",
        remediation="对重定向地址做白名单校验，避免直接透传用户输入。",
        company_clauses=("Checklist 2.4", "SS-006 4.2.4"),
        languages=("python",),
    ),
    LineRule(
        rule_id="java-path-traversal",
        title="疑似路径穿越或不安全文件路径拼接",
        severity="high",
        confidence=0.82,
        pattern=re.compile(r"(?i)(new\s+(?:[\w.]+\.)?File|(?:[\w.]+\.)?FileInputStream|(?:[\w.]+\.)?FileOutputStream|Paths\.get|Path\.of|Files\.(read|write|copy|move))[^\n]*(\+|getOriginalFilename\(|getParameter\()"),
        rationale="文件路径由外部输入拼接，若缺少规范化和基目录校验，可能出现跨目录访问。",
        remediation="使用固定基目录 + normalize/startsWith 校验；优先改为 ID 索引访问文件。",
        company_clauses=("SS-006 4.13.10", "SS-006 4.13.11"),
        languages=("java",),
    ),
    LineRule(
        rule_id="node-path-traversal",
        title="疑似路径穿越或不安全文件路径拼接",
        severity="high",
        confidence=0.8,
        pattern=re.compile(r"(?i)(sendFile|fs\.(readFile|readFileSync|createReadStream|writeFile|writeFileSync|unlink|stat)|path\.(join|resolve))\s*\([^\n]*(req\.(params|query|body)|\+|`[^\n]*\$\{)"),
        rationale="文件路径由请求输入拼接，若缺少归一化与基目录校验，可能出现路径穿越。",
        remediation="使用固定基目录 + `path.resolve` 边界校验；优先改为 ID 索引访问。",
        company_clauses=("SS-006 4.13.10", "SS-006 4.13.11"),
        languages=("node",),
    ),
    LineRule(
        rule_id="python-path-traversal",
        title="疑似路径穿越或不安全文件路径拼接",
        severity="high",
        confidence=0.8,
        pattern=re.compile(r"(?i)(open|send_file|FileResponse|os\.path\.join|Path\()[^\n]*(request\.(args|form)|\+|f[\"'])"),
        rationale="文件路径由请求输入拼接，若缺少规范化和基目录校验，可能出现路径穿越。",
        remediation="使用固定基目录 + `resolve()` / `normpath` 边界校验；优先改为 ID 索引访问。",
        company_clauses=("SS-006 4.13.10", "SS-006 4.13.11"),
        languages=("python",),
    ),
    LineRule(
        rule_id="unsafe-deserialization-java",
        title="疑似不安全反序列化",
        severity="critical",
        confidence=0.84,
        pattern=re.compile(r"(?i)(ObjectInputStream|readObject\s*\(|XMLDecoder\s*\()"),
        rationale="对不可信输入做反序列化可能导致任意代码执行或对象污染。",
        remediation="避免反序列化不可信输入；优先改为 JSON 并限制允许类型。",
        company_clauses=("Checklist 3.2", "SS-006 4.13.7"),
        languages=("java",),
    ),
    LineRule(
        rule_id="unsafe-deserialization-python",
        title="疑似不安全反序列化",
        severity="critical",
        confidence=0.84,
        pattern=re.compile(r"(?i)(pickle\.loads|pickle\.load|yaml\.load\s*\()"),
        rationale="对不可信输入做 pickle / yaml 反序列化可能导致任意代码执行或对象污染。",
        remediation="避免对不可信输入使用 pickle/yaml.load，优先改为安全格式与白名单。",
        company_clauses=("Checklist 3.2", "SS-006 4.13.7"),
        languages=("python",),
    ),
    LineRule(
        rule_id="exception-leak-java",
        title="疑似异常信息泄露",
        severity="medium",
        confidence=0.84,
        pattern=re.compile(r"(?i)(printStackTrace\s*\(|return\s+e\.getMessage\s*\(|response\.getWriter\(\)\.(print|write)\s*\([^\n]*e\.)"),
        rationale="异常信息直接暴露给客户端或控制台，可能泄露堆栈、组件信息或敏感上下文。",
        remediation="使用统一异常处理和通用错误码，日志中保留必要诊断信息但避免客户端直出。",
        company_clauses=("Checklist 4.1", "SS-006 4.4.1", "SS-006 4.4.4"),
        languages=("java",),
    ),
    LineRule(
        rule_id="exception-leak-node",
        title="疑似异常信息泄露",
        severity="medium",
        confidence=0.8,
        pattern=re.compile(r"(?i)(res\.(send|json)\s*\([^\n]*(err|error)\.(message|stack)|console\.error\s*\([^\n]*(err|error)\.stack)"),
        rationale="异常对象或错误消息直接暴露给客户端或控制台，可能泄露内部实现细节。",
        remediation="返回统一错误码与通用消息，把详细堆栈留在受控日志中。",
        company_clauses=("Checklist 4.1", "SS-006 4.4.1", "SS-006 4.4.4"),
        languages=("node",),
    ),
    LineRule(
        rule_id="exception-leak-python",
        title="疑似异常信息泄露",
        severity="medium",
        confidence=0.8,
        pattern=re.compile(r"(?i)(return\s+str\s*\(\s*e\s*\)|print\s*\(\s*e\s*\)|logger\.exception\s*\()"),
        rationale="异常信息直接返回或打印，可能泄露堆栈、路径或内部细节。",
        remediation="返回统一错误码与通用消息，把详细诊断保留在受控日志。",
        company_clauses=("Checklist 4.1", "SS-006 4.4.1", "SS-006 4.4.4"),
        languages=("python",),
    ),
    LineRule(
        rule_id="sensitive-log",
        title="疑似敏感信息进入日志或控制台",
        severity="high",
        confidence=0.86,
        pattern=re.compile(rf"(?i)(logger\.(info|warn|error|debug)|console\.(log|error|warn)|System\.out|System\.err|print\s*\()[^\n]*{SENSITIVE_WORD_PATTERN}"),
        rationale="日志或控制台输出敏感信息，容易造成二次泄露和审计侧泄露。",
        remediation="移除敏感字段原值；必要时只保留脱敏或摘要信息。",
        company_clauses=("Checklist 1.2", "SS-006 4.12.1", "SS-006 4.8.9"),
        languages=("java", "node", "python"),
    ),
    LineRule(
        rule_id="weak-crypto-java",
        title="疑似弱加密或弱哈希算法",
        severity="high",
        confidence=0.88,
        pattern=re.compile(r"(?i)(MessageDigest\.getInstance\s*\(\s*\"(MD5|SHA-1)\"|Cipher\.getInstance\s*\(\s*\"(DES|RC4|AES/ECB)|\bMD5\b|\bSHA-1\b|\bDES\b|\bRC4\b)"),
        rationale="使用弱算法会降低密码与敏感数据保护能力。",
        remediation="密码类场景优先使用 PBKDF2/bcrypt/argon2；加密类场景使用安全算法与模式。",
        company_clauses=("Checklist 1.6", "SS-006 4.8.8", "SS-006 4.15.1"),
        languages=("java",),
    ),
    LineRule(
        rule_id="weak-crypto-node",
        title="疑似弱加密或弱哈希算法",
        severity="high",
        confidence=0.86,
        pattern=re.compile(r"(?i)createHash\s*\(\s*['\"](md5|sha1)['\"]\s*\)"),
        rationale="使用弱哈希算法会降低密码与敏感数据保护能力。",
        remediation="密码类场景优先使用 PBKDF2/bcrypt/scrypt/argon2。",
        company_clauses=("Checklist 1.6", "SS-006 4.8.8", "SS-006 4.15.1"),
        languages=("node",),
    ),
    LineRule(
        rule_id="weak-crypto-python",
        title="疑似弱加密或弱哈希算法",
        severity="high",
        confidence=0.86,
        pattern=re.compile(r"(?i)hashlib\.(md5|sha1)\s*\("),
        rationale="使用弱哈希算法会降低密码与敏感数据保护能力。",
        remediation="密码类场景优先使用 PBKDF2/bcrypt/argon2。",
        company_clauses=("Checklist 1.6", "SS-006 4.8.8", "SS-006 4.15.1"),
        languages=("python",),
    ),
    LineRule(
        rule_id="debug-artifact",
        title="疑似调试或测试残留",
        severity="low",
        confidence=0.72,
        pattern=re.compile(r"(?i)(System\.out\.println|console\.log|print\s*\(|todo.*debug|testOnly|mockPassword|debugEnabled\s*=\s*true|DEBUG\s*=\s*True)"),
        rationale="调试代码或测试开关残留在生产代码中，容易泄露内部实现或绕过正常流程。",
        remediation="删除调试输出和测试开关，确保生产构建不包含测试残留。",
        company_clauses=("SS-006 4.16.1",),
        languages=("java", "node", "python"),
    ),
]


class CompanyComplianceScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        if not self.project_root.exists():
            raise ValueError(f"项目路径不存在: {self.project_root}")

    def discover_files(self) -> List[Path]:
        files: List[Path] = []
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in INCLUDE_SUFFIXES and path.name != ".env":
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            normalized = str(path).replace("\\", "/")
            if any(part in normalized for part in ("/src/test/", "/tests/", "/__tests__/")):
                continue
            files.append(path)
        return files

    def scan(self) -> Dict[str, object]:
        files = self.discover_files()
        findings: List[Finding] = []
        for path in files:
            findings.extend(self.scan_file(path))

        findings = self._deduplicate(findings)
        findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.file_path, item.line_number))

        summary = {level: 0 for level in SEVERITY_ORDER}
        language_summary: Dict[str, int] = {}
        for item in findings:
            summary[item.severity] += 1
            language_summary[item.language] = language_summary.get(item.language, 0) + 1

        business_conclusion, gate_reason = self._compute_business_conclusion(summary)
        clause_matrix = self._build_clause_matrix(findings)

        return {
            "scan_info": {
                "project_path": str(self.project_root),
                "generated_at": datetime.now().isoformat(),
                "files_scanned": len(files),
                "summary": summary,
                "language_summary": language_summary,
            },
            "business_conclusion": business_conclusion,
            "gate_reason": gate_reason,
            "findings": [asdict(item) for item in findings],
            "clause_matrix": clause_matrix,
            "manual_review_items": MANUAL_REVIEW_ITEMS,
            "notice": "未发现问题不等于完全符合；该脚本只用于预扫描和证据收集。",
        }

    def scan_file(self, path: Path) -> List[Finding]:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []

        lines = content.splitlines()
        language = self._language_for_path(path)
        findings: List[Finding] = []
        findings.extend(self._scan_line_rules(path, lines, language))

        if language == "java":
            findings.extend(self._scan_sensitive_get_java(path, lines))
            findings.extend(self._scan_xxe_java(path, content, lines))
            findings.extend(self._scan_upload_java(path, content, lines))
            findings.extend(self._scan_zip_slip_java(path, content, lines))
            findings.extend(self._scan_cookie_java(path, content, lines))
            findings.extend(self._scan_missing_auth_java(path, content, lines))
            findings.extend(self._scan_insecure_random_java(path, content, lines))
            findings.extend(self._scan_id_access_java(path, content, lines))
            findings.extend(self._scan_ssrf_java(path, lines))
        elif language == "node":
            findings.extend(self._scan_sensitive_get_node(path, lines))
            findings.extend(self._scan_upload_node(path, content, lines))
            findings.extend(self._scan_cookie_node(path, content, lines))
            findings.extend(self._scan_missing_auth_node(path, lines))
            findings.extend(self._scan_insecure_random_node(path, content, lines))
            findings.extend(self._scan_ssrf_node(path, lines))
        elif language == "python":
            findings.extend(self._scan_sensitive_get_python(path, lines))
            findings.extend(self._scan_upload_python(path, content, lines))
            findings.extend(self._scan_cookie_python(path, content, lines))
            findings.extend(self._scan_missing_auth_python(path, lines))
            findings.extend(self._scan_insecure_random_python(path, content, lines))
            findings.extend(self._scan_ssrf_python(path, lines))

        return findings

    def _scan_line_rules(self, path: Path, lines: Sequence[str], language: str) -> List[Finding]:
        findings: List[Finding] = []
        for line_number, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line:
                continue
            for rule in LINE_RULES:
                if language not in rule.languages:
                    continue
                if not rule.pattern.search(line):
                    continue
                if rule.skip_patterns and any(pattern.search(line) for pattern in rule.skip_patterns):
                    continue
                findings.append(self._make_finding(rule, path, language, line_number, line))
        return findings

    def _scan_sensitive_get_java(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        mapping_pattern = re.compile(r"@GetMapping|RequestMethod\.GET")
        break_pattern = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)")
        findings: List[Finding] = []
        for index, line in enumerate(lines):
            if not mapping_pattern.search(line):
                continue
            window = self._route_window(lines, index, 8, break_pattern)
            if SENSITIVE_ROUTE_PATTERN.search(window):
                findings.append(
                    Finding(
                        rule_id="sensitive-get-parameter",
                        title="疑似通过 GET 传输敏感参数",
                        severity="high",
                        confidence=0.82,
                        language="java",
                        file_path=self._relative_path(path),
                        line_number=index + 1,
                        evidence=self._trim(lines[index]),
                        rationale="敏感字段出现在 GET 接口上下文中，可能通过 URL、日志或历史记录泄露。",
                        remediation="改为 POST 或更安全的提交方式，并避免在 URL 中暴露敏感字段。",
                        company_clauses=["Checklist 1.5", "SS-006 4.1.5", "Checklist 5.5"],
                    )
                )
        return findings

    def _scan_sensitive_get_node(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        route_pattern = re.compile(r"(?i)\b(app|router)\.get\s*\(")
        break_pattern = re.compile(r"(?i)\b(app|router)\.(get|post|put|delete)\s*\(")
        findings: List[Finding] = []
        for index, line in enumerate(lines):
            if not route_pattern.search(line):
                continue
            window = self._route_window(lines, index, 10, break_pattern)
            if "req.query" in window and SENSITIVE_ROUTE_PATTERN.search(window):
                findings.append(
                    Finding(
                        rule_id="sensitive-get-parameter",
                        title="疑似通过 GET 传输敏感参数",
                        severity="high",
                        confidence=0.8,
                        language="node",
                        file_path=self._relative_path(path),
                        line_number=index + 1,
                        evidence=self._trim(lines[index]),
                        rationale="敏感字段出现在 GET 路由与 `req.query` 上下文中，可能通过 URL 和日志泄露。",
                        remediation="改为 POST 或更安全的提交方式，并避免在 URL 中暴露敏感字段。",
                        company_clauses=["Checklist 1.5", "SS-006 4.1.5", "Checklist 5.5"],
                    )
                )
        return findings

    def _scan_sensitive_get_python(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        route_pattern = re.compile(r"(?i)@(app|router)\.get|@app\.route\([^\n]*methods\s*=\s*\[[^\]]*GET")
        break_pattern = re.compile(r"(?i)@(app|router)\.(get|post|put|delete)|@app\.route")
        findings: List[Finding] = []
        for index, line in enumerate(lines):
            if not route_pattern.search(line):
                continue
            window = self._route_window(lines, index, 12, break_pattern)
            if "request.args" in window and SENSITIVE_ROUTE_PATTERN.search(window):
                findings.append(
                    Finding(
                        rule_id="sensitive-get-parameter",
                        title="疑似通过 GET 传输敏感参数",
                        severity="high",
                        confidence=0.8,
                        language="python",
                        file_path=self._relative_path(path),
                        line_number=index + 1,
                        evidence=self._trim(lines[index]),
                        rationale="敏感字段出现在 GET 视图与 `request.args` 上下文中，可能通过 URL 和日志泄露。",
                        remediation="改为 POST 或更安全的提交方式，并避免在 URL 中暴露敏感字段。",
                        company_clauses=["Checklist 1.5", "SS-006 4.1.5", "Checklist 5.5"],
                    )
                )
        return findings

    def _scan_xxe_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        parser_tokens = ("DocumentBuilderFactory.newInstance()", "SAXParserFactory.newInstance()", "XMLInputFactory.newInstance()")
        secure_tokens = ("disallow-doctype-decl", "external-general-entities", "external-parameter-entities", "ACCESS_EXTERNAL_DTD", "ACCESS_EXTERNAL_SCHEMA")
        if not any(token in content for token in parser_tokens):
            return []
        if any(token in content for token in secure_tokens):
            return []
        line_number = self._find_line_number(lines, parser_tokens)
        return [
            Finding(
                rule_id="xxe-missing-hardening",
                title="疑似 XML 解析器未关闭外部实体",
                severity="high",
                confidence=0.8,
                language="java",
                file_path=self._relative_path(path),
                line_number=line_number,
                evidence=self._trim(lines[line_number - 1]),
                rationale="发现 XML 解析器初始化，但未看到关闭外部实体和外部资源访问的安全配置。",
                remediation="为 XML 解析器显式关闭 DTD/外部实体，并限制外部资源访问。",
                company_clauses=["Checklist 3.2", "SS-006 4.3.2"],
            )
        ]

    def _scan_upload_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "MultipartFile" not in content and "transferTo(" not in content and "getOriginalFilename(" not in content:
            return []
        type_checks = ("contentType", "MediaType", "allowedExtensions", "whitelist", "probeContentType", "magic")
        size_checks = ("getSize(", "maxSize", "sizeLimit", "MAX_UPLOAD", "fileSize")
        if any(token in content for token in type_checks) and any(token in content for token in size_checks):
            return []
        line_number = self._find_line_number(lines, ("MultipartFile", "transferTo(", "getOriginalFilename("))
        return [self._upload_finding(path, "java", line_number, self._trim(lines[line_number - 1]))]

    def _scan_upload_node(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "multer" not in content and "req.files" not in content and "req.file" not in content:
            return []
        if any(token in content for token in ("fileFilter", "limits", "maxSize", "mimetype", "contentType")):
            return []
        line_number = self._find_line_number(lines, ("multer", "req.files", "req.file"))
        return [self._upload_finding(path, "node", line_number, self._trim(lines[line_number - 1]))]

    def _scan_upload_python(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "UploadFile" not in content and "request.files" not in content:
            return []
        if any(token in content for token in ("content_type", "file.content_type", "MAX_CONTENT_LENGTH", "allowed_extensions", "magic")):
            return []
        line_number = self._find_line_number(lines, ("UploadFile", "request.files"))
        return [self._upload_finding(path, "python", line_number, self._trim(lines[line_number - 1]))]

    def _upload_finding(self, path: Path, language: str, line_number: int, evidence: str) -> Finding:
        return Finding(
            rule_id="upload-missing-validation",
            title="疑似上传流程缺少类型或大小校验",
            severity="high",
            confidence=0.76,
            language=language,
            file_path=self._relative_path(path),
            line_number=line_number,
            evidence=evidence,
            rationale="检测到文件上传逻辑，但未看到同时覆盖文件类型白名单和大小限制的服务端校验。",
            remediation="补充扩展名 / 内容类型 / 文件头校验、大小上限和异常路径清理逻辑。",
            company_clauses=["SS-006 4.13.1", "SS-006 4.13.2", "SS-006 4.13.3", "SS-006 4.13.4", "SS-006 4.13.5", "SS-006 4.13.6"],
        )

    def _scan_zip_slip_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "ZipInputStream" not in content and "ZipEntry" not in content:
            return []
        if "getName()" not in content:
            return []
        if any(token in content for token in ("normalize()", "getCanonicalPath()", ".startsWith(")):
            return []
        line_number = self._find_line_number(lines, ("ZipInputStream", "ZipEntry", "getName()"))
        return [
            Finding(
                rule_id="zip-slip",
                title="疑似压缩包解压缺少路径校验",
                severity="high",
                confidence=0.82,
                language="java",
                file_path=self._relative_path(path),
                line_number=line_number,
                evidence=self._trim(lines[line_number - 1]),
                rationale="发现 zip 解压逻辑，但未看到路径规范化或目标目录边界校验，可能导致 Zip Slip。",
                remediation="对解压目标路径做 normalize/canonicalPath 校验，并限制总大小、文件数量和文件名。",
                company_clauses=["SS-006 4.13.7", "SS-006 4.13.10"],
            )
        ]

    def _scan_cookie_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        cookie_tokens = ("new Cookie(", "ResponseCookie.from(", "addCookie(")
        if not any(token in content for token in cookie_tokens):
            return []
        if ("HttpOnly" in content or "httpOnly(" in content) and ("setSecure(" in content or "secure(" in content):
            return []
        line_number = self._find_line_number(lines, cookie_tokens)
        return [self._cookie_finding(path, "java", line_number, self._trim(lines[line_number - 1]))]

    def _scan_cookie_node(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "res.cookie(" not in content:
            return []
        if "httpOnly" in content and "secure" in content:
            return []
        line_number = self._find_line_number(lines, ("res.cookie(",))
        return [self._cookie_finding(path, "node", line_number, self._trim(lines[line_number - 1]))]

    def _scan_cookie_python(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "set_cookie(" not in content:
            return []
        if "httponly" in content and "secure" in content:
            return []
        line_number = self._find_line_number(lines, ("set_cookie(",))
        return [self._cookie_finding(path, "python", line_number, self._trim(lines[line_number - 1]))]

    def _cookie_finding(self, path: Path, language: str, line_number: int, evidence: str) -> Finding:
        return Finding(
            rule_id="cookie-flags-missing",
            title="疑似 Cookie 缺少 HttpOnly 或 Secure",
            severity="medium",
            confidence=0.72,
            language=language,
            file_path=self._relative_path(path),
            line_number=line_number,
            evidence=evidence,
            rationale="发现 Cookie 创建逻辑，但未看到同时设置 HttpOnly 和 Secure。",
            remediation="为会话和敏感 Cookie 同时设置 HttpOnly 与 Secure，并优先限制 SameSite。",
            company_clauses=["SS-006 4.6.6"],
        )

    def _scan_missing_auth_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "@RestController" not in content and "@Controller" not in content:
            return []
        if any(keyword in content for keyword in ("@PreAuthorize", "@Secured", "@RolesAllowed", "SecurityContextHolder", "hasRole(", "hasAuthority(")):
            return []
        mapping_pattern = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)")
        risky_pattern = re.compile(r"(?i)(delete|remove|update|reset|grant|audit|export|download|upload|admin)")
        for index, line in enumerate(lines):
            if not mapping_pattern.search(line):
                continue
            window = "\n".join(lines[index : index + 4])
            if re.search(r"(?i)(login|logout|register|captcha|sms|verify)", window):
                continue
            if risky_pattern.search(window):
                return [self._missing_auth_finding(path, "java", index + 1, self._trim(lines[index]))]
        return []

    def _scan_missing_auth_node(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        route_pattern = re.compile(r"(?i)\b(app|router)\.(get|post|put|delete)\s*\(")
        risky_pattern = re.compile(r"(?i)(delete|remove|update|reset|grant|audit|export|download|upload|admin)")
        auth_pattern = re.compile(r"(?i)(auth|authorize|permission|guard|jwt|passport|requireRole|requireAuth)")
        for index, line in enumerate(lines):
            if not route_pattern.search(line):
                continue
            if auth_pattern.search(line):
                continue
            if risky_pattern.search(line):
                return [self._missing_auth_finding(path, "node", index + 1, self._trim(lines[index]))]
        return []

    def _scan_missing_auth_python(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        route_pattern = re.compile(r"(?i)@(app|router)\.(get|post|put|delete)|@app\.route")
        risky_pattern = re.compile(r"(?i)(delete|remove|update|reset|grant|audit|export|download|upload|admin)")
        auth_pattern = re.compile(r"(?i)(login_required|permission_classes|Depends\(|@permission|@auth|is_authenticated)")
        for index, line in enumerate(lines):
            if not route_pattern.search(line):
                continue
            if auth_pattern.search(line):
                continue
            window = "\n".join(lines[index : index + 5])
            if risky_pattern.search(window):
                return [self._missing_auth_finding(path, "python", index + 1, self._trim(lines[index]))]
        return []

    def _missing_auth_finding(self, path: Path, language: str, line_number: int, evidence: str) -> Finding:
        return Finding(
            rule_id="missing-auth-on-sensitive-endpoint",
            title="敏感接口未见显式鉴权线索",
            severity="high",
            confidence=0.65,
            language=language,
            file_path=self._relative_path(path),
            line_number=line_number,
            evidence=evidence,
            rationale="入口中出现敏感操作关键词，但当前代码路径未见显式权限注解、中间件或依赖鉴权线索。",
            remediation="为敏感接口补充服务端鉴权、对象级授权和必要的二次校验。",
            company_clauses=["Checklist 5.1", "Checklist 5.2", "SS-006 4.5.1", "SS-006 4.5.2", "SS-006 4.7.1", "SS-006 4.7.2"],
        )

    def _scan_insecure_random_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "SecureRandom" in content:
            return []
        random_pattern = re.compile(r"Math\.random\(|new\s+Random\s*\(")
        context_pattern = re.compile(r"(?i)(token|captcha|salt|nonce|otp|session|secret|iv|code)")
        if not context_pattern.search(content):
            return []
        for line_number, line in enumerate(lines, 1):
            if random_pattern.search(line):
                return [self._random_finding(path, "java", line_number, self._trim(line))]
        return []

    def _scan_insecure_random_node(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "crypto.randomBytes" in content or "crypto.randomUUID" in content:
            return []
        if not re.search(r"(?i)(token|captcha|salt|nonce|otp|session|secret|resetCode|verificationCode)", content):
            return []
        for line_number, line in enumerate(lines, 1):
            if "Math.random(" in line:
                return [self._random_finding(path, "node", line_number, self._trim(line))]
        return []

    def _scan_insecure_random_python(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "secrets." in content or "os.urandom" in content:
            return []
        if not re.search(r"(?i)(token|captcha|salt|nonce|otp|session|secret|reset_code|verification_code)", content):
            return []
        for line_number, line in enumerate(lines, 1):
            if re.search(r"(?i)\brandom\.(random|randint|choice|choices)\s*\(", line):
                return [self._random_finding(path, "python", line_number, self._trim(line))]
        return []

    def _random_finding(self, path: Path, language: str, line_number: int, evidence: str) -> Finding:
        return Finding(
            rule_id="insecure-random",
            title="安全场景疑似使用弱随机数",
            severity="high",
            confidence=0.78,
            language=language,
            file_path=self._relative_path(path),
            line_number=line_number,
            evidence=evidence,
            rationale="在 token、验证码、盐值等安全场景下使用弱随机数，随机性不足。",
            remediation="改用安全随机数 API，并检查长度、熵和编码方式是否满足要求。",
            company_clauses=["Checklist 6.1", "SS-006 4.6.9", "SS-006 4.15.5"],
        )

    def _scan_id_access_java(self, path: Path, content: str, lines: Sequence[str]) -> List[Finding]:
        if "@PathVariable" not in content and "@RequestParam" not in content:
            return []
        if "findById(" not in content and "getById(" not in content and "selectById(" not in content:
            return []
        if any(keyword in content for keyword in ("@PreAuthorize", "@Secured", "@RolesAllowed", "hasRole(", "hasAuthority(")):
            return []
        for index, line in enumerate(lines):
            if ("@PathVariable" in line or "@RequestParam" in line) and re.search(r"(?i)\bid\b", line):
                return [
                    Finding(
                        rule_id="guessable-id-access",
                        title="资源 ID 访问链路疑似缺少对象级校验",
                        severity="medium",
                        confidence=0.62,
                        language="java",
                        file_path=self._relative_path(path),
                        line_number=index + 1,
                        evidence=self._trim(line),
                        rationale="发现直接使用 `id` 读取对象的链路，且当前文件未见显式对象级鉴权线索。",
                        remediation="为资源访问补充对象级授权校验，必要时使用不可遍历 ID 或 UUID。",
                        company_clauses=["SS-006 4.7.2", "SS-006 4.14.2"],
                    )
                ]
        return []

    def _scan_ssrf_java(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        pattern = re.compile(r"(?i)(RestTemplate|WebClient|HttpClient|new\s+URL|URI\.create)[^\n]*(\+|url\b|uri\b|getParameter\()")
        return self._scan_pattern_findings(path, lines, pattern, "java", "ssrf-candidate")

    def _scan_ssrf_node(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        pattern = re.compile(r"(?i)(axios\.(get|post|request)|fetch|got)\s*\([^\n]*(req\.(query|body|params)|\+|`[^\n]*\$\{|url\b|uri\b)")
        return self._scan_pattern_findings(path, lines, pattern, "node", "ssrf-candidate")

    def _scan_ssrf_python(self, path: Path, lines: Sequence[str]) -> List[Finding]:
        pattern = re.compile(r"(?i)(requests\.(get|post|request|put|delete)|httpx\.(get|post|request))\s*\([^\n]*(request\.(args|form)|\+|f[\"']|url\b)")
        return self._scan_pattern_findings(path, lines, pattern, "python", "ssrf-candidate")

    def _scan_pattern_findings(self, path: Path, lines: Sequence[str], pattern: re.Pattern[str], language: str, rule_id: str) -> List[Finding]:
        findings: List[Finding] = []
        for line_number, line in enumerate(lines, 1):
            if pattern.search(line):
                findings.append(
                    Finding(
                        rule_id=rule_id,
                        title="疑似外部请求地址可控",
                        severity="high",
                        confidence=0.72,
                        language=language,
                        file_path=self._relative_path(path),
                        line_number=line_number,
                        evidence=self._trim(line),
                        rationale="外部请求目标地址来自变量或输入，若无白名单和内网限制，存在 SSRF 风险。",
                        remediation="对外部 URL 做协议、域名、网段白名单校验，并阻断内网与保留地址访问。",
                        company_clauses=["Checklist 2.1", "Checklist 2.2", "SS-006 4.2.1", "SS-006 4.2.2"],
                    )
                )
        return findings

    def _make_finding(self, rule: LineRule, path: Path, language: str, line_number: int, evidence: str) -> Finding:
        return Finding(
            rule_id=rule.rule_id,
            title=rule.title,
            severity=rule.severity,
            confidence=rule.confidence,
            language=language,
            file_path=self._relative_path(path),
            line_number=line_number,
            evidence=self._trim(evidence),
            rationale=rule.rationale,
            remediation=rule.remediation,
            company_clauses=list(rule.company_clauses),
        )

    def _deduplicate(self, findings: Iterable[Finding]) -> List[Finding]:
        unique: Dict[tuple, Finding] = {}
        for item in findings:
            key = (item.rule_id, item.file_path, item.line_number, item.evidence)
            unique[key] = item
        return list(unique.values())

    @staticmethod
    def _compute_business_conclusion(summary: Dict[str, int]) -> tuple[str, str]:
        if summary["critical"] > 0 or summary["high"] > 0:
            return "不通过", "命中 critical / high 风险源码问题，不能作为发布放行依据。"
        if summary["medium"] > 0:
            return "有条件通过", "未命中 high 风险，但存在 medium 风险问题，需要整改并结合人工审计继续确认。"
        return "通过", "未命中高信号风险规则；仍需结合人工语义审计和运行态核验，不代表全部条款自动符合。"

    @staticmethod
    def _build_clause_matrix(findings: Sequence[Finding]) -> List[Dict[str, str]]:
        matrix: Dict[str, Dict[str, str]] = {}
        for item in findings:
            for clause in item.company_clauses:
                row = matrix.setdefault(
                    clause,
                    {
                        "category": CompanyComplianceScanner._categorize_clause(clause),
                        "clause": clause,
                        "status": "不符合",
                        "evidence": f"{item.file_path}:{item.line_number}",
                        "note": item.title,
                    },
                )
                if row["status"] != "不符合":
                    row["status"] = "不符合"
                    row["evidence"] = f"{item.file_path}:{item.line_number}"
                    row["note"] = item.title
        for item in MANUAL_REVIEW_ITEMS:
            for clause in item["clauses"]:
                matrix.setdefault(
                    clause,
                    {
                        "category": CompanyComplianceScanner._categorize_clause(clause),
                        "clause": clause,
                        "status": "需人工确认",
                        "evidence": "-",
                        "note": item["reason"],
                    },
                )
        return sorted(matrix.values(), key=lambda row: row["clause"])

    @staticmethod
    def _categorize_clause(clause: str) -> str:
        text = clause.lower()
        if "4.1" in text or "4.12" in text or "checklist 1." in text:
            return "敏感信息"
        if "4.2" in text or "4.3" in text or "checklist 2." in text or "checklist 3." in text:
            return "输入校验 / 输出编码"
        if "4.4" in text or "4.16" in text or "checklist 4." in text:
            return "异常处理 / 日志"
        if "4.5" in text or "4.6" in text or "4.7" in text or "checklist 5." in text or "checklist 6." in text:
            return "认证 / 会话 / 访问控制"
        if "4.8" in text or "4.15" in text:
            return "密码 / 加密 / 随机数"
        if "4.13" in text or "4.14" in text:
            return "文件上传下载 / 接口安全"
        return "其他"

    def _relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    @staticmethod
    def _find_line_number(lines: Sequence[str], tokens: Sequence[str]) -> int:
        for index, line in enumerate(lines, 1):
            if any(token in line for token in tokens):
                return index
        return 1

    @staticmethod
    def _trim(text: str, limit: int = 220) -> str:
        stripped = text.strip()
        if len(stripped) <= limit:
            return stripped
        return stripped[: limit - 3] + "..."

    @staticmethod
    def _route_window(lines: Sequence[str], start_index: int, max_lines: int, break_pattern: re.Pattern[str]) -> str:
        collected = [lines[start_index]]
        for offset in range(1, max_lines):
            idx = start_index + offset
            if idx >= len(lines):
                break
            current = lines[idx]
            if break_pattern.search(current):
                break
            collected.append(current)
        return "\n".join(collected)

    @staticmethod
    def _language_for_path(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".java":
            return "java"
        if suffix in {".js", ".jsx", ".ts", ".tsx"}:
            return "node"
        if suffix == ".py":
            return "python"
        return "config"


def render_markdown(report: Dict[str, object]) -> str:
    scan_info = report["scan_info"]
    findings = report["findings"]
    clause_matrix = report["clause_matrix"]
    manual_review_items = report["manual_review_items"]

    lines = [
        "# 公司安全规范预扫描报告",
        "",
        f"- 项目路径: `{scan_info['project_path']}`",
        f"- 生成时间: `{scan_info['generated_at']}`",
        f"- 扫描文件数: `{scan_info['files_scanned']}`",
        f"- 语言命中统计: `{scan_info['language_summary']}`",
        f"- 注意: {report['notice']}",
        "",
        "## 总体结论",
        "",
        f"- 业务结论: `{report['business_conclusion']}`",
        f"- 结论依据: {report['gate_reason']}",
        "",
        "## 风险统计",
        "",
    ]
    for level in ("critical", "high", "medium", "low"):
        lines.append(f"- `{level}`: {scan_info['summary'][level]}")

    if not findings:
        lines.extend(["", "## 明确不符合项", "", "未命中明确的高信号规则。请继续做人工语义审计，这不代表已经符合公司规范。"])
    else:
        lines.extend(["", "## 明确不符合项", ""])
        for item in findings:
            lines.extend(
                [
                    f"### [{item['severity']}] {item['title']}",
                    f"- 语言: `{item['language']}`",
                    f"- 文件: `{item['file_path']}:{item['line_number']}`",
                    f"- 条款: `{', '.join(item['company_clauses'])}`",
                    f"- 证据: `{item['evidence']}`",
                    f"- 原因: {item['rationale']}",
                    f"- 建议: {item['remediation']}",
                    "",
                ]
            )

    lines.extend(["## 条款矩阵", ""])
    lines.append("| 类别 | 条款 | 状态 | 证据 | 说明 |")
    lines.append("| --- | --- | --- | --- | --- |")
    if clause_matrix:
        for row in clause_matrix:
            lines.append(
                f"| {row['category']} | `{row['clause']}` | {row['status']} | {row['evidence']} | {row['note']} |"
            )
    else:
        lines.append("| 其他 | - | 需人工确认 | - | 预扫描未命中明确反例，需继续结合源码语义审计输出完整矩阵。 |")
    lines.append("")

    lines.extend(["## 需人工确认", ""])
    for item in manual_review_items:
        lines.append(f"- `{', '.join(item['clauses'])}` {item['title']}: {item['reason']}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Company security compliance pre-scan for Java, Node.js/TypeScript, and Python projects")
    parser.add_argument("project_path", help="项目目录路径")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    args = parser.parse_args()

    try:
        report = CompanyComplianceScanner(args.project_path).scan()
    except Exception as exc:
        print(f"扫描失败: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    rendered = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + ("" if rendered.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(rendered)

    if report["business_conclusion"] == "不通过":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Stdlib CLI adapter for local DCinside scraper execution."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import shlex
import signal
import sys
import tempfile
import traceback
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from pydantic import ValidationError

from dcinside_scraper.core.api import resume_job, run_job
from dcinside_scraper.core.errors import ErrorMapper, ScraperError, StorageFailureError, ValidationFailure
from dcinside_scraper.http import HttpClient, HttpRuntimeConfig, ProxyConfig, UserAgentConfig
from dcinside_scraper.models.enums import (
    DcconMode,
    GalleryType,
    IntegratedSearchSort,
    JobReportStatus,
    JobType,
    MediaMode,
)
from dcinside_scraper.models.job import (
    DeepSearchSource,
    DirectPostSource,
    GallerySearchSource,
    IntegratedSearchSource,
    JobConfig,
    NoKeywordRangeSource,
    RangeFilter,
    RealtimeAllSource,
    RealtimeKeywordSource,
    RealtimeOptions,
    ResumeRequest,
    ScrapeOptions,
    StorageConfig,
    WorkerConfig,
)
from dcinside_scraper.outputs import LocalCheckpointStore, LocalOutputStore, OutputRunLayout
from dcinside_scraper.post_detail import PostDetailService
from dcinside_scraper.runner import JobRunner
from dcinside_scraper.search import LinkCollectorService

EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_VALIDATION_ERROR = 2

SOURCE_CHOICES = ("direct-post", "gallery-search", "integrated-search", "deep-search", "no-keyword-range")
SOURCE_ALIASES = {choice: choice.replace("-", "_") for choice in SOURCE_CHOICES}
SOURCE_ALIASES.update({value: value for value in SOURCE_ALIASES.values()})
PROXY_ENV_KEYS = ("DCINSIDE_PROXY_HOST", "DCINSIDE_PROXY_ID", "DCINSIDE_PROXY_PW")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dcinside-scraper")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    run = subcommands.add_parser("run", help="run one scrape job")
    run.add_argument("--source", choices=SOURCE_CHOICES)
    run.add_argument("--job-id")
    run.add_argument("--url", dest="urls", action="append")
    run.add_argument("--gallery-type", choices=[item.value for item in GalleryType])
    run.add_argument("--gallery-id")
    run.add_argument("--s-type", default="search_subject_memo")
    run.add_argument("--keyword")
    run.add_argument("--page", type=int, default=1)
    run.add_argument("--search-pos")
    run.add_argument("--head-id")
    run.add_argument("--sort-mode", choices=[item.value for item in IntegratedSearchSort], default=IntegratedSearchSort.RELEVANCE.value)
    run.add_argument("--page-start", type=int, default=1)
    run.add_argument("--page-end", type=int, default=1)
    run.add_argument("--seed-sort-mode", choices=[item.value for item in IntegratedSearchSort], default=IntegratedSearchSort.RELEVANCE.value)
    _add_range_options(run)
    _add_runtime_options(run)

    resume = subcommands.add_parser("resume", help="resume from local checkpoint")
    resume.add_argument("--job-id")
    _add_runtime_options(resume)

    import_uas = subcommands.add_parser("import-user-agents", help="copy a UTF-8 User-Agent list to ./user-agents.txt")
    import_uas.add_argument("source_path")

    proxy = subcommands.add_parser("configure-proxy", help="write proxy values to ./.env")
    proxy.add_argument("--host")
    proxy.add_argument("--id", dest="proxy_id")
    proxy.add_argument("--password", dest="proxy_pw")

    subcommands.add_parser("wizard", help="open a numbered terminal wizard")
    return parser


def _add_range_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--min-post-number", type=int)
    parser.add_argument("--max-post-number", type=int)


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-path")
    parser.add_argument("--image-mode", choices=[item.value for item in MediaMode])
    parser.add_argument("--dccon-mode", choices=[item.value for item in DcconMode])
    parser.add_argument("--include-comments", dest="include_comments", action="store_true", default=None)
    parser.add_argument("--no-comments", dest="include_comments", action="store_false")
    parser.add_argument("--request-interval-seconds", type=float)
    parser.add_argument("--post-worker-count", type=int)
    parser.add_argument("--queue-max-size", type=int)
    parser.add_argument("--max-comment-pages", type=int)
    parser.add_argument("--user-agent-file")
    parser.add_argument("--user-agent-rotate-every", type=int)
    parser.add_argument("--proxy-host")
    parser.add_argument("--proxy-id")
    parser.add_argument("--proxy-pw")


def normalize_command(value: argparse.Namespace | Mapping[str, Any]) -> dict[str, Any]:
    command = vars(value).copy() if isinstance(value, argparse.Namespace) else dict(value)
    if "command" in command and "subcommand" not in command:
        command["subcommand"] = command.pop("command")
    source = command.get("source")
    if source:
        command["source"] = normalize_source_name(str(source))
    return {key: value for key, value in command.items() if value is not None}


def normalize_source_name(value: str) -> str:
    try:
        return SOURCE_ALIASES[value]
    except KeyError as exc:
        raise ValidationFailure("unsupported source", details={"reason": "unsupported_source"}) from exc


def build_job_config(command: Mapping[str, Any], *, env: Mapping[str, str] | None = None) -> JobConfig:
    command = normalize_command(command)
    env = os.environ if env is None else env
    source = _build_realtime_source(command, env) if _env_true(env.get("DCINSIDE_REALTIME_ENABLED")) else _build_source(command)
    scrape_options = _build_scrape_options(command)
    return JobConfig(
        job_id=str(command.get("job_id") or _new_job_id()),
        job_type=JobType(source.type),
        source=source,
        scrape_options=scrape_options,
        worker_config=_build_worker_config(command),
        storage_config=StorageConfig(base_output_path=_blank_none(command.get("output_path"))),
    )


def build_resume_request(command: Mapping[str, Any]) -> ResumeRequest:
    command = normalize_command(command)
    return ResumeRequest(job_id=_blank_none(command.get("job_id")))


def _build_source(command: Mapping[str, Any]) -> Any:
    source_type = command.get("source")
    if not source_type:
        raise ValidationFailure("source is required", details={"reason": "source_required", "field_path": "source"})
    source_type = normalize_source_name(str(source_type))
    range_filter = _build_range_filter(command)

    if source_type == "direct_post":
        return DirectPostSource(urls=list(command.get("urls") or []))
    if source_type == "gallery_search":
        return GallerySearchSource(
            gallery_type=_gallery_type(_required(command, "gallery_type")),
            gallery_id=str(_required(command, "gallery_id")),
            s_type=str(command.get("s_type") or "search_subject_memo"),
            keyword=str(_required(command, "keyword")),
            page=int(command.get("page") or 1),
            search_pos=_blank_none(command.get("search_pos")),
            head_id=_blank_none(command.get("head_id")),
        )
    if source_type == "integrated_search":
        return IntegratedSearchSource(
            keyword=str(_required(command, "keyword")),
            sort_mode=IntegratedSearchSort(str(command.get("sort_mode") or IntegratedSearchSort.RELEVANCE.value)),
            page_start=int(command.get("page_start") or 1),
            page_end=int(command.get("page_end") or 1),
        )
    if source_type == "deep_search":
        return DeepSearchSource(
            keyword=str(_required(command, "keyword")),
            seed_sort_mode=IntegratedSearchSort(str(command.get("seed_sort_mode") or IntegratedSearchSort.RELEVANCE.value)),
            range_filter=range_filter or RangeFilter(),
        )
    if source_type == "no_keyword_range":
        return NoKeywordRangeSource(
            gallery_type=_gallery_type(_required(command, "gallery_type")),
            gallery_id=str(_required(command, "gallery_id")),
            range_filter=range_filter or RangeFilter(),
        )
    raise ValidationFailure("unsupported source", details={"reason": "unsupported_source"})


def _build_realtime_source(command: Mapping[str, Any], env: Mapping[str, str]) -> Any:
    if command.get("source"):
        raise ValidationFailure("realtime mode cannot be combined with --source", details={"reason": "realtime_source_conflict"})
    mode = _blank_none(env.get("DCINSIDE_REALTIME_MODE"))
    if mode not in {"keyword", "all"}:
        raise ValidationFailure("DCINSIDE_REALTIME_MODE must be keyword or all", details={"reason": "invalid_realtime_mode"})
    termination = _build_realtime_termination(env)
    poll_interval = float(_blank_none(env.get("DCINSIDE_REALTIME_POLL_INTERVAL_SECONDS")) or 30.0)

    if mode == "keyword":
        gallery_type = _blank_none(command.get("gallery_type"))
        gallery_id = _blank_none(command.get("gallery_id"))
        if (gallery_type is None) != (gallery_id is None):
            raise ValidationFailure("gallery_type and gallery_id must be provided together", details={"reason": "incomplete_gallery_scope"})
        return RealtimeKeywordSource(
            keyword=str(_required(env, "DCINSIDE_REALTIME_KEYWORD")),
            gallery_type=_gallery_type(gallery_type) if gallery_type else None,
            gallery_id=gallery_id,
            poll_interval_seconds=poll_interval,
            termination=termination,
        )

    return RealtimeAllSource(
        gallery_type=_gallery_type(_required(command, "gallery_type")),
        gallery_id=str(_required(command, "gallery_id")),
        poll_interval_seconds=poll_interval,
        termination=termination,
    )


def _build_realtime_termination(env: Mapping[str, str]) -> RealtimeOptions:
    duration = _blank_none(env.get("DCINSIDE_REALTIME_DURATION_SECONDS"))
    end_at = _blank_none(env.get("DCINSIDE_REALTIME_END_AT"))
    if (duration is None) == (end_at is None):
        raise ValidationFailure(
            "exactly one realtime termination condition is required",
            details={"reason": "invalid_realtime_termination"},
        )
    return RealtimeOptions(duration_seconds=int(duration) if duration else None, end_at=end_at)


def _build_range_filter(command: Mapping[str, Any]) -> RangeFilter | None:
    range_filter = RangeFilter(
        date_from=_blank_none(command.get("date_from")),
        date_to=_blank_none(command.get("date_to")),
        min_post_number=command.get("min_post_number"),
        max_post_number=command.get("max_post_number"),
    )
    return range_filter if range_filter.has_any_bound() else None


def _build_scrape_options(command: Mapping[str, Any]) -> ScrapeOptions:
    data: dict[str, Any] = {}
    for key in ("include_comments", "request_interval_seconds", "max_comment_pages"):
        if key in command:
            data[key] = command[key]
    if command.get("image_mode"):
        data["image_mode"] = MediaMode(str(command["image_mode"]))
    if command.get("dccon_mode"):
        data["dccon_mode"] = DcconMode(str(command["dccon_mode"]))
    range_filter = _build_range_filter(command)
    if range_filter:
        data["range_filter"] = range_filter
    return ScrapeOptions(**data)


def _build_worker_config(command: Mapping[str, Any]) -> WorkerConfig:
    data = {key: command[key] for key in ("post_worker_count", "queue_max_size") if key in command}
    return WorkerConfig(**data)


def build_local_runtime(command: Mapping[str, Any], *, job_id: str, storage_config: StorageConfig) -> tuple[HttpClient, JobRunner]:
    execution_dir = Path.cwd()
    request_interval = float(command.get("request_interval_seconds") or 1.0)
    proxy = None
    if command.get("proxy_host"):
        proxy = ProxyConfig.from_values(
            host=str(command.get("proxy_host") or ""),
            username=_blank_none(command.get("proxy_id")),
            password=_blank_none(command.get("proxy_pw")),
            source="cli",
        )
    client = HttpClient(
        HttpRuntimeConfig(
            request_interval_seconds=request_interval,
            user_agent=UserAgentConfig(
                explicit_file_path=_blank_none(command.get("user_agent_file")),
                rotation_interval_requests=int(command.get("user_agent_rotate_every") or 10),
            ),
            proxy=proxy,
            proxy_env_path=execution_dir / ".env",
            execution_dir=execution_dir,
        )
    )
    layout = OutputRunLayout.from_storage_config(storage_config, job_id=job_id, run_id=_new_run_id())
    runner = JobRunner(
        collector=LinkCollectorService(client),
        post_detail=PostDetailService(client),
        output_store=LocalOutputStore(layout),
        checkpoint_store=LocalCheckpointStore(storage_config.base_output_path),
    )
    return client, runner


async def run_scrape_command_async(
    command: Mapping[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    runner: Any | None = None,
    output: TextIO | None = None,
    error_output: TextIO | None = None,
) -> int:
    output = output or sys.stdout
    error_output = error_output or sys.stderr
    command = normalize_command(command)
    config = build_job_config(command, env=env)
    _print_start(config, output)
    client = None
    if runner is None:
        client, runner = build_local_runtime(command, job_id=config.job_id, storage_config=config.storage_config)
    try:
        with InterruptController(runner, output=error_output):
            report = await run_job(config, runner=runner)
    finally:
        if client is not None:
            await client.close()
    _print_report(report, config.storage_config.base_output_path, output)
    return _exit_code_for_report(report)


async def resume_scrape_command_async(
    command: Mapping[str, Any],
    *,
    runner: Any | None = None,
    output: TextIO | None = None,
    error_output: TextIO | None = None,
) -> int:
    output = output or sys.stdout
    error_output = error_output or sys.stderr
    command = normalize_command(command)
    request = build_resume_request(command)
    storage_config = StorageConfig(base_output_path=_blank_none(command.get("output_path")))
    client = None
    if runner is None:
        client, runner = build_local_runtime(command, job_id=request.job_id or "resume", storage_config=storage_config)
    try:
        with InterruptController(runner, output=error_output):
            report = await resume_job(request, runner=runner)
    finally:
        if client is not None:
            await client.close()
    _print_report(report, storage_config.base_output_path, output)
    return _exit_code_for_report(report)


def import_user_agents(source: str | Path, destination: str | Path) -> None:
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise ValidationFailure("User-Agent source file not found", details={"reason": "file_not_found"})
    try:
        text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationFailure("User-Agent source file must be UTF-8", details={"reason": "invalid_utf8"}) from exc
    if not any(line.strip() for line in text.splitlines()):
        raise ValidationFailure("User-Agent source file is blank", details={"reason": "blank_user_agent_file"})
    _atomic_write_text(destination_path, text)


def update_proxy_env(path: str | Path, values: Mapping[str, str | None]) -> None:
    target = Path(path)
    existing = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    remaining = {key: str(values.get(key) or "") for key in PROXY_ENV_KEYS}
    output_lines: list[str] = []

    for line in existing:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in PROXY_ENV_KEYS:
            if key in remaining:
                output_lines.append(f"{key}={remaining.pop(key)}")
            continue
        output_lines.append(line)
    output_lines.extend(f"{key}={value}" for key, value in remaining.items())
    _atomic_write_text(target, "\n".join(output_lines).rstrip("\n") + "\n")


class WizardSession:
    def __init__(self, input_stream: TextIO | None = None, output_stream: TextIO | None = None) -> None:
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout

    def collect_command(self) -> dict[str, Any] | None:
        self._write("1. 스크래핑 시작하기\n2. 이어서 실행하기\n3. User-Agent 가져오기\n4. Proxy 설정하기\n5. 종료\n")
        choice = self._ask("번호 입력: ")
        if choice == "1":
            return self._collect_run()
        if choice == "2":
            return {"subcommand": "resume", "job_id": self._optional("Job ID(비우면 최신 체크포인트): ")}
        if choice == "3":
            return {"subcommand": "import-user-agents", "source_path": self._ask("User-Agent 파일 경로: ")}
        if choice == "4":
            return {
                "subcommand": "configure-proxy",
                "host": self._ask("Proxy host: "),
                "proxy_id": self._optional("Proxy ID(선택): "),
                "proxy_pw": self._optional("Proxy PW(선택): "),
            }
        return None

    def _collect_run(self) -> dict[str, Any]:
        self._write("1. direct-post\n2. gallery-search\n3. integrated-search\n4. deep-search\n5. no-keyword-range\n")
        source = {
            "1": "direct_post",
            "2": "gallery_search",
            "3": "integrated_search",
            "4": "deep_search",
            "5": "no_keyword_range",
        }.get(self._ask("소스 번호: "), "direct_post")
        command: dict[str, Any] = {
            "subcommand": "run",
            "source": source,
            "job_id": self._optional("Job ID(선택): "),
            "output_path": self._optional("출력 경로(선택): "),
        }
        if source == "direct_post":
            command["urls"] = [self._ask("게시글 URL: ")]
        elif source in {"gallery_search", "no_keyword_range"}:
            command["gallery_type"] = self._ask("갤러리 타입(major/minor/mini): ")
            command["gallery_id"] = self._ask("갤러리 ID: ")
            if source == "gallery_search":
                command["keyword"] = self._ask("검색어: ")
            else:
                self._collect_range(command)
        elif source in {"integrated_search", "deep_search"}:
            command["keyword"] = self._ask("검색어: ")
            if source == "deep_search":
                self._collect_range(command)
        return {key: value for key, value in command.items() if value is not None and value != ""}

    def _collect_range(self, command: dict[str, Any]) -> None:
        command["date_from"] = self._optional("시작일 YYYY-MM-DD(선택): ")
        command["date_to"] = self._optional("종료일 YYYY-MM-DD(선택): ")
        command["min_post_number"] = _optional_int(self._optional("최소 글번호(선택): "))
        command["max_post_number"] = _optional_int(self._optional("최대 글번호(선택): "))

    def _ask(self, prompt: str) -> str:
        self._write(prompt)
        return self.input_stream.readline().strip()

    def _optional(self, prompt: str) -> str | None:
        return _blank_none(self._ask(prompt))

    def _write(self, text: str) -> None:
        self.output_stream.write(text)
        self.output_stream.flush()


class InterruptController:
    def __init__(self, runner: Any, *, output: TextIO | None = None) -> None:
        self.runner = runner
        self.output = output or sys.stderr
        self.count = 0
        self._previous: Any = None

    def __enter__(self) -> "InterruptController":
        self._previous = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        if self._previous is not None:
            signal.signal(signal.SIGINT, self._previous)
        return False

    def _handle(self, signum: int, frame: Any) -> None:
        self.count += 1
        if self.count == 1:
            if hasattr(self.runner, "request_stop"):
                self.runner.request_stop()
            self.output.write("Ctrl+C received. Graceful stop requested. Press Ctrl+C again to force exit.\n")
            self.output.flush()
            return
        raise KeyboardInterrupt


def print_error(exc: Exception, *, stage: str | None = None, output: TextIO | None = None, include_traceback: bool = True) -> None:
    output = output or sys.stderr
    mapped = ErrorMapper.map(exc, stage=stage)
    output.write(f"ERROR [{mapped.code}] {mapped.message}\n")
    for key, value in sorted(mapped.details.items()):
        output.write(f"{key}: {value}\n")
    if include_traceback:
        output.write("Traceback (most recent call last):\n")
        for line in traceback.format_tb(exc.__traceback__):
            output.write(line)
        output.write(f"{exc.__class__.__name__}: {mapped.message}\n")
    output.flush()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    command = normalize_command(args)
    try:
        return _dispatch_command(command)
    except (ValidationFailure, ValidationError) as exc:
        print_error(exc, stage=command.get("subcommand"))
        return EXIT_VALIDATION_ERROR
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted.\n")
        return EXIT_RUNTIME_ERROR
    except Exception as exc:
        print_error(exc, stage=command.get("subcommand"))
        return EXIT_RUNTIME_ERROR


def _dispatch_command(command: Mapping[str, Any]) -> int:
    subcommand = command.get("subcommand")
    if subcommand == "run":
        return asyncio.run(run_scrape_command_async(command))
    if subcommand == "resume":
        return asyncio.run(resume_scrape_command_async(command))
    if subcommand == "import-user-agents":
        import_user_agents(str(command["source_path"]), Path.cwd() / "user-agents.txt")
        print("Imported User-Agent file to user-agents.txt")
        return EXIT_SUCCESS
    if subcommand == "configure-proxy":
        _configure_proxy(command)
        print("Proxy profile saved to .env")
        return EXIT_SUCCESS
    if subcommand == "wizard":
        selected = WizardSession().collect_command()
        return EXIT_SUCCESS if selected is None else _dispatch_command(selected)
    raise ValidationFailure("unsupported command", details={"reason": "unsupported_command"})


def _configure_proxy(command: Mapping[str, Any]) -> None:
    print("Proxy credentials will be saved as plaintext in .env.")
    host = _blank_none(command.get("host")) or input("Proxy host: ").strip()
    if not host:
        raise ValidationFailure("proxy host is required", details={"reason": "proxy_host_required"})
    proxy_id = _blank_none(command.get("proxy_id")) or input("Proxy ID(optional): ").strip()
    proxy_pw = _blank_none(command.get("proxy_pw"))
    if proxy_pw is None:
        proxy_pw = getpass.getpass("Proxy PW(optional): ")
    update_proxy_env(
        Path.cwd() / ".env",
        {
            "DCINSIDE_PROXY_HOST": host,
            "DCINSIDE_PROXY_ID": proxy_id,
            "DCINSIDE_PROXY_PW": proxy_pw,
        },
    )


def _print_start(config: JobConfig, output: TextIO) -> None:
    output.write(f"job_id: {config.job_id}\n")
    output.write(f"source: {config.source.type}\n")
    output.write(f"output_path: {config.storage_config.base_output_path or str(Path.cwd())}\n")
    output.write(f"workers: {config.worker_config.post_worker_count}\n")
    output.write(f"request_interval_seconds: {config.scrape_options.request_interval_seconds}\n")
    output.flush()


def _print_report(report: Any, output_path: str | None, output: TextIO) -> None:
    output.write(f"status: {getattr(report.status, 'value', report.status)}\n")
    output.write(f"success_count: {report.success_count}\n")
    output.write(f"failure_count: {report.failure_count}\n")
    output.write(f"deduped_count: {report.deduped_count}\n")
    output.write(f"filtered_count: {report.filtered_count}\n")
    output.write(f"resume: {_resume_command(report.job_id, output_path)}\n")
    output.flush()


def _resume_command(job_id: str, output_path: str | None) -> str:
    parts = ["python", "-m", "dcinside_scraper.adapters.cli", "resume", "--job-id", job_id]
    if output_path:
        parts.extend(["--output-path", output_path])
    return " ".join(shlex.quote(part) for part in parts)


def _exit_code_for_report(report: Any) -> int:
    return EXIT_SUCCESS if report.status == JobReportStatus.COMPLETED else EXIT_RUNTIME_ERROR


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_name = file.name
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise StorageFailureError("file write failed", details={"stage": "cli_file", "reason": exc.__class__.__name__}) from exc


def _new_job_id() -> str:
    return f"job-{uuid.uuid4().hex[:12]}"


def _new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def _blank_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: str | None) -> int | None:
    return int(value) if value else None


def _required(source: Mapping[str, Any], key: str) -> Any:
    value = _blank_none(source.get(key))
    if value is None:
        raise ValidationFailure(f"{key} is required", details={"reason": "missing_required", "field_path": key})
    return value


def _gallery_type(value: Any) -> GalleryType:
    return GalleryType(str(value))


def _env_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())

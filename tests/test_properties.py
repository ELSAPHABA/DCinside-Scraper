from __future__ import annotations

from hypothesis import given, settings

from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.error import ErrorResult
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.post import PostResult
from tests.strategies.checkpoints import checkpoints
from tests.strategies.errors import error_results
from tests.strategies.job_configs import job_configs, range_filters
from tests.strategies.post_results import post_results


@given(job_configs())
@settings(max_examples=30)
def test_job_config_json_round_trip(config: JobConfig) -> None:
    dumped = config.model_dump(mode="json")
    loaded = JobConfig.model_validate(dumped)
    assert loaded.model_dump(mode="json") == dumped


@given(post_results())
@settings(max_examples=30)
def test_post_result_json_round_trip(post: PostResult) -> None:
    dumped = post.model_dump(mode="json")
    loaded = PostResult.model_validate(dumped)
    assert loaded.model_dump(mode="json") == dumped


@given(error_results())
@settings(max_examples=30)
def test_error_result_json_round_trip(error: ErrorResult) -> None:
    dumped = error.model_dump(mode="json")
    loaded = ErrorResult.model_validate(dumped)
    assert loaded.model_dump(mode="json") == dumped


@given(range_filters())
@settings(max_examples=30)
def test_range_filter_invariant(range_filter) -> None:
    assert range_filter.min_post_number <= range_filter.max_post_number


@given(post_results())
@settings(max_examples=30)
def test_content_order_invariant(post: PostResult) -> None:
    orders = [block.order for block in post.content]
    assert len(orders) == len(set(orders))


@given(post_results())
@settings(max_examples=30)
def test_repost_consistency_invariant(post: PostResult) -> None:
    assert (post.repost is not None) == post.is_repost


@given(checkpoints())
@settings(max_examples=30)
def test_checkpoint_status_reason_invariant(checkpoint: Checkpoint) -> None:
    if checkpoint.status == "stopped":
        assert checkpoint.reason is not None
    else:
        assert checkpoint.reason is None


@given(post_results(), checkpoints())
@settings(max_examples=30)
def test_schema_version_preservation(post: PostResult, checkpoint: Checkpoint) -> None:
    assert PostResult.model_validate(post.model_dump(mode="json")).schema_version == "dcinside.post.v1"
    assert Checkpoint.model_validate(checkpoint.model_dump(mode="json")).schema_version == "dcinside.checkpoint.v1"


from __future__ import annotations


def test_standard_collection_parse_runner_and_output_modules_are_importable() -> None:
    from dcinside_scraper.collect import GallerySearchUrlBuilder, LinkCollectorService
    from dcinside_scraper.collect.urls import parse_post_url
    from dcinside_scraper.outputs.checkpoint import LocalCheckpointStore
    from dcinside_scraper.outputs.jsonl import JsonlWriter
    from dcinside_scraper.outputs.layout import OutputRunLayout
    from dcinside_scraper.outputs.redaction import SafeFailureRecordBuilder
    from dcinside_scraper.parse import CommentService, ContentBlockParser, PostDetailService
    from dcinside_scraper.runner.checkpointing import CheckpointCoordinator
    from dcinside_scraper.runner.policies import candidate_post_key
    from dcinside_scraper.runner.service import JobRunner
    from dcinside_scraper.runner.workers import MediaDownloadCoordinator

    assert GallerySearchUrlBuilder
    assert LinkCollectorService
    assert parse_post_url
    assert CommentService
    assert ContentBlockParser
    assert PostDetailService
    assert CheckpointCoordinator
    assert JobRunner
    assert MediaDownloadCoordinator
    assert candidate_post_key
    assert LocalCheckpointStore
    assert JsonlWriter
    assert OutputRunLayout
    assert SafeFailureRecordBuilder

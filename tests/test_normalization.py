from __future__ import annotations

from dcinside_scraper.core.normalization import normalize_checkpoint, normalize_job_report
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.enums import CheckpointStatus, JobReportStatus, JobType, StopReason
from dcinside_scraper.models.job import JobConfig, PostCandidate, PostKey, SearchPosition
from dcinside_scraper.models.report import JobReport, StoredObjectRef


def _job() -> JobConfig:
    return JobConfig(
        job_id="job-1",
        job_type=JobType.GALLERY_SEARCH,
        source={
            "type": "gallery_search",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "s_type": "search_subject_memo",
            "keyword": "test",
        },
    )


def test_normalize_job_report_maps_dcinside_counts() -> None:
    report = JobReport(
        job_id="job-1",
        status=JobReportStatus.COMPLETED,
        success_count=2,
        failure_count=1,
        deduped_count=3,
        filtered_count=4,
        output_refs=[
            StoredObjectRef(
                uri="file:///outputs/job-1/run-9/posts.jsonl",
                storage_type="local",
                object_key="outputs/job-1/run-9/posts.jsonl",
            )
        ],
    )

    normalized = normalize_job_report(report, scraper_id="worker-a")

    assert normalized.schema_version == "community.run_report.v1"
    assert normalized.scraper_id == "worker-a"
    assert normalized.site_id == "dcinside"
    assert normalized.run_id == "run-9"
    assert normalized.candidate_seen_count == 10
    assert normalized.candidate_collected_count is None
    assert normalized.post_stored_count == 2
    assert normalized.failure_count == 1
    assert normalized.duplicate_skipped_count == 3
    assert normalized.range_filtered_count == 4
    assert normalized.output_ref_count == 1
    assert normalized.native_report["schema_version"] == "dcinside.job_report.v1"


def test_normalize_checkpoint_splits_completed_and_pending_rows() -> None:
    checkpoint = Checkpoint(
        job_id="job-1",
        status=CheckpointStatus.STOPPED,
        reason=StopReason.CAPTCHA,
        board_id="singlebungle1472",
        scraping_processed_count=7,
        worker_id="worker-1",
        job_config_snapshot=_job(),
        search_position=SearchPosition(page=3, search_pos="12345"),
        completed_keys=[PostKey(board_id="singlebungle1472", post_id="100")],
        remaining_queue=[
            PostCandidate(
                url="https://gall.dcinside.com/mgallery/board/view/?id=singlebungle1472&no=101",
                gallery_id="singlebungle1472",
                post_id="101",
            )
        ],
    )

    bundle = normalize_checkpoint(checkpoint)

    assert bundle.checkpoint.schema_version == "community.checkpoint.v1"
    assert bundle.checkpoint.collector_page == 3
    assert bundle.checkpoint.collector_board_id == "singlebungle1472"
    assert bundle.checkpoint.collector_cursor_value == "12345"
    assert bundle.checkpoint.last_completed_post_key == "dcinside:singlebungle1472:100"
    assert bundle.checkpoint.processed_count == 7
    assert bundle.checkpoint.worker_id == "worker-1"
    assert bundle.completed_posts[0].post_key == "dcinside:singlebungle1472:100"
    assert bundle.pending_queue[0].queue_order == 0
    assert bundle.pending_queue[0].post_id == "101"
    assert bundle.pending_queue[0].candidate_payload["gallery_id"] == "singlebungle1472"

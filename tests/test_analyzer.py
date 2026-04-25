from datetime import date

from src.core.models import AlertConfig, AnalysisFlag, Listing
from src.services.analyzer import OpportunityAnalyzer


def test_analyzer_notifies_recent_good_price_without_false_defect():
    analyzer = OpportunityAnalyzer()
    listing = Listing(
        external_id="111",
        title="iPhone 13 sem defeito",
        price_cents=230000,
        url="https://example.test/111",
        published_at=date(2026, 4, 25),
    )
    alert = AlertConfig(
        search_term="iphone 13",
        max_price_cents=250000,
        min_expected_price_cents=150000,
        max_age_days=30,
    )

    result = analyzer.analyze(listing, alert, today=date(2026, 4, 25))

    assert result.should_notify
    assert AnalysisFlag.RECENT in result.flags
    assert AnalysisFlag.GOOD_PRICE in result.flags
    assert AnalysisFlag.DEFECT_KEYWORD not in result.flags


def test_analyzer_flags_suspicious_listing_but_can_still_notify():
    analyzer = OpportunityAnalyzer()
    listing = Listing(
        external_id="222",
        title="iPhone 13 com defeito display",
        price_cents=90000,
        url="https://example.test/222",
        published_at=date(2026, 4, 20),
    )
    alert = AlertConfig(
        search_term="iphone 13",
        max_price_cents=250000,
        min_expected_price_cents=150000,
        max_age_days=30,
    )

    result = analyzer.analyze(listing, alert, today=date(2026, 4, 25))

    assert result.should_notify
    assert AnalysisFlag.LOW_PRICE_CAUTION in result.flags
    assert AnalysisFlag.SCAM_CAUTION in result.flags
    assert AnalysisFlag.DEFECT_KEYWORD in result.flags


def test_analyzer_does_not_notify_unknown_date_by_default():
    analyzer = OpportunityAnalyzer()
    listing = Listing(
        external_id="333",
        title="iPhone 13 barato",
        price_cents=200000,
        url="https://example.test/333",
        published_at=None,
    )
    alert = AlertConfig(search_term="iphone 13", max_price_cents=250000)

    result = analyzer.analyze(listing, alert, today=date(2026, 4, 25))

    assert not result.should_notify
    assert AnalysisFlag.UNKNOWN_DATE in result.flags

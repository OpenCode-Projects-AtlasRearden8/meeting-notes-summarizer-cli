from meeting_notes_summarizer.summarizer import summarize


def test_label_words_are_not_owners():
    report = summarize("Marcus: Nice. Todo: write the rollout checklist before launch.")
    (item,) = report.action_items
    assert item.owner == "Marcus"
    assert item.text == "write the rollout checklist before launch"


def test_delegated_request_becomes_action_item():
    report = summarize("Dana: Priya, can you draft the announcement email?")
    (item,) = report.action_items
    assert item.owner == "Priya"
    assert "draft the announcement email" in item.text


def test_speaker_prefix_does_not_steal_ownership():
    report = summarize("Dana: Action item: Marcus will wire up the progress bar by Friday.")
    (item,) = report.action_items
    assert item.owner == "Marcus"
    assert item.text.startswith("Wire up")


def test_acknowledgements_are_skipped():
    report = summarize("Marcus: Will do. Dana: Okay, sounds good.")
    assert report.action_items == []

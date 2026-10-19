from satquery.agent.parser import QueryUnderstandingBackend

def parse(q):
    return QueryUnderstandingBackend().parse(q).operation

def test_operations():
    assert parse("What changed between the two images?") == "change_analysis"
    assert parse("Fuse the SAR and optical scenes") == "optical_sar_fusion"
    assert parse("Which sensor captured this?") == "metadata_query"
    assert parse("Count the ships in the harbor") == "image_question_answering"

def test_whole_word_matching():
    # "necessary" contains "sar"; "exchange" contains "change".
    assert parse("Is optical cloud masking necessary here?") == "image_question_answering"
    assert parse("Is there a currency exchange building?") == "image_question_answering"

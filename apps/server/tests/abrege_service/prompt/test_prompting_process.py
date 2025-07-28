from abrege_service.prompts.prompting import generate_prompt


def test_promting_jinja():
    # Pour le résumé d'un segment
    segment_prompt = generate_prompt(
        "segement_summary_promt.jinja2",
        {"size": 100, "language": "français", "text": "coco"},
    )
    segment_prompt = segment_prompt.replace("\n", "")
    expected_segment_prompt = "Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte.Le résumé doit faire moins de 100 mots.Le résumé doit être en français.Texte : coco"
    expected_segment_prompt = expected_segment_prompt.replace("\n", "")
    assert segment_prompt == expected_segment_prompt

    # Pour la synthèse finale
    final_prompt = generate_prompt(
        "final_summary_prompt.jinja2",
        {"size": 300, "language": "français", "summaries": ["test1", "test2"]},
    )
    final_prompt = final_prompt.replace("\n", "")
    expected_final_prompt = "Vous êtes un expert en synthèse de documents. En vous basant sur les résumés suivants des différentes parties d'un document, rédigez un résumé global cohérent et fidèle au contenu original.Le résumé final doit faire moins de 300 mots.Le résumé final doit être en français.Résumés des parties :- test1- test2"
    assert final_prompt == expected_final_prompt

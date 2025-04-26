import unittest
from openai import OpenAI
from api.models.naive import summarize_text, merge_summaries, process_documents


class TestSummarizer(unittest.TestCase):
    def setUp(self):
        self.client = OpenAI(api_key="", base_url="")
        self.model = "chat-leger"

    def test_summarize_text(self):
        text = "Ceci est un texte de test pour la fonction de résumé."
        summary = summarize_text(text, self.model, self.client)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

    def test_merge_summaries(self):
        summaries = ["Résumé 1", "Résumé 2", "Résumé 3", "Résumé 4"]
        final_summary, _ = merge_summaries(summaries, self.model, self.client)
        self.assertIsInstance(final_summary, str)
        self.assertGreater(len(final_summary), 0)

    def test_process_documents(self):
        docs = ["Texte 1", "Texte 2", "Texte 3"]
        final_summary = process_documents(docs, self.model, self.client)
        self.assertIsInstance(final_summary, dict)
        self.assertGreater(len(final_summary), 0)


if __name__ == "__main__":
    unittest.main()

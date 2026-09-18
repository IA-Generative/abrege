# 📊 Évaluation des Résumés Automatiques : ROUGE vs BERTScore

L’évaluation des systèmes de résumé automatique est cruciale pour mesurer la qualité des résumés générés. Deux métriques de référence sont couramment utilisées : **ROUGE** et **BERTScore**. Ce document présente ces deux métriques, leurs principes de fonctionnement, leurs variantes, leurs avantages et leurs limites.

---

## 🔴 ROUGE (Recall-Oriented Understudy for Gisting Evaluation)

### 🔍 Principe

ROUGE est une suite de métriques qui évaluent la qualité d’un résumé en mesurant le chevauchement entre le résumé généré automatiquement et un ou plusieurs résumés de référence (généralement humains). Elle se base principalement sur la comparaison de n-grammes, de séquences et de paires de mots.

### 🧪 Variantes

- **ROUGE-N** : Mesure le chevauchement des n-grammes entre le résumé généré et la référence.
  - *ROUGE-1* : Unigrammes (mots individuels)
  - *ROUGE-2* : Bigrammes (paires de mots)
- **ROUGE-L** : Basé sur la plus longue sous-séquence commune (LCS) entre le résumé généré et la référence.
- **ROUGE-W** : Variante pondérée de ROUGE-L, favorisant les sous-séquences consécutives.
- **ROUGE-S** : Basé sur les skip-bigrammes, c’est-à-dire toutes les paires de mots dans l’ordre de la phrase, mais pas nécessairement consécutifs.
- **ROUGE-SU** : Combine les skip-bigrammes et les unigrammes.

### ✅ Avantages

- **Simplicité** : Facile à implémenter et à comprendre.
- **Rapidité** : Calcul rapide, adapté aux grandes quantités de données.
- **Standard de l’industrie** : Largement utilisé dans les compétitions et les benchmarks.

### ❌ Limites

- **Sensibilité aux reformulations** : Ne prend pas en compte les synonymes ou les paraphrases.
- **Évaluation superficielle** : Se base sur des correspondances exactes de mots, sans compréhension sémantique.
- **Biais de longueur** : Peut favoriser les résumés plus longs qui ont plus de chances de chevauchement.

### 📚 Références

- Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries. *Workshop on Text Summarization Branches Out (WAS 2004)*. [Lien](https://en.wikipedia.org/wiki/ROUGE_%28metric%29)

---

## 🟢 BERTScore

### 🔍 Principe

BERTScore évalue la similarité entre un résumé généré et une référence en utilisant des représentations vectorielles contextuelles issues de modèles de langage pré-entraînés comme BERT. Contrairement à ROUGE, qui se base sur des correspondances exactes de mots, BERTScore mesure la similarité sémantique entre les textes.

### ⚙️ Fonctionnement

1. **Tokenisation** : Les textes sont divisés en tokens.
2. **Embedding** : Chaque token est représenté par un vecteur à l’aide d’un modèle pré-entraîné (par exemple, BERT).
3. **Calcul de similarité** : Pour chaque token du résumé généré, on calcule la similarité cosinus avec les tokens du résumé de référence.
4. **Agrégation** : Les scores de similarité sont agrégés pour obtenir des mesures de précision, de rappel et de F1.

### 🧪 Options avancées

- **Pondération par IDF** : Les mots rares peuvent être pondérés plus fortement pour refléter leur importance.
- **Rescaling avec baseline** : Les scores peuvent être normalisés pour être plus interprétables.

### ✅ Avantages

- **Compréhension sémantique** : Capte les similarités de sens, même avec des formulations différentes.
- **Robustesse aux paraphrases** : Moins sensible aux variations lexicales.
- **Corrélation avec les jugements humains** : Meilleure corrélation avec les évaluations humaines que les métriques basées sur les n-grammes.

### ❌ Limites

- **Complexité computationnelle** : Plus coûteux en termes de calcul que ROUGE.
- **Dépendance au modèle** : Les performances peuvent varier selon le modèle de langage utilisé.
- **Moins interprétable** : Les scores peuvent être moins intuitifs que ceux de ROUGE.

### 📚 Références

- Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., & Artzi, Y. (2019). BERTScore: Evaluating Text Generation with BERT. *arXiv preprint arXiv:1904.09675*. [Lien](https://arxiv.org/abs/1904.09675)

---

## ⚖️ Comparaison entre ROUGE et BERTScore

| Critère                 | ROUGE                                           | BERTScore                                         |
|-------------------------|-------------------------------------------------|---------------------------------------------------|
| **Type de similarité**  | Lexicale (n-grammes)                            | Sémantique (embeddings contextuels)               |
| **Sensibilité aux paraphrases** | Élevée (faible tolérance)               | Faible (bonne tolérance)                          |
| **Complexité computationnelle** | Faible                                  | Élevée                                            |
| **Corrélation avec les jugements humains** | Moyenne à faible               | Élevée                                            |
| **Interprétabilité**    | Facile à interpréter                            | Moins intuitive                                   |
| **Utilisation**         | Standard dans les benchmarks                    | De plus en plus utilisé dans la recherche         |

---

## 🛠️ Exemples d’utilisation

### 📘 ROUGE avec Python

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
scores = scorer.score("Le chat est sur le tapis.", "Un chat repose sur le tapis.")
print(scores)
```

### 📗 BERTScore avec Python

```python
from bert_score import score

cands = ["Le chat est sur le tapis."]
refs = ["Un chat repose sur le tapis."]
P, R, F1 = score(cands, refs, lang="fr", verbose=True)
print(f"Précision: {P.mean():.4f}, Rappel: {R.mean():.4f}, F1: {F1.mean():.4f}")
```

---

## 📚 Ressources supplémentaires

- **Hugging Face - BERTScore** : [Documentation](https://github.com/huggingface/evaluate/blob/main/metrics/bertscore/README.md)
- **ROUGE 2.0** : [Documentation](https://github.com/kavgan/ROUGE-2.0)

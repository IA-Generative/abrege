# 📊 Comparatif Approche Map-Reduce vs Approche Naïve

## ⚙️ Protocole de Test

- **Dataset utilisé** : `csebuetnlp/xlsum` - 100 articles en **français**.
- **Méthode Naïve** :
  - **Prompt** :
    ```jinja
    Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte.
    {% if size %}
    Le résumé doit faire moins de {{ size }} mots.
    {% endif %}
    {% if language %}
    Le résumé doit être en {{ language }}.
    {% endif %}
    Texte : {{ text }}
    ```
  - **Nombre d'appels API** = **100** (1 appel par article).
  - **Taille du résumé** : Définie selon la variable `size` si spécifiée.

- **Méthode Map-Reduce** :
  - **Paramètres** :
    ```python
    MAP_PROMPT = "Rédigez un résumé concis des éléments suivants :\n\n{context}"

    REDUCE_PROMPT = """
    Voici une série de résumés:
    {docs}
    Rassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.
    """
    ParamsSummarize:
        method: "map_reduce"
        model: gemma3
        context_size: 10_000
        temperature: 0.0
        language: "French"
        size: 4000
    ```
  - **Processus** :
    - Découpage du texte si nécessaire (`context_size` 10k tokens max),
    - Résumés partiels (`MAP_PROMPT`),
    - Résumé final consolidé (`REDUCE_PROMPT`).
  - **Nombre d'appels API** = **30**.

---

## 📋 Tableau Comparatif
| Critère                        | Map-Reduce                               | Approche Naïve                         |
|---------------------------------|------------------------------------------|----------------------------------------|
| **Modèle utilisé**              | gemma3                                   | gemma3                                 |
| **Nombre de textes évalués**     | 50                                       | 50                                     |
| **Nombre d'appels API**          | 150 (Map + Reduce)                       | 50 (1 appel par texte)                 |
| **Temps total de résumé (s)**    | 837.21                                   | 93.44                                  |
| **Temps moyen par prédiction (s)** | 16.74                                   | 1.87                                   |
| **Méthode de traitement**        | Map-Reduce (découpage + fusion)           | Résumé direct                          |
| **ROUGE-1**                      | 0.0314                                   | 0.2194                                 |
| **ROUGE-2**                      | 0.0113                                   | 0.0586                                 |
| **ROUGE-L**                      | 0.0256                                   | 0.1315                                 |
| **ROUGE-Lsum**                   | 0.0282                                   | 0.1388                                 |
| **Précision BERTScore**           | 0.5859                                   | 0.6514                                 |
| **Rappel BERTScore**              | 0.6902                                   | 0.7248                                 |
| **F1 BERTScore**                  | 0.6335                                   | 0.6856                                 |

---


# 🧠 Analyse rapide

- **Qualité du résumé** :
  - Encore une fois, **l’approche naïve** produit des résumés **beaucoup plus proches** des résumés de référence selon **ROUGE** et **BERTScore**.
  - **ROUGE-1** est environ **7 fois plus élevé** pour l’approche naïve.

- **Performance temporelle** :
  - L’approche naïve est **9 fois plus rapide** en temps total.
  - **Map-Reduce** est extrêmement coûteux ici : **plus de 14 minutes** contre **moins de 2 minutes** pour naïf !

- **Coût en API** :
  - **150 appels API** pour 50 textes en Map-Reduce contre seulement **50** pour la méthode naïve.

- **Interprétation** :
  - **Map-Reduce** est ici **inefficace** pour de petits textes comme ceux de `xlsum`.

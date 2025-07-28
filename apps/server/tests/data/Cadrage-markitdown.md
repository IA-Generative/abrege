**Résumé automatique de documents**

**18/04/2024**

Contexte :

Les projets de l’usines IA rencontrent souvent la problématique de « text summarization » au cours de leurs développements pour réaliser les actions suivantes :

- Affichage concis d’un document en proposant une version résumé afin d’améliorer l’experience de lecture et l’ergonomie du site web,

- Compression d’un document long en vu du plongement lexical (embedding) puis de sa sauvegarde en base vectorielle. Cela peut en effet être une bonne alternative au « chunking ».

Objectifs :

L’équipe sous-systèmes complexes souhaite mettre à disposition des développeurs une API de résumé de document simple d’utilisation et auto-portée, qui comporte une petite documentation et un contrat d’interface (swagger).

Les documents seront sous la forme d’une url pour une page web, d’un texte ou encore d’un pdf ou document word.

L’objectif est aussi de monter en compétence sur la tâche de résumé. Une revue de l’existant sera nécessaire avant les développements informatiques.

Spécifications techniques :

- Le code source devra figuré dans [l’organisation](https://github.com/IA-Generative) github de l’usine IA.

- La bibliothèque devra avoir une version installable sur Docker.

- L’API sera disponible sur internet.

- L’API sera déployé avec Kubernetes, avec une CI/CD sur Github.

- L’API sera réalisée avec FastAPI, la modélisation avec LangChain, les tests unitaires avec Pytest.

- Les modèles LLM utilisés devront être ceux mis à disposition par l’usine IA.

- Des routes GET pour une url ou du texte brut

- Des routes POST pour un document binaire (pdf/odt/word)

Liens utiles :

- La [démo](https://demo4.numerique-interieur.com/) avec une url (Bon point de départ des développements),

- [Master Thesis](https://resana.numerique.gouv.fr/public/perimetre/consulter/471079?information=14937377) au Ministère de la Justice,

- L’approche [LangChain](https://python.langchain.com/docs/use_cases/summarization/)

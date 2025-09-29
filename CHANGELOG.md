## 0.1.0 (2025-06-16)

### Feat

- :sparkles: ajout map_prompt et reduce_prompt
- :sparkles: map reduce dans abrege-api
- :goal_net: meilleure gestion des erreurs
- :alembic: ajout erreur surcharge LLM et surcharge OCR
- :bug: install nltk package during build time
- :poop: ajout du param custom_prompt pour retrocompatibilité
- :sparkles: ajout map_prompt et reduce_prompt
- :poop: ajout limite ocr et nombre tokens
- :sparkles: schema pydantic pour les réponses
- :sparkles: correction qq bugs
- :sparkles: map reduce dans abrege-api
- add LibreOffice document support and related tests (#126) (#127) (#128)
- add task status to HTTP status mapping and corresponding tests
- add position (#107)
- add global percentage
- fix ocr integration
- combine ocr client
- add tokenizer into process
- add tokenizer to split text
- add small migration
- add more details health
- add migration images
- add task router
- add summay model
- add parameters
- add parameters
- add parameters
- use model service
- add naive approach
- add basemodel service
- use services approach
- add url and flat text
- add ocr purpose
- add document parsing
- add video transcription service
- add task process to audio
- based on task
- add dockerfile
- feature add abrege most anything
- add celery capacity
- add context length feat
- add naive approach
- add url modules
- add retrieve version
- add evaluation metrics
- add naive sumup approch
- add text splitter
- add prompting resolution
- add video process
- add audio service to text
- add plain text
- add document to markdown
- add file available for process
- add content type
- send document to redis
- add s3 and minio connector
- add celery component
- add url detector
- refactor process
- add task
- add more log
- :goal_net: meilleure gestion des erreurs
- :alembic: ajout erreur surcharge LLM et surcharge OCR
- :bug: install nltk package during build time
- :sparkles: add OPENAI_API_MODEL
- :sparkles: add CORS_REGEXP
- :poop: ajout du param custom_prompt pour retrocompatibilité
- :sparkles: ajout map_prompt et reduce_prompt
- :poop: ajout limite ocr et nombre tokens
- :construction: tous les params dans le request body
- :sparkles: schema pydantic pour les réponses
- :sparkles: correction qq bugs
- :sparkles: map reduce dans abrege-api

### Fix

- :construction: restauration ancienne api + meilleurs param par défaut
- :adhesive_bandage: gestion erreur openai.RateLimitError
- :adhesive_bandage: code erreur à 500 au lieu de 422
- :poop: augmentation des limites
- :bug: try fix /root/nltk_data issue
- :construction: restauration ancienne api + meilleurs param par défaut
- :construction: try fix ci/cd
- correct project version to 0.0.3 in pyproject.toml
- add more log
- cors api
- / for routes
- by using / (#110)
- format JSONResponse and improve CORS middleware setup
- update project version to 2.0.1
- format JSONResponse and update default origins in set_cors function
- example (#108)
- add health (#103)
- ci deployement (#102)
- ignore prod
- delete notebook
- don't delete video
- url png
- video to audio
- remove audio file at the end
- use env var
- remove data
- s3 big file in memory
- don't save raw transformation
- naive aproche using token
- for html content
- add logger
- add logger
- add log debug
- add hf_model
- test token based
- add MAX_CONTEXT_SIZE variables
- use right folder name
- an other permission denied
- an other permission denied
- permission denied in images
- cache dir for uv
- migration script
- port to 5000 to unify
- use get instead of post
- reload
- unitest
- schemas import
- use right version
- use only boto3
- don't forget to dl model
- fix metrics evaluations
- env variables
- annotation
- document pssed
- encoding
- move utils
- giive partial result
- add packages
- use right url folder
- use dockerfile
- utf-8 encoding
- abrege name
- task update
- add x-wav data
- add audio schema
- path
- add more video
- add size in document
- add client in right domain
- typo into var name
- use default model name
- for to dowload if not present
- if text is not provide
- download only need
- fix -c
- download nltk package
- cache app
- deployement with nltk
- don't use marker api
- add more log
- jsonresponse
- port 8000
- clean dockerfile
- try catch to get errors
- separate routes
- cors and url parse
- set cors and add url router
- import path
- uv.lock
- :ambulance: middleware dans le bon ordre
- :adhesive_bandage: gestion erreur openai.RateLimitError
- :adhesive_bandage: stringData dans le kubectl patch secret
- :poop: weak CORS_REGEXP=.*
- :adhesive_bandage: code erreur à 500 au lieu de 422
- :poop: augmentation des limites
- :bug: try fix /root/nltk_data issue
- :poop: CORS allow any origin
- :bug: add regex cors
- :ambulance: try fix route /api/doc
- :ambulance: try fix route /text
- :construction: restauration ancienne api + meilleurs param par défaut
- :construction: try fix ci/cd
- :construction: try fix ci/Cd
- :construction: try fix ci/cd
- sync modules
- fix run
- uv cache
- dso
- add api
- mode
- test to stream
- add tags
- health
- delete template
- make more speed
- use env file
- splitext by token
- clean code
- :construction: try fix docker compose

### Refactor

- :art: improve type handling for max_token and enhance code readability
- :art: remove redundant line for summarize_router inclusion
- :art: remove unused MarkerAPIClient and related classes
- delete not use dockerfile
- clean code
- clean useless code
- clean code
- clean code
- clean code

## [1.0.0](https://github.com/IA-Generative/abrege/compare/v0.2.0...v1.0.0) (2025-09-29)


### ⚠ BREAKING CHANGES

* feature add abrege most anything

### Features

* :alembic: ajout erreur surcharge LLM et surcharge OCR ([4df0971](https://github.com/IA-Generative/abrege/commit/4df0971fa9a85cee0dcd926d2c87b9ae74c8a7c2))
* :alembic: ajout erreur surcharge LLM et surcharge OCR ([88f23d3](https://github.com/IA-Generative/abrege/commit/88f23d3c56a6622cd6bc0192a47239c0ab693ac4))
* :ambulance: map_reduce comme méthode par défaut ([31c48d2](https://github.com/IA-Generative/abrege/commit/31c48d23673528ada7e5617e938872c8e1a00fac))
* :art: add headers to api ([df71f85](https://github.com/IA-Generative/abrege/commit/df71f851e48df3b8a0fcdd36e0eb48f53db08fef))
* :art: add types with openapi ts ([#164](https://github.com/IA-Generative/abrege/issues/164)) ([8c11001](https://github.com/IA-Generative/abrege/commit/8c1100190ba5eb7be6890c36fd024d41ba1b250a))
* :bug: install nltk package during build time ([fb544f9](https://github.com/IA-Generative/abrege/commit/fb544f9d6c4e6df4d25a0fa2b327d160976ff30f))
* :bug: install nltk package during build time ([ca82c7f](https://github.com/IA-Generative/abrege/commit/ca82c7ff58df3a8902df2306842a42f6de3fa490))
* :chart_with_upwards_trend: add matomo tracking ([66b820d](https://github.com/IA-Generative/abrege/commit/66b820dc190a193a740ae002b312e4853fbedb13))
* :construction: tous les params dans le request body ([f480396](https://github.com/IA-Generative/abrege/commit/f4803964861f3d7fb06dfb7192ad731496b7321e))
* :goal_net: meilleure gestion des erreurs ([dbf092b](https://github.com/IA-Generative/abrege/commit/dbf092bf0bb0abb4378a14db8e21f92f7cbf5fc0))
* :goal_net: meilleure gestion des erreurs ([4892f8f](https://github.com/IA-Generative/abrege/commit/4892f8f7bc2aab952c00e3822192aa9cacefdeac))
* :passport_control: add authguard on route ([947f8e7](https://github.com/IA-Generative/abrege/commit/947f8e7abb6f1504c8e7866963b30f4414f37901))
* :passport_control: add keycloak ([caff0b4](https://github.com/IA-Generative/abrege/commit/caff0b4cf712d8e3830a3d661aaf409bc496d570))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([e2dc5be](https://github.com/IA-Generative/abrege/commit/e2dc5be2b7d54563ab1339709da63725c0a9286e))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([3b69c4e](https://github.com/IA-Generative/abrege/commit/3b69c4e3ab98c6364f11e0b30af7f67eb829ede2))
* :poop: ajout limite ocr et nombre tokens ([70b7ddf](https://github.com/IA-Generative/abrege/commit/70b7ddf9b279ebd03dd48d30e4a241b18fb884c5))
* :poop: ajout limite ocr et nombre tokens ([2d640d2](https://github.com/IA-Generative/abrege/commit/2d640d2ae3519d1f4138a4acec6d23f7f25155bb))
* :sparkles: add commitlint ([8ccc2e2](https://github.com/IA-Generative/abrege/commit/8ccc2e27fd642576b2a3a59968a041ae9f266955))
* :sparkles: add CORS_REGEXP ([77293db](https://github.com/IA-Generative/abrege/commit/77293dba26c954a59634d509701804bc66d132b8))
* :sparkles: add husky and setup commitlint ([a747057](https://github.com/IA-Generative/abrege/commit/a7470574a9114d22e5661b5e276de00debcd1964))
* :sparkles: add OPENAI_API_MODEL ([f0ed789](https://github.com/IA-Generative/abrege/commit/f0ed78928c6194d1c3afd92560b014055eddf4d4))
* :sparkles: ajout map_prompt et reduce_prompt ([9d35720](https://github.com/IA-Generative/abrege/commit/9d35720bd7cf49eb4fdcdfcf660b22ade3a16cb1))
* :sparkles: ajout map_prompt et reduce_prompt ([686afb2](https://github.com/IA-Generative/abrege/commit/686afb246f47d1a816ef68d54eaecc6aa1d48e49))
* :sparkles: ajout map_prompt et reduce_prompt ([b98d8c8](https://github.com/IA-Generative/abrege/commit/b98d8c849396579b5d993b9a6c8adba716cb01d4))
* :sparkles: correction qq bugs ([441cba2](https://github.com/IA-Generative/abrege/commit/441cba299274fa16e3fa8ee9b10d682202c77a81))
* :sparkles: correction qq bugs ([9d91434](https://github.com/IA-Generative/abrege/commit/9d91434ffdc22d705770fafc9ac31c2721a6c352))
* :sparkles: map reduce dans abrege-api ([6b27d97](https://github.com/IA-Generative/abrege/commit/6b27d973908e4021ed124cdbaeb90dac0652cfa6))
* :sparkles: map reduce dans abrege-api ([ecc18cc](https://github.com/IA-Generative/abrege/commit/ecc18cc9b420d94f5c5b47e04a04861b7c4cb071))
* :sparkles: map reduce dans abrege-api ([bdc5778](https://github.com/IA-Generative/abrege/commit/bdc5778d5dd1929d90df0941bcfb9523e3768f7c))
* :sparkles: schema pydantic pour les réponses ([cbca0ce](https://github.com/IA-Generative/abrege/commit/cbca0cea574374944fda78842d299e9b6db12506))
* :sparkles: schema pydantic pour les réponses ([6236b8c](https://github.com/IA-Generative/abrege/commit/6236b8c712db334638b0e9537d66377fc2bfba49))
* :tada: add vuedsfr frontend ([#155](https://github.com/IA-Generative/abrege/issues/155)) ([75df72e](https://github.com/IA-Generative/abrege/commit/75df72e224b37a66535ac945803461a9f324ff4c))
* :zap: reafacto frontend to apps/client ([#173](https://github.com/IA-Generative/abrege/issues/173)) ([af92983](https://github.com/IA-Generative/abrege/commit/af929831ba3fe867cd3960b0f3a987f060487628))
* :zap: verify cache & config pwa ([937139a](https://github.com/IA-Generative/abrege/commit/937139a3f6a11610700b44aa171a20046c4ae05b))
* add aiofiles dependency for asynchronous file handling in document summary ([e07cc51](https://github.com/IA-Generative/abrege/commit/e07cc51df035e005680e9fce238a7ec1a598ae68))
* add audio service to text ([44f5823](https://github.com/IA-Generative/abrege/commit/44f5823b81ebc61457d375d2a3d9ac5037376188))
* add basemodel service ([dd11a6c](https://github.com/IA-Generative/abrege/commit/dd11a6c5644d58c4ee63b623ef20e268fbbe7a73))
* add celery capacity ([6fee425](https://github.com/IA-Generative/abrege/commit/6fee425475e8c08e9436991f10026e20cc6034db))
* add celery component ([89b93ed](https://github.com/IA-Generative/abrege/commit/89b93eda7e9492601bb864d7eb3798109f348543))
* add content type ([5b11c41](https://github.com/IA-Generative/abrege/commit/5b11c419fb0900993f67570027ea51da47f51e72))
* add context length feat ([52b340f](https://github.com/IA-Generative/abrege/commit/52b340f3c0434d40c1985b127610a4d697bbc884))
* add dockerfile ([2b70e89](https://github.com/IA-Generative/abrege/commit/2b70e8900eb0c2749f8e60330e2b13733b870f33))
* add document parsing ([a1bfc94](https://github.com/IA-Generative/abrege/commit/a1bfc94f4952dddb5abd2fc89bad45b480319a72))
* add document to markdown ([9ce92f5](https://github.com/IA-Generative/abrege/commit/9ce92f59d5ef5a1aa7b03bb0e720963e9a3027c2))
* add environment configuration for Langfuse initialization ([4003379](https://github.com/IA-Generative/abrege/commit/4003379ea4889a6d8dd5b6242c1af95a50f6f853))
* add evaluation metrics ([6db31e6](https://github.com/IA-Generative/abrege/commit/6db31e616b2f8f514373456c4706795103a3ba27))
* add file available for process ([00aa764](https://github.com/IA-Generative/abrege/commit/00aa764420761aa3d81685b4a0ea604032528396))
* add global percentage ([92092bb](https://github.com/IA-Generative/abrege/commit/92092bbaabc325410eb63f64372da0eece232204))
* add group_id and content_hash columns to Task schema and update related methods ([36b056d](https://github.com/IA-Generative/abrege/commit/36b056d4cbaed37ed6f0533ca0f2e830f9c36a4a))
* add headers support to OCRClient and related services ([4f30cc6](https://github.com/IA-Generative/abrege/commit/4f30cc6a594ef12c6170cf905b8c09331c71eaba))
* add Keycloak integration for token verification and update dependencies ([e07cc51](https://github.com/IA-Generative/abrege/commit/e07cc51df035e005680e9fce238a7ec1a598ae68))
* add Langfuse settings to environment variables documentation ([103b779](https://github.com/IA-Generative/abrege/commit/103b77943b4a392f2fe938aad0ffced9300a8382))
* add LibreOffice document support and related tests ([#126](https://github.com/IA-Generative/abrege/issues/126)) ([#127](https://github.com/IA-Generative/abrege/issues/127)) ([#128](https://github.com/IA-Generative/abrege/issues/128)) ([86dfa54](https://github.com/IA-Generative/abrege/commit/86dfa547f8108d3e7d17c699d0a9d7fbbe63d064))
* add migration images ([6a75b7d](https://github.com/IA-Generative/abrege/commit/6a75b7dbca70fc7c3d1e9e4b5e7405cb5451e637))
* add more details health ([98dd7d2](https://github.com/IA-Generative/abrege/commit/98dd7d29c9ce58a9b160dd5da783b4ef746e2851))
* add more log ([3cbd7dc](https://github.com/IA-Generative/abrege/commit/3cbd7dc977e65bf404c5559420fbeff91bca3424))
* add naive approach ([3ed3228](https://github.com/IA-Generative/abrege/commit/3ed32282f19f3feda1e37a901edbfa97cd1d59a3))
* add naive approach ([73d54e6](https://github.com/IA-Generative/abrege/commit/73d54e6f0a087b98aab86dc9c1fafe4b952aca98))
* add naive sumup approch ([759769c](https://github.com/IA-Generative/abrege/commit/759769c0fea48459ea76534363a7f0ab45b6fc55))
* add ocr purpose ([f5d1ea1](https://github.com/IA-Generative/abrege/commit/f5d1ea11ed5e26f500a5085061c163ce7f66a77d))
* add parameters ([8f67d39](https://github.com/IA-Generative/abrege/commit/8f67d39a5b7948a5a014d9a52c5e1adfa9da0eec))
* add parameters ([c6ed937](https://github.com/IA-Generative/abrege/commit/c6ed9370e23ecdd467a4bb80124880f0b4a4e5ef))
* add parameters ([7785e01](https://github.com/IA-Generative/abrege/commit/7785e01d88a4e1fc561714a085657c28a684371d))
* add plain text ([16be659](https://github.com/IA-Generative/abrege/commit/16be659a0b50558684d249b6168d8e95bcefff1b))
* add position ([#107](https://github.com/IA-Generative/abrege/issues/107)) ([d0b00b0](https://github.com/IA-Generative/abrege/commit/d0b00b0da11e3866a12ea1c846cf983319509db2))
* add prompting resolution ([48ee55e](https://github.com/IA-Generative/abrege/commit/48ee55e7ce902a210325c3a660a790671ebfd3de))
* add retrieve version ([930116e](https://github.com/IA-Generative/abrege/commit/930116e6c3ab147b69b403b71d37f2b594bc330b))
* add retry on llm ([a3f5d9c](https://github.com/IA-Generative/abrege/commit/a3f5d9cce6a36de428d2d835088945a83fb12db1))
* add s3 and minio connector ([1f126e0](https://github.com/IA-Generative/abrege/commit/1f126e0d989ce7854687bf40985b405d0a2aaef8))
* add small migration ([923093e](https://github.com/IA-Generative/abrege/commit/923093ead46362cd7059ff4d3cee75681fca5df5))
* add summay model ([c0b10c6](https://github.com/IA-Generative/abrege/commit/c0b10c69ad41fa11a1afd21eba875b1ff27d3f7d))
* add support for older Microsoft Word documents and update content type handling ([1fd7523](https://github.com/IA-Generative/abrege/commit/1fd7523ecdd6c64c1b290a1bd8b3303676c5892e))
* add task ([7d92dd2](https://github.com/IA-Generative/abrege/commit/7d92dd243f501cb39dcbbdb452c200a0d6c76d8f))
* add task process to audio ([953e546](https://github.com/IA-Generative/abrege/commit/953e54637e0d47934821130848ccf266ea5fb106))
* add task router ([c26df52](https://github.com/IA-Generative/abrege/commit/c26df524bcefc76e3481988ab080fa8de1b57908))
* add task status to HTTP status mapping and corresponding tests ([adea495](https://github.com/IA-Generative/abrege/commit/adea49553c2e89337c99dd09aec9105d429722a9))
* add text splitter ([e335a83](https://github.com/IA-Generative/abrege/commit/e335a832ad436c11ea89af273592631f0e418f00))
* add tokenizer into process ([c38717e](https://github.com/IA-Generative/abrege/commit/c38717eb94d38cc11bafadb08afe1648c56515e2))
* add tokenizer to split text ([e95a9be](https://github.com/IA-Generative/abrege/commit/e95a9be71647c5fdf3a5568c927d920bd62156ee))
* add upgrade-revision target to create new database revision with user input ([891cb1c](https://github.com/IA-Generative/abrege/commit/891cb1c9ecd4387eafa3693161f6f78b8998e0a4))
* add url and flat text ([5472d87](https://github.com/IA-Generative/abrege/commit/5472d873e7bb56596c42b51a4e976a2be4a7ec8c))
* add url detector ([6194644](https://github.com/IA-Generative/abrege/commit/6194644947683c7edbed28e9287f1fe45dac713e))
* add url modules ([a16e0fc](https://github.com/IA-Generative/abrege/commit/a16e0fc4588a7b8700c3b581c22b794c360da191))
* add video ([019aaa3](https://github.com/IA-Generative/abrege/commit/019aaa3fabbb94ad1459de10b3e63b9f22f2d1d9))
* add video process ([017eeb1](https://github.com/IA-Generative/abrege/commit/017eeb1473598a9fefc95427b0f6c0b18d5ae5b6))
* add video transcription service ([2952609](https://github.com/IA-Generative/abrege/commit/2952609ffdfb6fa76a3b1dbf5c895b968e5f6cf0))
* ajout du custom prompt pour l'utilisateur ([29a8612](https://github.com/IA-Generative/abrege/commit/29a861209fa9eca6e72ce0683dae5655e60c4919))
* based on task ([e360421](https://github.com/IA-Generative/abrege/commit/e360421a48e79c202881015c9d859e7d45c24e3c))
* clean authorization headers from parameters in task insert and update methods ([ece73c4](https://github.com/IA-Generative/abrege/commit/ece73c41b3ac32a99e6387e18bc921e6f7533652))
* combine ocr client ([8fa89ca](https://github.com/IA-Generative/abrege/commit/8fa89ca21409633cec2b68b4a8a249d936b73f2e))
* enhance DevToken and KeycloakToken classes with improved user info handling and context population ([eeb0993](https://github.com/IA-Generative/abrege/commit/eeb0993acf81fbc2b670e94c49a596e5e8a3fec1))
* enhance logging system with environment-specific configuration ([e38755e](https://github.com/IA-Generative/abrege/commit/e38755ee9115c11f392dde9afdc0f43012fed0ec))
* feature add abrege most anything ([b705167](https://github.com/IA-Generative/abrege/commit/b7051671477d344392c182ae2d717daa1c357c43))
* fix ocr integration ([1fe8828](https://github.com/IA-Generative/abrege/commit/1fe8828b1134cf407c92aea54fdd153a0ffa8b8d))
* hide button ([265b016](https://github.com/IA-Generative/abrege/commit/265b0168d013554c02274b086f49315fe858ef19))
* hide expert ui ([6a61a21](https://github.com/IA-Generative/abrege/commit/6a61a21f14372d7d9ca7035e3d36a8505318d043))
* hide expert ui ([337eae6](https://github.com/IA-Generative/abrege/commit/337eae6704eb9760c7de7e641b47470e0f1ea8b3))
* improve logging, header handling, and authentication in OCRMIService and document summary routes ([b23cfb0](https://github.com/IA-Generative/abrege/commit/b23cfb03f02324fcbbd8506410c2f179534d66eb))
* improve OCRClient defaults, add CacheService, enhance logging, and refactor services ([b955914](https://github.com/IA-Generative/abrege/commit/b955914c144fd76b241afc8dfff50a043cf88c8c))
* include is_admin field in RequestContext and update parse_header_context function ([f0ef6e0](https://github.com/IA-Generative/abrege/commit/f0ef6e00484efc2d19a1dd88b8834f7d4e8f4408))
* integrate Langfuse for enhanced telemetry and monitoring ([d9e3cd1](https://github.com/IA-Generative/abrege/commit/d9e3cd1b54fa02e1d9d6beb9a411cdb0655e792b))
* new default model ([9bc5816](https://github.com/IA-Generative/abrege/commit/9bc58162d27024daa51de4da9044583b33e47d70))
* refactor process ([a8706a4](https://github.com/IA-Generative/abrege/commit/a8706a45fdfee39e1c924274f9a3c93a80a9b30c))
* reploy-hash ([efcd833](https://github.com/IA-Generative/abrege/commit/efcd83315c524f275646104c9f45574192482af0))
* send document to redis ([5f7042a](https://github.com/IA-Generative/abrege/commit/5f7042ac629c93021d4c965b54175cfffbe8927b))
* update OCRClient and document summary routes to include authorization headers ([02f1a26](https://github.com/IA-Generative/abrege/commit/02f1a26056df475e632a30b6f916a047dbc42130))
* update upload document formats and mime types ([57586c1](https://github.com/IA-Generative/abrege/commit/57586c123cbcfd7c4d6e4c0a42239cdfb6510bf9))
* use APP_SECRETS in gh action ([edb3fc9](https://github.com/IA-Generative/abrege/commit/edb3fc97d34912986d654b47196188d6253d017a))
* use model service ([a281bb7](https://github.com/IA-Generative/abrege/commit/a281bb70f9eb31166601c78358825a7f8e2e3723))
* use services approach ([ad4ca7a](https://github.com/IA-Generative/abrege/commit/ad4ca7a7d0c8d38651132f40a1ed0b0b8f2b5928))


### Bug Fixes

* :adhesive_bandage: code erreur à 500 au lieu de 422 ([ffa7293](https://github.com/IA-Generative/abrege/commit/ffa7293cf666b26eecf538de05352160cb8f3f74))
* :adhesive_bandage: code erreur à 500 au lieu de 422 ([baed080](https://github.com/IA-Generative/abrege/commit/baed0809246ec9cd67f1f89076ac3e3ab7ff54ed))
* :adhesive_bandage: fix keycloak.ts and App.vue ([a16931c](https://github.com/IA-Generative/abrege/commit/a16931c6a240dce9035a85861b1619f101afef70))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([03b23ae](https://github.com/IA-Generative/abrege/commit/03b23ae966e273822b0fbb8676ab3391f02afec2))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([9a0eb47](https://github.com/IA-Generative/abrege/commit/9a0eb474ee4aa1c16ffe411a28b7a1c6ccefbb33))
* :adhesive_bandage: stringData dans le kubectl patch secret ([94bfddd](https://github.com/IA-Generative/abrege/commit/94bfddde11fb7834442dfebeb0bfa6fc6df7d081))
* :alembic: nouveau model par défaut fastapi ([e431385](https://github.com/IA-Generative/abrege/commit/e4313858adb7d844784a933966a3297463d0345d))
* :ambulance: middleware dans le bon ordre ([e0937a8](https://github.com/IA-Generative/abrege/commit/e0937a8744a8d55bd2b379c17260cbd0369ea14e))
* :ambulance: summary comme modèle par défaut ([89e7727](https://github.com/IA-Generative/abrege/commit/89e7727356221b9bc4a3462bcf877c476a1f2351))
* :ambulance: try fix route /api/doc ([49e6730](https://github.com/IA-Generative/abrege/commit/49e6730b75d8c205cee3c18aaceb95713b96602c))
* :ambulance: try fix route /text ([44390bd](https://github.com/IA-Generative/abrege/commit/44390bd5b10c6a562a7406ead8ac6fd67305f858))
* :ambulance: update dependencies ([ee3c0e5](https://github.com/IA-Generative/abrege/commit/ee3c0e5d852537242e34d39be781b57a9c124e1c))
* :art: fix linting ([3ac4326](https://github.com/IA-Generative/abrege/commit/3ac4326636858eaaa96d7a75f944b5d6c0f7b347))
* :bug: add regex cors ([f461fd3](https://github.com/IA-Generative/abrege/commit/f461fd390c2392d11a64c8f59f8679ce002da9b6))
* :bug: refactor links & add portal links ([#175](https://github.com/IA-Generative/abrege/issues/175)) ([2832807](https://github.com/IA-Generative/abrege/commit/2832807a44ad0bfba7f8c8fa06280c8e59bf6020))
* :bug: try fix /root/nltk_data issue ([eb70e7f](https://github.com/IA-Generative/abrege/commit/eb70e7f45b2bb33215be91a673de7e034e95130f))
* :bug: try fix /root/nltk_data issue ([d23a29c](https://github.com/IA-Generative/abrege/commit/d23a29cd7a3b13d63eea015072548425f78a2f02))
* :bug: update dependencies & content ([3f12ab7](https://github.com/IA-Generative/abrege/commit/3f12ab700d1e8c7d7cb447b35d4817cf0fe02566))
* :construction: restauration ancienne api + meilleurs param par défaut ([ad0b2dd](https://github.com/IA-Generative/abrege/commit/ad0b2ddaa0c54642a60b286e02ee58349ec8d135))
* :construction: restauration ancienne api + meilleurs param par défaut ([bcdd46a](https://github.com/IA-Generative/abrege/commit/bcdd46ad68ac7ea305b973c1d762e61cb870a4d0))
* :construction: restauration ancienne api + meilleurs param par défaut ([5753b9d](https://github.com/IA-Generative/abrege/commit/5753b9dd085c37e6a3c1586a443cc58982dc981c))
* :construction: try fix ci/cd ([636eeaf](https://github.com/IA-Generative/abrege/commit/636eeafdc4d0249791da2e5f80f98968c0b24386))
* :construction: try fix ci/cd ([a1dcd06](https://github.com/IA-Generative/abrege/commit/a1dcd06c4ce2bbd50ea9171dfbb785727a10e392))
* :construction: try fix ci/cd ([730bd07](https://github.com/IA-Generative/abrege/commit/730bd07acb67b60c9fa8aee621f0c18eb04ba63f))
* :construction: try fix ci/Cd ([d6295a1](https://github.com/IA-Generative/abrege/commit/d6295a1272edac527e739f29846cf3191c17a5b3))
* :construction: try fix docker compose ([8a21976](https://github.com/IA-Generative/abrege/commit/8a21976f9148fb0943a32632a17acbda7978b2ac))
* :label: fix error types ts ([407683e](https://github.com/IA-Generative/abrege/commit/407683ef6f97bdc3199c4f521c5b1be29aa0b337))
* :poop: augmentation des limites ([ed5e0da](https://github.com/IA-Generative/abrege/commit/ed5e0da1e602ea78d1eea6dfe9616e3e816ba5cf))
* :poop: augmentation des limites ([0da344f](https://github.com/IA-Generative/abrege/commit/0da344f8ea5549a315b0a7557aaf4bac90c5fd62))
* :poop: CORS allow any origin ([da18055](https://github.com/IA-Generative/abrege/commit/da180557508e2aebc859b20d491ee34299b10457))
* :poop: weak CORS_REGEXP=.* ([b708090](https://github.com/IA-Generative/abrege/commit/b7080907e2677dfc58d1f1f7a44b771a0117d190))
* / for routes ([5fb559e](https://github.com/IA-Generative/abrege/commit/5fb559eda5fe459248b0a361e2d7682eb6aa5751))
* abrege name ([b3ce04b](https://github.com/IA-Generative/abrege/commit/b3ce04bfd5021207aa85afbca6f19688e6eb7491))
* add api ([2adf7d0](https://github.com/IA-Generative/abrege/commit/2adf7d051b7ccabfb89e088ff90e0238afb08652))
* add audio schema ([a794c8b](https://github.com/IA-Generative/abrege/commit/a794c8b93766fd79afe17f88d0fa6bd7e1ac30e0))
* add client in right domain ([8877d41](https://github.com/IA-Generative/abrege/commit/8877d4132b88249fac2a0089280464e9ae4f9e1e))
* add health ([#103](https://github.com/IA-Generative/abrege/issues/103)) ([39ef458](https://github.com/IA-Generative/abrege/commit/39ef458f40b24edcf85eb059098346795e2a8b13))
* add hf_model ([4272a79](https://github.com/IA-Generative/abrege/commit/4272a79069202fb4ee642e7ee2c547e63140b654))
* add log debug ([43e5d9c](https://github.com/IA-Generative/abrege/commit/43e5d9c25d781ddae7d6a402925e141ab918d7d1))
* add logger ([9c52f92](https://github.com/IA-Generative/abrege/commit/9c52f92366a8edae50d7229705d8a454c5cecf75))
* add logger ([cb7f93e](https://github.com/IA-Generative/abrege/commit/cb7f93ed71b3be0422b143cc73f767ecc7104f8e))
* add MAX_CONTEXT_SIZE variables ([8f53612](https://github.com/IA-Generative/abrege/commit/8f536120d93c3afa37d3cf9cb9977abb582f21a8))
* add more log ([51af2b9](https://github.com/IA-Generative/abrege/commit/51af2b9e378dc9acf2bc02b70106993ecb23a99c))
* add more log ([11f9f29](https://github.com/IA-Generative/abrege/commit/11f9f2996527e4ab06ccbe102c1b9e4a8d387fbd))
* add more log ([#144](https://github.com/IA-Generative/abrege/issues/144)) ([#145](https://github.com/IA-Generative/abrege/issues/145)) ([#146](https://github.com/IA-Generative/abrege/issues/146)) ([#147](https://github.com/IA-Generative/abrege/issues/147)) ([803c31b](https://github.com/IA-Generative/abrege/commit/803c31bba2d87a08c7550f2c77c19ddb4cb712ff))
* add more video ([e116051](https://github.com/IA-Generative/abrege/commit/e1160510539c30adea42d263eb77f09df1d2029d))
* add packages ([61b241e](https://github.com/IA-Generative/abrege/commit/61b241e2d85055541c3494fbd4d8b239bfa3c83d))
* add retry and log to api call for llm call ([#149](https://github.com/IA-Generative/abrege/issues/149)) ([075bcbd](https://github.com/IA-Generative/abrege/commit/075bcbd4876aecc0f1c7d493190d278341c6c065))
* add size in document ([36aca9b](https://github.com/IA-Generative/abrege/commit/36aca9b220aaca3d98314312844c449f5dfea3f1))
* add tags ([8737077](https://github.com/IA-Generative/abrege/commit/8737077ba6e060a9cc4ce9acdd4cc259614b5974))
* add x-wav data ([867fec9](https://github.com/IA-Generative/abrege/commit/867fec9e3d5acf1350b1abe63e0e1c27fd7300a8))
* an other permission denied ([05a0265](https://github.com/IA-Generative/abrege/commit/05a02653a16ccd08374b67a4f9d89f08fa857780))
* an other permission denied ([8411867](https://github.com/IA-Generative/abrege/commit/8411867cb8975a630e951dffec31ab04f205f4c1))
* annotation ([040152f](https://github.com/IA-Generative/abrege/commit/040152f02128015789bbcae70de54bb1345093c4))
* by using / ([#110](https://github.com/IA-Generative/abrege/issues/110)) ([2107d80](https://github.com/IA-Generative/abrege/commit/2107d805fa70a1434d78812c8a26888617ddbe5d))
* cache app ([124e634](https://github.com/IA-Generative/abrege/commit/124e6342900368f0e94079558e4465a7709e633e))
* cache dir for uv ([4a1c2aa](https://github.com/IA-Generative/abrege/commit/4a1c2aaa71ea7c8a9742425d901af3573788a132))
* ci deployement ([#102](https://github.com/IA-Generative/abrege/issues/102)) ([c5136ea](https://github.com/IA-Generative/abrege/commit/c5136eaa8095592ec2ef39d3201e3b74488dbe07))
* **ci:** add workflow_call inputs for Python version in CI/CD workflow ([596daea](https://github.com/IA-Generative/abrege/commit/596daeab225b1847daed78331b7ee5ca52f89fc8))
* clean code ([86a912e](https://github.com/IA-Generative/abrege/commit/86a912ec999f3578d0c0d95ddea713dd5f81b803))
* clean dockerfile ([b92101e](https://github.com/IA-Generative/abrege/commit/b92101eda390c53943cd1696306b6d7732a95d60))
* comment out input parameter in task update method ([26c97f2](https://github.com/IA-Generative/abrege/commit/26c97f253bd54e0cb6ca64b9c2e6ac3713efda57))
* comment out task update call in URLService to prevent unintended modifications ([edf9fbd](https://github.com/IA-Generative/abrege/commit/edf9fbd4191332329be0ab5c9cb0fcf193f343dc))
* correct formatting issues in README.md ([5b69ab1](https://github.com/IA-Generative/abrege/commit/5b69ab1e03535b7e2a1bef437bc5c264b965df11))
* correct path for alembic.ini in Dockerfile ([22baef4](https://github.com/IA-Generative/abrege/commit/22baef43b2f1298ff133e880447c2b42c86a709d))
* correct project version to 0.0.3 in pyproject.toml ([d116ce0](https://github.com/IA-Generative/abrege/commit/d116ce01b54da4e4314054c94e631c9bb8e1f566))
* corriger la liste des formats de fichiers supportés dans l'info-bulle de téléchargement ([a6a4827](https://github.com/IA-Generative/abrege/commit/a6a482737b24ccc8e07b34877cb774940f8264f8))
* cors and url parse ([d81db88](https://github.com/IA-Generative/abrege/commit/d81db88a21ff84911ad10464a3b5def980682adb))
* cors api ([166792e](https://github.com/IA-Generative/abrege/commit/166792e52f810b580bfdd38997f3c558b3fb04be))
* delete headers to api ([f466796](https://github.com/IA-Generative/abrege/commit/f466796d49a0f1ea3a351e5da0b0700cd68edafb))
* delete notebook ([222c841](https://github.com/IA-Generative/abrege/commit/222c841603edc2d0e674ec528632b2c54bf091c1))
* delete template ([afc66ca](https://github.com/IA-Generative/abrege/commit/afc66cad875b306042b12964694385a7deab577c))
* deployement with nltk ([e3c4d64](https://github.com/IA-Generative/abrege/commit/e3c4d644dc07abf2c09ccfc8e3408405c9c3b134))
* document pssed ([27749ba](https://github.com/IA-Generative/abrege/commit/27749ba1c5b5c3c9bfce4e5cfdf4ed09896ac01e))
* don't delete video ([bcb0c0b](https://github.com/IA-Generative/abrege/commit/bcb0c0b76a5e0330cf860e2bf7edaf044ffd8094))
* don't forget to dl model ([9bfb6a3](https://github.com/IA-Generative/abrege/commit/9bfb6a3f3a95caaf0b3d05c05607ff4e5c493b85))
* don't save raw transformation ([3cd06aa](https://github.com/IA-Generative/abrege/commit/3cd06aa037f6e89b2f1e78f8432b80d28bae745d))
* don't use applicatif timeout ([32bb18b](https://github.com/IA-Generative/abrege/commit/32bb18b009cf7bd31321baa90cfcde6d1e119311))
* don't use marker api ([5dc4e4d](https://github.com/IA-Generative/abrege/commit/5dc4e4d5c7251b7761709d4c0e46e956995d878f))
* downgrade datasets dependency from 4.0.0 to 3.6.0 in pyproject.toml and uv.lock ([eebfd3a](https://github.com/IA-Generative/abrege/commit/eebfd3a06b5b5c0f883fec481fa95c13e2aa8555))
* download nltk package ([9c7cadb](https://github.com/IA-Generative/abrege/commit/9c7cadb01d902c3c2982139cb5eb993bd637b9c8))
* download only need ([ad8ca7e](https://github.com/IA-Generative/abrege/commit/ad8ca7e58bf3561aaa29579d0dab12b98cec3008))
* dso ([0914699](https://github.com/IA-Generative/abrege/commit/09146993031aae2564a4a4a2828cbfdaf6eb16a0))
* encoding ([86a0cfb](https://github.com/IA-Generative/abrege/commit/86a0cfba580b5edb232c549b33995700508f0a25))
* env variables ([4a302a2](https://github.com/IA-Generative/abrege/commit/4a302a201a6d4371823f7c9ab87fff768a7e1f07))
* example ([#108](https://github.com/IA-Generative/abrege/issues/108)) ([b5bc7e5](https://github.com/IA-Generative/abrege/commit/b5bc7e579eb5b29f5fa2dba989a29d761d3cc491))
* fix -c ([19a011c](https://github.com/IA-Generative/abrege/commit/19a011cb178959ce2fc20e4855b8ba5b4db088bb))
* fix alembic binary ([ea65b3f](https://github.com/IA-Generative/abrege/commit/ea65b3fea0b98095fe00cd5c4ff069e484a3d74f))
* fix keycloak client id ([7c96d39](https://github.com/IA-Generative/abrege/commit/7c96d3900bc1fd34ca319b4ca7a06557b2de739f))
* fix metrics evaluations ([1110247](https://github.com/IA-Generative/abrege/commit/11102475753da193780af2319697890fc20d9dda))
* fix run ([d98da58](https://github.com/IA-Generative/abrege/commit/d98da58357ed8d509c6ea6a600ad3775cfb6d517))
* for html content ([8e868b7](https://github.com/IA-Generative/abrege/commit/8e868b75eee51b08ddfeae8dce0cc6554a8a038a))
* for to dowload if not present ([e911d5e](https://github.com/IA-Generative/abrege/commit/e911d5ee00251df4d9171a81a12cddf66eb7750b))
* format JSONResponse and improve CORS middleware setup ([b7bd1fa](https://github.com/IA-Generative/abrege/commit/b7bd1fa3909db141732448779cb9cb22ef88d410))
* format JSONResponse and update default origins in set_cors function ([bbfd5c6](https://github.com/IA-Generative/abrege/commit/bbfd5c6e01566ebecb3e18d932daad671ec777b2))
* giive partial result ([5c0f767](https://github.com/IA-Generative/abrege/commit/5c0f76758fa8e8c3950daeb7e943fda280347eb1))
* health ([c2d7e66](https://github.com/IA-Generative/abrege/commit/c2d7e66751c7fe8a31131b8988ead56a244c30a7))
* if text is not provide ([5b4302e](https://github.com/IA-Generative/abrege/commit/5b4302e56ebde4af7f58ed39fefce33062baf825))
* ignore prod ([b02e964](https://github.com/IA-Generative/abrege/commit/b02e964bb4b4b9f45b7815694449342ce1df247b))
* import path ([00af728](https://github.com/IA-Generative/abrege/commit/00af7288fc6b01d8e5f5a58dce173ad3ac5031d9))
* jsonresponse ([1920481](https://github.com/IA-Generative/abrege/commit/1920481805a7820cd8f0411f5086bc849f9a3284))
* make more speed ([acdd446](https://github.com/IA-Generative/abrege/commit/acdd446d698d351d5fa97e443111f3619a8280f1))
* map_reduce langchain bug ([f25d5a5](https://github.com/IA-Generative/abrege/commit/f25d5a5453d7c022dc603dc6eb6dc2647898a0c4))
* map_reduce langchain bug ([3dfb7fd](https://github.com/IA-Generative/abrege/commit/3dfb7fd9de5cdecf39fd576729377cb6ef08156c))
* migration script ([d3044c6](https://github.com/IA-Generative/abrege/commit/d3044c637d7bb920f084750da67009ba7b1c9061))
* mode ([28252af](https://github.com/IA-Generative/abrege/commit/28252af3e7648808510975172105e77bb4e95e45))
* move utils ([ba7e4c7](https://github.com/IA-Generative/abrege/commit/ba7e4c7f08bc32d0ba31d17d3b8d5e8b2aa8fa07))
* naive aproche using token ([88b47e8](https://github.com/IA-Generative/abrege/commit/88b47e84f3797ba78c558d98e08c5d98a8670483))
* now gh action on arc-runner ([0d4a29f](https://github.com/IA-Generative/abrege/commit/0d4a29f281d53a9adc6f5a7dffe1e42bb8c3fd5a))
* OCR API ([bf032bf](https://github.com/IA-Generative/abrege/commit/bf032bfc3f38ed0922a828100b57831be415a48f))
* package fix ([#136](https://github.com/IA-Generative/abrege/issues/136)) ([6ed7101](https://github.com/IA-Generative/abrege/commit/6ed7101a4d0f7636b0308a70985e72a0c645d7f8))
* path ([0591a2b](https://github.com/IA-Generative/abrege/commit/0591a2ba945c167ade86f62548a50af6b412c3ff))
* permission denied in images ([665981f](https://github.com/IA-Generative/abrege/commit/665981fcd81365be8ddfe447ea4d5e6e6d98b271))
* port 8000 ([58bbb03](https://github.com/IA-Generative/abrege/commit/58bbb0363907da73b60e9ef86971f7b35d6fe325))
* port to 5000 to unify ([49cb507](https://github.com/IA-Generative/abrege/commit/49cb507769c95e2a34aeb0b67ffbe74a5b2cd93a))
* prompt map reduce ([366e0aa](https://github.com/IA-Generative/abrege/commit/366e0aaa2601d9fffd9089c8b34354b316c61297))
* prompt map reduce ([ce6a0f6](https://github.com/IA-Generative/abrege/commit/ce6a0f64683fb9aa345993739e1b26447307c7f8))
* reload ([56b8714](https://github.com/IA-Generative/abrege/commit/56b871428044776b80f6bec7c11d293d41291364))
* remove audio file at the end ([630a560](https://github.com/IA-Generative/abrege/commit/630a560491ea893bbfcef9b990d1a69f0812173b))
* remove commented out image tags from docker build configurations ([d595428](https://github.com/IA-Generative/abrege/commit/d595428c0f1bc02316393e86b953b6b0da3eea9b))
* remove data ([58fbe0f](https://github.com/IA-Generative/abrege/commit/58fbe0fb33c6f28f1fd604757e6002fc3de65464))
* retirer la température pour monsieur tout le monde ([7585ae0](https://github.com/IA-Generative/abrege/commit/7585ae02e765a6d6d0dcb57b7002cf8996956b4a))
* s3 big file in memory ([c2018fb](https://github.com/IA-Generative/abrege/commit/c2018fbc82567e1a8b4b3854d45e90eb5bebf4ee))
* schemas import ([3d0dd04](https://github.com/IA-Generative/abrege/commit/3d0dd04333bbdb929cf275d3526bf1c309037161))
* separate routes ([6797197](https://github.com/IA-Generative/abrege/commit/6797197555534a2a640f0df8bae32e4a86166997))
* set cors and add url router ([be37604](https://github.com/IA-Generative/abrege/commit/be37604a98b3fc2958640bad7c3a89ee52318406))
* splitext by token ([830f353](https://github.com/IA-Generative/abrege/commit/830f353cf4731b65da230f898fd4ca1302a0c6a6))
* sync modules ([9731a1b](https://github.com/IA-Generative/abrege/commit/9731a1b6dbfa2fb9266a476d62fe87f9fa1da902))
* task update ([ac6b9e4](https://github.com/IA-Generative/abrege/commit/ac6b9e480dd0875368ed8b80b3a538abcea19563))
* test to stream ([02f90c5](https://github.com/IA-Generative/abrege/commit/02f90c54be569ed7b2bbb4addb529c387a6c2f39))
* test token based ([8b874b5](https://github.com/IA-Generative/abrege/commit/8b874b5ed8dd915d834862a80ddbd6faf3c02165))
* try catch to get errors ([afee0bd](https://github.com/IA-Generative/abrege/commit/afee0bde6bffc7afdfba45671682786099c1e8f1))
* typo into var name ([958b9e3](https://github.com/IA-Generative/abrege/commit/958b9e3a842467b374c319ad57e0c065dff4af82))
* unitest ([125e627](https://github.com/IA-Generative/abrege/commit/125e627f5a513b06c0db700ceef95e1864221827))
* update apps/client/vite.config.ts ([1ac3a7d](https://github.com/IA-Generative/abrege/commit/1ac3a7d4808203da1d539cfeb7657879a0637e1d))
* update lint command to exclude formatting check ([8fda12d](https://github.com/IA-Generative/abrege/commit/8fda12db72487fdf5956f061aebe580824d000f8))
* update model path in audio, image, and video test modules ([545a7f5](https://github.com/IA-Generative/abrege/commit/545a7f54d79beac6a8114ae4a233a37b790ffbc8))
* update project version to 2.0.1 ([d216a59](https://github.com/IA-Generative/abrege/commit/d216a596e7e74c71966e830a8bd3296aef8e3fc0))
* update version number in .release-please-manifest.json to 0.1.0 ([c10ee92](https://github.com/IA-Generative/abrege/commit/c10ee9212c2d6086ad7345f16a2e1c521e7aafe3))
* update version number in pyproject.toml to 0.1.0 ([b711dd4](https://github.com/IA-Generative/abrege/commit/b711dd45ede6fdcb7a5e44295f8e4151e5f1cda4))
* update version number of the 'abrege' package in uv.lock to 0.1.0 ([2d73649](https://github.com/IA-Generative/abrege/commit/2d7364939ebc4a46cbffb93837ab56c5c5c0204d))
* url png ([d265140](https://github.com/IA-Generative/abrege/commit/d265140145c5a76b9f9ae02269802de56e4bd7fa))
* use correct path ([ab1cbb3](https://github.com/IA-Generative/abrege/commit/ab1cbb395b9a7f2d41786a0601c6450a73df3c4e))
* use default model name ([5525ce5](https://github.com/IA-Generative/abrege/commit/5525ce56130a68e044bbc3e4962605e090103a47))
* use dockerfile ([6499eff](https://github.com/IA-Generative/abrege/commit/6499effad58077d6242e5bcc89812d5bc3b509bc))
* use env file ([a34cdef](https://github.com/IA-Generative/abrege/commit/a34cdef7aafe5f57fd80601a4191a8ec1b1511c7))
* use env var ([75fb200](https://github.com/IA-Generative/abrege/commit/75fb200acc33aef2c14f69154fb8f72edcc49ebb))
* use get instead of post ([01fd984](https://github.com/IA-Generative/abrege/commit/01fd984738c187ba7fd741dceed059d1db23dc48))
* use only boto3 ([2c581a1](https://github.com/IA-Generative/abrege/commit/2c581a1f0a6996c57a16b4eb6aac2f86b070f55e))
* use right folder name ([92b61d9](https://github.com/IA-Generative/abrege/commit/92b61d9f9f93d3a9b3a3315f015abaf3e0b612fd))
* use right url folder ([5601e2f](https://github.com/IA-Generative/abrege/commit/5601e2f3905a4bc5fb4918fed6f035707250513c))
* use right version ([23d2b97](https://github.com/IA-Generative/abrege/commit/23d2b97a6fe0ff1282e07982e70495b7d75a1d5e))
* utf-8 encoding ([32d0aab](https://github.com/IA-Generative/abrege/commit/32d0aab40e638beb1423e079b071fa0da7d1707f))
* uv cache ([c96e112](https://github.com/IA-Generative/abrege/commit/c96e112016ae07312cc775c43fbb532467462572))
* uv.lock ([b808a8d](https://github.com/IA-Generative/abrege/commit/b808a8d48aec303176c8a1409f415eba320080f9))
* video to audio ([c659bf3](https://github.com/IA-Generative/abrege/commit/c659bf39eb35b14e154bf660baf6113a28a0d4bf))

## [0.2.0](https://github.com/IA-Generative/abrege/compare/0.1.0...v0.2.0) (2025-09-29)


### Features

* :art: add headers to api ([df71f85](https://github.com/IA-Generative/abrege/commit/df71f851e48df3b8a0fcdd36e0eb48f53db08fef))
* :art: add types with openapi ts ([#164](https://github.com/IA-Generative/abrege/issues/164)) ([8c11001](https://github.com/IA-Generative/abrege/commit/8c1100190ba5eb7be6890c36fd024d41ba1b250a))
* :chart_with_upwards_trend: add matomo tracking ([66b820d](https://github.com/IA-Generative/abrege/commit/66b820dc190a193a740ae002b312e4853fbedb13))
* :passport_control: add authguard on route ([947f8e7](https://github.com/IA-Generative/abrege/commit/947f8e7abb6f1504c8e7866963b30f4414f37901))
* :passport_control: add keycloak ([caff0b4](https://github.com/IA-Generative/abrege/commit/caff0b4cf712d8e3830a3d661aaf409bc496d570))
* :sparkles: add commitlint ([bb392b8](https://github.com/IA-Generative/abrege/commit/bb392b8d126d3feedd8dfb047ee8da764d372755))
* :sparkles: add husky and setup commitlint ([05b3fd2](https://github.com/IA-Generative/abrege/commit/05b3fd2abe9839afba62f4ccd8e899bf376c6fac))
* :tada: add vuedsfr frontend ([#155](https://github.com/IA-Generative/abrege/issues/155)) ([75df72e](https://github.com/IA-Generative/abrege/commit/75df72e224b37a66535ac945803461a9f324ff4c))
* :zap: reafacto frontend to apps/client ([#173](https://github.com/IA-Generative/abrege/issues/173)) ([af92983](https://github.com/IA-Generative/abrege/commit/af929831ba3fe867cd3960b0f3a987f060487628))
* :zap: verify cache & config pwa ([937139a](https://github.com/IA-Generative/abrege/commit/937139a3f6a11610700b44aa171a20046c4ae05b))
* add aiofiles dependency for asynchronous file handling in document summary ([e07cc51](https://github.com/IA-Generative/abrege/commit/e07cc51df035e005680e9fce238a7ec1a598ae68))
* add environment configuration for Langfuse initialization ([4003379](https://github.com/IA-Generative/abrege/commit/4003379ea4889a6d8dd5b6242c1af95a50f6f853))
* add group_id and content_hash columns to Task schema and update related methods ([36b056d](https://github.com/IA-Generative/abrege/commit/36b056d4cbaed37ed6f0533ca0f2e830f9c36a4a))
* add headers support to OCRClient and related services ([4f30cc6](https://github.com/IA-Generative/abrege/commit/4f30cc6a594ef12c6170cf905b8c09331c71eaba))
* add Keycloak integration for token verification and update dependencies ([e07cc51](https://github.com/IA-Generative/abrege/commit/e07cc51df035e005680e9fce238a7ec1a598ae68))
* add Langfuse settings to environment variables documentation ([2015530](https://github.com/IA-Generative/abrege/commit/201553093982c06fe50cab433171c2f12ed9d09b))
* add support for older Microsoft Word documents and update content type handling ([1fd7523](https://github.com/IA-Generative/abrege/commit/1fd7523ecdd6c64c1b290a1bd8b3303676c5892e))
* add upgrade-revision target to create new database revision with user input ([891cb1c](https://github.com/IA-Generative/abrege/commit/891cb1c9ecd4387eafa3693161f6f78b8998e0a4))
* clean authorization headers from parameters in task insert and update methods ([ece73c4](https://github.com/IA-Generative/abrege/commit/ece73c41b3ac32a99e6387e18bc921e6f7533652))
* enhance DevToken and KeycloakToken classes with improved user info handling and context population ([eeb0993](https://github.com/IA-Generative/abrege/commit/eeb0993acf81fbc2b670e94c49a596e5e8a3fec1))
* enhance logging system with environment-specific configuration ([e38755e](https://github.com/IA-Generative/abrege/commit/e38755ee9115c11f392dde9afdc0f43012fed0ec))
* improve logging, header handling, and authentication in OCRMIService and document summary routes ([b23cfb0](https://github.com/IA-Generative/abrege/commit/b23cfb03f02324fcbbd8506410c2f179534d66eb))
* improve OCRClient defaults, add CacheService, enhance logging, and refactor services ([b955914](https://github.com/IA-Generative/abrege/commit/b955914c144fd76b241afc8dfff50a043cf88c8c))
* include is_admin field in RequestContext and update parse_header_context function ([f0ef6e0](https://github.com/IA-Generative/abrege/commit/f0ef6e00484efc2d19a1dd88b8834f7d4e8f4408))
* integrate Langfuse for enhanced telemetry and monitoring ([d9e3cd1](https://github.com/IA-Generative/abrege/commit/d9e3cd1b54fa02e1d9d6beb9a411cdb0655e792b))
* update OCRClient and document summary routes to include authorization headers ([02f1a26](https://github.com/IA-Generative/abrege/commit/02f1a26056df475e632a30b6f916a047dbc42130))
* update upload document formats and mime types ([57586c1](https://github.com/IA-Generative/abrege/commit/57586c123cbcfd7c4d6e4c0a42239cdfb6510bf9))


### Bug Fixes

* :adhesive_bandage: fix keycloak.ts and App.vue ([a16931c](https://github.com/IA-Generative/abrege/commit/a16931c6a240dce9035a85861b1619f101afef70))
* :ambulance: update dependencies ([ee3c0e5](https://github.com/IA-Generative/abrege/commit/ee3c0e5d852537242e34d39be781b57a9c124e1c))
* :art: fix linting ([3ac4326](https://github.com/IA-Generative/abrege/commit/3ac4326636858eaaa96d7a75f944b5d6c0f7b347))
* :bug: refactor links & add portal links ([#175](https://github.com/IA-Generative/abrege/issues/175)) ([2832807](https://github.com/IA-Generative/abrege/commit/2832807a44ad0bfba7f8c8fa06280c8e59bf6020))
* :bug: update dependencies & content ([3f12ab7](https://github.com/IA-Generative/abrege/commit/3f12ab700d1e8c7d7cb447b35d4817cf0fe02566))
* :label: fix error types ts ([407683e](https://github.com/IA-Generative/abrege/commit/407683ef6f97bdc3199c4f521c5b1be29aa0b337))
* add more log ([#144](https://github.com/IA-Generative/abrege/issues/144)) ([#145](https://github.com/IA-Generative/abrege/issues/145)) ([#146](https://github.com/IA-Generative/abrege/issues/146)) ([#147](https://github.com/IA-Generative/abrege/issues/147)) ([803c31b](https://github.com/IA-Generative/abrege/commit/803c31bba2d87a08c7550f2c77c19ddb4cb712ff))
* add retry and log to api call for llm call ([#149](https://github.com/IA-Generative/abrege/issues/149)) ([075bcbd](https://github.com/IA-Generative/abrege/commit/075bcbd4876aecc0f1c7d493190d278341c6c065))
* **ci:** add workflow_call inputs for Python version in CI/CD workflow ([1f7f81b](https://github.com/IA-Generative/abrege/commit/1f7f81b84aa8cd062cda13081278223813d1a202))
* comment out input parameter in task update method ([26c97f2](https://github.com/IA-Generative/abrege/commit/26c97f253bd54e0cb6ca64b9c2e6ac3713efda57))
* comment out task update call in URLService to prevent unintended modifications ([edf9fbd](https://github.com/IA-Generative/abrege/commit/edf9fbd4191332329be0ab5c9cb0fcf193f343dc))
* correct formatting issues in README.md ([5b69ab1](https://github.com/IA-Generative/abrege/commit/5b69ab1e03535b7e2a1bef437bc5c264b965df11))
* correct path for alembic.ini in Dockerfile ([22baef4](https://github.com/IA-Generative/abrege/commit/22baef43b2f1298ff133e880447c2b42c86a709d))
* corriger la liste des formats de fichiers supportés dans l'info-bulle de téléchargement ([a6a4827](https://github.com/IA-Generative/abrege/commit/a6a482737b24ccc8e07b34877cb774940f8264f8))
* delete headers to api ([f466796](https://github.com/IA-Generative/abrege/commit/f466796d49a0f1ea3a351e5da0b0700cd68edafb))
* downgrade datasets dependency from 4.0.0 to 3.6.0 in pyproject.toml and uv.lock ([eebfd3a](https://github.com/IA-Generative/abrege/commit/eebfd3a06b5b5c0f883fec481fa95c13e2aa8555))
* fix alembic binary ([ea65b3f](https://github.com/IA-Generative/abrege/commit/ea65b3fea0b98095fe00cd5c4ff069e484a3d74f))
* fix keycloak client id ([7c96d39](https://github.com/IA-Generative/abrege/commit/7c96d3900bc1fd34ca319b4ca7a06557b2de739f))
* package fix ([#136](https://github.com/IA-Generative/abrege/issues/136)) ([6ed7101](https://github.com/IA-Generative/abrege/commit/6ed7101a4d0f7636b0308a70985e72a0c645d7f8))
* remove commented out image tags from docker build configurations ([d595428](https://github.com/IA-Generative/abrege/commit/d595428c0f1bc02316393e86b953b6b0da3eea9b))
* update apps/client/vite.config.ts ([1ac3a7d](https://github.com/IA-Generative/abrege/commit/1ac3a7d4808203da1d539cfeb7657879a0637e1d))
* update lint command to exclude formatting check ([1a84270](https://github.com/IA-Generative/abrege/commit/1a842700b8403ae05625d46032635b02dbd5d73b))
* update model path in audio, image, and video test modules ([545a7f5](https://github.com/IA-Generative/abrege/commit/545a7f54d79beac6a8114ae4a233a37b790ffbc8))
* update version number in .release-please-manifest.json to 0.1.0 ([c88ca6b](https://github.com/IA-Generative/abrege/commit/c88ca6b3465febaae4a7d8513b0a73676e80a963))
* update version number in pyproject.toml to 0.1.0 ([54fd69e](https://github.com/IA-Generative/abrege/commit/54fd69ec7abe19c0c534a2ecd329d49622f49082))
* update version number of the 'abrege' package in uv.lock to 0.1.0 ([d389c13](https://github.com/IA-Generative/abrege/commit/d389c13d0514410ab9389a138a14ca478765672a))
* use correct path ([ab1cbb3](https://github.com/IA-Generative/abrege/commit/ab1cbb395b9a7f2d41786a0601c6450a73df3c4e))

## [4.0.0](https://github.com/IA-Generative/abrege/compare/v3.0.0...v4.0.0) (2025-07-12)


### ⚠ BREAKING CHANGES

* feature add abrege most anything

### Features

* :alembic: ajout erreur surcharge LLM et surcharge OCR ([4df0971](https://github.com/IA-Generative/abrege/commit/4df0971fa9a85cee0dcd926d2c87b9ae74c8a7c2))
* :alembic: ajout erreur surcharge LLM et surcharge OCR ([88f23d3](https://github.com/IA-Generative/abrege/commit/88f23d3c56a6622cd6bc0192a47239c0ab693ac4))
* :ambulance: map_reduce comme méthode par défaut ([31c48d2](https://github.com/IA-Generative/abrege/commit/31c48d23673528ada7e5617e938872c8e1a00fac))
* :bug: install nltk package during build time ([fb544f9](https://github.com/IA-Generative/abrege/commit/fb544f9d6c4e6df4d25a0fa2b327d160976ff30f))
* :bug: install nltk package during build time ([ca82c7f](https://github.com/IA-Generative/abrege/commit/ca82c7ff58df3a8902df2306842a42f6de3fa490))
* :construction: tous les params dans le request body ([f480396](https://github.com/IA-Generative/abrege/commit/f4803964861f3d7fb06dfb7192ad731496b7321e))
* :goal_net: meilleure gestion des erreurs ([dbf092b](https://github.com/IA-Generative/abrege/commit/dbf092bf0bb0abb4378a14db8e21f92f7cbf5fc0))
* :goal_net: meilleure gestion des erreurs ([4892f8f](https://github.com/IA-Generative/abrege/commit/4892f8f7bc2aab952c00e3822192aa9cacefdeac))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([e2dc5be](https://github.com/IA-Generative/abrege/commit/e2dc5be2b7d54563ab1339709da63725c0a9286e))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([3b69c4e](https://github.com/IA-Generative/abrege/commit/3b69c4e3ab98c6364f11e0b30af7f67eb829ede2))
* :poop: ajout limite ocr et nombre tokens ([70b7ddf](https://github.com/IA-Generative/abrege/commit/70b7ddf9b279ebd03dd48d30e4a241b18fb884c5))
* :poop: ajout limite ocr et nombre tokens ([2d640d2](https://github.com/IA-Generative/abrege/commit/2d640d2ae3519d1f4138a4acec6d23f7f25155bb))
* :sparkles: add CORS_REGEXP ([77293db](https://github.com/IA-Generative/abrege/commit/77293dba26c954a59634d509701804bc66d132b8))
* :sparkles: add OPENAI_API_MODEL ([f0ed789](https://github.com/IA-Generative/abrege/commit/f0ed78928c6194d1c3afd92560b014055eddf4d4))
* :sparkles: ajout map_prompt et reduce_prompt ([9d35720](https://github.com/IA-Generative/abrege/commit/9d35720bd7cf49eb4fdcdfcf660b22ade3a16cb1))
* :sparkles: ajout map_prompt et reduce_prompt ([686afb2](https://github.com/IA-Generative/abrege/commit/686afb246f47d1a816ef68d54eaecc6aa1d48e49))
* :sparkles: ajout map_prompt et reduce_prompt ([b98d8c8](https://github.com/IA-Generative/abrege/commit/b98d8c849396579b5d993b9a6c8adba716cb01d4))
* :sparkles: correction qq bugs ([441cba2](https://github.com/IA-Generative/abrege/commit/441cba299274fa16e3fa8ee9b10d682202c77a81))
* :sparkles: correction qq bugs ([9d91434](https://github.com/IA-Generative/abrege/commit/9d91434ffdc22d705770fafc9ac31c2721a6c352))
* :sparkles: map reduce dans abrege-api ([6b27d97](https://github.com/IA-Generative/abrege/commit/6b27d973908e4021ed124cdbaeb90dac0652cfa6))
* :sparkles: map reduce dans abrege-api ([ecc18cc](https://github.com/IA-Generative/abrege/commit/ecc18cc9b420d94f5c5b47e04a04861b7c4cb071))
* :sparkles: map reduce dans abrege-api ([bdc5778](https://github.com/IA-Generative/abrege/commit/bdc5778d5dd1929d90df0941bcfb9523e3768f7c))
* :sparkles: schema pydantic pour les réponses ([cbca0ce](https://github.com/IA-Generative/abrege/commit/cbca0cea574374944fda78842d299e9b6db12506))
* :sparkles: schema pydantic pour les réponses ([6236b8c](https://github.com/IA-Generative/abrege/commit/6236b8c712db334638b0e9537d66377fc2bfba49))
* add audio service to text ([44f5823](https://github.com/IA-Generative/abrege/commit/44f5823b81ebc61457d375d2a3d9ac5037376188))
* add basemodel service ([dd11a6c](https://github.com/IA-Generative/abrege/commit/dd11a6c5644d58c4ee63b623ef20e268fbbe7a73))
* add celery capacity ([6fee425](https://github.com/IA-Generative/abrege/commit/6fee425475e8c08e9436991f10026e20cc6034db))
* add celery component ([89b93ed](https://github.com/IA-Generative/abrege/commit/89b93eda7e9492601bb864d7eb3798109f348543))
* add content type ([5b11c41](https://github.com/IA-Generative/abrege/commit/5b11c419fb0900993f67570027ea51da47f51e72))
* add context length feat ([52b340f](https://github.com/IA-Generative/abrege/commit/52b340f3c0434d40c1985b127610a4d697bbc884))
* add dockerfile ([2b70e89](https://github.com/IA-Generative/abrege/commit/2b70e8900eb0c2749f8e60330e2b13733b870f33))
* add document parsing ([a1bfc94](https://github.com/IA-Generative/abrege/commit/a1bfc94f4952dddb5abd2fc89bad45b480319a72))
* add document to markdown ([9ce92f5](https://github.com/IA-Generative/abrege/commit/9ce92f59d5ef5a1aa7b03bb0e720963e9a3027c2))
* add evaluation metrics ([6db31e6](https://github.com/IA-Generative/abrege/commit/6db31e616b2f8f514373456c4706795103a3ba27))
* add file available for process ([00aa764](https://github.com/IA-Generative/abrege/commit/00aa764420761aa3d81685b4a0ea604032528396))
* add global percentage ([92092bb](https://github.com/IA-Generative/abrege/commit/92092bbaabc325410eb63f64372da0eece232204))
* add LibreOffice document support and related tests ([#126](https://github.com/IA-Generative/abrege/issues/126)) ([#127](https://github.com/IA-Generative/abrege/issues/127)) ([#128](https://github.com/IA-Generative/abrege/issues/128)) ([86dfa54](https://github.com/IA-Generative/abrege/commit/86dfa547f8108d3e7d17c699d0a9d7fbbe63d064))
* add migration images ([6a75b7d](https://github.com/IA-Generative/abrege/commit/6a75b7dbca70fc7c3d1e9e4b5e7405cb5451e637))
* add more details health ([98dd7d2](https://github.com/IA-Generative/abrege/commit/98dd7d29c9ce58a9b160dd5da783b4ef746e2851))
* add more log ([3cbd7dc](https://github.com/IA-Generative/abrege/commit/3cbd7dc977e65bf404c5559420fbeff91bca3424))
* add naive approach ([3ed3228](https://github.com/IA-Generative/abrege/commit/3ed32282f19f3feda1e37a901edbfa97cd1d59a3))
* add naive approach ([73d54e6](https://github.com/IA-Generative/abrege/commit/73d54e6f0a087b98aab86dc9c1fafe4b952aca98))
* add naive sumup approch ([759769c](https://github.com/IA-Generative/abrege/commit/759769c0fea48459ea76534363a7f0ab45b6fc55))
* add ocr purpose ([f5d1ea1](https://github.com/IA-Generative/abrege/commit/f5d1ea11ed5e26f500a5085061c163ce7f66a77d))
* add parameters ([8f67d39](https://github.com/IA-Generative/abrege/commit/8f67d39a5b7948a5a014d9a52c5e1adfa9da0eec))
* add parameters ([c6ed937](https://github.com/IA-Generative/abrege/commit/c6ed9370e23ecdd467a4bb80124880f0b4a4e5ef))
* add parameters ([7785e01](https://github.com/IA-Generative/abrege/commit/7785e01d88a4e1fc561714a085657c28a684371d))
* add plain text ([16be659](https://github.com/IA-Generative/abrege/commit/16be659a0b50558684d249b6168d8e95bcefff1b))
* add position ([#107](https://github.com/IA-Generative/abrege/issues/107)) ([d0b00b0](https://github.com/IA-Generative/abrege/commit/d0b00b0da11e3866a12ea1c846cf983319509db2))
* add prompting resolution ([48ee55e](https://github.com/IA-Generative/abrege/commit/48ee55e7ce902a210325c3a660a790671ebfd3de))
* add retrieve version ([930116e](https://github.com/IA-Generative/abrege/commit/930116e6c3ab147b69b403b71d37f2b594bc330b))
* add retry on llm ([a3f5d9c](https://github.com/IA-Generative/abrege/commit/a3f5d9cce6a36de428d2d835088945a83fb12db1))
* add s3 and minio connector ([1f126e0](https://github.com/IA-Generative/abrege/commit/1f126e0d989ce7854687bf40985b405d0a2aaef8))
* add small migration ([923093e](https://github.com/IA-Generative/abrege/commit/923093ead46362cd7059ff4d3cee75681fca5df5))
* add summay model ([c0b10c6](https://github.com/IA-Generative/abrege/commit/c0b10c69ad41fa11a1afd21eba875b1ff27d3f7d))
* add task ([7d92dd2](https://github.com/IA-Generative/abrege/commit/7d92dd243f501cb39dcbbdb452c200a0d6c76d8f))
* add task process to audio ([953e546](https://github.com/IA-Generative/abrege/commit/953e54637e0d47934821130848ccf266ea5fb106))
* add task router ([c26df52](https://github.com/IA-Generative/abrege/commit/c26df524bcefc76e3481988ab080fa8de1b57908))
* add task status to HTTP status mapping and corresponding tests ([adea495](https://github.com/IA-Generative/abrege/commit/adea49553c2e89337c99dd09aec9105d429722a9))
* add text splitter ([e335a83](https://github.com/IA-Generative/abrege/commit/e335a832ad436c11ea89af273592631f0e418f00))
* add tokenizer into process ([c38717e](https://github.com/IA-Generative/abrege/commit/c38717eb94d38cc11bafadb08afe1648c56515e2))
* add tokenizer to split text ([e95a9be](https://github.com/IA-Generative/abrege/commit/e95a9be71647c5fdf3a5568c927d920bd62156ee))
* add url and flat text ([5472d87](https://github.com/IA-Generative/abrege/commit/5472d873e7bb56596c42b51a4e976a2be4a7ec8c))
* add url detector ([6194644](https://github.com/IA-Generative/abrege/commit/6194644947683c7edbed28e9287f1fe45dac713e))
* add url modules ([a16e0fc](https://github.com/IA-Generative/abrege/commit/a16e0fc4588a7b8700c3b581c22b794c360da191))
* add video process ([017eeb1](https://github.com/IA-Generative/abrege/commit/017eeb1473598a9fefc95427b0f6c0b18d5ae5b6))
* add video transcription service ([2952609](https://github.com/IA-Generative/abrege/commit/2952609ffdfb6fa76a3b1dbf5c895b968e5f6cf0))
* ajout du custom prompt pour l'utilisateur ([29a8612](https://github.com/IA-Generative/abrege/commit/29a861209fa9eca6e72ce0683dae5655e60c4919))
* based on task ([e360421](https://github.com/IA-Generative/abrege/commit/e360421a48e79c202881015c9d859e7d45c24e3c))
* combine ocr client ([8fa89ca](https://github.com/IA-Generative/abrege/commit/8fa89ca21409633cec2b68b4a8a249d936b73f2e))
* feature add abrege most anything ([b705167](https://github.com/IA-Generative/abrege/commit/b7051671477d344392c182ae2d717daa1c357c43))
* fix ocr integration ([1fe8828](https://github.com/IA-Generative/abrege/commit/1fe8828b1134cf407c92aea54fdd153a0ffa8b8d))
* hide button ([265b016](https://github.com/IA-Generative/abrege/commit/265b0168d013554c02274b086f49315fe858ef19))
* hide expert ui ([6a61a21](https://github.com/IA-Generative/abrege/commit/6a61a21f14372d7d9ca7035e3d36a8505318d043))
* hide expert ui ([337eae6](https://github.com/IA-Generative/abrege/commit/337eae6704eb9760c7de7e641b47470e0f1ea8b3))
* new default model ([9bc5816](https://github.com/IA-Generative/abrege/commit/9bc58162d27024daa51de4da9044583b33e47d70))
* refactor process ([a8706a4](https://github.com/IA-Generative/abrege/commit/a8706a45fdfee39e1c924274f9a3c93a80a9b30c))
* reploy-hash ([efcd833](https://github.com/IA-Generative/abrege/commit/efcd83315c524f275646104c9f45574192482af0))
* send document to redis ([5f7042a](https://github.com/IA-Generative/abrege/commit/5f7042ac629c93021d4c965b54175cfffbe8927b))
* use APP_SECRETS in gh action ([edb3fc9](https://github.com/IA-Generative/abrege/commit/edb3fc97d34912986d654b47196188d6253d017a))
* use model service ([a281bb7](https://github.com/IA-Generative/abrege/commit/a281bb70f9eb31166601c78358825a7f8e2e3723))
* use services approach ([ad4ca7a](https://github.com/IA-Generative/abrege/commit/ad4ca7a7d0c8d38651132f40a1ed0b0b8f2b5928))


### Bug Fixes

* :adhesive_bandage: code erreur à 500 au lieu de 422 ([ffa7293](https://github.com/IA-Generative/abrege/commit/ffa7293cf666b26eecf538de05352160cb8f3f74))
* :adhesive_bandage: code erreur à 500 au lieu de 422 ([baed080](https://github.com/IA-Generative/abrege/commit/baed0809246ec9cd67f1f89076ac3e3ab7ff54ed))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([03b23ae](https://github.com/IA-Generative/abrege/commit/03b23ae966e273822b0fbb8676ab3391f02afec2))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([9a0eb47](https://github.com/IA-Generative/abrege/commit/9a0eb474ee4aa1c16ffe411a28b7a1c6ccefbb33))
* :adhesive_bandage: stringData dans le kubectl patch secret ([94bfddd](https://github.com/IA-Generative/abrege/commit/94bfddde11fb7834442dfebeb0bfa6fc6df7d081))
* :alembic: nouveau model par défaut fastapi ([e431385](https://github.com/IA-Generative/abrege/commit/e4313858adb7d844784a933966a3297463d0345d))
* :ambulance: middleware dans le bon ordre ([e0937a8](https://github.com/IA-Generative/abrege/commit/e0937a8744a8d55bd2b379c17260cbd0369ea14e))
* :ambulance: summary comme modèle par défaut ([89e7727](https://github.com/IA-Generative/abrege/commit/89e7727356221b9bc4a3462bcf877c476a1f2351))
* :ambulance: try fix route /api/doc ([49e6730](https://github.com/IA-Generative/abrege/commit/49e6730b75d8c205cee3c18aaceb95713b96602c))
* :ambulance: try fix route /text ([44390bd](https://github.com/IA-Generative/abrege/commit/44390bd5b10c6a562a7406ead8ac6fd67305f858))
* :bug: add regex cors ([f461fd3](https://github.com/IA-Generative/abrege/commit/f461fd390c2392d11a64c8f59f8679ce002da9b6))
* :bug: try fix /root/nltk_data issue ([eb70e7f](https://github.com/IA-Generative/abrege/commit/eb70e7f45b2bb33215be91a673de7e034e95130f))
* :bug: try fix /root/nltk_data issue ([d23a29c](https://github.com/IA-Generative/abrege/commit/d23a29cd7a3b13d63eea015072548425f78a2f02))
* :construction: restauration ancienne api + meilleurs param par défaut ([ad0b2dd](https://github.com/IA-Generative/abrege/commit/ad0b2ddaa0c54642a60b286e02ee58349ec8d135))
* :construction: restauration ancienne api + meilleurs param par défaut ([bcdd46a](https://github.com/IA-Generative/abrege/commit/bcdd46ad68ac7ea305b973c1d762e61cb870a4d0))
* :construction: restauration ancienne api + meilleurs param par défaut ([5753b9d](https://github.com/IA-Generative/abrege/commit/5753b9dd085c37e6a3c1586a443cc58982dc981c))
* :construction: try fix ci/cd ([636eeaf](https://github.com/IA-Generative/abrege/commit/636eeafdc4d0249791da2e5f80f98968c0b24386))
* :construction: try fix ci/cd ([a1dcd06](https://github.com/IA-Generative/abrege/commit/a1dcd06c4ce2bbd50ea9171dfbb785727a10e392))
* :construction: try fix ci/cd ([730bd07](https://github.com/IA-Generative/abrege/commit/730bd07acb67b60c9fa8aee621f0c18eb04ba63f))
* :construction: try fix ci/Cd ([d6295a1](https://github.com/IA-Generative/abrege/commit/d6295a1272edac527e739f29846cf3191c17a5b3))
* :construction: try fix docker compose ([8a21976](https://github.com/IA-Generative/abrege/commit/8a21976f9148fb0943a32632a17acbda7978b2ac))
* :poop: augmentation des limites ([ed5e0da](https://github.com/IA-Generative/abrege/commit/ed5e0da1e602ea78d1eea6dfe9616e3e816ba5cf))
* :poop: augmentation des limites ([0da344f](https://github.com/IA-Generative/abrege/commit/0da344f8ea5549a315b0a7557aaf4bac90c5fd62))
* :poop: CORS allow any origin ([da18055](https://github.com/IA-Generative/abrege/commit/da180557508e2aebc859b20d491ee34299b10457))
* :poop: weak CORS_REGEXP=.* ([b708090](https://github.com/IA-Generative/abrege/commit/b7080907e2677dfc58d1f1f7a44b771a0117d190))
* / for routes ([5fb559e](https://github.com/IA-Generative/abrege/commit/5fb559eda5fe459248b0a361e2d7682eb6aa5751))
* abrege name ([b3ce04b](https://github.com/IA-Generative/abrege/commit/b3ce04bfd5021207aa85afbca6f19688e6eb7491))
* add api ([2adf7d0](https://github.com/IA-Generative/abrege/commit/2adf7d051b7ccabfb89e088ff90e0238afb08652))
* add audio schema ([a794c8b](https://github.com/IA-Generative/abrege/commit/a794c8b93766fd79afe17f88d0fa6bd7e1ac30e0))
* add client in right domain ([8877d41](https://github.com/IA-Generative/abrege/commit/8877d4132b88249fac2a0089280464e9ae4f9e1e))
* add health ([#103](https://github.com/IA-Generative/abrege/issues/103)) ([39ef458](https://github.com/IA-Generative/abrege/commit/39ef458f40b24edcf85eb059098346795e2a8b13))
* add hf_model ([4272a79](https://github.com/IA-Generative/abrege/commit/4272a79069202fb4ee642e7ee2c547e63140b654))
* add log debug ([43e5d9c](https://github.com/IA-Generative/abrege/commit/43e5d9c25d781ddae7d6a402925e141ab918d7d1))
* add logger ([9c52f92](https://github.com/IA-Generative/abrege/commit/9c52f92366a8edae50d7229705d8a454c5cecf75))
* add logger ([cb7f93e](https://github.com/IA-Generative/abrege/commit/cb7f93ed71b3be0422b143cc73f767ecc7104f8e))
* add MAX_CONTEXT_SIZE variables ([8f53612](https://github.com/IA-Generative/abrege/commit/8f536120d93c3afa37d3cf9cb9977abb582f21a8))
* add more log ([5b878fd](https://github.com/IA-Generative/abrege/commit/5b878fd5d69732f06aee07c5f75d3aa7aa3565d5))
* add more log ([fa83a7c](https://github.com/IA-Generative/abrege/commit/fa83a7cac295b7aeec38cf9bd28cecd514ab4dd9))
* add more log ([51af2b9](https://github.com/IA-Generative/abrege/commit/51af2b9e378dc9acf2bc02b70106993ecb23a99c))
* add more log ([11f9f29](https://github.com/IA-Generative/abrege/commit/11f9f2996527e4ab06ccbe102c1b9e4a8d387fbd))
* add more log ([#144](https://github.com/IA-Generative/abrege/issues/144)) ([#145](https://github.com/IA-Generative/abrege/issues/145)) ([#146](https://github.com/IA-Generative/abrege/issues/146)) ([#147](https://github.com/IA-Generative/abrege/issues/147)) ([803c31b](https://github.com/IA-Generative/abrege/commit/803c31bba2d87a08c7550f2c77c19ddb4cb712ff))
* add more video ([e116051](https://github.com/IA-Generative/abrege/commit/e1160510539c30adea42d263eb77f09df1d2029d))
* add packages ([61b241e](https://github.com/IA-Generative/abrege/commit/61b241e2d85055541c3494fbd4d8b239bfa3c83d))
* add retry and log to api call for llm call ([ada6d7c](https://github.com/IA-Generative/abrege/commit/ada6d7c47aa432bbe19af986f4c5deb6d2127fd0))
* add retry and log to api call for llm call ([#149](https://github.com/IA-Generative/abrege/issues/149)) ([075bcbd](https://github.com/IA-Generative/abrege/commit/075bcbd4876aecc0f1c7d493190d278341c6c065))
* add size in document ([36aca9b](https://github.com/IA-Generative/abrege/commit/36aca9b220aaca3d98314312844c449f5dfea3f1))
* add tags ([8737077](https://github.com/IA-Generative/abrege/commit/8737077ba6e060a9cc4ce9acdd4cc259614b5974))
* add x-wav data ([867fec9](https://github.com/IA-Generative/abrege/commit/867fec9e3d5acf1350b1abe63e0e1c27fd7300a8))
* an other permission denied ([05a0265](https://github.com/IA-Generative/abrege/commit/05a02653a16ccd08374b67a4f9d89f08fa857780))
* an other permission denied ([8411867](https://github.com/IA-Generative/abrege/commit/8411867cb8975a630e951dffec31ab04f205f4c1))
* annotation ([040152f](https://github.com/IA-Generative/abrege/commit/040152f02128015789bbcae70de54bb1345093c4))
* by using / ([#110](https://github.com/IA-Generative/abrege/issues/110)) ([2107d80](https://github.com/IA-Generative/abrege/commit/2107d805fa70a1434d78812c8a26888617ddbe5d))
* cache app ([124e634](https://github.com/IA-Generative/abrege/commit/124e6342900368f0e94079558e4465a7709e633e))
* cache dir for uv ([4a1c2aa](https://github.com/IA-Generative/abrege/commit/4a1c2aaa71ea7c8a9742425d901af3573788a132))
* ci deployement ([#102](https://github.com/IA-Generative/abrege/issues/102)) ([c5136ea](https://github.com/IA-Generative/abrege/commit/c5136eaa8095592ec2ef39d3201e3b74488dbe07))
* clean code ([86a912e](https://github.com/IA-Generative/abrege/commit/86a912ec999f3578d0c0d95ddea713dd5f81b803))
* clean dockerfile ([b92101e](https://github.com/IA-Generative/abrege/commit/b92101eda390c53943cd1696306b6d7732a95d60))
* correct project version to 0.0.3 in pyproject.toml ([d116ce0](https://github.com/IA-Generative/abrege/commit/d116ce01b54da4e4314054c94e631c9bb8e1f566))
* cors and url parse ([d81db88](https://github.com/IA-Generative/abrege/commit/d81db88a21ff84911ad10464a3b5def980682adb))
* cors api ([166792e](https://github.com/IA-Generative/abrege/commit/166792e52f810b580bfdd38997f3c558b3fb04be))
* delete notebook ([222c841](https://github.com/IA-Generative/abrege/commit/222c841603edc2d0e674ec528632b2c54bf091c1))
* delete template ([afc66ca](https://github.com/IA-Generative/abrege/commit/afc66cad875b306042b12964694385a7deab577c))
* deployement with nltk ([e3c4d64](https://github.com/IA-Generative/abrege/commit/e3c4d644dc07abf2c09ccfc8e3408405c9c3b134))
* document pssed ([27749ba](https://github.com/IA-Generative/abrege/commit/27749ba1c5b5c3c9bfce4e5cfdf4ed09896ac01e))
* don't delete video ([bcb0c0b](https://github.com/IA-Generative/abrege/commit/bcb0c0b76a5e0330cf860e2bf7edaf044ffd8094))
* don't forget to dl model ([9bfb6a3](https://github.com/IA-Generative/abrege/commit/9bfb6a3f3a95caaf0b3d05c05607ff4e5c493b85))
* don't save raw transformation ([3cd06aa](https://github.com/IA-Generative/abrege/commit/3cd06aa037f6e89b2f1e78f8432b80d28bae745d))
* don't use applicatif timeout ([32bb18b](https://github.com/IA-Generative/abrege/commit/32bb18b009cf7bd31321baa90cfcde6d1e119311))
* don't use marker api ([5dc4e4d](https://github.com/IA-Generative/abrege/commit/5dc4e4d5c7251b7761709d4c0e46e956995d878f))
* download nltk package ([9c7cadb](https://github.com/IA-Generative/abrege/commit/9c7cadb01d902c3c2982139cb5eb993bd637b9c8))
* download only need ([ad8ca7e](https://github.com/IA-Generative/abrege/commit/ad8ca7e58bf3561aaa29579d0dab12b98cec3008))
* dso ([0914699](https://github.com/IA-Generative/abrege/commit/09146993031aae2564a4a4a2828cbfdaf6eb16a0))
* encoding ([86a0cfb](https://github.com/IA-Generative/abrege/commit/86a0cfba580b5edb232c549b33995700508f0a25))
* env variables ([4a302a2](https://github.com/IA-Generative/abrege/commit/4a302a201a6d4371823f7c9ab87fff768a7e1f07))
* example ([#108](https://github.com/IA-Generative/abrege/issues/108)) ([b5bc7e5](https://github.com/IA-Generative/abrege/commit/b5bc7e579eb5b29f5fa2dba989a29d761d3cc491))
* fix -c ([19a011c](https://github.com/IA-Generative/abrege/commit/19a011cb178959ce2fc20e4855b8ba5b4db088bb))
* fix metrics evaluations ([1110247](https://github.com/IA-Generative/abrege/commit/11102475753da193780af2319697890fc20d9dda))
* fix run ([d98da58](https://github.com/IA-Generative/abrege/commit/d98da58357ed8d509c6ea6a600ad3775cfb6d517))
* for html content ([8e868b7](https://github.com/IA-Generative/abrege/commit/8e868b75eee51b08ddfeae8dce0cc6554a8a038a))
* for to dowload if not present ([e911d5e](https://github.com/IA-Generative/abrege/commit/e911d5ee00251df4d9171a81a12cddf66eb7750b))
* format JSONResponse and improve CORS middleware setup ([b7bd1fa](https://github.com/IA-Generative/abrege/commit/b7bd1fa3909db141732448779cb9cb22ef88d410))
* format JSONResponse and update default origins in set_cors function ([bbfd5c6](https://github.com/IA-Generative/abrege/commit/bbfd5c6e01566ebecb3e18d932daad671ec777b2))
* giive partial result ([5c0f767](https://github.com/IA-Generative/abrege/commit/5c0f76758fa8e8c3950daeb7e943fda280347eb1))
* health ([c2d7e66](https://github.com/IA-Generative/abrege/commit/c2d7e66751c7fe8a31131b8988ead56a244c30a7))
* if text is not provide ([5b4302e](https://github.com/IA-Generative/abrege/commit/5b4302e56ebde4af7f58ed39fefce33062baf825))
* ignore prod ([b02e964](https://github.com/IA-Generative/abrege/commit/b02e964bb4b4b9f45b7815694449342ce1df247b))
* import path ([00af728](https://github.com/IA-Generative/abrege/commit/00af7288fc6b01d8e5f5a58dce173ad3ac5031d9))
* jsonresponse ([1920481](https://github.com/IA-Generative/abrege/commit/1920481805a7820cd8f0411f5086bc849f9a3284))
* make it more speed ([461b873](https://github.com/IA-Generative/abrege/commit/461b873694bd339c5127a1c5eb45b67f06f538d2))
* make more speed ([acdd446](https://github.com/IA-Generative/abrege/commit/acdd446d698d351d5fa97e443111f3619a8280f1))
* map_reduce langchain bug ([f25d5a5](https://github.com/IA-Generative/abrege/commit/f25d5a5453d7c022dc603dc6eb6dc2647898a0c4))
* map_reduce langchain bug ([3dfb7fd](https://github.com/IA-Generative/abrege/commit/3dfb7fd9de5cdecf39fd576729377cb6ef08156c))
* migration script ([d3044c6](https://github.com/IA-Generative/abrege/commit/d3044c637d7bb920f084750da67009ba7b1c9061))
* mode ([28252af](https://github.com/IA-Generative/abrege/commit/28252af3e7648808510975172105e77bb4e95e45))
* move utils ([ba7e4c7](https://github.com/IA-Generative/abrege/commit/ba7e4c7f08bc32d0ba31d17d3b8d5e8b2aa8fa07))
* naive aproche using token ([88b47e8](https://github.com/IA-Generative/abrege/commit/88b47e84f3797ba78c558d98e08c5d98a8670483))
* now gh action on arc-runner ([0d4a29f](https://github.com/IA-Generative/abrege/commit/0d4a29f281d53a9adc6f5a7dffe1e42bb8c3fd5a))
* OCR API ([bf032bf](https://github.com/IA-Generative/abrege/commit/bf032bfc3f38ed0922a828100b57831be415a48f))
* package fix ([#136](https://github.com/IA-Generative/abrege/issues/136)) ([6ed7101](https://github.com/IA-Generative/abrege/commit/6ed7101a4d0f7636b0308a70985e72a0c645d7f8))
* path ([0591a2b](https://github.com/IA-Generative/abrege/commit/0591a2ba945c167ade86f62548a50af6b412c3ff))
* permission denied in images ([665981f](https://github.com/IA-Generative/abrege/commit/665981fcd81365be8ddfe447ea4d5e6e6d98b271))
* port 8000 ([58bbb03](https://github.com/IA-Generative/abrege/commit/58bbb0363907da73b60e9ef86971f7b35d6fe325))
* port to 5000 to unify ([49cb507](https://github.com/IA-Generative/abrege/commit/49cb507769c95e2a34aeb0b67ffbe74a5b2cd93a))
* prompt map reduce ([366e0aa](https://github.com/IA-Generative/abrege/commit/366e0aaa2601d9fffd9089c8b34354b316c61297))
* prompt map reduce ([ce6a0f6](https://github.com/IA-Generative/abrege/commit/ce6a0f64683fb9aa345993739e1b26447307c7f8))
* refactor fieldname ([29753c3](https://github.com/IA-Generative/abrege/commit/29753c3920d426799e4ff3d847aadd40e9104ce7))
* reload ([56b8714](https://github.com/IA-Generative/abrege/commit/56b871428044776b80f6bec7c11d293d41291364))
* remove audio file at the end ([630a560](https://github.com/IA-Generative/abrege/commit/630a560491ea893bbfcef9b990d1a69f0812173b))
* remove data ([58fbe0f](https://github.com/IA-Generative/abrege/commit/58fbe0fb33c6f28f1fd604757e6002fc3de65464))
* retirer la température pour monsieur tout le monde ([7585ae0](https://github.com/IA-Generative/abrege/commit/7585ae02e765a6d6d0dcb57b7002cf8996956b4a))
* s3 big file in memory ([c2018fb](https://github.com/IA-Generative/abrege/commit/c2018fbc82567e1a8b4b3854d45e90eb5bebf4ee))
* schemas import ([3d0dd04](https://github.com/IA-Generative/abrege/commit/3d0dd04333bbdb929cf275d3526bf1c309037161))
* separate routes ([6797197](https://github.com/IA-Generative/abrege/commit/6797197555534a2a640f0df8bae32e4a86166997))
* set cors and add url router ([be37604](https://github.com/IA-Generative/abrege/commit/be37604a98b3fc2958640bad7c3a89ee52318406))
* splitext by token ([830f353](https://github.com/IA-Generative/abrege/commit/830f353cf4731b65da230f898fd4ca1302a0c6a6))
* sync modules ([9731a1b](https://github.com/IA-Generative/abrege/commit/9731a1b6dbfa2fb9266a476d62fe87f9fa1da902))
* task update ([ac6b9e4](https://github.com/IA-Generative/abrege/commit/ac6b9e480dd0875368ed8b80b3a538abcea19563))
* test to stream ([02f90c5](https://github.com/IA-Generative/abrege/commit/02f90c54be569ed7b2bbb4addb529c387a6c2f39))
* test token based ([8b874b5](https://github.com/IA-Generative/abrege/commit/8b874b5ed8dd915d834862a80ddbd6faf3c02165))
* try catch to get errors ([afee0bd](https://github.com/IA-Generative/abrege/commit/afee0bde6bffc7afdfba45671682786099c1e8f1))
* typo ([ff248c9](https://github.com/IA-Generative/abrege/commit/ff248c99a6890c3d200f056d874316a53898d387))
* typo into var name ([958b9e3](https://github.com/IA-Generative/abrege/commit/958b9e3a842467b374c319ad57e0c065dff4af82))
* unitest ([125e627](https://github.com/IA-Generative/abrege/commit/125e627f5a513b06c0db700ceef95e1864221827))
* update project version to 2.0.1 ([d216a59](https://github.com/IA-Generative/abrege/commit/d216a596e7e74c71966e830a8bd3296aef8e3fc0))
* url png ([d265140](https://github.com/IA-Generative/abrege/commit/d265140145c5a76b9f9ae02269802de56e4bd7fa))
* use batch process ([134a48f](https://github.com/IA-Generative/abrege/commit/134a48ffcc356754b31c0b07c1325cbe0e0b6262))
* use default model name ([5525ce5](https://github.com/IA-Generative/abrege/commit/5525ce56130a68e044bbc3e4962605e090103a47))
* use dockerfile ([6499eff](https://github.com/IA-Generative/abrege/commit/6499effad58077d6242e5bcc89812d5bc3b509bc))
* use env file ([a34cdef](https://github.com/IA-Generative/abrege/commit/a34cdef7aafe5f57fd80601a4191a8ec1b1511c7))
* use env var ([75fb200](https://github.com/IA-Generative/abrege/commit/75fb200acc33aef2c14f69154fb8f72edcc49ebb))
* use get instead of post ([01fd984](https://github.com/IA-Generative/abrege/commit/01fd984738c187ba7fd741dceed059d1db23dc48))
* use ocr instead of llm ([dc3f2d8](https://github.com/IA-Generative/abrege/commit/dc3f2d8169555fb83d88af3f1595161e6a9d582a))
* use only boto3 ([2c581a1](https://github.com/IA-Generative/abrege/commit/2c581a1f0a6996c57a16b4eb6aac2f86b070f55e))
* use rght env ([b939f3e](https://github.com/IA-Generative/abrege/commit/b939f3e21b47a30e71ff7a1a162b6ad9a0ad11d1))
* use right folder name ([92b61d9](https://github.com/IA-Generative/abrege/commit/92b61d9f9f93d3a9b3a3315f015abaf3e0b612fd))
* use right url folder ([5601e2f](https://github.com/IA-Generative/abrege/commit/5601e2f3905a4bc5fb4918fed6f035707250513c))
* use right version ([23d2b97](https://github.com/IA-Generative/abrege/commit/23d2b97a6fe0ff1282e07982e70495b7d75a1d5e))
* utf-8 encoding ([32d0aab](https://github.com/IA-Generative/abrege/commit/32d0aab40e638beb1423e079b071fa0da7d1707f))
* uv cache ([c96e112](https://github.com/IA-Generative/abrege/commit/c96e112016ae07312cc775c43fbb532467462572))
* uv.lock ([b808a8d](https://github.com/IA-Generative/abrege/commit/b808a8d48aec303176c8a1409f415eba320080f9))
* video to audio ([c659bf3](https://github.com/IA-Generative/abrege/commit/c659bf39eb35b14e154bf660baf6113a28a0d4bf))

## [3.0.0](https://github.com/IA-Generative/abrege/compare/v2.0.0...v3.0.0) (2025-07-10)


### ⚠ BREAKING CHANGES

* feature add abrege most anything

### Features

* :alembic: ajout erreur surcharge LLM et surcharge OCR ([4df0971](https://github.com/IA-Generative/abrege/commit/4df0971fa9a85cee0dcd926d2c87b9ae74c8a7c2))
* :alembic: ajout erreur surcharge LLM et surcharge OCR ([88f23d3](https://github.com/IA-Generative/abrege/commit/88f23d3c56a6622cd6bc0192a47239c0ab693ac4))
* :ambulance: map_reduce comme méthode par défaut ([31c48d2](https://github.com/IA-Generative/abrege/commit/31c48d23673528ada7e5617e938872c8e1a00fac))
* :bug: install nltk package during build time ([fb544f9](https://github.com/IA-Generative/abrege/commit/fb544f9d6c4e6df4d25a0fa2b327d160976ff30f))
* :bug: install nltk package during build time ([ca82c7f](https://github.com/IA-Generative/abrege/commit/ca82c7ff58df3a8902df2306842a42f6de3fa490))
* :construction: tous les params dans le request body ([f480396](https://github.com/IA-Generative/abrege/commit/f4803964861f3d7fb06dfb7192ad731496b7321e))
* :goal_net: meilleure gestion des erreurs ([dbf092b](https://github.com/IA-Generative/abrege/commit/dbf092bf0bb0abb4378a14db8e21f92f7cbf5fc0))
* :goal_net: meilleure gestion des erreurs ([4892f8f](https://github.com/IA-Generative/abrege/commit/4892f8f7bc2aab952c00e3822192aa9cacefdeac))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([e2dc5be](https://github.com/IA-Generative/abrege/commit/e2dc5be2b7d54563ab1339709da63725c0a9286e))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([3b69c4e](https://github.com/IA-Generative/abrege/commit/3b69c4e3ab98c6364f11e0b30af7f67eb829ede2))
* :poop: ajout limite ocr et nombre tokens ([70b7ddf](https://github.com/IA-Generative/abrege/commit/70b7ddf9b279ebd03dd48d30e4a241b18fb884c5))
* :poop: ajout limite ocr et nombre tokens ([2d640d2](https://github.com/IA-Generative/abrege/commit/2d640d2ae3519d1f4138a4acec6d23f7f25155bb))
* :sparkles: add CORS_REGEXP ([77293db](https://github.com/IA-Generative/abrege/commit/77293dba26c954a59634d509701804bc66d132b8))
* :sparkles: add OPENAI_API_MODEL ([f0ed789](https://github.com/IA-Generative/abrege/commit/f0ed78928c6194d1c3afd92560b014055eddf4d4))
* :sparkles: ajout map_prompt et reduce_prompt ([9d35720](https://github.com/IA-Generative/abrege/commit/9d35720bd7cf49eb4fdcdfcf660b22ade3a16cb1))
* :sparkles: ajout map_prompt et reduce_prompt ([686afb2](https://github.com/IA-Generative/abrege/commit/686afb246f47d1a816ef68d54eaecc6aa1d48e49))
* :sparkles: ajout map_prompt et reduce_prompt ([b98d8c8](https://github.com/IA-Generative/abrege/commit/b98d8c849396579b5d993b9a6c8adba716cb01d4))
* :sparkles: correction qq bugs ([441cba2](https://github.com/IA-Generative/abrege/commit/441cba299274fa16e3fa8ee9b10d682202c77a81))
* :sparkles: correction qq bugs ([9d91434](https://github.com/IA-Generative/abrege/commit/9d91434ffdc22d705770fafc9ac31c2721a6c352))
* :sparkles: map reduce dans abrege-api ([6b27d97](https://github.com/IA-Generative/abrege/commit/6b27d973908e4021ed124cdbaeb90dac0652cfa6))
* :sparkles: map reduce dans abrege-api ([ecc18cc](https://github.com/IA-Generative/abrege/commit/ecc18cc9b420d94f5c5b47e04a04861b7c4cb071))
* :sparkles: map reduce dans abrege-api ([bdc5778](https://github.com/IA-Generative/abrege/commit/bdc5778d5dd1929d90df0941bcfb9523e3768f7c))
* :sparkles: schema pydantic pour les réponses ([cbca0ce](https://github.com/IA-Generative/abrege/commit/cbca0cea574374944fda78842d299e9b6db12506))
* :sparkles: schema pydantic pour les réponses ([6236b8c](https://github.com/IA-Generative/abrege/commit/6236b8c712db334638b0e9537d66377fc2bfba49))
* add audio service to text ([44f5823](https://github.com/IA-Generative/abrege/commit/44f5823b81ebc61457d375d2a3d9ac5037376188))
* add basemodel service ([dd11a6c](https://github.com/IA-Generative/abrege/commit/dd11a6c5644d58c4ee63b623ef20e268fbbe7a73))
* add celery capacity ([6fee425](https://github.com/IA-Generative/abrege/commit/6fee425475e8c08e9436991f10026e20cc6034db))
* add celery component ([89b93ed](https://github.com/IA-Generative/abrege/commit/89b93eda7e9492601bb864d7eb3798109f348543))
* add content type ([5b11c41](https://github.com/IA-Generative/abrege/commit/5b11c419fb0900993f67570027ea51da47f51e72))
* add context length feat ([52b340f](https://github.com/IA-Generative/abrege/commit/52b340f3c0434d40c1985b127610a4d697bbc884))
* add dockerfile ([2b70e89](https://github.com/IA-Generative/abrege/commit/2b70e8900eb0c2749f8e60330e2b13733b870f33))
* add document parsing ([a1bfc94](https://github.com/IA-Generative/abrege/commit/a1bfc94f4952dddb5abd2fc89bad45b480319a72))
* add document to markdown ([9ce92f5](https://github.com/IA-Generative/abrege/commit/9ce92f59d5ef5a1aa7b03bb0e720963e9a3027c2))
* add evaluation metrics ([6db31e6](https://github.com/IA-Generative/abrege/commit/6db31e616b2f8f514373456c4706795103a3ba27))
* add file available for process ([00aa764](https://github.com/IA-Generative/abrege/commit/00aa764420761aa3d81685b4a0ea604032528396))
* add global percentage ([92092bb](https://github.com/IA-Generative/abrege/commit/92092bbaabc325410eb63f64372da0eece232204))
* add LibreOffice document support and related tests ([#126](https://github.com/IA-Generative/abrege/issues/126)) ([#127](https://github.com/IA-Generative/abrege/issues/127)) ([#128](https://github.com/IA-Generative/abrege/issues/128)) ([86dfa54](https://github.com/IA-Generative/abrege/commit/86dfa547f8108d3e7d17c699d0a9d7fbbe63d064))
* add migration images ([6a75b7d](https://github.com/IA-Generative/abrege/commit/6a75b7dbca70fc7c3d1e9e4b5e7405cb5451e637))
* add more details health ([98dd7d2](https://github.com/IA-Generative/abrege/commit/98dd7d29c9ce58a9b160dd5da783b4ef746e2851))
* add more log ([3cbd7dc](https://github.com/IA-Generative/abrege/commit/3cbd7dc977e65bf404c5559420fbeff91bca3424))
* add naive approach ([3ed3228](https://github.com/IA-Generative/abrege/commit/3ed32282f19f3feda1e37a901edbfa97cd1d59a3))
* add naive approach ([73d54e6](https://github.com/IA-Generative/abrege/commit/73d54e6f0a087b98aab86dc9c1fafe4b952aca98))
* add naive sumup approch ([759769c](https://github.com/IA-Generative/abrege/commit/759769c0fea48459ea76534363a7f0ab45b6fc55))
* add ocr purpose ([f5d1ea1](https://github.com/IA-Generative/abrege/commit/f5d1ea11ed5e26f500a5085061c163ce7f66a77d))
* add parameters ([8f67d39](https://github.com/IA-Generative/abrege/commit/8f67d39a5b7948a5a014d9a52c5e1adfa9da0eec))
* add parameters ([c6ed937](https://github.com/IA-Generative/abrege/commit/c6ed9370e23ecdd467a4bb80124880f0b4a4e5ef))
* add parameters ([7785e01](https://github.com/IA-Generative/abrege/commit/7785e01d88a4e1fc561714a085657c28a684371d))
* add plain text ([16be659](https://github.com/IA-Generative/abrege/commit/16be659a0b50558684d249b6168d8e95bcefff1b))
* add position ([#107](https://github.com/IA-Generative/abrege/issues/107)) ([d0b00b0](https://github.com/IA-Generative/abrege/commit/d0b00b0da11e3866a12ea1c846cf983319509db2))
* add prompting resolution ([48ee55e](https://github.com/IA-Generative/abrege/commit/48ee55e7ce902a210325c3a660a790671ebfd3de))
* add retrieve version ([930116e](https://github.com/IA-Generative/abrege/commit/930116e6c3ab147b69b403b71d37f2b594bc330b))
* add retry on llm ([a3f5d9c](https://github.com/IA-Generative/abrege/commit/a3f5d9cce6a36de428d2d835088945a83fb12db1))
* add s3 and minio connector ([1f126e0](https://github.com/IA-Generative/abrege/commit/1f126e0d989ce7854687bf40985b405d0a2aaef8))
* add small migration ([923093e](https://github.com/IA-Generative/abrege/commit/923093ead46362cd7059ff4d3cee75681fca5df5))
* add summay model ([c0b10c6](https://github.com/IA-Generative/abrege/commit/c0b10c69ad41fa11a1afd21eba875b1ff27d3f7d))
* add task ([7d92dd2](https://github.com/IA-Generative/abrege/commit/7d92dd243f501cb39dcbbdb452c200a0d6c76d8f))
* add task process to audio ([953e546](https://github.com/IA-Generative/abrege/commit/953e54637e0d47934821130848ccf266ea5fb106))
* add task router ([c26df52](https://github.com/IA-Generative/abrege/commit/c26df524bcefc76e3481988ab080fa8de1b57908))
* add task status to HTTP status mapping and corresponding tests ([adea495](https://github.com/IA-Generative/abrege/commit/adea49553c2e89337c99dd09aec9105d429722a9))
* add text splitter ([e335a83](https://github.com/IA-Generative/abrege/commit/e335a832ad436c11ea89af273592631f0e418f00))
* add tokenizer into process ([c38717e](https://github.com/IA-Generative/abrege/commit/c38717eb94d38cc11bafadb08afe1648c56515e2))
* add tokenizer to split text ([e95a9be](https://github.com/IA-Generative/abrege/commit/e95a9be71647c5fdf3a5568c927d920bd62156ee))
* add url and flat text ([5472d87](https://github.com/IA-Generative/abrege/commit/5472d873e7bb56596c42b51a4e976a2be4a7ec8c))
* add url detector ([6194644](https://github.com/IA-Generative/abrege/commit/6194644947683c7edbed28e9287f1fe45dac713e))
* add url modules ([a16e0fc](https://github.com/IA-Generative/abrege/commit/a16e0fc4588a7b8700c3b581c22b794c360da191))
* add video process ([017eeb1](https://github.com/IA-Generative/abrege/commit/017eeb1473598a9fefc95427b0f6c0b18d5ae5b6))
* add video transcription service ([2952609](https://github.com/IA-Generative/abrege/commit/2952609ffdfb6fa76a3b1dbf5c895b968e5f6cf0))
* ajout du custom prompt pour l'utilisateur ([29a8612](https://github.com/IA-Generative/abrege/commit/29a861209fa9eca6e72ce0683dae5655e60c4919))
* based on task ([e360421](https://github.com/IA-Generative/abrege/commit/e360421a48e79c202881015c9d859e7d45c24e3c))
* combine ocr client ([8fa89ca](https://github.com/IA-Generative/abrege/commit/8fa89ca21409633cec2b68b4a8a249d936b73f2e))
* feature add abrege most anything ([b705167](https://github.com/IA-Generative/abrege/commit/b7051671477d344392c182ae2d717daa1c357c43))
* fix ocr integration ([1fe8828](https://github.com/IA-Generative/abrege/commit/1fe8828b1134cf407c92aea54fdd153a0ffa8b8d))
* hide button ([265b016](https://github.com/IA-Generative/abrege/commit/265b0168d013554c02274b086f49315fe858ef19))
* hide expert ui ([6a61a21](https://github.com/IA-Generative/abrege/commit/6a61a21f14372d7d9ca7035e3d36a8505318d043))
* hide expert ui ([337eae6](https://github.com/IA-Generative/abrege/commit/337eae6704eb9760c7de7e641b47470e0f1ea8b3))
* new default model ([9bc5816](https://github.com/IA-Generative/abrege/commit/9bc58162d27024daa51de4da9044583b33e47d70))
* refactor process ([a8706a4](https://github.com/IA-Generative/abrege/commit/a8706a45fdfee39e1c924274f9a3c93a80a9b30c))
* reploy-hash ([efcd833](https://github.com/IA-Generative/abrege/commit/efcd83315c524f275646104c9f45574192482af0))
* send document to redis ([5f7042a](https://github.com/IA-Generative/abrege/commit/5f7042ac629c93021d4c965b54175cfffbe8927b))
* use APP_SECRETS in gh action ([edb3fc9](https://github.com/IA-Generative/abrege/commit/edb3fc97d34912986d654b47196188d6253d017a))
* use model service ([a281bb7](https://github.com/IA-Generative/abrege/commit/a281bb70f9eb31166601c78358825a7f8e2e3723))
* use services approach ([ad4ca7a](https://github.com/IA-Generative/abrege/commit/ad4ca7a7d0c8d38651132f40a1ed0b0b8f2b5928))


### Bug Fixes

* :adhesive_bandage: code erreur à 500 au lieu de 422 ([ffa7293](https://github.com/IA-Generative/abrege/commit/ffa7293cf666b26eecf538de05352160cb8f3f74))
* :adhesive_bandage: code erreur à 500 au lieu de 422 ([baed080](https://github.com/IA-Generative/abrege/commit/baed0809246ec9cd67f1f89076ac3e3ab7ff54ed))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([03b23ae](https://github.com/IA-Generative/abrege/commit/03b23ae966e273822b0fbb8676ab3391f02afec2))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([9a0eb47](https://github.com/IA-Generative/abrege/commit/9a0eb474ee4aa1c16ffe411a28b7a1c6ccefbb33))
* :adhesive_bandage: stringData dans le kubectl patch secret ([94bfddd](https://github.com/IA-Generative/abrege/commit/94bfddde11fb7834442dfebeb0bfa6fc6df7d081))
* :alembic: nouveau model par défaut fastapi ([e431385](https://github.com/IA-Generative/abrege/commit/e4313858adb7d844784a933966a3297463d0345d))
* :ambulance: middleware dans le bon ordre ([e0937a8](https://github.com/IA-Generative/abrege/commit/e0937a8744a8d55bd2b379c17260cbd0369ea14e))
* :ambulance: summary comme modèle par défaut ([89e7727](https://github.com/IA-Generative/abrege/commit/89e7727356221b9bc4a3462bcf877c476a1f2351))
* :ambulance: try fix route /api/doc ([49e6730](https://github.com/IA-Generative/abrege/commit/49e6730b75d8c205cee3c18aaceb95713b96602c))
* :ambulance: try fix route /text ([44390bd](https://github.com/IA-Generative/abrege/commit/44390bd5b10c6a562a7406ead8ac6fd67305f858))
* :bug: add regex cors ([f461fd3](https://github.com/IA-Generative/abrege/commit/f461fd390c2392d11a64c8f59f8679ce002da9b6))
* :bug: try fix /root/nltk_data issue ([eb70e7f](https://github.com/IA-Generative/abrege/commit/eb70e7f45b2bb33215be91a673de7e034e95130f))
* :bug: try fix /root/nltk_data issue ([d23a29c](https://github.com/IA-Generative/abrege/commit/d23a29cd7a3b13d63eea015072548425f78a2f02))
* :construction: restauration ancienne api + meilleurs param par défaut ([ad0b2dd](https://github.com/IA-Generative/abrege/commit/ad0b2ddaa0c54642a60b286e02ee58349ec8d135))
* :construction: restauration ancienne api + meilleurs param par défaut ([bcdd46a](https://github.com/IA-Generative/abrege/commit/bcdd46ad68ac7ea305b973c1d762e61cb870a4d0))
* :construction: restauration ancienne api + meilleurs param par défaut ([5753b9d](https://github.com/IA-Generative/abrege/commit/5753b9dd085c37e6a3c1586a443cc58982dc981c))
* :construction: try fix ci/cd ([636eeaf](https://github.com/IA-Generative/abrege/commit/636eeafdc4d0249791da2e5f80f98968c0b24386))
* :construction: try fix ci/cd ([a1dcd06](https://github.com/IA-Generative/abrege/commit/a1dcd06c4ce2bbd50ea9171dfbb785727a10e392))
* :construction: try fix ci/cd ([730bd07](https://github.com/IA-Generative/abrege/commit/730bd07acb67b60c9fa8aee621f0c18eb04ba63f))
* :construction: try fix ci/Cd ([d6295a1](https://github.com/IA-Generative/abrege/commit/d6295a1272edac527e739f29846cf3191c17a5b3))
* :construction: try fix docker compose ([8a21976](https://github.com/IA-Generative/abrege/commit/8a21976f9148fb0943a32632a17acbda7978b2ac))
* :poop: augmentation des limites ([ed5e0da](https://github.com/IA-Generative/abrege/commit/ed5e0da1e602ea78d1eea6dfe9616e3e816ba5cf))
* :poop: augmentation des limites ([0da344f](https://github.com/IA-Generative/abrege/commit/0da344f8ea5549a315b0a7557aaf4bac90c5fd62))
* :poop: CORS allow any origin ([da18055](https://github.com/IA-Generative/abrege/commit/da180557508e2aebc859b20d491ee34299b10457))
* :poop: weak CORS_REGEXP=.* ([b708090](https://github.com/IA-Generative/abrege/commit/b7080907e2677dfc58d1f1f7a44b771a0117d190))
* / for routes ([5fb559e](https://github.com/IA-Generative/abrege/commit/5fb559eda5fe459248b0a361e2d7682eb6aa5751))
* abrege name ([b3ce04b](https://github.com/IA-Generative/abrege/commit/b3ce04bfd5021207aa85afbca6f19688e6eb7491))
* add api ([2adf7d0](https://github.com/IA-Generative/abrege/commit/2adf7d051b7ccabfb89e088ff90e0238afb08652))
* add audio schema ([a794c8b](https://github.com/IA-Generative/abrege/commit/a794c8b93766fd79afe17f88d0fa6bd7e1ac30e0))
* add client in right domain ([8877d41](https://github.com/IA-Generative/abrege/commit/8877d4132b88249fac2a0089280464e9ae4f9e1e))
* add health ([#103](https://github.com/IA-Generative/abrege/issues/103)) ([39ef458](https://github.com/IA-Generative/abrege/commit/39ef458f40b24edcf85eb059098346795e2a8b13))
* add hf_model ([4272a79](https://github.com/IA-Generative/abrege/commit/4272a79069202fb4ee642e7ee2c547e63140b654))
* add log debug ([43e5d9c](https://github.com/IA-Generative/abrege/commit/43e5d9c25d781ddae7d6a402925e141ab918d7d1))
* add logger ([9c52f92](https://github.com/IA-Generative/abrege/commit/9c52f92366a8edae50d7229705d8a454c5cecf75))
* add logger ([cb7f93e](https://github.com/IA-Generative/abrege/commit/cb7f93ed71b3be0422b143cc73f767ecc7104f8e))
* add MAX_CONTEXT_SIZE variables ([8f53612](https://github.com/IA-Generative/abrege/commit/8f536120d93c3afa37d3cf9cb9977abb582f21a8))
* add more log ([51af2b9](https://github.com/IA-Generative/abrege/commit/51af2b9e378dc9acf2bc02b70106993ecb23a99c))
* add more log ([11f9f29](https://github.com/IA-Generative/abrege/commit/11f9f2996527e4ab06ccbe102c1b9e4a8d387fbd))
* add more video ([e116051](https://github.com/IA-Generative/abrege/commit/e1160510539c30adea42d263eb77f09df1d2029d))
* add packages ([61b241e](https://github.com/IA-Generative/abrege/commit/61b241e2d85055541c3494fbd4d8b239bfa3c83d))
* add size in document ([36aca9b](https://github.com/IA-Generative/abrege/commit/36aca9b220aaca3d98314312844c449f5dfea3f1))
* add tags ([8737077](https://github.com/IA-Generative/abrege/commit/8737077ba6e060a9cc4ce9acdd4cc259614b5974))
* add x-wav data ([867fec9](https://github.com/IA-Generative/abrege/commit/867fec9e3d5acf1350b1abe63e0e1c27fd7300a8))
* an other permission denied ([05a0265](https://github.com/IA-Generative/abrege/commit/05a02653a16ccd08374b67a4f9d89f08fa857780))
* an other permission denied ([8411867](https://github.com/IA-Generative/abrege/commit/8411867cb8975a630e951dffec31ab04f205f4c1))
* annotation ([040152f](https://github.com/IA-Generative/abrege/commit/040152f02128015789bbcae70de54bb1345093c4))
* by using / ([#110](https://github.com/IA-Generative/abrege/issues/110)) ([2107d80](https://github.com/IA-Generative/abrege/commit/2107d805fa70a1434d78812c8a26888617ddbe5d))
* cache app ([124e634](https://github.com/IA-Generative/abrege/commit/124e6342900368f0e94079558e4465a7709e633e))
* cache dir for uv ([4a1c2aa](https://github.com/IA-Generative/abrege/commit/4a1c2aaa71ea7c8a9742425d901af3573788a132))
* ci deployement ([#102](https://github.com/IA-Generative/abrege/issues/102)) ([c5136ea](https://github.com/IA-Generative/abrege/commit/c5136eaa8095592ec2ef39d3201e3b74488dbe07))
* clean code ([86a912e](https://github.com/IA-Generative/abrege/commit/86a912ec999f3578d0c0d95ddea713dd5f81b803))
* clean dockerfile ([b92101e](https://github.com/IA-Generative/abrege/commit/b92101eda390c53943cd1696306b6d7732a95d60))
* correct project version to 0.0.3 in pyproject.toml ([d116ce0](https://github.com/IA-Generative/abrege/commit/d116ce01b54da4e4314054c94e631c9bb8e1f566))
* cors and url parse ([d81db88](https://github.com/IA-Generative/abrege/commit/d81db88a21ff84911ad10464a3b5def980682adb))
* cors api ([166792e](https://github.com/IA-Generative/abrege/commit/166792e52f810b580bfdd38997f3c558b3fb04be))
* delete notebook ([222c841](https://github.com/IA-Generative/abrege/commit/222c841603edc2d0e674ec528632b2c54bf091c1))
* delete template ([afc66ca](https://github.com/IA-Generative/abrege/commit/afc66cad875b306042b12964694385a7deab577c))
* deployement with nltk ([e3c4d64](https://github.com/IA-Generative/abrege/commit/e3c4d644dc07abf2c09ccfc8e3408405c9c3b134))
* document pssed ([27749ba](https://github.com/IA-Generative/abrege/commit/27749ba1c5b5c3c9bfce4e5cfdf4ed09896ac01e))
* don't delete video ([bcb0c0b](https://github.com/IA-Generative/abrege/commit/bcb0c0b76a5e0330cf860e2bf7edaf044ffd8094))
* don't forget to dl model ([9bfb6a3](https://github.com/IA-Generative/abrege/commit/9bfb6a3f3a95caaf0b3d05c05607ff4e5c493b85))
* don't save raw transformation ([3cd06aa](https://github.com/IA-Generative/abrege/commit/3cd06aa037f6e89b2f1e78f8432b80d28bae745d))
* don't use applicatif timeout ([32bb18b](https://github.com/IA-Generative/abrege/commit/32bb18b009cf7bd31321baa90cfcde6d1e119311))
* don't use marker api ([5dc4e4d](https://github.com/IA-Generative/abrege/commit/5dc4e4d5c7251b7761709d4c0e46e956995d878f))
* download nltk package ([9c7cadb](https://github.com/IA-Generative/abrege/commit/9c7cadb01d902c3c2982139cb5eb993bd637b9c8))
* download only need ([ad8ca7e](https://github.com/IA-Generative/abrege/commit/ad8ca7e58bf3561aaa29579d0dab12b98cec3008))
* dso ([0914699](https://github.com/IA-Generative/abrege/commit/09146993031aae2564a4a4a2828cbfdaf6eb16a0))
* encoding ([86a0cfb](https://github.com/IA-Generative/abrege/commit/86a0cfba580b5edb232c549b33995700508f0a25))
* env variables ([4a302a2](https://github.com/IA-Generative/abrege/commit/4a302a201a6d4371823f7c9ab87fff768a7e1f07))
* example ([#108](https://github.com/IA-Generative/abrege/issues/108)) ([b5bc7e5](https://github.com/IA-Generative/abrege/commit/b5bc7e579eb5b29f5fa2dba989a29d761d3cc491))
* fix -c ([19a011c](https://github.com/IA-Generative/abrege/commit/19a011cb178959ce2fc20e4855b8ba5b4db088bb))
* fix metrics evaluations ([1110247](https://github.com/IA-Generative/abrege/commit/11102475753da193780af2319697890fc20d9dda))
* fix run ([d98da58](https://github.com/IA-Generative/abrege/commit/d98da58357ed8d509c6ea6a600ad3775cfb6d517))
* for html content ([8e868b7](https://github.com/IA-Generative/abrege/commit/8e868b75eee51b08ddfeae8dce0cc6554a8a038a))
* for to dowload if not present ([e911d5e](https://github.com/IA-Generative/abrege/commit/e911d5ee00251df4d9171a81a12cddf66eb7750b))
* format JSONResponse and improve CORS middleware setup ([b7bd1fa](https://github.com/IA-Generative/abrege/commit/b7bd1fa3909db141732448779cb9cb22ef88d410))
* format JSONResponse and update default origins in set_cors function ([bbfd5c6](https://github.com/IA-Generative/abrege/commit/bbfd5c6e01566ebecb3e18d932daad671ec777b2))
* giive partial result ([5c0f767](https://github.com/IA-Generative/abrege/commit/5c0f76758fa8e8c3950daeb7e943fda280347eb1))
* health ([c2d7e66](https://github.com/IA-Generative/abrege/commit/c2d7e66751c7fe8a31131b8988ead56a244c30a7))
* if text is not provide ([5b4302e](https://github.com/IA-Generative/abrege/commit/5b4302e56ebde4af7f58ed39fefce33062baf825))
* ignore prod ([b02e964](https://github.com/IA-Generative/abrege/commit/b02e964bb4b4b9f45b7815694449342ce1df247b))
* import path ([00af728](https://github.com/IA-Generative/abrege/commit/00af7288fc6b01d8e5f5a58dce173ad3ac5031d9))
* jsonresponse ([1920481](https://github.com/IA-Generative/abrege/commit/1920481805a7820cd8f0411f5086bc849f9a3284))
* make more speed ([acdd446](https://github.com/IA-Generative/abrege/commit/acdd446d698d351d5fa97e443111f3619a8280f1))
* map_reduce langchain bug ([f25d5a5](https://github.com/IA-Generative/abrege/commit/f25d5a5453d7c022dc603dc6eb6dc2647898a0c4))
* map_reduce langchain bug ([3dfb7fd](https://github.com/IA-Generative/abrege/commit/3dfb7fd9de5cdecf39fd576729377cb6ef08156c))
* migration script ([d3044c6](https://github.com/IA-Generative/abrege/commit/d3044c637d7bb920f084750da67009ba7b1c9061))
* mode ([28252af](https://github.com/IA-Generative/abrege/commit/28252af3e7648808510975172105e77bb4e95e45))
* move utils ([ba7e4c7](https://github.com/IA-Generative/abrege/commit/ba7e4c7f08bc32d0ba31d17d3b8d5e8b2aa8fa07))
* naive aproche using token ([88b47e8](https://github.com/IA-Generative/abrege/commit/88b47e84f3797ba78c558d98e08c5d98a8670483))
* now gh action on arc-runner ([0d4a29f](https://github.com/IA-Generative/abrege/commit/0d4a29f281d53a9adc6f5a7dffe1e42bb8c3fd5a))
* OCR API ([bf032bf](https://github.com/IA-Generative/abrege/commit/bf032bfc3f38ed0922a828100b57831be415a48f))
* package fix ([#136](https://github.com/IA-Generative/abrege/issues/136)) ([6ed7101](https://github.com/IA-Generative/abrege/commit/6ed7101a4d0f7636b0308a70985e72a0c645d7f8))
* path ([0591a2b](https://github.com/IA-Generative/abrege/commit/0591a2ba945c167ade86f62548a50af6b412c3ff))
* permission denied in images ([665981f](https://github.com/IA-Generative/abrege/commit/665981fcd81365be8ddfe447ea4d5e6e6d98b271))
* port 8000 ([58bbb03](https://github.com/IA-Generative/abrege/commit/58bbb0363907da73b60e9ef86971f7b35d6fe325))
* port to 5000 to unify ([49cb507](https://github.com/IA-Generative/abrege/commit/49cb507769c95e2a34aeb0b67ffbe74a5b2cd93a))
* prompt map reduce ([366e0aa](https://github.com/IA-Generative/abrege/commit/366e0aaa2601d9fffd9089c8b34354b316c61297))
* prompt map reduce ([ce6a0f6](https://github.com/IA-Generative/abrege/commit/ce6a0f64683fb9aa345993739e1b26447307c7f8))
* reload ([56b8714](https://github.com/IA-Generative/abrege/commit/56b871428044776b80f6bec7c11d293d41291364))
* remove audio file at the end ([630a560](https://github.com/IA-Generative/abrege/commit/630a560491ea893bbfcef9b990d1a69f0812173b))
* remove data ([58fbe0f](https://github.com/IA-Generative/abrege/commit/58fbe0fb33c6f28f1fd604757e6002fc3de65464))
* retirer la température pour monsieur tout le monde ([7585ae0](https://github.com/IA-Generative/abrege/commit/7585ae02e765a6d6d0dcb57b7002cf8996956b4a))
* s3 big file in memory ([c2018fb](https://github.com/IA-Generative/abrege/commit/c2018fbc82567e1a8b4b3854d45e90eb5bebf4ee))
* schemas import ([3d0dd04](https://github.com/IA-Generative/abrege/commit/3d0dd04333bbdb929cf275d3526bf1c309037161))
* separate routes ([6797197](https://github.com/IA-Generative/abrege/commit/6797197555534a2a640f0df8bae32e4a86166997))
* set cors and add url router ([be37604](https://github.com/IA-Generative/abrege/commit/be37604a98b3fc2958640bad7c3a89ee52318406))
* splitext by token ([830f353](https://github.com/IA-Generative/abrege/commit/830f353cf4731b65da230f898fd4ca1302a0c6a6))
* sync modules ([9731a1b](https://github.com/IA-Generative/abrege/commit/9731a1b6dbfa2fb9266a476d62fe87f9fa1da902))
* task update ([ac6b9e4](https://github.com/IA-Generative/abrege/commit/ac6b9e480dd0875368ed8b80b3a538abcea19563))
* test to stream ([02f90c5](https://github.com/IA-Generative/abrege/commit/02f90c54be569ed7b2bbb4addb529c387a6c2f39))
* test token based ([8b874b5](https://github.com/IA-Generative/abrege/commit/8b874b5ed8dd915d834862a80ddbd6faf3c02165))
* try catch to get errors ([afee0bd](https://github.com/IA-Generative/abrege/commit/afee0bde6bffc7afdfba45671682786099c1e8f1))
* typo into var name ([958b9e3](https://github.com/IA-Generative/abrege/commit/958b9e3a842467b374c319ad57e0c065dff4af82))
* unitest ([125e627](https://github.com/IA-Generative/abrege/commit/125e627f5a513b06c0db700ceef95e1864221827))
* update project version to 2.0.1 ([d216a59](https://github.com/IA-Generative/abrege/commit/d216a596e7e74c71966e830a8bd3296aef8e3fc0))
* url png ([d265140](https://github.com/IA-Generative/abrege/commit/d265140145c5a76b9f9ae02269802de56e4bd7fa))
* use default model name ([5525ce5](https://github.com/IA-Generative/abrege/commit/5525ce56130a68e044bbc3e4962605e090103a47))
* use dockerfile ([6499eff](https://github.com/IA-Generative/abrege/commit/6499effad58077d6242e5bcc89812d5bc3b509bc))
* use env file ([a34cdef](https://github.com/IA-Generative/abrege/commit/a34cdef7aafe5f57fd80601a4191a8ec1b1511c7))
* use env var ([75fb200](https://github.com/IA-Generative/abrege/commit/75fb200acc33aef2c14f69154fb8f72edcc49ebb))
* use get instead of post ([01fd984](https://github.com/IA-Generative/abrege/commit/01fd984738c187ba7fd741dceed059d1db23dc48))
* use only boto3 ([2c581a1](https://github.com/IA-Generative/abrege/commit/2c581a1f0a6996c57a16b4eb6aac2f86b070f55e))
* use right folder name ([92b61d9](https://github.com/IA-Generative/abrege/commit/92b61d9f9f93d3a9b3a3315f015abaf3e0b612fd))
* use right url folder ([5601e2f](https://github.com/IA-Generative/abrege/commit/5601e2f3905a4bc5fb4918fed6f035707250513c))
* use right version ([23d2b97](https://github.com/IA-Generative/abrege/commit/23d2b97a6fe0ff1282e07982e70495b7d75a1d5e))
* utf-8 encoding ([32d0aab](https://github.com/IA-Generative/abrege/commit/32d0aab40e638beb1423e079b071fa0da7d1707f))
* uv cache ([c96e112](https://github.com/IA-Generative/abrege/commit/c96e112016ae07312cc775c43fbb532467462572))
* uv.lock ([b808a8d](https://github.com/IA-Generative/abrege/commit/b808a8d48aec303176c8a1409f415eba320080f9))
* video to audio ([c659bf3](https://github.com/IA-Generative/abrege/commit/c659bf39eb35b14e154bf660baf6113a28a0d4bf))

## [3.0.0](https://github.com/IA-Generative/abrege/compare/v2.0.0...v3.0.0) (2025-07-10)


### ⚠ BREAKING CHANGES

* feature add abrege most anything

### Features

* :alembic: ajout erreur surcharge LLM et surcharge OCR ([4df0971](https://github.com/IA-Generative/abrege/commit/4df0971fa9a85cee0dcd926d2c87b9ae74c8a7c2))
* :alembic: ajout erreur surcharge LLM et surcharge OCR ([88f23d3](https://github.com/IA-Generative/abrege/commit/88f23d3c56a6622cd6bc0192a47239c0ab693ac4))
* :ambulance: map_reduce comme méthode par défaut ([31c48d2](https://github.com/IA-Generative/abrege/commit/31c48d23673528ada7e5617e938872c8e1a00fac))
* :bug: install nltk package during build time ([fb544f9](https://github.com/IA-Generative/abrege/commit/fb544f9d6c4e6df4d25a0fa2b327d160976ff30f))
* :bug: install nltk package during build time ([ca82c7f](https://github.com/IA-Generative/abrege/commit/ca82c7ff58df3a8902df2306842a42f6de3fa490))
* :construction: tous les params dans le request body ([f480396](https://github.com/IA-Generative/abrege/commit/f4803964861f3d7fb06dfb7192ad731496b7321e))
* :goal_net: meilleure gestion des erreurs ([dbf092b](https://github.com/IA-Generative/abrege/commit/dbf092bf0bb0abb4378a14db8e21f92f7cbf5fc0))
* :goal_net: meilleure gestion des erreurs ([4892f8f](https://github.com/IA-Generative/abrege/commit/4892f8f7bc2aab952c00e3822192aa9cacefdeac))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([e2dc5be](https://github.com/IA-Generative/abrege/commit/e2dc5be2b7d54563ab1339709da63725c0a9286e))
* :poop: ajout du param custom_prompt pour retrocompatibilité ([3b69c4e](https://github.com/IA-Generative/abrege/commit/3b69c4e3ab98c6364f11e0b30af7f67eb829ede2))
* :poop: ajout limite ocr et nombre tokens ([70b7ddf](https://github.com/IA-Generative/abrege/commit/70b7ddf9b279ebd03dd48d30e4a241b18fb884c5))
* :poop: ajout limite ocr et nombre tokens ([2d640d2](https://github.com/IA-Generative/abrege/commit/2d640d2ae3519d1f4138a4acec6d23f7f25155bb))
* :sparkles: add CORS_REGEXP ([77293db](https://github.com/IA-Generative/abrege/commit/77293dba26c954a59634d509701804bc66d132b8))
* :sparkles: add OPENAI_API_MODEL ([f0ed789](https://github.com/IA-Generative/abrege/commit/f0ed78928c6194d1c3afd92560b014055eddf4d4))
* :sparkles: ajout map_prompt et reduce_prompt ([9d35720](https://github.com/IA-Generative/abrege/commit/9d35720bd7cf49eb4fdcdfcf660b22ade3a16cb1))
* :sparkles: ajout map_prompt et reduce_prompt ([686afb2](https://github.com/IA-Generative/abrege/commit/686afb246f47d1a816ef68d54eaecc6aa1d48e49))
* :sparkles: ajout map_prompt et reduce_prompt ([b98d8c8](https://github.com/IA-Generative/abrege/commit/b98d8c849396579b5d993b9a6c8adba716cb01d4))
* :sparkles: correction qq bugs ([441cba2](https://github.com/IA-Generative/abrege/commit/441cba299274fa16e3fa8ee9b10d682202c77a81))
* :sparkles: correction qq bugs ([9d91434](https://github.com/IA-Generative/abrege/commit/9d91434ffdc22d705770fafc9ac31c2721a6c352))
* :sparkles: map reduce dans abrege-api ([6b27d97](https://github.com/IA-Generative/abrege/commit/6b27d973908e4021ed124cdbaeb90dac0652cfa6))
* :sparkles: map reduce dans abrege-api ([ecc18cc](https://github.com/IA-Generative/abrege/commit/ecc18cc9b420d94f5c5b47e04a04861b7c4cb071))
* :sparkles: map reduce dans abrege-api ([bdc5778](https://github.com/IA-Generative/abrege/commit/bdc5778d5dd1929d90df0941bcfb9523e3768f7c))
* :sparkles: schema pydantic pour les réponses ([cbca0ce](https://github.com/IA-Generative/abrege/commit/cbca0cea574374944fda78842d299e9b6db12506))
* :sparkles: schema pydantic pour les réponses ([6236b8c](https://github.com/IA-Generative/abrege/commit/6236b8c712db334638b0e9537d66377fc2bfba49))
* add audio service to text ([44f5823](https://github.com/IA-Generative/abrege/commit/44f5823b81ebc61457d375d2a3d9ac5037376188))
* add basemodel service ([dd11a6c](https://github.com/IA-Generative/abrege/commit/dd11a6c5644d58c4ee63b623ef20e268fbbe7a73))
* add celery capacity ([6fee425](https://github.com/IA-Generative/abrege/commit/6fee425475e8c08e9436991f10026e20cc6034db))
* add celery component ([89b93ed](https://github.com/IA-Generative/abrege/commit/89b93eda7e9492601bb864d7eb3798109f348543))
* add content type ([5b11c41](https://github.com/IA-Generative/abrege/commit/5b11c419fb0900993f67570027ea51da47f51e72))
* add context length feat ([52b340f](https://github.com/IA-Generative/abrege/commit/52b340f3c0434d40c1985b127610a4d697bbc884))
* add dockerfile ([2b70e89](https://github.com/IA-Generative/abrege/commit/2b70e8900eb0c2749f8e60330e2b13733b870f33))
* add document parsing ([a1bfc94](https://github.com/IA-Generative/abrege/commit/a1bfc94f4952dddb5abd2fc89bad45b480319a72))
* add document to markdown ([9ce92f5](https://github.com/IA-Generative/abrege/commit/9ce92f59d5ef5a1aa7b03bb0e720963e9a3027c2))
* add evaluation metrics ([6db31e6](https://github.com/IA-Generative/abrege/commit/6db31e616b2f8f514373456c4706795103a3ba27))
* add file available for process ([00aa764](https://github.com/IA-Generative/abrege/commit/00aa764420761aa3d81685b4a0ea604032528396))
* add global percentage ([92092bb](https://github.com/IA-Generative/abrege/commit/92092bbaabc325410eb63f64372da0eece232204))
* add LibreOffice document support and related tests ([#126](https://github.com/IA-Generative/abrege/issues/126)) ([#127](https://github.com/IA-Generative/abrege/issues/127)) ([#128](https://github.com/IA-Generative/abrege/issues/128)) ([86dfa54](https://github.com/IA-Generative/abrege/commit/86dfa547f8108d3e7d17c699d0a9d7fbbe63d064))
* add migration images ([6a75b7d](https://github.com/IA-Generative/abrege/commit/6a75b7dbca70fc7c3d1e9e4b5e7405cb5451e637))
* add more details health ([98dd7d2](https://github.com/IA-Generative/abrege/commit/98dd7d29c9ce58a9b160dd5da783b4ef746e2851))
* add more log ([3cbd7dc](https://github.com/IA-Generative/abrege/commit/3cbd7dc977e65bf404c5559420fbeff91bca3424))
* add naive approach ([3ed3228](https://github.com/IA-Generative/abrege/commit/3ed32282f19f3feda1e37a901edbfa97cd1d59a3))
* add naive approach ([73d54e6](https://github.com/IA-Generative/abrege/commit/73d54e6f0a087b98aab86dc9c1fafe4b952aca98))
* add naive sumup approch ([759769c](https://github.com/IA-Generative/abrege/commit/759769c0fea48459ea76534363a7f0ab45b6fc55))
* add ocr purpose ([f5d1ea1](https://github.com/IA-Generative/abrege/commit/f5d1ea11ed5e26f500a5085061c163ce7f66a77d))
* add parameters ([8f67d39](https://github.com/IA-Generative/abrege/commit/8f67d39a5b7948a5a014d9a52c5e1adfa9da0eec))
* add parameters ([c6ed937](https://github.com/IA-Generative/abrege/commit/c6ed9370e23ecdd467a4bb80124880f0b4a4e5ef))
* add parameters ([7785e01](https://github.com/IA-Generative/abrege/commit/7785e01d88a4e1fc561714a085657c28a684371d))
* add plain text ([16be659](https://github.com/IA-Generative/abrege/commit/16be659a0b50558684d249b6168d8e95bcefff1b))
* add position ([#107](https://github.com/IA-Generative/abrege/issues/107)) ([d0b00b0](https://github.com/IA-Generative/abrege/commit/d0b00b0da11e3866a12ea1c846cf983319509db2))
* add prompting resolution ([48ee55e](https://github.com/IA-Generative/abrege/commit/48ee55e7ce902a210325c3a660a790671ebfd3de))
* add retrieve version ([930116e](https://github.com/IA-Generative/abrege/commit/930116e6c3ab147b69b403b71d37f2b594bc330b))
* add retry on llm ([a3f5d9c](https://github.com/IA-Generative/abrege/commit/a3f5d9cce6a36de428d2d835088945a83fb12db1))
* add s3 and minio connector ([1f126e0](https://github.com/IA-Generative/abrege/commit/1f126e0d989ce7854687bf40985b405d0a2aaef8))
* add small migration ([923093e](https://github.com/IA-Generative/abrege/commit/923093ead46362cd7059ff4d3cee75681fca5df5))
* add summay model ([c0b10c6](https://github.com/IA-Generative/abrege/commit/c0b10c69ad41fa11a1afd21eba875b1ff27d3f7d))
* add task ([7d92dd2](https://github.com/IA-Generative/abrege/commit/7d92dd243f501cb39dcbbdb452c200a0d6c76d8f))
* add task process to audio ([953e546](https://github.com/IA-Generative/abrege/commit/953e54637e0d47934821130848ccf266ea5fb106))
* add task router ([c26df52](https://github.com/IA-Generative/abrege/commit/c26df524bcefc76e3481988ab080fa8de1b57908))
* add task status to HTTP status mapping and corresponding tests ([adea495](https://github.com/IA-Generative/abrege/commit/adea49553c2e89337c99dd09aec9105d429722a9))
* add text splitter ([e335a83](https://github.com/IA-Generative/abrege/commit/e335a832ad436c11ea89af273592631f0e418f00))
* add tokenizer into process ([c38717e](https://github.com/IA-Generative/abrege/commit/c38717eb94d38cc11bafadb08afe1648c56515e2))
* add tokenizer to split text ([e95a9be](https://github.com/IA-Generative/abrege/commit/e95a9be71647c5fdf3a5568c927d920bd62156ee))
* add url and flat text ([5472d87](https://github.com/IA-Generative/abrege/commit/5472d873e7bb56596c42b51a4e976a2be4a7ec8c))
* add url detector ([6194644](https://github.com/IA-Generative/abrege/commit/6194644947683c7edbed28e9287f1fe45dac713e))
* add url modules ([a16e0fc](https://github.com/IA-Generative/abrege/commit/a16e0fc4588a7b8700c3b581c22b794c360da191))
* add video process ([017eeb1](https://github.com/IA-Generative/abrege/commit/017eeb1473598a9fefc95427b0f6c0b18d5ae5b6))
* add video transcription service ([2952609](https://github.com/IA-Generative/abrege/commit/2952609ffdfb6fa76a3b1dbf5c895b968e5f6cf0))
* ajout du custom prompt pour l'utilisateur ([29a8612](https://github.com/IA-Generative/abrege/commit/29a861209fa9eca6e72ce0683dae5655e60c4919))
* based on task ([e360421](https://github.com/IA-Generative/abrege/commit/e360421a48e79c202881015c9d859e7d45c24e3c))
* combine ocr client ([8fa89ca](https://github.com/IA-Generative/abrege/commit/8fa89ca21409633cec2b68b4a8a249d936b73f2e))
* feature add abrege most anything ([b705167](https://github.com/IA-Generative/abrege/commit/b7051671477d344392c182ae2d717daa1c357c43))
* fix ocr integration ([1fe8828](https://github.com/IA-Generative/abrege/commit/1fe8828b1134cf407c92aea54fdd153a0ffa8b8d))
* hide button ([265b016](https://github.com/IA-Generative/abrege/commit/265b0168d013554c02274b086f49315fe858ef19))
* hide expert ui ([6a61a21](https://github.com/IA-Generative/abrege/commit/6a61a21f14372d7d9ca7035e3d36a8505318d043))
* hide expert ui ([337eae6](https://github.com/IA-Generative/abrege/commit/337eae6704eb9760c7de7e641b47470e0f1ea8b3))
* new default model ([9bc5816](https://github.com/IA-Generative/abrege/commit/9bc58162d27024daa51de4da9044583b33e47d70))
* refactor process ([a8706a4](https://github.com/IA-Generative/abrege/commit/a8706a45fdfee39e1c924274f9a3c93a80a9b30c))
* reploy-hash ([efcd833](https://github.com/IA-Generative/abrege/commit/efcd83315c524f275646104c9f45574192482af0))
* send document to redis ([5f7042a](https://github.com/IA-Generative/abrege/commit/5f7042ac629c93021d4c965b54175cfffbe8927b))
* use APP_SECRETS in gh action ([edb3fc9](https://github.com/IA-Generative/abrege/commit/edb3fc97d34912986d654b47196188d6253d017a))
* use model service ([a281bb7](https://github.com/IA-Generative/abrege/commit/a281bb70f9eb31166601c78358825a7f8e2e3723))
* use services approach ([ad4ca7a](https://github.com/IA-Generative/abrege/commit/ad4ca7a7d0c8d38651132f40a1ed0b0b8f2b5928))


### Bug Fixes

* :adhesive_bandage: code erreur à 500 au lieu de 422 ([ffa7293](https://github.com/IA-Generative/abrege/commit/ffa7293cf666b26eecf538de05352160cb8f3f74))
* :adhesive_bandage: code erreur à 500 au lieu de 422 ([baed080](https://github.com/IA-Generative/abrege/commit/baed0809246ec9cd67f1f89076ac3e3ab7ff54ed))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([03b23ae](https://github.com/IA-Generative/abrege/commit/03b23ae966e273822b0fbb8676ab3391f02afec2))
* :adhesive_bandage: gestion erreur openai.RateLimitError ([9a0eb47](https://github.com/IA-Generative/abrege/commit/9a0eb474ee4aa1c16ffe411a28b7a1c6ccefbb33))
* :adhesive_bandage: stringData dans le kubectl patch secret ([94bfddd](https://github.com/IA-Generative/abrege/commit/94bfddde11fb7834442dfebeb0bfa6fc6df7d081))
* :alembic: nouveau model par défaut fastapi ([e431385](https://github.com/IA-Generative/abrege/commit/e4313858adb7d844784a933966a3297463d0345d))
* :ambulance: middleware dans le bon ordre ([e0937a8](https://github.com/IA-Generative/abrege/commit/e0937a8744a8d55bd2b379c17260cbd0369ea14e))
* :ambulance: summary comme modèle par défaut ([89e7727](https://github.com/IA-Generative/abrege/commit/89e7727356221b9bc4a3462bcf877c476a1f2351))
* :ambulance: try fix route /api/doc ([49e6730](https://github.com/IA-Generative/abrege/commit/49e6730b75d8c205cee3c18aaceb95713b96602c))
* :ambulance: try fix route /text ([44390bd](https://github.com/IA-Generative/abrege/commit/44390bd5b10c6a562a7406ead8ac6fd67305f858))
* :bug: add regex cors ([f461fd3](https://github.com/IA-Generative/abrege/commit/f461fd390c2392d11a64c8f59f8679ce002da9b6))
* :bug: try fix /root/nltk_data issue ([eb70e7f](https://github.com/IA-Generative/abrege/commit/eb70e7f45b2bb33215be91a673de7e034e95130f))
* :bug: try fix /root/nltk_data issue ([d23a29c](https://github.com/IA-Generative/abrege/commit/d23a29cd7a3b13d63eea015072548425f78a2f02))
* :construction: restauration ancienne api + meilleurs param par défaut ([ad0b2dd](https://github.com/IA-Generative/abrege/commit/ad0b2ddaa0c54642a60b286e02ee58349ec8d135))
* :construction: restauration ancienne api + meilleurs param par défaut ([bcdd46a](https://github.com/IA-Generative/abrege/commit/bcdd46ad68ac7ea305b973c1d762e61cb870a4d0))
* :construction: restauration ancienne api + meilleurs param par défaut ([5753b9d](https://github.com/IA-Generative/abrege/commit/5753b9dd085c37e6a3c1586a443cc58982dc981c))
* :construction: try fix ci/cd ([636eeaf](https://github.com/IA-Generative/abrege/commit/636eeafdc4d0249791da2e5f80f98968c0b24386))
* :construction: try fix ci/cd ([a1dcd06](https://github.com/IA-Generative/abrege/commit/a1dcd06c4ce2bbd50ea9171dfbb785727a10e392))
* :construction: try fix ci/cd ([730bd07](https://github.com/IA-Generative/abrege/commit/730bd07acb67b60c9fa8aee621f0c18eb04ba63f))
* :construction: try fix ci/Cd ([d6295a1](https://github.com/IA-Generative/abrege/commit/d6295a1272edac527e739f29846cf3191c17a5b3))
* :construction: try fix docker compose ([8a21976](https://github.com/IA-Generative/abrege/commit/8a21976f9148fb0943a32632a17acbda7978b2ac))
* :poop: augmentation des limites ([ed5e0da](https://github.com/IA-Generative/abrege/commit/ed5e0da1e602ea78d1eea6dfe9616e3e816ba5cf))
* :poop: augmentation des limites ([0da344f](https://github.com/IA-Generative/abrege/commit/0da344f8ea5549a315b0a7557aaf4bac90c5fd62))
* :poop: CORS allow any origin ([da18055](https://github.com/IA-Generative/abrege/commit/da180557508e2aebc859b20d491ee34299b10457))
* :poop: weak CORS_REGEXP=.* ([b708090](https://github.com/IA-Generative/abrege/commit/b7080907e2677dfc58d1f1f7a44b771a0117d190))
* / for routes ([5fb559e](https://github.com/IA-Generative/abrege/commit/5fb559eda5fe459248b0a361e2d7682eb6aa5751))
* abrege name ([b3ce04b](https://github.com/IA-Generative/abrege/commit/b3ce04bfd5021207aa85afbca6f19688e6eb7491))
* add api ([2adf7d0](https://github.com/IA-Generative/abrege/commit/2adf7d051b7ccabfb89e088ff90e0238afb08652))
* add audio schema ([a794c8b](https://github.com/IA-Generative/abrege/commit/a794c8b93766fd79afe17f88d0fa6bd7e1ac30e0))
* add client in right domain ([8877d41](https://github.com/IA-Generative/abrege/commit/8877d4132b88249fac2a0089280464e9ae4f9e1e))
* add health ([#103](https://github.com/IA-Generative/abrege/issues/103)) ([39ef458](https://github.com/IA-Generative/abrege/commit/39ef458f40b24edcf85eb059098346795e2a8b13))
* add hf_model ([4272a79](https://github.com/IA-Generative/abrege/commit/4272a79069202fb4ee642e7ee2c547e63140b654))
* add log debug ([43e5d9c](https://github.com/IA-Generative/abrege/commit/43e5d9c25d781ddae7d6a402925e141ab918d7d1))
* add logger ([9c52f92](https://github.com/IA-Generative/abrege/commit/9c52f92366a8edae50d7229705d8a454c5cecf75))
* add logger ([cb7f93e](https://github.com/IA-Generative/abrege/commit/cb7f93ed71b3be0422b143cc73f767ecc7104f8e))
* add MAX_CONTEXT_SIZE variables ([8f53612](https://github.com/IA-Generative/abrege/commit/8f536120d93c3afa37d3cf9cb9977abb582f21a8))
* add more log ([51af2b9](https://github.com/IA-Generative/abrege/commit/51af2b9e378dc9acf2bc02b70106993ecb23a99c))
* add more log ([11f9f29](https://github.com/IA-Generative/abrege/commit/11f9f2996527e4ab06ccbe102c1b9e4a8d387fbd))
* add more video ([e116051](https://github.com/IA-Generative/abrege/commit/e1160510539c30adea42d263eb77f09df1d2029d))
* add packages ([61b241e](https://github.com/IA-Generative/abrege/commit/61b241e2d85055541c3494fbd4d8b239bfa3c83d))
* add size in document ([36aca9b](https://github.com/IA-Generative/abrege/commit/36aca9b220aaca3d98314312844c449f5dfea3f1))
* add tags ([8737077](https://github.com/IA-Generative/abrege/commit/8737077ba6e060a9cc4ce9acdd4cc259614b5974))
* add x-wav data ([867fec9](https://github.com/IA-Generative/abrege/commit/867fec9e3d5acf1350b1abe63e0e1c27fd7300a8))
* an other permission denied ([05a0265](https://github.com/IA-Generative/abrege/commit/05a02653a16ccd08374b67a4f9d89f08fa857780))
* an other permission denied ([8411867](https://github.com/IA-Generative/abrege/commit/8411867cb8975a630e951dffec31ab04f205f4c1))
* annotation ([040152f](https://github.com/IA-Generative/abrege/commit/040152f02128015789bbcae70de54bb1345093c4))
* by using / ([#110](https://github.com/IA-Generative/abrege/issues/110)) ([2107d80](https://github.com/IA-Generative/abrege/commit/2107d805fa70a1434d78812c8a26888617ddbe5d))
* cache app ([124e634](https://github.com/IA-Generative/abrege/commit/124e6342900368f0e94079558e4465a7709e633e))
* cache dir for uv ([4a1c2aa](https://github.com/IA-Generative/abrege/commit/4a1c2aaa71ea7c8a9742425d901af3573788a132))
* ci deployement ([#102](https://github.com/IA-Generative/abrege/issues/102)) ([c5136ea](https://github.com/IA-Generative/abrege/commit/c5136eaa8095592ec2ef39d3201e3b74488dbe07))
* clean code ([86a912e](https://github.com/IA-Generative/abrege/commit/86a912ec999f3578d0c0d95ddea713dd5f81b803))
* clean dockerfile ([b92101e](https://github.com/IA-Generative/abrege/commit/b92101eda390c53943cd1696306b6d7732a95d60))
* correct project version to 0.0.3 in pyproject.toml ([d116ce0](https://github.com/IA-Generative/abrege/commit/d116ce01b54da4e4314054c94e631c9bb8e1f566))
* cors and url parse ([d81db88](https://github.com/IA-Generative/abrege/commit/d81db88a21ff84911ad10464a3b5def980682adb))
* cors api ([166792e](https://github.com/IA-Generative/abrege/commit/166792e52f810b580bfdd38997f3c558b3fb04be))
* delete notebook ([222c841](https://github.com/IA-Generative/abrege/commit/222c841603edc2d0e674ec528632b2c54bf091c1))
* delete template ([afc66ca](https://github.com/IA-Generative/abrege/commit/afc66cad875b306042b12964694385a7deab577c))
* deployement with nltk ([e3c4d64](https://github.com/IA-Generative/abrege/commit/e3c4d644dc07abf2c09ccfc8e3408405c9c3b134))
* document pssed ([27749ba](https://github.com/IA-Generative/abrege/commit/27749ba1c5b5c3c9bfce4e5cfdf4ed09896ac01e))
* don't delete video ([bcb0c0b](https://github.com/IA-Generative/abrege/commit/bcb0c0b76a5e0330cf860e2bf7edaf044ffd8094))
* don't forget to dl model ([9bfb6a3](https://github.com/IA-Generative/abrege/commit/9bfb6a3f3a95caaf0b3d05c05607ff4e5c493b85))
* don't save raw transformation ([3cd06aa](https://github.com/IA-Generative/abrege/commit/3cd06aa037f6e89b2f1e78f8432b80d28bae745d))
* don't use applicatif timeout ([32bb18b](https://github.com/IA-Generative/abrege/commit/32bb18b009cf7bd31321baa90cfcde6d1e119311))
* don't use marker api ([5dc4e4d](https://github.com/IA-Generative/abrege/commit/5dc4e4d5c7251b7761709d4c0e46e956995d878f))
* download nltk package ([9c7cadb](https://github.com/IA-Generative/abrege/commit/9c7cadb01d902c3c2982139cb5eb993bd637b9c8))
* download only need ([ad8ca7e](https://github.com/IA-Generative/abrege/commit/ad8ca7e58bf3561aaa29579d0dab12b98cec3008))
* dso ([0914699](https://github.com/IA-Generative/abrege/commit/09146993031aae2564a4a4a2828cbfdaf6eb16a0))
* encoding ([86a0cfb](https://github.com/IA-Generative/abrege/commit/86a0cfba580b5edb232c549b33995700508f0a25))
* env variable to docker ([219e70c](https://github.com/IA-Generative/abrege/commit/219e70c3b86cca511577855b8a40bc9e859672e6))
* env variables ([4a302a2](https://github.com/IA-Generative/abrege/commit/4a302a201a6d4371823f7c9ab87fff768a7e1f07))
* example ([#108](https://github.com/IA-Generative/abrege/issues/108)) ([b5bc7e5](https://github.com/IA-Generative/abrege/commit/b5bc7e579eb5b29f5fa2dba989a29d761d3cc491))
* fix -c ([19a011c](https://github.com/IA-Generative/abrege/commit/19a011cb178959ce2fc20e4855b8ba5b4db088bb))
* fix metrics evaluations ([1110247](https://github.com/IA-Generative/abrege/commit/11102475753da193780af2319697890fc20d9dda))
* fix run ([d98da58](https://github.com/IA-Generative/abrege/commit/d98da58357ed8d509c6ea6a600ad3775cfb6d517))
* for html content ([8e868b7](https://github.com/IA-Generative/abrege/commit/8e868b75eee51b08ddfeae8dce0cc6554a8a038a))
* for to dowload if not present ([e911d5e](https://github.com/IA-Generative/abrege/commit/e911d5ee00251df4d9171a81a12cddf66eb7750b))
* format JSONResponse and improve CORS middleware setup ([b7bd1fa](https://github.com/IA-Generative/abrege/commit/b7bd1fa3909db141732448779cb9cb22ef88d410))
* format JSONResponse and update default origins in set_cors function ([bbfd5c6](https://github.com/IA-Generative/abrege/commit/bbfd5c6e01566ebecb3e18d932daad671ec777b2))
* giive partial result ([5c0f767](https://github.com/IA-Generative/abrege/commit/5c0f76758fa8e8c3950daeb7e943fda280347eb1))
* health ([c2d7e66](https://github.com/IA-Generative/abrege/commit/c2d7e66751c7fe8a31131b8988ead56a244c30a7))
* if text is not provide ([5b4302e](https://github.com/IA-Generative/abrege/commit/5b4302e56ebde4af7f58ed39fefce33062baf825))
* ignore prod ([b02e964](https://github.com/IA-Generative/abrege/commit/b02e964bb4b4b9f45b7815694449342ce1df247b))
* import path ([00af728](https://github.com/IA-Generative/abrege/commit/00af7288fc6b01d8e5f5a58dce173ad3ac5031d9))
* jsonresponse ([1920481](https://github.com/IA-Generative/abrege/commit/1920481805a7820cd8f0411f5086bc849f9a3284))
* make more speed ([acdd446](https://github.com/IA-Generative/abrege/commit/acdd446d698d351d5fa97e443111f3619a8280f1))
* map_reduce langchain bug ([f25d5a5](https://github.com/IA-Generative/abrege/commit/f25d5a5453d7c022dc603dc6eb6dc2647898a0c4))
* map_reduce langchain bug ([3dfb7fd](https://github.com/IA-Generative/abrege/commit/3dfb7fd9de5cdecf39fd576729377cb6ef08156c))
* migration script ([d3044c6](https://github.com/IA-Generative/abrege/commit/d3044c637d7bb920f084750da67009ba7b1c9061))
* mode ([28252af](https://github.com/IA-Generative/abrege/commit/28252af3e7648808510975172105e77bb4e95e45))
* move utils ([ba7e4c7](https://github.com/IA-Generative/abrege/commit/ba7e4c7f08bc32d0ba31d17d3b8d5e8b2aa8fa07))
* naive aproche using token ([88b47e8](https://github.com/IA-Generative/abrege/commit/88b47e84f3797ba78c558d98e08c5d98a8670483))
* now gh action on arc-runner ([0d4a29f](https://github.com/IA-Generative/abrege/commit/0d4a29f281d53a9adc6f5a7dffe1e42bb8c3fd5a))
* OCR API ([bf032bf](https://github.com/IA-Generative/abrege/commit/bf032bfc3f38ed0922a828100b57831be415a48f))
* package fix ([#136](https://github.com/IA-Generative/abrege/issues/136)) ([6ed7101](https://github.com/IA-Generative/abrege/commit/6ed7101a4d0f7636b0308a70985e72a0c645d7f8))
* path ([0591a2b](https://github.com/IA-Generative/abrege/commit/0591a2ba945c167ade86f62548a50af6b412c3ff))
* permission denied in images ([665981f](https://github.com/IA-Generative/abrege/commit/665981fcd81365be8ddfe447ea4d5e6e6d98b271))
* port 8000 ([58bbb03](https://github.com/IA-Generative/abrege/commit/58bbb0363907da73b60e9ef86971f7b35d6fe325))
* port to 5000 to unify ([49cb507](https://github.com/IA-Generative/abrege/commit/49cb507769c95e2a34aeb0b67ffbe74a5b2cd93a))
* prompt map reduce ([366e0aa](https://github.com/IA-Generative/abrege/commit/366e0aaa2601d9fffd9089c8b34354b316c61297))
* prompt map reduce ([ce6a0f6](https://github.com/IA-Generative/abrege/commit/ce6a0f64683fb9aa345993739e1b26447307c7f8))
* reload ([56b8714](https://github.com/IA-Generative/abrege/commit/56b871428044776b80f6bec7c11d293d41291364))
* remove audio file at the end ([630a560](https://github.com/IA-Generative/abrege/commit/630a560491ea893bbfcef9b990d1a69f0812173b))
* remove data ([58fbe0f](https://github.com/IA-Generative/abrege/commit/58fbe0fb33c6f28f1fd604757e6002fc3de65464))
* retirer la température pour monsieur tout le monde ([7585ae0](https://github.com/IA-Generative/abrege/commit/7585ae02e765a6d6d0dcb57b7002cf8996956b4a))
* s3 big file in memory ([c2018fb](https://github.com/IA-Generative/abrege/commit/c2018fbc82567e1a8b4b3854d45e90eb5bebf4ee))
* schemas import ([3d0dd04](https://github.com/IA-Generative/abrege/commit/3d0dd04333bbdb929cf275d3526bf1c309037161))
* separate routes ([6797197](https://github.com/IA-Generative/abrege/commit/6797197555534a2a640f0df8bae32e4a86166997))
* set cors and add url router ([be37604](https://github.com/IA-Generative/abrege/commit/be37604a98b3fc2958640bad7c3a89ee52318406))
* splitext by token ([830f353](https://github.com/IA-Generative/abrege/commit/830f353cf4731b65da230f898fd4ca1302a0c6a6))
* sync modules ([9731a1b](https://github.com/IA-Generative/abrege/commit/9731a1b6dbfa2fb9266a476d62fe87f9fa1da902))
* task update ([ac6b9e4](https://github.com/IA-Generative/abrege/commit/ac6b9e480dd0875368ed8b80b3a538abcea19563))
* test to stream ([02f90c5](https://github.com/IA-Generative/abrege/commit/02f90c54be569ed7b2bbb4addb529c387a6c2f39))
* test token based ([8b874b5](https://github.com/IA-Generative/abrege/commit/8b874b5ed8dd915d834862a80ddbd6faf3c02165))
* try catch to get errors ([afee0bd](https://github.com/IA-Generative/abrege/commit/afee0bde6bffc7afdfba45671682786099c1e8f1))
* typo into var name ([958b9e3](https://github.com/IA-Generative/abrege/commit/958b9e3a842467b374c319ad57e0c065dff4af82))
* unitest ([125e627](https://github.com/IA-Generative/abrege/commit/125e627f5a513b06c0db700ceef95e1864221827))
* update project version to 2.0.1 ([d216a59](https://github.com/IA-Generative/abrege/commit/d216a596e7e74c71966e830a8bd3296aef8e3fc0))
* url png ([d265140](https://github.com/IA-Generative/abrege/commit/d265140145c5a76b9f9ae02269802de56e4bd7fa))
* use correct env var ([3f252ef](https://github.com/IA-Generative/abrege/commit/3f252ef8df9f719c3a1053dd598c672098d8a26e))
* use default model name ([5525ce5](https://github.com/IA-Generative/abrege/commit/5525ce56130a68e044bbc3e4962605e090103a47))
* use dockerfile ([6499eff](https://github.com/IA-Generative/abrege/commit/6499effad58077d6242e5bcc89812d5bc3b509bc))
* use env file ([a34cdef](https://github.com/IA-Generative/abrege/commit/a34cdef7aafe5f57fd80601a4191a8ec1b1511c7))
* use env var ([75fb200](https://github.com/IA-Generative/abrege/commit/75fb200acc33aef2c14f69154fb8f72edcc49ebb))
* use get instead of post ([01fd984](https://github.com/IA-Generative/abrege/commit/01fd984738c187ba7fd741dceed059d1db23dc48))
* use only boto3 ([2c581a1](https://github.com/IA-Generative/abrege/commit/2c581a1f0a6996c57a16b4eb6aac2f86b070f55e))
* use right folder name ([92b61d9](https://github.com/IA-Generative/abrege/commit/92b61d9f9f93d3a9b3a3315f015abaf3e0b612fd))
* use right url folder ([5601e2f](https://github.com/IA-Generative/abrege/commit/5601e2f3905a4bc5fb4918fed6f035707250513c))
* use right version ([23d2b97](https://github.com/IA-Generative/abrege/commit/23d2b97a6fe0ff1282e07982e70495b7d75a1d5e))
* utf-8 encoding ([32d0aab](https://github.com/IA-Generative/abrege/commit/32d0aab40e638beb1423e079b071fa0da7d1707f))
* uv cache ([c96e112](https://github.com/IA-Generative/abrege/commit/c96e112016ae07312cc775c43fbb532467462572))
* uv.lock ([b808a8d](https://github.com/IA-Generative/abrege/commit/b808a8d48aec303176c8a1409f415eba320080f9))
* video to audio ([c659bf3](https://github.com/IA-Generative/abrege/commit/c659bf39eb35b14e154bf660baf6113a28a0d4bf))

## 0.0.2 (2025-03-21)

## 0.0.1 (2025-03-12)

### Feat

- :ambulance: map_reduce comme méthode par défaut
- use APP_SECRETS in gh action
- add retry on llm
- ajout du custom prompt pour l'utilisateur
- hide expert ui
- new default model
- reploy-hash
- hide button

### Fix

- :ambulance: summary comme modèle par défaut
- :alembic: nouveau model par défaut fastapi
- now gh action on arc-runner
- OCR API
- map_reduce langchain bug
- retirer la température pour monsieur tout le monde
- prompt map reduce

# 🚀 Python Backend & DevOps Architecture Showcase (90 сервисов)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)
![pytest](https://img.shields.io/badge/pytest-passing-0A9EDC?style=for-the-badge&logo=pytest)

Портфолио из 90 папок. 30 сервисов в `medium/` можно поднять и прогнать тестами: у каждого свой README, `docker-compose.yml` и CI. 60 папок в `services/` — наброски сценариев, не готовые сервисы.

---

## Сервисы

| Сервис | Стек | Описание & README |
|---|---|---|
| `invoice_numbers` | FastAPI, SQLite | [README](medium/18_invoice_numbers/README.md) • Аннулированный номер не переиспользуется |
| `oauth2_server` | FastAPI, SQLite | [README](medium/03_oauth2_server/README.md) • Свой код авторизации и ротация refresh |
| `decorator_cache_telemetry` | набросок | [README](services/group6_solid/50_decorator_cache_telemetry/README.md) • Декоратор кэширования и метрик |
| `checkout_saga` | FastAPI, SQLite | [README](medium/01_checkout_saga/README.md) • Отказ оплаты возвращает остаток |
| `fastapi_sse_stream` | набросок | [README](services/group4_frameworks/30_fastapi_sse_stream/README.md) • Стриминг данных Server-Sent Events |
| `promo_codes` | FastAPI, SQLite | [README](medium/10_promo_codes/README.md) • Скидка, срок, лимит и пригласивший |
| `discord_webhook_bot` | набросок | [README](services/group5_bots/40_discord_webhook_bot/README.md) • Discord бот для системных алертов |
| `repository_unit_of_work` | набросок | [README](services/group6_solid/44_repository_unit_of_work/README.md) • Изоляция слоя БД через Repository & UoW |
| `redis_jwt_blacklist` | набросок | [README](services/group1_auth/04_redis_jwt_blacklist/README.md) • Черный список токенов через Redis TTL |
| `inventory_reservation` | FastAPI, SQLite | [README](medium/04_inventory_reservation/README.md) • Два заказа не продают один остаток |
| `telegram_celery_monitor` | набросок | [README](services/group5_bots/37_telegram_celery_monitor/README.md) • Бот-мониторинг сбоев фоновых задач |
| `async_web_scraper` | набросок | [README](services/group5_bots/38_async_web_scraper/README.md) • Асинхронный скрапер с очередью asyncio.Queue |
| `document_workflow` | FastAPI, SQLite | [README](medium/17_document_workflow/README.md) • Автор не согласует свой документ |
| `rabbitmq_priority_queue` | набросок | [README](services/group3_queues/25_rabbitmq_priority_queue/README.md) • Приоритетные очереди задач по SLA |
| `fastapi_pydantic_crud` | набросок | [README](services/group4_frameworks/27_fastapi_pydantic_crud/README.md) • Асинхронный REST API CRUD с валидацией |
| `cqrs_event_sourcing` | набросок | [README](services/group6_solid/46_cqrs_event_sourcing/README.md) • CQRS Разделение команд и запросов |
| `alembic_migrations` | набросок | [README](services/group2_databases/12_alembic_migrations/README.md) • Авто-миграции и скрипты откатов |
| `django_drf_rbac` | набросок | [README](services/group1_auth/03_django_drf_rbac/README.md) • Кастомные claims & Роли RBAC |
| `redis_rate_limiter` | набросок | [README](services/group1_auth/06_redis_rate_limiter/README.md) • Rate Limiting Middleware |
| `pdf_excel_exporter` | набросок | [README](services/group4_frameworks/34_pdf_excel_exporter/README.md) • Генерация PDF отчетов и XLSX таблиц |
| `argon2_password_hasher` | набросок | [README](services/group1_auth/05_argon2_password_hasher/README.md) • Хэширование паролей & Benchmark |
| `celery_beat_scheduler` | набросок | [README](services/group3_queues/22_celery_beat_scheduler/README.md) • Планировщик периодических задач (Cron) |
| `mysql_pool_failover` | набросок | [README](services/group2_databases/11_mysql_pool_failover/README.md) • Пулинг соединений & Failover Monitor |
| `docker_compose_fullstack` | набросок | [README](services/group7_devops/54_docker_compose_fullstack/README.md) • Multi-Container стек микросервисов |
| `webhook_dispatcher` | FastAPI, SQLite, HMAC | [README](medium/21_webhook_dispatcher/README.md) • Повтор доставки и подпись тела |
| `github_actions_cicd` | набросок | [README](services/group7_devops/56_github_actions_cicd/README.md) • CI/CD Пайплайн (Lint, Test, Build) |
| `dlq_replay` | FastAPI, SQLite | [README](medium/22_dlq_replay/README.md) • Три ошибки, потом ручной возврат |
| `factory_cloud_storage` | набросок | [README](services/group6_solid/49_factory_cloud_storage/README.md) • Фабрика драйверов хранилищ (S3/GCS/Azure) |
| `django_drf_viewsets` | набросок | [README](services/group4_frameworks/28_django_drf_viewsets/README.md) • ViewSets с фильтрацией и пагинацией |
| `structlog_json_logging` | набросок | [README](services/group7_devops/59_structlog_json_logging/README.md) • Структурированное JSON-логирование |
| `docker_multistage_python` | набросок | [README](services/group7_devops/53_docker_multistage_python/README.md) • Минимальный образ Docker (45MB) |
| `rabbitmq_pubsub_eventbus` | набросок | [README](services/group3_queues/19_rabbitmq_pubsub_eventbus/README.md) • Шина событий Pub/Sub + Dead-Letter Queue |
| `django_signals_audit` | набросок | [README](services/group4_frameworks/31_django_signals_audit/README.md) • Событийный аудит действий пользователей |
| `redis_pubsub_notifications` | набросок | [README](services/group3_queues/21_redis_pubsub_notifications/README.md) • Рассылка уведомлений в реальном времени |
| `schema_registry` | FastAPI, SQLite | [README](medium/25_schema_registry/README.md) • Убрать обязательное поле нельзя |
| `fastapi_celery_email` | набросок | [README](services/group3_queues/24_fastapi_celery_email/README.md) • Асинхронная отправка Email писем |
| `redis_redlock_manager` | набросок | [README](services/group3_queues/23_redis_redlock_manager/README.md) • Распределенный менеджер блокировок |
| `tracing` | FastAPI | [README](medium/29_tracing/README.md) • Ошибка склада помечает и заказ |
| `hmac_api_signer` | набросок | [README](services/group1_auth/07_hmac_api_signer/README.md) • Подпись запросов & Защита от Replay Attack |
| `clean_onion_architecture` | набросок | [README](services/group6_solid/51_clean_onion_architecture/README.md) • Слоистая Clean / Onion Architecture |
| `autocomplete` | FastAPI | [README](medium/26_autocomplete/README.md) • Префикс, синоним и одна опечатка |
| `usage_quotas` | FastAPI, SQLite | [README](medium/09_usage_quotas/README.md) • Месячный лимит, не частота запросов |
| `nginx_security_headers` | набросок | [README](services/group1_auth/08_nginx_security_headers/README.md) • OWASP заголовки & CORS Guard |
| `transaction_isolation_sandbox` | набросок | [README](services/group2_databases/14_transaction_isolation_sandbox/README.md) • Симулятор уровней изоляции транзакций |
| `csv_import` | FastAPI, SQLite | [README](medium/19_csv_import/README.md) • Плохие строки не роняют верные |
| `multi_tenant` | FastAPI, SQLite | [README](medium/20_multi_tenant/README.md) • Чужой арендатор не видит заметку |
| `audit_log` | FastAPI, SQLite | [README](medium/14_audit_log/README.md) • Журнал только дописывается |
| `notification_hub` | FastAPI, SQLite | [README](medium/05_notification_hub/README.md) • Выключенный канал не вызывается |
| `nginx_reverse_proxy` | набросок | [README](services/group7_devops/55_nginx_reverse_proxy/README.md) • Reverse Proxy с SSL и балансировкой |
| `api_keys` | FastAPI, SQLite | [README](medium/12_api_keys/README.md) • Scope, ротация, отзыв |
| `report_jobs` | FastAPI, SQLite | [README](medium/24_report_jobs/README.md) • Скачивание только после готовности |
| `chat_rooms` | FastAPI, SQLite | [README](medium/27_chat_rooms/README.md) • Чужой не пишет, пока не вошёл |
| `sqlalchemy_soft_delete` | набросок | [README](services/group2_databases/16_sqlalchemy_soft_delete/README.md) • Soft Delete & Аудит через Event Listeners |
| `redis_geospatial_api` | набросок | [README](services/group3_queues/26_redis_geospatial_api/README.md) • Геолокационный поиск объектов поблизости |
| `postgres_copy_seeder` | набросок | [README](services/group2_databases/17_postgres_copy_seeder/README.md) • Высокоскоростной сеедер (COPY IN) |
| `strategy_payment_gateway` | набросок | [README](services/group6_solid/47_strategy_payment_gateway/README.md) • Адаптер платежек (Stripe, PayPal, Crypto) |
| `rss_news_parser_bot` | набросок | [README](services/group5_bots/41_rss_news_parser_bot/README.md) • RSS-агрегатор с дедупликацией в Redis |
| `two_factor` | FastAPI, SQLite, TOTP | [README](medium/11_two_factor/README.md) • TOTP и одноразовый запасной код |
| `gdpr_erasure` | FastAPI, SQLite | [README](medium/13_gdpr_erasure/README.md) • Выгрузка, затем стирание личности |
| `sqlalchemy_async_engine` | набросок | [README](services/group2_databases/09_sqlalchemy_async_engine/README.md) • Async Engine & Session Manager |
| `subscriptions` | FastAPI, SQLite | [README](medium/08_subscriptions/README.md) • Второй отказ отменяет подписку |
| `aiogram3_telegram_bot` | набросок | [README](services/group5_bots/36_aiogram3_telegram_bot/README.md) • Telegram бот с FSM и Inline клавиатурами |
| `crypto_tracker_bot` | набросок | [README](services/group5_bots/42_crypto_tracker_bot/README.md) • Мониторинг криптовалют и пороги цен |
| `gitflow_release_automator` | набросок | [README](services/group7_devops/57_gitflow_release_automator/README.md) • Автоматизация релизов GitFlow |
| `celery_task_pipeline` | набросок | [README](services/group3_queues/18_celery_task_pipeline/README.md) • Конвейер задач (Chains, Groups, Chords) |
| `dependency_injection_container` | набросок | [README](services/group6_solid/45_dependency_injection_container/README.md) • Dependency Inversion Principle (DIP) |
| `pytest_suite_runner` | набросок | [README](services/group7_devops/52_pytest_suite_runner/README.md) • Набор unit и integration тестов |
| `graceful_shutdown_handler` | набросок | [README](services/group7_devops/60_graceful_shutdown_handler/README.md) • Корректное завершение процессов в Docker |
| `transactional_outbox` | FastAPI, SQLite | [README](medium/02_transactional_outbox/README.md) • Повтор события не плодит счёт |
| `s3_file_uploader` | набросок | [README](services/group4_frameworks/35_s3_file_uploader/README.md) • Загрузка файлов в S3/MinIO с компрессией |
| `redis_cache_aside` | набросок | [README](services/group3_queues/20_redis_cache_aside/README.md) • Паттерны Cache-Aside & Write-Through |
| `webhook_telegram_relay` | набросок | [README](services/group5_bots/43_webhook_telegram_relay/README.md) • Реле Webhook -> Telegram с лимитами |
| `booking` | FastAPI, SQLite | [README](medium/16_booking/README.md) • Пересекающиеся слоты нельзя занять |
| `idempotent_payments` | FastAPI, SQLite | [README](medium/07_idempotent_payments/README.md) • Тот же ключ не списывает дважды |
| `cdc_projector` | FastAPI, SQLite | [README](medium/28_cdc_projector/README.md) • Витрина отстаёт, пока её не спроецировали |
| `feature_flags` | FastAPI, SQLite | [README](medium/30_feature_flags/README.md) • Список допуска сильнее нулевого процента |
| `django_multidb_router` | набросок | [README](services/group2_databases/15_django_multidb_router/README.md) • Multi-DB Router & Read Replicas |
| `upload_pipeline` | FastAPI, SQLite | [README](medium/23_upload_pipeline/README.md) • Не-PNG не становится готовым |
| `circuit_breaker` | FastAPI | [README](medium/06_circuit_breaker/README.md) • После трёх ошибок апстрим не дёргается |
| `sessions` | FastAPI, SQLite | [README](medium/15_sessions/README.md) • Выход с одного устройства не гасит другое |
| `webhook_receiver_retry` | набросок | [README](services/group4_frameworks/33_webhook_receiver_retry/README.md) • Приемник Webhook с асинхронными повторами |
| `fastapi_jwt_auth` | набросок | [README](services/group1_auth/01_fastapi_jwt_auth/README.md) • Access/Refresh ротация токенов |
| `postgres_fulltext_search` | набросок | [README](services/group2_databases/13_postgres_fulltext_search/README.md) • Полнотекстовый поиск (tsvector, GIN) |
| `flask_oauth2_social` | набросок | [README](services/group1_auth/02_flask_oauth2_social/README.md) • Social Auth Google & GitHub |
| `prometheus_fastapi_exporter` | набросок | [README](services/group7_devops/58_prometheus_fastapi_exporter/README.md) • Экспортер метрик приложения |
| `strawberry_graphql_api` | набросок | [README](services/group4_frameworks/32_strawberry_graphql_api/README.md) • GraphQL API микросервис |
| `django_query_optimizer` | набросок | [README](services/group2_databases/10_django_query_optimizer/README.md) • Устранение N+1 (select_related) |
| `observer_domain_events` | набросок | [README](services/group6_solid/48_observer_domain_events/README.md) • Паттерн Наблюдатель для событий домена |
| `flask_modular_blueprints` | набросок | [README](services/group4_frameworks/29_flask_modular_blueprints/README.md) • Модульная архитектура микросервиса |
| `playwright_headless_bot` | набросок | [README](services/group5_bots/39_playwright_headless_bot/README.md) • Автоматизация браузера и скриншоты E2E |

© 2026 Python Backend Architecture Showcase. All rights reserved.

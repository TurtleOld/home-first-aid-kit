# Changelog

## [1.1.2](https://github.com/TurtleOld/home-first-aid-kit/compare/v1.1.1...v1.1.2) (2026-06-13)


### Bug Fixes

* **docker:** задать HOME для app в entrypoint ([#31](https://github.com/TurtleOld/home-first-aid-kit/issues/31)) ([1e781fc](https://github.com/TurtleOld/home-first-aid-kit/commit/1e781fcf27af44fbea9b60ddd051ed7d6e9f27de))

## [1.1.1](https://github.com/TurtleOld/home-first-aid-kit/compare/v1.1.0...v1.1.1) (2026-06-13)


### Bug Fixes

* **docker:** чинить владельца смонтированных томов перед запуском от app ([#28](https://github.com/TurtleOld/home-first-aid-kit/issues/28)) ([b26cd8a](https://github.com/TurtleOld/home-first-aid-kit/commit/b26cd8a93f3cfa150c3f424e2cdda54e937814d2))

## [1.1.0](https://github.com/TurtleOld/home-first-aid-kit/compare/v1.0.0...v1.1.0) (2026-06-12)


### Features

* **backend:** добавить проверку БД и кеша в health-check ([8d10454](https://github.com/TurtleOld/home-first-aid-kit/commit/8d104549dc6924bb0e2fa741dd10472a92185d32))
* **backend:** добавить проверку БД и кеша в health-check ([97d6684](https://github.com/TurtleOld/home-first-aid-kit/commit/97d6684fe928d2bc9449f1cebc2503ffa7f045f4))


### Bug Fixes

* **backend:** отключить Browsable API renderer вне DEBUG ([31bda4c](https://github.com/TurtleOld/home-first-aid-kit/commit/31bda4c40b9d80b5b71feab81069e14785de7920))
* **backend:** убрать маршрут /admin/, проверить защиту от mass-assignment ([323d871](https://github.com/TurtleOld/home-first-aid-kit/commit/323d871359f275b0623fb407c71be99b3ea181fe))
* **ci:** синхронизировать uv.lock с версией в релизном PR ([#23](https://github.com/TurtleOld/home-first-aid-kit/issues/23)) ([78b2e70](https://github.com/TurtleOld/home-first-aid-kit/commit/78b2e70b6835e9e6f8ca7792a6c84b58c07fef93))
* **docker:** запускать backend-контейнер от непривилегированного пользователя ([886e755](https://github.com/TurtleOld/home-first-aid-kit/commit/886e755dddccf1d4979298093bea027442920457))


### Performance Improvements

* **notifications:** убрать N+1 запросы при рассылке напоминаний ([875c183](https://github.com/TurtleOld/home-first-aid-kit/commit/875c18391d60d4b3363cad327edf50d795498dfc))

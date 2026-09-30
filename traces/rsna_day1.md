# Трейс кейса rsna_day1

Режим replay, модель claude-opus-5-5, скиллы: подключаются. Полные промпты и результаты инструментов лежат рядом в .jsonl

Запрос: Мы только что вступили в соревнование rsna-knee-abnormality-detection, своих посылок еще нет. Нужен план первой недели: что это за соревнование и какие в нем ограничения, что с метрикой, как устроить валидацию, что пробовать первым и на что не тратить посылки. План запиши в notes/PLAN.md.

<details><summary>метапромпт диспетчера с каталогами субагентов и скиллов</summary>

````
Ты - диспетчер команды, которая участвует в ML-соревновании на Kaggle. Сам ты задачу не решаешь: не читаешь материалы, не пишешь код, не считаешь метрики и не судишь, какой прогон лучше. Инструментов у тебя нет. Твоя работа - понять, что нужно пользователю, разложить это на шаги, отдать каждый шаг подходящему исполнителю с подходящей методикой, прочитать результат и решить, что делать дальше.

## Исполнители
- scout: разведчик. Собирает факты о соревновании и о состоянии команды: метрика, данные, устройство теста и паблика, ограничения, сроки, что уже сделано. Источники - рабочая папка и Kaggle API на чтение (страницы, файлы и профиль таблиц, публичные ноутбуки с исходниками, лидерборд). Только у него есть доступ к Kaggle. Решений не принимает. Нужен в начале работы и когда не хватает фактов
- validation_engineer: инженер валидации. Разбирается, каким локальным цифрам можно верить: устройство метрики, дорожки валидации (честные и in-sample), число независимых единиц, шум валидации и шум публичного лидерборда. Считает сам: сравнения прогонов по единицам, бутстрап, свой код. Сабмиты не выбирает
- experiment_engineer: инженер экспериментов. Пишет и запускает код в рабочей папке: анализ результатов, новые варианты, проверки гипотез. Регистрирует новые прогоны в реестре с результатами по единицам валидации. Нужен, когда нужно что-то посчитать или получить новый прогон, а не оценить готовые
- auditor: аудитор. Проверяет прогоны: утечки, in-sample компоненты, подгонку под валидацию и под паблик, клоны, расхождение валидации и сабмита. Записывает в реестр вердикт по каждому прогону (принять, доработать, исключить). Без вердикта 'принять' прогон не может стать финальным сабмитом
- strategist: стратег. Принимает решения по цифрам валидации: помогло ли изменение, какие линии продолжать, что отправлять, какие прогоны финалить. Записывает финальные сабмиты с пререгистрацией и разбор прошлых решений команды. Выводы инженера валидации и аудитора видит, только если они переданы через context_step_list

## Скиллы
Скилл - это методика, которую harness на один шаг подмешивает исполнителю в системный промпт. Ты видишь только названия и описания, сам текст увидит исполнитель.
- change_acceptance: Правило принятия изменений и закрытия линий работы - парное сравнение по единицам, совпадение знака по группам, механизм, три исхода, пререгистрация до посылки, когда линию нельзя закрывать. Подключать, когда решается, помогло ли изменение, продолжать ли линию и что отправлять в оставшиеся слоты
- code_competition_submit: Посылки в code competition - гейтинг ноутбука, контроль времени и fallback'и, проверки формата, очередь и зависания, последний безопасный момент, журнал посылок. Подключать, когда планируются или проверяются посылки в соревновании, где сабмит - это ноутбук с лимитом времени и без интернета
- competition_recon: Разведка соревнования в первый день и перед важными решениями - что вытащить из страниц, правил, данных, публичных ноутбуков, форума и лидерборда, как записать и чему из найденного не верить. Подключать разведчику, когда собираются факты о соревновании или о том, что известно про решения других
- compute_ops: Облачные ресурсы и долгие задачи - реестр ресурсов и самоудаление, мастер-скрипт с чекпойнтами, ожидание до терминального статуса, хранение состояния, учетные данные на чужих машинах. Подключать, когда планируются или запускаются долгие вычисления на арендованных GPU или на платформе
- final_picks: Выбор финальных сабмитов - кого включать в кандидаты, первый слот по надежной валидации, второй другому семейству, клоны не занимают два слота, что делать с отвергнутыми по паблику, пререгистрация. Подключать стратегу, когда выбираются финальные сабмиты
- honest_validation: Как строить локальную валидацию и как оценивать уже имеющиеся дорожки - сплит как у теста, честность для всех обученных компонент включая публичные веса, совпадение с кодом сабмита, число независимых единиц, lockbox. Подключать, когда проектируется валидация или нужно решить, каким локальным цифрам можно верить
- lb_noise: Шум публичного лидерборда - как оценить его бутстрапом по единицам валидации, как читать разницу на паблике в единицах SD, поправка на множественные сравнения, что шум из своих данных не моделирует. Подключать, когда нужно понять, значит ли что-нибудь разница публичных скоров, и до первого решения по лидерборду
- leak_audit: Аудит прогонов и кандидатов перед сравнением и финальным выбором - in-sample компоненты и утечки, подгонка под валидацию и под паблик, семейства и клоны, расхождение кода валидации и сабмита, какой вердикт выносить. Подключать аудитору, когда проверяются прогоны, посылки или список кандидатов
- lever_priority: Куда вкладывать время и посылки - порядок рычагов от модели и данных до ручек пост-процессинга, сколько попыток давать линии, как делить вычисления, как составлять очередь экспериментов на неделю. Подключать, когда составляется план работ или очередь экспериментов и посылок
- metric_port: Порт метрики соревнования и его проверка - что считать источником истины, как сверять с официальным кодом на пертурбациях, какие причуды искать чтением кода, симуляцией и пробной посылкой. Подключать, когда разбирается устройство метрики, пишется или проверяется локальный расчет скора

## Как работать
1. Сначала план. На первом ходу составь план под конкретный запрос и дальше веди его в plan_list: план с прошлого хода тебе показывают, обнови его по итогам шага. Не гоняй полный цикл, если просят часть, и не зови исполнителя, которому на этом запросе нечего делать.
2. Один шаг - один исполнитель - одна проверяемая подзадача. Исполнитель не видит ни запроса пользователя, ни истории шагов. Он получает subtask_text, список файлов рабочей папки, ответы шагов из context_step_list целиком и свои инструменты, которыми сам читает файлы и считает. В subtask_text напиши, что сделать, какие условия из запроса пользователя важны для этого шага и что должно быть в ответе. Это постановка, а не подсказка: не пиши в ней выводы, к которым исполнитель должен прийти сам по своим данным и методике, и не повторяй то, что он и так увидит в контексте. Не сужай сам круг прогонов, которые исполнитель должен рассмотреть, если этого не требует запрос: список "претендентов", который ты составил по публичному скору, - это уже решение, а решения принимаешь не ты. Охват определяет исполнитель по своей методике. Обычно хватает 3-7 предложений. В context_step_list клади только те шаги, без которых исполнитель не справится.
3. Скилл подключай, когда его описание подходит к тому, что делается на шаге. Обычно это один скилл, редко два. Если подходящего нет - пустой список: лишняя методика только размывает промпт.
4. После каждого шага читай итог и пересматривай план. Строки "[harness]" в итоге - это факты, которые записал сам harness (вердикты, финальный выбор, новые прогоны), им можно верить больше, чем словам исполнителя. Если исполнитель ответил не по существу или уперся в ограничение - переформулируй подзадачу, добавь контекст или отдай другому, не повторяй ту же формулировку.
5. Порядок, который нельзя нарушать:
   - решения не принимаются, пока не собраны факты: если про соревнование или про состояние команды чего-то не хватает - сначала разведчик;
   - цифрам валидации можно верить только после инженера валидации: какая дорожка честная и какой у нее шум;
   - прогон не идет в финальный выбор без вердикта аудитора;
   - помогло ли изменение, что отправлять и что финалить, решает стратег - не ты и не публичный лидерборд.
6. Заканчивай, когда запрос выполнен или когда кончается бюджет шагов. В final_answer - короткий ответ пользователю: что сделано, что выбрано и почему, что осталось под вопросом. Ответы исполнителей целиком не пересказывай.

## Формат ответа
Только один JSON-объект, без текста вокруг:
{
  "thought": "1-3 фразы: что уже известно и почему следующий шаг именно такой",
  "plan_list": ["оставшиеся шаги, коротко, начиная с текущего"],
  "action": "delegate или finish",
  "agent_nm": "название исполнителя (для delegate)",
  "skill_nm_list": ["названия скиллов или пустой список (для delegate)"],
  "subtask_text": "подзадача исполнителю (для delegate)",
  "context_step_list": [номера прошлых шагов, ответы которых нужно передать исполнителю (для delegate)],
  "final_answer": "ответ пользователю (для finish)"
}
````

</details>

## Диспетчер, ход 1

````
{
  "thought": "Команда только вступила, рабочая папка пуста, фактов о соревновании нет. Сначала разведчик собирает факты, потом можно проектировать валидацию и план.",
  "plan_list": [
    "scout: разведка соревнования (метрика, данные, устройство теста и паблика, формат посылок, лимиты, сроки, публичные ноутбуки, лидерборд)",
    "validation_engineer: устройство метрики и ее локальный порт, что проверить",
    "validation_engineer: схема честной валидации под устройство теста, число независимых единиц, ожидаемый шум валидации и паблика",
    "strategist: очередь экспериментов и посылок на первую неделю, на что не тратить посылки; записать notes/PLAN.md",
    "finish: короткий итог пользователю"
  ],
  "action": "delegate",
  "agent_nm": "scout",
  "skill_nm_list": [
    "competition_recon"
  ],
  "subtask_text": "Команда только что вступила в соревнование rsna-knee-abnormality-detection на Kaggle, своих посылок и материалов в рабочей папке нет. Собери через Kaggle API факты о соревновании, которые нужны для плана первой недели: постановка задачи и целевые переменные; метрика (точное определение, есть ли официальный код, усреднение, веса, особенности); данные (файлы, размеры, модальности, структура таблиц, единицы типа пациент/исследование, баланс классов); устройство теста и деление на паблик/приват; формат сабмита (файл или ноутбук, лимиты времени, интернета, железа); лимит посылок в день и число финальных сабмитов; сроки (в том числе дедлайны на вступление и слияние команд); правила по внешним данным и предобученным весам; что видно в публичных ноутбуках (подходы, их скоры, с исходниками) и на лидерборде (разброс скоров, плотность топа). В ответе раздели, что подтверждено первоисточником (страницы, правила, файлы), а что взято из чужих ноутбуков или обсуждений и требует проверки, и отдельно перечисли, что узнать не удалось. Сохрани сводку в notes/RECON.md.",
  "context_step_list": []
}
````

## Шаг 1: scout

Скиллы, выбранные диспетчером: competition_recon. Контекст: шаги []

Системный промпт: 8318 символов, из них скиллы - 4238

<details><summary>системный промпт целиком</summary>

````
Ты - разведчик в команде, которая участвует в ML-соревновании на Kaggle. Твоя работа - собрать факты, на которых остальные будут строить решения: что за задача, как устроены метрика, данные, тест и публичный лидерборд, какие есть ограничения (code competition, лимит времени ноутбука, интернет, число посылок в день, число финальных сабмитов, сроки), что уже сделала команда, что видно по публичным ноутбукам и по лидерборду.

Факты берутся из рабочей папки (страницы соревнования, журнал посылок, заметки команды) и через Kaggle API, если он доступен. К каждому факту - откуда он. Отделяй то, что написано в источнике, от своих выводов. Если источники расходятся или чего-то в них нет - так и пиши, не заполняй пробелы догадками.

Ты не предлагаешь модели, не оцениваешь прогоны и не выбираешь сабмиты.

## Инструменты
- list_files: список файлов рабочей папки с размерами в символах. Аргументов нет
- read_file: прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата будет подсказка, с какого offset продолжать. Аргументы: path - путь к файлу от корня рабочей папки; offset - с какого символа читать (необязательный, по умолчанию 0); limit - сколько символов вернуть, за один вызов отдается не больше 10000 (необязательный, по умолчанию 10000)
- write_file: записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается. Атрибуты тега: path - путь к файлу от корня рабочей папки. Внутри блока - содержимое файла
- kaggle_pages: страницы соревнования через Kaggle API: список страниц или текст одной страницы, по 6000 символов за вызов. Аргументы: page - название страницы; без него вернется список страниц (необязательный); offset - с какого символа читать страницу (необязательный, по умолчанию 0)
- kaggle_files: сводка по файлам данных соревнования через Kaggle API. Аргументов нет
- kaggle_csv_profile: профиль табличного файла соревнования через Kaggle API: число строк, типы, пропуски, доли значений. Сам файл не сохраняется. Аргументы: file - имя csv-файла из списка файлов соревнования
- kaggle_kernels: публичные ноутбуки соревнования через Kaggle API. Аргументы: sort_by - сортировка: hotness | commentCount | dateCreated | dateRun | scoreAscending | scoreDescending | viewCount | voteCount (необязательный, по умолчанию voteCount); page_size - сколько ноутбуков вернуть, не больше 100 (необязательный, по умолчанию 20)
- kaggle_kernel_source: исходный код публичного ноутбука через Kaggle API, без выходов ячеек, по 6000 символов за вызов. Аргументы: ref - ссылка на ноутбук вида автор/название из kaggle_kernels; offset - с какого символа читать (необязательный, по умолчанию 0)
- kaggle_leaderboard: верх публичного лидерборда через Kaggle API: места и скоры. Аргументов нет

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{"path": "journal.md"}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше 14 вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.

=== МЕТОДИКА: competition_recon ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Разведка соревнования

От разведки нужен список фактов, от которых зависят решения, и источник у каждого. Пересказ страниц никому не нужен. Все, что команда не проверила сама, так и помечается: непроверенное.

## Что собрать

1. Паспорт. Что предсказываем и в каком формате сабмит. Метрика: формула, по каким единицам она пулится или усредняется, что округляется, какие есть штрафы и капы. Сроки: дедлайн входа, слияния команд, финальный. Сколько посылок в день и сколько финальных.
2. Ограничения исполнения. Если это code competition: лимит времени ноутбука на CPU и GPU, есть ли интернет, разрешены ли внешние данные и веса и на каких условиях, как называется файл сабмита. И лимиты платформы, про которые страницы молчат: число одновременных GPU-сессий, недельная квота GPU.
3. Устройство теста. На этом пункте потом стоит вся валидация, времени на него не жалеть. Чем тест отличается от трейна: новые группы (пациент, площадка, эмбрион, устройство), другой период, другой источник. Какой размер у скрытого теста. Какая доля теста в публичном лидерборде и сколько это независимых единиц. До скольких знаков округляется табло. Видимая часть теста - это настоящий тест или копия трейна. Доли паблика и числа знаков на страницах может не быть, тогда искать в API соревнования и на странице лидерборда.
4. Данные. Состав и размер файлов, какая часть размечена, есть ли доп. источники (тексты, метаданные), как устроены идентификаторы групп.
5. Официальный код. Репозиторий организаторов с метрикой и конвертерами и история его коммитов: патчи метрики посреди соревнования меняют смысл старых скоров.
6. Публичные решения. Топ ноутбуков по скору и по голосам: на чем обучены модели, какие сплиты, сколько идет ноутбук, какие стадии в пайплайне. Публичные веса и датасеты: что внутри и на каких данных обучено.
7. Форум. Ответы хостов про правила и метрику, найденные баги, сообщения топ-участников о том, что у них работает и что нет. Читать с комментариями, самое полезное обычно в ответах.
8. Лидерборд. Плотность верха (сколько команд делят один скор) и число посылок у команд наверху. Мало посылок при высоком скоре - признак своего пайплайна; подбор по паблику выглядит иначе, посылок там много.

## Чему не верить на слово

Скор в названии ноутбука или датасета ("0.95 LB"). Это результат отбора по публичному лидерборду тысячами людей, и на привате такие компоненты теряют больше, чем свои. К тому же скор мог быть получен до патча метрики или на эксплойте, который с тех пор закрыли.

"Валидация" внутри публичного ноутбука. Проверь, на чем обучены веса. Если на всем трейне, то любая локальная проверка на этих весах - in-sample, какой бы сплит ни стоял в коде.

Публичный ноутбук "как есть". Прежде чем на нем строить, прочитай код: бывает, что заявленный компонент молча не работает. Веса грузятся с strict=False в другую архитектуру, исключение проглатывается, функция возвращает None - ноутбук идет дальше без компонента, а в описании он есть.

Конфиг, который ноутбук выбрал на коммите. Если внутри есть перебор с валидацией на видимых данных, на скрытом реране он может выбрать другой конфиг. Тогда в логе коммита записан один конфиг, а скор дал другой.

Текст страницы про метрику и формат. Источник истины - код метрики на конкретном коммите. Чего в коде нет (обертка грейдера), проверяется пробной посылкой.

## Как записать

Таблица: утверждение - источник - проверено ли нами - на что влияет. Например:

    паблик - 25% теста, около 40 единиц | страница лидерборда | да | порог шума паблика
    публичные веса обучены на всем трейне | описание датасета | нет, читать код обучения | честность локальной валидации на этих весах
    дробные значения в сабмите допустимы | код конвертера | нет, страница требует целые | пробная посылка

Если два источника расходятся, в таблицу идут оба. Выбирать тот, что удобнее, нельзя.

И два списка отдельно от таблицы.

Первый: чего выяснить не удалось и как это можно выяснить (спросить на форуме, пробная посылка, прочитать код).

Второй: советы сильных участников про стратегию - что у них не сработало, куда они советуют вкладываться. К нему нужно возвращаться перед каждым решением закрыть линию работы. Составить такой список в первый день легко, труднее потом его открывать.
=== КОНЕЦ МЕТОДИКИ: competition_recon ===
````

</details>

Подзадача: Команда только что вступила в соревнование rsna-knee-abnormality-detection на Kaggle, своих посылок и материалов в рабочей папке нет. Собери через Kaggle API факты о соревновании, которые нужны для плана первой недели: постановка задачи и целевые переменные; метрика (точное определение, есть ли официальный код, усреднение, веса, особенности); данные (файлы, размеры, модальности, структура таблиц, единицы типа пациент/исследование, баланс классов); устройство теста и деление на паблик/приват; формат сабмита (файл или ноутбук, лимиты времени, интернета, железа); лимит посылок в день и число финальных сабмитов; сроки (в том числе дедлайны на вступление и слияние команд); правила по внешним данным и предобученным весам; что видно в публичных ноутбуках (подходы, их скоры, с исходниками) и на лидерборде (разброс скоров, плотность топа). В ответе раздели, что подтверждено первоисточником (страницы, правила, файлы), а что взято из чужих ноутбуков или обсуждений и требует проверки, и отдельно перечисли, что узнать не удалось. Сохрани сводку в notes/RECON.md.

### scout, сообщение 1

````
Начну со списка страниц соревнования, чтобы понять, какие первоисточники доступны через API.

<tool name="kaggle_pages">{}</tool>
````

Результат kaggle_pages:

````
Страницы соревнования: rules, Description, Evaluation, Timeline, data-description, Prizes, Code Requirements, abstract, Efficiency Prize Evaluation, Acknowledgements
````

### scout, сообщение 2

````
Читаю страницу Evaluation: определение метрики и формат сабмита - основа для всего остального.

<tool name="kaggle_pages">{"page": "Evaluation"}</tool>
````

Результат kaggle_pages:

````
Submissions are evaluated by the average [area under the ROC curve](http://en.wikipedia.org/wiki/Receiver_operating_characteristic) between the predicted confidence scores and the observed targets across the twelve targets:

$$
\text{Final Score} = \frac{1}{12}\sum_{i=0}^{11} AUC_i
$$

The final score is, in other words, the macro-averaged AUC ROC.

## Submission File
For each row in the test set, you must predict a confidence score for each of the twelve target labels. The file should contain a header and have the following format:

```
StudyInstanceUID,ACL,MCL,Medial Meniscus,Lateral Meniscus,Medial OA,Lateral OA,PF OA,Effusion,Synovitis,Baker's,Contusion,Fracture
<uid_1>,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5
<uid_2>,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5
...
```
````

### scout, сообщение 3

````
Метрика - macro AUC по 12 таргетам, сабмит на уровне StudyInstanceUID. Теперь страница Code Requirements: лимиты ноутбука, интернет, внешние данные.

<tool name="kaggle_pages">{"page": "Code Requirements"}</tool>
````

Результат kaggle_pages:

````
<img src="https://storage.googleapis.com/kaggle-media/competitions/general/Kerneler-white-desc2_transparent.png" style="float: right; width: 70px; padding: 10px">

Submissions to this competition must be made through Notebooks. In order for the "Submit" button to be active after a commit, the following conditions must be met: 
- CPU Notebook <= 9 hours run-time 
- GPU Notebook <= 9 hours run-time 
- Internet access disabled 
- Freely & publicly available external data is allowed, including pre-trained models 
- Submission file must be named `submission.csv` 

Please see the [Code Competition FAQ](https://www.kaggle.com/docs/competitions#notebooks-only-FAQ) for more information on how to submit. And review the [code debugging doc](https://www.kaggle.com/code-competition-debugging) if you are encountering submission errors.
````

### scout, сообщение 4

````
Code competition: 9 часов CPU/GPU, без интернета, внешние данные и веса разрешены. Дальше Timeline: дедлайны входа, слияния и финальный.

<tool name="kaggle_pages">{"page": "Timeline"}</tool>
````

Результат kaggle_pages:

````
* **July 30, 2026** - Start Date. 
* **October 15, 2026** - Entry Deadline. You must accept the competition rules before this date in order to compete. 
* **October 15, 2026** - Team Merger Deadline. This is the last day participants may join or merge teams. 
* **October 22, 2026** - Final Submission Deadline.
* **November 5, 2026** - Winners' Requirement Deadline. This is the deadline for winners to submit to the host/Kaggle their training code, video and method description.

All deadlines are at 11:59 PM UTC on the corresponding day unless otherwise noted. The competition organizers reserve the right to update the contest timeline if they deem it necessary.
````

### scout, сообщение 5

````
Сроки есть: вход и слияние до 15 октября, финал 22 октября 2026. Теперь data-description: состав файлов, единицы, устройство теста.

<tool name="kaggle_pages">{"page": "data-description"}</tool>
````

Результат kaggle_pages:

````
## Dataset Description

This dataset contains knee MRI studies annotated for twelve common findings: ligament and meniscus injuries, three compartments of osteoarthritis, joint effusion, synovitis, Baker's cyst, bone contusion, and fracture. Each study comprises a collection of individual MRI sequences from a single scanning session formatted as DICOM series. Your task is to predict the per-study probability of each of the twelve findings.

Studies come from a diverse international mix of imaging sites and span a wide range of scanners, protocols, and populations. Only a small subset of training studies carry per-condition labels. We also provide the original text of the radiology report from which you may wish to derive the labels for the remaining studies.

## Files

**train.csv** One row per training study.

*   `StudyInstanceUID` - unique identifier for the study; matches the folder name under `train_series/`.
*   `Report` - the free-text radiology report. May be in any of several languages, depending on the reporting institution.

Twelve binary labels:
*   `ACL` - anterior cruciate ligament injury (0/1).
*   `MCL` - medial collateral ligament injury (0/1).
*   `Medial Meniscus` - medial meniscus tear (0/1).
*   `Lateral Meniscus` - lateral meniscus tear (0/1).
*   `Medial OA` - osteoarthritis of the medial tibiofemoral compartment (0/1).
*   `Lateral OA` - osteoarthritis of the lateral tibiofemoral compartment (0/1).
*   `PF OA` - patellofemoral osteoarthritis (0/1).
*  
... (обрезано, всего 3979 символов)
````

### scout, сообщение 6

````
Данные описаны: лишь малая часть трейна размечена, в тесте около 1300 исследований, отчётов там нет. Теперь правила: лимит посылок в день, число финальных сабмитов, условия по внешним данным.

<tool name="kaggle_pages">{"page": "rules"}</tool>
````

Результат kaggle_pages:

````
##ENTRY IN THIS COMPETITION CONSTITUTES YOUR ACCEPTANCE OF THESE OFFICIAL COMPETITION RULES.

**[See Section 3.18 for defined terms](rules#18.-terms)**

*The Competition named below is a skills-based competition to promote and further the field of data science. You must register via the Competition Website to enter. To enter the Competition, you must agree to these Official Competition Rules, which incorporate by reference the provisions and content of the Competition Website and any Specific Competition Rules herein (collectively, the "Rules"). Please read these Rules carefully before entry to ensure you understand and agree. You further agree that Submission in the Competition constitutes agreement to these Rules. You may not submit to the Competition and are not eligible to receive the prizes associated with this Competition unless you agree to these Rules. These Rules form a binding legal agreement between you and the Competition Sponsor with respect to the Competition. Your competition Submissions  must conform to the requirements stated on the Competition Website. Your Submissions will be scored based on the evaluation metric described on the Competition Website. Subject to compliance with the Competition Rules, Prizes, if any, will be awarded to Participants with the best scores, based on the merits of the data science models submitted. See below for the complete Competition Rules. For Hackathon Competitions, your Submissions will be judged by the Competition Sponsor b
... (обрезано, всего 6061 символов)
````

### scout, сообщение 7

````
Правила дали лимиты: 5 посылок в день, 2 финальных, команда до 5 человек. Теперь сводка по файлам данных: размеры и состав.

<tool name="kaggle_files">{}</tool>
````

Результат kaggle_files:

````
Файлов в списке: 3000 (список обрезан, файлов больше). Сводка по верхнему уровню:
sample_submission.csv: файлов 1, 0.0 МБ
test.csv: файлов 1, 0.0 МБ
test_series.csv: файлов 1, 0.0 МБ
test_series: файлов 557, 600.0 МБ
train.csv: файлов 1, 5.7 МБ
train_series.csv: файлов 1, 3.5 МБ
train_series: файлов 2438, 1519.1 МБ
````

### scout, сообщение 8

````
Список файлов обрезан, поэтому размеры папок неполные. Профиль train.csv даст число исследований, долю размеченных и баланс классов.

<tool name="kaggle_csv_profile">{"file": "train.csv"}</tool>
````

Результат kaggle_csv_profile:

````
train.csv: строк 4407, колонок 14
колонка                     тип       уникальных  пропуски  значения
StudyInstanceUID            str       4407        0.000     длина строк: медиана 64
Report                      str       4276        0.000     длина строк: медиана 977
ACL                         float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
MCL                         float64   2           0.987     nan: 0.987, 0.0: 0.011, 1.0: 0.002
Medial Meniscus             float64   2           0.987     nan: 0.987, 0.0: 0.007, 1.0: 0.006
Lateral Meniscus            float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
Medial OA                   float64   2           0.987     nan: 0.987, 0.0: 0.010, 1.0: 0.003
Lateral OA                  float64   2           0.987     nan: 0.987, 0.0: 0.011, 1.0: 0.002
PF OA                       float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
Effusion                    float64   2           0.987     nan: 0.987, 1.0: 0.008, 0.0: 0.005
Synovitis                   float64   2           0.987     nan: 0.987, 0.0: 0.007, 1.0: 0.006
Baker's                     float64   2           0.987     nan: 0.987, 0.0: 0.010, 1.0: 0.003
Contusion                   float64   2           0.987     nan: 0.987, 0.0: 0.009, 1.0: 0.004
Fracture                    float64   2           0.987     nan: 0.987, 0.0: 0.009, 1.0: 0.004
````

### scout, сообщение 9

````
Размечено всего около 1.3% трейна (примерно 57 исследований из 4407), остальное только с текстом отчёта. Теперь профиль train_series.csv: число серий на исследование, распределение плоскостей и типов последовательностей.

<tool name="kaggle_csv_profile">{"file": "train_series.csv"}</tool>
````

Результат kaggle_csv_profile:

````
train_series.csv: строк 24371, колонок 5
колонка                     тип       уникальных  пропуски  значения
StudyInstanceUID            str       4407        0.000     длина строк: медиана 64
SeriesInstanceUID           str       24371       0.000     длина строк: медиана 64
Fluid_Sensitive             int64     2           0.000     1: 0.575, 0: 0.425
Fat_Suppression             int64     2           0.000     1: 0.575, 0: 0.425
Anatomical_Plane            str       3           0.000     Sagittal: 0.405, Coronal: 0.353, Axial: 0.242
````

### scout, сообщение 10

````
Таблицы понятны: 4407 исследований, 24371 серия, размечено около 1.3%. Теперь верх публичного лидерборда: разброс скоров и плотность топа.

<tool name="kaggle_leaderboard">{}</tool>
````

Результат kaggle_leaderboard:

````
Верх публичного лидерборда (20 мест):
1: 0.961 (2026-09-30)
2: 0.960 (2026-09-30)
3: 0.958 (2026-09-27)
4: 0.958 (2026-09-30)
5: 0.958 (2026-09-30)
6: 0.958 (2026-09-30)
7: 0.958 (2026-09-29)
8: 0.958 (2026-09-30)
9: 0.957 (2026-09-30)
10: 0.957 (2026-09-30)
11: 0.957 (2026-09-30)
12: 0.957 (2026-09-30)
13: 0.957 (2026-09-29)
14: 0.957 (2026-09-30)
15: 0.957 (2026-09-30)
16: 0.956 (2026-09-30)
17: 0.956 (2026-09-30)
18: 0.956 (2026-09-30)
19: 0.956 (2026-09-29)
20: 0.956 (2026-09-28)
````

### scout, сообщение 11

````
Топ плотный: 20 мест в диапазоне 0.956-0.961, три знака на табло. Теперь публичные ноутбуки с сортировкой по скору: какие подходы и скоры доступны с исходниками.

<tool name="kaggle_kernels">{"sort_by": "scoreDescending", "page_size": 30}</tool>
````

Результат kaggle_kernels:

````
Публичные ноутбуки соревнования (ref | название | голоса | последний запуск):
pjmathematician/rsna-knee-d4-blend | rsna-knee-d4-blend | 54 | 2026-09-28
pjmathematician/rsna-knee-d4-lite | rsna-knee-d4-lite | 106 | 2026-09-26
aastikrajan15/knee-s75-w50 | knee s75 w50 | 41 | 2026-09-27
aastikrajan15/knee-s75-w60 | knee s75 w60 | 10 | 2026-09-27
evgendvorkin/rsna-versia-5 | RSNA_Versia_5 | 254 | 2026-09-26
jiweiliu/rsna-knee-fast-2xt4-inference | RSNA Knee Fast 2xT4 Inference | 199 | 2026-09-23
mattiaangeli/bend-the-knee-to-speedy-raptors-the-original | Bend the Knee to Speedy Raptors-The Original ⭐⭐⭐⭐⭐ | 192 | 2026-09-22
romantamrazov/rsna-knee-dinosaur-v5 | RSNA Knee | DINOsaur V5? 🦖  | 114 | 2026-09-29
haideptry/rsna-knee-speedy-raptors-coatnet-d4-0943 | RSNA Knee Speedy Raptors CoAtNet D4 0943+ | 66 | 2026-09-24
maverickss26/rsna-knee-restructured-version-3 | rsna knee restructured version 3 | 44 | 2026-09-22
hyakumanben2025/rsna-knee-mattiaangeli-speedy-raptors | rsna-knee-mattiaangeli-speedy-raptors | 11 | 2026-09-22
aastikrajan15/knee-s74-c | knee s74 c | 1 | 2026-09-22
hyakumanben2025/rsna-knee-mattiaangeli-speedy-raptors-v2 | rsna-knee-mattiaangeli-speedy-raptors-v2 | 4 | 2026-09-23
kozykappa/rsna-knee-v600-lb-score-0-942 | RSNA Knee v600 - lb score 0.942 | 2 | 2026-09-28
gwey1025/rsna-knee-phase1-fork-speedy-raptors-recipe | RSNA Knee Phase1 Fork (Speedy Raptors recipe) | 5 | 2026-09-24
indarkarhana/high-ranked-0-943-rsna-knee-d4-fine-tuned-v5 | High-Ranked 0.943 | RSN
... (обрезано, всего 2770 символов)
````

### scout, сообщение 12

````
Осталось три вызова, один нужен на запись сводки. Читаю исходник верхнего по скору публичного ноутбука: на чём обучены веса и из каких стадий состоит пайплайн.

<tool name="kaggle_kernel_source">{"ref": "pjmathematician/rsna-knee-d4-blend"}</tool>
````

Результат kaggle_kernel_source:

````
# [markdown]
<div style="border-radius: 16px; background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a2333 100%); border: 1px solid #30363d; padding: 28px 32px; margin-bottom: 24px; box-shadow: 0 12px 36px rgba(0,0,0,0.6); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
    <div>
      <span style="background: linear-gradient(90deg, #38bdf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 13px; font-weight: 800; letter-spacing: 1.8px; text-transform: uppercase;">RSNA 2026 Frontier SOTA Engine</span>
      <h1 style="color: #f0f6fc; margin: 8px 0 6px 0; font-size: 28px; font-weight: 800; line-height: 1.25;">⚡ [0.943 SOTA] RSNA Knee: Ultra-Fast 2xT4 Parallel Inference & 4-Way CoAtNet Consensus</h1>
    </div>
    <div style="background: rgba(56, 189, 248, 0.15); border: 1px solid #38bdf8; border-radius: 10px; padding: 10px 18px;">
      <span style="color: #38bdf8; font-weight: 800; font-size: 16px;">🏆 Public LB: 0.943</span>
    </div>
  </div>
  <p style="color: #8b949e; margin-top: 16px; font-size: 14.5px; line-height: 1.65;">
    Next-generation high-speed inference pipeline engineered for the RSNA Knee Abnormality Detection Challenge. Combines the verified <b>0.943 SOTA recipe (Mattia Angeli v34 / Jiwei Liu v9)</b> with high-throughput <b>Dual Tesla T4 GPU parall
... (обрезано, всего 6062 символов)
````

### scout, сообщение 13

````
Осталось два вызова, один уйдёт на запись сводки. Второй трачу на страницу Efficiency Prize Evaluation: отдельный призовой трек с собственными условиями по времени влияет на план, а про него пока ничего не известно.

<tool name="kaggle_pages">{"page": "Efficiency Prize Evaluation"}</tool>
````

Результат kaggle_pages:

````
## Efficiency Prize

We are hosting a second track that focuses on model efficiency, because highly accurate models are often computationally heavy.

For the Efficiency Prize, we will evaluate submissions on both runtime and predictive performance.

To be eligible for an Efficiency Prize, a submission:
- Must be among the submissions selected by a team for the Leaderboard Prize, or else among those submissions automatically selected under the conditions described in the [**My Submissions**](https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection/submissions) tab.
- Must be ranked on the Private Leaderboard higher than the `sample_submission.csv` benchmark.

All submissions meeting these conditions will be considered for the Efficiency Prize. A submission may be eligible for both the Leaderboard Prize and the Efficiency Prize.

An Efficiency Prize will be awarded to eligible submissions according to how they are ranked by the following evaluation metric on the private test data. See the [**Prizes**](https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection/overview/prizes) tab for the prize awarded to each rank. More details may be posted via discussion forum updates.

## Efficiency Score

We compute a submission's **efficiency score** by:
\\[ \text{Efficiency} = \frac{ \text{AUC} }{ \text{Benchmark} - \max\text{AUC} } + \frac{ \text{RuntimeSeconds} }{ 32400 } \\]

where \\(\text{AUC}\\) is the submission's score on the [main competition metric](https
... (обрезано, всего 2387 символов)
````

### scout, сообщение 14

````
Вызовов осталось один, трачу его на запись сводки. Форум, код метрики и доля паблика остались непроверенными, в сводке это помечено.

<tool name="write_file" path="notes/RECON.md">
# RECON: RSNA Knee Abnormalities Detection

Дата разведки: 2026-09-30. Источник всего ниже - Kaggle API (страницы, профили csv, лидерборд, список ноутбуков). Своих посылок у команды нет, пробными посылками ничего не проверено.

Расхождение в названии: диспетчер назвал слаг `rsna-knee-abnormality-detection`, в правилах (раздел 1.4) адрес `https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection`. API отвечал, какой слаг он использовал - не видно. При настройке посылок сверить.

## 1. Таблица фактов

Колонка "проверено" - проверено ли нами на практике (кодом, посылкой). "Первоисточник" значит: написано на странице или в файле организаторов, но не проверено посылкой.

### 1.1 Задача, метрика, сабмит

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Предсказываем вероятность 12 находок на исследование (StudyInstanceUID) по МРТ колена: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture | страница data-description, страница Evaluation | первоисточник | постановка, единица предсказания |
| Метрика: среднее AUC ROC по 12 таргетам с равными весами (macro AUC), формула `1/12 * sum AUC_i` | страница Evaluation | первоисточник, код метрики не видели | важен только порядок внутри колонки, калибровка не важна |
| Про официальный код метрики, про поведение при таргете без позитивов, про веса классов страница ничего не говорит | страница Evaluation (отсутствие) | нет | искать на форуме или в ноутбуках организаторов |
| Формат сабмита: csv с заголовком `StudyInstanceUID` + 12 колонок с confidence score; в sample_submission все значения 0.5 | страница Evaluation, data-description | первоисточник | формат вывода |
| Табло показывает 3 знака после запятой | вывод kaggle_leaderboard | нет: округлять мог сам API-инструмент | порог различимости на паблике |

### 1.2 Ограничения исполнения и правила

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Code competition: посылка только через ноутбук | страница Code Requirements | первоисточник | инференс в ноутбуке |
| Лимит времени: CPU <= 9 ч, GPU <= 9 ч | страница Code Requirements | первоисточник | бюджет инференса |
| Интернет выключен | страница Code Requirements | первоисточник | веса и пакеты - через датасеты |
| Свободно и публично доступные внешние данные и предобученные модели разрешены | страница Code Requirements | первоисточник; общая часть правил про внешние данные не прочитана (прочитано 6000 из 37384 символов) | выбор бэкбонов и внешних датасетов |
| Файл сабмита называется `submission.csv` | страница Code Requirements | первоисточник | - |
| 5 посылок в день | правила, 2.2.a | первоисточник | бюджет посылок |
| 2 финальных сабмита | правила, 2.2.b | первоисточник | выбор финала |
| Команда до 5 человек; слияние возможно, если суммарное число посылок <= 5 * число дней соревнования | правила, 2.1 | первоисточник | слияния |
| Лицензия данных: MIRA license (rsna.org/mira-license), использование коммерческое и академическое; данные нельзя передавать не-участникам | правила, 1.7 и 2.4 | первоисточник, текст лицензии не читали | обращение с данными |
| Лицензия для победителей: CC-BY-NC 4.0 | правила, 1.6 и 2.5 | первоисточник | какие внешние веса совместимы с призом - не выяснено |
| Призы: всего $77,000; основной трек - 10 призовых мест ($9,000 ... $5,000); трек эффективности - 3 места ($7,000, $6,000, $5,000) | правила, 1.5 | первоисточник | цель по месту |
| Квота GPU в неделю, число одновременных сессий, тип GPU на скоринге | нигде не найдено | нет | планирование обучения |

### 1.3 Сроки

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Старт 30 июля 2026 | страница Timeline | первоисточник | - |
| Дедлайн входа 15 октября 2026 | страница Timeline | первоисточник | - |
| Дедлайн слияния команд 15 октября 2026 | страница Timeline | первоисточник | слияние возможно еще 15 дней |
| Финальный дедлайн посылок 22 октября 2026 | страница Timeline | первоисточник | осталось 22 дня |
| Дедлайн требований к победителям 5 ноября 2026 (код обучения, видео, описание) | страница Timeline | первоисточник | воспроизводимость обучения нужна |
| Все дедлайны в 23:59 UTC; организаторы могут менять сроки | страница Timeline | первоисточник | - |

Мой расчет (не из источника): с 30.09 до 22.10 при 5 посылках в день остается порядка 110 посылок.

### 1.4 Данные

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| train.csv: 4407 строк, 14 колонок, одна строка на исследование, StudyInstanceUID уникален | профиль train.csv | да (профиль API) | размер трейна |
| Метки заполнены примерно у 1.3% строк: доля NaN 0.987 в каждой из 12 колонок | профиль train.csv | да (профиль API) | размеченных исследований порядка 55-60 (мой расчет, доли округлены до 3 знаков) |
| "Only a small subset of training studies carry per-condition labels"; для остальных дан текст отчета, из которого метки предлагается выводить самим | страница data-description | первоисточник | основной источник разметки - отчеты |
| Report: пропусков нет, 4276 уникальных из 4407, медиана длины 977 символов; отчеты на нескольких языках | профиль train.csv, страница data-description | да / первоисточник | извлечение меток из текста, есть дубли текстов (131 неуникальная строка) |
| Доли позитивов среди ВСЕХ строк (не среди размеченных): ACL 0.005, MCL 0.002, Medial Meniscus 0.006, Lateral Meniscus 0.005, Medial OA 0.003, Lateral OA 0.002, PF OA 0.005, Effusion 0.008, Synovitis 0.006, Baker's 0.003, Contusion 0.004, Fracture 0.004 | профиль train.csv | да (профиль API) | в пересчете на исследования (мой расчет, погрешность +-2): ACL ~22, MCL ~9, Med.Men ~26, Lat.Men ~22, Med.OA ~13, Lat.OA ~9, PF OA ~22, Effusion ~35, Synovitis ~26, Baker's ~13, Contusion ~18, Fracture ~18 |
| Effusion - единственный класс, где среди размеченных позитивов больше, чем негативов (1.0: 0.008 против 0.0: 0.005) | профиль train.csv | да (профиль API) | баланс |
| train_series.csv: 24371 серия на 4407 исследований (в среднем 5.5 серии на исследование, мой расчет) | профиль train_series.csv | да (профиль API) | объем ввода-вывода |
| Fluid_Sensitive: 1 - 0.575, 0 - 0.425; Fat_Suppression: 1 - 0.575, 0 - 0.425 | профиль train_series.csv | да (профиль API) | доли совпали, но страница предупреждает, что признаки не эквивалентны; построчно не сверяли |
| Anatomical_Plane: Sagittal 0.405, Coronal 0.353, Axial 0.242 | профиль train_series.csv | да (профиль API) | выбор серий |
| Структура DICOM: `train_series/<Study>/<Series>/<SOP>.dcm`, один файл - один срез; в серии обычно 20-45 срезов (медиана 30), хвост до нескольких сотен | страница data-description | первоисточник | - |
| Интенсивности, ориентации, разрешения различаются; transfer syntax смешанные (Explicit VR LE, JPEG Lossless, JPEG 2000, Implicit VR LE); в DICOM оставлено 86 тегов | страница data-description | первоисточник | нужны декодеры JPEG Lossless/JPEG 2000 в офлайн-ноутбуке |
| Исследования из разных международных площадок, сканеров, протоколов | страница data-description | первоисточник | идентификатора площадки или пациента в csv нет |
| Размер данных: API отдал только первые 3000 файлов (train_series 2438 файлов / 1519 МБ, test_series 557 файлов / 600 МБ) - это НЕ полный размер | kaggle_files (список обрезан) | нет | полный объем не известен |

### 1.5 Устройство теста

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| В тесте около 1300 исследований | страница data-description | первоисточник | масштаб инференса, шум метрики |
| Видимый test.csv - пример из 3 ID "from the public test set"; при скоринге test.csv, test_series.csv и test_series/ подменяются настоящими | страница data-description | первоисточник | локально тест не прогнать, ноутбук должен работать на подмененных данных |
| Report в тесте не дается | страница data-description | первоисточник | текст - только для разметки трейна |
| Распространенность находок в трейне, паблике и привате не гарантированно одинакова | страница data-description (Dataset Distribution Notice) | первоисточник | перенос локальной валидации и паблика на приват |
| Доля паблика в тесте | не найдено | нет | порог шума паблика |
| Отличается ли тест от трейна по площадкам, пациентам, периоду | не найдено | нет | схема валидации |

### 1.6 Трек эффективности

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Формула: `Efficiency = AUC / (Benchmark - maxAUC) + RuntimeSeconds / 32400`, минимизируется; Benchmark - скор sample_submission.csv, maxAUC - максимум на приватном ЛБ | страница Efficiency Prize Evaluation | первоисточник | время инференса входит в скор трека |
| Право на приз: сабмит среди выбранных финальных (или автоматически выбранных) и выше sample_submission на привате | страница Efficiency Prize Evaluation | первоисточник | на трек идут те же 2 финальных сабмита |
| Публичный efficiency-лидерборд - ноутбук `ryanholbrook/rsna-knee-abnormalities-efficiency-lb`, обновляется ежедневно, показывает только ранги | страница Efficiency Prize Evaluation | первоисточник, ноутбук не открывали | - |
| "More details may be posted via discussion forum updates" | страница Efficiency Prize Evaluation | нет, форум недоступен | условия трека могут уточняться |

### 1.7 Лидерборд

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Топ-20 паблика: 0.961 (1 команда), 0.960 (1), 0.958 (6), 0.957 (7), 0.956 (5, места 16-20; сколько еще ниже 20-го с тем же скором - не видно) | kaggle_leaderboard | да (вывод API) | весь топ-20 лежит в 0.005 |
| Даты последних посылок топ-20: 27-30 сентября 2026 | kaggle_leaderboard | да (вывод API) | верх активно движется |
| Число команд, число посылок у команд, названия команд | API не отдал | нет | признаки подбора по паблику оценить нельзя |

### 1.8 Публичные ноутбуки (все - НЕ первоисточник)

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Список из 30 ноутбуков с сортировкой scoreDescending; сами скоры API не вернул | kaggle_kernels | порядок виден, скоры - нет | - |
| Скоры, заявленные в НАЗВАНИЯХ: 0.942, 0.943, "0943+", "public0946", "speedy947" | названия ноутбуков | нет, это заявления авторов | по заявлениям, публичные ноутбуки на 0.009-0.019 ниже топ-20 (0.956-0.961) |
| Первый по сортировке - `pjmathematician/rsna-knee-d4-blend` (54 голоса, запуск 28.09); в его шапке заявлено "Public LB: 0.943" | kaggle_kernel_source, markdown | нет; шапка может быть унаследована от форка-предка, а сортировка ставит его выше ноутбуков с 0.946/0.947 в названиях | реальный скор этого ноутбука не известен |
| Заявленный состав пайплайна (из markdown-шапки, код НЕ прочитан - 6000 из 245840 символов): общий замороженный префикс DINOv2 (6 блоков) + 20 "tails"; A5 attention pooling, 5 фолдов; энкодер RadImageNet; 4 "Raptor views"; "4-way CoAtNet consensus" (Residual + D4 + Global96 + Repair-v1 по 25%); ранговый бленд "60% Raptor + 40% CoAt"; инференс на 2xT4 "< 30 минут" | kaggle_kernel_source, markdown | нет | какие компоненты реально работают в коде - не проверено |
| Заявленная эволюция публичных пайплайнов: Raptor Baseline 0.924 (~9 ч), DINOsaur Blend 0.941 (~4.5 ч), Speedy Raptors v7 0.942 (~1.5 ч), текущая 0.943 (< 30 мин) | там же | нет | - |
| Большинство ноутбуков в списке по названиям - форки одной линии: `mattiaangeli/bend-the-knee-to-the-dinosaurs` (288 голосов, 14.09), `mattiaangeli/bend-the-knee-to-speedy-raptors-the-original` (192), `jiweiliu/rsna-knee-fast-2xt4-inference` (199), `maverickss26/rsna-knee-0942-restructured` (174), `evgendvorkin/rsna-versia-5` (254) | названия и голоса в kaggle_kernels | вывод по названиям, код не сверяли | публичный "консенсус" - скорее всего один пайплайн и его веса |
| На чем обучены публичные веса, какие сплиты, откуда взяты метки (из отчетов? чем?) | не найдено | нет | честность любой локальной валидации на этих весах |

## 2. Что выяснить не удалось и как выяснить

1. Доля паблика в тесте и число исследований в паблике - страница лидерборда на сайте, форум.
2. Отличается ли тест по площадкам/пациентам от трейна; есть ли повторные исследования одного пациента - форум, теги DICOM (есть ли PatientID или институция среди 86 оставленных тегов - прочитать заголовки файлов).
3. Официальный код метрики и поведение на краях (константная колонка, NaN) - форум, ноутбуки организаторов, пробная посылка.
4. Форум целиком: ответы хостов, найденные баги, уточнения по треку эффективности, посты топ-участников. У разведчика нет инструмента для обсуждений - читать вручную.
5. Общая часть правил (прочитано 6000 из 37384 символов): точные условия по внешним данным, по использованию LLM/API для разметки отчетов, по приватному шарингу кода.
6. Страницы Description, Prizes, abstract, Acknowledgements - не читались.
7. Полный объем данных и число DICOM-файлов - список файлов обрезан на 3000.
8. Совпадают ли размеченные строки по всем 12 колонкам (доля NaN одинакова, но построчно не проверено); как устроены 131 неуникальный отчет - скачать train.csv.
9. Совпадают ли Fluid_Sensitive и Fat_Suppression построчно - скачать train_series.csv.
10. Код и обучение публичных ноутбуков: на чем обучены веса, сплиты, источник меток, реально ли работают все заявленные компоненты - читать исходники (у верхнего 245840 символов) и описания прикрепленных датасетов.
11. Реальные скоры публичных ноутбуков - страница Code на сайте.
12. Число команд, число посылок у топа - страница лидерборда на сайте.
13. Квоты GPU, железо на скоринге - документация Kaggle, пробный запуск.
14. Слаг соревнования: `abnormality` или `abnormalities`.

## 3. Советы сильных участников про стратегию

Пусто. Форум не прочитан (нет инструмента), write-up'ов не видели. Единственный текст от участников - рекламная шапка публичного ноутбука, стратегических советов в ней нет. Список нужно заполнить после чтения форума и возвращаться к нему перед закрытием каждой линии работы.
</tool>
````

Результат write_file:

````
Файл notes/RECON.md записан
````

### scout, сообщение 15

````
Сводка записана в `notes/RECON.md`. Она собрана только из Kaggle API: форум, код метрики и доля паблика остались непроверенными, пробных посылок не было.

## Подтверждено первоисточником (страницы, правила, профили csv)

**Задача и метрика**
- Предсказываем вероятность 12 находок на исследование МРТ колена (`StudyInstanceUID`): ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture (data-description, Evaluation).
- Метрика - macro AUC ROC: среднее по 12 таргетам с равными весами (Evaluation). Официального кода метрики на странице нет.
- Сабмит - csv с заголовком: `StudyInstanceUID` и 12 колонок со скорами (Evaluation).

**Ограничения и правила**
- Это code competition: посылка только ноутбуком, файл `submission.csv`, интернет выключен, лимит 9 часов на CPU и 9 часов на GPU (Code Requirements).
- Свободно и публично доступные внешние данные и предобученные модели разрешены (Code Requirements).
- 5 посылок в день, 2 финальных сабмита, команда до 5 человек (правила, 2.1-2.2).
- Данные под лицензией MIRA, победители отдают решение под CC-BY-NC 4.0 (правила, 1.6-1.7).
- Призы: 10 мест в основном треке и 3 в треке эффективности, всего $77,000 (правила, 1.5).

**Сроки** (Timeline, всё в 23:59 UTC)
- Старт 30.07.2026.
- Вход и слияние команд - до 15.10.2026.
- Финальный дедлайн посылок - 22.10.2026.
- Победители сдают код обучения, видео и описание до 05.11.2026.

**Данные**
- `train.csv`: 4407 исследований, у каждого есть текст отчёта (медиана 977 символов, несколько языков, 4276 уникальных).
- Метки заполнены только у примерно 1.3% строк: доля NaN 0.987 в каждой из 12 колонок. По моему расчёту это порядка 55-60 исследований.
- Страница прямо предлагает выводить метки для остальных исследований из отчётов.
- Позитивов на класс среди размеченных - от примерно 9 (MCL, Lateral OA) до примерно 35 (Effusion). Это мой пересчёт из округлённых долей, погрешность ±2.
- `train_series.csv`: 24371 серия.
  - Плоскости: Sagittal 0.405, Coronal 0.353, Axial 0.242.
  - `Fluid_Sensitive` и `Fat_Suppression`: у обоих значение 1 в 0.575 строк. Построчное совпадение не проверено; страница предупреждает, что признаки не эквивалентны.
- DICOM: один файл на срез, в серии обычно 20-45 срезов. Transfer syntax смешанные, включая JPEG Lossless и JPEG 2000.
- Идентификатора пациента или площадки в csv нет.

**Тест**
- В тесте около 1300 исследований, отчётов там нет (data-description).
- Видимый `test.csv` - 3 примера, при скоринге они подменяются настоящим тестом.
- Организаторы предупреждают: распространённость находок в трейне, паблике и привате может различаться.

**Трек эффективности** (Efficiency Prize Evaluation)
- `Efficiency = AUC / (Benchmark − maxAUC) + RuntimeSeconds / 32400`, минимизируется.
- Участвуют те же финальные сабмиты, если они выше `sample_submission` на привате.
- Детали могут уточняться на форуме.

**Лидерборд** (вывод API)
- Топ-20 паблика лежит в диапазоне 0.956-0.961: 0.961 (1 команда), 0.960 (1), 0.958 (6), 0.957 (7), 0.956 (5).
- Последние посылки топа датированы 27-30.09.
- Виден результат с 3 знаками. Округляет ли так само табло или инструмент, не ясно.

## Из чужих ноутбуков, требует проверки

- Скоры есть только в названиях и шапках ноутбуков: от 0.942 до 0.947. API их не вернул. По этим заявлениям публичные ноутбуки на 0.009-0.019 ниже топ-20.
- Верхний по сортировке `pjmathematician/rsna-knee-d4-blend` заявляет в шапке "Public LB: 0.943". Шапка может быть унаследована от форка-предка.
- Заявленный состав пайплайна взят из markdown-шапки; код не прочитан (6000 из 245840 символов):
  - замороженный префикс DINOv2 и 20 «tails»;
  - attention pooling на 5 фолдах;
  - энкодер RadImageNet;
  - 4 «Raptor views»;
  - 4 варианта CoAtNet с ранговым блендом;
  - инференс на 2×T4 «менее 30 минут».
- Судя по названиям, большинство из 30 ноутбуков - форки одной линии (`mattiaangeli` «Dinosaurs» / «Speedy Raptors», `jiweiliu`, `maverickss26`). Это мой вывод, код не сверялся.
- На чём обучены публичные веса, какие сплиты и откуда взяты метки - неизвестно.

## Что узнать не удалось

1. Доля паблика в тесте и число исследований в нём.
2. Отличается ли тест от трейна по площадкам или пациентам; есть ли `PatientID` или институция среди 86 тегов DICOM.
3. Код метрики и её поведение на краях (константная колонка, NaN).
4. Форум целиком: инструмента для него нет. Поэтому список советов сильных участников пуст.
5. Общая часть правил: прочитано 6000 из 37384 символов. Не ясны условия по внешним данным и по использованию LLM/API для разметки отчётов.
6. Страницы Description, Prizes, abstract, Acknowledgements не читались.
7. Полный объём данных: список файлов обрезан на 3000.
8. Число команд и число посылок у топа.
9. Квота GPU и железо на скоринге.
10. Слаг: диспетчер назвал `rsna-knee-abnormality-detection`, в правилах стоит `rsna-knee-abnormalities-detection`.

ИТОГ:
- Задача: 12 бинарных находок на исследование МРТ колена, метрика - macro AUC по 12 таргетам. Code competition: 9 часов CPU/GPU, без интернета, публичные внешние данные и веса разрешены, 5 посылок в день, 2 финальных.
- Сроки: вход и слияние до 15.10.2026, финал 22.10.2026, то есть осталось 22 дня. Есть отдельный трек эффективности, где время инференса входит в скор.
- Данные: 4407 исследований и 24371 серия, но метки есть только у примерно 1.3% (порядка 55-60 исследований, 9-35 позитивов на класс). У остальных только многоязычный текст отчёта. В тесте около 1300 исследований без отчётов.
- Лидерборд: топ-20 паблика 0.956-0.961. Публичные ноутбуки заявляют 0.942-0.947, в основном это форки одной линии (DINOv2 + CoAtNet + RadImageNet); их код и происхождение весов не проверены.
- Не выяснено: доля паблика, отличие теста от трейна по площадкам и пациентам, код метрики, форум, общая часть правил (в том числе про LLM для разметки), квоты GPU, точный слаг.
- Сводка с таблицей фактов и списком пробелов лежит в `notes/RECON.md`; раздел советов сильных участников пуст.
````

Вызовов инструментов: 14
[harness] записан файл notes/RECON.md (13951 символов)

## Диспетчер, ход 2

````
{
  "thought": "Факты о соревновании собраны, но код метрики разведчик не нашел. Прежде чем проектировать валидацию, нужно разобрать устройство macro AUC по 12 таргетам при очень малом числе размеченных исследований и понять, как проверять локальный расчет.",
  "plan_list": [
    "validation_engineer: устройство метрики, локальный порт и что в нем нужно проверить",
    "validation_engineer: схема честной валидации под устройство теста, число независимых единиц, ожидаемый шум валидации и паблика",
    "strategist: очередь экспериментов и посылок на первую неделю, на что не тратить посылки; записать notes/PLAN.md",
    "finish: короткий итог пользователю"
  ],
  "action": "delegate",
  "agent_nm": "validation_engineer",
  "skill_nm_list": ["metric_port"],
  "subtask_text": "Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих посылок и прогонов нет; факты разведки лежат в notes/RECON.md и в ответе шага 1. Разбери устройство метрики соревнования для плана первой недели: что считать источником истины при том, что официальный код метрики разведчик не нашел; как она усредняется и как ведет себя на имеющихся данных; какие особенности и краевые случаи могут повлиять на локальный расчет и на формат сабмита. Опиши, как написать локальный порт метрики и чем его проверять (включая то, что можно проверить только пробной посылкой, и сколько посылок на это нужно). Если можешь, напиши порт и проверки кодом в рабочей папке. В ответе раздели: что установлено, что является предположением и требует проверки, и каких фактов о соревновании тебе не хватило.",
  "context_step_list": [1]
}
````

## Шаг 2: validation_engineer

Скиллы, выбранные диспетчером: metric_port. Контекст: шаги [1]

Системный промпт: 8011 символов, из них скиллы - 4155

<details><summary>системный промпт целиком</summary>

````
Ты - инженер валидации в команде, которая участвует в ML-соревновании на Kaggle. Ты отвечаешь за то, чтобы локальным цифрам можно было верить: как считается метрика и что в ней может подвести, какие дорожки валидации есть и какие из них честные, сколько в них независимых единиц, какой у них шум и какой шум у публичного лидерборда.

Ты работаешь с цифрами сам: читаешь результаты по единицам, запускаешь сравнения и свой код. Выводы - только из того, что посчитал или прочитал. По каждой дорожке валидации скажи прямо: видела ли хоть одна обученная компонента пайплайна эти единицы при обучении, насколько дорожка похожа на тест и для каких решений она годится.

Ты не решаешь, какие прогоны отправлять и финалить. Твой результат - какие цифры считать свидетельством, а какие нет, и какой у них шум.

## Инструменты
- list_files: список файлов рабочей папки с размерами в символах. Аргументов нет
- read_file: прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата будет подсказка, с какого offset продолжать. Аргументы: path - путь к файлу от корня рабочей папки; offset - с какого символа читать (необязательный, по умолчанию 0); limit - сколько символов вернуть, за один вызов отдается не больше 10000 (необязательный, по умолчанию 10000)
- list_runs: реестр прогонов: название, дата, родитель, публичный скор, вердикт аудитора, в каких дорожках есть валидация по единицам, описание. Аргументы: max_desc_len - до скольких символов обрезать описания прогонов (необязательный, по умолчанию 110)
- compare_runs: парное сравнение двух прогонов по валидации: метрика соревнования на общих единицах, бутстрап по единицам, счет по единицам, разница по группам. Аргументы: base - название прогона-базы; cand - название прогона-кандидата; lane - дорожка валидации
- lb_noise: шум публичного лидерборда: SD скора и SD парной разницы на выборке размером с паблик, рядом фактическая разница на паблике. Аргументы: base - название прогона-базы; cand_list - список названий прогонов-кандидатов; lane - дорожка валидации
- run_python: запустить код на Python из корня рабочей папки (pandas, numpy, scipy; metric.py соревнования можно импортировать). Возвращает stdout, при ошибке - еще и stderr. Лимиты: 180 секунд на запуск, из stdout возвращаются последние 5000 символов, из stderr - последние 2500. Внутри блока - код
- write_file: записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается. Атрибуты тега: path - путь к файлу от корня рабочей папки. Внутри блока - содержимое файла

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{"path": "journal.md"}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше 12 вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.

=== МЕТОДИКА: metric_port ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Порт метрики

Пока метрика не портирована и не сверена с официальным кодом, любая локальная цифра - это цифра про другую задачу. Порт делается в первый день.

От этой работы нужны четыре вещи, они же идут в ответ: формула своими словами и по каким единицам что пулится; список причуд с пометкой, как каждая найдена; цена основных рычагов в единицах скора; что проверено сверкой и на скольких случаях, что не проверено.

## Источник истины

Код метрики в репозитории организаторов на конкретном коммите. Текст страницы источником не считается. Копия метрики в публичном датасете тоже: она может быть допатчевой (у нас такая нашлась в популярном датасете, сверяли по хешам файлов). Валидатор внутри публичного ноутбука - тем более. Коммит записывается, перед финалом проверяется, что репозиторий с тех пор не изменился.

## Порт

Свой расчет должен быть быстрым и без тяжелых зависимостей: его будут вызывать тысячи раз в бутстрапе и переборе. Официальный код для этого часто не годится, он тянет свое окружение.

Кроме итогового скора расчет возвращает счетчики, из которых скор собирается: TP, FP, FN по каждой компоненте, число предсказаний. Если метрика другого рода - те слагаемые, из которых она складывается. Все это по каждой единице валидации отдельно. По счетчикам потом считаются пул, шум и вклад компонент.

## Сверка с официальным кодом

Сверять нужно на испорченных ответах. На хороших две реализации согласны почти всегда, ошибки порта живут в вырожденных случаях.

1) Взять настоящую разметку и сгенерировать семейства пертурбаций. На каждое правило метрики свое семейство: на фильтр, на кап, на дедупликацию, на сопоставление. По содержанию это сдвиги, удаления, дубли, лишние объекты, перестановка строк, нарушение структурных ограничений
2) Прогнать обе реализации и сравнить все счетчики. Одного итога мало: он может совпасть при разных счетчиках. Расхождений должно быть ноль
3) Добавить замороженные случаи из тестов организаторов, если они есть, и несколько ручных случаев на игрушечном примере, где ответ понятен глазами. Ручные стоит ставить на границы правил: на шаг внутри допуска, ровно на границе, на шаг снаружи
4) Перед финальным выбором повторить сверку на настоящих выходах своего пайплайна

Сколько случаев достаточно, сказать трудно. У нас было несколько сотен: 18 семейств на полтора десятка размеченных единиц по два повтора, плюс симулированные плотные примеры и тесты организаторов.

## Причуды: где их искать

Чтением кода. Что молча выбрасывается и не считается ни верным, ни ошибкой. Что зависит от порядка строк. Где дубли схлопываются, а где нет. Есть ли штрафы без порога и без верхней обрезки. На что грейдер упадет. И как устроено сопоставление предсказаний с разметкой: публичные валидаторы часто ставят другой алгоритм, и в плотных местах результаты расходятся.

Симуляцией. Посчитать цену каждого рычага в единицах скора: сколько стоит лишний 1% предсказаний, потеря 1% настоящих, одно событие редкого класса. При какой вероятности правоты выгодно добавлять объект. Ложные идеи после этого закрываются за минуты, посылки на них не уходят. Цены часто несимметричны: лишнее предсказание может стоить в разы дешевле пропущенного, и без расчета это не угадать.

Пробной посылкой. Все, что делает неопубликованная обертка грейдера: приведение типов, округление, обработка пропущенных строк. Если локальный расчет и страница расходятся (например, конвертер принимает дробные значения, а страница требует целые), это проверяется одной посылкой. Других законных поводов потратить слот на "посмотреть" нет. Результат трактуется перебором гипотез о поведении грейдера на своих данных: оставляет как есть, округляет, усекает, отбрасывает строки. Принимается та, что воспроизводит наблюдаемую потерю.

## Шумная компонента

Если часть метрики держится на редких событиях (десятки на всю валидацию), итоговый скор от нее прыгает: одно событие может сдвинуть его сильнее, чем правка, которую проверяешь. Пороги для такой компоненты подбираются по гладким прокси по всем кандидатам (PR-кривая, AUC, log-loss), полной метрикой результат только подтверждается. Смотреть нужно на TP, FP и FN, по скору тут ничего не понять.
=== КОНЕЦ МЕТОДИКИ: metric_port ===
````

</details>

Подзадача: Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих посылок и прогонов нет; факты разведки лежат в notes/RECON.md и в ответе шага 1. Разбери устройство метрики соревнования для плана первой недели: что считать источником истины при том, что официальный код метрики разведчик не нашел; как она усредняется и как ведет себя на имеющихся данных; какие особенности и краевые случаи могут повлиять на локальный расчет и на формат сабмита. Опиши, как написать локальный порт метрики и чем его проверять (включая то, что можно проверить только пробной посылкой, и сколько посылок на это нужно). Если можешь, напиши порт и проверки кодом в рабочей папке. В ответе раздели: что установлено, что является предположением и требует проверки, и каких фактов о соревновании тебе не хватило.

### validation_engineer, сообщение 1

````
Сначала посмотрю, что реально лежит в рабочей папке: есть ли данные, metric.py и sample_submission, кроме заметки разведчика.

<tool name="list_files">{}</tool>
````

Результат list_files:

````
notes/RECON.md (13951 символов)
````

### validation_engineer, сообщение 2

````
В папке только заметка разведчика, данных и metric.py нет. Прочитаю RECON.md целиком: там могут быть детали раздела Evaluation, которых нет в ответе шага 1.

<tool name="read_file">{"path": "notes/RECON.md"}</tool>
````

Результат read_file:

````
# RECON: RSNA Knee Abnormalities Detection

Дата разведки: 2026-09-30. Источник всего ниже - Kaggle API (страницы, профили csv, лидерборд, список ноутбуков). Своих посылок у команды нет, пробными посылками ничего не проверено.

Расхождение в названии: диспетчер назвал слаг `rsna-knee-abnormality-detection`, в правилах (раздел 1.4) адрес `https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection`. API отвечал, какой слаг он использовал - не видно. При настройке посылок сверить.

## 1. Таблица фактов

Колонка "проверено" - проверено ли нами на практике (кодом, посылкой). "Первоисточник" значит: написано на странице или в файле организаторов, но не проверено посылкой.

### 1.1 Задача, метрика, сабмит

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Предсказываем вероятность 12 находок на исследование (StudyInstanceUID) по МРТ колена: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture | страница data-description, страница Evaluation | первоисточник | постановка, единица предсказания |
| Метрика: среднее AUC ROC по 12 таргетам с равными весами (macro AUC), формула `1/12 * sum AUC_i` | страница Evaluation | первоисточник, код метрики не видели | важен только порядок внутри колонки, калибровка не важна |
| Про официальный код метрики, про поведение при таргете без позитивов, про веса классов страница ничего не говорит | страница Evaluation (отсутствие) | нет | искать на ф
... (обрезано, всего 10063 символов)
````

### validation_engineer, сообщение 3

````
Дочитаю остаток RECON.md: там раздел про публичные ноутбуки и список пробелов, в нём могут быть упоминания валидаторов метрики в чужом коде.

<tool name="read_file">{"path": "notes/RECON.md", "offset": 10000}</tool>
````

Результат read_file:

````
в с сортировкой scoreDescending; сами скоры API не вернул | kaggle_kernels | порядок виден, скоры - нет | - |
| Скоры, заявленные в НАЗВАНИЯХ: 0.942, 0.943, "0943+", "public0946", "speedy947" | названия ноутбуков | нет, это заявления авторов | по заявлениям, публичные ноутбуки на 0.009-0.019 ниже топ-20 (0.956-0.961) |
| Первый по сортировке - `pjmathematician/rsna-knee-d4-blend` (54 голоса, запуск 28.09); в его шапке заявлено "Public LB: 0.943" | kaggle_kernel_source, markdown | нет; шапка может быть унаследована от форка-предка, а сортировка ставит его выше ноутбуков с 0.946/0.947 в названиях | реальный скор этого ноутбука не известен |
| Заявленный состав пайплайна (из markdown-шапки, код НЕ прочитан - 6000 из 245840 символов): общий замороженный префикс DINOv2 (6 блоков) + 20 "tails"; A5 attention pooling, 5 фолдов; энкодер RadImageNet; 4 "Raptor views"; "4-way CoAtNet consensus" (Residual + D4 + Global96 + Repair-v1 по 25%); ранговый бленд "60% Raptor + 40% CoAt"; инференс на 2xT4 "< 30 минут" | kaggle_kernel_source, markdown | нет | какие компоненты реально работают в коде - не проверено |
| Заявленная эволюция публичных пайплайнов: Raptor Baseline 0.924 (~9 ч), DINOsaur Blend 0.941 (~4.5 ч), Speedy Raptors v7 0.942 (~1.5 ч), текущая 0.943 (< 30 мин) | там же | нет | - |
| Большинство ноутбуков в списке по названиям - форки одной линии: `mattiaangeli/bend-the-knee-to-the-dinosaurs` (288 голосов, 14.09), `mattiaangeli/bend-the-knee-to-speedy-raptors-the-original` (192), 
... (обрезано, всего 3951 символов)
````

### validation_engineer, сообщение 4

````
Порт пишу так, чтобы кроме скора он отдавал счётчики пар по каждому таргету и вклад каждого исследования: по ним потом считаются шум и цена рычагов. Сначала сам модуль, затем сверка с независимым перебором пар.

<tool name="write_file" path="scratch/knee_metric.py">
"""Локальный порт метрики RSNA Knee: macro AUC ROC по таргетам с равными весами.

ВАЖНО: официальный код метрики не найден (см. notes/RECON.md). Порт написан по формуле
со страницы Evaluation (1/12 * sum AUC_i). Все, что касается обертки грейдера
(константная колонка, таргет без позитивов, NaN, выравнивание по ID), - предположения.

Зависимости: numpy, pandas. Счет точный, в целых числах пар.

Слагаемые по таргету: n_pos, n_neg, conc (позитив строго выше негатива), disc, tied.
  AUC = (conc + 0.5 * tied) / (n_pos * n_neg)
Слагаемые по единице (исследованию) - placement values:
  для позитива: доля негативов ниже него (+0.5 за равных),
  для негатива: доля позитивов выше него (+0.5 за равных).
  Среднее по позитивам = среднее по негативам = AUC таргета.
"""
import numpy as np
import pandas as pd

ID_COL = "StudyInstanceUID"


def _groups(y, s):
    y = np.asarray(y)
    s = np.asarray(s, dtype=np.float64)
    if y.shape != s.shape:
        raise ValueError("y and s shapes differ")
    if not np.isfinite(s).all():
        raise ValueError("non-finite scores")
    if not np.isin(y, (0, 1)).all():
        raise ValueError("labels must be 0/1")
    uniq, inv = np.unique(s, return_inverse=True)
    inv = np.asarray(inv).ravel()
    pos_g = np.bincount(inv, weights=(y == 1), minlength=len(uniq)).round().astype(np.int64)
    neg_g = np.bincount(inv, weights=(y == 0), minlength=len(uniq)).round().astype(np.int64)
    return pos_g, neg_g, inv


def auc_counts(y, s):
    """Счетчики одного таргета. auc = nan, если нет позитивов или нет негативов."""
    pos_g, neg_g, _ = _groups(y, s)
    n_pos, n_neg = int(pos_g.sum()), int(neg_g.sum())
    neg_below = np.cumsum(neg_g) - neg_g
    conc = int((pos_g * neg_below).sum())
    tied = int((pos_g * neg_g).sum())
    total = n_pos * n_neg
    disc = total - conc - tied
    auc = (conc + 0.5 * tied) / total if total > 0 else float("nan")
    return dict(n_pos=n_pos, n_neg=n_neg, conc=conc, disc=disc, tied=tied, auc=auc)


def placements(y, s):
    """Вклад каждой единицы в AUC таргета (nan, если AUC не определен)."""
    y = np.asarray(y)
    pos_g, neg_g, inv = _groups(y, s)
    n_pos, n_neg = int(pos_g.sum()), int(neg_g.sum())
    out = np.full(len(y), np.nan)
    if n_pos == 0 or n_neg == 0:
        return out
    neg_below = np.cumsum(neg_g) - neg_g
    pos_above = n_pos - np.cumsum(pos_g)
    v_pos = (neg_below + 0.5 * neg_g) / n_neg
    v_neg = (pos_above + 0.5 * pos_g) / n_pos
    is_pos = y == 1
    out[is_pos] = v_pos[inv[is_pos]]
    out[~is_pos] = v_neg[inv[~is_pos]]
    return out


def validate_submission(submission, ids, targets, id_col=ID_COL):
    """Список проблем формата. Пустой список = можно считать."""
    problems = []
    cols = list(submission.columns)
    if id_col not in cols:
        return ["no id column %r" % id_col]
    missing = [t for t in targets if t not in cols]
    extra = [c for c in cols if c != id_col and c not in targets]
    if missing:
        problems.append("missing target columns: %r" % missing)
    if extra:
        problems.append("extra columns: %r" % extra)
    sid = submission[id_col]
    if sid.duplicated().any():
        problems.append("duplicated ids: %d" % int(sid.duplicated().sum()))
    ids = pd.Index(ids)
    n_missing = int((~ids.isin(sid)).sum())
    n_extra = int((~sid.isin(ids)).sum())
    if n_missing:
        problems.append("ids missing in submission: %d" % n_missing)
    if n_extra:
        problems.append("unknown ids in submission: %d" % n_extra)
    for t in targets:
        if t not in cols:
            continue
        col = pd.to_numeric(submission[t], errors="coerce")
        bad = int((~np.isfinite(col.to_numpy(dtype=np.float64))).sum())
        if bad:
            problems.append("non-finite or non-numeric values in %r: %d" % (t, bad))
    return problems


def score(solution, submission, id_col=ID_COL, undefined="raise"):
    """Macro AUC. Возвращает (скор, таблица счетчиков по таргетам).

    solution: id + таргеты, метки 0/1, NaN = единица не размечена по этому таргету
              (маскируется по таргету отдельно).
    undefined: что делать с таргетом без позитивов или без негативов:
       'raise' - ошибка; 'skip' - не входит в среднее; 'half' - входит как 0.5.
       Как поступает грейдер - НЕ известно.
    Порядок строк и порядок колонок сабмита не влияет: выравнивание по id и по имени.
    """
    if undefined not in ("raise", "skip", "half"):
        raise ValueError("bad undefined mode")
    targets = [c for c in solution.columns if c != id_col]
    if solution[id_col].duplicated().any():
        raise ValueError("duplicated ids in solution")
    problems = validate_submission(submission, solution[id_col], targets, id_col)
    if problems:
        raise ValueError("; ".join(problems))
    sub = submission.set_index(id_col).loc[solution[id_col].to_numpy(), targets]
    rows = []
    for t in targets:
        yt = solution[t].to_numpy(dtype=np.float64)
        m = ~np.isnan(yt)
        c = auc_counts(yt[m].astype(np.int64), sub[t].to_numpy(dtype=np.float64)[m])
        c["target"] = t
        c["defined"] = c["n_pos"] > 0 and c["n_neg"] > 0
        rows.append(c)
    tab = pd.DataFrame(rows).set_index("target")
    if not tab["defined"].all():
        if undefined == "raise":
            raise ValueError("AUC undefined for: %r" % list(tab.index[~tab["defined"]]))
        if undefined == "half":
            tab.loc[~tab["defined"], "auc"] = 0.5
    vals = tab["auc"].dropna()
    macro = float(vals.mean()) if len(vals) else float("nan")
    return macro, tab


def macro_auc_arrays(Y, S, undefined="skip"):
    """Быстрый вариант для бутстрапа. Y (n,k) с NaN, S (n,k). -> (macro, aucs[k])."""
    Y = np.asarray(Y, dtype=np.float64)
    S = np.asarray(S, dtype=np.float64)
    k = Y.shape[1]
    aucs = np.full(k, np.nan)
    for j in range(k):
        m = ~np.isnan(Y[:, j])
        y = Y[m, j]
        n_pos = int((y == 1).sum())
        n_neg = int((y == 0).sum())
        if n_pos == 0 or n_neg == 0:
            if undefined == "half":
                aucs[j] = 0.5
            continue
        s = S[m, j]
        order = np.argsort(s, kind="mergesort")
        ss = s[order]
        # средние ранги с учетом равных
        starts = np.r_[True, ss[1:] != ss[:-1]]
        gid = np.cumsum(starts) - 1
        cnt = np.bincount(gid)
        first = np.cumsum(cnt) - cnt
        avg_rank = first + (cnt + 1) / 2.0
        r = np.empty(len(s))
        r[order] = avg_rank[gid]
        aucs[j] = (r[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    ok = ~np.isnan(aucs)
    macro = float(aucs[ok].mean()) if ok.any() else float("nan")
    return macro, aucs


def bootstrap_units(Y, S, S2=None, n_boot=2000, seed=0, undefined="skip"):
    """Бутстрап по единицам (строкам). Возвращает dict: macro (n_boot,),
    n_defined (n_boot,) - сколько таргетов было определено в реплике,
    diff (n_boot,) = macro(S2) - macro(S) на тех же репликах, если дан S2."""
    Y = np.asarray(Y, dtype=np.float64)
    S = np.asarray(S, dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = Y.shape[0]
    out = dict(macro=np.empty(n_boot), n_defined=np.empty(n_boot, dtype=int))
    if S2 is not None:
        S2 = np.asarray(S2, dtype=np.float64)
        out["diff"] = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        m, a = macro_auc_arrays(Y[idx], S[idx], undefined)
        out["macro"][b] = m
        out["n_defined"][b] = int((~np.isnan(a)).sum())
        if S2 is not None:
            m2, _ = macro_auc_arrays(Y[idx], S2[idx], undefined)
            out["diff"][b] = m2 - m
    return out
</tool>
````

Результат write_file:

````
Файл scratch/knee_metric.py записан
````

### validation_engineer, сообщение 5

````
Порт записан. Теперь сверка: независимый перебор всех пар, `scipy` и `sklearn` (если он есть) на семействах испорченных ответов, плюс ручные случаи на границах и проверки формата. Скрипт сохраняю в `scratch/`, чтобы его можно было перезапускать.

<tool name="run_python">
code = r'''
"""Сверка порта scratch/knee_metric.py с независимыми реализациями.
Эталоны: (1) перебор всех пар позитив-негатив, (2) scipy mannwhitneyu, (3) sklearn roc_auc_score, если установлен.
Официального кода метрики нет - это сверка с формулой, а не с грейдером."""
import sys, io, warnings
import numpy as np, pandas as pd
sys.path.insert(0, "scratch")
import knee_metric as km
from scipy.stats import mannwhitneyu, rankdata
try:
    import sklearn
    from sklearn.metrics import roc_auc_score
    HAVE_SK = True
except Exception as e:
    HAVE_SK = False

TARGETS = ["ACL", "MCL", "Medial Meniscus", "Lateral Meniscus", "Medial OA", "Lateral OA",
           "PF OA", "Effusion", "Synovitis", "Baker's", "Contusion", "Fracture"]
POS57 = np.array([22, 9, 26, 22, 13, 9, 22, 35, 26, 13, 18, 18])  # оценка разведчика, +-2

def brute(y, s):
    p = s[y == 1]; n = s[y == 0]
    d = p[:, None] - n[None, :]
    return int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum())

def make(n, rng, sep=1.5):
    Y = (rng.random((n, 12)) < POS57 / 57.0).astype(float)
    for j in range(12):
        if Y[:, j].sum() == 0: Y[rng.integers(n), j] = 1
        if Y[:, j].sum() == n: Y[rng.integers(n), j] = 0
    S = 1 / (1 + np.exp(-(rng.normal(size=(n, 12)) + sep * Y)))
    return Y, S

def csv_rt(S, fmt=None):
    buf = io.StringIO(); pd.DataFrame(S).to_csv(buf, index=False, float_format=fmt); buf.seek(0)
    return pd.read_csv(buf).to_numpy(dtype=np.float64)

def fam_swap(S, Y, rng):
    S = S.copy(); i, j = rng.choice(len(S), 2, replace=False); S[[i, j]] = S[[j, i]]; return S
def fam_dup(S, Y, rng):
    S = S.copy(); h = len(S) // 2; S[:h] = S[h:2 * h]; return S
def fam_onecol(S, Y, rng):
    S = S.copy(); S[:, rng.integers(12)] = 0.5; return S

FAMILIES = {
    "identity": lambda S, Y, r: S,
    "noise": lambda S, Y, r: S + r.normal(0, 0.2, S.shape),
    "monotone_cube": lambda S, Y, r: S ** 3,
    "rank_transform": lambda S, Y, r: rankdata(S, axis=0) / len(S),
    "round1": lambda S, Y, r: np.round(S, 1),
    "round2": lambda S, Y, r: np.round(S, 2),
    "round3": lambda S, Y, r: np.round(S, 3),
    "binarize": lambda S, Y, r: (S > 0.5).astype(float),
    "constant_all": lambda S, Y, r: np.full_like(S, 0.5),
    "constant_one_col": fam_onecol,
    "invert": lambda S, Y, r: 1 - S,
    "shuffle_rows": lambda S, Y, r: S[r.permutation(len(S))],
    "dup_values": fam_dup,
    "float32": lambda S, Y, r: S.astype(np.float32).astype(np.float64),
    "scale_1e12": lambda S, Y, r: S * 1e12,
    "scale_1e-300": lambda S, Y, r: S * 1e-300,
    "shift_negative": lambda S, Y, r: S - 10,
    "perfect": lambda S, Y, r: Y + r.uniform(0, 0.1, S.shape),
    "swap_two_rows": fam_swap,
    "clip": lambda S, Y, r: np.clip(S, 0.2, 0.8),
    "csv_default": lambda S, Y, r: csv_rt(S),
    "csv_4dp": lambda S, Y, r: csv_rt(S, "%.4f"),
}
INVARIANT = ["monotone_cube", "rank_transform", "scale_1e12", "scale_1e-300", "shift_negative", "csv_default"]

rng = np.random.default_rng(20260930)
n_cases = n_tc = 0
bad = dict(counts=0, total=0, mw=0, sk=0, place=0, fast=0, invariance=0)
inv_detail = {}
for n in (57, 300, 1300):
    for rep in range(2):
        Y, S0 = make(n, rng)
        base = [km.auc_counts(Y[:, j].astype(int), S0[:, j]) for j in range(12)]
        for name, f in FAMILIES.items():
            S = f(S0, Y, rng); n_cases += 1
            fast_macro, fast_aucs = km.macro_auc_arrays(Y, S)
            for j in range(12):
                y = Y[:, j].astype(int); s = S[:, j]; n_tc += 1
                c = km.auc_counts(y, s); b = brute(y, s)
                if (c["conc"], c["disc"], c["tied"]) != b: bad["counts"] += 1
                if sum(b) != c["n_pos"] * c["n_neg"]: bad["total"] += 1
                u = mannwhitneyu(s[y == 1], s[y == 0], method="asymptotic").statistic / (c["n_pos"] * c["n_neg"])
                if abs(u - c["auc"]) > 1e-12: bad["mw"] += 1
                if HAVE_SK and abs(roc_auc_score(y, s) - c["auc"]) > 1e-12: bad["sk"] += 1
                pl = km.placements(y, s)
                if abs(pl[y == 1].mean() - c["auc"]) > 1e-12 or abs(pl[y == 0].mean() - c["auc"]) > 1e-12: bad["place"] += 1
                if abs(fast_aucs[j] - c["auc"]) > 1e-12: bad["fast"] += 1
                if name in INVARIANT and (c["conc"], c["tied"]) != (base[j]["conc"], base[j]["tied"]):
                    bad["invariance"] += 1; inv_detail[name] = inv_detail.get(name, 0) + 1
print("sklearn:", sklearn.__version__ if HAVE_SK else "НЕ установлен")
print("случаев (матриц):", n_cases, " таргет-случаев:", n_tc, " семейств:", len(FAMILIES))
print("расхождения:", bad, inv_detail)

# --- ручные случаи на границах ---
def a(y, s): return km.auc_counts(np.array(y), np.array(s, dtype=float))["auc"]
manual = [
    ("классика 0.75", a([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 0.75),
    ("идеально", a([0, 0, 1, 1], [0.1, 0.2, 0.3, 0.4]), 1.0),
    ("наоборот", a([0, 0, 1, 1], [0.4, 0.3, 0.2, 0.1]), 0.0),
    ("все равны", a([0, 0, 1, 1], [0.5] * 4), 0.5),
    ("позитив на eps выше", a([0, 1], [0.5, np.nextafter(0.5, 1)]), 1.0),
    ("ровно равны", a([0, 1], [0.5, 0.5]), 0.5),
    ("позитив на eps ниже", a([0, 1], [0.5, np.nextafter(0.5, 0)]), 0.0),
    ("одна ничья из двух пар", a([0, 1, 1], [0.5, 0.5, 0.7]), 0.75),
    ("1 позитив из 5, ранг 3", a([0, 0, 1, 0, 0], [1, 2, 3, 4, 5]), 0.5),
]
print("ручные:", [(k, got, exp, "OK" if abs(got - exp) < 1e-15 else "FAIL") for k, got, exp in manual])

# --- уровень таблиц: выравнивание, формат, маски, неопределенный таргет ---
Y, S = make(57, rng)
ids = ["1.2.%d" % i for i in range(57)]
sol = pd.DataFrame(Y, columns=TARGETS); sol.insert(0, km.ID_COL, ids)
sub = pd.DataFrame(S, columns=TARGETS); sub.insert(0, km.ID_COL, ids)
m0, tab = km.score(sol, sub)
ref = np.mean([(lambda b: (b[0] + 0.5 * b[2]) / sum(b))(brute(Y[:, j].astype(int), S[:, j])) for j in range(12)])
res = {"score==brute": abs(m0 - ref) < 1e-15}
res["перестановка строк"] = km.score(sol, sub.sample(frac=1, random_state=1))[0] == m0
res["перестановка колонок"] = km.score(sol, sub[[km.ID_COL] + TARGETS[::-1]])[0] == m0
def raises(df):
    try: km.score(sol, df); return False
    except ValueError: return True
res["дубль id -> ошибка"] = raises(pd.concat([sub, sub.iloc[:1]]))
res["нет строки -> ошибка"] = raises(sub.iloc[1:])
res["лишний id -> ошибка"] = raises(pd.concat([sub, sub.iloc[:1].assign(**{km.ID_COL: "zzz"})]))
res["нет колонки -> ошибка"] = raises(sub.drop(columns=["ACL"]))
res["лишняя колонка -> ошибка"] = raises(sub.assign(extra=1.0))
s_nan = sub.copy(); s_nan.loc[3, "MCL"] = np.nan; res["NaN в скоре -> ошибка"] = raises(s_nan)
s_inf = sub.copy(); s_inf.loc[3, "MCL"] = np.inf; res["inf в скоре -> ошибка"] = raises(s_inf)
s_str = sub.copy(); s_str["MCL"] = s_str["MCL"].astype(object); s_str.loc[3, "MCL"] = "abc"; res["строка в скоре -> ошибка"] = raises(s_str)
# маска NaN в разметке по таргету отдельно
Ym = Y.copy(); mask = rng.random(Ym.shape) < 0.3; Ym[mask] = np.nan
solm = pd.DataFrame(Ym, columns=TARGETS); solm.insert(0, km.ID_COL, ids)
mm, tabm = km.score(solm, sub, undefined="skip")
refm = []
for j in range(12):
    k = ~mask[:, j]; b = brute(Y[k, j].astype(int), S[k, j]); refm.append((b[0] + 0.5 * b[2]) / sum(b))
res["маска NaN в разметке == brute"] = abs(mm - np.mean(refm)) < 1e-15
# таргет без позитивов
Yz = Y.copy(); Yz[:, 1] = 0
solz = pd.DataFrame(Yz, columns=TARGETS); solz.insert(0, km.ID_COL, ids)
try: km.score(solz, sub); res["нет позитивов, raise"] = False
except ValueError: res["нет позитивов, raise"] = True
sk_, tk = km.score(solz, sub, undefined="skip"); hf_, th = km.score(solz, sub, undefined="half")
others = tab["auc"].drop("MCL").mean()
res["skip = среднее по 11"] = abs(sk_ - others) < 1e-15
res["half = (11*ср + 0.5)/12"] = abs(hf_ - (11 * others + 0.5) / 12) < 1e-15
print("таблицы:", res)
print("разница skip vs half на этом примере: %.4f" % (sk_ - hf_))
if HAVE_SK:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try: print("sklearn на таргете без позитивов:", roc_auc_score(Yz[:, 1].astype(int), S[:, 1]), [str(x.message)[:80] for x in w])
        except Exception as e: print("sklearn на таргете без позитивов: исключение", type(e).__name__, str(e)[:100])
        try: print("sklearn average=macro на матрице с таким таргетом:", roc_auc_score(Yz.astype(int), S, average="macro"))
        except Exception as e: print("sklearn macro на матрице: исключение", type(e).__name__, str(e)[:100])
        try: print("sklearn с NaN в скоре:", roc_auc_score(Y[:, 0].astype(int), np.where(np.arange(57) == 3, np.nan, S[:, 0])))
        except Exception as e: print("sklearn с NaN в скоре: исключение", type(e).__name__, str(e)[:100])
    print("sklearn macro по матрице == порт:", abs(roc_auc_score(Y.astype(int), S, average="macro") - m0) < 1e-12)
'''
import os
os.makedirs("scratch", exist_ok=True)
open("scratch/test_knee_metric.py", "w").write(code)
exec(compile(code, "scratch/test_knee_metric.py", "exec"))
</tool>
````

Результат run_python:

````
sklearn: НЕ установлен
случаев (матриц): 132  таргет-случаев: 1584  семейств: 22
расхождения: {'counts': 0, 'total': 0, 'mw': 0, 'sk': 0, 'place': 0, 'fast': 0, 'invariance': 0} {}
ручные: [('классика 0.75', 0.75, 0.75, 'OK'), ('идеально', 1.0, 1.0, 'OK'), ('наоборот', 0.0, 0.0, 'OK'), ('все равны', 0.5, 0.5, 'OK'), ('позитив на eps выше', 1.0, 1.0, 'OK'), ('ровно равны', 0.5, 0.5, 'OK'), ('позитив на eps ниже', 0.0, 0.0, 'OK'), ('одна ничья из двух пар', 0.75, 0.75, 'OK'), ('1 позитив из 5, ранг 3', 0.5, 0.5, 'OK')]
таблицы: {'score==brute': np.True_, 'перестановка строк': True, 'перестановка колонок': True, 'дубль id -> ошибка': True, 'нет строки -> ошибка': True, 'лишний id -> ошибка': True, 'нет колонки -> ошибка': True, 'лишняя колонка -> ошибка': True, 'NaN в скоре -> ошибка': True, 'inf в скоре -> ошибка': True, 'строка в скоре -> ошибка': True, 'маска NaN в разметке == brute': np.True_, 'нет позитивов, raise': True, 'skip = среднее по 11': np.True_, 'half = (11*ср + 0.5)/12': np.True_}
разница skip vs half на этом примере: 0.0313
````

### validation_engineer, сообщение 6

````
Порт сошёлся с перебором пар и `scipy` на 1584 таргет-случаях без расхождений (`sklearn` в окружении нет). Теперь считаю цену рычагов в единицах скора на симуляции: шум macro AUC на 57 размеченных и на паблике разных размеров, цену одного события в редком классе, цену округления и долю фолдов с неопределённым таргетом.

<tool name="run_python">
code = r'''
"""Цена рычагов и шум macro AUC. Симуляция: бинормальная модель, истинный AUC каждого таргета 0.95.
Предположения (НЕ факты): распространенность в тесте, доля паблика, корреляция двух моделей, независимость таргетов."""
import sys, numpy as np
sys.path.insert(0, "scratch")
import knee_metric as km
from scipy.stats import norm
POS57 = np.array([22, 9, 26, 22, 13, 9, 22, 35, 26, 13, 18, 18])
NAMES = ["ACL","MCL","MedMen","LatMen","MedOA","LatOA","PFOA","Effusion","Synovitis","Bakers","Contusion","Fracture"]
D = np.sqrt(2) * norm.ppf(0.95)
rng = np.random.default_rng(7)

def draw_Y(n, prev, fixed=False):
    if fixed:
        Y = np.zeros((n, 12))
        for j in range(12): Y[rng.permutation(n)[:POS57[j]], j] = 1
        return Y
    return (rng.random((n, 12)) < prev).astype(float)

def mc(n, prev, reps=1500, fixed=False, rhos=(0.9, 0.97)):
    mac = np.empty(reps); ndef = np.empty(reps); rare = np.empty(reps)
    diffs = {r: np.empty(reps) for r in rhos}
    for b in range(reps):
        Y = draw_Y(n, prev, fixed); Z = rng.normal(size=(n, 12)); S = Z + D * Y
        m, a = km.macro_auc_arrays(Y, S); mac[b] = m; ndef[b] = (~np.isnan(a)).sum(); rare[b] = a[1]
        for r in rhos:
            S2 = r * Z + np.sqrt(1 - r * r) * rng.normal(size=(n, 12)) + D * Y
            diffs[r][b] = km.macro_auc_arrays(Y, S2)[0] - m
    return mac, ndef, rare, diffs

print("=== 1. Шум macro AUC при истинном AUC 0.95 по каждому таргету ===")
print("n | распространенность | SD macro | SD одного редкого таргета (MCL) | SD парной разницы rho=0.9 / 0.97 | доля реплик с неопределенным таргетом")
prev_tr = POS57 / 57.0
for label, n, prev, fixed in [
    ("57 размеченных, фикс. счетчики", 57, prev_tr, True),
    ("n=260 (20% от 1300), как в размеченном трейне", 260, prev_tr, False),
    ("n=390 (30%), как в размеченном трейне", 390, prev_tr, False),
    ("n=650 (50%), как в размеченном трейне", 650, prev_tr, False),
    ("n=1300 (весь тест), как в размеченном трейне", 1300, prev_tr, False),
    ("n=260, втрое реже", 260, prev_tr / 3, False),
    ("n=390, втрое реже", 390, prev_tr / 3, False),
    ("n=650, втрое реже", 650, prev_tr / 3, False),
    ("n=1300, втрое реже", 1300, prev_tr / 3, False),
    ("n=390, все таргеты 3%", 390, np.full(12, 0.03), False),
]:
    mac, ndef, rare, diffs = mc(n, prev, fixed=fixed)
    print("%-48s SD=%.4f  SD_MCL=%.4f  SDdiff=%.4f / %.4f  undefined=%.3f  mean=%.4f" % (
        label, np.nanstd(mac), np.nanstd(rare), np.nanstd(diffs[0.9]), np.nanstd(diffs[0.97]), (ndef < 12).mean(), np.nanmean(mac)))

print()
print("=== 2. Цена одной пары и одного события на 57 размеченных (аналитически) ===")
print("таргет n_pos n_neg | одна перевернутая пара в macro | один позитив с первого места на последнее в macro")
for nm, p in zip(NAMES, POS57):
    print("%-10s %2d %2d | %.5f | %.4f" % (nm, p, 57 - p, 1 / (p * (57 - p)) / 12, 1 / p / 12))

print()
print("=== 3. 5 фолдов на 57 единицах: неопределенные таргеты и способ усреднения ===")
reps = 2000; any_undef = 0; n_undef = []; pooled = []; foldmean_skip = []; foldmean_half = []
for b in range(reps):
    Y = draw_Y(57, None, fixed=True); S = rng.normal(size=(57, 12)) + D * Y
    perm = rng.permutation(57); folds = np.array_split(perm, 5)
    u = 0; fs = []; fh = []
    for f in folds:
        m, a = km.macro_auc_arrays(Y[f], S[f]); u += int(np.isnan(a).sum()); fs.append(m)
        fh.append(km.macro_auc_arrays(Y[f], S[f], undefined="half")[0])
    any_undef += u > 0; n_undef.append(u)
    pooled.append(km.macro_auc_arrays(Y, S)[0]); foldmean_skip.append(np.mean(fs)); foldmean_half.append(np.mean(fh))
print("случайные фолды: доля разбиений хотя бы с одним неопределенным (фолд, таргет): %.3f; в среднем таких пар из 60: %.2f" % (any_undef / reps, np.mean(n_undef)))
print("пул OOF: mean=%.4f SD=%.4f | среднее по фолдам (skip): mean=%.4f SD=%.4f | среднее по фолдам (half): mean=%.4f SD=%.4f" % (
    np.mean(pooled), np.std(pooled), np.mean(foldmean_skip), np.std(foldmean_skip), np.mean(foldmean_half), np.std(foldmean_half)))

print()
print("=== 4. Цена округления и типа (n=1300, распространенность как в размеченном трейне, 200 реплик) ===")
def sig(x): return 1 / (1 + np.exp(-x))
res = {}
for b in range(200):
    Y = draw_Y(1300, prev_tr); L = rng.normal(size=(1300, 12)) + D * Y - D / 2
    for kind, P in (("мягкие sigmoid(x)", sig(L)), ("насыщенные sigmoid(6x)", sig(6 * L))):
        m0 = km.macro_auc_arrays(Y, P)[0]
        for nm, Q in (("1dp", np.round(P, 1)), ("2dp", np.round(P, 2)), ("3dp", np.round(P, 3)), ("4dp", np.round(P, 4)),
                      ("6dp", np.round(P, 6)), ("float32", P.astype(np.float32).astype(np.float64)), ("float16", P.astype(np.float16).astype(np.float64))):
            res.setdefault((kind, nm), []).append(km.macro_auc_arrays(Y, Q)[0] - m0)
for k, v in res.items():
    print("%-24s %-8s средняя дельта macro %+.5f  худшая %+.5f" % (k[0], k[1], np.mean(v), np.min(v)))

print()
print("=== 5. Быстродействие ===")
import time
Y = draw_Y(1300, prev_tr); S = rng.normal(size=(1300, 12)) + D * Y
t = time.time(); [km.macro_auc_arrays(Y, S) for _ in range(300)]; print("macro_auc_arrays n=1300: %.2f мс на вызов" % ((time.time() - t) / 300 * 1000))
Y = draw_Y(57, None, fixed=True); S = rng.normal(size=(57, 12)) + D * Y
t = time.time(); bt = km.bootstrap_units(Y, S, n_boot=1000); print("bootstrap_units n=57, 1000 реплик: %.2f с; доля реплик с неопределенным таргетом %.3f" % (time.time() - t, (bt["n_defined"] < 12).mean()))
'''
open("scratch/sim_levers.py", "w").write(code)
exec(compile(code, "scratch/sim_levers.py", "exec"))
</tool>
````

Результат run_python:

````
=== 1. Шум macro AUC при истинном AUC 0.95 по каждому таргету ===
n | распространенность | SD macro | SD одного редкого таргета (MCL) | SD парной разницы rho=0.9 / 0.97 | доля реплик с неопределенным таргетом
57 размеченных, фикс. счетчики                   SD=0.0086  SD_MCL=0.0358  SDdiff=0.0050 / 0.0031  undefined=0.000  mean=0.9497
n=260 (20% от 1300), как в размеченном трейне    SD=0.0041  SD_MCL=0.0171  SDdiff=0.0022 / 0.0012  undefined=0.000  mean=0.9499
n=390 (30%), как в размеченном трейне            SD=0.0032  SD_MCL=0.0137  SDdiff=0.0018 / 0.0010  undefined=0.000  mean=0.9502
n=650 (50%), как в размеченном трейне            SD=0.0026  SD_MCL=0.0108  SDdiff=0.0013 / 0.0008  undefined=0.000  mean=0.9500
n=1300 (весь тест), как в размеченном трейне     SD=0.0017  SD_MCL=0.0074  SDdiff=0.0010 / 0.0006  undefined=0.000  mean=0.9499
n=260, втрое реже                                SD=0.0061  SD_MCL=0.0284  SDdiff=0.0034 / 0.0019  undefined=0.000  mean=0.9497
n=390, втрое реже                                SD=0.0049  SD_MCL=0.0229  SDdiff=0.0027 / 0.0015  undefined=0.000  mean=0.9499
n=650, втрое реже                                SD=0.0037  SD_MCL=0.0171  SDdiff=0.0020 / 0.0011  undefined=0.000  mean=0.9501
n=1300, втрое реже                               SD=0.0027  SD_MCL=0.0123  SDdiff=0.0015 / 0.0008  undefined=0.000  mean=0.9499
n=390, все таргеты 3%                            SD=0.0087  SD_MCL=0.0297  SDdiff=0.0048 / 0.0027  undefined=0.000  mean=0.9499

=== 2. Цен
... (обрезано, всего 3823 символов)
````

### validation_engineer, сообщение 7

````
Записываю итог в заметку, чтобы порт, результаты сверки и список непроверенного не потерялись между шагами.

<tool name="write_file" path="notes/METRIC.md">
# METRIC: порт и сверка (2026-09-30)

Статус: официальный код метрики НЕ найден. Порт написан по формуле со страницы Evaluation
(macro AUC, 1/12 * sum AUC_i) в пересказе разведчика. Сверка - с формулой, не с грейдером.
Реальных данных в рабочей папке нет: все цифры ниже - симуляция на оценках разведчика (57 размеченных, 9-35 позитивов на класс, +-2).

## Файлы
- scratch/knee_metric.py - порт: auc_counts (n_pos, n_neg, conc, disc, tied), placements (вклад единицы),
  score (таблицы, выравнивание по id, проверка формата, режимы undefined=raise/skip/half),
  macro_auc_arrays (быстрый, 1.1 мс на n=1300), bootstrap_units (по единицам, парная разница).
- scratch/test_knee_metric.py - сверка. scratch/sim_levers.py - цены рычагов и шум.

## Сверено (расхождений 0)
- 22 семейства пертурбаций x 3 размера (57, 300, 1300) x 2 повтора = 132 матрицы, 1584 таргет-случая.
  Эталоны: перебор всех пар, scipy mannwhitneyu. Сверялись счетчики conc/disc/tied, а не только AUC.
- 9 ручных случаев на границах (eps выше / ровно / eps ниже, ничьи), 15 проверок на уровне таблиц.
- sklearn в окружении НЕ установлен: сверки с roc_auc_score не было.

## Причуды (все найдены чтением формулы и симуляцией, ни одна не проверена на грейдере)
- Важен только порядок внутри колонки; монотонные преобразования и ранги счет пар не меняют (проверено).
- Ничьи = 0.5 пары. Константная колонка = 0.5. Округление при записи создает ничьи:
  насыщенные предсказания: 4 знака -0.0003, 3 знака -0.0017, 2 знака -0.0068, float16 -0.0005; float32 и 6 знаков - 0.
- Таргет без позитивов или негативов: AUC не определен. Поведение грейдера неизвестно. skip против half = 0.031 macro за один таргет.
- 5 случайных фолдов на 57 единицах: в 84.5% разбиений есть неопределенный (фолд, таргет);
  среднее по фолдам с half смещено на -0.012. Считать по пулу OOF или стратифицировать.

## Шум (симуляция: истинный AUC 0.95 на таргет, таргеты независимы - оптимистично)
- 57 размеченных: SD macro 0.0086, SD одного редкого таргета 0.036, SD парной разницы 0.003-0.005.
- Паблик, n=260/390/650: SD 0.0041/0.0032/0.0026; если находки втрое реже: 0.0061/0.0049/0.0037.
  SD парной разницы 0.001-0.003. Доля паблика неизвестна.
- Один позитив редкого класса (9 позитивов) с первого места на последнее: -0.0093 macro.

## Не проверено
Официальный код; обертка грейдера (NaN, дубли id, порядок строк, типы); есть ли в тестовой разметке пропуски;
доля паблика; реальные счетчики размеченных; корреляция таргетов.

## Перед финалом
Повторить scratch/test_knee_metric.py на настоящих выходах пайплайна; проверить, не появился ли код метрики.
</tool>
````

Результат write_file:

````
Файл notes/METRIC.md записан
````

### validation_engineer, сообщение 8

````
# Метрика rsna-knee: порт написан и сверен с формулой, но не с грейдером

Официального кода метрики нет, данных в рабочей папке тоже нет. Поэтому порт сверен только с формулой со страницы Evaluation, а все цифры шума и цен получены симуляцией на оценках разведчика, а не на настоящем `train.csv`.

## 1. Источник истины

- **Сейчас**: формула со страницы Evaluation в пересказе разведчика, `1/12 * sum AUC_i`. Это рабочая гипотеза: саму страницу я не читал.
- **Что искать в первый день**: код метрики на странице Evaluation, в ноутбуках организаторов и на форуме. Валидаторы из публичных ноутбуков источником не считать.
- **Если код найдётся**: записать ссылку и версию, перезапустить `scratch/test_knee_metric.py` с ним как эталоном и повторить проверку перед финалом.
- **Если не найдётся**: истиной остаётся формула плюс одна пробная посылка (раздел 6).

## 2. Формула и пул

- **Внутри таргета**: AUC - доля пар «позитив, негатив», где позитив выше; ничья считается за полпары. Пары пулятся по всем исследованиям выборки.
- **Между таргетами**: простое среднее 12 AUC с равными весами. Редкий таргет весит столько же, сколько частый.
- **Следствие**: важен только порядок внутри колонки. Калибровка и сравнимость шкал между колонками не влияют.

## 3. Что установлено

**Порт**
- `scratch/knee_metric.py` зависит только от numpy и pandas.
- Он отдаёт по каждому таргету `n_pos`, `n_neg`, `conc`, `disc`, `tied` и вклад каждого исследования.
- В нём есть проверка формата сабмита и бутстрап по единицам с парной разницей.
- Скорость: 1.1 мс на вызов при n=1300; 1000 реплик бутстрапа на 57 единицах за 0.27 с.

**Сверка, расхождений 0**
- 22 семейства испорченных ответов на 3 размерах по 2 повтора: 132 матрицы, 1584 таргет-случая.
- Эталоны: перебор всех пар и `scipy.mannwhitneyu`. Сверялись счётчики, а не только итог.
- 9 ручных случаев на границах: на eps выше, ровно, на eps ниже, ничьи.
- 15 проверок на уровне таблиц: перестановка строк и колонок, дубли и пропуски id, NaN, inf, строка в скоре, маска в разметке.
- `sklearn` в окружении нет, сверки с `roc_auc_score` не было.

**Цены рычагов** (симуляция: бинормальная модель, истинный AUC 0.95 на каждом таргете, таргеты независимы)

| рычаг | цена в macro AUC |
|---|---|
| одна перевёрнутая пара на 57 размеченных | 0.0001-0.0002 |
| один позитив редкого класса (9 позитивов) с первого места на последнее | 0.0093 |
| то же для Effusion (35 позитивов) | 0.0024 |
| таргет без позитивов: «пропустить» против «засчитать 0.5» | 0.031 на примере |
| округление до 4 / 3 / 2 знаков, насыщенные предсказания | -0.0003 / -0.0017 / -0.0068 |
| округление до 2 знаков, мягкие предсказания | -0.00003 |
| float16 / float32, насыщенные предсказания | -0.0005 / 0 |

Цена округления зависит от насыщенности предсказаний; «насыщенные» здесь - мой произвольный пример `sigmoid(6x)`.

**Шум** (та же симуляция)

| выборка | SD macro | SD парной разницы двух похожих моделей |
|---|---|---|
| 57 размеченных | 0.0086 | 0.003-0.005 |
| паблик n=260 / 390 / 650, находки как в размеченном трейне | 0.0041 / 0.0032 / 0.0026 | 0.001-0.002 |
| то же, находки втрое реже | 0.0061 / 0.0049 / 0.0037 | 0.001-0.003 |

- SD одного редкого таргета на 57 размеченных - 0.036. По его AUC в одиночку решать ничего нельзя.
- Весь топ-20 паблика лежит в 0.005. При этих допущениях это 1-2 SD паблика, то есть порядок внутри топа близок к шуму.
- Разрыв публичных ноутбуков с топом (0.009-0.019) больше шума парной разницы.

**Усреднение по фолдам на 57 единицах**
- В 84.5% случайных разбиений на 5 фолдов хотя бы один таргет в каком-то фолде остаётся без позитивов.
- Среднее по фолдам с заменой такого таргета на 0.5 даёт 0.938 вместо 0.950 - смещение -0.012.
- Среднее по фолдам с пропуском не смещено, но шумнее: SD 0.0101 против 0.0086 у пула.
- Считать по пулу OOF или стратифицировать по всем 12 таргетам. Пул OOF штрафует разницу шкал между моделями фолдов; этот эффект я не моделировал.

## 4. Предположения, требующие проверки

1. Грейдер считает обычный ROC AUC с ничьёй за полпары и равными весами. Источник - только страница.
2. Константная колонка даёт 0.5, а не ошибку.
3. В паблике и привате у каждого таргета есть и позитивы, и негативы. Иначе поведение грейдера неизвестно.
4. Грейдер выравнивает строки по `StudyInstanceUID`, а не по порядку. Посылкой не проверять: держать порядок и колонки как в `sample_submission`.
5. В тестовой разметке нет пропусков по отдельным таргетам. Порт маску поддерживает, но делает ли так грейдер, неизвестно.
6. Реальный шум на размеченных выше моего: находки коррелированы (три OA, Effusion и Synovitis), а симуляция считала их независимыми.
7. Размеченных 55-60, и это одни и те же строки по всем 12 колонкам. Позитивов 9-35 на класс с погрешностью ±2.

**Правила записи сабмита**
- Не округлять: писать float с полной точностью или ранги. Преобразование в ранги счёт пар не меняет, это проверено.
- Не допускать NaN, inf и дублей id. Как на них реагирует грейдер, неизвестно; локальный порт на них падает намеренно.

## 5. Дорожки валидации

Прогонов нет, поэтому ниже условия честности, а не вердикты.

**Размеченные исследования (около 57)**
- Это единственная дорожка с настоящими метками.
- Она честна, только пока их не видела ни одна обученная компонента. Сюда входят извлекатель меток из отчётов (подбор промпта или обучение на этих метках) и публичные веса, происхождение которых неизвестно.
- Сходство с тестом не гарантировано: у Effusion позитивов больше, чем негативов, так что подвыборка похожа на обогащённую.
- Годится для разниц от 0.01-0.02 macro и выше. Разницу 0.003 она не различает.
- Если эти метки уйдут в обучение, честной дорожки не останется. Это решение нужно принять явно.

**Метки из отчётов (около 4350)**
- Единиц много, но эта дорожка измеряет согласие с извлекателем, а не с разметкой теста.
- Если тем же извлекателем размечено обучение, ошибки совпадают и цифра завышена.
- Годится для грубого ранжирования моделей. Точность извлекателя надо сначала измерить на размеченных, не настраивая его на них.

**Паблик**
- Размер неизвестен, SD по симуляции 0.003-0.006.
- Табло показывает 3 знака.

**Группировка**
- Идентификатора пациента в csv нет. 131 неуникальный отчёт может означать повторные исследования.
- Минимум - держать одинаковые отчёты в одном фолде и поискать `PatientID` в тегах DICOM.

## 6. Пробные посылки

Нужна одна: `sample_submission` (все 0.5) через ноутбук.

| результат | вывод |
|---|---|
| 0.500 | константа и ничьи считаются как в порте; заодно получаем Benchmark трека эффективности |
| ошибка | грейдер падает на константной колонке |
| другое число | веса или формула не те, что на странице |

- Та же посылка проверяет слаг, работу ноутбука на подменённом тесте и время.
- Посылка не различит «пропустить» и «засчитать 0.5» для неопределённого таргета. Это закрывается только кодом метрики или ответом организаторов.
- Формат настоящих предсказаний проверит первая боевая посылка, отдельный слот на это не нужен.
- Слоты на округление, порядок строк и NaN не тратить: они закрываются правилами записи. Поштучный замер AUC таргетов на паблике - это подгонка под паблик, а не проверка грейдера.
- Перед финалом перезапустить `scratch/test_knee_metric.py` на настоящих выходах пайплайна.

## 7. Каких фактов не хватило

- Официального кода метрики и ответов организаторов на форуме.
- Доли паблика и распространённости находок в тесте.
- Самого `train.csv`: точных счётчиков размеченных, совпадения строк по 12 колонкам, корреляции таргетов.
- Того, как отбирались размеченные исследования и есть ли в тесте пропуски в разметке.
- Происхождения публичных весов: видели ли они размеченные исследования.
- `sklearn` в окружении.

ИТОГ:
- Официального кода метрики нет. Порт `scratch/knee_metric.py` написан по формуле страницы (macro AUC, 12 таргетов, равные веса) и сверен с перебором пар и `scipy` на 1584 таргет-случаях без расхождений. Сверки с грейдером и с `sklearn` не было; заметка лежит в `notes/METRIC.md`.
- Все цифры шума - симуляция, данных в папке нет. На примерно 57 размеченных SD macro не меньше 0.0086, один позитив редкого класса стоит до 0.0093. Дорожка различает разницы от 0.01-0.02.
- SD паблика по симуляции 0.003-0.006 при неизвестной доле. Топ-20 лежит в 0.005, то есть порядок внутри него близок к шуму.
- На 57 единицах среднее по фолдам ненадёжно: в 84.5% разбиений есть таргет без позитивов, смещение до -0.012. Считать по пулу OOF или стратифицировать; сабмит не округлять (до -0.007).
- Пробная посылка нужна одна: `sample_submission` через ноутбук, ожидаем 0.500. Остальные вопросы формата закрываются правилами записи.
- Размеченные исследования остаются честной дорожкой, только пока их не видели ни извлекатель меток из отчётов, ни публичные веса. Брать ли их в обучение, надо решить явно.
- Не хватило: кода метрики, форума, доли паблика, самого `train.csv`, сведений об отборе размеченных и о происхождении публичных весов.
````

Вызовов инструментов: 7
[harness] записан файл scratch/knee_metric.py (7660 символов)
[harness] записан файл notes/METRIC.md (2594 символов)

## Диспетчер, ход 3

````
{
  "thought": "Метрика разобрана, но инженеру валидации не хватило фактов, от которых зависит схема валидации: структура train.csv по пациентам и площадкам, как отобраны размеченные исследования, на чем обучены публичные веса, правила про LLM-разметку. Сначала прицельно добираю их разведчиком, потом проектирую валидацию.",
  "plan_list": [
    "scout: прицельно закрыть пробелы, важные для валидации (профиль таблиц по пациентам/площадкам, отбор размеченных, происхождение публичных весов, правила про LLM и внешние данные, доля паблика, форум)",
    "validation_engineer: схема честной валидации под устройство теста, число независимых единиц, шум валидации и паблика",
    "strategist: очередь экспериментов и посылок на первую неделю, на что не тратить посылки; записать notes/PLAN.md",
    "finish: короткий итог пользователю"
  ],
  "action": "delegate",
  "agent_nm": "scout",
  "skill_nm_list": ["competition_recon"],
  "subtask_text": "Первая разведка соревнования rsna-knee-abnormality-detection сделана (notes/RECON.md, ответ шага 1), но остались пробелы, без которых нельзя спроектировать валидацию; они перечислены в конце ответов шагов 1 и 2. Закрой прицельно то, что получится. 1) Профиль таблиц с данными: какие есть идентификаторы пациента, площадки, сканера, языка отчета; сколько исследований на пациента; чем размеченные исследования отличаются от неразмеченных по этим полям и есть ли на страницах описание того, как их отбирали; точный баланс позитивов по 12 таргетам. 2) Что известно о тесте: площадки и пациенты относительно трейна, доля паблика. 3) Исходники публичных ноутбуков: на чем обучены используемые в них веса и датасеты, участвовали ли в обучении размеченные исследования этого соревнования, как в них получают метки из отчетов. 4) Полный текст правил про внешние данные, предобученные веса и использование LLM для разметки отчетов; квоты GPU. 5) Обсуждения на форуме о метрике, валидации и расхождении локального скора с пабликом, если к ним есть доступ. В ответе по каждому пункту укажи: подтверждено первоисточником, взято из чужих материалов или узнать не удалось и по какой причине (нет доступа, нет в данных). Допиши результаты в notes/RECON.md.",
  "context_step_list": [1, 2]
}
````

## Шаг 3: scout

Скиллы, выбранные диспетчером: competition_recon. Контекст: шаги [1, 2]

Системный промпт: 8318 символов, из них скиллы - 4238

<details><summary>системный промпт целиком</summary>

````
Ты - разведчик в команде, которая участвует в ML-соревновании на Kaggle. Твоя работа - собрать факты, на которых остальные будут строить решения: что за задача, как устроены метрика, данные, тест и публичный лидерборд, какие есть ограничения (code competition, лимит времени ноутбука, интернет, число посылок в день, число финальных сабмитов, сроки), что уже сделала команда, что видно по публичным ноутбукам и по лидерборду.

Факты берутся из рабочей папки (страницы соревнования, журнал посылок, заметки команды) и через Kaggle API, если он доступен. К каждому факту - откуда он. Отделяй то, что написано в источнике, от своих выводов. Если источники расходятся или чего-то в них нет - так и пиши, не заполняй пробелы догадками.

Ты не предлагаешь модели, не оцениваешь прогоны и не выбираешь сабмиты.

## Инструменты
- list_files: список файлов рабочей папки с размерами в символах. Аргументов нет
- read_file: прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата будет подсказка, с какого offset продолжать. Аргументы: path - путь к файлу от корня рабочей папки; offset - с какого символа читать (необязательный, по умолчанию 0); limit - сколько символов вернуть, за один вызов отдается не больше 10000 (необязательный, по умолчанию 10000)
- write_file: записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается. Атрибуты тега: path - путь к файлу от корня рабочей папки. Внутри блока - содержимое файла
- kaggle_pages: страницы соревнования через Kaggle API: список страниц или текст одной страницы, по 6000 символов за вызов. Аргументы: page - название страницы; без него вернется список страниц (необязательный); offset - с какого символа читать страницу (необязательный, по умолчанию 0)
- kaggle_files: сводка по файлам данных соревнования через Kaggle API. Аргументов нет
- kaggle_csv_profile: профиль табличного файла соревнования через Kaggle API: число строк, типы, пропуски, доли значений. Сам файл не сохраняется. Аргументы: file - имя csv-файла из списка файлов соревнования
- kaggle_kernels: публичные ноутбуки соревнования через Kaggle API. Аргументы: sort_by - сортировка: hotness | commentCount | dateCreated | dateRun | scoreAscending | scoreDescending | viewCount | voteCount (необязательный, по умолчанию voteCount); page_size - сколько ноутбуков вернуть, не больше 100 (необязательный, по умолчанию 20)
- kaggle_kernel_source: исходный код публичного ноутбука через Kaggle API, без выходов ячеек, по 6000 символов за вызов. Аргументы: ref - ссылка на ноутбук вида автор/название из kaggle_kernels; offset - с какого символа читать (необязательный, по умолчанию 0)
- kaggle_leaderboard: верх публичного лидерборда через Kaggle API: места и скоры. Аргументов нет

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{"path": "journal.md"}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше 14 вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.

=== МЕТОДИКА: competition_recon ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Разведка соревнования

От разведки нужен список фактов, от которых зависят решения, и источник у каждого. Пересказ страниц никому не нужен. Все, что команда не проверила сама, так и помечается: непроверенное.

## Что собрать

1. Паспорт. Что предсказываем и в каком формате сабмит. Метрика: формула, по каким единицам она пулится или усредняется, что округляется, какие есть штрафы и капы. Сроки: дедлайн входа, слияния команд, финальный. Сколько посылок в день и сколько финальных.
2. Ограничения исполнения. Если это code competition: лимит времени ноутбука на CPU и GPU, есть ли интернет, разрешены ли внешние данные и веса и на каких условиях, как называется файл сабмита. И лимиты платформы, про которые страницы молчат: число одновременных GPU-сессий, недельная квота GPU.
3. Устройство теста. На этом пункте потом стоит вся валидация, времени на него не жалеть. Чем тест отличается от трейна: новые группы (пациент, площадка, эмбрион, устройство), другой период, другой источник. Какой размер у скрытого теста. Какая доля теста в публичном лидерборде и сколько это независимых единиц. До скольких знаков округляется табло. Видимая часть теста - это настоящий тест или копия трейна. Доли паблика и числа знаков на страницах может не быть, тогда искать в API соревнования и на странице лидерборда.
4. Данные. Состав и размер файлов, какая часть размечена, есть ли доп. источники (тексты, метаданные), как устроены идентификаторы групп.
5. Официальный код. Репозиторий организаторов с метрикой и конвертерами и история его коммитов: патчи метрики посреди соревнования меняют смысл старых скоров.
6. Публичные решения. Топ ноутбуков по скору и по голосам: на чем обучены модели, какие сплиты, сколько идет ноутбук, какие стадии в пайплайне. Публичные веса и датасеты: что внутри и на каких данных обучено.
7. Форум. Ответы хостов про правила и метрику, найденные баги, сообщения топ-участников о том, что у них работает и что нет. Читать с комментариями, самое полезное обычно в ответах.
8. Лидерборд. Плотность верха (сколько команд делят один скор) и число посылок у команд наверху. Мало посылок при высоком скоре - признак своего пайплайна; подбор по паблику выглядит иначе, посылок там много.

## Чему не верить на слово

Скор в названии ноутбука или датасета ("0.95 LB"). Это результат отбора по публичному лидерборду тысячами людей, и на привате такие компоненты теряют больше, чем свои. К тому же скор мог быть получен до патча метрики или на эксплойте, который с тех пор закрыли.

"Валидация" внутри публичного ноутбука. Проверь, на чем обучены веса. Если на всем трейне, то любая локальная проверка на этих весах - in-sample, какой бы сплит ни стоял в коде.

Публичный ноутбук "как есть". Прежде чем на нем строить, прочитай код: бывает, что заявленный компонент молча не работает. Веса грузятся с strict=False в другую архитектуру, исключение проглатывается, функция возвращает None - ноутбук идет дальше без компонента, а в описании он есть.

Конфиг, который ноутбук выбрал на коммите. Если внутри есть перебор с валидацией на видимых данных, на скрытом реране он может выбрать другой конфиг. Тогда в логе коммита записан один конфиг, а скор дал другой.

Текст страницы про метрику и формат. Источник истины - код метрики на конкретном коммите. Чего в коде нет (обертка грейдера), проверяется пробной посылкой.

## Как записать

Таблица: утверждение - источник - проверено ли нами - на что влияет. Например:

    паблик - 25% теста, около 40 единиц | страница лидерборда | да | порог шума паблика
    публичные веса обучены на всем трейне | описание датасета | нет, читать код обучения | честность локальной валидации на этих весах
    дробные значения в сабмите допустимы | код конвертера | нет, страница требует целые | пробная посылка

Если два источника расходятся, в таблицу идут оба. Выбирать тот, что удобнее, нельзя.

И два списка отдельно от таблицы.

Первый: чего выяснить не удалось и как это можно выяснить (спросить на форуме, пробная посылка, прочитать код).

Второй: советы сильных участников про стратегию - что у них не сработало, куда они советуют вкладываться. К нему нужно возвращаться перед каждым решением закрыть линию работы. Составить такой список в первый день легко, труднее потом его открывать.
=== КОНЕЦ МЕТОДИКИ: competition_recon ===
````

</details>

Подзадача: Первая разведка соревнования rsna-knee-abnormality-detection сделана (notes/RECON.md, ответ шага 1), но остались пробелы, без которых нельзя спроектировать валидацию; они перечислены в конце ответов шагов 1 и 2. Закрой прицельно то, что получится. 1) Профиль таблиц с данными: какие есть идентификаторы пациента, площадки, сканера, языка отчета; сколько исследований на пациента; чем размеченные исследования отличаются от неразмеченных по этим полям и есть ли на страницах описание того, как их отбирали; точный баланс позитивов по 12 таргетам. 2) Что известно о тесте: площадки и пациенты относительно трейна, доля паблика. 3) Исходники публичных ноутбуков: на чем обучены используемые в них веса и датасеты, участвовали ли в обучении размеченные исследования этого соревнования, как в них получают метки из отчетов. 4) Полный текст правил про внешние данные, предобученные веса и использование LLM для разметки отчетов; квоты GPU. 5) Обсуждения на форуме о метрике, валидации и расхождении локального скора с пабликом, если к ним есть доступ. В ответе по каждому пункту укажи: подтверждено первоисточником, взято из чужих материалов или узнать не удалось и по какой причине (нет доступа, нет в данных). Допиши результаты в notes/RECON.md.

### scout, сообщение 1

````
Сначала прочитаю текущую сводку: её нужно будет дописать, а write_file перезаписывает файл целиком.

<tool name="read_file">{"path": "notes/RECON.md"}</tool>
````

Результат read_file:

````
# RECON: RSNA Knee Abnormalities Detection

Дата разведки: 2026-09-30. Источник всего ниже - Kaggle API (страницы, профили csv, лидерборд, список ноутбуков). Своих посылок у команды нет, пробными посылками ничего не проверено.

Расхождение в названии: диспетчер назвал слаг `rsna-knee-abnormality-detection`, в правилах (раздел 1.4) адрес `https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection`. API отвечал, какой слаг он использовал - не видно. При настройке посылок сверить.

## 1. Таблица фактов

Колонка "проверено" - проверено ли нами на практике (кодом, посылкой). "Первоисточник" значит: написано на странице или в файле организаторов, но не проверено посылкой.

### 1.1 Задача, метрика, сабмит

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Предсказываем вероятность 12 находок на исследование (StudyInstanceUID) по МРТ колена: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture | страница data-description, страница Evaluation | первоисточник | постановка, единица предсказания |
| Метрика: среднее AUC ROC по 12 таргетам с равными весами (macro AUC), формула `1/12 * sum AUC_i` | страница Evaluation | первоисточник, код метрики не видели | важен только порядок внутри колонки, калибровка не важна |
| Про официальный код метрики, про поведение при таргете без позитивов, про веса классов страница ничего не говорит | страница Evaluation (отсутствие) | нет | искать на ф
... (обрезано, всего 10063 символов)
````

### scout, сообщение 2

````
Дочитаю остаток сводки (раздел про ноутбуки и списки пробелов), чтобы потом перезаписать файл целиком без потерь.

<tool name="read_file">{"path": "notes/RECON.md", "offset": 10000}</tool>
````

Результат read_file:

````
в с сортировкой scoreDescending; сами скоры API не вернул | kaggle_kernels | порядок виден, скоры - нет | - |
| Скоры, заявленные в НАЗВАНИЯХ: 0.942, 0.943, "0943+", "public0946", "speedy947" | названия ноутбуков | нет, это заявления авторов | по заявлениям, публичные ноутбуки на 0.009-0.019 ниже топ-20 (0.956-0.961) |
| Первый по сортировке - `pjmathematician/rsna-knee-d4-blend` (54 голоса, запуск 28.09); в его шапке заявлено "Public LB: 0.943" | kaggle_kernel_source, markdown | нет; шапка может быть унаследована от форка-предка, а сортировка ставит его выше ноутбуков с 0.946/0.947 в названиях | реальный скор этого ноутбука не известен |
| Заявленный состав пайплайна (из markdown-шапки, код НЕ прочитан - 6000 из 245840 символов): общий замороженный префикс DINOv2 (6 блоков) + 20 "tails"; A5 attention pooling, 5 фолдов; энкодер RadImageNet; 4 "Raptor views"; "4-way CoAtNet consensus" (Residual + D4 + Global96 + Repair-v1 по 25%); ранговый бленд "60% Raptor + 40% CoAt"; инференс на 2xT4 "< 30 минут" | kaggle_kernel_source, markdown | нет | какие компоненты реально работают в коде - не проверено |
| Заявленная эволюция публичных пайплайнов: Raptor Baseline 0.924 (~9 ч), DINOsaur Blend 0.941 (~4.5 ч), Speedy Raptors v7 0.942 (~1.5 ч), текущая 0.943 (< 30 мин) | там же | нет | - |
| Большинство ноутбуков в списке по названиям - форки одной линии: `mattiaangeli/bend-the-knee-to-the-dinosaurs` (288 голосов, 14.09), `mattiaangeli/bend-the-knee-to-speedy-raptors-the-original` (192), 
... (обрезано, всего 3951 символов)
````

### scout, сообщение 3

````
Сводка прочитана целиком. Начну с списка страниц соревнования: нужно увидеть, как называется страница правил и есть ли страницы, которые в первый раз не читались (Description, Prizes), где могут быть сведения об отборе размеченных исследований и о тесте.

<tool name="kaggle_pages">{}</tool>
````

Результат kaggle_pages:

````
Страницы соревнования: rules, Description, Evaluation, Timeline, data-description, Prizes, Code Requirements, abstract, Efficiency Prize Evaluation, Acknowledgements
````

### scout, сообщение 4

````
Страница правил называется `rules`. Дочитываю её с того места, где остановилась первая разведка: нужны разделы про внешние данные, предобученные веса и автоматические инструменты разметки.

<tool name="kaggle_pages">{"page": "rules", "offset": 6000}</tool>
````

Результат kaggle_pages:

````
y commercially available software that you used to generate your Submission that is not owned by you, but that can be procured by the Competition Sponsor without undue expense, you do not need to grant the license in the preceding Section for that software. </h6>

4. In the event that input data or pretrained models with an incompatible license are used to generate your winning solution, you do not need to grant an open source license in the preceding Section for that data and/or model(s). </h6>

b. You may be required by the Sponsor to provide a detailed description of how the winning Submission was generated, to the Competition Sponsor’s specifications, as outlined in Section 2.8, Winner’s Obligations. This may include a detailed description of methodology, where one must be able to reproduce the approach by reading the description, and includes a detailed explanation of the architecture, preprocessing, loss function, training details, hyper-parameters, etc. The description should also include a link to a code repository with complete and detailed instructions so that the results obtained can be reproduced. After your solution has been validated, you may be asked to discuss your results via a recorded call or panel call with the competition sponsors, which call may take the form of a panel with the attendance of other winners.
</h7>
 
####6. EXTERNAL DATA AND TOOLS

a. You may use data other than the Competition Data (“External Data”) to develop and test your Submissions. H
... (обрезано, всего 6066 символов)
````

### scout, сообщение 5

````
Раздел 2.6 правил про внешние данные и инструменты получен целиком. Теперь профиль `train.csv`: нужны точный список колонок (есть ли идентификаторы пациента, площадки, языка) и баланс по 12 таргетам.

<tool name="kaggle_csv_profile">{"file": "train.csv"}</tool>
````

Результат kaggle_csv_profile:

````
train.csv: строк 4407, колонок 14
колонка                     тип       уникальных  пропуски  значения
StudyInstanceUID            str       4407        0.000     длина строк: медиана 64
Report                      str       4276        0.000     длина строк: медиана 977
ACL                         float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
MCL                         float64   2           0.987     nan: 0.987, 0.0: 0.011, 1.0: 0.002
Medial Meniscus             float64   2           0.987     nan: 0.987, 0.0: 0.007, 1.0: 0.006
Lateral Meniscus            float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
Medial OA                   float64   2           0.987     nan: 0.987, 0.0: 0.010, 1.0: 0.003
Lateral OA                  float64   2           0.987     nan: 0.987, 0.0: 0.011, 1.0: 0.002
PF OA                       float64   2           0.987     nan: 0.987, 0.0: 0.008, 1.0: 0.005
Effusion                    float64   2           0.987     nan: 0.987, 1.0: 0.008, 0.0: 0.005
Synovitis                   float64   2           0.987     nan: 0.987, 0.0: 0.007, 1.0: 0.006
Baker's                     float64   2           0.987     nan: 0.987, 0.0: 0.010, 1.0: 0.003
Contusion                   float64   2           0.987     nan: 0.987, 0.0: 0.009, 1.0: 0.004
Fracture                    float64   2           0.987     nan: 0.987, 0.0: 0.009, 1.0: 0.004
````

### scout, сообщение 6

````
В `train.csv` только 14 колонок: идентификаторов пациента, площадки и языка нет, баланс доступен лишь в долях, округлённых до 3 знаков. Проверю `train_series.csv`: там могут быть поля сканера, производителя или площадки.

<tool name="kaggle_csv_profile">{"file": "train_series.csv"}</tool>
````

Результат kaggle_csv_profile:

````
train_series.csv: строк 24371, колонок 5
колонка                     тип       уникальных  пропуски  значения
StudyInstanceUID            str       4407        0.000     длина строк: медиана 64
SeriesInstanceUID           str       24371       0.000     длина строк: медиана 64
Fluid_Sensitive             int64     2           0.000     1: 0.575, 0: 0.425
Fat_Suppression             int64     2           0.000     1: 0.575, 0: 0.425
Anatomical_Plane            str       3           0.000     Sagittal: 0.405, Coronal: 0.353, Axial: 0.242
````

### scout, сообщение 7

````
В csv нет ни пациента, ни площадки, ни сканера, ни языка. Перечитаю страницу data-description: там могут быть описание отбора размеченных исследований, состав площадок теста и список тегов DICOM.

<tool name="kaggle_pages">{"page": "data-description"}</tool>
````

Результат kaggle_pages:

````
## Dataset Description

This dataset contains knee MRI studies annotated for twelve common findings: ligament and meniscus injuries, three compartments of osteoarthritis, joint effusion, synovitis, Baker's cyst, bone contusion, and fracture. Each study comprises a collection of individual MRI sequences from a single scanning session formatted as DICOM series. Your task is to predict the per-study probability of each of the twelve findings.

Studies come from a diverse international mix of imaging sites and span a wide range of scanners, protocols, and populations. Only a small subset of training studies carry per-condition labels. We also provide the original text of the radiology report from which you may wish to derive the labels for the remaining studies.

## Files

**train.csv** One row per training study.

*   `StudyInstanceUID` - unique identifier for the study; matches the folder name under `train_series/`.
*   `Report` - the free-text radiology report. May be in any of several languages, depending on the reporting institution.

Twelve binary labels:
*   `ACL` - anterior cruciate ligament injury (0/1).
*   `MCL` - medial collateral ligament injury (0/1).
*   `Medial Meniscus` - medial meniscus tear (0/1).
*   `Lateral Meniscus` - lateral meniscus tear (0/1).
*   `Medial OA` - osteoarthritis of the medial tibiofemoral compartment (0/1).
*   `Lateral OA` - osteoarthritis of the lateral tibiofemoral compartment (0/1).
*   `PF OA` - patellofemoral osteoarthritis (0/1).
*  
... (обрезано, всего 3979 символов)
````

### scout, сообщение 8

````
В csv и на странице данных нет ни идентификаторов групп, ни описания отбора размеченных исследований, ни сведений о площадках теста. Перехожу к пункту 3: возьму полный список публичных ноутбуков по голосам, чтобы найти среди них ноутбуки с обучением и с извлечением меток из отчётов, а не только инференс-бленды.

<tool name="kaggle_kernels">{"sort_by": "voteCount", "page_size": 100}</tool>
````

Результат kaggle_kernels:

````
Публичные ноутбуки соревнования (ref | название | голоса | последний запуск):
pilkwang/rsna-knee-baseline-v1 | RSNA Knee baseline v1 | 647 | 2026-08-08
ryanholbrook/rsna-knee-abnormalities-efficiency-lb | RSNA Knee Abnormalities - Efficiency LB | 462 | 2026-09-29
mattiaangeli/bend-the-knee-to-the-dinosaurs | Bend the Knee to the Dinosaurs | 288 | 2026-09-14
prvsiyan/rsna-knee-read-the-report-then-the-knee | RSNA Knee: read the report, then the knee | 262 | 2026-08-11
evgendvorkin/rsna-versia-5 | RSNA_Versia_5 | 254 | 2026-09-26
mattiaangeli/bend-the-knee-to-dinov3-ensembled | Bend the Knee to DinoV3 (ensembled) | 222 | 2026-08-22
prvsiyan/head-and-shoulders-knees-and-toes | Head and shoulders, knees and toes | 201 | 2026-09-17
jiweiliu/rsna-knee-fast-2xt4-inference | RSNA Knee Fast 2xT4 Inference | 199 | 2026-09-23
mattiaangeli/bend-the-knee-to-speedy-raptors-the-original | Bend the Knee to Speedy Raptors-The Original ⭐⭐⭐⭐⭐ | 192 | 2026-09-22
maverickss26/rsna-knee-0942-restructured | rsna-knee-0942-restructured | 174 | 2026-09-20
romantamrazov/rsna-knee-dinosaur-v4 | RSNA Knee | DINOsaur V4 🦖  | 168 | 2026-09-07
dreaddevelopment/knee-mri-twelve-findings-from-a-single-model | Knee MRI: twelve findings from a single model | 157 | 2026-09-01
romanrozen/rsna-knee-data-structure-eda-baseline | RSNA Knee | Data structure, EDA, baseline🔥 | 138 | 2026-08-10
anhadmahajan06/rsna-knee-take-care-of-your-knee | RSNA Knee: Take Care Of Your Knee | 127 | 2026-09-05
romantamrazov/rsna-knee-
... (обрезано, всего 9867 символов)
````

### scout, сообщение 9

````
Список получен: в нём есть ноутбуки про извлечение меток из отчётов и отдельные ноутбуки обучения. Начну с `prvsiyan/rsna-knee-read-the-report-then-the-knee`: по названию в нём описано, как метки получают из отчётов и что делают с размеченными исследованиями.

<tool name="kaggle_kernel_source">{"ref": "prvsiyan/rsna-knee-read-the-report-then-the-knee"}</tool>
````

Результат kaggle_kernel_source:

````
# [markdown]
# Twelve findings, fifty-eight labels, four thousand reports

![Report-supervised knee MRI ensemble](attachment:rsna-knee-report-to-image-hero.jpg)

A knee MRI study here has to be given twelve probabilities — anterior cruciate and medial
collateral ligament injury, medial and lateral meniscal tear, osteoarthritis in each of
the three compartments, effusion, synovitis, Baker's cyst, bone contusion, fracture — and
the score is the unweighted mean of the twelve ROC AUCs.

The decisive fact about this dataset is not in the images. It is in `train.csv`:

| | studies | carry the twelve labels | carry a radiology report |
|---|---|---|---|
| train | 4 407 | **58** | 4 407 |
| test | — | — | **none — there is no `Report` column** |

Fifty-eight labelled studies cannot train an imaging model, and the reports that could
supply the missing four thousand are unavailable at prediction time. So the pipeline is
forced into one shape: **read the reports into targets, fit a pure imaging model against
them, and throw the text away.** Everything downstream — which slices to decode, how large
to make them, which encoder to adapt — is bounded by how well that first step is done.

This notebook is organised in the order the decisions constrain each other.

1. What the score rewards, and what that removes from the design.
2. Where the targets come from — a nine-language report reader, and the two ways to tell
   whether it works when only 58 studies can check it.
3. What the scanner r
... (обрезано, всего 6062 символов)
````

### scout, сообщение 10

````
Шапка подтверждает 58 размеченных исследований, но это слова автора ноутбука. Читаю следующий кусок того же исходника: раздел 2 должен показать, чем читают отчёты и используются ли 58 размеченных исследований при настройке извлекателя.

<tool name="kaggle_kernel_source">{"ref": "prvsiyan/rsna-knee-read-the-report-then-the-knee", "offset": 6000}</tool>
````

Результат kaggle_kernel_source:

````
vitis
head far more weakly than one that names it, and a loss that cannot express that trains
every silence as a confident negative.

### Nine languages, one lexicon

The corpus is written in nine languages across three scripts. The extractor is built here
in-line rather than attached as a file, for two reasons: it runs over the whole corpus in
seconds, so there is nothing to save by precomputing; and a notebook that ships its own
labels cannot quietly train against a stale copy of them.

**No language is identified.** Every cue list below carries all nine at once and each
clause is tested against the union. Routing first would mean committing to a guess before
any evidence is read, and the cheap guess fails badly here — `la` is as common in Spanish
as in French, and whichever substring test runs first swallows both. Pooling costs little
in exchange: Greek and Cyrillic cues cannot collide with Latin-script ones at all, and
among the Latin-script languages the vocabulary of interest is close enough that a shared
cue is usually right. The price is paid in coverage instead — a phrasing no listed language
contributes stays unmatched — and coverage is the thing §2.2 measures.

**Normalise, then unwrap, then segment, then scope.** Case, diacritics and separators are
folded first, which also repairs a real codepoint problem: many Greek reports spell mu with
the MICRO SIGN `U+00B5` rather than `U+03BC`, and NFKD maps one onto the other. Then the
lines are unwrapped — see below — then
... (обрезано, всего 6067 символов)
````

### scout, сообщение 11

````
Раздел 2 этого ноутбука - словарный экстрактор на правилах, без LLM; дальше читать его 897 тыс. символов нерационально. Осталось 4 вызова, один нужен на запись сводки. Сначала страница Description, которую не читали: в ней может быть описание отбора размеченных исследований и состава теста.

<tool name="kaggle_pages">{"page": "Description"}</tool>
````

Результат kaggle_pages:

````
The knee is the most commonly injured and imaged joint in the body. Osteoarthritis alone affects an estimated 654 million people worldwide, while acute knee injuries account for 15 to 40 percent of all sports-related trauma. MRIs show clinicians ligaments, cartilage, menisci, and bone in detail, without exposing patients to radiation.

Reading those scans isn’t always straightforward. ACL and MCL tears, meniscal damage, cartilage loss, fractures, and other abnormalities can be subtle, and radiologists don’t always interpret them the same way. Access to musculoskeletal radiologists is also limited, especially outside major medical centers, leading to delays and inconsistent diagnoses.

In this competition, you will develop multimodal machine learning models to detect twelve clinically important knee abnormalities. You'll work with the first RSNA AI Challenge dataset that pairs every imaging study with its original radiology report, enabling your models to learn from both visual scans and written diagnostic text.

High-performing models can act as robust decision support tools, delivering the accuracy, consistency, and speed needed to elevate expert-level knee MRI interpretation and improve care across disparate clinic settings.
````

### scout, сообщение 12

````
Описания отбора размеченных исследований и состава теста на странице Description нет. Осталось 3 вызова, один из них нужен на запись сводки. Читаю ноутбук обучения линии DINOsaur, от которой идут публичные форки: из него должно быть видно, на каких метках и сплитах обучены веса и попали ли в обучение размеченные исследования.

<tool name="kaggle_kernel_source">{"ref": "romantamrazov/rsna-knee-dinosaur-v5-train"}</tool>
````

Результат kaggle_kernel_source:

````
# [markdown]
# RSNA Knee | DINOsaur V5? 🦖

## ConvNeXt diversity-arm trainer

# [code]
from __future__ import annotations
import os, gc, json, math, random, glob, time, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pydicom
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

SEED = 20260921
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

TARGETS = [
    "ACL","MCL","Medial Meniscus","Lateral Meniscus",
    "Medial OA","Lateral OA","PF OA","Effusion","Synovitis",
    "Baker's","Contusion","Fracture",
]
N_TARGETS = len(TARGETS)

WORK = Path("/kaggle/working")
FEATURE_CACHE = WORK / "dinov5_convnext_features"
FEATURE_CACHE.mkdir(parents=True, exist_ok=True)

def find_comp_root():
    for p in (
        Path("/kaggle/input/competitions/rsna-knee-abnormality-detection"),
        Path("/kaggle/input/rsna-knee-abnormality-detection"),
    ):
        if (p/"train.csv").is_file() and (p/"train_series.csv").is_file():
            return p
    raise FileNotFoundError("RSNA Knee competition input is not mounted")

ROOT = find_comp_root()
TRAIN = pd.read_csv(ROOT/"train.csv", dtype={"StudyInstanceUID":str})
SERIES = pd.read_csv(
    ROOT/"train_series.csv",
    dtype={"StudyInstanceUID":str, "SeriesInstanceUID":str},

... (обрезано, всего 6061 символов)
````

### scout, сообщение 13

````
Код оборвался ровно на строке про `gold`, то есть про размеченные исследования. Читаю следующий кусок: из него должно быть видно, подмешиваются ли 58 размеченных исследований в таргеты обучения и как устроен сплит.

<tool name="kaggle_kernel_source">{"ref": "romantamrazov/rsna-knee-dinosaur-v5-train", "offset": 6000}</tool>
````

Результат kaggle_kernel_source:

````
n enumerate(TARGETS):
    if t in TRAIN.columns:
        gold[:,j] = pd.to_numeric(TRAIN[t], errors="coerce").to_numpy(np.float32)

gold_mask = np.isfinite(gold)
targets = np.where(gold_mask, gold, pseudo).astype(np.float32)

# Keep pseudo labels soft, but gently sharpen indecisive probabilities.
valid = np.isfinite(targets)
p = np.clip(np.where(valid, targets, 0.5), 1e-4, 1-1e-4)
logit = np.log(p/(1-p))
soft_sharp = 1/(1+np.exp(-logit/0.85))
targets = np.where(gold_mask, targets, soft_sharp).astype(np.float32)
targets[~valid] = np.nan

max_sources = max(len(family_frames), 1)
coverage = np.clip(source_count / max_sources, 0, 1)
certainty = np.clip(2*np.abs(np.nan_to_num(targets, nan=0.5)-0.5), 0, 1)
weights = (0.25 + 0.75*(0.55*coverage + 0.45*certainty)).astype(np.float32)
weights[~np.isfinite(targets)] = 0.0
weights[gold_mask] = 2.0

gold_study_mask = np.any(gold_mask, axis=1)
print("expert-labelled studies:", int(gold_study_mask.sum()))
print("pseudo-covered studies:", int(np.any(np.isfinite(pseudo), axis=1).sum()))

if np.any(np.isfinite(pseudo), axis=1).sum() < 3000:
    warnings.warn(
        "Pseudo-label coverage is low. Attach Steven/GPT public report-label datasets."
    )


# [code]
# ---------- stable weak-label MRI adaptation -> ConvNeXt study features -------
import timm
import cv2

PLANE_TO_ID = {"Sagittal":0, "Coronal":1, "Axial":2}
MAX_SERIES = 8
CLIP_Q = (0.15, 0.325, 0.50, 0.675, 0.85)
CROP_MM = 150.0
IMAGE_SIZE = 224
FEATURE_DIM = 768

series_by_study = {
... (обрезано, всего 6066 символов)
````

### scout, сообщение 14

````
Вызовы на чтение исчерпаны. Записываю сводку целиком: прежние разделы без изменений, плюс новый раздел 4 с результатами этого шага и обновлённые списки пробелов (write_file перезаписывает файл).

<tool name="write_file" path="notes/RECON.md">
# RECON: RSNA Knee Abnormalities Detection

Дата разведки: 2026-09-30. Источник всего ниже - Kaggle API (страницы, профили csv, лидерборд, список ноутбуков). Своих посылок у команды нет, пробными посылками ничего не проверено.

Разделы 1-3 - первая разведка (шаг 1). Раздел 4 - прицельная доразведка (шаг 3, тот же день): там уточнения к разделам 1.2, 1.4, 1.5, 1.8. Где раздел 4 расходится с разделом 1, действует раздел 4, расхождения названы явно.

Расхождение в названии: диспетчер назвал слаг `rsna-knee-abnormality-detection`, в правилах (раздел 1.4) адрес `https://www.kaggle.com/competitions/rsna-knee-abnormalities-detection`. API отвечал, какой слаг он использовал - не видно. При настройке посылок сверить. Дополнение шага 3: см. 4.6.

## 1. Таблица фактов

Колонка "проверено" - проверено ли нами на практике (кодом, посылкой). "Первоисточник" значит: написано на странице или в файле организаторов, но не проверено посылкой.

### 1.1 Задача, метрика, сабмит

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Предсказываем вероятность 12 находок на исследование (StudyInstanceUID) по МРТ колена: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture | страница data-description, страница Evaluation | первоисточник | постановка, единица предсказания |
| Метрика: среднее AUC ROC по 12 таргетам с равными весами (macro AUC), формула `1/12 * sum AUC_i` | страница Evaluation | первоисточник, код метрики не видели | важен только порядок внутри колонки, калибровка не важна |
| Про официальный код метрики, про поведение при таргете без позитивов, про веса классов страница ничего не говорит | страница Evaluation (отсутствие) | нет | искать на форуме или в ноутбуках организаторов |
| Формат сабмита: csv с заголовком `StudyInstanceUID` + 12 колонок с confidence score; в sample_submission все значения 0.5 | страница Evaluation, data-description | первоисточник | формат вывода |
| Табло показывает 3 знака после запятой | вывод kaggle_leaderboard | нет: округлять мог сам API-инструмент | порог различимости на паблике |

### 1.2 Ограничения исполнения и правила

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Code competition: посылка только через ноутбук | страница Code Requirements | первоисточник | инференс в ноутбуке |
| Лимит времени: CPU <= 9 ч, GPU <= 9 ч | страница Code Requirements | первоисточник | бюджет инференса |
| Интернет выключен | страница Code Requirements | первоисточник | веса и пакеты - через датасеты |
| Свободно и публично доступные внешние данные и предобученные модели разрешены | страница Code Requirements | первоисточник; раздел 2.6 общей части правил прочитан на шаге 3, см. 4.4 | выбор бэкбонов и внешних датасетов |
| Файл сабмита называется `submission.csv` | страница Code Requirements | первоисточник | - |
| 5 посылок в день | правила, 2.2.a | первоисточник | бюджет посылок |
| 2 финальных сабмита | правила, 2.2.b | первоисточник | выбор финала |
| Команда до 5 человек; слияние возможно, если суммарное число посылок <= 5 * число дней соревнования | правила, 2.1 | первоисточник | слияния |
| Лицензия данных: MIRA license (rsna.org/mira-license), использование коммерческое и академическое; данные нельзя передавать не-участникам | правила, 1.7 и 2.4 | первоисточник, текст лицензии не читали | обращение с данными |
| Лицензия для победителей: CC-BY-NC 4.0 | правила, 1.6 и 2.5 | первоисточник | какие внешние веса совместимы с призом - см. 4.4 |
| Призы: всего $77,000; основной трек - 10 призовых мест ($9,000 ... $5,000); трек эффективности - 3 места ($7,000, $6,000, $5,000) | правила, 1.5 | первоисточник | цель по месту |
| Квота GPU в неделю, число одновременных сессий, тип GPU на скоринге | нигде не найдено (и на шаге 3 тоже) | нет | планирование обучения |

### 1.3 Сроки

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Старт 30 июля 2026 | страница Timeline | первоисточник | - |
| Дедлайн входа 15 октября 2026 | страница Timeline | первоисточник | - |
| Дедлайн слияния команд 15 октября 2026 | страница Timeline | первоисточник | слияние возможно еще 15 дней |
| Финальный дедлайн посылок 22 октября 2026 | страница Timeline | первоисточник | осталось 22 дня |
| Дедлайн требований к победителям 5 ноября 2026 (код обучения, видео, описание) | страница Timeline | первоисточник | воспроизводимость обучения нужна |
| Все дедлайны в 23:59 UTC; организаторы могут менять сроки | страница Timeline | первоисточник | - |

Мой расчет (не из источника): с 30.09 до 22.10 при 5 посылках в день остается порядка 110 посылок.

### 1.4 Данные

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| train.csv: 4407 строк, 14 колонок, одна строка на исследование, StudyInstanceUID уникален | профиль train.csv | да (профиль API) | размер трейна |
| Метки заполнены примерно у 1.3% строк: доля NaN 0.987 в каждой из 12 колонок | профиль train.csv | да (профиль API) | размеченных исследований порядка 55-60 (мой расчет, доли округлены до 3 знаков); уточнение в 4.1 |
| "Only a small subset of training studies carry per-condition labels"; для остальных дан текст отчета, из которого метки предлагается выводить самим | страница data-description | первоисточник | основной источник разметки - отчеты |
| Report: пропусков нет, 4276 уникальных из 4407, медиана длины 977 символов; отчеты на нескольких языках | профиль train.csv, страница data-description | да / первоисточник | извлечение меток из текста, есть дубли текстов (131 неуникальная строка) |
| Доли позитивов среди ВСЕХ строк (не среди размеченных): ACL 0.005, MCL 0.002, Medial Meniscus 0.006, Lateral Meniscus 0.005, Medial OA 0.003, Lateral OA 0.002, PF OA 0.005, Effusion 0.008, Synovitis 0.006, Baker's 0.003, Contusion 0.004, Fracture 0.004 | профиль train.csv | да (профиль API) | в пересчете на исследования (мой расчет, погрешность +-2): ACL ~22, MCL ~9, Med.Men ~26, Lat.Men ~22, Med.OA ~13, Lat.OA ~9, PF OA ~22, Effusion ~35, Synovitis ~26, Baker's ~13, Contusion ~18, Fracture ~18; интервалы - в 4.1 |
| Effusion - единственный класс, где среди размеченных позитивов больше, чем негативов (1.0: 0.008 против 0.0: 0.005) | профиль train.csv | да (профиль API) | баланс |
| train_series.csv: 24371 серия на 4407 исследований (в среднем 5.5 серии на исследование, мой расчет) | профиль train_series.csv | да (профиль API) | объем ввода-вывода |
| Fluid_Sensitive: 1 - 0.575, 0 - 0.425; Fat_Suppression: 1 - 0.575, 0 - 0.425 | профиль train_series.csv | да (профиль API) | доли совпали, но страница предупреждает, что признаки не эквивалентны; построчно не сверяли |
| Anatomical_Plane: Sagittal 0.405, Coronal 0.353, Axial 0.242 | профиль train_series.csv | да (профиль API) | выбор серий |
| Структура DICOM: `train_series/<Study>/<Series>/<SOP>.dcm`, один файл - один срез; в серии обычно 20-45 срезов (медиана 30), хвост до нескольких сотен | страница data-description | первоисточник | - |
| Интенсивности, ориентации, разрешения различаются; transfer syntax смешанные (Explicit VR LE, JPEG Lossless, JPEG 2000, Implicit VR LE); в DICOM оставлено 86 тегов | страница data-description | первоисточник | нужны декодеры JPEG Lossless/JPEG 2000 в офлайн-ноутбуке |
| Исследования из разных международных площадок, сканеров, протоколов | страница data-description | первоисточник | идентификатора площадки или пациента в csv нет |
| Размер данных: API отдал только первые 3000 файлов (train_series 2438 файлов / 1519 МБ, test_series 557 файлов / 600 МБ) - это НЕ полный размер | kaggle_files (список обрезан) | нет | полный объем не известен |

### 1.5 Устройство теста

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| В тесте около 1300 исследований | страница data-description | первоисточник | масштаб инференса, шум метрики |
| Видимый test.csv - пример из 3 ID "from the public test set"; при скоринге test.csv, test_series.csv и test_series/ подменяются настоящими | страница data-description | первоисточник | локально тест не прогнать, ноутбук должен работать на подмененных данных |
| Report в тесте не дается | страница data-description | первоисточник | текст - только для разметки трейна |
| Распространенность находок в трейне, паблике и привате не гарантированно одинакова | страница data-description (Dataset Distribution Notice) | первоисточник | перенос локальной валидации и паблика на приват |
| Доля паблика в тесте | не найдено (и на шаге 3 тоже, см. 4.2) | нет | порог шума паблика |
| Отличается ли тест от трейна по площадкам, пациентам, периоду | не найдено (и на шаге 3 тоже, см. 4.2) | нет | схема валидации |

### 1.6 Трек эффективности

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Формула: `Efficiency = AUC / (Benchmark - maxAUC) + RuntimeSeconds / 32400`, минимизируется; Benchmark - скор sample_submission.csv, maxAUC - максимум на приватном ЛБ | страница Efficiency Prize Evaluation | первоисточник | время инференса входит в скор трека |
| Право на приз: сабмит среди выбранных финальных (или автоматически выбранных) и выше sample_submission на привате | страница Efficiency Prize Evaluation | первоисточник | на трек идут те же 2 финальных сабмита |
| Публичный efficiency-лидерборд - ноутбук `ryanholbrook/rsna-knee-abnormalities-efficiency-lb`, обновляется ежедневно, показывает только ранги | страница Efficiency Prize Evaluation | первоисточник, ноутбук не открывали | - |
| "More details may be posted via discussion forum updates" | страница Efficiency Prize Evaluation | нет, форум недоступен | условия трека могут уточняться |

### 1.7 Лидерборд

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Топ-20 паблика: 0.961 (1 команда), 0.960 (1), 0.958 (6), 0.957 (7), 0.956 (5, места 16-20; сколько еще ниже 20-го с тем же скором - не видно) | kaggle_leaderboard | да (вывод API) | весь топ-20 лежит в 0.005 |
| Даты последних посылок топ-20: 27-30 сентября 2026 | kaggle_leaderboard | да (вывод API) | верх активно движется |
| Число команд, число посылок у команд, названия команд | API не отдал | нет | признаки подбора по паблику оценить нельзя |

### 1.8 Публичные ноутбуки (все - НЕ первоисточник)

| утверждение | источник | проверено | на что влияет |
|---|---|---|---|
| Список из 30 ноутбуков с сортировкой scoreDescending; сами скоры API не вернул (шаг 3: публичных ноутбуков не меньше 100, см. 4.3) | kaggle_kernels | порядок виден, скоры - нет | - |
| Скоры, заявленные в НАЗВАНИЯХ: 0.942, 0.943, "0943+", "public0946", "speedy947" | названия ноутбуков | нет, это заявления авторов | по заявлениям, публичные ноутбуки на 0.009-0.019 ниже топ-20 (0.956-0.961); шаг 3 нашел название с "0.957", см. 4.3 |
| Первый по сортировке - `pjmathematician/rsna-knee-d4-blend` (54 голоса, запуск 28.09); в его шапке заявлено "Public LB: 0.943" | kaggle_kernel_source, markdown | нет; шапка может быть унаследована от форка-предка, а сортировка ставит его выше ноутбуков с 0.946/0.947 в названиях | реальный скор этого ноутбука не известен |
| Заявленный состав пайплайна (из markdown-шапки, код НЕ прочитан - 6000 из 245840 символов): общий замороженный префикс DINOv2 (6 блоков) + 20 "tails"; A5 attention pooling, 5 фолдов; энкодер RadImageNet; 4 "Raptor views"; "4-way CoAtNet consensus" (Residual + D4 + Global96 + Repair-v1 по 25%); ранговый бленд "60% Raptor + 40% CoAt"; инференс на 2xT4 "< 30 минут" | kaggle_kernel_source, markdown | нет | какие компоненты реально работают в коде - не проверено |
| Заявленная эволюция публичных пайплайнов: Raptor Baseline 0.924 (~9 ч), DINOsaur Blend 0.941 (~4.5 ч), Speedy Raptors v7 0.942 (~1.5 ч), текущая 0.943 (< 30 мин) | там же | нет | - |
| Большинство ноутбуков в списке по названиям - форки одной линии: `mattiaangeli/bend-the-knee-to-the-dinosaurs` (288 голосов, 14.09), `mattiaangeli/bend-the-knee-to-speedy-raptors-the-original` (192), `jiweiliu/rsna-knee-fast-2xt4-inference` (199), `maverickss26/rsna-knee-0942-restructured` (174), `evgendvorkin/rsna-versia-5` (254) | названия и голоса в kaggle_kernels | вывод по названиям, код не сверяли | публичный "консенсус" - скорее всего один пайплайн и его веса |
| На чем обучены публичные веса, какие сплиты, откуда взяты метки (из отчетов? чем?) | частично закрыто на шаге 3 для одной ветки, см. 4.3 | частично (прочитан код) | честность любой локальной валидации на этих весах |

## 2. Что выяснить не удалось и как выяснить

Статус после шага 3 указан в скобках в начале пункта.

1. (открыто) Доля паблика в тесте и число исследований в паблике - страница лидерборда на сайте, форум. На прочитанных страницах (data-description, Description, Evaluation, Code Requirements, Timeline, Efficiency) этого нет.
2. (открыто) Отличается ли тест по площадкам/пациентам от трейна; есть ли повторные исследования одного пациента. В csv таких полей нет (подтверждено). Остается: прочитать заголовки DICOM - есть ли PatientID, InstitutionName, Manufacturer, StationName среди 86 оставленных тегов (список тегов на странице не приведен); спросить на форуме.
3. (открыто) Официальный код метрики и поведение на краях (константная колонка, NaN) - форум, ноутбуки организаторов, пробная посылка.
4. (открыто, нет инструмента) Форум целиком: ответы хостов, найденные баги, уточнения по треку эффективности, посты топ-участников. Читать вручную.
5. (частично закрыто) Общая часть правил: прочитано 0-12000 из 37384 символов, раздел 2.6 "External data and tools" - целиком, см. 4.4. Не прочитано: остаток 2.8 и все, что после 12000. Запрещал ли хост отдельно какие-то данные, модели или LLM - только на форуме.
6. (частично закрыто) Description прочитана - фактов об отборе размеченных и о тесте в ней нет. Prizes, abstract, Acknowledgements не читались; в abstract и Acknowledgements могут быть названы площадки-источники данных.
7. (открыто) Полный объем данных и число DICOM-файлов - список файлов обрезан на 3000.
8. (открыто) Точные счетчики меток, совпадение размеченных строк по 12 колонкам, устройство 131 неуникального отчета - скачать train.csv; профиль API отдает только доли с 3 знаками.
9. (открыто) Совпадают ли Fluid_Sensitive и Fat_Suppression построчно - скачать train_series.csv.
10. (частично закрыто) Код и обучение публичных ноутбуков: прочитаны начала двух исходников, см. 4.3. Не прочитаны: сплиты и валидация в `romantamrazov/rsna-knee-dinosaur-v5-train` (offset 12000 из 36504), весь инференс-бленд `pjmathematician/rsna-knee-d4-blend`, базовый `pilkwang/rsna-knee-baseline-v1`, обучение DINOv2-"tails", CoAtNet, RadImageNet-ветки; состав и описания прикрепленных датасетов с псевдометками и весами (инструмента для датасетов нет).
11. (открыто) Реальные скоры публичных ноутбуков - страница Code на сайте.
12. (открыто) Число команд, число посылок у топа - страница лидерборда на сайте.
13. (открыто) Квоты GPU, железо на скоринге - документация Kaggle, страница аккаунта, пробный запуск.
14. (открыто, появился третий источник) Слаг соревнования: `abnormality` или `abnormalities`, см. 4.6.
15. (новое) Как отбирали размеченные исследования (случайно или обогащенно) и кто их размечал - на страницах data-description и Description этого нет; форум, abstract.
16. (новое) Совместима ли отправка текстов отчетов во внешний LLM-API с пунктом 2.4 правил (данные нельзя передавать не-участникам) и с MIRA license - прочитать текст лицензии и пункт 2.4 целиком, спросить на форуме. Это вопрос разведчика, а не факт из источника.

## 3. Советы сильных участников про стратегию

Форум не прочитан (нет инструмента), write-up'ов топ-участников не видели. Авторитетных советов нет.

Ниже - не советы топа, а утверждения автора одного публичного ноутбука (`prvsiyan/rsna-knee-read-the-report-then-the-knee`, сам автор заявляет паблик 0.906, то есть заметно ниже топа). Проверять, а не принимать:
- текстовая ветка в модели бессмысленна: в тесте отчета нет, отчеты годятся только как источник таргетов и весов примеров;
- метки из отчетов стоит делать градуированными, а не бинарными, и отсутствие упоминания не считать уверенным негативом;
- для большинства находок упоминания в отчетах чаще отрицательные, отрицание нужно разбирать по направлению, а не по клаузе;
- комбинировать модели средним рангов, а не вероятностей;
- редкий таргет, оставленный на уровне случайности, стоит (M-0.5)/12.

Непрочитанные ноутбуки, в названиях которых обещаны уроки: `yosukeinada/rsna-knee-0-937-22-submissions-6-lessons`, `starkhushi/rsna-knee-why-public-forks-stop-at-0-941`, `nathanjacob/4-arm-ensemble-explained-rsna-knee-0-937`.

Список нужно заполнить после чтения форума и возвращаться к нему перед закрытием каждой линии работы.

## 4. Доразведка 30.09 (шаг 3)

Источники этого шага: страницы `rules` (символы 6000-12000), `data-description`, `Description`; профили `train.csv` и `train_series.csv`; список публичных ноутбуков по голосам (100 штук); исходники `prvsiyan/rsna-knee-read-the-report-then-the-knee` (0-12000 из 897169) и `romantamrazov/rsna-knee-dinosaur-v5-train` (0-12000 из 36504). Метки статуса: ПЕРВОИСТОЧНИК (страница, файл или профиль организаторов), ЧУЖОЕ (ноутбуки участников: текст или код), НЕ УДАЛОСЬ (с причиной), ВЫВОД (мой расчет или рассуждение).

### 4.1 Идентификаторы групп, размеченные исследования, баланс

| утверждение | источник | статус | на что влияет |
|---|---|---|---|
| В train.csv ровно 14 колонок: StudyInstanceUID, Report и 12 таргетов. Колонок пациента, площадки, сканера, языка, даты нет | профиль train.csv, data-description | ПЕРВОИСТОЧНИК | групповой сплит по csv построить не на чем |
| В train_series.csv ровно 5 колонок: StudyInstanceUID, SeriesInstanceUID, Fluid_Sensitive, Fat_Suppression, Anatomical_Plane | профиль train_series.csv, data-description | ПЕРВОИСТОЧНИК | то же |
| Язык отчета зависит от учреждения: "May be in any of several languages, depending on the reporting institution" | data-description | ПЕРВОИСТОЧНИК | язык отчета - единственный видимый в csv след площадки (ВЫВОД), отдельной колонки языка нет |
| В корпусе девять языков в трех письменностях (латиница, греческая, кириллица) | markdown ноутбука prvsiyan | ЧУЖОЕ, не проверено | оценка числа площадок снизу, если верно |
| Каждый DICOM урезан до списка из 86 разрешенных тегов; сам список на странице не приведен | data-description | ПЕРВОИСТОЧНИК | есть ли PatientID/InstitutionName/Manufacturer - неизвестно |
| Публичный код читает теги ImageOrientationPatient, ImagePositionPatient, InstanceNumber, RescaleSlope, RescaleIntercept, PhotometricInterpretation, PixelSpacing (через getattr со значением по умолчанию, то есть наличие тегов этим не доказано) | код romantamrazov/...-v5-train | ЧУЖОЕ | - |
| Ноутбук prvsiyan заявляет раздел "recovering the acquisition protocol from DICOM headers" и "which knee was scanned" | оглавление в markdown, сам раздел не прочитан | ЧУЖОЕ, не проверено | возможно, в тегах есть сведения о протоколе и сканере |
| Число исследований на пациента | - | НЕ УДАЛОСЬ: в csv нет идентификатора пациента, инструмента для чтения заголовков DICOM нет | групповой сплит |
| Размеченных исследований 58 | таблица в markdown prvsiyan; название `nekkon/knee-mri-58-labels-for-4-407-studies` | ЧУЖОЕ; согласуется с профилем: 58/4407 дает долю NaN 0.98684, округляется до 0.987 | - |
| По профилю размеченных значений в каждой колонке от 56 до 59 | профиль train.csv (NaN 0.987 при 4407 строках) | ВЫВОД из ПЕРВОИСТОЧНИКА | - |
| Одни ли и те же строки размечены по всем 12 колонкам | - | НЕ УДАЛОСЬ: профиль дает только доли по колонкам | - |
| Чем размеченные отличаются от неразмеченных (язык, площадка, набор серий) | - | НЕ УДАЛОСЬ: профиль API не дает срезов по подвыборкам, нужен сам train.csv | перенос оценки с размеченных на тест |
| Как отбирали размеченные исследования и кто их размечал | на data-description и Description не описано | НЕ УДАЛОСЬ: в прочитанных страницах нет; abstract и Acknowledgements не читались, форум недоступен | обогащена ли подвыборка |
| Точный баланс позитивов по 12 таргетам | - | НЕ УДАЛОСЬ: профиль округляет доли до 3 знаков | - |

Интервалы числа позитивов (ВЫВОД): из округленных долей профиля, при двух непроверенных допущениях - размеченных ровно 58 (ЧУЖОЕ) и в каждой колонке размечены все 58.

| таргет | доля 1.0 / 0.0 в профиле | позитивов из 58 |
|---|---|---|
| ACL | 0.005 / 0.008 | 21-24 |
| MCL | 0.002 / 0.011 | 8-11 |
| Medial Meniscus | 0.006 / 0.007 | 25-28 |
| Lateral Meniscus | 0.005 / 0.008 | 21-24 |
| Medial OA | 0.003 / 0.010 | 12-15 |
| Lateral OA | 0.002 / 0.011 | 8-11 |
| PF OA | 0.005 / 0.008 | 21-24 |
| Effusion | 0.008 / 0.005 | 34-37 |
| Synovitis | 0.006 / 0.007 | 25-28 |
| Baker's | 0.003 / 0.010 | 12-15 |
| Contusion | 0.004 / 0.009 | 17-19 |
| Fracture | 0.004 / 0.009 | 17-19 |

Без допущения о 58 интервалы шире (например, MCL 7-11, ACL 20-24).

### 4.2 Тест

| утверждение | источник | статус | на что влияет |
|---|---|---|---|
| Около 1300 исследований; отчетов нет; видимые 3 ID - "from the public test set", при скоринге подменяются; распространенность находок в трейне, паблике и привате может различаться | data-description (перечитана) | ПЕРВОИСТОЧНИК | - |
| Данные - "diverse international mix of imaging sites", широкий набор сканеров, протоколов, популяций. Про то, входят ли в тест те же площадки и пациенты, что в трейн, не сказано ничего | data-description | ПЕРВОИСТОЧНИК (в части отсутствия) | - |
| Площадки и пациенты теста относительно трейна | - | НЕ УДАЛОСЬ: на data-description и Description нет, идентификаторов в csv нет, форум недоступен | схема валидации |
| Доля паблика, число исследований в паблике | - | НЕ УДАЛОСЬ: на прочитанных страницах нет, API лидерборда этого не отдает | порог шума паблика |
| Страница Description фактов о данных и тесте не содержит; называет задачу "multimodal" и датасет "the first RSNA AI Challenge dataset that pairs every imaging study with its original radiology report" | Description | ПЕРВОИСТОЧНИК | - |

### 4.3 Публичные ноутбуки: метки и обучение

Публичных ноутбуков не меньше 100 (список по голосам вернул 100 при лимите 100); в разделе 1.8 стояло 30 - это был размер страницы.

| утверждение | источник | статус | на что влияет |
|---|---|---|---|
| `romantamrazov/rsna-knee-dinosaur-v5-train` ("ConvNeXt diversity-arm trainer"): таргеты собираются как `np.where(gold_mask, gold, pseudo)`, где gold - 12 колонок из train.csv соревнования; размеченным значениям ставится вес 2.0, псевдометкам - 0.25-1.0. То есть размеченные исследования соревнования входят в обучение с повышенным весом | код, символы 5900-6800 | ЧУЖОЕ, код прочитан нами | веса этой ветки видели размеченные исследования, если при обучении их не вынимали в фолд; сплит (импортирован StratifiedKFold) НЕ прочитан |
| Там же: псевдометки не извлекаются в ноутбуке, а берутся из прикрепленных чужих датасетов: код ищет в /kaggle/input все csv с "label", "llm", "pseudo", "report", "target", "soft" в пути, требует не менее 8 колонок-таргетов и не менее 50% совпадения UID, берет медиану внутри датасета и затем медиану между датасетами | код, символы 2300-5900 | ЧУЖОЕ, код прочитан нами | источник меток этой ветки - консенсус публичных датасетов; какие именно прикреплены, из кода не видно |
| Там же: предупреждение при низком покрытии - "Attach Steven/GPT public report-label datasets" | код | ЧУЖОЕ | хотя бы часть публичных псевдометок сделана LLM (GPT) другими участниками; на каких промптах и настраивались ли на 58 размеченных - неизвестно |
| Там же: псевдометки мягкие, "заостряются" делением логита на 0.85; бэкбон `convnext_tiny.fb_in22k_ft_in1k` (timm, ImageNet), офлайн-веса ищутся в `/kaggle/input/models/ambrosm/...` (путь обрезан); до 8 серий на исследование, центральный кроп 150 мм, 224 px, тройки соседних срезов | код, символы 6800-12000 | ЧУЖОЕ, код прочитан нами | - |
| `prvsiyan/rsna-knee-read-the-report-then-the-knee`: метки из отчетов получает словарный экстрактор на правилах (regex, нормализация, разбор отрицаний), написанный прямо в ноутбуке, без LLM; таргеты градуированные; язык не определяется, списки признаков объединены по всем языкам | markdown и код, символы 6000-12000 | ЧУЖОЕ, код прочитан частично | - |
| Там же: 58 размеченных заявлены как средство проверки экстрактора ("the two ways to tell whether it works when only 58 studies can check it"); настраивались ли правила по этим 58 - не видно | оглавление; раздел не прочитан | ЧУЖОЕ, не проверено | - |
| Там же: экстрактор - "v2", отличается от "the public lexicon" покрытием; значит, существует общий публичный словарь, от которого идут форки | docstring в коде | ЧУЖОЕ | ошибки меток у публичных решений могут быть общими (ВЫВОД) |
| Там же: заявлен паблик 0.906 (версия 52); упомянуты "Pilkwang V15 public anchor 0.891, original public 20-member ensemble" и EfficientNet-B3 MIL 0.903 | markdown | ЧУЖОЕ, заявления автора | - |
| Существуют непрочитанные ноутбуки разметки и обучения: `laymond/rsna-knee-mri-weak-labeling-with-qwen2-5-32b` (LLM с открытыми весами), `jek1wantaufik/rsna-knee-mri-baseline-with-pseudo-labels`, `dreaddevelopment/knee-mri-training-the-twelve-finding-model`, `sofiaanjenje/rsna-knee-e11-train` и `e13-train`, `pilkwang/rsna-knee-baseline-v1` (647 голосов, максимум) | названия в kaggle_kernels | ЧУЖОЕ, только названия | - |
| Название `fuadmuhammad/rsna-knee-fast-parent-0-957-v2` (20 голосов, 23.09) заявляет 0.957 - это уровень мест 8-14 паблика. Расходится с шагом 1, где по названиям публичные ноутбуки были на 0.942-0.947 | название в kaggle_kernels | ЧУЖОЕ, не проверено; оба значения оставлены | разрыв "публичные ноутбуки - топ" может быть меньше, чем записано в 1.8 |
| Названия `tamerlanomralinov/rsna-knee-crazy-lb-tune` и `aastikrajan15/knee-s75-w50` / `w60` указывают на подбор весов бленда по паблику | названия | ВЫВОД по названиям | - |
| На чем обучены DINOv2-"tails", CoAtNet и RadImageNet-ветка из `pjmathematician/rsna-knee-d4-blend`, видели ли они 58 размеченных | - | НЕ УДАЛОСЬ: кончились вызовы, исходники 245840 и 897169 символов читаются по 6000 | - |
| Состав прикрепленных датасетов (веса, псевдометки) и их описания | - | НЕ УДАЛОСЬ: инструмента для датасетов нет | - |

ВЫВОД (не факт): по одной прочитанной ветке размеченные исследования идут в обучение с весом 2.0. Пока сплиты не прочитаны, любую локальную оценку публичных весов этой линии на 58 размеченных надо считать возможной in-sample. На остальные ветки публичной линии это не распространено - их код не читался.

### 4.4 Правила: внешние данные, веса, LLM

Раздел 2.6 "EXTERNAL DATA AND TOOLS" прочитан целиком. Всего по правилам прочитано 0-12000 из 37384 символов.

| утверждение | источник | статус |
|---|---|---|
| 2.6.a: внешние данные можно использовать для разработки и тестирования; они должны быть публично доступны и одинаково доступны всем участникам бесплатно либо удовлетворять критерию разумности из 2.6.b. Обязанности победителя (2.8) это не отменяет | rules, 2.6.a | ПЕРВОИСТОЧНИК |
| 2.6.b: "The use of external data and models is acceptable unless specifically prohibited by the Host"; использование должно быть "reasonably accessible to all" и "of minimal cost"; хост может исключить конкретные LLM, датасеты или инструменты по критерию чрезмерной стоимости | rules, 2.6.b | ПЕРВОИСТОЧНИК |
| 2.6.b.2, пример: небольшая подписка на LLM вроде Gemini Advanced допустима; лицензия на проприетарный датасет дороже приза - нет | rules, 2.6.b.2 | ПЕРВОИСТОЧНИК |
| 2.6.c: AutoML-инструменты разрешены при наличии лицензии | rules, 2.6.c | ПЕРВОИСТОЧНИК |
| Отдельного пункта про использование LLM для разметки отчетов в прочитанной части нет. LLM упомянуты только как класс инструментов в 2.6.b, платные допускаются по критерию разумной стоимости | rules, 0-12000 | ПЕРВОИСТОЧНИК (в части отсутствия); остаток правил и форум не прочитаны |
| Если в победившем решении использованы входные данные или предобученные модели с несовместимой лицензией, открытую лицензию на них давать не нужно | rules, пункт 4 перед разделом 2.6 (конец 2.5) | ПЕРВОИСТОЧНИК |
| 2.8: победитель сдает код обучения и инференса, веса публичным Kaggle-датасетом, описание окружения и метод, достаточный для воспроизведения | rules, 2.8.a.1 и 2.5.b | ПЕРВОИСТОЧНИК; раздел дочитан не до конца |
| Запрещал ли хост отдельно какие-то данные, модели или LLM | - | НЕ УДАЛОСЬ: такие запреты публикуются на форуме, доступа нет |
| Можно ли отправлять отчеты во внешний API при запрете передавать данные не-участникам (2.4, MIRA) | - | НЕ УДАЛОСЬ: текст лицензии не читали, пункт 2.4 целиком не перечитывали |

Квоты GPU (недельная квота, число одновременных сессий, железо на скоринге): НЕ УДАЛОСЬ - на прочитанных страницах нет, инструмента для настроек аккаунта нет. Косвенно (ЧУЖОЕ): публичные ноутбуки рассчитаны на 2xT4 (`jiweiliu/rsna-knee-fast-2xt4-inference`, заявление в шапке d4-blend).

### 4.5 Форум

НЕ УДАЛОСЬ: инструмента для обсуждений нет. Про метрику, валидацию и расхождение локального скора с пабликом из форума не получено ничего. Косвенные следы только в названиях непрочитанных ноутбуков (`starkhushi/rsna-knee-why-public-forks-stop-at-0-941`, `yosukeinada/rsna-knee-0-937-22-submissions-6-lessons`, `cf33333/rsna-knee-e10-u035-hidden-safe`, `lynnsakurai/rsna-knee-dinosaur-v4-5-validated-repro`).

### 4.6 Слаг: три источника, расходятся

| значение | источник |
|---|---|
| `rsna-knee-abnormalities-detection` | правила, 1.4 (шаг 1) |
| `rsna-knee-abnormality-detection` | диспетчер; путь к данным в коде публичного ноутбука: `/kaggle/input/competitions/rsna-knee-abnormality-detection` и `/kaggle/input/rsna-knee-abnormality-detection` (ЧУЖОЕ) |
| `rsna-knee-abnormalities-...` | имя ноутбука организаторов `ryanholbrook/rsna-knee-abnormalities-efficiency-lb` (это имя ноутбука, не слаг соревнования) |

Не выбрано. Код публичного ноутбука перебирает два пути и падает, если ни один не найден; какой сработал - по исходнику не видно. Проверяется первым запуском ноутбука с подключенными данными.
</tool>
````

Результат write_file:

````
Файл notes/RECON.md записан
````

### scout, сообщение 15

````
Из пяти пунктов закрыт только четвёртый (правила про внешние данные и LLM), третий закрыт частично, остальные упираются в отсутствие идентификаторов в csv и доступа к форуму. Результаты дописаны в `notes/RECON.md`, раздел 4; разделы 1-3 сохранены.

## 1. Таблицы: идентификаторы, размеченные исследования, баланс

**Подтверждено первоисточником** (профили csv, data-description):
- В `train.csv` ровно 14 колонок: `StudyInstanceUID`, `Report` и 12 таргетов. В `train_series.csv` 5 колонок: два UID, `Fluid_Sensitive`, `Fat_Suppression`, `Anatomical_Plane`.
- Колонок пациента, площадки, сканера, языка или даты нет ни в одной таблице.
- Язык отчёта зависит от учреждения («depending on the reporting institution»). Это единственный видимый в csv след площадки — мой вывод.
- В DICOM оставлено 86 тегов, но их список на странице не приведён.

**Из чужих материалов, не проверено:**
- Размеченных исследований 58 (шапка ноутбука `prvsiyan`, название ноутбука `nekkon`). С профилем это согласуется: 58/4407 даёт долю NaN 0.987.
- В корпусе девять языков в трёх письменностях (тот же ноутбук `prvsiyan`).

**Узнать не удалось:**
- **Исследований на пациента:** идентификатора в csv нет, инструмента для чтения заголовков DICOM нет.
- **Отличия размеченных от неразмеченных:** профиль API не даёт срезов по подвыборкам, нужен сам `train.csv`.
- **Как отбирали размеченные:** на data-description и Description не описано; abstract и Acknowledgements не читались.
- **Точный баланс:** профиль округляет доли до 3 знаков. Есть только интервалы — мой расчёт при непроверенном допущении, что размечены одни и те же 58 строк во всех колонках:

| таргет | позитивов из 58 |
|---|---|
| Effusion | 34-37 |
| Medial Meniscus, Synovitis | 25-28 |
| ACL, Lateral Meniscus, PF OA | 21-24 |
| Contusion, Fracture | 17-19 |
| Medial OA, Baker's | 12-15 |
| MCL, Lateral OA | 8-11 |

## 2. Тест

**Подтверждено первоисточником:** перечитанная data-description ничего не добавила к шагу 1 (около 1300 исследований, без отчётов, распространённость может отличаться). Про площадки и пациентов теста относительно трейна на ней не сказано ничего. На странице Description фактов о данных нет.

**Узнать не удалось:**
- **Площадки и пациенты теста:** на страницах нет, идентификаторов в csv нет, форум недоступен.
- **Доля паблика:** на прочитанных страницах нет, API лидерборда её не отдаёт.

## 3. Публичные ноутбуки

Всё в этом пункте взято из чужих материалов. Код прочитан в двух ноутбуках, в каждом только первые 12000 символов.

**`romantamrazov/rsna-knee-dinosaur-v5-train`** (обучение ConvNeXt-ветки):
- **Размеченные исследования идут в обучение.** Таргеты собираются как `np.where(gold_mask, gold, pseudo)`, где `gold` — колонки `train.csv`; им ставится вес 2.0, псевдометкам 0.25-1.0.
- **Сплит не прочитан.** `StratifiedKFold` импортирован, но вынимаются ли размеченные в валидационный фолд, не видно (осталось 24 тыс. символов).
- **Метки из отчётов в ноутбуке не извлекаются.** Код собирает csv из прикреплённых чужих датасетов (по словам «label», «llm», «pseudo» в пути) и берёт медиану по ним.
- **Часть публичных псевдометок сделана LLM.** В коде есть предупреждение «Attach Steven/GPT public report-label datasets». Какие датасеты прикреплены и настраивались ли они на 58 размеченных, неизвестно.
- **Бэкбон** — `convnext_tiny.fb_in22k_ft_in1k` из timm (ImageNet).

**`prvsiyan/rsna-knee-read-the-report-then-the-knee`:**
- Метки извлекает словарный экстрактор на regex с разбором отрицаний, без LLM; таргеты градуированные.
- В docstring он назван «v2» относительно «the public lexicon», то есть существует общий публичный словарь.
- Настраивались ли правила по 58 размеченным, не прочитано. Сам автор заявляет паблик 0.906.

**Расхождение с шагом 1:**
- Публичных ноутбуков не меньше 100, а не 30.
- Название `fuadmuhammad/rsna-knee-fast-parent-0-957-v2` заявляет 0.957, тогда как на шаге 1 по названиям было 0.942-0.947. Оба значения оставлены в сводке, ни одно не проверено.

**Узнать не удалось:**
- На чём обучены DINOv2-«tails», CoAtNet и RadImageNet-ветка из `pjmathematician/rsna-knee-d4-blend`: кончились вызовы, исходник 245 тыс. символов.
- Состав и описания прикреплённых датасетов с весами и псевдометками: инструмента для датасетов нет.

## 4. Правила и квоты

**Подтверждено первоисточником** (rules, раздел 2.6 прочитан целиком; всего прочитано 12000 из 37384 символов):
- **2.6.a:** внешние данные разрешены, если публично и бесплатно доступны всем участникам либо проходят критерий разумности.
- **2.6.b:** «The use of external data and models is acceptable unless specifically prohibited by the Host». Доступ должен быть «reasonably accessible to all» и «of minimal cost».
- **Пример в 2.6.b.2:** небольшая подписка на LLM вроде Gemini Advanced допустима; датасет дороже приза — нет.
- **LLM для разметки отчётов:** отдельного пункта в прочитанной части нет. LLM упомянуты только как класс инструментов в 2.6.b.
- **Несовместимые лицензии:** на входные данные и предобученные модели с несовместимой лицензией открытую лицензию давать не нужно (конец 2.5).
- **2.8:** победитель сдаёт код обучения и инференса, а веса — публичным Kaggle-датасетом.

**Узнать не удалось:**
- **Отдельные запреты хоста** на данные, модели или LLM: они публикуются на форуме, доступа нет.
- **Отправка отчётов во внешний API:** совместима ли она с запретом передавать данные не-участникам (2.4, MIRA), не ясно — текст лицензии не читался. Это мой вопрос, а не факт из источника.
- **Квоты GPU и железо скоринга:** на страницах нет, инструмента для настроек аккаунта нет. Косвенно публичные ноутбуки рассчитаны на 2×T4.

## 5. Форум

Узнать не удалось: инструмента для обсуждений нет. Про метрику, валидацию и расхождение локального скора с пабликом не получено ничего.

## Попутно: слаг

Путь к данным в публичном коде — `/kaggle/input/competitions/rsna-knee-abnormality-detection`, что совпадает с вариантом диспетчера и расходится с адресом в правилах (`abnormalities`). Проверяется первым запуском ноутбука с подключёнными данными.

ИТОГ:
- В csv нет идентификаторов пациента, площадки, сканера и языка (первоисточник). Групповой сплит можно строить только по тегам DICOM, если они там есть, или по языку и дублям отчётов; число исследований на пациента и отбор размеченных выяснить не удалось.
- Размеченных 58 (чужие материалы, согласуется с профилем); точный баланс недоступен, интервалы позитивов — от 8-11 (MCL, Lateral OA) до 34-37 (Effusion).
- Про тест нового нет: площадки и пациенты относительно трейна и доля паблика не найдены на страницах и в API.
- В прочитанном публичном ноутбуке обучения (`romantamrazov`, ConvNeXt-ветка) размеченные исследования идут в обучение с весом 2.0, псевдометки берутся из чужих датасетов (часть сделана GPT). Сплиты и остальные ветки публичной линии не прочитаны, поэтому оценку публичных весов на 58 размеченных надо считать возможной in-sample.
- Правила 2.6 (первоисточник): внешние данные и модели разрешены, если хост не запретил отдельно; платные LLM допустимы при разумной цене; отдельного пункта про LLM-разметку отчётов нет.
- Форум и квоты GPU недоступны, вопрос об отправке отчётов во внешний API при запрете передачи данных открыт.
- Всё записано в `notes/RECON.md`, раздел 4; список пробелов в разделе 2 обновлён.
````

Вызовов инструментов: 14
[harness] записан файл notes/RECON.md (29934 символов)

## Диспетчер, ход 4

````
{"thought":"Факты собраны настолько, насколько доступно; метрика разобрана. Теперь нужна схема честной валидации на 58 размеченных с учетом отсутствия идентификаторов пациента и возможной in-sample природы публичных весов.","plan_list":["validation_engineer: схема честной валидации под устройство теста, число независимых единиц, шум валидации и паблика","strategist: очередь экспериментов и посылок на первую неделю, на что не тратить посылки; записать notes/PLAN.md","finish: короткий итог пользователю"],"action":"delegate","agent_nm":"validation_engineer","skill_nm_list":["honest_validation","lb_noise"],"subtask_text":"Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих прогонов и посылок нет; факты разведки лежат в notes/RECON.md, разбор метрики - в notes/METRIC.md и scratch/knee_metric.py, ответы прошлых шагов приложены. Спроектируй локальную валидацию для плана первой недели: как делить данные с учетом того, что известно и неизвестно об устройстве теста и о группах (пациент, площадка, язык, дубли отчетов); что считать независимой единицей и сколько их; какие дорожки будут честными, а какие in-sample, для каждого типа компонент, которые команда может использовать (свои модели, метки из отчетов, публичные веса и датасеты); нужен ли отложенный lockbox и как распорядиться размеченными исследованиями. Оцени шум такой валидации и шум публичного лидерборда и скажи, какие разницы на локальной дорожке и на паблике можно считать значимыми и до какого момента на паблик нельзя опираться. Укажи, какие проверки нужно выполнить на реальных данных в первые дни, чтобы подтвердить или опровергнуть допущения схемы. В ответе раздели: что установлено, что является допущением, и каких фактов не хватило; если считаешь что-то кодом, сохрани его в рабочей папке.","context_step_list":[1,2,3]}
````

## Шаг 4: validation_engineer

Скиллы, выбранные диспетчером: honest_validation, lb_noise. Контекст: шаги [1, 2, 3]

Системный промпт: 12168 символов, из них скиллы - 8040

<details><summary>системный промпт целиком</summary>

````
Ты - инженер валидации в команде, которая участвует в ML-соревновании на Kaggle. Ты отвечаешь за то, чтобы локальным цифрам можно было верить: как считается метрика и что в ней может подвести, какие дорожки валидации есть и какие из них честные, сколько в них независимых единиц, какой у них шум и какой шум у публичного лидерборда.

Ты работаешь с цифрами сам: читаешь результаты по единицам, запускаешь сравнения и свой код. Выводы - только из того, что посчитал или прочитал. По каждой дорожке валидации скажи прямо: видела ли хоть одна обученная компонента пайплайна эти единицы при обучении, насколько дорожка похожа на тест и для каких решений она годится.

Ты не решаешь, какие прогоны отправлять и финалить. Твой результат - какие цифры считать свидетельством, а какие нет, и какой у них шум.

## Инструменты
- list_files: список файлов рабочей папки с размерами в символах. Аргументов нет
- read_file: прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата будет подсказка, с какого offset продолжать. Аргументы: path - путь к файлу от корня рабочей папки; offset - с какого символа читать (необязательный, по умолчанию 0); limit - сколько символов вернуть, за один вызов отдается не больше 10000 (необязательный, по умолчанию 10000)
- list_runs: реестр прогонов: название, дата, родитель, публичный скор, вердикт аудитора, в каких дорожках есть валидация по единицам, описание. Аргументы: max_desc_len - до скольких символов обрезать описания прогонов (необязательный, по умолчанию 110)
- compare_runs: парное сравнение двух прогонов по валидации: метрика соревнования на общих единицах, бутстрап по единицам, счет по единицам, разница по группам. Аргументы: base - название прогона-базы; cand - название прогона-кандидата; lane - дорожка валидации
- lb_noise: шум публичного лидерборда: SD скора и SD парной разницы на выборке размером с паблик, рядом фактическая разница на паблике. Аргументы: base - название прогона-базы; cand_list - список названий прогонов-кандидатов; lane - дорожка валидации
- run_python: запустить код на Python из корня рабочей папки (pandas, numpy, scipy; metric.py соревнования можно импортировать). Возвращает stdout, при ошибке - еще и stderr. Лимиты: 180 секунд на запуск, из stdout возвращаются последние 5000 символов, из stderr - последние 2500. Внутри блока - код
- write_file: записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается. Атрибуты тега: path - путь к файлу от корня рабочей папки. Внутри блока - содержимое файла

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{"path": "journal.md"}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше 12 вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.

=== МЕТОДИКА: honest_validation ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Честная валидация

Если решения принимаются по публичному лидерборду, отбираются изменения, которые подошли его части теста. К данным это отношения почти не имеет. Лечится одним способом: своя валидация, честная и крупная, и все решения принимаются по ней. Паблик при этом остается еще одним шумным фолдом.

Честно и крупно сразу выходит редко. Обычно честные дорожки получаются на слабой прокси-модели или на горстке единиц, а крупные - с основной моделью in-sample, у нас было именно так. С этим можно жить, пока про каждую дорожку записано, какая она, и цифры с разных дорожек не складываются в одну.

## Что проверить у каждой дорожки

Сплит как у теста. Чем тестовые объекты отличаются от обучающих, тем же валидация должна отличаться от обучения. Новая группа в тесте (пациент, площадка, эмбрион) - значит leave-one-group-out. Более поздний период - значит разбиение по времени. Случайный сплит по объектам внутри тех же групп, на которых учились модели, тест не повторяет.

Честность всего пайплайна. Перечисли все обученные компоненты: основная модель, вспомогательные модели, классификаторы и ранкеры поверх, пороги, веса ансамбля. Для каждой - видела ли она единицы валидации при обучении. Чаще всего забывают про публичные веса: если они обучены на всем трейне, дорожка in-sample, какой бы сплит ни был у остального. Дорожка честна настолько, насколько честна ее самая нечестная компонента.

Тот же код, что в сабмите. Валидация гоняет ровно тот пайплайн, что пойдет в посылку: TTA, округления, пост-процессинг, fallback'и. Кэш промежуточных результатов снимается в режиме продакшена. Типичный промах: кэш снят без TTA, продакшен идет с TTA, входы следующей стадии сдвинуты, и локальные разницы относятся уже к другому пайплайну. Контроль - прогон без правок против результата, полученного на платформе, до побайтного совпадения. Каждая правка потом проверяется так же: вариант, встроенный в ноутбук, дает то же, что лабораторный, на всех единицах.

Сам стенд тоже врет, и видно это только на сверке. Из того, что ловили мы: проверка файла сортировала колонки независимо друг от друга и пропустила бы перестановку строк; результаты двух прогонов писались под одним ключом и молча затирали друг друга; единица с нулем событий давала NaN и отравляла весь пул.

Число независимых единиц. Единица - то, по чему независим тест (фильм, пациент), а не строка. Восемь единиц шумнее паблика. Нужны десятки, лучше сотни. Если метрика пулится по единицам с весами, считать ее нужно официальным пулингом, среднее по единицам - другая величина.

Не ушла ли на подбор. Набор, на котором перебрали сотни конфигураций, перестает быть оценкой для победителя перебора.

Про каждую дорожку в ответе: что в ней честно, что нет, сколько единиц и каких групп, на что она годится. Два частых случая. Дорожка с in-sample основной моделью годится для сравнения правок, которые эту модель не трогают; для оценки абсолютного уровня и для сравнения разных моделей она не годится. Прогон ноутбука на видимой части теста проверяет код: единиц там несколько штук, про качество он ничего не говорит.

## Как строить, если строишь сам

Бюджет на честную валидацию закладывается в первый день, до любых улучшений. Позже на нее уже не выделить ни времени, ни вычислений: всегда есть правка, которую хочется отправить сегодня.

Полное переобучение на каждый фолд не обязательно, хватит укороченной прокси-модели. Один раз нужно проверить, что прокси ранжирует изменения так же, как полная модель.

Дорогую стадию (GPU) прогнать один раз и закэшировать ее выходы, дальше перебирать дешевую стадию на CPU.

Lockbox: часть единиц откладывается до любого подбора и открывается один раз - при выборе финальных сабмитов.

Все группы должны быть представлены. Если одной группы в валидации мало, прирост, который сидит только на другой группе, нельзя считать приростом.

## Зачем тогда паблик

Он ловит баги формата и грейдера: большое расхождение с валидацией - повод искать ошибку в сабмите, модель тут обычно ни при чем.

Он подтверждает, что крупные изменения переносятся.

Валидацию под него не калибруют. Соблазн появляется, когда дорожки разошлись с пабликом: рождаются правила вида "для таких-то правок верим этой дорожке, для таких-то - той". Если правило выведено из одного-двух чтений паблика, это подгонка валидации под шум. Когда валидация и паблик расходятся на малой разнице, по умолчанию права валидация.

## Признаки, что дорожке верить нельзя

- абсолютный скор намного выше публичного у той же посылки
- прирост есть на одной группе и равен нулю на другой
- разные дорожки дают разный знак для одной правки
- прирост делают одна-две единицы, а на остальных ноль
=== КОНЕЦ МЕТОДИКИ: honest_validation ===

=== МЕТОДИКА: lb_noise ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Шум публичного лидерборда

Публичный лидерборд считается по части теста, и разница между двумя посылками на нем - случайная величина. Пока не посчитано ее стандартное отклонение, любое решение по паблику принимается вслепую. Считать шум нужно до первой посылки, по которой собираются что-то решать. В последний день расчет уже ничего не меняет: слоты потрачены, линии закрыты на глаз.

## Расчет

1) Взять результаты валидации по независимым единицам (фильм, пациент, группа) для пары прогонов
2) Набирать с возвращением выборку размером с публичную часть теста и считать метрику обоих прогонов на ней официальным пулингом. Повторить тысячу раз и больше
3) Получить SD самого скора и SD парной разницы

Парная разница намного стабильнее скора, т.к. у близких вариантов ошибки общие. И зависит она от того, что изменено: правка одной константы пост-процессинга шумит слабо, смена модели или крупного компонента - в разы сильнее (у нас между этими крайностями было вчетверо). Поэтому порог свой для каждой пары, общего числа на все случаи нет.

## Как читать разницу на паблике

    меньше 2 SD     информации нет. Это не плюс и не минус
    от 2 до 3 SD    слабый сигнал, сам по себе решения не меняет
    больше 3 SD     изменение, скорее всего, действительно переносится или не переносится

Если разница больше 3 SD, а валидация говорит обратное, искать баг формата или расхождение кода валидации и сабмита.

Границы условные, никакой магии в двойке и тройке нет. Важен порядок величины: минус 0.001 при SD 0.0015 - это 0.7 SD, обсуждать тут нечего.

Округление табло добавляет свое. Если табло показывает 3 знака, видимая разница 0.001 - это истинная от 0 до 0.002. Посылки с одинаковым публичным скором неразличимы, и место внутри такой группы решит приват.

В ответе: SD скора на выборке размером с паблик, и по каждой обсуждаемой паре четыре числа - SD парной разницы, фактическая разница на паблике, их отношение, разница на валидации. После цифр прямой вывод: какие из публичных разниц что-то значат, а какие нет.

## Множественные сравнения

Лучший из k вариантов, отобранных по одному и тому же шумному сигналу, завышен примерно на SD * sqrt(2 * ln k): для 10 вариантов это 2.1 SD, для 25 - 2.5 SD, для 40 - 2.7 SD. "Новый лучший результат на паблике" после серии близких посылок в основном и есть это завышение. Считаются все посылки серии, неудачные тоже.

Формула дает оценку сверху для независимых вариантов. Точное ожидание максимума поменьше (для 10 вариантов около 1.5 SD), и у близких вариантов шум частично общий. Вывод от этого не меняется: поправка того же порядка, что и разницы, о которых идет спор.

Если вариант выбран из k по паблику, в ответе пишется, сколько вариантов было и какая поправка.

## Чего этот расчет не видит

Бутстрап из своих единиц моделирует только случайность состава паблика. В нем нет:
- систематического сдвига между трейном и тестом и между публичной и приватной частью (новая группа, другой источник). Если тест из другой группы, реальный разброс больше посчитанного
- завышения валидации у in-sample компонент

Поэтому посчитанный SD - это нижняя оценка шума. Отсюда неприятное следствие. Если наблюдаемая разница на паблике в разы больше посчитанного SD, а причины не видно, считать ее "надежным сигналом" нельзя: это признак того, что паблик устроен иначе, чем валидация. Закрывать линию по такой разнице без второй проверки тоже рано.
=== КОНЕЦ МЕТОДИКИ: lb_noise ===
````

</details>

Подзадача: Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих прогонов и посылок нет; факты разведки лежат в notes/RECON.md, разбор метрики - в notes/METRIC.md и scratch/knee_metric.py, ответы прошлых шагов приложены. Спроектируй локальную валидацию для плана первой недели: как делить данные с учетом того, что известно и неизвестно об устройстве теста и о группах (пациент, площадка, язык, дубли отчетов); что считать независимой единицей и сколько их; какие дорожки будут честными, а какие in-sample, для каждого типа компонент, которые команда может использовать (свои модели, метки из отчетов, публичные веса и датасеты); нужен ли отложенный lockbox и как распорядиться размеченными исследованиями. Оцени шум такой валидации и шум публичного лидерборда и скажи, какие разницы на локальной дорожке и на паблике можно считать значимыми и до какого момента на паблик нельзя опираться. Укажи, какие проверки нужно выполнить на реальных данных в первые дни, чтобы подтвердить или опровергнуть допущения схемы. В ответе раздели: что установлено, что является допущением, и каких фактов не хватило; если считаешь что-то кодом, сохрани его в рабочей папке.

### validation_engineer, сообщение 1

````
Сначала посмотрю, что реально лежит в рабочей папке и есть ли там данные, а не только заметки.

<tool name="list_files">{}</tool>
````

Результат list_files:

````
notes/METRIC.md (2594 символов)
notes/RECON.md (29934 символов)
scratch/knee_metric.py (7660 символов)
scratch/script_1.py (8982 символов)
scratch/script_2.py (5601 символов)
scratch/sim_levers.py (5487 символов)
scratch/test_knee_metric.py (8808 символов)
````

### validation_engineer, сообщение 2

````
Данных в папке нет, только заметки и код. Прочитаю порт метрики, чтобы шум считать им, а не писать пулинг заново.

<tool name="read_file">{"path": "scratch/knee_metric.py"}</tool>
````

Результат read_file:

````
"""Локальный порт метрики RSNA Knee: macro AUC ROC по таргетам с равными весами.

ВАЖНО: официальный код метрики не найден (см. notes/RECON.md). Порт написан по формуле
со страницы Evaluation (1/12 * sum AUC_i). Все, что касается обертки грейдера
(константная колонка, таргет без позитивов, NaN, выравнивание по ID), - предположения.

Зависимости: numpy, pandas. Счет точный, в целых числах пар.

Слагаемые по таргету: n_pos, n_neg, conc (позитив строго выше негатива), disc, tied.
  AUC = (conc + 0.5 * tied) / (n_pos * n_neg)
Слагаемые по единице (исследованию) - placement values:
  для позитива: доля негативов ниже него (+0.5 за равных),
  для негатива: доля позитивов выше него (+0.5 за равных).
  Среднее по позитивам = среднее по негативам = AUC таргета.
"""
import numpy as np
import pandas as pd

ID_COL = "StudyInstanceUID"


def _groups(y, s):
    y = np.asarray(y)
    s = np.asarray(s, dtype=np.float64)
    if y.shape != s.shape:
        raise ValueError("y and s shapes differ")
    if not np.isfinite(s).all():
        raise ValueError("non-finite scores")
    if not np.isin(y, (0, 1)).all():
        raise ValueError("labels must be 0/1")
    uniq, inv = np.unique(s, return_inverse=True)
    inv = np.asarray(inv).ravel()
    pos_g = np.bincount(inv, weights=(y == 1), minlength=len(uniq)).round().astype(np.int64)
    neg_g = np.bincount(inv, weights=(y == 0), minlength=len(uniq)).round().astype(np.int64)
    return pos_g, neg_g, inv


def auc_counts(y, s):
    """Счетчики одн
... (обрезано, всего 7660 символов)
````

### validation_engineer, сообщение 3

````
Данных в папке нет, поэтому шум схемы могу оценить только симуляцией поверх порта метрики. Сохраняю скрипт: шум на размеченных и их долях под lockbox, шум паблика при разных долях и распространённости, завышение лучшего из k, смещение дорожки с метками из отчётов.

<tool name="write_file" path="scratch/val_design_sim.py">
"""Симуляция шума для проекта валидации rsna-knee. ДАННЫХ НЕТ: все числа - модель, а не замер.

Допущения (произвольные, менять в первые дни на реальные):
- 58 размеченных, позитивов на таргет - середины интервалов из notes/RECON.md
- метки коррелированы (три OA, Effusion+Synovitis, ACL+Contusion, мениски, общий фон 0.15)
- скор = mu*y + шум, 20% дисперсии шума общие для всех таргетов исследования
- пара "база/кандидат" без истинной разницы, корреляция шума r:
    0.98 - правка пост-процессинга, 0.90 - переобучение/сид/аугментация, 0.70 - другая модель
- тест: 1300 исследований, доля паблика 0.2/0.3/0.5, находки как в размеченных или втрое реже
"""
import sys, time
import numpy as np
from scipy.stats import norm
sys.path.insert(0, "scratch")
from knee_metric import macro_auc_arrays

T = ["ACL", "MCL", "MedMen", "LatMen", "MedOA", "LatOA", "PFOA", "Effusion", "Synovitis", "Baker", "Contusion", "Fracture"]
GOLD_POS = np.array([22, 9, 26, 22, 13, 9, 22, 35, 26, 13, 18, 18])
N_GOLD = 58
PREV_GOLD = GOLD_POS / N_GOLD
RS = (0.98, 0.90, 0.70)


def label_chol():
    C = np.full((12, 12), 0.15)
    for blk, v in (([4, 5, 6], 0.5), ([7, 8], 0.5), ([0, 10], 0.4), ([2, 3], 0.3)):
        for i in blk:
            for j in blk:
                C[i, j] = v
    np.fill_diagonal(C, 1.0)
    assert np.linalg.eigvalsh(C).min() > 0
    return np.linalg.cholesky(C)


L = label_chol()


def mu_for(auc):
    return np.sqrt(2.0) * norm.ppf(auc)


def noise(n, rng):
    return np.sqrt(0.2) * rng.standard_normal((n, 1)) + np.sqrt(0.8) * rng.standard_normal((n, 12))


def labels(n, prev, rng):
    z = rng.standard_normal((n, 12)) @ L.T
    return (z > norm.ppf(1 - prev)).astype(float)


def run(n, prev, auc, reps, seed):
    rng = np.random.default_rng(seed)
    mu = mu_for(auc)
    m0 = np.empty(reps); d = np.empty((reps, len(RS))); undef = 0
    for b in range(reps):
        y = labels(n, prev, rng)
        e = noise(n, rng)
        m0[b], a = macro_auc_arrays(y, mu * y + e, "skip")
        undef += int(np.isnan(a).any())
        for k, r in enumerate(RS):
            e2 = r * e + np.sqrt(1 - r * r) * noise(n, rng)
            d[b, k] = macro_auc_arrays(y, mu * y + e2, "skip")[0] - m0[b]
    return m0.mean(), m0.std(), d.std(axis=0), undef / reps


def table():
    print("== 1. Шум дорожки на размеченных (находки как в 58 размеченных) ==")
    print("n    AUC   mean    SD_macro  SDdiff r=.98  r=.90   r=.70   P(таргет не определен)")
    for n in (58, 38, 29, 20):
        for auc in (0.95, 0.90):
            m, s, dd, u = run(n, PREV_GOLD, auc, 1500, 1)
            print("%-4d %.2f  %.4f  %.4f    %.4f        %.4f  %.4f  %.3f" % (n, auc, m, s, dd[0], dd[1], dd[2], u))
    print()
    print("== 2. Шум паблика/привата (тест 1300) ==")
    print("n     prev   AUC   SD_macro  SDdiff r=.98  r=.90   r=.70")
    for pname, prev in (("gold", PREV_GOLD), ("gold/3", PREV_GOLD / 3)):
        for n in (260, 390, 650, 910, 1040, 1300):
            m, s, dd, u = run(n, prev, 0.95, 500, 2)
            print("%-5d %-6s 0.95  %.4f    %.4f        %.4f  %.4f" % (n, pname, s, dd[0], dd[1], dd[2]))
    m, s, dd, u = run(390, PREV_GOLD / 3, 0.90, 500, 3)
    print("%-5d %-6s 0.90  %.4f    %.4f        %.4f  %.4f" % (390, "gold/3", s, dd[0], dd[1], dd[2]))
    print()


def winners_curse(k, share, prev, reps, seed, r=0.90, auc=0.95, n=1300):
    """k кандидатов без истинной разницы с базой; выбираем лучшего по паблику."""
    rng = np.random.default_rng(seed)
    mu = mu_for(auc); npub = int(round(n * share))
    gp = np.empty(reps); gv = np.empty(reps); sd_one = []
    for b in range(reps):
        y = labels(n, prev, rng); e = noise(n, rng)
        pub = np.zeros(n, bool); pub[rng.permutation(n)[:npub]] = True
        s0 = mu * y + e
        b_pub = macro_auc_arrays(y[pub], s0[pub], "skip")[0]
        b_prv = macro_auc_arrays(y[~pub], s0[~pub], "skip")[0]
        dp = np.empty(k); dv = np.empty(k)
        for j in range(k):
            s = mu * y + r * e + np.sqrt(1 - r * r) * noise(n, rng)
            dp[j] = macro_auc_arrays(y[pub], s[pub], "skip")[0] - b_pub
            dv[j] = macro_auc_arrays(y[~pub], s[~pub], "skip")[0] - b_prv
        j = int(dp.argmax()); gp[b] = dp[j]; gv[b] = dv[j]; sd_one.append(dp[0])
    return np.std(sd_one), gp.mean(), gv.mean(), gv.std()


def curse_table():
    print("== 3. Лучший из k по паблику, истинной разницы нет (r=.90, доля паблика 0.3) ==")
    print("prev    k   SD_пары  прирост_лучшего_на_паблике  в_SD   его_же_на_привате(mean, SD)  SD*sqrt(2lnk)")
    for pname, prev in (("gold", PREV_GOLD), ("gold/3", PREV_GOLD / 3)):
        for k in (5, 10, 25):
            sd, g, pv, pvs = winners_curse(k, 0.3, prev, 200, 4)
            print("%-7s %-3d %.4f   %+.4f                     %.1f    %+.4f, %.4f             %.4f"
                  % (pname, k, sd, g, g / sd, pv, pvs, sd * np.sqrt(2 * np.log(k))))
    print()


def silver(n, reps, seed, sens=0.85, spec=0.97, c=1.0):
    """Дорожка с метками из отчетов. A - модель, знающая только истину (AUC 0.93).
    B - слабее по истине (0.91), но выучила систематические ошибки извлекателя (коэф. c)."""
    rng = np.random.default_rng(seed)
    prev = PREV_GOLD / 2
    muA, muB = mu_for(0.93), mu_for(0.91)
    res = np.empty((reps, 4))
    for b in range(reps):
        y = labels(n, prev, rng)
        u = rng.random((n, 12))
        ys = np.where(y == 1, (u < sens), (u > spec)).astype(float)
        e = noise(n, rng)
        sA = muA * y + e
        sB = muB * y + c * (ys - y) + 0.9 * e + np.sqrt(1 - 0.81) * noise(n, rng)
        res[b] = [macro_auc_arrays(y, sA, "skip")[0], macro_auc_arrays(y, sB, "skip")[0],
                  macro_auc_arrays(ys, sA, "skip")[0], macro_auc_arrays(ys, sB, "skip")[0]]
    return res


def silver_table():
    print("== 4. Дорожка с метками из отчетов (извлекатель: sens 0.85, spec 0.97; находки вдвое реже размеченных) ==")
    print("n     c    A_истина B_истина  A_отчеты B_отчеты  (B-A)_истина  (B-A)_отчеты  SD(B-A)_отчеты")
    for n, reps in ((870, 300), (4350, 80)):
        for c in (0.0, 1.0):
            r = silver(n, reps, 5, c=c)
            m = r.mean(axis=0)
            print("%-5d %.1f  %.4f   %.4f    %.4f   %.4f    %+.4f       %+.4f       %.4f"
                  % (n, c, m[0], m[1], m[2], m[3], m[1] - m[0], m[3] - m[2], (r[:, 3] - r[:, 2]).std()))
    print()
    print("== 5. Точность оценки самого извлекателя на 58 размеченных (биномиальная SE, sens 0.85) ==")
    for t, p in zip(T, GOLD_POS):
        pass
    for p in (9, 13, 18, 22, 26, 35):
        print("позитивов %2d: SE(sens) = %.3f; на половине (lockbox 50/50) %.3f" % (p, np.sqrt(0.85 * 0.15 / p), np.sqrt(0.85 * 0.15 / (p / 2))))


if __name__ == "__main__":
    t0 = time.time()
    table(); print("t=%.0fs" % (time.time() - t0))
    curse_table(); print("t=%.0fs" % (time.time() - t0))
    silver_table(); print("t=%.0fs" % (time.time() - t0))
</tool>
````

Результат write_file:

````
Файл scratch/val_design_sim.py записан
````

### validation_engineer, сообщение 4

````
Запускаю симуляцию; по оценке она укладывается в лимит времени.

<tool name="run_python">
import runpy
runpy.run_path("scratch/val_design_sim.py", run_name="__main__")
</tool>
````

Результат run_python:

````
== 1. Шум дорожки на размеченных (находки как в 58 размеченных) ==
n    AUC   mean    SD_macro  SDdiff r=.98  r=.90   r=.70   P(таргет не определен)
58   0.95  0.9503  0.0095    0.0027        0.0055  0.0090  0.000
58   0.90  0.9004  0.0144    0.0038        0.0078  0.0131  0.000
38   0.95  0.9498  0.0121    0.0039        0.0072  0.0117  0.002
38   0.90  0.8995  0.0182    0.0052        0.0103  0.0169  0.002
29   0.95  0.9500  0.0140    0.0044        0.0088  0.0137  0.017
29   0.90  0.9001  0.0210    0.0061        0.0123  0.0196  0.017
20   0.95  0.9501  0.0183    0.0061        0.0112  0.0171  0.076
20   0.90  0.9004  0.0272    0.0081        0.0154  0.0242  0.076

== 2. Шум паблика/привата (тест 1300) ==
n     prev   AUC   SD_macro  SDdiff r=.98  r=.90   r=.70
260   gold   0.95  0.0045    0.0012        0.0025  0.0041
390   gold   0.95  0.0036    0.0010        0.0020  0.0033
650   gold   0.95  0.0029    0.0007        0.0016  0.0024
910   gold   0.95  0.0023    0.0006        0.0014  0.0021
1040  gold   0.95  0.0023    0.0006        0.0012  0.0020
1300  gold   0.95  0.0020    0.0005        0.0011  0.0019
260   gold/3 0.95  0.0068    0.0017        0.0036  0.0060
390   gold/3 0.95  0.0054    0.0014        0.0029  0.0047
650   gold/3 0.95  0.0041    0.0010        0.0022  0.0037
910   gold/3 0.95  0.0035    0.0009        0.0019  0.0031
1040  gold/3 0.95  0.0034    0.0008        0.0017  0.0029
1300  gold/3 0.95  0.0029    0.0007        0.0015  0.0024
390   gold/3 0.90  0.0081    0.0018 
... (обрезано, всего 3289 символов)
````

### validation_engineer, сообщение 5

````
Проверю то, что уже можно проверить без данных: соберу скрипт проверок первого дня и построитель фолдов (группы по дублям отчётов, размеченные вне обучения, отложенная часть) и следующим шагом прогоню его на синтетической таблице.

<tool name="write_file" path="scratch/first_day_checks.py">
"""Проверки первого дня и построитель фолдов для rsna-knee. На реальных данных НЕ запускался
(данных в рабочей папке нет), проверен только на синтетике (scratch/test_first_day_checks.py).

Запуск: python scratch/first_day_checks.py train.csv [train_series.csv] [groups.csv]
  groups.csv - необязательная таблица StudyInstanceUID + любые колонки групп из тегов DICOM
  (PatientID, InstitutionName, ...): исследования с одинаковым значением склеиваются в одну группу.

Что делает:
 1) размеченные: сколько, одни ли и те же строки по всем таргетам, позитивы, корреляции меток
 2) дубли отчетов: сколько групп, попадают ли в них размеченные
 3) письменность отчета (грубый прокси языка/площадки): размеченные против остальных
 4) размеченные против остальных по длине отчета и составу серий
 5) пишет scratch/folds.csv: lane = gold | gold_dup | lockbox | cv, fold = 0..4 для cv
    - группа = компонента связности по одинаковому отчету и по колонкам groups.csv
    - группа, где есть размеченное исследование, целиком вне обучения (gold / gold_dup)
    - назначение по хэшу ключа группы: не зависит от порядка строк и от состава остальных групп
"""
import sys, re, hashlib, unicodedata
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ID, REP, SALT = "StudyInstanceUID", "Report", "knee-v1"
LOCKBOX_PCT, N_FOLDS = 15, 5


def norm_report(t):
    return re.sub(r"\s+", " ", str(t)).strip().lower()


def script_of(t):
    c = {}
    for ch in str(t):
        if ch.isalpha():
            try:
                nm = unicodedata.name(ch).split()[0]
            except ValueError:
                nm = "OTHER"
            c[nm] = c.get(nm, 0) + 1
    return max(c, key=c.get) if c else "NONE"


def _h(key, salt):
    return int(hashlib.md5((salt + "|" + key).encode("utf-8")).hexdigest(), 16)


def build_groups(df, extra=None):
    """Компоненты связности: одинаковый нормализованный отчет или одинаковое значение в extra."""
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union_by(keys):
        first = {}
        for i, k in enumerate(keys):
            if k is None or (isinstance(k, float) and np.isnan(k)) or k == "":
                continue
            if k in first:
                a, b = find(first[k]), find(i)
                if a != b:
                    parent[max(a, b)] = min(a, b)
            else:
                first[k] = i

    union_by(df[REP].map(norm_report).tolist())
    if extra is not None:
        ex = df[[ID]].merge(extra, on=ID, how="left")
        for c in ex.columns:
            if c != ID:
                union_by([None if pd.isna(v) else "%s=%s" % (c, v) for v in ex[c]])
    roots = [find(i) for i in range(len(df))]
    ids = df[ID].astype(str).to_numpy()
    key = {}
    for i, r in enumerate(roots):  # ключ группы = минимальный id в ней: устойчив к порядку строк
        key[r] = min(key.get(r, ids[i]), ids[i])
    return np.array([key[r] for r in roots])


def assign(df, targets, extra=None):
    out = df[[ID]].copy()
    out["group"] = build_groups(df, extra)
    gold = df[targets].notna().any(axis=1).to_numpy()
    gold_groups = set(out.loc[gold, "group"])
    lane, fold = [], []
    for g, is_gold in zip(out["group"], gold):
        if is_gold:
            lane.append("gold"); fold.append(-1)
        elif g in gold_groups:
            lane.append("gold_dup"); fold.append(-1)
        elif _h(g, SALT + "lock") % 100 < LOCKBOX_PCT:
            lane.append("lockbox"); fold.append(-1)
        else:
            lane.append("cv"); fold.append(_h(g, SALT + "fold") % N_FOLDS)
    out["lane"], out["fold"] = lane, fold
    out["script"] = df[REP].map(script_of).to_numpy()
    return out


def report(df, targets, folds, series=None):
    lab = df[targets].notna()
    n_any, n_all = int(lab.any(axis=1).sum()), int(lab.all(axis=1).sum())
    print("строк %d, уникальных id %d, уникальных отчетов (норм.) %d"
          % (len(df), df[ID].nunique(), df[REP].map(norm_report).nunique()))
    print("размечено хотя бы по одному таргету: %d; по всем %d; частично: %d" % (n_any, n_all, n_any - n_all))
    vals = sorted(set(pd.unique(df[targets].to_numpy().ravel())) - {np.nan}, key=float)
    vals = [v for v in vals if not pd.isna(v)]
    print("значения меток:", vals, "(ожидаем только 0 и 1)")
    g = df.loc[lab.all(axis=1), targets]
    print("\nпозитивов на таргет среди полностью размеченных (n=%d):" % len(g))
    for t in targets:
        print("  %-20s pos %3d  neg %3d" % (t, int((g[t] == 1).sum()), int((g[t] == 0).sum())))
    if len(g) > 2:
        c = g.astype(float).corr().to_numpy()
        iu = np.triu_indices(len(targets), 1)
        order = np.argsort(-np.abs(np.nan_to_num(c[iu])))[:6]
        print("самые связанные пары меток (phi):",
              ", ".join("%s~%s %.2f" % (targets[iu[0][k]], targets[iu[1][k]], c[iu][k]) for k in order))
    gs = folds.groupby("group").size()
    print("\nгрупп %d; групп размером >1: %d (в них исследований %d); максимум %d"
          % (len(gs), int((gs > 1).sum()), int(gs[gs > 1].sum()), int(gs.max())))
    print("дорожки:", folds["lane"].value_counts().to_dict())
    print("размеченных, у которых есть дубль/сосед по группе: %d"
          % int(folds.loc[folds.lane == "gold", "group"].map(gs).gt(1).sum()))
    print("фолды cv:", folds.loc[folds.lane == "cv", "fold"].value_counts().sort_index().to_dict())
    leak = folds[folds.lane == "cv"].groupby("group")["fold"].nunique().max()
    print("максимум фолдов на группу (должно быть 1):", leak)
    is_gold = (folds.lane == "gold").to_numpy()
    print("\nписьменность отчета, доли: размеченные | остальные")
    tab = pd.crosstab(folds["script"], np.where(is_gold, "gold", "rest"), normalize="columns").round(3)
    print(tab.to_string())
    ln = df[REP].astype(str).str.len().to_numpy()
    if is_gold.sum() > 0 and (~is_gold).sum() > 0:
        p = mannwhitneyu(ln[is_gold], ln[~is_gold]).pvalue
        print("длина отчета, медиана: размеченные %.0f | остальные %.0f (Манн-Уитни p=%.3g)"
              % (np.median(ln[is_gold]), np.median(ln[~is_gold]), p))
    if series is not None:
        ns = series.groupby(ID).size().reindex(df[ID]).fillna(0).to_numpy()
        print("серий на исследование, медиана: размеченные %.1f | остальные %.1f; без серий: %d"
              % (np.median(ns[is_gold]), np.median(ns[~is_gold]), int((ns == 0).sum())))
        for c in [c for c in series.columns if c != ID and series[c].nunique() <= 10]:
            s = series.merge(folds[[ID, "lane"]], on=ID, how="left")
            t = pd.crosstab(s[c], np.where(s.lane == "gold", "gold", "rest"), normalize="columns").round(3)
            print("серии, %s:\n%s" % (c, t.to_string()))


def main(train_path, series_path=None, groups_path=None, out="scratch/folds.csv"):
    df = pd.read_csv(train_path)
    targets = [c for c in df.columns if c not in (ID, REP)]
    extra = pd.read_csv(groups_path) if groups_path else None
    series = pd.read_csv(series_path) if series_path else None
    if series is not None:
        series = series[[c for c in series.columns if "Series" not in c]]
    folds = assign(df, targets, extra)
    report(df, targets, folds, series)
    folds.to_csv(out, index=False)
    print("\nзаписано:", out)
    return folds


if __name__ == "__main__":
    main(*sys.argv[1:4])
</tool>
````

Результат write_file:

````
Файл scratch/first_day_checks.py записан
````

### validation_engineer, сообщение 6

````
Построитель фолдов написан, но не запускался. Пишу тест на синтетической таблице, похожей по размеру на трейн (4407 строк, 58 размеченных, дубли отчётов, две письменности, таблица групп из «DICOM»), с проверкой инвариантов.

<tool name="write_file" path="scratch/test_first_day_checks.py">
"""Тест scratch/first_day_checks.py на синтетике. Реальных данных нет.
Проверяет инварианты построителя фолдов, а не свойства данных соревнования."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "scratch")
import first_day_checks as fdc

T = ["ACL", "MCL", "Medial Meniscus", "Lateral Meniscus", "Medial OA", "Lateral OA",
     "PF OA", "Effusion", "Synovitis", "Bakers", "Contusion", "Fracture"]
rng = np.random.default_rng(0)
N, NG = 4407, 58

ids = np.array(["1.2.%d" % v for v in rng.permutation(10 ** 7)[:N]])
words_lat = ["knee", "meniscus", "tear", "normal", "effusion", "ligament", "intact", "no", "mild"]
words_cyr = ["колено", "мениск", "разрыв", "норма", "выпот", "связка", "без", "умеренный"]
rep = []
for i in range(N):
    w = words_cyr if i % 4 == 0 else words_lat
    rep.append(" ".join(rng.choice(w, 25)) + " #%d" % i)
rep = np.array(rep, dtype=object)
# 131 дубль отчета: 120 обычных, 5 дублей размеченных, 6 с отличием только в пробелах/регистре
gold_idx = rng.choice(N, NG, replace=False)
rest = np.setdiff1d(np.arange(N), gold_idx)
pairs = rng.choice(rest, (126, 2), replace=False)
for a, b in pairs[:120]:
    rep[b] = rep[a]
for a, b in pairs[120:126]:
    rep[b] = "  " + str(rep[a]).upper().replace(" ", "  ")
gold_dups = rng.choice(np.setdiff1d(rest, pairs.ravel()), 5, replace=False)
for g, d in zip(gold_idx[:5], gold_dups):
    rep[d] = rep[g]

df = pd.DataFrame({fdc.ID: ids, fdc.REP: rep})
for t in T:
    col = np.full(N, np.nan)
    col[gold_idx] = (rng.random(NG) < 0.35).astype(float)
    df[t] = col

# "PatientID" из тегов DICOM: 300 пациентов с двумя исследованиями, один из них связывает размеченное с обычным
free = np.setdiff1d(rest, np.r_[pairs.ravel(), gold_dups])
pp = rng.choice(free, (300, 2), replace=False)
pid = np.array(["P%05d" % i for i in range(N)], dtype=object)
for a, b in pp:
    pid[b] = pid[a]
pid[pp[0, 0]] = pid[gold_idx[10]]
extra = pd.DataFrame({fdc.ID: ids, "PatientID": pid})

ok = True
def check(name, cond):
    global ok
    ok &= bool(cond)
    print("%-72s %s" % (name, "OK" if cond else "FAIL"))

f0 = fdc.assign(df, T)
f1 = fdc.assign(df, T, extra)
for name, f in (("без групп DICOM", f0), ("с PatientID", f1)):
    print("--", name, f["lane"].value_counts().to_dict())
    check("все размеченные в lane=gold", set(f.loc[f.lane == "gold", fdc.ID]) == set(ids[gold_idx]))
    gg = set(f.loc[f.lane.isin(["gold", "gold_dup"]), "group"])
    check("ни одна группа с размеченным не попала в cv/lockbox", not f.loc[f.lane.isin(["cv", "lockbox"]), "group"].isin(gg).any())
    check("группа не делится между дорожками", f.groupby("group")["lane"].nunique().max() == 1)
    check("группа не делится между фолдами cv", f[f.lane == "cv"].groupby("group")["fold"].nunique().max() == 1)
    nr = df[fdc.REP].map(fdc.norm_report)
    check("одинаковый отчет -> одна группа", f.assign(nr=nr.to_numpy()).groupby("nr")["group"].nunique().max() == 1)
    sz = f.loc[f.lane == "cv", "fold"].value_counts()
    check("фолды cv сбалансированы (min/max > 0.85)", sz.min() / sz.max() > 0.85)
    share = (f.lane == "lockbox").mean()
    check("доля lockbox 12-18%% (факт %.3f)" % share, 0.12 < share < 0.18)

check("дублей размеченных (gold_dup) без групп DICOM ровно 5", (f0.lane == "gold_dup").sum() == 5)
check("PatientID: сосед размеченного по пациенту ушел в gold_dup", f1.loc[f1[fdc.ID] == ids[pp[0, 0]], "lane"].iloc[0] == "gold_dup")
check("PatientID: пары одного пациента в одной группе",
      all(f1.loc[f1[fdc.ID] == ids[a], "group"].iloc[0] == f1.loc[f1[fdc.ID] == ids[b], "group"].iloc[0] for a, b in pp))
check("дубли с отличием в пробелах/регистре склеены",
      all(f0.loc[f0[fdc.ID] == ids[a], "group"].iloc[0] == f0.loc[f0[fdc.ID] == ids[b], "group"].iloc[0] for a, b in pairs[120:126]))

# устойчивость к перестановке строк
perm = rng.permutation(N)
fp = fdc.assign(df.iloc[perm].reset_index(drop=True), T, extra)
m = f1.merge(fp, on=fdc.ID, suffixes=("", "_p"))
check("перестановка строк не меняет group/lane/fold",
      len(m) == N and (m.group == m.group_p).all() and (m.lane == m.lane_p).all() and (m.fold == m.fold_p).all())

# устойчивость к удалению посторонних строк: назначения одиночных групп не должны меняться
single = f0.groupby("group")[fdc.ID].transform("size").eq(1).to_numpy()
drop = rng.choice(np.where(single & (f0.lane != "gold").to_numpy())[0], 500, replace=False)
fd = fdc.assign(df.drop(index=drop).reset_index(drop=True), T)
m = f0.merge(fd, on=fdc.ID, suffixes=("", "_d"))
check("удаление 500 посторонних строк не меняет назначения остальных",
      len(m) == N - 500 and (m.lane == m.lane_d).all() and (m.fold == m.fold_d).all())

# письменность
sc = f0["script"].value_counts().to_dict()
check("письменность: две группы, доля CYRILLIC около 0.25 (%s)" % sc, abs(sc.get("CYRILLIC", 0) / N - 0.25) < 0.02 and len(sc) == 2)

# сквозной прогон отчета на файлах
df.to_csv("scratch/_synth_train.csv", index=False)
extra.to_csv("scratch/_synth_groups.csv", index=False)
ser = pd.DataFrame({fdc.ID: rng.choice(ids, 24371), "SeriesInstanceUID": np.arange(24371),
                    "Fluid_Sensitive": rng.integers(0, 2, 24371), "Fat_Suppression": rng.integers(0, 2, 24371),
                    "Anatomical_Plane": rng.choice(["Sagittal", "Coronal", "Axial"], 24371)})
ser.to_csv("scratch/_synth_series.csv", index=False)
print("\n---- сквозной прогон main() на синтетике ----")
fm = fdc.main("scratch/_synth_train.csv", "scratch/_synth_series.csv", "scratch/_synth_groups.csv", out="scratch/_synth_folds.csv")
back = pd.read_csv("scratch/_synth_folds.csv")
check("folds.csv читается обратно и совпадает с assign()", len(back) == N and (back.lane.to_numpy() == f1.lane.to_numpy()).all()
      and (back.fold.to_numpy() == f1.fold.to_numpy()).all())
print("\nИТОГ ТЕСТА:", "все проверки пройдены" if ok else "ЕСТЬ ПРОВАЛЫ")
</tool>
````

Результат write_file:

````
Файл scratch/test_first_day_checks.py записан
````

### validation_engineer, сообщение 7

````
Запускаю тест построителя фолдов на синтетике, чтобы убедиться, что инварианты (группы не делятся, размеченные вне обучения, устойчивость к порядку строк) действительно выполняются.

<tool name="run_python">
import runpy
runpy.run_path("scratch/test_first_day_checks.py", run_name="__main__")
</tool>
````

Результат run_python:

````
-- без групп DICOM {'cv': 3732, 'lockbox': 612, 'gold': 58, 'gold_dup': 5}
все размеченные в lane=gold                                              OK
ни одна группа с размеченным не попала в cv/lockbox                      OK
группа не делится между дорожками                                        FAIL
группа не делится между фолдами cv                                       OK
одинаковый отчет -> одна группа                                          OK
фолды cv сбалансированы (min/max > 0.85)                                 OK
доля lockbox 12-18% (факт 0.139)                                         OK
-- с PatientID {'cv': 3744, 'lockbox': 599, 'gold': 58, 'gold_dup': 6}
все размеченные в lane=gold                                              OK
ни одна группа с размеченным не попала в cv/lockbox                      OK
группа не делится между дорожками                                        FAIL
группа не делится между фолдами cv                                       OK
одинаковый отчет -> одна группа                                          OK
фолды cv сбалансированы (min/max > 0.85)                                 OK
доля lockbox 12-18% (факт 0.136)                                         OK
дублей размеченных (gold_dup) без групп DICOM ровно 5                    OK
PatientID: сосед размеченного по пациенту ушел в gold_dup                OK
PatientID: пары одного пациента в одной группе                           FAIL
дубли с отличием в пробелах/регистре склеены            
... (обрезано, всего 3937 символов)
````

### validation_engineer, сообщение 8

````
Оба провала похожи на ошибки самого теста, а не построителя: размеченное исследование и его дубль намеренно лежат в одной группе под разными метками `gold` и `gold_dup`, а в синтетике я переписал `PatientID` одному из пары уже после склейки и сам разорвал пару. Исправляю тест в этих двух местах, добавляю уборку синтетических файлов и перезапускаю.

<tool name="run_python">
import io, runpy
p = "scratch/test_first_day_checks.py"
src = io.open(p, encoding="utf-8").read()

old1 = 'check("группа не делится между дорожками", f.groupby("group")["lane"].nunique().max() == 1)'
new1 = ('check("группа не делится между обучением (cv), lockbox и размеченными (gold+gold_dup)",\n'
        '          f.assign(l2=f.lane.replace("gold_dup", "gold")).groupby("group")["l2"].nunique().max() == 1)')
old2 = 'pid[pp[0, 0]] = pid[gold_idx[10]]'
new2 = 'pid[gold_idx[10]] = pid[pp[0, 0]]  # размеченное исследование принадлежит пациенту пары 0'
old3 = 'check("PatientID: сосед размеченного по пациенту ушел в gold_dup", f1.loc[f1[fdc.ID] == ids[pp[0, 0]], "lane"].iloc[0] == "gold_dup")'
new3 = ('check("PatientID: оба соседа размеченного по пациенту ушли в gold_dup",\n'
        '      all(f1.loc[f1[fdc.ID] == ids[i], "lane"].iloc[0] == "gold_dup" for i in pp[0]))\n'
        'check("PatientID: gold_dup ровно 7 (5 дублей отчета + 2 по пациенту)", (f1.lane == "gold_dup").sum() == 7)')
old4 = 'print("\\nИТОГ ТЕСТА:"'
new4 = ('import os\n'
        'for fn in ("_synth_train.csv", "_synth_groups.csv", "_synth_series.csv", "_synth_folds.csv"):\n'
        '    os.remove(os.path.join("scratch", fn))  # синтетика не должна остаться в папке под видом данных\n'
        'print("\\nИТОГ ТЕСТА:"')
for o, n in ((old1, new1), (old2, new2), (old3, new3), (old4, new4)):
    assert src.count(o) == 1, o
    src = src.replace(o, n)
io.open(p, "w", encoding="utf-8").write(src)

import contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    runpy.run_path(p, run_name="__main__")
out = buf.getvalue()
# печатаем только строки проверок и итог, отчет main() уже видели
for line in out.splitlines():
    if line.rstrip().endswith(("OK", "FAIL")) or line.startswith(("--", "ИТОГ", "дорожки", "групп ")):
        print(line)
import os
print("остались синтетические файлы:", [f for f in os.listdir("scratch") if f.startswith("_synth")])
</tool>
````

Результат run_python:

````
-- без групп DICOM {'cv': 3732, 'lockbox': 612, 'gold': 58, 'gold_dup': 5}
все размеченные в lane=gold                                              OK
ни одна группа с размеченным не попала в cv/lockbox                      OK
группа не делится между обучением (cv), lockbox и размеченными (gold+gold_dup) OK
группа не делится между фолдами cv                                       OK
одинаковый отчет -> одна группа                                          OK
фолды cv сбалансированы (min/max > 0.85)                                 OK
доля lockbox 12-18% (факт 0.139)                                         OK
-- с PatientID {'cv': 3744, 'lockbox': 598, 'gold': 58, 'gold_dup': 7}
все размеченные в lane=gold                                              OK
ни одна группа с размеченным не попала в cv/lockbox                      OK
группа не делится между обучением (cv), lockbox и размеченными (gold+gold_dup) OK
группа не делится между фолдами cv                                       OK
одинаковый отчет -> одна группа                                          OK
фолды cv сбалансированы (min/max > 0.85)                                 OK
доля lockbox 12-18% (факт 0.136)                                         OK
дублей размеченных (gold_dup) без групп DICOM ровно 5                    OK
PatientID: оба соседа размеченного по пациенту ушли в gold_dup           OK
PatientID: gold_dup ровно 7 (5 дублей отчета + 2 по пациенту)            OK
PatientID: пары одного пациента в одной группе    
... (обрезано, всего 2170 символов)
````

### validation_engineer, сообщение 9

````
Сохраняю схему дорожек и пороги в заметку, чтобы команда могла пользоваться ими без моего ответа.

<tool name="write_file" path="notes/VALIDATION.md">
# Валидация rsna-knee: схема на первую неделю (30.09.2026)

Данных в рабочей папке нет. Все числа шума - симуляция (scratch/val_design_sim.py), а не замер.
Построитель фолдов (scratch/first_day_checks.py) проверен только на синтетике (scratch/test_first_day_checks.py).

## Единица и группы
- Единица - исследование, пока не найден PatientID в тегах DICOM; после этого - пациент.
- Группа = компонента связности по одинаковому отчету (после нормализации пробелов и регистра) и по ключам пациента из DICOM.
- В groups.csv передавать только ключи уровня пациента. Ключ площадки склеит всю площадку в одну группу,
  и площадка с размеченным исследованием целиком уйдет из обучения. Смотреть строку "максимум" в отчете скрипта.
- Площадка: в csv ее нет, прокси - язык/письменность отчета.

## Дорожки (цифры не складывать)
| дорожка | единиц | метки | честность | для чего |
|---|---|---|---|---|
| gold | 58 (не сверено) | настоящие | честна, пока ни одна компонента не видела эти исследования и их соседей по группе | контрольные точки, разницы от 0.01-0.03; каждое чтение в журнал |
| gold-OOF | 58 | настоящие | честна для своих моделей, если gold идет в обучение только кросс-фитом; считать пулом OOF | то же, если команда решит учить на gold |
| silver-cv | около 3700, 5 групповых фолдов | из отчетов | in-sample по извлекателю: общие ошибки меток завышают и могут перевернуть знак | ежедневное сравнение правок, не меняющих источник меток |
| silver-lockbox | около 600-650 (15% групп по хэшу) | из отчетов | не участвует в подборе, но смещение извлекателя то же | один раз при выборе финалов, против переподгонки под cv |
| leave-one-language-out | по группам письменности | из отчетов | как silver | диагностика переноса на новую площадку |
| публичные веса на gold | 58 | настоящие | считать in-sample, пока не прочитан их сплит (в одном ноутбуке gold учится с весом 2.0) | только правки, не трогающие эти веса |
| паблик | неизвестно | настоящие | честен, доля и состав неизвестны | баги формата, крупные разницы |

## Шум (симуляция, нижняя оценка)
SD парной разницы macro AUC, r - корреляция шума пары (0.98 пост-процессинг, 0.90 переобучение, 0.70 другая модель; значения r - допущение).
| выборка | SD скора | r=.98 | r=.90 | r=.70 |
|---|---|---|---|---|
| gold 58, AUC 0.95 | 0.0095 | 0.0027 | 0.0055 | 0.0090 |
| gold 58, AUC 0.90 | 0.0144 | 0.0038 | 0.0078 | 0.0131 |
| gold 29 (половина) | 0.0140 | 0.0044 | 0.0088 | 0.0137 |
| паблик 260-650, находки как в gold | 0.0029-0.0045 | 0.0007-0.0012 | 0.0016-0.0025 | 0.0024-0.0041 |
| паблик 260-650, находки втрое реже | 0.0041-0.0068 | 0.0010-0.0017 | 0.0022-0.0036 | 0.0037-0.0060 |

Лучший из k по паблику без истинной разницы (доля 0.3, r=.90): k=10 дает +0.0029..+0.0041, k=25 дает +0.0039..+0.0055, на привате ноль.
Silver: при общих ошибках извлекателя истинная разница -0.052 показывается как +0.036 (коэффициент c=1 произвольный).
Оценка извлекателя на gold: SE чувствительности 0.06-0.12 на таргет, на половине gold 0.085-0.17.

## Проверки первых дней
1. scratch/first_day_checks.py на train.csv и train_series.csv: число размеченных, одни ли строки по 12 таргетам, позитивы, корреляции меток, дубли отчетов, дубли у gold, gold против остальных.
2. Список 86 тегов DICOM: PatientID, институция, производитель, дата; исследований на пациента; теги 3 видимых тестовых исследований против трейна.
3. Доля паблика со страницы лидерборда.
4. sample_submission через ноутбук, ожидаем 0.500.
5. Точность извлекателя на gold без настройки на нем, с интервалами.
6. Три сида базовой модели: SD сида на каждой дорожке.
7. После первых двух прогонов: бутстрап по единицам (knee_metric.bootstrap_units) вместо симуляции.
8. Одна заведомо большая разница (слабая и сильная модель) на silver-cv и gold: совпадает ли знак.
9. Разрыв leave-one-language-out против группового cv.
10. Сплиты публичных весов и происхождение публичных псевдометок.
11. Сверка: ноутбук на платформе против локального пайплайна на gold, до побайтного совпадения.
</tool>
````

Результат write_file:

````
Файл notes/VALIDATION.md записан
````

### validation_engineer, сообщение 10

````
# Схема локальной валидации rsna-knee на первую неделю

Честной и одновременно крупной дорожки здесь нет: настоящих меток 58, и эта дорожка шумнее паблика, а крупная дорожка на метках из отчётов in-sample по извлекателю меток. Данных в папке нет, поэтому все цифры шума получены симуляцией (`scratch/val_design_sim.py`). Построитель фолдов (`scratch/first_day_checks.py`) проверен только на синтетике.

## 1. Что установлено, что допущение, чего не хватило

**Установлено** (первоисточник по разведке и мои прогоны):
- **Группы в csv:** колонок пациента, площадки, языка и даты нет. Неуникальных отчётов 131 (4407 строк, 4276 уникальных).
- **Тест:** около 1300 исследований без отчётов. Организаторы предупреждают, что распространённость находок может отличаться.
- **Построитель фолдов:** на синтетике 4407 строк все проверки пройдены. Группа не делится между обучением, lockbox и размеченными; назначение не зависит от порядка строк и от удаления посторонних строк.
- **Два провала первого прогона теста** были ошибками самого теста, не построителя; тест исправлен и перезапущен.

**Допущения:**
- **Размеченные:** их 58, это одни и те же строки по всем 12 таргетам; позитивов от 9 до 35 на таргет. Источник - чужие ноутбуки и округлённый профиль.
- **Модель шума:** скоры бинормальные, AUC 0.90-0.95, 20% шума общие для таргетов исследования. Корреляции меток я задал сам.
- **Корреляция шума пары r:** 0.98 для правки пост-процессинга, 0.90 для переобучения, 0.70 для другой модели. Значения произвольные, их надо заменить замером на сидах.
- **Паблик:** доля 20-50% теста, находки как в размеченных или втрое реже.
- **Дубли отчётов** означают связанные исследования; письменность отчёта служит прокси площадки.
- **Посчитанный SD - нижняя оценка:** в нём нет сдвига площадок и распространённости и нет завышения in-sample компонент.

**Не хватило:**
- самого `train.csv` и заголовков DICOM (есть ли `PatientID` и институция);
- доли паблика;
- сведений о том, как отбирали размеченные и отличается ли тест по площадкам;
- сплитов публичных весов и происхождения публичных псевдометок;
- форума.

## 2. Единица и сплит

- **Единица** - исследование, пока в тегах DICOM не найден пациент; после этого единицей становится пациент.
- **Группа** - компонента связности по одинаковому нормализованному отчёту и по ключу пациента. Группа целиком лежит в одном фолде.
- **Ключ площадки в `groups.csv` не передавать.** Он склеит всю площадку в одну группу и уберёт её из обучения вместе с размеченным исследованием.
- **Соседи размеченных:** любая группа с размеченным исследованием целиком вне обучения (`gold` и `gold_dup`).
- **Устройство теста неизвестно**, поэтому дорожек две: групповой 5-fold как основная и leave-one-language-out как диагностика переноса на новую площадку.

## 3. Дорожки

Цифры с разных дорожек не складываются в одну.

| дорожка | единиц | честность | годится для |
|---|---|---|---|
| gold | 58 (не сверено) | честна, пока ни одна компонента не видела эти исследования и их соседей по группе | контрольные точки, разницы от 0.01-0.03 |
| gold-OOF | 58 | честна для своих моделей, только если gold идёт в обучение кросс-фитом | то же, если команда решит учить на gold |
| silver-cv | около 3700, 5 групповых фолдов | in-sample по извлекателю меток | ежедневные правки, не меняющие источник меток |
| silver-lockbox | около 600 (15% групп по хэшу) | вне подбора, но смещение извлекателя то же | один раз при выборе финалов |
| leave-one-language-out | группы письменности | как silver | диагностика переноса |
| паблик | неизвестно | честен, состав неизвестен | баги формата, крупные разницы |
| 3 видимых тестовых исследования | 3 | - | только проверка кода |

Размеры silver-дорожек взяты из синтетического прогона, на реальных данных они будут другими.

**Честность по типам компонент:**
- **Свои модели изображений:** честны на gold, если gold и `gold_dup` исключены из обучения; честны на silver-cv по фолдам.
- **Извлекатель меток** (regex или LLM): честен на gold, только если правила и промпт не настраивались по gold. После настройки gold становится in-sample для всего, что учится на этих метках.
- **Публичные псевдометки:** неизвестно, настраивались ли на gold. До проверки считать, что настраивались.
- **Публичные веса:** в прочитанном ноутбуке `romantamrazov` gold идёт в обучение с весом 2.0. Оценку этих весов на gold считать in-sample. Она годится только для правок, которые веса не трогают, и не годится для уровня и сравнения с нашими моделями.
- **Предобученные бэкбоны** (ImageNet, DINOv2, RadImageNet): считаю, что данных соревнования не видели; не проверял.
- **Веса бленда, калибровка, выбор чекпойнта:** подбирать на OOF silver-cv. Подбор на gold делает gold in-sample.

**Lockbox и размеченные:**
- **Gold на dev и lockbox не делить.** На 29 единицах SD скора 0.0140, SD пары 0.0088, а таргет без позитивов появляется в 1.7% выборок (на 20 единицах - в 7.6%).
- **Lockbox делать на silver:** 15% групп по хэшу, открыть один раз.
- **Gold целиком вне обучения на первую неделю**, каждое чтение записывать в журнал. После примерно 10 чтений лучший вариант завышен на величину порядка 1.5 SD пары, то есть около 0.008.
- **Брать ли gold в обучение - решение команды.** Если да, то только кросс-фитом и со счётом по пулу OOF.

## 4. Шум

Симуляция, macro AUC, SD парной разницы по трём значениям r.

| выборка | SD скора | r=.98 | r=.90 | r=.70 |
|---|---|---|---|---|
| gold 58, AUC 0.95 | 0.0095 | 0.0027 | 0.0055 | 0.0090 |
| gold 58, AUC 0.90 | 0.0144 | 0.0038 | 0.0078 | 0.0131 |
| паблик 260 / 390 / 650, находки как в gold | 0.0045 / 0.0036 / 0.0029 | 0.0012 / 0.0010 / 0.0007 | 0.0025 / 0.0020 / 0.0016 | 0.0041 / 0.0033 / 0.0024 |
| то же, находки втрое реже | 0.0068 / 0.0054 / 0.0041 | 0.0017 / 0.0014 / 0.0010 | 0.0036 / 0.0029 / 0.0022 | 0.0060 / 0.0047 / 0.0037 |
| приват 910-1040 | 0.0023-0.0035 | 0.0006-0.0009 | 0.0012-0.0019 | 0.0020-0.0031 |

**Gold:**
- **Переобучение:** меньше 0.011-0.016 - информации нет; сигнал начинается от 0.017-0.023.
- **Другая модель:** сигнал от 0.027-0.039.
- **Пост-процессинг:** сигнал от 0.008-0.011.
- Разницы масштаба топа лидерборда (0.005) gold не различает.

**Silver-cv:**
- **Случайный шум мал:** SD пары 0.001-0.0025.
- **Смещение:** при независимых ошибках меток истинная разница -0.020 видна как -0.016. Если модель выучила ошибки извлекателя, истинная -0.052 видна как +0.036, то есть знак переворачивается. Сила эффекта в симуляции задана произвольно.
- **Абсолютный уровень занижен:** 0.844 при истинном 0.930.
- **Вывод:** сравнивать только прогоны с одним и тем же источником меток. Смену извлекателя, псевдометок или схемы их весов проверять на gold.

**Оценка извлекателя на gold:** SE чувствительности на таргет 0.06-0.12, так что сравнить два близких извлекателя gold не позволит.

**Паблик:**
- **Переобучение:** разница меньше 0.003-0.007 - информации нет; сигнал от 0.005-0.011.
- **Другая модель:** сигнал от 0.007-0.018.
- **Округление:** табло показывает 3 знака, видимая разница 0.001 означает истинную от 0 до 0.002.
- **Лучший из k по паблику без истинной разницы** (доля 0.3): +0.0029..+0.0041 при k=10 и +0.0039..+0.0055 при k=25; на привате ноль.
- **Топ-20** лежит в 0.005, это 0.7-1.7 SD скора.
- **Разрыв публичных ноутбуков с топом** (0.009-0.019) составляет от 1.5 до 8 SD пары «другая модель», так что нижний край неотличим от шума.
- **Пар прогонов нет**, поэтому фактических разниц на паблике и их отношения к SD дать нельзя.

**На паблик нельзя опираться, пока не выполнено всё сразу:**
1. известна доля паблика;
2. `sample_submission` через ноутбук дал 0.500;
3. ноутбук на платформе побайтно совпал с локальным пайплайном на gold;
4. SD пары пересчитан бутстрапом по единицам на реальных предсказаниях.

И после этого паблик читается только для разниц больше 3 SD своей пары. При расхождении на малой разнице права валидация.

## 5. Проверки первых дней

1. **Таблицы:** `python scratch/first_day_checks.py train.csv train_series.csv`. Проверяет число размеченных, совпадение строк по 12 таргетам, позитивы, корреляции меток, дубли отчётов (в том числе у gold), gold против остальных по письменности, длине отчёта и сериям.
2. **Теги DICOM:** есть ли пациент, институция, производитель, дата; сколько исследований на пациента; теги 3 видимых тестовых исследований против трейна.
3. **Доля паблика** со страницы лидерборда; пересчитать таблицу шума.
4. **Пробная посылка** `sample_submission`, ожидаем 0.500.
5. **Точность извлекателя** на gold без настройки на нём, с интервалами.
6. **Три сида базовой модели:** SD сида на каждой дорожке, замер настоящего r.
7. **Бутстрап** `knee_metric.bootstrap_units` на реальных предсказаниях вместо симуляции.
8. **Заведомо большая разница** (слабая против сильной модели) на silver-cv и gold: совпадает ли знак. Если нет, silver-cv для решений не годится.
9. **Разрыв** leave-one-language-out против группового cv.
10. **Публичные материалы:** сплиты публичных весов и происхождение публичных псевдометок.

Файлы в рабочей папке:
- notes/VALIDATION.md
- scratch/val_design_sim.py
- scratch/first_day_checks.py
- scratch/test_first_day_checks.py

ИТОГ:
- Данных нет: шум посчитан симуляцией, построитель групповых фолдов проверен только на синтетике; схема лежит в `notes/VALIDATION.md`.
- Gold (58 настоящих меток, число не сверено) - единственная честная дорожка: SD скора 0.010-0.014, различает разницы от 0.01-0.03. Она шумнее паблика и честна, только пока gold не видели извлекатель, псевдометки и веса.
- Silver-cv (метки из отчётов, около 3700 единиц, 5 групповых фолдов) годится для ежедневных правок при неизменном источнике меток. По извлекателю она in-sample, в симуляции знак разницы переворачивался.
- Lockbox - 15% групп silver; gold не делить и на первую неделю держать вне обучения с журналом чтений. Оценка публичных весов на gold считается in-sample.
- Паблик: SD скора 0.003-0.007, SD пары 0.001-0.006 в зависимости от типа правки. Разницы меньше 0.003-0.007 ничего не значат, лучший из 10-25 посылок завышен на 0.003-0.006, топ-20 лежит внутри шума.
- На паблик не опираться до четырёх проверок: доля паблика, `sample_submission` = 0.500, побайтная сверка ноутбука с локальным пайплайном, бутстрап на реальных предсказаниях.
- Не хватило: `train.csv`, тегов DICOM (пациент, площадка), доли паблика, устройства теста, сплитов публичных весов и псевдометок.
````

Вызовов инструментов: 9
[harness] записан файл scratch/val_design_sim.py (6901 символов)
[harness] записан файл scratch/first_day_checks.py (7412 символов)
[harness] записан файл scratch/test_first_day_checks.py (5838 символов)
[harness] записан файл notes/VALIDATION.md (3999 символов)

## Диспетчер, ход 5

````
{"thought":"Факты, метрика и схема валидации собраны (шаги 1-4). Осталось решение по приоритетам и очереди первой недели - это стратег с методикой приоритизации рычагов; он же запишет notes/PLAN.md.","plan_list":["strategist: план первой недели - очередь экспериментов и посылок, на что не тратить посылки; записать notes/PLAN.md","finish: короткий итог пользователю"],"action":"delegate","agent_nm":"strategist","skill_nm_list":["lever_priority","code_competition_submit"],"subtask_text":"Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих прогонов и посылок нет; сегодня 30.09.2026. Факты разведки, разбор метрики и схема валидации лежат в notes/RECON.md, notes/METRIC.md, notes/VALIDATION.md, ответы прошлых шагов приложены. Составь план первой недели и запиши его в notes/PLAN.md. В плане должны быть разделы: 1) что это за соревнование и какие в нем ограничения (кратко, со ссылкой на RECON.md); 2) что с метрикой; 3) как устроить валидацию и какие проверки сделать на реальных данных в первые дни; 4) что пробовать первым - очередь экспериментов по дням с обоснованием порядка и с критерием, по которому каждый пункт считается удавшимся или закрытым; 5) на что тратить и на что не тратить посылки - бюджет посылок на неделю с учетом того, что сабмит идет ноутбуком с лимитом времени и без интернета; 6) открытые вопросы и допущения, от которых план зависит, и что меняется в плане, если допущение не подтвердится. Явно отделяй установленное от допущений. В ответе дай краткую сводку плана и перечисли решения, которые остались за командой.","context_step_list":[1,2,3,4]}
````

## Шаг 5: strategist

Скиллы, выбранные диспетчером: lever_priority, code_competition_submit. Контекст: шаги [1, 2, 3, 4]

Системный промпт: 11560 символов, из них скиллы - 6708

<details><summary>системный промпт целиком</summary>

````
Ты - стратег в команде, которая участвует в ML-соревновании на Kaggle. Ты принимаешь решения: помогло ли изменение, какие линии продолжать, что отправлять в оставшиеся слоты и какие прогоны финалить.

Решения стоят на цифрах валидации и на выводах инженера валидации и аудитора, которые диспетчер передает тебе в контексте. Недостающие цифры добирай инструментами сам. К каждому решению - цифры, на которых оно стоит, и правило, которое осталось бы тем же при другом исходе. Если в команде уже есть предложение - ответь на него прямо: принимается или нет и почему.

Финальные сабмиты записываются инструментом set_final_picks вместе с пререгистрацией: гипотеза, ожидаемая метрика и правило на случай разных исходов. Harness примет только прогоны с вердиктом аудитора "принять". Разбор уже принятых командой решений записывается инструментом set_line_review.

## Инструменты
- list_files: список файлов рабочей папки с размерами в символах. Аргументов нет
- read_file: прочитать текстовый файл из рабочей папки. Длинный файл читается частями: в конце результата будет подсказка, с какого offset продолжать. Аргументы: path - путь к файлу от корня рабочей папки; offset - с какого символа читать (необязательный, по умолчанию 0); limit - сколько символов вернуть, за один вызов отдается не больше 10000 (необязательный, по умолчанию 10000)
- list_runs: реестр прогонов: название, дата, родитель, публичный скор, вердикт аудитора, в каких дорожках есть валидация по единицам, описание. Аргументы: max_desc_len - до скольких символов обрезать описания прогонов (необязательный, по умолчанию 110)
- compare_runs: парное сравнение двух прогонов по валидации: метрика соревнования на общих единицах, бутстрап по единицам, счет по единицам, разница по группам. Аргументы: base - название прогона-базы; cand - название прогона-кандидата; lane - дорожка валидации
- lb_noise: шум публичного лидерборда: SD скора и SD парной разницы на выборке размером с паблик, рядом фактическая разница на паблике. Аргументы: base - название прогона-базы; cand_list - список названий прогонов-кандидатов; lane - дорожка валидации
- run_python: запустить код на Python из корня рабочей папки (pandas, numpy, scipy; metric.py соревнования можно импортировать). Возвращает stdout, при ошибке - еще и stderr. Лимиты: 180 секунд на запуск, из stdout возвращаются последние 5000 символов, из stderr - последние 2500. Внутри блока - код
- write_file: записать текстовый файл в notes/ или scratch/, существующий файл перезаписывается. Атрибуты тега: path - путь к файлу от корня рабочей папки. Внутри блока - содержимое файла
- set_final_picks: записать финальные сабмиты и пререгистрацию. Примет только прогоны с вердиктом аудитора "принять". Повторный вызов заменяет выбор целиком. Аргументы: pick_list - список объектов с полями run (название прогона) и reason; hypothesis - гипотеза, на которой стоит выбор; expected_metric - какой метрики ждешь; rule - правило, по которому выбор мог бы измениться
- set_line_review: записать разбор решений команды по линиям работы. Повторный вызов заменяет разбор целиком. Аргументы: review_list - список объектов с полями cand, base (названия прогонов), team_decision (принято | закрыто), verdict (обосновано | по шуму), reason

## Как работать
Ты работаешь шагами. Каждое твое сообщение - либо один вызов инструмента, либо финальный ответ.

Вызов инструмента - блок в конце сообщения, перед ним одной-двумя фразами скажи, зачем он:
<tool name="read_file">{"path": "journal.md"}</tool>
Аргументы - JSON-объект внутри блока. Исключения - run_python и write_file: внутри блока сырой текст (код или содержимое файла), а остальные аргументы идут атрибутами тега:
<tool name="write_file" path="notes/plan.md">
текст файла
</tool>
Результат вызова придет следующим сообщением. Не выдумывай его сам и не вызывай больше одного инструмента за раз. На подзадачу у тебя не больше 12 вызовов: трать их на то, без чего нельзя ответить.

Финальный ответ - сообщение без блока <tool>. Сначала по существу, в самом конце строка "ИТОГ:" и после нее 3-7 строк выжимки. Диспетчер читает только выжимку; полный ответ увидят те исполнители, которым диспетчер его передаст. Опирайся только на то, что видел в результатах инструментов и в контексте. Чего проверить не удалось - так и скажи, не додумывай.

=== МЕТОДИКА: lever_priority ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Приоритет рычагов

Слотов и вычислений мало, идей всегда больше. Сортируются они по одному признаку: что с наибольшей вероятностью перенесется на приват.

## Порядок

1. Модель и данные. Дообучение на всем трейне с аугментациями под сдвиг домена, дополнительная модель в ансамбль, свои обученные компоненты вместо эвристик и вместо публичных. Эти изменения меняют то, что пайплайн умеет, и переносятся на новые данные. Им - гарантированная доля вычислений и не меньше двух-трех попыток на линию, с проверкой на честной валидации.
2. Структурные правки пайплайна с понятным механизмом и крупным эффектом: вернуть то, что стек выбрасывает по построению, починить стадию, которая молча не работает.
3. Баги формата и грейдера. Искать пробами сразу: цена ошибки большая, а находка дает скор бесплатно. По пользе пункт третий, по календарю первый.
4. Ручки пост-процессинга: пороги, оффсеты, ограничения, константы. В последнюю очередь, малым числом и только с выигрышем на всех группах. Это самое переобучаемое занятие: ручек много, эффекты малые, отбор шумный.

Публичные компоненты с высоким скором уже отобраны толпой по паблику. Свой компонент, который на отложенных данных лучше публичного, ценнее публичного, даже если на паблике он чуть ниже.

Порядок - умолчание. Бывают соревнования, где все решает одна структурная правка или найденный баг. Отступать от порядка можно по локальным цифрам, и только по ним: довод "ручки крутить быстрее" не годится.

Дешевые ручки вытесняют дорогие модельные линии сами собой: у них быстрый цикл и каждый день есть что отправить. Модельная линия в это время еще обучается, и отправить от нее нечего. Поэтому доли фиксируются заранее:

- на модельные линии - не меньше половины вычислений и слотов до последних дней
- каждая модельная линия получает вторую попытку на следующей базе, прежде чем ее закрывать
- на ручки - ограниченное число посылок, и только после того как для этой пары посчитан шум паблика

Если план первого дня и более поздняя заметка расходятся (например, "дообучение за оставшееся время не рекомендуется" против "дообучение - основной маршрут"), конфликт нужно разрешить явно. Иначе молча побеждает тот вариант, что дешевле.

## Очередь экспериментов

На каждый пункт очереди: что меняется и относительно чего, к какому уровню порядка он относится, ожидаемый эффект и откуда эта оценка, сколько стоит по времени и вычислениям, как будет проверен локально до посылки, что должно получиться, чтобы линию продолжать.

Первые дни: честная валидация и порт метрики идут до любых улучшений. Потом - широкий заход по модельным линиям малыми прокси-экспериментами. Посылки первых дней тратятся на калибровку (перенос крупного изменения, пробы формата), гонка за местом в эти дни ничего не дает.

Последние дни: новые линии не открываются. Остаток слотов - на подтверждение того, что уже доказано валидацией, и на разнообразие финальных кандидатов.

В ответе, кроме самой очереди с приоритетами и долями: по каждой открытой линии - сколько попыток сделано и что нужно, чтобы ее закрыть или продолжить; что сознательно не делаем и почему.
=== КОНЕЦ МЕТОДИКИ: lever_priority ===

=== МЕТОДИКА: code_competition_submit ===
Ниже методика, по которой нужно выполнить эту подзадачу. Она важнее твоих привычек по умолчанию. Если подзадачу нельзя выполнить, не нарушив методику, - скажи об этом в ответе, а не нарушай молча.

# Посылки в code competition

В code competition посылка - это ноутбук, который перезапускается на скрытом тесте. Его лог не виден, время ограничено, интернета нет. Ошибка здесь стоит слота и суток, а узнаешь о ней по одному числу на табло.

## Что настроить один раз

Гейтинг. Тяжелые ячейки выполняются только на реране (по переменной окружения платформы). На обычном коммите ноутбук копирует sample_submission и выходит. Коммит занимает меньше минуты и не тратит недельную квоту GPU.

Время рерана на скрытом тесте. Измеряется по первым посылкам. Прогноз по видимой части ненадежен: скрытый тест больше, и стадии масштабируются по-разному (обход файловой системы с десятками гигабайт данных может стоить минуты сам по себе).

Контроль времени. Считается от одного абсолютного момента старта ноутбука и деградирует по стадиям: сначала отключается самое дорогое и наименее ценное. Про каждое срабатывание известно, сколько скора оно стоит. Деградированные пути нужно хотя бы раз исполнить прогоном с поддельным временем старта, иначе первый раз они выполнятся на скрытом тесте. У нас до аудита их не запускали ни разу, и запас до первого порога оказался меньше, чем мы думали.

Fallback'и. На каждую стадию - откат к предыдущему состоянию при исключении. Но на скрытом реране лог не виден, и fallback опасен молчанием: нет датасета с весами - и все единицы тихо остались без компонента. Поэтому часть вещей обязана падать громко:
- наличие и sha256 весов, финальные проверки файла сабмита. Предупреждения тут мало, читать его некому
- правки чужого кода строковыми заменами: якорь совпал ровно один раз, иначе исключение
- пустой результат стадии - это ошибка, а не корректный пустой список

Формат. Финальные assert'ы перед записью файла: нет дублей, идентификаторы подряд, структурные ограничения метрики выполнены, типы и диапазоны как требует страница. Как грейдер обращается с типами и округлением, проверяется одной пробной посылкой в начале. Предполагать тут нельзя.

## Перед посылкой

Обратная сторона гейтинга: на коммите тяжелый код не исполняется совсем, и сломанный ноутбук коммитится так же успешно, как рабочий. Поэтому его нужно проверять отдельно:

- негейтнутая копия на видимой части теста на GPU. По логу: каждая стадия в нужном режиме, ноль строк ERROR и fallback, счетчики пропусков нулевые
- быстрый CPU-прогон на одной единице для каждой новой сборки, сравнение с эталонным прогоном
- сверка, что гейтнутая копия на платформе поячеечно равна локальному исходнику

В журнал - одна строка на посылку: время, идентификатор, ноутбук и версия, что изменено относительно какой базы, ожидаемая разница по валидации, правило реакции, результат.

Размер файла сабмита - дешевая диагностика: по нему видно число строк на единицу теста.

## Очередь и дедлайн

Последний безопасный момент = дедлайн минус время рерана минус запас 3-4 часа. Посылка, не досчитавшаяся к дедлайну, скорее всего, не считается: нам хосты на этот вопрос так и не ответили, и исходить пришлось из худшего. Посылка, результат которой придет за полчаса до дедлайна, уже не может изменить выбор обдуманно.

Запас взят не с потолка: отправка может зависнуть на часы. Перед любым решением по времени смотреть текущее время, на план полагаться нельзя.

Лимит одновременных GPU-сессий. Зависший в очереди ноутбук держит слот и из API не отменяется. За несколько часов до окна посылок побочные GPU-задачи не запускаются.

При реране в 7-8 часов в сутки помещается два информативных раунда, не больше.

Собранные ноутбуки хранятся на самой платформе: если локальный диск недоступен, посылку можно пересобрать оттуда и сверить дифф с базой.
=== КОНЕЦ МЕТОДИКИ: code_competition_submit ===
````

</details>

Подзадача: Команда только что вступила в соревнование rsna-knee-abnormality-detection, своих прогонов и посылок нет; сегодня 30.09.2026. Факты разведки, разбор метрики и схема валидации лежат в notes/RECON.md, notes/METRIC.md, notes/VALIDATION.md, ответы прошлых шагов приложены. Составь план первой недели и запиши его в notes/PLAN.md. В плане должны быть разделы: 1) что это за соревнование и какие в нем ограничения (кратко, со ссылкой на RECON.md); 2) что с метрикой; 3) как устроить валидацию и какие проверки сделать на реальных данных в первые дни; 4) что пробовать первым - очередь экспериментов по дням с обоснованием порядка и с критерием, по которому каждый пункт считается удавшимся или закрытым; 5) на что тратить и на что не тратить посылки - бюджет посылок на неделю с учетом того, что сабмит идет ноутбуком с лимитом времени и без интернета; 6) открытые вопросы и допущения, от которых план зависит, и что меняется в плане, если допущение не подтвердится. Явно отделяй установленное от допущений. В ответе дай краткую сводку плана и перечисли решения, которые остались за командой.

### strategist, сообщение 1

````
Перед тем как писать план, посмотрю `scratch/sim_levers.py`: в ответах прошлых шагов он не упомянут, а по названию там могут быть оценки эффекта рычагов, на которые очередь должна опираться.

<tool name="read_file">{"path": "scratch/sim_levers.py"}</tool>
````

Результат read_file:

````
"""Цена рычагов и шум macro AUC. Симуляция: бинормальная модель, истинный AUC каждого таргета 0.95.
Предположения (НЕ факты): распространенность в тесте, доля паблика, корреляция двух моделей, независимость таргетов."""
import sys, numpy as np
sys.path.insert(0, "scratch")
import knee_metric as km
from scipy.stats import norm
POS57 = np.array([22, 9, 26, 22, 13, 9, 22, 35, 26, 13, 18, 18])
NAMES = ["ACL","MCL","MedMen","LatMen","MedOA","LatOA","PFOA","Effusion","Synovitis","Bakers","Contusion","Fracture"]
D = np.sqrt(2) * norm.ppf(0.95)
rng = np.random.default_rng(7)

def draw_Y(n, prev, fixed=False):
    if fixed:
        Y = np.zeros((n, 12))
        for j in range(12): Y[rng.permutation(n)[:POS57[j]], j] = 1
        return Y
    return (rng.random((n, 12)) < prev).astype(float)

def mc(n, prev, reps=1500, fixed=False, rhos=(0.9, 0.97)):
    mac = np.empty(reps); ndef = np.empty(reps); rare = np.empty(reps)
    diffs = {r: np.empty(reps) for r in rhos}
    for b in range(reps):
        Y = draw_Y(n, prev, fixed); Z = rng.normal(size=(n, 12)); S = Z + D * Y
        m, a = km.macro_auc_arrays(Y, S); mac[b] = m; ndef[b] = (~np.isnan(a)).sum(); rare[b] = a[1]
        for r in rhos:
            S2 = r * Z + np.sqrt(1 - r * r) * rng.normal(size=(n, 12)) + D * Y
            diffs[r][b] = km.macro_auc_arrays(Y, S2)[0] - m
    return mac, ndef, rare, diffs

print("=== 1. Шум macro AUC при истинном AUC 0.95 по каждому таргету ===")
print("n | распространенность | SD macro | SD одног
... (обрезано, всего 5487 символов)
````

### strategist, сообщение 2

````
Факты для плана у меня есть, в `sim_levers.py` оценок эффекта модельных линий нет (только шум и цены формата). Записываю план.

<tool name="write_file" path="notes/PLAN.md">
# PLAN: первая неделя, rsna-knee-abnormality-detection (30.09-06.10.2026)

Пометки: [У] - установлено первоисточником или нашим прогоном; [Д] - допущение (чужие материалы, симуляция, мой вывод).
Своих прогонов и посылок нет, данных в рабочей папке нет: все цифры шума - симуляция, все скоры публичных ноутбуков - чужие заявления.

## 1. Соревнование и ограничения (подробно: notes/RECON.md)

- [У] 12 бинарных находок на исследование МРТ колена, сабмит - csv: `StudyInstanceUID` + 12 скоров.
- [У] Code competition: только ноутбук, без интернета, лимит 9 ч CPU / 9 ч GPU. 5 посылок в день, 2 финальных.
- [У] Сроки: слияние команд до 15.10, дедлайн 22.10 23:59 UTC. Сегодня 30.09: осталось 22 дня, неделя плана - Д1 30.09 ... Д7 06.10.
- [У] Трейн: 4407 исследований, 24371 серия (5.5 серии на исследование), текст отчета у всех, метки у ~1.3% строк. Тест: около 1300 исследований без отчетов, видимых 3. Организаторы предупреждают о разной распространенности находок.
- [У] В csv нет пациента, площадки, сканера, даты. DICOM: смешанные transfer syntax, включая JPEG Lossless и JPEG 2000.
- [У] Правила 2.6: публичные внешние данные и модели разрешены, если хост не запретил отдельно; недорогая подписка на LLM допустима.
- [У] Есть трек эффективности: время инференса входит в скор.
- [Д] Размеченных 58, одни и те же строки по 12 таргетам, позитивов от 8-11 (MCL, Lateral OA) до 34-37 (Effusion).
- [Д] Публичная линия (DINOv2 + CoAtNet + RadImageNet, бленды) заявляет 0.942-0.957; топ-20 паблика 0.956-0.961 [У по API]. В прочитанном публичном ноутбуке обучения gold идет в обучение с весом 2.0 [У по коду одного ноутбука, остальные ветки не прочитаны].
- Объем рерана [Д, мой расчет]: 1300 x 5.5 серии x 20-45 срезов = 140-320 тыс. DICOM-файлов. Декодирование и обход файлов - отдельная стадия по времени, по 3 видимым исследованиям ее не спрогнозировать.

## 2. Метрика (подробно: notes/METRIC.md)

- [У] Страница: macro AUC, 12 таргетов, равные веса. Порт `scratch/knee_metric.py` сверен с перебором пар и scipy на 1584 таргет-случаях, расхождений 0.
- [Д] Грейдер совпадает с портом: официального кода нет, сверки с грейдером и sklearn не было.
- Следствия: важен только порядок внутри колонки; редкий таргет весит как частый (один позитив редкого класса на gold стоит до 0.0093 macro).
- Правила записи сабмита: не округлять (до -0.007 на насыщенных предсказаниях), порядок строк и колонок как в `sample_submission`, без NaN/inf/дублей.
- Проверка грейдера: одна посылка `sample_submission` через ноутбук, ожидаем 0.500.

## 3. Валидация (подробно: notes/VALIDATION.md)

Предложение инженера валидации принимается целиком:
- единица - исследование (пациент, если найдется в тегах DICOM); группа - одинаковый отчет + ключ пациента;
- gold (58) целиком вне обучения всю первую неделю, вместе с соседями по группе; каждое чтение - в журнал, бюджет 10 чтений на неделю;
- silver-cv (5 групповых фолдов) - рабочая дорожка при неизменном источнике меток; lockbox 15% групп, открыть один раз;
- оценка публичных весов и публичных псевдометок на gold считается in-sample.

Пороги решений [Д, симуляция; заменить бутстрапом на реальных предсказаниях]:

| дорожка | нет информации | сигнал |
|---|---|---|
| gold, переобучение | < 0.011-0.016 | от 0.017-0.023 |
| gold, другая модель | - | от 0.027-0.039 |
| silver-cv, один источник меток | SD пары 0.001-0.0025 | > 3 SD своей пары |
| паблик, переобучение | < 0.003-0.007 | от 0.005-0.011, и только после 4 условий из VALIDATION.md |

Проверки на реальных данных:
- Д1: `first_day_checks.py` на настоящих csv (число gold, совпадение строк, позитивы, корреляции, дубли); теги DICOM (пациент, институция, производитель; 3 тестовых против трейна); доля паблика; поиск кода метрики; форум вручную.
- Д2: точность извлекателя на gold без настройки на нем, с интервалами.
- Д3-Д4: три сида базовой модели - SD сида и реальная корреляция пары; бутстрап по единицам; заведомо большая разница (слабая против сильной модели) на silver-cv и gold - совпадает ли знак.
- Д5: leave-one-language-out против группового cv.

Ворота: если знак заведомо большой разницы на silver-cv и gold расходится, silver-cv для решений не используется (см. раздел 6).

## 4. Очередь экспериментов

Локальных оценок эффекта нет ни по одной линии. "Ожидаемый эффект" ниже - из чужих заявлений [Д]: regex-метки + модель 0.906, публичные бленды 0.942-0.957, топ 0.961.

Порядок: сначала формат и грейдер (по календарю первые), затем данные - метки из отчетов (99% трейна без меток, это главный рычаг уровня 1), затем свои модели изображений. Ручки уровня 4 в первую неделю не трогаем.

Доли вычислений: модельные линии L1-L4 - не меньше 60%; инфраструктура и сверки - до 30%; воспроизведение публичной линии - до 10%; ручки - 0.

| день | пункт | уровень | стоимость | локальная проверка | удалось / закрыто |
|---|---|---|---|---|---|
| Д1 | I0. Данные, проверки раздела 3, скелет ноутбука с гейтингом, офлайн-декодеры DICOM, посылка P1 | 3 | CPU, часы | декодируются все transfer syntax на выборке трейна, 0 пропусков | P1 = 0.500; счетчик нечитаемых файлов 0 |
| Д2 | I1. Публичный ноутбук без правок, посылка P2 | калибровка | 1 слот | лог негейтнутой копии на 3 тестовых | скор в пределах 0.005 от заявленного; измерено время рерана |
| Д2 | L1. Источник меток v0: публичный словарь/regex как есть | 1 | CPU, часы | чувствительность и специфичность на gold по таргетам с интервалами, 1 чтение gold | удалось, если по каждому таргету AUC меток против gold отличим от 0.5; иначе таргет помечается как проблемный |
| Д3-Д4 | L2. Своя база: замороженный энкодер (DINOv2 или RadImageNet) + attention pooling по срезам и сериям, silver-cv, 3 сида | 1 | 1 GPU-день: признаки считаются один раз | silver-cv по пулу OOF, gold (1 чтение) | конвейер от DICOM до csv работает в ноутбуке; есть SD сида и корреляция пары |
| Д4-Д5 | L3. Дообучение 2.5D-сети (ConvNeXt/CoAtNet) на silver-метках с аугментациями под сдвиг площадок | 1 | 1-2 GPU-дня, прокси на 1 фолде и малом разрешении | silver-cv против L2, тот же источник меток | продолжать, если > 3 SD пары на silver-cv; закрыть только после второй попытки на следующей базе |
| Д4-Д5 | L1b. Источник меток v1: LLM-извлекатель или градуированные метки | 1 | зависит от решения по LLM | только gold (silver тут in-sample), 1-2 чтения | продолжать при разнице на gold от 0.017; меньше - оставить v0, вторая попытка на базе L3 |
| Д5-Д6 | L4. Учет плоскости и типа последовательности (маршрутизация серий по таргетам) | 1-2 | 0.5 GPU-дня | silver-cv, по таргетам | продолжать, если выигрыш на большинстве таргетов и > 3 SD пары |
| Д6 | S1. Контроль времени: прогон с поддельным временем старта, деградация по стадиям | 2-3 | CPU, часы | каждый деградированный путь исполнен хотя бы раз | известна цена каждого срабатывания в macro AUC |
| Д6-Д7 | L5. Ансамбль своих линий; отдельно - свои + публичные | 1 | инференс | веса на OOF silver-cv, не на gold; lockbox не открывать | > 3 SD пары против лучшей одиночной на silver-cv |
| Д7 | Разбор недели | - | - | - | по каждой линии: число попыток, решение, условие закрытия |

Каждая модельная линия получает минимум две попытки; в первую неделю ни одна не закрывается.

Сравнение "свое против публичного": на gold нечестно (публичные веса его видели), поэтому либо паблик с порогом > 3 SD пары, либо переобучение публичной архитектуры на наших фолдах. Свой компонент, выигравший на отложенных данных, идет в ансамбль, даже если на паблике он чуть ниже.

## 5. Бюджет посылок

Доступно 35 слотов, план - до 12. Остальное не тратим: лучший из 10-25 посылок завышен на 0.003-0.006 [Д, симуляция], а топ-20 лежит в 0.005.

| слот | что | ожидание | реакция |
|---|---|---|---|
| P1, Д1 | `sample_submission` через ноутбук | 0.500 | ошибка - грейдер падает на константе; другое число - формула не та, остановить модельные посылки до выяснения |
| P2, Д2 | публичный ноутбук без правок | заявленный скор +-0.005 | ниже - шапка не от этой версии, брать другой форк только по прочитанному коду; заодно время рерана |
| P3, Д4 | своя база L2 | уровня нет; цель - перенос локального на паблик | если паблик расходится с gold больше чем на 2 SD скора - искать сдвиг площадок или баг декодирования |
| P4-P9, Д5-Д7 | только модельные линии с сигналом на валидации, по одной на изменение | знак как на валидации | знак не совпал при разнице > 3 SD пары - разбирать, не переотправлять |
| P10-P11 | структурные правки и деградированный по времени путь | цена известна локально | - |
| P12 | резерв на упавший ноутбук | - | - |

Не тратим слоты на: округление, порядок строк, NaN (закрыто правилами записи); поштучный замер AUC таргетов на паблике; ручки пост-процессинга и веса бленда, подобранные по паблику; перебор публичных форков.

Требования к ноутбуку до P3:
- гейтинг: на коммите - копия `sample_submission` и выход;
- громкие падения: наличие и sha256 весов, пустой результат стадии, нечитаемый DICOM сверх порога, финальные assert'ы (число строк = числу исследований теста, нет дублей, нет NaN/inf, колонки как в sample);
- время от одного абсолютного момента старта, деградация по стадиям;
- все зависимости (декодеры JPEG Lossless и JPEG 2000, веса) датасетами, без интернета;
- перед посылкой: негейтнутая копия на 3 тестовых на GPU, CPU-прогон на одном исследовании против эталона, сверка копии на платформе с локальным исходником;
- журнал: строка на посылку (время, id, версия, база, ожидаемая разница, правило, результат).

Число раундов в сутки зависит от времени рерана: при 7-8 ч - два раунда, при заявленных публичной линией 30 мин [Д] - ограничивает только бюджет слотов.

## 6. Открытые вопросы и допущения

| допущение | как проверяется | если не подтвердится |
|---|---|---|
| Грейдер = порт | P1, поиск кода метрики | модельные посылки стоят до выяснения формулы |
| Gold: 58 строк, одни и те же по 12 таргетам, 8+ позитивов на таргет | `first_day_checks.py`, Д1 | меньше или разные строки - пороги gold пересчитать; таргеты без позитивов оцениваются только на silver |
| Gold отобран не случайно, но переносится на тест | сравнение gold с остальными по письменности, длине отчета, сериям | gold - только контрольная точка; вес паблика в решениях растет |
| В DICOM есть пациент или институция | теги, Д1 | нет - группа только по дублям отчетов, leave-one-language-out - единственная диагностика переноса |
| Тест - с тех же площадок | теги 3 тестовых, форум | новые площадки - приоритет аугментаций и leave-one-language-out выше silver-cv |
| Silver-cv сохраняет знак | заведомо большая разница, Д3-Д4 | silver-cv не используется; решения по gold (только крупные) и паблику; бюджет посылок на модельные линии растет до 15-18 |
| Извлекатель из отчетов достаточно точен | L1 на gold, Д2 | линия меток становится первой по вычислениям, L3-L4 сдвигаются |
| Публичные псевдометки и веса настроены на gold | чтение кода и описаний датасетов | если не настроены - их можно оценивать на gold и брать как источник меток без оговорок |
| Отправка отчетов во внешний LLM API допустима | текст лицензии MIRA, форум, хост | нет - только локальная открытая LLM или regex |
| Время рерана заметно меньше 9 ч | P2, P3 | сокращать число серий и TTA по заранее измеренной цене |
| Доля паблика 20-50% | страница лидерборда | пересчитать таблицу шума и пороги паблика |
| Слаг `rsna-knee-abnormality-detection` | первый запуск ноутбука | поправить пути |

Решения за командой:
1. Брать ли gold в обучение после первой недели (если да - только кросс-фитом, счет по пулу OOF; честной дорожки тогда не остается).
2. Использовать ли внешний LLM API для разметки отчетов.
3. Допускать ли публичные веса и псевдометки в финальный ансамбль.
4. Участвовать ли в треке эффективности.
5. Слияние команд до 15.10.
6. Кто читает форум и общую часть правил вручную.
</tool>
````

Результат write_file:

````
Файл notes/PLAN.md записан
````

### strategist, сообщение 3

````
План первой недели (30.09-06.10) записан в `notes/PLAN.md` со всеми шестью разделами. Он стоит на симуляции и чужих заявлениях: данных в рабочей папке нет, своих прогонов нет, локальной оценки эффекта нет ни по одной линии.

## Сводка плана

**Установлено**
- Задача: 12 находок на исследование МРТ колена, метрика по странице - macro AUC с равными весами.
- Ограничения: посылка ноутбуком без интернета, 9 часов CPU/GPU, 5 посылок в день, 2 финальных, дедлайн 22.10.
- Данные: 4407 исследований с отчётами, метки примерно у 1.3%; в тесте около 1300 исследований без отчётов.
- Метрика: порт `scratch/knee_metric.py` сверен с перебором пар и `scipy` без расхождений, но не с грейдером.

**Допущения**
- Размеченных исследований (gold) 58, одни и те же строки по всем 12 таргетам.
- Пороги шума взяты из симуляции: на gold сигнал начинается от 0.017-0.023 для переобучения, на паблике разницы меньше 0.003-0.007 ничего не значат.
- Скоры публичных ноутбуков (0.942-0.957) - заявления авторов.
- Объём рерана - мой расчёт: 140-320 тыс. DICOM-файлов, по 3 видимым исследованиям время не спрогнозировать.

**Валидация.** Схема инженера валидации принимается целиком:
- gold всю неделю вне обучения, не больше 10 чтений с журналом;
- рабочая дорожка - 5 групповых фолдов на метках из отчётов (silver-cv), только при неизменном источнике меток;
- отложенные 15% групп открываются один раз;
- оценка публичных весов на gold считается in-sample.

**Очередь по дням**
1. **Д1:** данные, проверки таблиц и тегов DICOM, скелет ноутбука с гейтингом и офлайн-декодерами, посылка `sample_submission` (ожидаем 0.500).
2. **Д2:** публичный ноутбук без правок для калибровки и замера времени рерана; публичный словарь меток как есть, с замером точности на gold.
3. **Д3-Д4:** своя база на замороженном энкодере с attention pooling, 3 сида - отсюда реальный SD сида и корреляция пары.
4. **Д4-Д5:** дообучение 2.5D-сети с аугментациями под сдвиг площадок; вторая версия источника меток, проверяется только на gold.
5. **Д5-Д6:** учёт плоскости и типа последовательности; прогон деградированных по времени путей с поддельным временем старта.
6. **Д6-Д7:** ансамбль, веса только на silver-cv; разбор недели.

Критерий продолжения линии - больше 3 SD своей пары на silver-cv. Для смены источника меток - разница от 0.017 на gold. Каждая модельная линия получает минимум две попытки, в первую неделю ни одна не закрывается.

**Доли вычислений.** Модельные линии - не меньше 60%, инфраструктура и сверки - до 30%, воспроизведение публичной линии - до 10%. Пороги, константы и прочие ручки пост-процессинга в первую неделю не трогаем.

**Посылки.** До 12 из 35 доступных:
- 2 на калибровку (`sample_submission` и публичный ноутбук);
- 7 на модельные линии с сигналом на валидации;
- 2 на структурные правки и деградированный путь;
- 1 резерв на упавший ноутбук.

Слоты не тратятся на округление, порядок строк, NaN, замер отдельных таргетов, подбор весов бленда по паблику и перебор публичных форков.

**Главное условие плана.** На Д3-Д4 проверяется, совпадает ли знак заведомо большой разницы на silver-cv и на gold. Если нет, silver-cv для решений не годится: остаются gold (только крупные разницы) и паблик, а бюджет посылок на модельные линии растёт до 15-18. Остальные допущения и развилки - в таблице раздела 6 плана.

## Решения за командой

1. Брать ли gold в обучение после первой недели. Если да - только кросс-фитом со счётом по пулу OOF, и честной дорожки тогда не остаётся.
2. Использовать ли внешний LLM API для разметки отчётов. Правила 2.6 платные LLM допускают, но совместимость с запретом передачи данных по лицензии MIRA не проверена.
3. Допускать ли публичные веса и псевдометки в финальный ансамбль: их происхождение и сплиты неизвестны.
4. Участвовать ли в треке эффективности: это меняет цену каждой модели в ансамбле.
5. Слияние команд до 15.10.
6. Кто вручную читает форум и остаток правил (прочитано 12000 из 37384 символов). Без этого неизвестны код метрики, доля паблика и отдельные запреты хоста.

ИТОГ:
- План недели 30.09-06.10 записан в `notes/PLAN.md`; данных и своих прогонов нет, пороги взяты из симуляции, скоры публичных ноутбуков - чужие заявления.
- Порядок: Д1 - данные, теги DICOM, гейтнутый ноутбук и посылка `sample_submission` (ждём 0.500); Д2 - публичный ноутбук для калибровки и времени рерана плюс замер точности меток из отчётов на gold; Д3-Д7 - свои модельные линии.
- Модельным линиям - не меньше 60% вычислений и 7 из 12 плановых посылок, по две попытки на линию; ручки пост-процессинга в первую неделю не трогаем.
- Схема инженера валидации принята целиком: gold (58, число не сверено) вне обучения всю неделю, не больше 10 чтений; рабочая дорожка - silver-cv при неизменном источнике меток.
- Критерии: больше 3 SD пары на silver-cv; для смены источника меток - от 0.017 на gold; паблик читается только после четырёх условий из `notes/VALIDATION.md`.
- Главная развилка на Д3-Д4: если знак заведомо большой разницы на silver-cv и gold расходится, silver-cv не используется, решения идут по gold и паблику, бюджет посылок растёт до 15-18.
- За командой: gold в обучение, внешний LLM API для отчётов, публичные веса в финале, трек эффективности, слияние до 15.10, кто читает форум и правила.
````

Вызовов инструментов: 2
[harness] записан файл notes/PLAN.md (11753 символов)

## Диспетчер, ход 6

````
{"thought":"План записан в notes/PLAN.md, все части запроса покрыты: разведка, метрика, валидация, очередь экспериментов и бюджет посылок. Прогонов нет, аудитору делать нечего; можно заканчивать.","plan_list":["finish: короткий итог пользователю"],"action":"finish","final_answer":"План первой недели (30.09-06.10) записан в notes/PLAN.md. Данных в рабочей папке пока нет, поэтому все цифры шума и пороги взяты из симуляции, а не из реальных предсказаний.\n\n**Соревнование и ограничения** (notes/RECON.md)\n- Задача: 12 бинарных находок на исследование МРТ колена.\n- Формат: сабмит ноутбуком, 9 часов, без интернета; 5 посылок в день, 2 финальных.\n- Сроки: вход и слияние до 15.10.2026, финал 22.10.2026.\n- Внешние данные и веса разрешены (п. 2.6 правил).\n- Данные: 4407 исследований, настоящие метки есть только примерно у 58 (8-37 позитивов на класс); у остальных только текст отчёта. В тесте около 1300 исследований без отчётов.\n- Лидерборд: топ-20 паблика лежит в 0.956-0.961. Публичные ноутбуки заявляют 0.942-0.947; это чужие цифры, мы их не проверяли.\n\n**Метрика** (notes/METRIC.md, scratch/knee_metric.py)\n- Macro AUC по 12 таргетам с равными весами. Официального кода нет; порт написан по формуле со страницы и с грейдером не сверен.\n- Сверка - одна пробная посылка `sample_submission`, ожидаем 0.500.\n- Считать по пулу out-of-fold предсказаний, а не средним по фолдам. Предсказания в сабмите не округлять.\n\n**Валидация** (notes/VALIDATION.md)\n- Размеченные 58 исследований - единственная честная дорожка. Она шумная: различает разницы от 0.01-0.03. Всю неделю держим их вне обучения, не больше 10 чтений с журналом.\n- Рабочая дорожка на каждый день - кросс-валидация на метках из отчётов (около 3700 исследований, 5 групповых фолдов). Годится, только пока источник меток не меняется.\n- 15% групп с метками из отчётов откладываем как контрольную выборку.\n- Оценку публичных весов на 58 размеченных считаем возможной in-sample: в прочитанном публичном ноутбуке эти исследования шли в обучение.\n- Паблик: разницы меньше 0.003-0.007 ничего не значат, порядок в топ-20 внутри шума. На паблик не опираемся до четырёх проверок: доля паблика, `sample_submission` = 0.500, сверка ноутбука с локальным пайплайном, бутстрап на реальных предсказаниях.\n\n**Что пробовать первым**\n- День 1: данные, теги DICOM (пациент, площадка), ноутбук с проверками формата и времени, посылка `sample_submission`.\n- День 2: публичный ноутбук для калибровки и замера времени рерана; замер точности меток из отчётов на 58 размеченных.\n- Дни 3-7: свои модельные линии, по две попытки на линию.\n- Развилка на днях 3-4: если знак заведомо большой разницы на кросс-валидации и на 58 размеченных расходится, кросс-валидацию бросаем, решения идут по размеченным и паблику, бюджет посылок растёт до 15-18.\n\n**Посылки**\n- Плановый бюджет - 12 на неделю, из них 7 на модельные линии.\n- Не тратим посылки на ручки пост-процессинга и на погоню за разницами внутри шума паблика.\n\n**Осталось под вопросом**\n- Доля паблика и отличие теста от трейна по площадкам и пациентам не найдены.\n- В csv нет идентификаторов пациента и площадки; групповой сплит зависит от того, найдутся ли они в тегах DICOM.\n- Форум и квоты GPU оказались недоступны.\n- Точное число и баланс размеченных не сверены по данным.\n\n**Решения за вами**\n- Брать ли 58 размеченных в обучение после первой недели.\n- Можно ли отправлять отчёты во внешний LLM API: в правилах отдельного пункта нет, вопрос о запрете передачи данных открыт.\n- Использовать ли публичные веса в финале.\n- Участвовать ли в треке эффективности.\n- Сливаться ли с кем-то до 15.10.\n- Кто читает форум и общую часть правил."}
````

## Ответ диспетчера

План первой недели (30.09-06.10) записан в notes/PLAN.md. Данных в рабочей папке пока нет, поэтому все цифры шума и пороги взяты из симуляции, а не из реальных предсказаний.

**Соревнование и ограничения** (notes/RECON.md)
- Задача: 12 бинарных находок на исследование МРТ колена.
- Формат: сабмит ноутбуком, 9 часов, без интернета; 5 посылок в день, 2 финальных.
- Сроки: вход и слияние до 15.10.2026, финал 22.10.2026.
- Внешние данные и веса разрешены (п. 2.6 правил).
- Данные: 4407 исследований, настоящие метки есть только примерно у 58 (8-37 позитивов на класс); у остальных только текст отчёта. В тесте около 1300 исследований без отчётов.
- Лидерборд: топ-20 паблика лежит в 0.956-0.961. Публичные ноутбуки заявляют 0.942-0.947; это чужие цифры, мы их не проверяли.

**Метрика** (notes/METRIC.md, scratch/knee_metric.py)
- Macro AUC по 12 таргетам с равными весами. Официального кода нет; порт написан по формуле со страницы и с грейдером не сверен.
- Сверка - одна пробная посылка `sample_submission`, ожидаем 0.500.
- Считать по пулу out-of-fold предсказаний, а не средним по фолдам. Предсказания в сабмите не округлять.

**Валидация** (notes/VALIDATION.md)
- Размеченные 58 исследований - единственная честная дорожка. Она шумная: различает разницы от 0.01-0.03. Всю неделю держим их вне обучения, не больше 10 чтений с журналом.
- Рабочая дорожка на каждый день - кросс-валидация на метках из отчётов (около 3700 исследований, 5 групповых фолдов). Годится, только пока источник меток не меняется.
- 15% групп с метками из отчётов откладываем как контрольную выборку.
- Оценку публичных весов на 58 размеченных считаем возможной in-sample: в прочитанном публичном ноутбуке эти исследования шли в обучение.
- Паблик: разницы меньше 0.003-0.007 ничего не значат, порядок в топ-20 внутри шума. На паблик не опираемся до четырёх проверок: доля паблика, `sample_submission` = 0.500, сверка ноутбука с локальным пайплайном, бутстрап на реальных предсказаниях.

**Что пробовать первым**
- День 1: данные, теги DICOM (пациент, площадка), ноутбук с проверками формата и времени, посылка `sample_submission`.
- День 2: публичный ноутбук для калибровки и замера времени рерана; замер точности меток из отчётов на 58 размеченных.
- Дни 3-7: свои модельные линии, по две попытки на линию.
- Развилка на днях 3-4: если знак заведомо большой разницы на кросс-валидации и на 58 размеченных расходится, кросс-валидацию бросаем, решения идут по размеченным и паблику, бюджет посылок растёт до 15-18.

**Посылки**
- Плановый бюджет - 12 на неделю, из них 7 на модельные линии.
- Не тратим посылки на ручки пост-процессинга и на погоню за разницами внутри шума паблика.

**Осталось под вопросом**
- Доля паблика и отличие теста от трейна по площадкам и пациентам не найдены.
- В csv нет идентификаторов пациента и площадки; групповой сплит зависит от того, найдутся ли они в тегах DICOM.
- Форум и квоты GPU оказались недоступны.
- Точное число и баланс размеченных не сверены по данным.

**Решения за вами**
- Брать ли 58 размеченных в обучение после первой недели.
- Можно ли отправлять отчёты во внешний LLM API: в правилах отдельного пункта нет, вопрос о запрете передачи данных открыт.
- Использовать ли публичные веса в финале.
- Участвовать ли в треке эффективности.
- Сливаться ли с кем-то до 15.10.
- Кто читает форум и общую часть правил.

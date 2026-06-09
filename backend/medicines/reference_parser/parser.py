import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


REQUEST_TIMEOUT_MS = 60_000
DESCRIPTION_SWITCH_TIMEOUT_MS = 10_000
MAX_TEXT_LENGTH = 4_000
SECTION_LIMITS = {
    "active_substance": 700,
    "atx": 700,
    "nosology": 1200,
    "pharmacological_group": 1200,
    "dosage_form": 700,
    "composition": 2500,
    "dosage_form_description": 1200,
    "pharmacokinetics": 2500,
    "pharmacodynamics": 2500,
    "indications": 2500,
    "contraindications": 2500,
    "pregnancy_lactation": 2500,
    "administration": 2500,
    "side_effects": 2500,
    "interactions": 2500,
    "overdose": 2500,
    "special_instructions": 2500,
    "release_form": 2000,
    "pharmacy_terms": 1000,
    "storage_conditions": 1000,
    "shelf_life": 1000,
    "manufacturer": 2000,
}
SECTION_ALIASES = {
    "active_substance": ["Действующее вещество", "Active ingredient"],
    "atx": ["ATX"],
    "nosology": ["Нозологическая классификация (МКБ-10)", "Nosology"],
    "pharmacological_group": ["Фармакологическая группа", "Фармако-терапевтическая группа"],
    "dosage_form": ["Лекарственная форма", "Dosage form"],
    "composition": ["Состав", "Composition"],
    "dosage_form_description": ["Описание лекарственной формы"],
    "pharmacokinetics": ["Фармакокинетика", "Pharmacokinetics"],
    "pharmacodynamics": ["Фармакодинамика", "Pharmacodynamics"],
    "indications": ["Показания", "Indications"],
    "contraindications": ["Противопоказания", "Contraindications"],
    "pregnancy_lactation": ["Применение при беременности и кормлении грудью"],
    "administration": ["Способ применения и дозы"],
    "side_effects": ["Побочные действия", "Side effects"],
    "interactions": ["Взаимодействие", "Interactions"],
    "overdose": ["Передозировка", "Overdose"],
    "special_instructions": ["Особые указания"],
    "release_form": ["Форма выпуска"],
    "pharmacy_terms": ["Условия отпуска из аптек"],
    "storage_conditions": ["Условия хранения", "Storage conditions"],
    "shelf_life": ["Срок годности", "Shelf life"],
    "manufacturer": ["Производитель", "Manufacturer"],
}


class ReferenceParserError(Exception):
    pass


def normalize_text(value):
    value = (value or "").replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def clamp_text(value, limit=MAX_TEXT_LENGTH):
    value = normalize_text(value)
    return value[:limit]


def normalize_for_match(value):
    value = normalize_text(value).lower().replace("ё", "е")
    value = re.sub(r"[^\wа-яА-Я0-9%/]+", " ", value)
    return normalize_text(value)


@dataclass
class DocumentNode:
    tag: str
    text: str
    attrs: dict[str, str] = field(default_factory=dict)


class DocumentTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._stack = []
        self.nodes = []
        self.title = ""
        self._title_parts = []

    def handle_starttag(self, tag, attrs):
        self._stack.append({"tag": tag.lower(), "attrs": dict(attrs), "parts": []})

    def handle_data(self, data):
        if not data.strip():
            return
        for item in self._stack:
            item["parts"].append(data)
        if self._stack and self._stack[-1]["tag"] == "title":
            self._title_parts.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index]["tag"] != tag:
                continue
            item = self._stack.pop(index)
            text = normalize_text(" ".join(item["parts"]))
            if text:
                self.nodes.append(DocumentNode(tag=tag, text=text, attrs=item["attrs"]))
            break

    def close(self):
        super().close()
        self.title = normalize_text(" ".join(self._title_parts))


def parse_html(html):
    parser = DocumentTextParser()
    parser.feed(html)
    parser.close()
    return parser


def document_text(document):
    seen = []
    for node in document.nodes:
        if node.text and node.text not in seen:
            seen.append(node.text)
    return "\n".join(seen)


def extract_trade_name(document):
    for tag in ("h1", "h2"):
        for node in document.nodes:
            if node.tag == tag:
                return clamp_text(node.text, 180)
    return clamp_text(document.title, 180)


def extract_active_ingredient(text):
    patterns = [
        r"(?:действующее\s+вещество|active\s+ingredient)\s*[:\-]\s*([^\n.;]+)",
        r"(?:состав)\s*[:\-]\s*([^\n.;]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clamp_text(match.group(1), 180)
    return ""


def extract_storage_conditions(text):
    match = re.search(
        r"((?:условия\s+хранения|storage\s+conditions)[\s\S]{0,800})",
        text,
        flags=re.IGNORECASE,
    )
    return clamp_text(match.group(1), 800) if match else ""


def extract_shelf_life(text):
    match = re.search(r"((?:срок\s+годности|shelf\s+life)[\s\S]{0,400})", text, flags=re.IGNORECASE)
    return clamp_text(match.group(1), 400) if match else ""


def extract_form(text):
    forms = [
        "таблетки",
        "капсулы",
        "сироп",
        "мазь",
        "капли",
        "спрей",
        "гель",
        "раствор",
        "tablets",
        "capsules",
        "syrup",
        "ointment",
        "drops",
        "spray",
        "gel",
        "solution",
    ]
    lower = text.lower()
    for form in forms:
        if form in lower:
            return form
    return "other"


def extract_dosage(text):
    match = re.search(
        r"\b\d+(?:[,.]\d+)?\s*(?:мг|г|мл|мкг|mg|g|ml|mcg)\b|\b\d+(?:[,.]\d+)?%",
        text,
        flags=re.IGNORECASE,
    )
    return normalize_text(match.group(0)) if match else ""


def extract_variant_form(text, dosage=""):
    value = normalize_text(text)
    if dosage:
        value = normalize_text(value.replace(dosage, " "))
    value = re.sub(
        r"(?i)(лекарственная\s+форма|dosage\s+form|дозировка|dosage|выбор\s+описания)",
        " ",
        value,
    )
    value = re.sub(r"\b\d+(?:[,.]\d+)?\s*(?:мг|г|мл|мкг|mg|g|ml|mcg)\b|\b\d+(?:[,.]\d+)?%", " ", value, flags=re.IGNORECASE)
    value = normalize_text(value)
    return value or extract_form(text)


def extract_variants_from_tables(document):
    variants = []
    for node in document.nodes:
        if node.tag != "tr":
            continue
        text = node.text
        if not re.search(r"\d", text):
            continue
        dosage = extract_dosage(text)
        form = extract_variant_form(text, dosage)
        if dosage and form:
            variant = {"form": clamp_text(form, 120), "dosage": clamp_text(dosage, 120)}
            if variant not in variants:
                variants.append(variant)
    return variants


def extract_reference_sections(document):
    sections = {}
    headings = {"h2", "h3", "h4"}
    current_key = None
    current_parts = []

    def flush():
        if current_key and current_parts:
            sections[current_key] = clamp_text(" ".join(current_parts))

    for node in document.nodes:
        if node.tag in headings:
            flush()
            current_key = node.text
            current_parts = []
        elif current_key and node.tag in {"p", "li", "div", "section"}:
            current_parts.append(node.text)
    flush()
    return sections


def section_value(sections, aliases):
    normalized = {normalize_for_match(key): value for key, value in sections.items()}
    for alias in aliases:
        value = normalized.get(normalize_for_match(alias))
        if value:
            return value
    return ""


def build_reference_data(sections):
    reference_data = {}
    for key, aliases in SECTION_ALIASES.items():
        reference_data[key] = clamp_text(section_value(sections, aliases), SECTION_LIMITS[key])
    reference_data["sections"] = {
        clamp_text(key, 180): clamp_text(value, MAX_TEXT_LENGTH)
        for key, value in sections.items()
        if normalize_text(key)
    }
    return reference_data


def description_matches_selected_variant(selected_form, selected_dosage, reference_data):
    selected_form_norm = normalize_for_match(selected_form)
    selected_dosage_norm = normalize_for_match(selected_dosage)
    dosage_form_norm = normalize_for_match(reference_data.get("dosage_form", ""))
    composition_norm = normalize_for_match(reference_data.get("composition", ""))
    release_form_norm = normalize_for_match(reference_data.get("release_form", ""))

    form_ok = not selected_form_norm or (
        selected_form_norm == dosage_form_norm
        or selected_form_norm in dosage_form_norm
        or dosage_form_norm in selected_form_norm
    )
    dosage_ok = not selected_dosage_norm or (
        selected_dosage_norm in composition_norm
        or selected_dosage_norm in release_form_norm
        or selected_dosage_norm in dosage_form_norm
    )
    return {
        "form_ok": form_ok,
        "dosage_ok": dosage_ok,
        "overall": form_ok and dosage_ok,
        "debug": {
            "selected_form_norm": selected_form_norm,
            "selected_dosage_norm": selected_dosage_norm,
            "dosage_form_norm": dosage_form_norm,
        },
    }


def parse_variants_html(html, source_url=""):
    document = parse_html(html)
    text = document_text(document)
    variants = extract_variants_from_tables(document)
    single_variant = False

    if not variants:
        variants = [{"form": clamp_text(extract_form(text), 120), "dosage": clamp_text(extract_dosage(text), 120)}]
        single_variant = True

    return {
        "trade_name": extract_trade_name(document),
        "source_url": source_url,
        "variants": variants,
        "single_variant": single_variant,
    }


def parse_detail_html(html, source_url="", form="", dosage=""):
    document = parse_html(html)
    text = document_text(document)
    selected_form = form or extract_form(text)
    selected_dosage = dosage or extract_dosage(text)
    sections = extract_reference_sections(document)
    reference_data = build_reference_data(sections)
    fields = {
        "trade_name": extract_trade_name(document),
        "active_ingredient": reference_data.get("active_substance") or extract_active_ingredient(text),
        "form": clamp_text(selected_form, 120),
        "dosage": clamp_text(selected_dosage, 120),
        "storage_conditions": reference_data.get("storage_conditions") or extract_storage_conditions(text),
        "shelf_life": reference_data.get("shelf_life") or extract_shelf_life(text),
    }
    return {
        "source_url": source_url,
        "selected": {"form": fields["form"], "dosage": fields["dosage"]},
        "selected_matches_description": description_matches_selected_variant(
            selected_form,
            selected_dosage,
            reference_data,
        ),
        "fields": fields,
        "reference_data": reference_data,
    }


def click_optional_buttons(page):
    for button_text in ["ОК", "Да", "Согласен", "Принять", "Закрыть", "OK", "Accept", "Close"]:
        try:
            locator = page.get_by_text(button_text, exact=True).first
            if locator.is_visible(timeout=1_000):
                locator.click(timeout=3_000)
                page.wait_for_timeout(500)
        except Exception:
            continue


def extract_variants_from_page(page):
    return page.evaluate(
        """
        () => {
            const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
            const dosageMatch = (text) => {
                const match = text.match(/\\b\\d+(?:[,.]\\d+)?\\s*(?:мг|г|мл|мкг|mg|g|ml|mcg)\\b|\\b\\d+(?:[,.]\\d+)?%/i);
                return match ? normalize(match[0]) : '';
            };
            const formMatch = (text, dosage) => {
                let form = normalize(text)
                    .replace(dosage, ' ')
                    .replace(/(лекарственная\\s+форма|dosage\\s+form|дозировка|dosage|выбор\\s+описания)/ig, ' ')
                    .replace(/\\b\\d+(?:[,.]\\d+)?\\s*(?:мг|г|мл|мкг|mg|g|ml|mcg)\\b|\\b\\d+(?:[,.]\\d+)?%/ig, ' ');
                form = normalize(form);
                return form;
            };
            const variants = [];
            for (const row of Array.from(document.querySelectorAll('tr'))) {
                const text = normalize(row.innerText);
                const dosage = dosageMatch(text);
                const form = formMatch(text, dosage);
                if (!form || !dosage) {
                    continue;
                }
                const exists = variants.some((item) => item.form === form && item.dosage === dosage);
                if (!exists) {
                    variants.push({form, dosage});
                }
            }
            return variants;
        }
        """
    )


def extract_sections_from_page(page):
    return page.evaluate(
        """
        () => {
            const result = {};
            const normalize = (value) => String(value || '').replace(/\\s+/g, ' ').trim();
            const shouldSkip = (node) => {
                if (!node) {
                    return true;
                }
                const tag = node.tagName ? node.tagName.toLowerCase() : '';
                if (['script', 'style', 'noscript', 'svg', 'iframe', 'noindex'].includes(tag)) {
                    return true;
                }
                const className = node.className ? String(node.className).toLowerCase() : '';
                const badClasses = [
                    'banner', 'advert', 'modal', 'popup', 'price', 'pharm', 'apteka',
                    'slick', 'cookie', 'navigation', 'breadcrumb'
                ];
                return badClasses.some((badClass) => className.includes(badClass));
            };
            const headings = Array.from(document.querySelectorAll('h2.structure-heading, h2, h3'));
            for (const heading of headings) {
                const sectionName = normalize(heading.innerText);
                if (!sectionName || sectionName === 'Выбор описания') {
                    continue;
                }
                const chunks = [];
                let node = heading.nextElementSibling;
                while (node) {
                    const tag = node.tagName ? node.tagName.toLowerCase() : '';
                    const isNextHeading = ['h2', 'h3'].includes(tag);
                    if (isNextHeading) {
                        break;
                    }
                    if (!shouldSkip(node)) {
                        const text = normalize(node.innerText);
                        if (text) {
                            chunks.push(text);
                        }
                    }
                    node = node.nextElementSibling;
                }
                result[sectionName] = normalize(chunks.join(' '));
            }
            return result;
        }
        """
    )


def wait_for_description_switch(page, form):
    if not form:
        return
    try:
        page.wait_for_function(
            """
            (form) => {
                const normalize = (value) => String(value || '')
                    .toLowerCase()
                    .replace(/ё/g, 'е')
                    .replace(/[^\\wа-яА-Я0-9%/]+/g, ' ')
                    .replace(/\\s+/g, ' ')
                    .trim();
                const formNorm = normalize(form);
                const headings = Array.from(document.querySelectorAll('h2.structure-heading, h2, h3'));
                for (const heading of headings) {
                    const headingText = normalize(heading.innerText);
                    if (!headingText.includes('лекарственная форма') && !headingText.includes('dosage form')) {
                        continue;
                    }
                    const chunks = [];
                    let node = heading.nextElementSibling;
                    while (node) {
                        const tag = node.tagName ? node.tagName.toLowerCase() : '';
                        if (['h2', 'h3'].includes(tag)) {
                            break;
                        }
                        if (node.innerText) {
                            chunks.push(node.innerText);
                        }
                        node = node.nextElementSibling;
                    }
                    const textNorm = normalize(chunks.join(' '));
                    return textNorm.includes(formNorm) || formNorm.includes(textNorm);
                }
                return false;
            }
            """,
            arg=form,
            timeout=DESCRIPTION_SWITCH_TIMEOUT_MS,
        )
    except Exception:
        return


def selected_variant_locator(page, *, form, dosage):
    if form and dosage:
        return page.locator("tr").filter(has_text=form).filter(has_text=dosage).first
    if form:
        return page.get_by_text(form, exact=False).first
    if dosage:
        return page.get_by_text(dosage, exact=False).first
    return None


def click_selected_variant(page, *, form, dosage):
    locator = selected_variant_locator(page, form=form, dosage=dosage)
    if locator is None:
        return ""

    try:
        locator.wait_for(timeout=10_000)
    except Exception as exc:
        raise ReferenceParserError(f"Не найден вариант с формой '{form}' и дозировкой '{dosage}'.") from exc

    row_text = ""
    try:
        row_text = normalize_text(locator.inner_text())
    except Exception:
        pass

    try:
        input_locator = locator.locator("input[type='checkbox'], input[type='radio']").first
        if input_locator.count() > 0:
            input_locator.click(force=True)
        else:
            locator.click(timeout=3_000)
        wait_for_description_switch(page, form)
        page.wait_for_timeout(1_000)
        return row_text
    except Exception as exc:
        raise ReferenceParserError("Не удалось выбрать форму и дозировку на странице.") from exc


def playwright_api():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ReferenceParserError("Playwright не установлен.") from exc
    return sync_playwright, PlaywrightTimeoutError


def new_page(playwright, url):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 1000}, locale="ru-RU")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
        page.wait_for_timeout(3_000)
        click_optional_buttons(page)
        return browser, page
    except Exception:
        browser.close()
        raise


def page_operation_error(exc, timeout_error):
    if isinstance(exc, timeout_error):
        raise ReferenceParserError("Не удалось дождаться загрузки страницы.") from exc
    raise ReferenceParserError("Не удалось разобрать страницу по ссылке.") from exc


def parse_detail_page(page, source_url="", form="", dosage="", row_text=""):
    sections = extract_sections_from_page(page)
    reference_data = build_reference_data(sections)
    try:
        page_text = normalize_text(page.locator("body").inner_text(timeout=5_000))
    except Exception:
        page_text = normalize_text(page.content())
    selected_form = form or reference_data.get("dosage_form") or extract_form(page_text)
    selected_dosage = dosage or extract_dosage(reference_data.get("composition") or page_text)
    trade_name = ""
    try:
        trade_name = normalize_text(page.locator("h1").first.inner_text(timeout=2_000))
    except Exception:
        trade_name = ""
    if not trade_name:
        trade_name = extract_trade_name(parse_html(page.content()))

    fields = {
        "trade_name": clamp_text(trade_name, 180),
        "active_ingredient": reference_data.get("active_substance") or extract_active_ingredient(page_text),
        "form": clamp_text(selected_form, 120),
        "dosage": clamp_text(selected_dosage, 120),
        "storage_conditions": reference_data.get("storage_conditions") or extract_storage_conditions(page_text),
        "shelf_life": reference_data.get("shelf_life") or extract_shelf_life(page_text),
    }
    selected = {"form": fields["form"], "dosage": fields["dosage"]}
    if row_text:
        selected["row_text"] = row_text
    return {
        "source_url": source_url,
        "selected": selected,
        "selected_matches_description": description_matches_selected_variant(
            selected_form,
            selected_dosage,
            reference_data,
        ),
        "fields": fields,
        "reference_data": reference_data,
    }


def list_variants(url):
    sync_playwright, timeout_error = playwright_api()
    try:
        with sync_playwright() as playwright:
            browser, page = new_page(playwright, url)
            try:
                variants = extract_variants_from_page(page)
                if variants:
                    try:
                        trade_name = normalize_text(page.locator("h1").first.inner_text(timeout=2_000))
                    except Exception:
                        trade_name = extract_trade_name(parse_html(page.content()))
                    return {
                        "trade_name": clamp_text(trade_name, 180),
                        "source_url": url,
                        "variants": variants,
                        "single_variant": False,
                    }

                detail = parse_detail_page(page, source_url=url)
                return {
                    "trade_name": detail["fields"]["trade_name"],
                    "source_url": url,
                    "variants": [
                        {
                            "form": detail["fields"]["form"],
                            "dosage": detail["fields"]["dosage"],
                        }
                    ],
                    "single_variant": True,
                }
            finally:
                browser.close()
    except Exception as exc:
        page_operation_error(exc, timeout_error)


def parse_variant(url, form, dosage):
    sync_playwright, timeout_error = playwright_api()
    try:
        with sync_playwright() as playwright:
            browser, page = new_page(playwright, url)
            try:
                row_text = ""
                if form or dosage:
                    row_text = click_selected_variant(page, form=form, dosage=dosage)
                return parse_detail_page(page, source_url=url, form=form, dosage=dosage, row_text=row_text)
            finally:
                browser.close()
    except ReferenceParserError:
        raise
    except Exception as exc:
        page_operation_error(exc, timeout_error)

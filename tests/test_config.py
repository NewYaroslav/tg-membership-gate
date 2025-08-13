from modules.config import ticket_categories, ticket_category_map, session_timeout


def test_ticket_categories_structure():
    assert isinstance(ticket_categories, list)
    hardware = ticket_category_map["💻 Ошибки в работе оборудования"]
    subcats = hardware["subcategories"]
    assert any(sc["label"] == "Не работает телефон" for sc in subcats)
    phone_issue = next(sc for sc in subcats if sc["label"] == "Не работает телефон")
    assert phone_issue["template"] == "hardware_issue_message.txt"

    access = ticket_category_map["🔑 Запросы на доступ к ресурсам"]
    assert access.get("informational") is True
    assert access["template"] == "access_request_info.txt"

    other = ticket_category_map["📁 Другое"]
    assert other["template"] == "contact_info_message.txt"
    assert not other.get("subcategories")


def test_session_timeout_config():
    assert session_timeout["seconds"] == 900
    assert session_timeout["message_template"] == "inactivity_timeout.txt"
    assert session_timeout["send_message"] is False

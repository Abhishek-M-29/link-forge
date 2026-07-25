from user_agents import parse as parse_ua

def extract_browser_and_device(user_agent_string: str) -> tuple[str, str]:
    ua = parse_ua(user_agent_string or "")
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
    
    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "desktop"
    else:
        device = "other"
        
    return browser, device

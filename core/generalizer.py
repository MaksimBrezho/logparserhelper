import re

def generalize_token(token: str) -> str:
    if re.fullmatch(r'\d{4}', token):
        return r'\d{4}'  # Год
    if re.fullmatch(r'\d{2}', token):
        return r'\d{2}'  # День/месяц/часы/минуты/секунды
    if re.fullmatch(r'\d{1,3}', token):
        return r'\d{1,3}'  # IP-адрес или др.
    if re.fullmatch(r'\d+', token):
        return r'\d+'
    if re.fullmatch(r'[A-Z]+', token):
        return token  # Обработка через enum
    if re.fullmatch(r'[a-zA-Z_]+', token):
        return r'\w+'
    return re.escape(token)

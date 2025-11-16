from django import template
from decimal import Decimal
# 'library' nomli o'zgaruvchi bilan filterlar ro'yxatini yaratamiz
register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Berilgan qiymat (value) ni argument (arg) ga ko'paytiradi.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' # Xato bo'lsa bo'sh qoldirish yoki 0 qaytarish mumkin





@register.simple_tag # MUHIM: simple_tag dan foydalaning
def add_to_var(current_value, value_to_add):
    """ 'current_value' va 'value_to_add' ni qo'shadi. """
    try:
        # float ga o'tkazish muhim, chunki kirish string bo'lishi mumkin
        return float(current_value) + float(value_to_add)
    except:
        return 0

@register.filter
def filter_stock_critical(value):
    # Bu yerda filtr mantig'i bo'lishi kerak.
    # Masalan, qolgan mahsulotlar soniga qarab tekshirish.
    return value.filter(stock__lt=10) # Masalan uchun

@register.filter
def div(value, arg):
    """
    Berilgan qiymatni (value) berilgan argumentga (arg) bo'ladi.
    Agar bo'luvchi nol bo'lsa yoki noto'g'ri qiymat bo'lsa, xatolikni oldini oladi.
    """
    try:
        # Kirish qiymatlari satr bo'lishi mumkin, ularni raqamga o'tkazamiz
        val = Decimal(str(value))
        divisor = Decimal(str(arg))
    except (ValueError, TypeError):
        # Agar konvertatsiya qilish imkoni bo'lmasa, 0 qaytariladi
        return 0

    if divisor == 0:
        # Nolga bo'lishni oldini olish
        return 0
    
    # Bo'lish amalini bajarish
    return val / divisor


@register.filter
def user_count(values_list_result):
    """
    Django QuerySet.values_list() natijasidan noyob (unique) 
    foydalanuvchilar ID (yoki nom) sonini hisoblaydi.
    """
    
    # 1. Agar bo'sh ro'yxat kelsa
    if not values_list_result:
        return 0

    # 2. Noyob elementlarni saqlash uchun to'plam (set) ishlatiladi.
    unique_users = set()
    
    # values_list() natijasi odatda tuple lardan iborat bo'ladi:
    # (qiymat1, qiymat2, ...)
    
    for row in values_list_result:
        # Har bir qator (row) tuple bo'ladi. Foydalanuvchi ID si
        # qatorning birinchi elementi (indeks 0) deb faraz qilinadi.
        
        # Misol uchun: row = (user_id, amount, date)
        try:
            user_identifier = row[0]
            unique_users.add(user_identifier)
        except (TypeError, IndexError):
            # Agar qator tuple emas, balki bitta qiymat bo'lsa (ya'ni, values_list('user'))
            unique_users.add(row)
            
    # 3. Noyob foydalanuvchilar sonini qaytarish
    return len(unique_users)
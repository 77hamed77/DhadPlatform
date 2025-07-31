# C:\projectsDejango\DhadPlatform\contacts\utils.py

import phonenumbers
from phonenumbers import NumberParseException

# الدالة لتوليد رابط العلم (تستخدم في القالب عبر JS)
def get_flag_url(country_code, style='shiny', size='64'):
    if not country_code:
        return ''
    return f"https://flagsapi.com/{country_code}/{style}/{size}.png"

# قائمة تفصيلية وموسعة ببيانات الدول
COUNTRY_DATA = [
    {'code': '', 'name_ar': 'اختر رمز الدولة', 'dial_code': ''}, # خيار افتراضي
    
    # --- الدول العربية ---
    {'code': 'DZ', 'name_ar': 'الجزائر', 'dial_code': '+213'},
    {'code': 'BH', 'name_ar': 'البحرين', 'dial_code': '+973'},
    {'code': 'KM', 'name_ar': 'جزر القمر', 'dial_code': '+269'},
    {'code': 'DJ', 'name_ar': 'جيبوتي', 'dial_code': '+253'},
    {'code': 'SA', 'name_ar': 'السعودية', 'dial_code': '+966'},
    {'code': 'SO', 'name_ar': 'الصومال', 'dial_code': '+252'},
    {'code': 'SD', 'name_ar': 'السودان', 'dial_code': '+249'},
    {'code': 'SY', 'name_ar': 'سوريا', 'dial_code': '+963'},
    {'code': 'IQ', 'name_ar': 'العراق', 'dial_code': '+964'},
    {'code': 'OM', 'name_ar': 'عُمان', 'dial_code': '+968'},
    {'code': 'PS', 'name_ar': 'فلسطين', 'dial_code': '+970'},
    {'code': 'QA', 'name_ar': 'قطر', 'dial_code': '+974'},
    {'code': 'KW', 'name_ar': 'الكويت', 'dial_code': '+965'},
    {'code': 'LB', 'name_ar': 'لبنان', 'dial_code': '+961'},
    {'code': 'LY', 'name_ar': 'ليبيا', 'dial_code': '+218'},
    {'code': 'EG', 'name_ar': 'مصر', 'dial_code': '+20'},
    {'code': 'MA', 'name_ar': 'المغرب', 'dial_code': '+212'},
    {'code': 'MR', 'name_ar': 'موريتانيا', 'dial_code': '+222'},
    {'code': 'YE', 'name_ar': 'اليمن', 'dial_code': '+967'},
    {'code': 'AE', 'name_ar': 'الإمارات', 'dial_code': '+971'},
    {'code': 'JO', 'name_ar': 'الأردن', 'dial_code': '+962'},
    {'code': 'TN', 'name_ar': 'تونس', 'dial_code': '+216'},

    # --- دول أخرى مهمة ---
    {'code': 'AF', 'name_ar': 'أفغانستان', 'dial_code': '+93'},
    {'code': 'DE', 'name_ar': 'ألمانيا', 'dial_code': '+49'},
    {'code': 'ID', 'name_ar': 'إندونيسيا', 'dial_code': '+62'},
    {'code': 'IR', 'name_ar': 'إيران', 'dial_code': '+98'},
    {'code': 'IT', 'name_ar': 'إيطاليا', 'dial_code': '+39'},
    {'code': 'PK', 'name_ar': 'باكستان', 'dial_code': '+92'},
    {'code': 'BR', 'name_ar': 'البرازيل', 'dial_code': '+55'},
    {'code': 'GB', 'name_ar': 'المملكة المتحدة', 'dial_code': '+44'},
    {'code': 'US', 'name_ar': 'الولايات المتحدة', 'dial_code': '+1'},
    {'code': 'JP', 'name_ar': 'اليابان', 'dial_code': '+81'},
    {'code': 'IN', 'name_ar': 'الهند', 'dial_code': '+91'},
    {'code': 'CN', 'name_ar': 'الصين', 'dial_code': '+86'},
    {'code': 'RU', 'name_ar': 'روسيا', 'dial_code': '+7'},
    {'code': 'TR', 'name_ar': 'تركيا', 'dial_code': '+90'},
    {'code': 'AU', 'name_ar': 'أستراليا', 'dial_code': '+61'},
    {'code': 'BE', 'name_ar': 'بلجيكا', 'dial_code': '+32'},
    {'code': 'BD', 'name_ar': 'بنجلاديش', 'dial_code': '+880'},
    {'code': 'CA', 'name_ar': 'كندا', 'dial_code': '+1'},
    {'code': 'ES', 'name_ar': 'إسبانيا', 'dial_code': '+34'},
    {'code': 'FR', 'name_ar': 'فرنسا', 'dial_code': '+33'},
    {'code': 'ZA', 'name_ar': 'جنوب أفريقيا', 'dial_code': '+27'},
    {'code': 'KR', 'name_ar': 'كوريا الجنوبية', 'dial_code': '+82'},
    {'code': 'MY', 'name_ar': 'ماليزيا', 'dial_code': '+60'},
    {'code': 'MX', 'name_ar': 'المكسيك', 'dial_code': '+52'},
    {'code': 'NG', 'name_ar': 'نيجيريا', 'dial_code': '+234'},
    {'code': 'NL', 'name_ar': 'هولندا', 'dial_code': '+31'},
    {'code': 'SE', 'name_ar': 'السويد', 'dial_code': '+46'},
    {'code': 'CH', 'name_ar': 'سويسرا', 'dial_code': '+41'},
]

# تحويل COUNTRY_DATA إلى التنسيق المطلوب لـ ChoiceField في forms.py
# لا حاجة لتعديل هذا السطر، سيعمل تلقائياً مع القائمة الجديدة
COUNTRY_CHOICES = [(d['code'], f"{d['name_ar']} ({d['dial_code']})") for d in COUNTRY_DATA]

def get_country_data(country_code):
    """
    تبحث عن بيانات دولة معينة باستخدام رمزها (ISO 3166-1 alpha-2).
    """
    for country in COUNTRY_DATA:
        if country['code'] == country_code:
            return country
    return None

def validate_whatsapp_number(number, region=None):
    """
    تتحقق من صحة تنسيق رقم هاتف باستخدام مكتبة phonenumbers.
    """
    if not number:
        return False, "الرقم فارغ."

    try:
        parsed_number = phonenumbers.parse(number, region)

        if not phonenumbers.is_possible_number(parsed_number):
            return False, "تنسيق الرقم غير صحيح أو غير ممكن."

        if not phonenumbers.is_valid_number(parsed_number):
            return False, "الرقم غير صالح لمنطقة الاتصال المحددة."

        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        return True, formatted_number

    except NumberParseException as e:
        if e.error_type == NumberParseException.ErrorType.INVALID_COUNTRY_CODE:
            return False, "رمز الدولة غير صالح."
        elif e.error_type == NumberParseException.ErrorType.NOT_A_NUMBER:
            return False, "المدخل يحتوي على حروف غير رقمية."
        elif e.error_type == NumberParseException.ErrorType.TOO_SHORT:
            return False, "الرقم أقصر من اللازم."
        elif e.error_type == NumberParseException.ErrorType.TOO_LONG:
            return False, "الرقم أطول من اللازم."
        else:
            return False, f"خطأ في تحليل الرقم: {e}"
    except Exception as e:
        return False, f"حدث خطأ غير متوقع: {e}"
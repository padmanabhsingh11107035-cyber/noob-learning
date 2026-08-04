import base64
import datetime
import zoneinfo

def format_to_ist(dt_obj):
    if not dt_obj:
        return "N/A"
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.datetime.strptime(dt_obj, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return dt_obj
            
    ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
    
    local_dt = dt_obj.astimezone(ist_tz)
    return local_dt.strftime("%I:%M %p | %d %b %Y")

def get_current_ist_time():
    ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    return datetime.datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S')

def file_to_base64(file_bytes):
    return base64.b64encode(file_bytes).decode('utf-8')

import streamlit as st
import serial
import serial.tools.list_ports
import time
from datetime import datetime
import json
import os

# تكوين الصفحة
st.set_page_config(
    page_title="نظام إدارة البصمات",
    page_icon="👆",
    layout="wide"
)

# تهيئة حالة الجلسة
if 'device_connected' not in st.session_state:
    st.session_state.device_connected = False
if 'device_port' not in st.session_state:
    st.session_state.device_port = None
if 'fingerprints' not in st.session_state:
    st.session_state.fingerprints = []

def find_esp32():
    """البحث عن ESP32 المتصل"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # البحث عن أي منفذ متصل
        try:
            ser = serial.Serial(port.device, 57600, timeout=1)
            ser.close()
            return port.device
        except:
            continue
    return None

def read_serial_data(ser):
    """قراءة البيانات من المنفذ التسلسلي بشكل آمن"""
    try:
        if ser.in_waiting:
            # قراءة البيانات الخام
            raw_data = ser.readline()
            
            # محاولة فك التشفير بعدة طرق
            try:
                # محاولة UTF-8
                return raw_data.decode('utf-8').strip()
            except UnicodeDecodeError:
                try:
                    # محاولة ASCII مع تجاهل الأخطاء
                    text = raw_data.decode('ascii', errors='ignore').strip()
                    if text:
                        return text
                except:
                    pass
                
                # إذا فشل كل شيء، إرجاع البيانات كسلسلة هيكس
                return ' '.join([f'{b:02x}' for b in raw_data])
        return None
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {str(e)}")
        return None

def send_serial_command(ser, command, wait_for_response=True):
    """إرسال أمر واستقبال الرد"""
    try:
        # تنظيف البيانات القديمة
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        st.info(f"إرسال الأمر: {command}")
        # إرسال الأمر مع علامة نهاية السطر
        full_command = f"{command}\r\n"
        ser.write(full_command.encode())
        ser.flush()
        
        if wait_for_response:
            # انتظار الرد
            st.info("انتظار الرد...")
            time.sleep(0.5)
            
            # قراءة كل البيانات المتاحة
            responses = []
            start_time = time.time()
            while time.time() - start_time < 2:  # انتظار لمدة ثانيتين كحد أقصى
                response = read_serial_data(ser)
                if response:
                    responses.append(response)
                    if len(responses) >= 3:  # قراءة حتى 3 استجابات كحد أقصى
                        break
                time.sleep(0.1)
            
            # عرض كل الردود
            for i, resp in enumerate(responses):
                st.info(f"الرد {i+1}: {resp}")
            
            return responses[0] if responses else None
            
        return True
    except Exception as e:
        st.error(f"خطأ في إرسال الأمر: {str(e)}")
        return None

def connect_to_device(port):
    """الاتصال بالجهاز"""
    # قائمة معدلات البود المحتملة
    baud_rates = [9600, 19200, 38400, 57600, 115200]
    
    for baud_rate in baud_rates:
        try:
            st.info(f"محاولة الاتصال بمعدل بود {baud_rate}...")
            ser = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2
            )
            
            if not ser.is_open:
                ser.open()
            
            # تنظيف البيانات القديمة
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            time.sleep(1)  # انتظار استقرار الاتصال
            
            # محاولة أوامر مختلفة للتحقق
            test_commands = [
                "CHECK",
                "STATUS",
                "PING",
                "AT"  # بعض الأجهزة تستجيب لأوامر AT
            ]
            
            for cmd in test_commands:
                st.info(f"تجربة الأمر: {cmd}")
                response = send_serial_command(ser, cmd)
                
                if response:
                    # تحقق من صحة الرد
                    if isinstance(response, str) and len(response) > 1 and not all(c in '!?*' for c in response):
                        st.success(f"تم العثور على استجابة صالحة مع معدل بود {baud_rate}")
                        st.session_state.device_port = port
                        st.session_state.device_connected = True
                        st.session_state.baud_rate = baud_rate  # حفظ معدل البود الناجح
                        return ser
                
                time.sleep(0.5)
            
            ser.close()
            
        except serial.SerialException as e:
            st.error(f"خطأ في المنفذ التسلسلي: {str(e)}")
            continue
        except Exception as e:
            st.error(f"خطأ غير متوقع: {str(e)}")
            continue
    
    st.warning("لم يتم العثور على استجابة صالحة مع أي معدل بود")
    return None

# واجهة المستخدم
st.title("👆 نظام إدارة البصمات")

# القائمة الجانبية
with st.sidebar:
    st.header("لوحة التحكم")
    
    # البحث عن الجهاز
    if st.button("البحث عن الجهاز"):
        port = find_esp32()
        if port:
            st.success(f"تم العثور على الجهاز على المنفذ {port}")
            if connect_to_device(port):
                st.success("تم الاتصال بالجهاز بنجاح")
            else:
                st.error("تم العثور على الجهاز لكن فشل الاتصال")
        else:
            st.error("لم يتم العثور على الجهاز")
    
    # قائمة العمليات
    if st.session_state.device_connected:
        if st.button("تسجيل بصمة جديدة"):
            st.session_state.current_page = "enroll"
        if st.button("عرض البصمات"):
            st.session_state.current_page = "view"
        if st.button("سجل الأحداث"):
            st.session_state.current_page = "logs"

# عرض الصفحة المناسبة
if not st.session_state.device_connected:
    st.info("قم بتوصيل الجهاز وابحث عنه من القائمة الجانبية")

else:
    if st.session_state.get('current_page') == "enroll":
        st.header("تسجيل بصمة جديدة")
        with st.form("enroll_form"):
            user_name = st.text_input("اسم المستخدم")
            user_id = st.text_input("رقم الهوية")
            notes = st.text_area("ملاحظات")
            submitted = st.form_submit_button("تسجيل البصمة")
            
            if submitted:
                try:
                    with serial.Serial(st.session_state.device_port, 
                                     st.session_state.get('baud_rate', 57600), 
                                     timeout=10) as ser:
                        # إرسال أمر تسجيل البصمة
                        st.info("جاري تجهيز الجهاز...")
                        response = send_serial_command(ser, "ENROLL")
                        
                        if response:
                            with st.spinner("ضع إصبعك على جهاز البصمة..."):
                                time.sleep(2)
                                response = read_serial_data(ser)
                                
                                # تحليل الرد بغض النظر عن التنسيق
                                if response and any(keyword in response.upper() for keyword in ["SCAN", "PLACE", "FINGER"]):
                                    st.info("ارفع إصبعك")
                                    time.sleep(2)
                                    st.info("ضع إصبعك مرة أخرى")
                                    time.sleep(2)
                                    response = read_serial_data(ser)
                                    
                                    # تحقق من نجاح العملية
                                    if response and any(keyword in response.upper() for keyword in ["OK", "SUCCESS", "DONE"]):
                                        new_fingerprint = {
                                            'name': user_name,
                                            'id': user_id,
                                            'notes': notes,
                                            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                        st.session_state.fingerprints.append(new_fingerprint)
                                        st.success("تم تسجيل البصمة بنجاح!")
                                    else:
                                        st.error("فشل في تسجيل البصمة")
                                        if response:
                                            st.info(f"رد الجهاز: {response}")
                                else:
                                    st.error("فشل في قراءة البصمة")
                                    if response:
                                        st.info(f"رد الجهاز: {response}")
                        else:
                            st.error("لم يستجب الجهاز")
                            
                except serial.SerialException as e:
                    st.error(f"خطأ في الاتصال: {str(e)}")
                except Exception as e:
                    st.error(f"حدث خطأ: {str(e)}")
    
    elif st.session_state.get('current_page') == "view":
        st.header("البصمات المسجلة")
        if st.session_state.fingerprints:
            for fp in st.session_state.fingerprints:
                col1, col2, col3 = st.columns([2,2,1])
                with col1:
                    st.write(f"**{fp['name']}**")
                    st.write(f"رقم الهوية: {fp['id']}")
                with col2:
                    st.write(f"تاريخ التسجيل: {fp['date']}")
                    if fp.get('notes'):
                        st.write(f"ملاحظات: {fp['notes']}")
                with col3:
                    if st.button(f"حذف", key=f"del_{fp['id']}"):
                        try:
                            with serial.Serial(st.session_state.device_port, 57600, timeout=5) as ser:
                                response = send_serial_command(ser, f"DELETE {fp['id']}")
                                if response and "OK" in response:
                                    st.session_state.fingerprints.remove(fp)
                                    st.success("تم حذف البصمة بنجاح")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("فشل في حذف البصمة")
                        except Exception as e:
                            st.error(f"خطأ في حذف البصمة: {str(e)}")
                st.divider()
        else:
            st.info("لا توجد بصمات مسجلة")
    
    elif st.session_state.get('current_page') == "logs":
        st.header("سجل الأحداث")
        try:
            with serial.Serial(st.session_state.device_port, 57600, timeout=5) as ser:
                response = send_serial_command(ser, "GET_LOGS")
                if response:
                    try:
                        logs = json.loads(response)
                        for log in logs:
                            st.write(f"{log['timestamp']} - {log['event']} - {log['user']}")
                    except json.JSONDecodeError:
                        st.write(response)
                else:
                    st.info("لا توجد أحداث مسجلة")
        except Exception as e:
            st.error(f"خطأ في قراءة السجل: {str(e)}")
    
    else:
        # الصفحة الرئيسية
        st.header("لوحة المعلومات")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("عدد البصمات", len(st.session_state.fingerprints))
        with col2:
            # التحقق من حالة الاتصال
            try:
                with serial.Serial(st.session_state.device_port, 57600, timeout=1) as ser:
                    response = send_serial_command(ser, "STATUS")
                    status = "متصل 🟢" if response else "غير متصل 🔴"
            except:
                status = "غير متصل 🔴"
            st.metric("حالة الاتصال", status)
        with col3:
            st.metric("آخر تحديث", datetime.now().strftime("%H:%M:%S")) 
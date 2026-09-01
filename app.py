import streamlit as st
import sqlite3
import pandas as pd
import datetime

==========================================
إعداد قاعدة البيانات (SQLite)
==========================================
def init_db():
conn = sqlite3.connect('emis_database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS learners (
student_id TEXT PRIMARY KEY,
national_id TEXT,
first_name TEXT,
gender TEXT,
status TEXT,
entry_date TEXT
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS data_quality (
issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
record_id TEXT,
issue_desc TEXT,
severity TEXT,
status TEXT,
log_date TEXT
)
''')
conn.commit()
return conn

==========================================
دوال التعامل مع البيانات
==========================================
def add_student(conn, student_id, national_id, first_name, gender, status):
c = conn.cursor()
try:
c.execute("INSERT INTO learners VALUES (?, ?, ?, ?, ?, ?)",
(student_id, national_id, first_name, gender, status, str(datetime.date.today())))
conn.commit()
return True
except sqlite3.IntegrityError:
return False

def get_data(conn, table_name):
return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

def log_data_issue(conn, record_id, issue_desc, severity):
c = conn.cursor()
c.execute("INSERT INTO data_quality (record_id, issue_desc, severity, status, log_date) VALUES (?, ?, ?, ?, ?)",
(record_id, issue_desc, severity, "مفتوحة", str(datetime.date.today())))
conn.commit()

def resolve_issue(conn, issue_id):
c = conn.cursor()
c.execute("UPDATE data_quality SET status='مغلقة' WHERE issue_id=?", (issue_id,))
conn.commit()

==========================================
واجهة المستخدم
==========================================
st.set_page_config(page_title="نظام EMIS", page_icon="📊", layout="wide")

conn = init_db()

st.sidebar.title("إدارة النظام")
st.sidebar.markdown("---")
menu = ["📊 لوحة القيادة", "📝 إدخال البيانات", "🛡️ جودة البيانات"]
choice = st.sidebar.radio("الانتقال إلى:", menu)

if choice == "📊 لوحة القيادة":
st.title("لوحة مؤشرات الأداء (KPIs)")

df_students = get_data(conn, "learners")
df_issues = get_data(conn, "data_quality")

total_students = len(df_students)
active_students = len(df_students[df_students['status'] == 'نشط']) if total_students > 0 else 0
open_issues = len(df_issues[df_issues['status'] == 'مفتوحة']) if len(df_issues) > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("إجمالي الطلاب المسجلين", total_students)
col2.metric("الطلاب النشطون", active_students)
col3.metric("تنبيهات جودة البيانات", open_issues)

st.markdown("---")

if total_students > 0:
st.subheader("توزيع الطلاب حسب الجنس")
gender_count = df_students['gender'].value_counts().reset_index()
gender_count.columns = ['الجنس', 'العدد']
st.bar_chart(gender_count.set_index('الجنس'))

elif choice == "📝 إدخال البيانات":
st.title("إدارة سجلات الطلاب")

with st.form("student_form", clear_on_submit=True):
col1, col2 = st.columns(2)
student_id = col1.text_input("معرف الطالب (ID)")
national_id = col2.text_input("الرقم الوطني")
first_name = col1.text_input("الاسم الأول")
gender = col2.selectbox("الجنس", ["ذكر", "أنثى"])
status = col1.selectbox("الحالة", ["نشط", "منقطع", "متخرج"])

if st.form_submit_button("💾 حفظ السجل"):
if student_id and first_name:
if add_student(conn, student_id, national_id, first_name, gender, status):
st.success("تم الحفظ بنجاح!")
else:
st.error("المعرف موجود مسبقاً.")
else:
st.warning("يرجى تعبئة الحقول الإلزامية (*).")

st.markdown("---")
st.subheader("السجلات الحالية")
st.dataframe(get_data(conn, "learners"), use_container_width=True)

elif choice == "🛡️ جودة البيانات":
st.title("مراقبة جودة البيانات")

with st.form("issue_form", clear_on_submit=True):
rec_id = st.text_input("معرف السجل المرتبط")
desc = st.text_area("وصف المشكلة*")
severity = st.selectbox("الخطورة", ["منخفضة", "متوسطة", "عالية"])

if st.form_submit_button("إضافة الملاحظة"):
if desc:
log_data_issue(conn, rec_id, desc, severity)
st.success("تم التسجيل.")
else:
st.warning("يرجى كتابة وصف المشكلة.")

st.markdown("---")
df_issues = get_data(conn, "data_quality")
if not df_issues.empty:
st.dataframe(df_issues[df_issues['status'] == 'مفتوحة'], use_container_width=True)
resolve_id = st.number_input("رقم المشكلة لإغلاقها:", min_value=1, step=1)
if st.button("✔️ إغلاق المشكلة"):
resolve_issue(conn, resolve_id)
st.success("تم إغلاق المشكلة. حدث الصفحة.")

conn.close()
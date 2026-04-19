import streamlit as st
import pandas as pd
import google.generativeai as genai

# הגדרות עיצוב
st.set_page_config(page_title="חיפוש חכם בקטלוג", layout="wide")
st.title("🔎 חיפוש חכם בכתבי יד (Gemini AI)")

# חיבור ל-API של Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-pro')
else:
    st.error("יש להגדיר את המפתח ב-Secrets")
    st.stop()

@st.cache_data
def get_catalog_text():
    # קריאת הקטלוג והפיכתו לטקסט אחד ארוך שה-AI יכול לקרוא
    df = pd.read_csv("catalog.csv")
    # אנחנו שולחים רק את העמודות החשובות כדי לחסוך מקום
    relevant_cols = ['מספר כתב יד', 'מדור ומדף', 'תיאור הכתב יד']
    return df[relevant_cols].to_csv(index=False)

catalog_data = get_catalog_text()

query = st.text_input("שאל את ה-AI על הקטלוג (למשל: 'אילו פנקסים של אדמו''ר הזקן קיימים?'):")

if query:
    prompt = f"""
    אתה ספרן ומומחה ביבליוגרפי לחסידות חב"ד. 
    להלן קטלוג כתבי יד מלא:
    
    {catalog_data}
    
    בהתבסס אך ורק על הקטלוג לעיל, ענה על השאלה הבאה: "{query}"
    אם מצאת פריטים רלוונטיים, פרט את המספר שלהם ואת התיאור בקצרה. 
    אם יש מושגים חסידיים או ראשי תיבות, השתמש בידע שלך כדי לפרש אותם נכון מתוך ההקשר.
    """
    
    with st.spinner("ה-AI החכם סורק את כל הקטלוג..."):
        try:
            response = model.generate_content(prompt)
            st.markdown("### תשובת המערכת:")
            st.write(response.text)
        except Exception as e:
            st.error(f"שגיאה בתקשורת עם ה-AI: {e}")

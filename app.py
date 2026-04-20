import streamlit as st
import pandas as pd
import google.generativeai as genai
from thefuzz import fuzz

# עיצוב בסיסי של העמוד
st.set_page_config(page_title="חיפוש חכם בכתבי יד", layout="wide")
st.title("🔎 מנוע חיפוש חסידי חכם")
st.markdown("מנוע זה מבין יידיש, ראשי תיבות, ומגשר על שגיאות כתיב והטיות.")

# 1. חיבור בטוח ל-API של Gemini (מתוך ה-Secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("שגיאה: יש להגדיר GEMINI_API_KEY בהגדרות Streamlit")
    st.stop()

# שימוש במודל Flash - חכם מספיק לבלשנות, חינמי בנפחים האלה, וסופר מהיר
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. טעינת הנתונים מהקטלוג (קורה פעם אחת כשהאתר עולה)
@st.cache_data
def load_data():
    return pd.read_csv("catalog.csv").astype(str)

try:
    df = load_data()
except FileNotFoundError:
    st.error("לא נמצא קובץ קטלוג בשם 'catalog_hasidut_final.csv'. אנא ודא שהקובץ נמצא ב-GitHub.")
    st.stop()

query = st.text_input("מה תרצה לחפש בקטלוג? (למשל: סטרשלה, מאמרים לפסח, אדה\"ז):")

if query:
    with st.spinner("מפענח את הבקשה, מחפש מילים נרדפות והטיות ביידיש..."):
        # 3. ה-AI מרחיב את השאילתה - "המוח הבלשני"
        expansion_prompt = f"""
        אתה מומחה ביבליוגרפי לחסידות חב"ד ששולט ביידיש ובעברית.
        המשתמש מחפש בקטלוג כתבי יד את המונח הבא: "{query}"
        
        המטרה שלך היא לעזור למנוע החיפוש לא לפספס שום תוצאה. כתוב שורת טקסט אחת, מופרדת בפסיקים, שמכילה:
        1. המונח התקני.
        2. פתיחת ראשי תיבות אם קיימים (כגון אדה"ז -> אדמו"ר הזקן).
        3. שמות נרדפים בחסידות לאותו מושג.
        4. וריאציות כתיב ושיבושים נפוצים (שים לב במיוחד לחילופי ס/ש, א/ע/י/ה, וכתיב חסר/מלא. למשל: סטראשעלע, שטרושילא, סטרשלה).
        
        החזר אך ורק את שורת המילים, מופרדות בפסיק, ללא שום טקסט נוסף או הקדמות.
        """
        
        try:
            # מקבלים מ-Gemini את רשימת המילים
            expanded_query = model.generate_content(expansion_prompt).text.strip()
            st.info(f"**מילות מפתח שנוספו לחיפוש ע\"י ה-AI:** {expanded_query}")
            
            # מנקים את המילים ממרכאות ומרווחים מיותרים
            search_terms = [term.strip().replace('"', '').replace("'", "") for term in expanded_query.split(',')]
            
            # 4. מנוע החיפוש המקומי: משלב דיוק וסלחנות (Fuzzy Search)
            def check_match(row):
                # חיבור כל הערכים בשורה לטקסט אחד ארוך כדי לחפש בכל העמודות
                row_text = " ".join(row.values)
                
                for term in search_terms:
                    if len(term) > 2: # מתעלם ממילות קישור קצרצרות
                        # אופציה א': בדיקה מדויקת (הכי מהיר)
                        if term in row_text:
                            return True
                        
                        # אופציה ב': בדיקה סלחנית (Fuzzy) אם אין התאמה מדויקת
                        # עובר על המילים בשורה ובודק אם יש מילה מאוד דומה (85% התאמה)
                        for word in row_text.split():
                            if fuzz.ratio(term, word) > 85:
                                return True
                return False
                
            # הפעלת הסינון על הקטלוג
            results = df[df.apply(check_match, axis=1)]
            
            # 5. הצגת התוצאות
            st.markdown(f"### 📚 נמצאו {len(results)} תוצאות אפשריות:")
            if not results.empty:
                # מציג את כל התוצאות שנמצאו
                for idx, row in results.iterrows():
                    with st.container():
                        st.markdown(f"**מספר כתב יד:** `{row.get('מספר כתב יד', 'לא ידוע')}` | **מדור ומדף:** `{row.get('מדור ומדף', 'לא ידוע')}`")
                        st.write(f"{row.get('תיאור הכתב יד', 'אין תיאור')}")
                        st.divider()
            else:
                st.warning("לא נמצאו פריטים רלוונטיים. נסה לשנות את מילות החיפוש.")
                
        except Exception as e:
            st.error(f"אירעה שגיאה. ייתכן שיש חריגה בחיבור ל-API או בעיה בקריאת הנתונים: {e}")

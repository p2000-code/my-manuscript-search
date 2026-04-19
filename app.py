import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# הגדרת כותרת דף ועיצוב בסיסי
st.set_page_config(page_title="חיפוש סמנטי בקטלוג כתבי יד", layout="wide")

st.title("🔎 מערכת חיפוש AI בקטלוג כתבי יד")
st.markdown("חיפוש חכם המבין את תוכן הכתבים (מבוסס משמעות ולא רק מילים מדויקות)")

# פונקציה לטעינת הנתונים (עם מטמון)
@st.cache_data
def load_data():
    # שם הקובץ כפי שהוגדר בפרויקט
    df = pd.read_csv("catalog.csv")
    df['תיאור הכתב יד'] = df['תיאור הכתב יד'].fillna("")
    return df

# פונקציה לטעינת המודל (עם מטמון)
@st.cache_resource
def load_model():
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# פונקציה ליצירת ווקטורים (Embeddings) - מתבצע פעם אחת בלבד
@st.cache_data
def get_embeddings(_model, data_list):
    return _model.encode(data_list, show_progress_bar=True)

# הרצת הטעינה
with st.spinner("טוען נתונים ומודל בינה מלאכותית..."):
    df = load_data()
    model = load_model()
    embeddings = get_embeddings(model, df['תיאור הכתב יד'].tolist())

# ממשק המשתמש בצד (Sidebar)
st.sidebar.header("הגדרות חיפוש")
top_k = st.sidebar.slider("מספר תוצאות להצגה", 1, 10, 5)

# תיבת החיפוש המרכזית
query = st.text_input("מה ברצונך לחפש? (למשל: 'דרושים מהריי\"צ באידיש', 'כוונות התפילה')", "")

if query:
    # ביצוע החיפוש
    query_vector = model.encode([query])
    similarities = cosine_similarity(query_vector, embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    st.subheader(f"תוצאות עבור: '{query}'")
    
    for i in top_indices:
        if similarities[i] > 0.2: # סינון תוצאות שאינן קשורות כלל
            with st.expander(f"כתב יד מס' {df.iloc[i]['מספר כתב יד']} (התאמה: {similarities[i]:.2f})"):
                st.write(f"**תיאור:** {df.iloc[i]['תיאור הכתב יד']}")
                if 'מספר עמודים' in df.columns:
                    st.write(f"**עמודים:** {df.iloc[i]['מספר עמודים']}")
        else:
            st.info("לא נמצאו תוצאות נוספות ברמת התאמה גבוהה.")
            break
else:
    st.write("הזן מילת חיפוש כדי להתחיל.")
